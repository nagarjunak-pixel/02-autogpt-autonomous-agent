"""Deliberately simple, non-LLM baseline for P06. A real system implements the same methods (adapter.py overrides some):

  triage(msg) -> {"priority", "ae", "flag"}      rules; the AE router must never depend on an LLM
  q_llm(instruction, untrusted_text) -> str      the quarantined reader: returns JSON text, has no tools
  summarise(text) -> str                         quarantined summariser (its output is rendered by render_safe)
  plan(request, var_types, history, pinned) -> [steps]   the privileged planner: never sees message bodies
  compact(history) -> history                    context compaction
  ui_message(plan, outcome) -> str               what the executive is told happened
  schedule(scenario, candidates) -> slot | None  pick one findMeetingTimes candidate

Its weaknesses are on purpose: keyword triage, an AE regex that ignores forwarded text, a reader that obeys the last
address it sees, a planner that reads the mode from history (curveball 3), and a UI that trusts the plan, not the result.
"""
import html
import json
import re

TAG = re.compile(r"<[^>]+>")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
HEADER = re.compile(r"^(From|To|Subject|Reply-To|Organizer|Start):.*$", re.M)
HIGH = re.compile(r"\b(urgent|asap|immediately|today|eod|confidential|board)\b", re.I)
LOW = re.compile(r"unsubscribe|newsletter|webinar|% off|wire transfer|verify your account", re.I)
AE = re.compile(r"adverse event|\bsae\b|serious adverse|side effect|hospitali[sz]", re.I)
FLAG = re.compile(r"ignore (all|previous)|remember:|display:\s*none|color:\s*#fff|approved by legal|forward\b.*\bto\b", re.I)
BODY = {"reply_request": "Thanks for your note. I will come back to you shortly.",
        "meeting_request": "Confirmed. A calendar hold will follow."}


def visible(text: str) -> str:
    """Strip tags and unescape. Hidden text (display:none, white 1-px spans) is kept: that is a known weakness."""
    return html.unescape(TAG.sub(" ", text.replace("<br>", "\n").replace("</p>", "\n")))


def top_part(text: str) -> str:
    """Naive reply stripping: drop forwarded sections and quoted lines. It hides forwarded AE reports."""
    text = text.split("---------- Forwarded message")[0]
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))


def sentences(text: str) -> list:
    return [s.strip() for s in re.split(r"(?<=[.!?।])\s+|\n+", text) if len(s.strip()) > 3]


class BaselineSystem:
    name = "baseline"

    def is_ae(self, text: str) -> bool:
        return bool(AE.search(top_part(visible(text))))

    def triage(self, msg: dict) -> dict:
        raw = msg["subject"] + "\n" + msg["body"]["content"]
        ae = self.is_ae(raw)
        prio = "high" if ae or HIGH.search(visible(raw)) else "low" if LOW.search(raw) else "normal"
        return {"priority": prio, "ae": ae, "flag": bool(FLAG.search(raw))}

    def q_llm(self, instruction: str, untrusted_text: str) -> str:
        keys, body = re.findall(r"'(\w+)'", instruction), visible(HEADER.sub("", untrusted_text))
        hdr = re.search(r"^(?:From|Organizer):.*$", untrusted_text, re.M)
        sender = (EMAIL.findall(hdr.group(0)) or [""])[0] if hdr else ""
        others = [a for a in EMAIL.findall(body) if a.lower() != sender.lower()]
        subject = re.search(r"^Subject: (.*)$", untrusted_text, re.M)
        note = re.search(r"remember:\s*(.+)", body, re.I)
        dur = re.search(r"(\d+)\s*min", body)
        when = re.search(r"\d{4}-\d{2}-\d{2}T[\d:+]+", untrusted_text)
        vals = {"requester_email": (others or [sender])[-1].rstrip("."),  # obeys the last address it sees: gullible on purpose
                "topic": subject.group(1) if subject else "", "duration_min": int(dur.group(1)) if dur else 30,
                "priority": "normal", "reply_needed": "?" in body, "memory_note": note.group(1).strip() if note else "",
                "organiser": sender, "start": when.group(0) if when else ""}
        return json.dumps({k: vals.get(k, "") for k in keys})

    def summarise(self, text: str) -> str:
        sents = sentences(visible(HEADER.sub("", text)))
        return " ".join(dict.fromkeys(sents[:1] + sents[-1:]))  # first and last sentence

    def plan(self, request: str, var_types: dict, history: str = "", pinned=None) -> list:
        """Sees the request, variable names/types and its own history. Ignores `pinned` (curveball 3's root cause)."""
        r, draft_only = request.lower(), bool(re.search(r"draft[-_ ]only", history, re.I))
        if "summar" in r:
            return [{"op": "summarise", "args": {"text": "$msg"}, "out": "summary"}]
        if "triage" in r:  # naive "learn preferences from mail": the policy refuses the memory write
            return [{"op": "extract", "args": {"text": "$msg", "schema": "triage"}, "out": "t"},
                    {"op": "field", "args": {"v": "$t", "key": "memory_note"}, "out": "note"},
                    {"op": "write_memory", "args": {"key": "learned", "value": "$note"}, "out": "m"}]
        schema = "meeting_request" if re.search(r"confirm|schedul|meeting", r) else "reply_request"
        send = not draft_only and "draft" not in r
        return [{"op": "extract", "args": {"text": "$msg", "schema": schema}, "out": "req"},
                {"op": "field", "args": {"v": "$req", "key": "requester_email"}, "out": "to"},
                {"op": "send_email" if send else "create_draft", "args": {"to": ["$to"], "body": BODY[schema]}, "out": "result"}]

    def compact(self, history: list) -> list:
        """Keeps the last three entries; the pinned constraint line is summarised away (curveball 3)."""
        return [f"SUMMARY: {len(history) - 3} earlier entries about routine mail."] + history[-3:] if len(history) > 4 else history

    def ui_message(self, plan: list, outcome: str) -> str:
        ops = {s["op"] for s in plan}
        return "Sent!" if "send_email" in ops else "Draft saved." if "create_draft" in ops else "Done."  # ignores outcome

    def schedule(self, scenario: dict, candidates: list):
        """Checks only the organiser's calendar, in UTC; other attendees' hours and holds are ignored."""
        org = next(a for a in scenario["attendees"] if a["address"] == scenario["organiser"])
        for c in candidates:
            if not any(b[0] < c["end"] and c["start"] < b[1] for b in org["busy"]):
                return c
        return None
