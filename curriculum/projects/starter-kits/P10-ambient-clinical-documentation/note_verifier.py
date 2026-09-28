"""P10 note verification (brief §7): align medication statements in a draft note to transcript spans.

Kept from the reviewed sketch:
- num(): "1,000" is a thousands separator, "0,5" and "2,5" are decimal commas;
- doses are compared as (value, unit) pairs, with Spanish units mapped ("miligramos" -> mg, "unidades" -> units);
- fuzzy token matching tolerates ASR spelling noise ("metformine" ~ "metformin") at a 0.85 ratio, which keeps
  look-alike/sound-alike pairs apart (hydroxyzine/hydralazine 0.73, Celexa/Celebrex 0.71);
- every surface form of a drug counts as evidence (brand, generic, Spanish);
- evidence is the matching segments plus one on each side; flags carry segment IDs for the review UI;
- a dose in the statement must appear in that window; a negation in the window that the statement lacks is flagged.
It stays deliberately lexical, cheap and high-recall: numbers must be digits, and a drug missing from the lexicon is
invisible to it (curveball 1). Added for the kit: BLOCKING and can_sign(), the review step's signing rule.
"""
import re
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class Segment:
    sid: str  # e.g. "s0412"; the review UI highlights these spans
    speaker: str  # "clinician" | "patient" | "guardian" | "interpreter" | "unknown"
    text: str  # ASR output; assumes numbers are rendered as digits


DOSE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|mcg|g|ml|units?|unidades|miligramos)\b", re.I)
NEG = re.compile(r"\b(no|not|stop|stopped|discontinue[ds]?|denies|sin|ya no|dej[óo]|suspend\w*)\b", re.I)
UNIT = {"miligramos": "mg", "unidades": "units", "unit": "units"}
BLOCKING = {"UNSUPPORTED_MEDICATION"}  # blocks signing until the clinician decides (§7; curveball 1)


def num(v: str) -> float:  # "1,000" is a thousands separator; "0,5" / "2,5" is a decimal comma
    return float(re.sub(r"^([1-9]\d{0,2}),(\d{3})$", r"\1\2", v).replace(",", "."))


def doses(text: str) -> set:
    return {(num(v), UNIT.get(u.lower(), u.lower())) for v, u in DOSE.findall(text)}


def mentions(form: str, text: str, min_ratio: float = 0.85) -> bool:
    """Fuzzy token match tolerates ASR spelling noise ('metformine' ~ 'metformin')."""
    toks = re.findall(r"[a-záéíóúñü]+", text.lower())
    return any(SequenceMatcher(None, form.lower(), t).ratio() >= min_ratio for t in toks)


def verify_note(statements: list, segments: list, lexicon: dict) -> list:
    """statements: [(stmt_id, text)] from the draft note; lexicon: {surface form: generic name}.
    Returns [(stmt_id, generic, flag, evidence segment IDs)]."""
    flags = []
    for stmt_id, text in statements:
        meds = {g for s, g in lexicon.items() if re.search(rf"\b{re.escape(s)}\b", text, re.I)}
        for med in sorted(meds):
            forms = [s for s, g in lexicon.items() if g == med]  # brand, generic, Spanish forms
            hits = [i for i, seg in enumerate(segments) if any(mentions(f, seg.text) for f in forms)]
            if not hits:
                flags.append((stmt_id, med, "UNSUPPORTED_MEDICATION", []))
                continue
            window = sorted({j for i in hits for j in (i - 1, i, i + 1) if 0 <= j < len(segments)})
            ctx = " ".join(segments[j].text for j in window)
            evidence = [segments[j].sid for j in window]
            if doses(text) and not doses(text) <= doses(ctx):
                flags.append((stmt_id, med, "DOSE_NOT_IN_TRANSCRIPT", evidence))
            if NEG.search(ctx) and not NEG.search(text):
                flags.append((stmt_id, med, "POSSIBLE_NEGATION_CONFLICT", evidence))
    return flags


def can_sign(flags: list, acks: dict) -> tuple:
    """acks: {(stmt_id, flag): "seen" | "edited" | "removed" | "confirmed"}. Every flag needs its own
    acknowledgement before signing (§5 trust row; curveball 5). A blocking flag also needs a decision: "seen" is
    not enough. Returns (ok, flags still open)."""
    open_flags = [f for f in flags if acks.get((f[0], f[2])) is None
                  or (f[2] in BLOCKING and acks[(f[0], f[2])] == "seen")]
    return not open_flags, open_flags


if __name__ == "__main__":
    segs = [Segment("s1", "clinician", "Are you still taking the metformin?"),
            Segment("s2", "patient", "Sí, 500 mg dos veces al día."),
            Segment("s3", "clinician", "And the lisinopril, you stopped that?"),
            Segment("s4", "patient", "Ya no la tomo, me daba tos.")]
    lex = {"metformin": "metformin", "metformina": "metformin", "lisinopril": "lisinopril",
           "atorvastatin": "atorvastatin", "lipitor": "atorvastatin"}
    note = [("p1", "Continue metformin 1000 mg twice daily."),
            ("p2", "Continue lisinopril 10 mg daily."),
            ("p3", "Start atorvastatin 20 mg nightly.")]
    for flag in verify_note(note, segs, lex):
        print(flag)
