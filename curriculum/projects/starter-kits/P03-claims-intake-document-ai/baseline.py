"""A deliberately simple, non-LLM baseline for P03: keyword page router, regex extractors, uncalibrated confidence.

    from baseline import BaselineSystem
    out = BaselineSystem("data").predict(packet)
    # {"fields": {name: Field}, "routes": {name: route}, "conflicts": [...], "fcu_flags": [...],
    #  "tamper_flags": [...], "status": one of review_router.STATUSES}

Validation, routing, fraud flags and status come from review_router (the brief's §7 control); keep them when you
replace this. Weaknesses on purpose: it reads the PDF text layer when there is one (so white-on-white text gets in)
and never diffs it against OCR; it ignores XMP and letterheads; it knows English and Marathi labels but not Hindi;
it does not normalise Devanagari numerals or deskew rotated pages; and it treats OCR confidence as calibrated.
"""
import json
import re
from datetime import datetime
from pathlib import Path

import review_router as rr

HERE = Path(__file__).resolve().parent
PAGE_TYPES = [("bill", r"BILL|INVOICE|बिल"), ("discharge", r"DISCHARGE|डिस्चार्ज"), ("fir", r"FIR|FIRST INFORMATION"),
              ("rc", r"REGISTRATION CERTIFICATE"), ("form", r"CLAIM FORM|दावा")]
NUM = r"₹?\s*([0-9०-९][0-9०-९,]*)"
PATTERNS = {  # English and Marathi labels only; first match wins
    "bill": {"invoice_no": r"(?:bill no|invoice no|bill number|बिल क्रमांक)\s*:\s*([A-Z]{2,4}-\w+)",
             "total_billed": r"(?:total|amount|एकूण)[^0-9०-९₹]{0,20}" + NUM},
    "discharge": {"patient_name": r"(?:patient name|रुग्णाचे नाव)\s*:\s*(.+)",
                  "admission_date": r"(?:date of admission|दाखल दिनांक)\s*:\s*(.+)",
                  "discharge_date": r"(?:date of discharge|डिस्चार्ज दिनांक)\s*:\s*(.+)"},
    "form": {"policy_no": r"(?:policy no|पॉलिसी क्रमांक)\s*:\s*(\S+)", "loss_date": r"date of loss\s*:\s*(.+)",
             "claimed_amount": r"(?:amount claimed|estimate|दावा रक्कम)\s*:\s*" + NUM},
    "fir": {"fir_no": r"(?:fir no|एफआयआर क्र\.)\s*:\s*(\S+)", "fir_date": r"^(?:date|दिनांक)\s*:\s*(.+)",
            "fir_reg_no": r"(?:vehicle no|वाहन क्रमांक)\s*:\s*(.+)"},
    "rc": {"vehicle_reg_no": r"regn\. no\s*:\s*(.+)"}}
REQUIRED = {"health": ["policy_no", "patient_name", "invoice_no", "total_billed", "admission_date", "discharge_date",
                       "claimed_amount"],
            "motor": ["policy_no", "vehicle_reg_no", "fir_no", "fir_date", "fir_reg_no", "loss_date", "claimed_amount"]}
LINE_ITEM = re.compile(r"\.{2,}\s*₹\s*([0-9०-९][0-9०-९,]*)\s*$")
INSTRUCTION = re.compile(r"approve|ignore (?:all|previous)|SYSTEM:|set total", re.I)


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def iso(text):
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d %b %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return text.strip()  # unparsed: the schema check will catch it


def clean(name, raw):
    if name.endswith("_date"):
        return iso(raw)
    return raw.replace(" ", "") if name.endswith("reg_no") else raw.strip()


class BaselineSystem:
    name = "baseline"

    def __init__(self, data_dir=HERE / "data"):
        self.policies = {p["policy_no"]: p for p in load_jsonl(Path(data_dir) / "policies.jsonl")}
        self.seen_bills = set()  # cross-claim state for the duplicate-bill signal

    def extract_page(self, kind, lines):
        """{field: (value, line_index, confidence)} for one routed page. Replace this with your extractor."""
        out = {}
        for i, (text, _bbox, conf) in enumerate(lines):
            for fname, rx in PATTERNS.get(kind, {}).items():
                if fname not in out and (m := re.search(rx, text, re.I)):
                    out[fname] = (clean(fname, m.group(1)), i, conf)
        return out

    def predict(self, packet):
        fs, items, text, exif, missing_docs = {}, [], [], [], False
        for doc in packet["docs"]:
            kind, pages_seen, pages_expected = "other", set(), 0
            for pg in doc["pages"]:
                if pg["text_layer"] is not None:  # the text layer includes anything hidden on the page
                    lines = [(ln["text"], ln["bbox"], 0.995) for ln in pg["text_layer"]]
                else:
                    lines = [(ln["text"], ln["bbox"], ln["conf"]) for ln in pg["ocr"]]
                head = " ".join(t for t, _, _ in lines[:3])
                kind = next((k for k, rx in PAGE_TYPES if re.search(rx, head)), kind)  # untitled pages continue
                text += [t for t, _, _ in lines]
                if "exif" in pg["meta"]:
                    exif.append(pg["meta"]["exif"]["DateTimeOriginal"][:10].replace(":", "-"))
                for t, _, _ in lines:
                    if m := re.fullmatch(r"Page (\d)/(\d)", t):
                        pages_seen.add(m.group(1))
                        pages_expected = max(pages_expected, int(m.group(2)))
                    if kind == "bill" and (m := LINE_ITEM.search(t)):
                        items.append(m.group(1))
                for fname, (value, i, conf) in self.extract_page(kind, lines).items():
                    if fname not in fs:
                        fs[fname] = rr.Field(fname, value, conf, (doc["doc_id"], pg["page"], lines[i][1]),
                                             handwritten=pg["handwritten"])
            missing_docs |= len(pages_seen) < pages_expected
        for fname in REQUIRED[packet["line"]]:
            fs.setdefault(fname, rr.Field(fname, "", 0.0, None))  # not found: re-key, never guess
        policy = self.policies.get(packet["policy_no"])
        nhcx = packet.get("nhcx_bill") or {}
        for f in fs.values():  # verified = matches an authoritative source; only these can be seeded
            f.verified = (f.name == "policy_no" and policy is not None and f.value == policy["policy_no"]) or \
                (f.name == "vehicle_reg_no" and policy is not None and f.value == policy.get("vehicle_reg_no")) or \
                (f.name in nhcx and f.value.replace(",", "") == nhcx[f.name])
        rr.validate(fs, policy, items, packet["intimated_on"])
        fraud = rr.fraud_signals(fs, policy, exif, self.seen_bills, packet.get("hospital_id"))
        tamper = ["instruction_text"] if any(INSTRUCTION.search(t) for t in text) else []
        routes = {n: rr.route(f) for n, f in fs.items()}
        conflicts = {e for f in fs.values() for e in f.errors} | set(fraud)
        return {"fields": fs, "routes": routes, "conflicts": sorted(conflicts & rr.CONFLICTS),
                "fcu_flags": fraud + tamper, "tamper_flags": tamper, "status": rr.claim_status(routes, missing_docs)}
