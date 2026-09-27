"""SQL guard from brief §7: runs on every statement before execution, on both the semantic and the fallback path.

Defence in depth only. Production also needs statement timeouts, warehouse cost caps and native row access
policies under a read-only role (brief §7, ADR-004).
"""
from typing import Callable, Optional

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

ALLOWED_TABLES = {"fct_sales_line", "fct_returns", "dim_store", "dim_product", "dim_date", "dim_region"}
RLS_COLUMN = {"fct_sales_line": "region_id", "fct_returns": "region_id", "dim_store": "region_id"}
FORBIDDEN_NODES = (exp.Insert, exp.Update, exp.Delete, exp.Merge, exp.Into, exp.Create,
                   exp.Drop, exp.Alter, exp.Command, exp.Copy)
MAX_ROWS = 5_000


class GuardError(Exception):
    """Raised with a message the agent can show the user or use to repair its SQL."""


def guard_sql(sql: str, region_ids: Optional[list[int]], dialect: str = "duckdb",
              estimate_cost: Optional[Callable[[str], float]] = None,
              max_cost: float = 0.0) -> str:
    """region_ids=None means national scope (HQ role); [] means no data access."""
    try:
        statements = sqlglot.parse(sql, read=dialect)
    except sqlglot.errors.ParseError as e:
        raise GuardError(f"unparseable SQL: {e}") from e
    if len(statements) != 1 or statements[0] is None:
        raise GuardError("exactly one statement is allowed")
    tree = statements[0]
    # 1. Read-only queries only, with no DML hidden inside CTEs.
    if not isinstance(tree, exp.Query):
        raise GuardError(f"only SELECT queries are allowed, got {type(tree).__name__}")
    if any(True for _ in tree.find_all(*FORBIDDEN_NODES)):
        raise GuardError("data-modifying or DDL clause found")
    # 2. Table allow-list. Resolve names by scope, so a CTE cannot shadow a real table.
    real = {id(s): s for sc in traverse_scope(tree) for s in sc.sources.values() if isinstance(s, exp.Table)}
    ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    if any(id(t) not in real and t.name.lower() not in ctes for t in tree.find_all(exp.Table)):
        raise GuardError("unresolved table reference")
    tables = list(real.values())
    for t in tables:
        if t.db or t.catalog or t.name.lower() not in ALLOWED_TABLES:
            raise GuardError(f"table not allowed: {t.sql(dialect=dialect) or 'table function'}")
    # 3. Row-level security: swap each protected table for a filtered subquery.
    if region_ids is not None:
        if not region_ids:
            raise GuardError("no region entitlement")
        for t in tables:
            col = RLS_COLUMN.get(t.name.lower())
            if col:
                pred = exp.column(col).isin(*[exp.Literal.number(int(r)) for r in region_ids])
                sub = exp.select("*").from_(exp.to_table(t.name)).where(pred)
                t.replace(sub.subquery(t.alias_or_name))
    # 4. Row cap: add or tighten LIMIT.
    limit = tree.args.get("limit")
    current = limit.expression if limit else None
    if not (isinstance(current, exp.Literal) and int(current.name) <= MAX_ROWS):
        tree = tree.limit(MAX_ROWS)
    safe_sql = tree.sql(dialect=dialect)
    # 5. Cost gate: dry run / EXPLAIN estimate before anything executes.
    if estimate_cost is not None and estimate_cost(safe_sql) > max_cost:
        raise GuardError("estimated cost above cap; ask the user to narrow the date range or stores")
    return safe_sql


def scan_cost_estimator(row_counts: dict[str, int], dialect: str = "duckdb") -> Callable[[str], float]:
    """Cost simulator stand-in (BigQuery-style bytes scanned): every real table reference is a full scan.

    CTE references are not counted twice. Swap this for a real dry run (BigQuery) or an EXPLAIN-based estimate
    (Snowflake, Postgres) when you have one.
    """
    def estimate(sql: str) -> float:
        tree = sqlglot.parse_one(sql, read=dialect)
        real = {id(s): s for sc in traverse_scope(tree) for s in sc.sources.values() if isinstance(s, exp.Table)}
        return float(sum(row_counts.get(t.name.lower(), 0) for t in real.values()))
    return estimate
