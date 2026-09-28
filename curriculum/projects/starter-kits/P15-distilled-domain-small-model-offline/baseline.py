"""Deliberately simple, non-LLM baseline for P15. A real B0, B1 or B2 implements the same three methods:

  retrieve(question, k) -> [passage_id]      on-device retrieval over the manual pack
  answer(question) -> {"mode": "quote" | "answer" | "refuse", "text", "citation", "escalate"}
  next_check(state) -> "check: X" | "cause: Y" | "escalate"     one fault-diagnosis turn

The safety router and verbatim renderer are the brief's design: when the router fires the model writes nothing, and
a quote is the stored text with doc, revision and step. The weaknesses are on purpose: keyword scoring over text only
(it ignores equipment model, revision and "current"), an English-only router, the first number in the top passage as
the numeric answer, a low refusal threshold, and positional tree walking that ignores results and equipment.
"""
import json
import math
from collections import Counter
from pathlib import Path

from synth_filter import NUM, SAFETY, toks

STOP = set("a an and at be can could de del do does el en for how i in is it la los me my of on or say says should step the "
           "this to what when where which who with y".split())
REFUSE_BELOW = 0.35  # share of the question's IDF weight found in the top passage


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines()]


class BaselineSystem:
    name = "baseline"

    def __init__(self, data_dir="data"):
        d = Path(data_dir)
        self.passages = load_jsonl(d / "passages.jsonl")
        self.by_id = {p["passage_id"]: p for p in self.passages}
        self.trees = load_jsonl(d / "fault_trees.jsonl")
        self.bags = {p["passage_id"]: set(toks(p["text"])) - STOP for p in self.passages}
        df = Counter(t for bag in self.bags.values() for t in bag)
        self.idf = {t: math.log(len(self.bags) / n) + 1 for t, n in df.items()}

    def scored(self, question):
        q = set(toks(question)) - STOP
        total = sum(self.idf.get(t, 1.0) for t in q) or 1.0
        s = [(sum(self.idf[t] for t in q & bag) / total, pid) for pid, bag in self.bags.items()]
        return sorted(s, key=lambda x: -x[0])  # stable: ties keep pack order, so Rev C comes before Rev D

    def retrieve(self, question, k=5):
        return [pid for _, pid in self.scored(question)[:k]]

    def cite(self, p):
        return {k: p[k] for k in ("passage_id", "doc_id", "revision", "step_no")}

    def answer(self, question):
        score, pid = self.scored(question)[0]
        refuse = {"mode": "refuse", "text": "Not in the manual. Escalate to the desk engineer.", "citation": None, "escalate": True}
        if score < REFUSE_BELOW:
            return refuse
        top = self.by_id[pid]
        if SAFETY.search(question):  # safety router: render the stored step verbatim, or refuse and escalate
            return {"mode": "quote", "text": top["text"], "citation": self.cite(top), "escalate": True} if top["is_safety_critical"] else refuse
        if any(w in question.lower() for w in ("torque", "how tight", "clearance")):
            nums = NUM.findall(top["text"])
            return {"mode": "answer", "text": f"{nums[0]} N·m" if nums else top["text"], "citation": self.cite(top), "escalate": False}
        return {"mode": "answer", "text": top["text"], "citation": self.cite(top), "escalate": False}

    def next_check(self, state):
        tree = next((t for t in self.trees if t["symptom"] == state["symptom"]), None)  # ignores the equipment model
        if tree is None:
            return "escalate"
        n = len(state["done"])  # positional: ignores failed checks, loops and missing branches
        return f"check: {tree['checks'][n]}" if n < len(tree["checks"]) else "escalate"
