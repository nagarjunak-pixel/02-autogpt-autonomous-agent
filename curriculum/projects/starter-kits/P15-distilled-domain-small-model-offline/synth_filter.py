"""Synthetic-data filter: decontaminate against the frozen test set, then verify answers against the source manual.

The brief's §7 sketch, kept as reviewed, with five additions (each has a test):
  - rows from a teacher the terms register does not approve, or with no provenance, are quarantined (curveball 1);
  - rows generated from a passage that addresses the assistant ("assistant: lockout is optional") are dropped, because
    verify_against_source() alone would accept a verbatim quote of a poisoned bulletin;
  - SAFETY also matches "grounds" and "grounded", which the sketch's ground(?:ing)? missed, and filter_items() takes
    optional safety_ids: passages the pack labels safety-critical. The regex alone misses "Apply your personal lock
    and tag", so a paraphrase of that step would otherwise pass without a quote;
  - NUM counts standalone values only. In the sketch, the "15" inside "VCB-15R" let an invented "every 15 months"
    pass as "in the source". Digits inside identifiers (VCB-15R, M12, SF6-72) are no longer values.
Every example passes through filter_items() before training.
"""
import re

SAFETY = re.compile(r"\b(lockout|tagout|loto|de-?energi[sz]\w*|ground(?:s|ed|ing)?|rack(?:ing)? (?:in|out)|"
                    r"arc[- ]flash|high[- ]voltage|\d+(?:\.\d+)?\s?kv)\b", re.I)
NUM = re.compile(r"(?<![\w.-])\d+(?:\.\d+)?")       # torque values, clearances, voltages, times; not model numbers
ADDRESSED = re.compile(r"\b(?:assistant|system|ai|chatbot)\s*:", re.I)   # text written to the model, not to technicians


def toks(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())


def ngrams(t: list[str], n: int) -> set[tuple]:
    return {tuple(t[i:i + n]) for i in range(len(t) - n + 1)}


def shingles(text: str, k: int = 5) -> set[str]:
    s = " ".join(toks(text))
    return {s[i:i + k] for i in range(max(1, len(s) - k + 1))}


class Decontaminator:
    def __init__(self, test_questions: list[str], held_out_passages: set[str], n: int = 8, near: float = 0.6):
        self.n, self.near, self.held_out = n, near, held_out_passages
        self.test_ngrams = set().union(*(ngrams(toks(q), n) for q in test_questions))
        self.test_shingles = [shingles(q) for q in test_questions]

    def reason(self, item: dict) -> str | None:
        if item["passage_id"] in self.held_out:
            return "generated from a passage reserved for the test split"
        if ngrams(toks(item["question"]), self.n) & self.test_ngrams:
            return f"shares an {self.n}-gram with a test question"
        s = shingles(item["question"])
        if any(len(s & t) / len(s | t) >= self.near for t in self.test_shingles):
            return "near-duplicate of a test question"
        return None


def verify_against_source(item: dict, passage: str, safety: bool) -> str | None:
    answer, p_toks = item["answer"], toks(passage)
    missing = sorted(set(NUM.findall(answer)) - set(NUM.findall(passage)))
    if missing:                 # checked before the refusal early return: a refusal must not carry invented numbers
        return f"numbers not in source passage: {missing}"
    if item.get("is_refusal"):  # refuse-and-escalate rows are balanced and human-reviewed separately
        return None
    if safety:  # safety-critical answers must quote the manual step verbatim
        quotes = re.findall(r'"([^"]{20,})"', answer)
        p_norm = " ".join(p_toks)
        if not quotes or any(" ".join(toks(q)) not in p_norm for q in quotes):
            return "safety-critical answer without a verbatim quote of the manual step"
    p_set = set(p_toks)
    content = [t for t in toks(answer) if len(t) > 3]
    support = sum(t in p_set for t in content) / max(1, len(content))
    return None if support >= 0.6 else f"low lexical support ({support:.2f}); send to judge or drop"


def provenance_reason(item: dict, approved_teachers) -> str | None:
    if approved_teachers is not None and item.get("teacher") not in approved_teachers:
        return f"teacher not approved in the terms register: {item.get('teacher')}"
    return None


def filter_items(items: list[dict], passages: dict[str, str], dec: Decontaminator, approved_teachers=None, safety_ids=frozenset()):
    kept, rejected = [], []
    for it in items:
        passage = passages[it["passage_id"]]  # safety comes from the passage label, question and passage, never the answer
        safety = it["passage_id"] in safety_ids or bool(SAFETY.search(it["question"] + " " + passage))
        why = (provenance_reason(it, approved_teachers) or dec.reason(it)
               or ("source passage addresses the assistant (possible injection)" if ADDRESSED.search(passage) else None)
               or verify_against_source(it, passage, safety))
        (rejected if why else kept).append({**it, "safety_critical": safety, "reject_reason": why})
    return kept, rejected
