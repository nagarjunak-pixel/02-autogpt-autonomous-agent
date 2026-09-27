"""Deliberately simple, non-LLM baseline for the P12 kit: the gateway configuration and policies a first sprint might
ship for Tavrenhill Holdings (fictional). Every system implements this interface (eval_harness.py calls it):

    ROUTES                                   route -> tiers (cheapest first), each a fallback chain of aliases/names
    tiers_for(use_case, deps)                -> tiers of router.Deployment for one use case
    accept(anchor, signals) -> bool          cascade validator on what the cheap tier's output shows
    budget_for(use_case) -> (monthly_usd, hourly_cap_usd)
    detect_pii(text) -> set of labels        DLP: aadhaar, pan, card, iban, gstin, name_health
    cache_key(bu, prompt) -> str
    authorise(vkey, caller_bu, key_owner) -> bool
    mcp_allow(server, tool, description, registry) -> bool
    discover(lines, directory) -> [finding]  shadow-AI findings: {"key", "line_ids", "owner", "data_class", "risk_tier"}
    allocate(exports, usage, use_cases, fx) -> {"by_bu": {bu: usd}, "platform": usd, "unallocated": usd}

Weak on purpose. Each weakness is marked "weak:" below. Replace it; do not tune it.
"""
import hashlib
import re
from collections import Counter, defaultdict

ROUTES = {  # weak: raw deployment names mixed with aliases, no residency, and "extract" has no fallback
    "extract": [["alias:cheap-in"], ["alias:strong-in"]],
    "triage": [["alias:cheap-in", "b-small-us"], ["a-large-inwest", "b-large-us"]],
    "summarise": [["alias:cheap-in", "b-small-us"], ["alias:strong-in", "b-large-us"]],
    "general": [["b-small-us", "alias:cheap-in"], ["b-large-us", "alias:strong-in"]],
}
TASK_ROUTE = {"extraction": "extract", "triage": "triage", "summarisation": "summarise"}
PII = {  # weak: ASCII digits only, fixed layouts, no checksums, no decoding, no names or health data
    "aadhaar": re.compile(r"\b[2-9][0-9]{3} ?[0-9]{4} ?[0-9]{4}\b"),
    "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    "card": re.compile(r"\b(?:[0-9]{4}[ -]?){3}[0-9]{4}\b"),
    "iban": re.compile(r"\b[A-Z]{2}[0-9]{2}(?: ?[A-Z0-9]{4}){3,7}\b"),
    "gstin": re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b"),
}
AI_DOMAINS = {"api.provider-a.example", "api.provider-b.example", "api.provider-c.example",
              "chat.consumer-ai.example", "free-llm-chat.example", "aiwriter.example"}
B_LIST_PRICE = (0.003, 0.015)  # USD per 1k tokens in / out, from the contract signed in 2025


class BaselineSystem:
    ROUTES = ROUTES

    def tiers_for(self, use_case, deps):
        route = TASK_ROUTE.get(use_case["task"], "general")
        return [[deps[ref] for ref in chain] for chain in ROUTES[route]]  # weak: no residency filter

    def accept(self, anchor, signals):
        return signals["schema_ok"]  # weak: schema only; ignores totals, citations and confidence

    def budget_for(self, use_case):
        return 3000.0, 3000.0  # weak: a monthly budget and no hourly burn-rate cap

    def detect_pii(self, text):
        return {label for label, rx in PII.items() if rx.search(text)}

    def cache_key(self, bu, prompt):
        return hashlib.sha256(prompt.encode()).hexdigest()  # weak: keyed on prompt text only, shared across BUs

    def authorise(self, vkey, caller_bu, key_owner):
        return vkey in key_owner  # weak: any valid key works for any BU

    def mcp_allow(self, server, tool, description, registry):
        return server in registry["approved"]  # weak: tool descriptions are not pinned, so a rug pull passes

    def discover(self, lines, directory):
        found = defaultdict(list)
        for line in lines:
            dest = line.get("dest") or line.get("query") or ""
            if dest in AI_DOMAINS and line.get("src_host") not in directory["gateway_hosts"]:
                found[dest].append(line["id"])
            elif line["kind"] == "card" and "AI" in line["merchant"]:  # weak: substring match ("THAI", "MAIL")
                found[line["merchant"]].append(line["id"])
        # weak: no owner, data class or risk tier, and one finding per domain rather than per use case
        return [{"key": k, "line_ids": ids, "owner": None, "data_class": None, "risk_tier": None}
                for k, ids in found.items()]

    def allocate(self, exports, usage, use_cases, fx):
        owner = {u["virtual_key"]: u["bu"] for u in use_cases}
        by_bu, unallocated = Counter(), 0.0
        for r in exports["provider_b_tokens"]:
            if r["line_type"] != "usage":
                continue  # weak: credits ignored
            usd = int(r["input_tokens"]) / 1000 * B_LIST_PRICE[0] + int(r["output_tokens"]) / 1000 * B_LIST_PRICE[1]
            by_bu[owner.get(r["api_key_id"], "?")] += usd  # weak: list price, so the mid-month price cut is missed
        for r in exports["provider_c_requests"]:
            usd = float(r["CostEUR"]) * fx["EUR"]
            if r["Project"]:
                by_bu[r["Project"].removeprefix("tvh-")] += usd
            else:
                unallocated += usd
        unallocated += sum(float(r["amount_usd"]) for r in exports["provider_a_ptu"])  # weak: PTU not amortised
        unallocated += sum(float(r["amount_inr"]) * fx["INR"] for r in exports["onprem_gpu"])  # weak: GPU not shared
        return {"by_bu": dict(by_bu), "platform": 0.0, "unallocated": unallocated}


SYSTEM = BaselineSystem()
