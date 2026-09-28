"""Tests for generate_data.py: determinism, checksum-valid identifiers and decoys, seeded cases and curveballs."""
import base64
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate_data as g  # noqa: E402


def rows(folder, name):
    return [json.loads(x) for x in (folder / name).read_text(encoding="utf-8").splitlines()]


def load(folder, name):
    return json.loads((folder / name).read_text(encoding="utf-8"))


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = g.main(["--out", str(Path(cls.tmp.name) / "a")])
        cls.dlp = rows(cls.out, "dlp_set.jsonl")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_deterministic(self):
        again = g.main(["--out", str(Path(self.tmp.name) / "b")])

        def digest(folder):
            return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(folder.rglob("*")) if p.is_file()}
        self.assertEqual(digest(self.out), digest(again))

    def test_scale_flag_multiplies_volumes(self):
        big = g.main(["--out", str(Path(self.tmp.name) / "c"), "--scale", "2"])
        self.assertEqual(len(rows(big, "dlp_set.jsonl")), 2 * len(self.dlp))

    def test_catalogue_is_12_bus_by_25_apps_with_anchors_and_residency(self):
        ucs = load(self.out, "use_cases.json")
        self.assertEqual(len(ucs), 300)
        self.assertEqual(len({u["bu"] for u in ucs}), 12)
        self.assertEqual({u["anchor"] for u in ucs if u["anchor"]}, set(g.ANCHORS))
        self.assertTrue(all(u["residency"] == "india" for u in ucs if u["bu"] == "diagnostics"))
        self.assertTrue(any(u["annex_iii_candidate"] for u in ucs))

    def test_dlp_identifiers_pass_their_checksums_and_decoys_fail(self):
        checks = {"aadhaar": lambda v: g.verhoeff_ok(v.replace(" ", "")), "iban": g.iban_ok,
                  "card": lambda v: g.luhn_ok(v.replace(" ", "")), "gstin": lambda v: g.gstin_check(v[:14]) == v[14]}
        for it in self.dlp:
            if it["label"] in checks:
                self.assertTrue(checks[it["label"]](it["value"]), it)
            if it["decoy"]:
                v = it["value"]
                self.assertFalse(g.verhoeff_ok(v) if len(v) == 12 else g.luhn_ok(v), it)

    def test_dlp_set_has_every_language_encoding_and_trap(self):
        self.assertEqual({it["lang"] for it in self.dlp}, {"en", "hi", "mr", "mixed"})
        self.assertEqual({it["encoding"] for it in self.dlp}, {"plain", "spaced", "unicode_digits", "base64"})
        self.assertTrue(any(it["decoy"] for it in self.dlp))
        self.assertTrue(any(it["label"] == "name_health" for it in self.dlp))
        b64 = next(it for it in self.dlp if it["encoding"] == "base64")
        self.assertIn(base64.b64encode(b64["value"].replace(" ", "").encode()).decode(), b64["text"])
        unicode_items = [it["text"] for it in self.dlp if it["encoding"] == "unicode_digits"]
        self.assertTrue(unicode_items and all(any("०" <= ch <= "९" for ch in t) for t in unicode_items))

    def test_forty_seeded_shadow_ai_cases_of_six_kinds(self):
        truth = load(self.out, "shadow_ai_truth.json")
        self.assertEqual(Counter(c["kind"] for c in truth), Counter(
            {"gateway_bypass_sdk": 10, "consumer_chatbot": 8, "exposed_n8n": 1, "workstation_ollama": 5,
             "saas_ai_feature": 8, "card_subscription": 8}))
        ids = {line["id"] for line in rows(self.out, "discovery_logs.jsonl")}
        self.assertTrue(all(set(c["line_ids"]) <= ids for c in truth))

    def test_billing_has_three_schemas_price_change_credits_and_currencies(self):
        def read(name):
            with open(self.out / "billing" / f"{name}.csv", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        a, b, c = read("provider_a_ptu"), read("provider_b_tokens"), read("provider_c_requests")
        self.assertIn("rate_usd_per_ptu_hour", a[0])
        self.assertIn("price_in_per_1k", b[0])
        self.assertIn("UnitPriceEUR", c[0])
        self.assertEqual(len({r["price_in_per_1k"] for r in b if r["line_type"] == "usage"}), 2)  # mid-month change
        self.assertTrue(any(r["line_type"] == "credit" for r in b))
        self.assertTrue(any(r["Project"] == "" for r in c))  # untagged spend
        invoices = load(self.out, "billing/invoices.json")
        self.assertEqual({v["currency"] for v in invoices.values()}, {"USD", "EUR", "INR"})
        self.assertAlmostEqual(invoices["provider_b_tokens"]["total"], sum(float(r["cost_usd"]) for r in b), places=1)

    def test_adversarial_inputs(self):
        calls, reg = rows(self.out, "mcp_calls.jsonl"), load(self.out, "mcp_registry.json")
        poisoned = [c for c in calls if c["kind"] == "poisoned"]
        self.assertTrue(poisoned and all("<IMPORTANT>" in c["description"] for c in poisoned))
        pinned = reg["approved"]
        self.assertTrue(all(hashlib.sha256(c["description"].encode()).hexdigest() != pinned[c["server"]][c["tool"]]
                            for c in poisoned))
        probes = rows(self.out, "isolation_probes.jsonl")
        pairs = [p for p in probes if p["kind"] == "cache_pair"]
        self.assertEqual(len(pairs), 10_000)
        self.assertTrue(any(p["bu_a"] == p["bu_b"] for p in pairs) and any(p["bu_a"] != p["bu_b"] for p in pairs))

    def test_curveball_fixtures(self):
        notice = load(self.out, "registry.json")["retirement_notices"][0]  # 1: 60 days' notice
        self.assertEqual((notice["announced"], notice["retires"]), ("2026-10-01", "2026-11-30"))
        self.assertGreater(load(self.out, "loop_sim.json")["growth_per_step"], 0)  # 2: growing context
        manifest = load(self.out, "deploy_manifest.json")  # 3: the mirror served the bad versions
        self.assertTrue(set(manifest["known_bad_versions"]) <= set(manifest["mirror"]["served_versions"]))
        self.assertEqual(load(self.out, "drill.json")["down_region"], "india-west")  # 4
        self.assertEqual({u["bu"] for u in load(self.out, "use_cases.json") if u["consumer_bu"]}, {"retail"})  # 5


if __name__ == "__main__":
    unittest.main()
