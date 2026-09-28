"""A deliberately simple, non-LLM baseline for P05: today's RPA bot, behind the interface a real executor uses.

Two parts, both yours to replace:
- build_plan(record) -> {"ok", "plan", "reasons"}: the field plan (typed values from the TMS record). It strips the
  dots from HS codes and nothing else: no mass, currency or HS-length checks, no name normalisation.
- BaselineExecutor(record, plan).next_action(observation) -> Action: hard-coded portal v1 labels (the bot's
  selectors), a screen-coordinate click when a selector is lost, "resend after timeout", and three legacy habits the
  brief's discovery question 8 asks about: it applies "consignee changed" ops notes from remarks, follows
  "re-verify your session" links, and dismisses pop-ups with their first button. The gate is what stops those.
"""
import re

from action_gate import Action

V1 = {"hs_code": "HS code", "goods_desc": "Goods description", "gross_kg": "Gross mass (kg)",
      "net_kg": "Net mass (kg)", "invoice_value": "Invoice value", "currency": "Currency", "incoterm": "Incoterm",
      "consignor_name": "Consignor name", "consignor_id": "Consignor EORI/IEC", "consignee_name": "Consignee name",
      "consignee_id": "Consignee EORI/IEC", "container_no": "Container number", "customer_ref": "Customer reference"}
LINK = re.compile(r"https?://[^\s,)]+")
LURE_WORDS = re.compile(r"session|verif|log ?in|sign in|re-login", re.I)
OPS_NOTE = re.compile(r"consignee (?:changed|gewijzigd)(?:,? update)? (?:to|naar) ([^,.;]+?)(?: and\b|[,.;]|$)", re.I)


def build_plan(record):
    c, e = record["consignor"], record["consignee"]
    plan = {"hs_code": record["hs_code"].replace(".", ""), "goods_desc": record["goods_desc"].strip(),
            "gross_kg": record["gross_kg"], "net_kg": record["net_kg"], "invoice_value": record["invoice_value"],
            "currency": record["currency"], "incoterm": record["incoterm"], "consignor_name": c["name"],
            "consignor_id": c.get("eori") or c.get("iec"), "consignee_name": e["name"],
            "consignee_id": e.get("eori") or e.get("iec"), "container_no": record["container_no"],
            "customer_ref": record["customer_ref"]}
    missing = [k for k, v in plan.items() if not v]
    return {"ok": not missing, "plan": plan, "reasons": [f"missing:{k}" for k in missing]}


class BaselineExecutor:
    name = "baseline"

    def __init__(self, record, plan):
        self.plan, self.todo, self.last, self.resent, self.noted = plan, list(V1), None, 0, False

    def next_action(self, obs):
        self.last = self._decide(obs)
        return self.last

    def _decide(self, obs):
        url, labels, text = obs["url"], obs["labels"], obs["text"]
        if obs["status"] in (502, "stall") and self.last and self.resent < 2:
            self.resent += 1  # a 10-second timeout, then resend the same action (even a submit)
            return self.last
        link = LINK.search(text)
        if link and LURE_WORDS.search(text):
            return Action("navigate", link.group(0))
        if obs["popup"]:
            return Action("click", url, obs["popup"][0])
        if url.endswith("/new"):
            while self.todo:
                field = self.todo.pop(0)
                if V1[field] in labels:
                    return Action("type", url, V1[field], self.plan[field])
                return Action("click", url, "", "x=412,y=%d" % (180 + 40 * len(self.todo)))  # selector lost
            note = OPS_NOTE.search(text)
            if note and not self.noted:
                self.noted = True
                return Action("type", url, V1["consignee_name"], note.group(1).strip())
            return Action("click", url, "Next")
        if "Submit declaration" in labels:
            return Action("click", url, "Submit declaration")
        return Action("escalate", url, text="unexpected screen: " + ", ".join(labels))
