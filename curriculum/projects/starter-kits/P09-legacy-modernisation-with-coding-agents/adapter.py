"""Plug a real coding model into P09 through any OpenAI-compatible /chat/completions endpoint.

Never used by tests or default runs. Enable it explicitly:
    export LLM_BASE_URL=http://localhost:11434/v1   # Ollama or vLLM (set the context length!), or a hosted API
    export LLM_MODEL=qwen2.5-coder:32b
    export LLM_API_KEY=...                           # only if the endpoint needs one; never hard-code it
    python3 eval_harness.py --system adapter --runs 3

Each run asks the model for a complete candidate engine (one Python file that speaks the §7 JSONL protocol),
saves it as results/candidates/run<N>.py, and the harness scores it against the legacy oracle.
The model sees only spec_stub.md and the rate-table header. It never sees fixtures, the golden answer key,
masked production data or tests: the oracle stays hidden (brief §9 and §15).

This single call stands in for a coding agent. The harness RUNS model-written code as a subprocess with a
timeout, which is NOT a sandbox: do this only inside a disposable container or VM with no secrets and no
network egress (brief §6 zone 2). Stdlib only (urllib).
"""
import json
import os
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPT = """Write ONE self-contained Python 3.11 script (standard library only) implementing this premium engine.
It must read one JSON policy per line from stdin and print exactly one JSON result per line to stdout.
Take the rate-table CSV path from a --rates command-line argument.
The legacy system's output is authoritative. Where this summary is ambiguous, say so in a comment; do not guess silently.
Reply with the code only, in one ```python block.

{spec}

Rate table header: {header}
"""


def chat(messages, temperature=0.2, timeout=300):
    missing = [v for v in ("LLM_BASE_URL", "LLM_MODEL") if not os.environ.get(v)]
    if missing:
        raise SystemExit(f"--system adapter needs these environment variables: {', '.join(missing)}")
    body = json.dumps({"model": os.environ["LLM_MODEL"], "messages": messages, "temperature": temperature}).encode()
    headers = {"Content-Type": "application/json"}
    if os.environ.get("LLM_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["LLM_API_KEY"]
    req = urllib.request.Request(os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions", data=body,
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)["choices"][0]["message"]["content"]


def write_candidate(path: Path) -> Path:
    """Ask the model for an engine and save it. Returns the path for the harness to run."""
    header = (HERE / "data" / "rate_table.csv").read_text().splitlines()[0]
    reply = chat([{"role": "user", "content": PROMPT.format(spec=(HERE / "spec_stub.md").read_text(), header=header)}])
    match = re.search(r"```(?:python)?\n(.*?)```", reply, re.S)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(match.group(1) if match else reply, encoding="utf-8")
    return path
