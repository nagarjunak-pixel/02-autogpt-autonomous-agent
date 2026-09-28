"""P06 control: quarantined reader plus data-flow policy (brief §7), with the pinned-constraint check from §6.

The planner sees only the trusted request and variable names/types. Every value carries provenance (Val.sources)
and sensitivity labels (Val.labels). The interpreter, not a model, decides which values may reach which tools:
  - send_email works only in internal-auto-send mode (draft-only, read-only and unknown modes fail closed);
  - it blocks external recipients, MNPI-labelled bodies and recipients derived from untrusted data;
  - drafts are allowed, but recipients from message content are flagged, and bodies are rendered without links/images;
  - there are no delete, move, forward or memory tools in a plan; memory is written only from the executive's UI;
  - the mode comes from the pinned store, and a missing or altered block fails closed to read-only;
  - an engaged kill switch denies every call, and a refused scope (curveball 1) denies the tool that needs it.
"""
import hashlib
import json
import re
from dataclasses import dataclass

INTERNAL_DOMAINS = {"helixtx.example"}
TRUSTED = {"user", "directory"}          # the exec's own request; the Entra directory


@dataclass(frozen=True)
class Val:                               # every value carries its provenance
    data: object
    sources: frozenset
    labels: frozenset = frozenset()      # sensitivity labels such as "MNPI"; they travel with the value

    def trusted(self) -> bool:
        return bool(self.sources) and self.sources <= TRUSTED   # no provenance is not trusted


class PolicyViolation(Exception):
    pass


SCHEMAS = {"meeting_request": {"requester_email": str, "topic": str, "duration_min": int},
           "reply_request": {"requester_email": str, "topic": str},
           "triage": {"priority": str, "reply_needed": bool, "memory_note": str},
           "invite": {"organiser": str, "start": str, "topic": str}}        # curveball 4: time, organiser, topic only
READ_OPS = {"extract", "field", "summarise", "sender_of", "lookup_directory", "find_meeting_times"}
WRITE_OPS = {"create_draft", "send_email"}                                   # no delete, move, forward or memory tool
TOOL_SCOPES = {"extract": "Mail.Read", "summarise": "Mail.Read", "sender_of": "Mail.Read", "lookup_directory": "User.Read",
               "find_meeting_times": "Calendars.Read.Shared", "create_draft": "Mail.ReadWrite", "send_email": "Mail.Send"}
LINKS = re.compile(r"!\[[^\]]*\]\([^)]*\)|<img\b[^>]*>|\[([^\]]*)\]\([^)]*\)|\b(?:https?|ftp)://\S+|\bwww\.\S+", re.I)
TAG_CHARS = dict.fromkeys(range(0xE0000, 0xE0080))                          # invisible Unicode tag characters


def quarantined_extract(q_llm, untrusted_text: str, schema: str, source: str, labels=frozenset()) -> Val:
    """Q-LLM: sees untrusted text, has no tools, output is parsed and type-checked, never obeyed."""
    spec = SCHEMAS[schema]
    try:
        obj = json.loads(q_llm(f"Return only JSON with keys {sorted(spec)}.", untrusted_text))
    except (TypeError, ValueError) as e:
        raise PolicyViolation(f"unparseable output from {source}") from e
    # type(...) is t, not isinstance: True must not pass as an int
    if not isinstance(obj, dict) or set(obj) != set(spec) or not all(type(obj[k]) is t for k, t in spec.items()):
        raise PolicyViolation(f"schema mismatch from {source}")
    return Val(obj, frozenset({source}), frozenset(labels))


def field(v: Val, key: str) -> Val:      # projections keep the parent's provenance and labels
    return Val(v.data[key], v.sources, v.labels)


def is_internal(addr: str) -> bool:
    m = re.fullmatch(r"[^@\s]+@([a-z0-9.-]+)", str(addr).strip().lower())
    return bool(m) and m.group(1) in INTERNAL_DOMAINS


def render_safe(text) -> str:
    """The summary and draft renderer: no remote images, links or invisible tag characters (EchoLeak-class channel)."""
    return LINKS.sub(lambda m: m.group(1) or "[link removed]", str(text).translate(TAG_CHARS))


def _recipients(to) -> list:
    out = []
    for r in to if isinstance(to, list) else [to]:
        if not isinstance(r, Val):
            raise PolicyViolation("recipient without provenance")
        out += [Val(d, r.sources, r.labels) for d in r.data] if isinstance(r.data, list) else [r]
    if not out:
        raise PolicyViolation("no recipients")
    return out


def send_email(to: list, body: Val, mode: str, approved: bool = False) -> list:
    if mode != "internal_auto_send":     # pinned constraint enforced in code; unknown modes fail closed
        raise PolicyViolation(f"send is disabled in {mode} mode")
    if not isinstance(body, Val) or "MNPI" in body.labels:
        raise PolicyViolation("MNPI-labelled or unlabelled content is never sent automatically")
    rcpts = _recipients(to)
    for r in rcpts:
        if not is_internal(str(r.data)):  # external sending stays human, even when approved
            raise PolicyViolation(f"external recipient blocked: {r.data}")
        if not r.trusted() and not approved:
            raise PolicyViolation(f"recipient came from untrusted data {sorted(r.sources)}")
    return [str(r.data).strip().lower() for r in rcpts]


def draft_email(to: list, body: Val, mode: str) -> dict:
    """Drafts need a human to press Send, so content-derived recipients are allowed but flagged in the UI."""
    if mode not in ("draft_only", "internal_auto_send"):
        raise PolicyViolation(f"drafting is disabled in {mode} mode")
    rcpts = _recipients(to)
    flags = [f"recipient from message content: {r.data}" for r in rcpts if not r.trusted()]
    flags += [f"external recipient, a human must send: {r.data}" for r in rcpts if not is_internal(str(r.data))]
    flags += ["contains MNPI"] if "MNPI" in getattr(body, "labels", ()) else []
    return {"to": [str(r.data).strip().lower() for r in rcpts], "body": render_safe(getattr(body, "data", body)), "flags": flags}


def write_memory(store: dict, key: str, value: Val, channel: str) -> None:
    """Preference memory: only from the executive's own UI, only trusted values (brief §9 memory writer)."""
    if channel != "exec_ui" or not isinstance(value, Val) or not value.trusted():
        raise PolicyViolation(f"memory write refused (channel={channel})")
    store[key] = {"value": value.data, "sources": sorted(value.sources)}


def pinned_hash(block: dict) -> str:
    return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()


def pinned_mode(block, expected_hash: str) -> str:
    """The mode comes from the pinned store, never from history; missing or altered means read-only."""
    if not isinstance(block, dict) or pinned_hash(block) != expected_hash:
        return "read_only"
    return block.get("mode", "read_only")


def resolve(x, env: dict):
    if isinstance(x, str) and x.startswith("$"):
        if x[1:] not in env:
            raise PolicyViolation(f"unknown variable {x}")
        return env[x[1:]]
    return [resolve(i, env) for i in x] if isinstance(x, list) else x


def _lit(x):                             # plan literals come from the P-LLM, which saw only the trusted request
    return [_lit(i) for i in x] if isinstance(x, list) else x if isinstance(x, Val) else Val(x, frozenset({"user"}))


def run_plan(plan: list, env: dict, tools: dict, pinned: dict, expected_hash: str, granted=None,
             kill_switch=lambda: False, audit=None) -> dict:
    """Plan comes from the P-LLM, which saw only the user request and variable names/types."""
    audit = [] if audit is None else audit
    mode = pinned_mode(pinned, expected_hash)
    for step in plan:
        op = step.get("op")
        try:
            if kill_switch():
                raise PolicyViolation("kill switch engaged: every call is denied")
            if op not in READ_OPS | WRITE_OPS:
                raise PolicyViolation(f"no such tool: {op}")
            if granted is not None and op in TOOL_SCOPES and TOOL_SCOPES[op] not in granted:
                raise PolicyViolation(f"{op} needs {TOOL_SCOPES[op]}, which is not granted")
            args = {k: resolve(v, env) for k, v in step.get("args", {}).items()}
            if op == "field":
                out = field(args["v"], args["key"])
            elif op == "send_email":     # approved is never read from a plan: only a UI click can approve
                body = _lit(args["body"])
                out = tools["send_email"](to=send_email(_lit(args.get("to", [])), body, mode), body=render_safe(body.data))
            elif op == "create_draft":
                out = tools["create_draft"](**draft_email(_lit(args.get("to", [])), _lit(args["body"]), mode))
            else:
                out = tools[op](**args)
            if op == "summarise" and isinstance(out, Val):
                out = Val(render_safe(out.data), out.sources, out.labels)
            env[step["out"]] = out if isinstance(out, Val) else Val(out, frozenset({f"tool:{op}"}))  # unlabelled = untrusted
            audit.append({"op": op, "decision": "allow"})
        except PolicyViolation as e:
            audit.append({"op": op, "decision": "deny", "reason": str(e)})
            raise
    return env
