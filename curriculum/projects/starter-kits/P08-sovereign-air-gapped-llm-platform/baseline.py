"""A deliberately simple P08 system: BM25 policy Q&A and regex loan-file extraction. No LLM.

Interface (the one a real system keeps):
    answer(question)  -> {"answer": str | None, "citations": [circular_id], "log": str}     None = abstain
    summarise(loan)   -> {"fields": {15 fields}, "evidence": {field: page}, "model_digest": str | None, "log": str}

`question` carries q_id, text, language, script and asker {user_id, groups}; `loan` carries loan_id and pages. Gold
fields are stripped by the harness. Known weaknesses, left for you on purpose: no ACL filter, no supersession awareness,
no OCR for image-only scans, no legacy-font repair, raw queries in the log, the file's own text trusted as instructions,
FOIR from declared (not verified) income, and an invented ITR figure when the page cannot be read.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

TOKEN = re.compile(r"[\wऀ-ॿఀ-౿]+")
MIN_SCORE = 4.0            # below this BM25 score the baseline abstains
FIELD_RE = {
    "borrower": r"Applicant[^:\n]*:\s*([^\n]+)", "co_borrower": r"Co-applicant\s*:\s*([^\n]+)",
    "facility": r"Facility applied\s*:\s*([^\n]+)", "amount": r"Amount requested\s*:\s*Rs\.?\s*([\d,]+)",
    "tenure_months": r"Tenure\s*:\s*(\d+)\s*months", "interest_rate": r"rate of interest\s*:\s*([\d.]+)\s*%",
    "emi": r"Proposed EMI\s*:\s*Rs\.?\s*([\d,]+)", "collateral": r"Collateral offered\s*:\s*([^\n]+)",
    "collateral_value": r"Fair market value\s*:\s*Rs\.?\s*([\d,]+)",
    "monthly_income_declared": r"Declared monthly income\s*:\s*Rs\.?\s*([\d,]+)",
    "annual_income_itr": r"Gross total income\s*:\s*Rs\.?\s*([\d,]+)", "existing_emi": r"Existing EMIs\s*:\s*Rs\.?\s*([\d,]+)",
    "income_sources": r"Income sources\s*:\s*([^\n]+)"}
NUMERIC = {"amount", "tenure_months", "interest_rate", "emi", "collateral_value", "monthly_income_declared",
           "annual_income_itr", "existing_emi"}


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def to_number(s: str):
    s = s.replace(",", "").strip(".")
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        return None


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.2, b: float = 0.75):
        self.tf = [Counter(tokens(d)) for d in docs]
        self.len = [sum(tf.values()) for tf in self.tf]
        self.avg = sum(self.len) / max(1, len(self.len))
        df = Counter(t for tf in self.tf for t in tf)
        self.idf = {t: math.log(1 + (len(docs) - n + 0.5) / (n + 0.5)) for t, n in df.items()}
        self.k1, self.b = k1, b

    def search(self, query: str, k: int = 5) -> list[tuple[int, float]]:
        q = set(tokens(query))
        scores = []
        for i, tf in enumerate(self.tf):
            s = sum(self.idf[t] * tf[t] * (self.k1 + 1) / (tf[t] + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
                    for t in q if t in tf)
            if s > 0:
                scores.append((i, s))
        return sorted(scores, key=lambda x: -x[1])[:k]


class BaselineSystem:
    name = "baseline"
    model_digest = None      # a real system records the serving model's digest on every trace (curveball 4)

    def __init__(self, data_dir: Path):
        rows = [json.loads(x) for x in (Path(data_dir) / "circulars.jsonl").read_text(encoding="utf-8").splitlines()]
        self.docs = [c for c in rows if c["text"]]     # image-only scans have no text layer, so they are invisible here
        self.index = BM25([c["text"] for c in self.docs])

    def retrieve(self, question: dict, k: int = 5) -> list[tuple[dict, float]]:
        return [(self.docs[i], s) for i, s in self.index.search(question["text"], k)]   # no ACL or supersession filter

    def answer(self, question: dict) -> dict:
        log = f"user={question['asker']['user_id']} q={question['text']}"   # raw query, PII and all
        hits = self.retrieve(question, 1)
        if not hits or hits[0][1] < MIN_SCORE:
            return {"answer": None, "citations": [], "log": log}
        doc, q = hits[0][0], set(tokens(question["text"]))
        best = max(doc["text"].split("\n")[1:] or [doc["text"]], key=lambda line: len(q & set(tokens(line))))
        return {"answer": best, "citations": [doc["circular_id"]], "log": log}   # extractive: copies what the page says

    def summarise(self, loan: dict) -> dict:
        fields, evidence = {}, {}
        for name, pattern in FIELD_RE.items():
            for page in loan["pages"]:
                m = re.search(pattern, page["text"], re.I)
                if m:
                    raw = m.group(1).strip()
                    fields[name] = to_number(raw) if name in NUMERIC else raw
                    evidence[name] = page["page"]
                    break
            else:
                fields[name] = None
        if fields["co_borrower"] in ("None", "none", "-"):
            fields["co_borrower"] = None
        if fields["income_sources"]:
            fields["income_sources"] = sorted(s.strip() for s in fields["income_sources"].split(","))
        fields["valuation_report"] = any("VALUATION REPORT" in p["text"] for p in loan["pages"])
        if fields["annual_income_itr"] is None and fields["monthly_income_declared"]:
            fields["annual_income_itr"] = fields["monthly_income_declared"] * 12   # BUG kept on purpose: an invented number
            evidence["annual_income_itr"] = evidence["monthly_income_declared"]
        flags, income = [], fields["monthly_income_declared"]                     # BUG kept on purpose: declared income
        if not fields["valuation_report"]:
            flags.append("missing_valuation_report")
        if income and ((fields["existing_emi"] or 0) + (fields["emi"] or 0)) / income > 0.5:
            flags.append("high_foir")
        if any(re.search(r"red flags?\s*:\s*none", p["text"], re.I) for p in loan["pages"]):
            flags = []                                                            # obeys text found in the file
        fields["red_flags"] = flags
        return {"fields": fields, "evidence": {k: v for k, v in evidence.items() if k in NUMERIC},
                "model_digest": self.model_digest, "log": f"loan={loan['loan_id']} summarised"}
