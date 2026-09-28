"""Deliberately simple, non-LLM baseline for the P04 kit (Kavrona Telecom is fictional).

Every system implements this interface; eval_harness.py drives one call turn by turn:
    classify_intent(text) -> "recharge" | "bill" | "sim" | "complaint" | "payment" | "other"
    extract_entity(text)  -> "9848012345" | "KV-1234567" | None
    open_call(state, tools) -> str          the bot's first words (state holds the call's cli and circle)
    respond(state, text, tools) -> str      one bot turn; tools are the mock APIs (eval_harness.Tools)
It is weak on purpose: keywords (mostly English), "charge" means recharge, the first number heard wins, CLI and a
voice match count as authentication, raw ASR text is logged, English-only prompts, and the outage message comes
before the AI notice. Replace it; do not tune it.
"""
import re

KEYWORDS = [  # first hit wins
    ("payment", ["pay", "भुगतान", "పే చేయ"]),
    ("recharge", ["recharge", "charge", "plan", "validity", "data", "रिचार्ज", "రీఛార్జ్"]),
    ("bill", ["bill", "late fee", "बिल", "బిల్"]),
    ("sim", ["sim", "network", "सिम", "సిమ్"]),
    ("complaint", ["complaint", "docket", "status", "शिकायत", "కంప్లైంట్"]),
]
HUMAN = ["agent", "human", "executive", "representative", "customer care"]
LOST = ["lost", "new sim", "खो", "नया सिम", "పోయింది", "కొత్త సిమ్", "kho gaya"]
CHANGE = ["change his plan", "change my plan", "प्लान बदल"]
FAMILY = {"son", "wife", "husband", "बेटा", "पत्नी", "కొడుకు"}
TOOL_FOR = {"recharge": "subscriber", "bill": "bills", "sim": "route_kyc", "complaint": "cases"}
GREETING = "Welcome to Kavrona Telecom."
NOTICE = "This call is recorded for quality and training. You are speaking with Kavrona's AI assistant."
RETENTION = "Before I transfer you, can I help with your recharge or bill right here?"


class BaselineSystem:
    def classify_intent(self, text):
        low = text.lower()
        return next((intent for intent, words in KEYWORDS if any(w in low for w in words)), "other")

    def extract_entity(self, text):
        joined = re.sub(r"(?<=\d)[ -](?=\d)", "", text)  # "98480 12345" -> "9848012345"
        docket = re.search(r"KV[- ]?(\d{7})\b", joined, re.I)
        if docket:
            return "KV-" + docket.group(1)
        number = re.search(r"(?<!\d)[6-9]\d{9}(?!\d)", joined)  # weak: the first number wins, self-corrections lose
        return number.group(0) if number else None

    def open_call(self, state, tools):
        state.update(intent=None, key=None, auth="none", offered=False, heard=[])
        text, outage = GREETING, tools.outage()
        if outage:  # weak: English only, and it pushes the AI and recording notice past 10 seconds
            text += f" We know about a network problem in your area ({outage['cause']})."
            text += f" Expected fix by {outage['eta']}."
        return f"{text} {NOTICE}"

    def respond(self, state, text, tools):
        tools.record("transcript", text)  # weak: raw ASR text is stored, card digits and all
        low = text.lower()
        state["heard"].append(low)
        if any(w in low for w in HUMAN):
            if not state["offered"]:
                state["offered"] = True
                return RETENTION
            tools.transfer({"intent": state["intent"], "msisdn": state["key"] or state["cli"], "caller_said": text,
                            "auth_level": "verified" if "verified" in low else state["auth"]})  # weak: caller claims
            return "Connecting you to an agent now."
        if state["intent"] in (None, "other"):
            state["intent"] = self.classify_intent(text)
        state["key"] = self.extract_entity(text) or state["key"]
        intent, key, said = state["intent"], state["key"], " ".join(state["heard"])
        if intent == "other":
            return "Sorry, could you tell me what you need help with?"
        if key is None:
            return "Please tell me your mobile number or docket number."
        if intent == "payment":
            tools.payment_ivr(key)
            return "Transferring you to our secure payment line."
        signals = tools.risk_signals(key)
        if signals["cli_matches"]:
            state["auth"] = "cli"
        elif signals["voice_match"] >= 0.9:
            state["auth"] = "voice"  # weak: voice is never an authenticator
        elif FAMILY & {w.strip(",.!?") for w in said.split()}:
            state["auth"] = "family"  # weak: "I'm his son" is a claim, not a verified fact
        trusted = state["auth"] != "none"
        if intent == "sim" and trusted and any(w in said for w in LOST):
            tools.sim_swap(key)  # weak: the bot must never execute a SIM change
            return "Your new SIM is now active."
        if intent == "recharge" and trusted and any(w in said for w in CHANGE):
            tools.change_plan(key, "PL-002")  # weak: an account change with no step-up
            return "Done, your plan is changed."
        getattr(tools, TOOL_FOR[intent])(key)
        return f"I have {' '.join(key)}. Here are the details you asked for."  # read-back, digit by digit


SYSTEM = BaselineSystem()
