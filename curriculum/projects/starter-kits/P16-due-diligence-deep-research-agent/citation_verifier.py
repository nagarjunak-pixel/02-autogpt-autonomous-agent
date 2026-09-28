"""Citation verifier from brief §7: every memo sentence must be supported by passages our own fetcher actually retrieved.

Every draft sentence goes through verify() before an analyst sees it. It strips sentences with no citation, with any
citation that was never accessed or belongs to another deal, or with unsupported or contradicted evidence. It flags
supported sentences whose quote or number does not match verbatim; the analyst decides.
"""
import re
from dataclasses import dataclass, field
from typing import Literal, Protocol

Label = Literal["entailed", "neutral", "contradicted"]


class Judge(Protocol):  # an NLI model, a MiniCheck-style checker or a pinned LLM judge
    def judge(self, evidence: str, claim: str) -> tuple[Label, float]: ...


@dataclass(frozen=True)
class Passage:
    pid: str
    text: str
    url: str
    deal_id: str
    retrieved: bool  # True only if the fetch log shows a successful retrieval by our own tools


@dataclass
class Verdict:
    sentence: str
    action: Literal["keep", "flag", "strip"]
    reasons: list[str] = field(default_factory=list)


CITE = re.compile(r"\[(S\d+)\]")
QUOTE = re.compile(r"[\"“]([^\"”]{12,})[\"”]")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("’", "'").replace(",", "")).strip().lower()


def verify(sentence: str, store: dict[str, Passage], deal_id: str, judge: Judge, min_conf: float = 0.8) -> Verdict:
    claim, ids, reasons = CITE.sub("", sentence).strip(), CITE.findall(sentence), []
    if not ids:
        return Verdict(sentence, "strip", ["no citation"])
    cited = []
    for pid in ids:
        p = store.get(pid)
        if p is None or not p.retrieved:
            reasons.append(f"{pid}: no retrieval record (cited but never accessed)")
        elif p.deal_id != deal_id:
            reasons.append(f"{pid}: belongs to another deal (information barrier)")
        else:
            cited.append(p)
    if reasons:  # one bad citation is enough: never-accessed or cross-deal evidence is not allowed
        return Verdict(sentence, "strip", reasons)
    evidence = "\n\n".join(p.text for p in cited)
    numbers = {norm(n) for n in NUMBER.findall(evidence)}  # whole numbers, so "2.5" does not match "12.5"
    reasons += [f"quote not verbatim: {q[:40]}" for q in QUOTE.findall(claim) if norm(q) not in norm(evidence)]
    reasons += [f"number {n} not in cited text" for n in NUMBER.findall(claim) if norm(n) not in numbers]
    label, conf = judge.judge(evidence, claim)
    if label == "contradicted":
        return Verdict(sentence, "strip", reasons + [f"contradicted by cited source ({conf:.2f})"])
    if label == "neutral" or conf < min_conf:
        return Verdict(sentence, "strip", reasons + [f"not supported ({label}, {conf:.2f})"])
    return Verdict(sentence, "flag" if reasons else "keep", reasons)
