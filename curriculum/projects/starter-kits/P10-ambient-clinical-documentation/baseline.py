"""A deliberately simple, non-LLM baseline for P10: keyword rules behind the interface a real drafter uses.

    BaselineSystem(data_dir).predict(encounter) -> SOAP note dict, or None when no draft may be made

consent_ok() checks only the patient's consent at the start of the visit: the classic failure that forgets
guardians, interpreters and withdrawal mid-visit. The drafter matches lexicon words exactly, takes the first dose and
frequency near a drug's first mention, writes every route as oral, trusts speaker labels (an interpreter's
first-person rendition becomes the interpreter's), treats any condition word as the patient's problem, takes the
first side word it hears, and writes everything down, including small talk and "please don't write that down".
"""
import json
import re
from pathlib import Path

DOSE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|mcg|units)\b", re.I)
SIDE = re.compile(r"\b(left|right|izquierd[ao]|derech[ao])\b", re.I)
NEG = re.compile(r"\b(no|nada de|denies)\b", re.I)
FAMILY = re.compile(r"\b(?:my|mi) (mother|father|brother|sister|madre|padre|hermano|hermana) (?:has|tiene) ", re.I)
ACTIONS = [("stop", r"\b(stop|stopped|ya no|suspend\w*)\b"), ("increase", r"\b(increase|subir)\b"),
           ("start", r"\b(start|empezar)\b")]
REQUIRED = {"symptom": ("item", "negated", "subject"), "problem": ("item", "laterality", "subject"),
            "medication": ("med", "dose", "frequency", "route", "action"), "allergy": ("item",),
            "family_history": ("item", "relation"), "plan": ("item",), "other": ("item",)}


def consent_ok(encounter):
    return any(c["role"] == "patient" and c["status"] == "active" and c["t"] == 0 for c in encounter["consent"])


def find(words, text):
    low = text.lower()
    return any(re.search(rf"\b{re.escape(w.lower())}\b", low) for w in words)


class BaselineSystem:
    name = "baseline"

    def __init__(self, data_dir):
        data = Path(data_dir)
        self.lexicon = json.loads((data / "lexicon.json").read_text(encoding="utf-8"))
        self.vocab = json.loads((data / "vocab.json").read_text(encoding="utf-8"))

    def predict(self, enc):
        if not consent_ok(enc):
            return None
        segs, v, stmts, seen = enc["segments"], self.vocab, [], set()

        def add(section, kind, text, **fields):
            if (kind, fields.get("item") or fields.get("med")) not in seen:
                seen.add((kind, fields.get("item") or fields.get("med")))
                stmts.append({"id": f"{section}{len(stmts) + 1}", "section": section, "kind": kind, "text": text,
                              **fields})

        side = SIDE.search(" ".join(s["text"] for s in segs))
        side = None if side is None else "left" if side.group(1).lower() in ("left", "izquierda", "izquierdo") \
            else "right"
        for i, s in enumerate(segs):
            text, who = s["text"], s["speaker"]
            window = text + " " + (segs[i + 1]["text"] if i + 1 < len(segs) else "")
            if who != "clinician":
                subject = "patient" if who in ("patient", "guardian") else who
                for name, words in v["symptoms"].items():
                    if find(words, text):
                        neg = bool(NEG.search(text))
                        add("S", "symptom", f"{'Denies' if neg else 'Reports'} {name}.", item=name, negated=neg,
                            subject=subject)
                for name, words in v["allergens"].items():
                    if find(words, text):
                        add("S", "allergy", f"Allergy: {name}.", item=name)
                fam = FAMILY.search(text)
                for name, p in v["problems"].items():
                    if fam and find(p["words"], text):
                        rel = next(k for k, ws in v["relations"].items() if fam.group(1).lower() in ws)
                        add("S", "family_history", f"Family history: {rel} with {name}.", item=name, relation=rel)
                if re.search(r"drinking|alcohol", text, re.I):
                    add("S", "other", "Reports increased alcohol use.", item="alcohol use")
            for name, p in v["problems"].items():  # any condition word is taken as the patient's problem
                if find(p["words"], text):
                    lat = side if isinstance(p["icd10"], dict) else None
                    add("A", "problem", name.capitalize() + (f", {lat}." if lat else "."), item=name, laterality=lat,
                        subject="patient")
            for form, med in sorted(self.lexicon.items(), key=lambda kv: -len(kv[0])):
                if find([form], text) and ("medication", med) not in seen:
                    dose = DOSE.search(window)
                    dose = f"{dose.group(1).replace(',', '')} {dose.group(2).lower()}" if dose else None
                    freq = next((k for k, ws in v["frequencies"].items() if find(ws, window)), None)
                    act = next((a for a, rx in ACTIONS if re.search(rx, window, re.I)), "continue")
                    words = f"{act.capitalize()} {med}" + ("." if act == "stop" else f" {dose} {freq}.")
                    add("P", "medication", words, med=med, dose=dose, frequency=freq, route="oral", action=act)
            if re.search(r"order labs|análisis", text, re.I):
                add("P", "plan", "Labs ordered; follow up in three months.", item="labs and follow-up")
        codes = []
        for s in stmts:
            if s["kind"] == "problem":
                code = v["problems"][s["item"]]["icd10"]
                codes.append(code.get(s["laterality"] or "right") if isinstance(code, dict) else code)
        order = {"S": 0, "O": 1, "A": 2, "P": 3}
        return {"encounter_id": enc["encounter_id"], "statements": sorted(stmts, key=lambda s: order[s["section"]]),
                "icd10": codes}
