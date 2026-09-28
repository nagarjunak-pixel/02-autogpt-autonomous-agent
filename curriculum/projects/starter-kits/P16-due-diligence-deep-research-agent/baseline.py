"""Deliberately simple, non-LLM baseline for P16: keyword retrieval, an extractive writer and a word-overlap judge.

It is meant to fail several acceptance criteria. adapter.py and your own system implement the same interface:
  policy(page) -> (allow, reason)       the fetch gateway's decision for one web page or licensed record
  research(task, env) -> Draft          plan -> search -> read -> write, using only the env tools
  judge(evidence, claim) -> (label, confidence)   called by citation_verifier.verify on every sentence
"""
import re
from dataclasses import dataclass, field

from citation_verifier import CITE, NUMBER

SECTION_WORDS = {"financial": ("revenue", "ebitda", "margin", "debt"), "customer": ("customer",),
                 "market": ("market", "sites"), "management": ("chief executive",), "ESG": ("emissions",),
                 "legal": ("trademark",), "red_flag": ("claim", "disput", "notice", "terminated")}
STOP = {"the", "a", "an", "of", "in", "for", "on", "to", "and", "by", "at", "as"}
NEGATION = re.compile(r"\b(not|no|never|cannot)\b")


@dataclass
class Draft:
    sentences: list[str]                                      # each carries citations such as [S12]
    conflicts: list[list[str]] = field(default_factory=list)  # pairs of passage ids that disagree
    cost_usd: float = 0.0                                     # model spend; the harness adds search and fetch costs


def policy(page: dict) -> tuple[bool, str]:
    """Fetch gateway that honours robots.txt only: Content-Signal, RSL, paywalls, logins and licences are ignored."""
    if page.get("robots") == "disallow":
        return False, "robots.txt disallows AI agents"
    return True, "robots.txt allows"


def gather(task: dict, env) -> dict[str, str]:
    """Plan, search and read. The query names the target (no query filter) and the CRM search has no wall check."""
    texts = {p["pid"]: p["text"] for p in env.vdr()}
    for hit in env.search(f"{task['short']} {task['question']}"):
        texts[hit["pid"]] = env.fetch(hit["pid"]) or hit["snippet"]  # bug on purpose: falls back to the snippet
    for note in env.crm(f"{task['short']} {task['question']}"):
        texts[note["pid"]] = note["text"]
    return texts


def write(task: dict, texts: dict[str, str]) -> list[str]:
    """Extractive writer: copies every sentence with a number and a section keyword, citing its passage."""
    sections = [task["section"]] if task.get("section") else list(SECTION_WORDS)
    words = [w for s in sections for w in SECTION_WORDS[s]]
    return [f"{s.strip()} [{pid}]" for pid, text in texts.items() for s in re.split(r"(?<=[.!?।])\s+", text)
            if re.search(r"\d", s) and any(w in s.lower() for w in words)]


def find_conflicts(sentences: list[str], vdr_pids: set[str]) -> list[list[str]]:
    """Same topic, different numbers, inside the data room only: there is no counter-search on the web."""
    by_topic: dict[str, list] = {}
    for s in sentences:
        pid, body = CITE.findall(s)[0], CITE.sub("", s).lower()
        topic = next((t for t in ("revenue", "customers", "sites", "margin") if t in body), None)
        if topic and pid in vdr_pids:
            by_topic.setdefault(topic, []).append((pid, set(NUMBER.findall(body))))
    return [[a, b] for group in by_topic.values() for i, (a, na) in enumerate(group)
            for b, nb in group[i + 1:] if a != b and na != nb]


def research(task: dict, env) -> Draft:
    sentences = write(task, gather(task, env))
    return Draft(sentences, find_conflicts(sentences, env.vdr_pids))


def _words(s: str) -> set[str]:
    return set(re.findall(r"[^\W_]+", s.lower())) - STOP


def judge(evidence: str, claim: str) -> tuple[str, float]:
    """Word-overlap stand-in for an NLI checker: share of claim words in the evidence, plus a crude negation test."""
    c = _words(claim)
    overlap = len(c & _words(evidence)) / len(c) if c else 0.0
    if overlap >= 0.5 and bool(NEGATION.search(claim.lower())) != bool(NEGATION.search(evidence.lower())):
        return "contradicted", overlap
    return ("entailed" if overlap >= 0.8 else "neutral"), overlap
