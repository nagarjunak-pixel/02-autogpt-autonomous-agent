"""Governed semantic layer for the P02 kit: 12 owned metrics compiled to deterministic DuckDB SQL.

A planner (rules or an LLM) only fills a MetricQuery; this module writes the SQL, and sql_guard checks it before
it runs. Students extend the catalogue to 30 metrics (brief §3).
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

# Curveball 4: when a migration renames columns, change this mapping once (e.g. net_amount -> net_sales_inr).
COLUMNS = {"net_amount": "net_amount", "store_id": "store_id"}

# name: (SQL expression, owner, finance metric?). Finance metrics must never go down the fallback path (AC-2).
METRICS = {
    "gross_sales": ("SUM(f.gross_amount)", "COO", False),
    "net_revenue": ("SUM(f.{net_amount}) - SUM(COALESCE(r.refund_amount, 0))", "CFO", True),
    "discount_amount": ("SUM(f.discount_amount)", "CFO", True),
    "gst_collected": ("SUM(f.gst_amount)", "CFO", True),
    "refund_amount": ("SUM(COALESCE(r.refund_amount, 0))", "CFO", True),
    "avg_discount_rate": ("SUM(f.discount_amount) / NULLIF(SUM(f.gross_amount), 0)", "CFO", True),
    "units_sold": ("SUM(f.qty)", "COO", False),
    "bill_count": ("COUNT(DISTINCT f.bill_id)", "COO", False),
    "avg_bill_value": ("SUM(f.gross_amount) / NULLIF(COUNT(DISTINCT f.bill_id), 0)", "COO", False),
    "return_rate": ("COUNT(r.original_bill_id) * 1.0 / NULLIF(COUNT(*), 0)", "COO", False),
    "private_label_share": ("SUM(CASE WHEN p.is_private_label THEN f.gross_amount ELSE 0 END)"
                            " / NULLIF(SUM(f.gross_amount), 0)", "COO", False),
    "active_stores": ("COUNT(DISTINCT s.{store_id})", "COO", False),
}
# Curveball 1: until the COO and CFO agree a default, "revenue" must trigger a clarifying question.
AMBIGUOUS_TERMS = {"revenue": ["gross_sales", "net_revenue"]}
DIMENSIONS = {  # name: (SQL expression, output column)
    "category": ("p.category", "category"), "brand": ("p.brand", "brand"), "format": ("s.format", "store_format"),
    "store": ("s.{store_id}", "store_code"), "region": ("f.region_id", "region_id"), "day": ("f.date_key", "sale_date"),
}
TIME_RANGES = ("yesterday", "last_week", "last_month", "fytd")
FALLBACK_LABEL = "unverified definition"


@dataclass
class Response:
    """What any system (baseline.py, adapter.py or yours) returns for one question."""
    kind: str                            # "answer" | "clarify" | "refuse"
    text: str = ""                       # shown to the user; answers must state scope and data freshness (AC-6)
    metric_query: Optional[dict] = None  # semantic path: {"metric", "dimensions", "time_range", "order", "limit"}
    sql: Optional[str] = None            # fallback path only; its text must carry FALLBACK_LABEL (AC-2)
    attempts: int = 1                    # generation + repair attempts used (AC-10 allows at most 2)

    @property
    def path(self) -> str:
        return "semantic" if self.metric_query else "fallback" if self.sql else "none"


def resolve_time_range(name: str, today: date) -> tuple[date, date]:
    """Relative dates are resolved in code, never by the model. The fiscal year runs April to March."""
    yesterday = today - timedelta(days=1)
    if name == "yesterday":
        return yesterday, yesterday
    if name == "last_week":  # the previous Monday-to-Sunday week
        start = today - timedelta(days=today.weekday() + 7)
        return start, start + timedelta(days=6)
    if name == "last_month":
        end = today.replace(day=1) - timedelta(days=1)
        return end.replace(day=1), end
    if name == "fytd":
        return date(today.year if today.month >= 4 else today.year - 1, 4, 1), yesterday
    raise ValueError(f"unknown time_range: {name!r}")


def compile_query(mq: dict, today: date, columns: dict = COLUMNS) -> str:
    """MetricQuery -> SQL. Raises ValueError for anything outside the catalogue, so the planner must retry or ask."""
    if mq.get("metric") not in METRICS:
        raise ValueError(f"unknown metric: {mq.get('metric')!r}")
    dims = list(mq.get("dimensions") or [])
    if any(d not in DIMENSIONS for d in dims):
        raise ValueError(f"unknown dimension in {dims}")
    start, end = resolve_time_range(mq.get("time_range") or "", today)
    select = [f"{DIMENSIONS[d][0].format(**columns)} AS {DIMENSIONS[d][1]}" for d in dims]
    select.append(f"ROUND({METRICS[mq['metric']][0].format(**columns)}, 4) AS value")
    sql = (f"SELECT {', '.join(select)} FROM fct_sales_line AS f "
           "JOIN dim_store AS s ON f.store_sk = s.store_sk "
           "JOIN dim_product AS p ON f.product_id = p.product_id "
           "LEFT JOIN fct_returns AS r ON r.original_bill_id = f.bill_id AND r.product_id = f.product_id "
           f"WHERE f.date_key BETWEEN DATE '{start}' AND DATE '{end}' "
           f"AND s.{columns['store_id']} NOT LIKE 'TEST-%'")  # default filter: test stores have no flag yet
    positions = ", ".join(str(i + 1) for i in range(len(dims)))
    if dims:
        sql += f" GROUP BY {positions}"
    if mq.get("order") == "desc":
        sql += " ORDER BY value DESC" + (f", {positions}" if dims else "")
    elif dims:
        sql += f" ORDER BY {positions}"
    if mq.get("limit"):
        sql += f" LIMIT {int(mq['limit'])}"
    return sql
