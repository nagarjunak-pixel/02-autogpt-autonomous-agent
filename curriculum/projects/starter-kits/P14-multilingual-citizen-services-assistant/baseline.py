"""A deliberately simple, non-LLM baseline for the P14 assistant. It is meant to fail several §5 thresholds.

Interface (eval_harness.py only calls these; keep them when you build the real system):
    answer(query) -> {"answer", "fact", "citations", "retrieved", "abstained", "route"}   (predict() is an alias)
    eligibility(profile) -> {"outcome": "appears_eligible" | "appears_ineligible" | "refer", "text": ...}
    status(app_id, mobile, api) -> {"status", "as_of", "stale_warning", "fallback", "text"}
    reset()                                                  start a fresh session (pass^k runs are independent)

What it does, and the brief §15 failure modes it walks into on purpose:
- BM25 over raw text with a \\w+ tokeniser: no NFC or Urdu code-point normalisation, no transliteration, and Telugu
  words split at every vowel sign (the pre-tokeniser problem in brief §8); no dense retrieval, reranker or pivot;
- trusts every document it is given: no registry check and no effective dating, so forged and superseded GOs get quoted;
- answers whenever it spots an intent keyword: no abstention threshold, no political or out-of-scope route;
- eligibility from the first rule version, on age and income only, phrased "You are eligible";
- status: one API attempt, no staleness warning, and a per-application cache keyed without the caller's mobile.
"""
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from mock_status_api import ServiceUnavailable

TOKEN = re.compile(r"\w+")
INTENTS = [("age", ["age", "old", "వయస్సు", "आयु", "عمر", "umar"]),  # checked first: "आयु" contains "आय"
           ("income", ["income", "ఆదాయ", "आय", "آمدنی", "amdani"]),
           ("benefit", ["money", "much", "pay", "డబ్బు", "पैसा", "کتنی", "raqam", "dabbu"])]
LABELS = {"income": ["Income limit", "ఆదాయ పరిమితి", "आय सीमा", "آمدنی کی حد"],
          "age": ["Minimum age", "కనీస వయస్సు", "न्यूनतम आयु", "کم از کم عمر"],
          "benefit": ["Benefit", "ప్రయోజనం", "लाभ", "فائدہ"]}


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def tokens(text):
    return TOKEN.findall(text.lower())


def digits(text):
    return "".join(ch for ch in str(text) if ch.isdigit())


class Baseline:
    name = "baseline"

    def __init__(self, data_dir="data"):
        data = Path(data_dir)
        self.docs = {d["doc_id"]: d for d in load_jsonl(data / "corpus.jsonl")}
        self.rules = json.loads((data / "rules.json").read_text(encoding="utf-8"))
        self.postings, self.length = defaultdict(list), {}
        for doc_id, d in self.docs.items():
            tf = Counter(tokens(d["text"]))
            self.length[doc_id] = sum(tf.values())
            for t, n in tf.items():
                self.postings[t].append((doc_id, n))
        self.avgdl = sum(self.length.values()) / len(self.length)
        self.cache = {}

    def reset(self):
        self.cache.clear()

    def retrieve(self, text, k=5, k1=1.5, b=0.75):
        scores, n_docs = Counter(), len(self.docs)
        for t in set(tokens(text)):
            post = self.postings.get(t, [])
            idf = math.log(1 + (n_docs - len(post) + 0.5) / (len(post) + 0.5))
            for doc_id, tf in post:
                scores[doc_id] += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * self.length[doc_id] / self.avgdl))
        return [d for d, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:k]]

    @staticmethod
    def intent(text):
        low = text.lower()
        return next((name for name, words in INTENTS if any(w in low for w in words)), None)

    @staticmethod
    def abstain(retrieved, route="escalate"):
        return {"answer": "I could not find this in the government orders. Connecting you to the helpline.", "fact": None,
                "citations": [], "retrieved": retrieved, "abstained": True, "route": route}

    def answer(self, query):
        retrieved = self.retrieve(query["text"])
        intent = self.intent(query["text"])
        if intent is None or not retrieved:
            return self.abstain(retrieved)
        return self.generate(query, intent, retrieved)

    predict = answer

    def generate(self, query, intent, retrieved):
        """Extractive: the clause line for the intent from the best-ranked document that has one."""
        for doc_id in retrieved:
            d = self.docs[doc_id]
            for line in d["text"].splitlines():
                if any(line.startswith(label) for label in LABELS[intent]) and digits(line):
                    return {"answer": f"{d['go_no']} ({d['date']}): {line}", "fact": digits(line.split(":", 1)[-1]),
                            "citations": [doc_id], "retrieved": retrieved, "abstained": False, "route": "grounded_qa"}
        return self.abstain(retrieved)

    def eligibility(self, profile):
        s = self.rules[profile["scheme_id"]]
        v = s["versions"][0]
        ok = (profile["age"] >= v["age_min"] and (v["age_max"] is None or profile["age"] <= v["age_max"])
              and profile["income"] <= v["income_max"])
        name = s["names"]["en"]
        return {"outcome": "appears_eligible" if ok else "appears_ineligible",
                "text": f"You are eligible for {name}." if ok else f"You are not eligible for {name}."}

    def status(self, app_id, mobile, api):
        if app_id in self.cache:  # saves a 1.8 s API call... and ignores who is asking
            return self.cache[app_id]
        try:
            r = api.get(app_id, mobile)
        except ServiceUnavailable:
            return {"status": None, "fallback": "callback", "text": "The status service is down. We will call you back."}
        if not r["found"]:
            return {"status": None, "fallback": None, "text": "No application found for this number."}
        reply = {"status": r["status"], "as_of": r["as_of"], "stale_warning": False, "fallback": None,
                 "text": f"Application {app_id}: {r['status'].replace('_', ' ')}."}
        self.cache[app_id] = reply
        return reply
