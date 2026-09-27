"""Adapter stub: plug a real model into the P02 kit through an OpenAI-compatible /chat/completions endpoint.

Off by default and never called by the tests. Enable it explicitly:
    LLM_BASE_URL=http://localhost:11434/v1 LLM_MODEL=qwen2.5:14b python3 eval_harness.py --system adapter
LLM_BASE_URL works with Ollama, vLLM or a hosted API. LLM_API_KEY is optional and only ever read from the environment.
The model sees the catalogue and the question, never rows. Scope and freshness are added in code, not by the model.
"""
import json
import os
import urllib.request

from semantic_layer import AMBIGUOUS_TERMS, DIMENSIONS, FALLBACK_LABEL, METRICS, TIME_RANGES, Response

PROMPT = f"""You turn a retail manager's question (English, Hindi or Hinglish) into ONE JSON object and nothing else:
{{"kind": "answer" | "clarify" | "refuse", "text": "<short reply>",
 "metric_query": {{...}} or null, "sql": null or "<DuckDB SELECT>"}}
metric_query = {{"metric": one of {sorted(METRICS)}, "dimensions": a subset of {sorted(DIMENSIONS)},
"time_range": one of {list(TIME_RANGES)}, "order": "desc" or null, "limit": an integer or null}}
Rules: ask a clarifying question when a term is ambiguous ({AMBIGUOUS_TERMS}). Refuse data changes, forecasts,
questions about individual people, and requests about regions outside the user's scope. Use "sql" only when no metric
fits (tables: fct_sales_line, fct_returns, dim_store, dim_product, dim_date, dim_region) and never for finance metrics."""


def check_config():
    missing = [k for k in ("LLM_BASE_URL", "LLM_MODEL") if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"adapter disabled: set {', '.join(missing)} (see adapter.py)")


def _chat(messages: list[dict]) -> str:
    headers = {"Content-Type": "application/json"}
    if os.environ.get("LLM_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["LLM_API_KEY"]
    body = json.dumps({"model": os.environ["LLM_MODEL"], "messages": messages}).encode()
    req = urllib.request.Request(os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions", body, headers)
    with urllib.request.urlopen(req, timeout=float(os.environ.get("LLM_TIMEOUT", "60"))) as resp:
        return json.load(resp)["choices"][0]["message"]["content"]


def predict(question: str, user: dict, ctx: dict) -> Response:
    messages = [{"role": "system", "content": PROMPT},
                {"role": "user", "content": f"User scope: {user['scope_label']}\nQuestion: {question}"}]
    out, attempt = None, 0
    for attempt in (1, 2):  # AC-10: at most 2 attempts per question
        raw = _chat(messages)
        try:
            out = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
            break
        except ValueError:
            messages += [{"role": "assistant", "content": raw}, {"role": "user", "content": "Reply with valid JSON only."}]
    if not isinstance(out, dict):
        return Response("clarify", "Sorry, I could not process that. Please rephrase.", attempts=attempt)
    kind, text = out.get("kind", "clarify"), out.get("text", "")
    if kind == "answer":
        fresh = ctx["freshness"]
        text += (f" ({FALLBACK_LABEL})" if out.get("sql") else "") + (
            f" Scope: {user['scope_label']}. Data complete to {fresh['complete_to']}; "
            f"{fresh['partial_date']} is partial ({fresh['partial_load_pct']}% loaded).")
    return Response(kind, text, metric_query=out.get("metric_query"), sql=out.get("sql"), attempts=attempt)
