"""Deliberately simple, non-LLM baseline for P02: keyword rules that fill a MetricQuery.

It is meant to fail several acceptance criteria (Hindi, clarification, refusals, freshness). Replace it with your
planner and watch the numbers move. Interface shared with adapter.py: predict(question, user, ctx) -> Response.
"""
import re

from semantic_layer import FALLBACK_LABEL, Response, resolve_time_range

REFUSE_WORDS = ("delete", "drop", "truncate", "update", "insert", "forecast", "cashier", "loyalty", "salary")
METRIC_WORDS = [  # first match wins, so the more specific phrase comes first
    ("net revenue", "net_revenue"), ("gross sales", "gross_sales"), ("return rate", "return_rate"),
    ("average bill", "avg_bill_value"), ("discount rate", "avg_discount_rate"), ("discount", "discount_amount"),
    ("gst", "gst_collected"), ("refund", "refund_amount"), ("private label", "private_label_share"),
    ("units", "units_sold"), ("bills", "bill_count"), ("active stores", "active_stores"), ("sales", "gross_sales"),
    ("बिक्री", "gross_sales"),  # the only Devanagari word it knows
]
DIM_WORDS = [("by category", "category"), ("category wise", "category"), ("by brand", "brand"), ("brand wise", "brand"),
             ("by store format", "format"), ("format wise", "format"), ("by store", "store"), ("store wise", "store"),
             ("by region", "region"), ("region wise", "region"), ("by day", "day")]
TIME_WORDS = [("yesterday", "yesterday"), ("kal", "yesterday"), ("last week", "last_week"),
              ("pichhle hafte", "last_week"), ("last month", "last_month"), ("pichhle mahine", "last_month"),
              ("financial year", "fytd")]
CANNED_SQL = {  # rung 1 of the brief's ladder: verified query templates, English trigger phrases only
    "return reason": "SELECT r.reason, COUNT(*) AS n FROM fct_returns AS r JOIN dim_store AS s ON r.store_sk = s.store_sk "
                     "WHERE r.return_date BETWEEN DATE '{start}' AND DATE '{end}' AND s.store_id NOT LIKE 'TEST-%' "
                     "GROUP BY r.reason ORDER BY n DESC, r.reason LIMIT 1",
    "distinct products": "SELECT COUNT(DISTINCT f.product_id) AS n FROM fct_sales_line AS f JOIN dim_store AS s "
                         "ON f.store_sk = s.store_sk WHERE f.date_key BETWEEN DATE '{start}' AND DATE '{end}' "
                         "AND s.store_id NOT LIKE 'TEST-%'",
}


def _first(pairs, text):
    return next((value for key, value in pairs if re.search(rf"(?<!\w){re.escape(key)}(?!\w)", text)), None)


def predict(question: str, user: dict, ctx: dict) -> Response:
    q = question.lower()
    footer = f"Scope: {user['scope_label']}."  # states scope, but not data freshness, so AC-6 fails
    if any(re.search(rf"\b{w}\b", q) for w in REFUSE_WORDS):
        return Response("refuse", "Sorry, I can't help with that request. " + footer)
    if re.search(r"\brevenue\b", q) and not re.search(r"\b(net|gross)\b", q):
        return Response("clarify", "Do you mean gross sales (COO definition) or net revenue (CFO definition)?")
    time_range = _first(TIME_WORDS, q) or "last_week"
    for trigger, sql in CANNED_SQL.items():
        if trigger in q:
            start, end = resolve_time_range(time_range, ctx["today"])
            return Response("answer", f"Answer uses an {FALLBACK_LABEL}. {footer}", sql=sql.format(start=start, end=end))
    metric = _first(METRIC_WORDS, q)
    if metric is None:  # no cross-scope check either: "West region ka sales" is silently answered for your own region
        return Response("clarify", "Sorry, I didn't understand. Could you rephrase?")
    top = re.search(r"\btop (\d+)", q)
    dims = ["store"] if top else [d for d in [_first(DIM_WORDS, q)] if d]
    mq = {"metric": metric, "dimensions": dims, "time_range": time_range,
          "order": "desc" if top else None, "limit": int(top.group(1)) if top else None}
    return Response("answer", f"{metric} for {time_range}. {footer}", metric_query=mq)
