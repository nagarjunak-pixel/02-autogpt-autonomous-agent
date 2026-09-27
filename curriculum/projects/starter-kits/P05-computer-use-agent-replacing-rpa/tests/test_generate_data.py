"""Tests for the generator: determinism, volumes, and every tricky case and curveball fixture from the brief."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_data as gd  # noqa: E402


def read(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines()]


def digest(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(folder).iterdir())}


class Generator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.meta = gd.generate(cls.tmp.name)
        d = Path(cls.tmp.name)
        cls.ships, cls.truth = read(d / "shipments.jsonl"), read(d / "truth.jsonl")
        cls.adv = read(d / "adversarial.jsonl")
        cls.cb = json.loads((d / "curveballs.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            gd.generate(other)
            self.assertEqual(digest(self.tmp.name), digest(other))

    def test_scale_flag(self):
        with tempfile.TemporaryDirectory() as other:
            self.assertEqual(gd.generate(other, scale=2)["shipments"], 800)
        self.assertEqual(self.meta["shipments"], len(self.ships))

    def test_fields_and_labels_kept_apart(self):
        for key in ("shipment_id", "direction", "decl_type", "hs_code", "goods_desc", "gross_kg", "net_kg",
                    "invoice_value", "currency", "incoterm", "consignor", "consignee", "container_no", "vessel",
                    "cutoff_utc", "remarks"):
            self.assertIn(key, self.ships[0])
        self.assertTrue(all("tags" not in s and "expected_fields" not in s for s in self.ships))
        self.assertEqual([s["record_id"] for s in self.ships], [t["record_id"] for t in self.truth])

    def test_tricky_share_and_every_case_present(self):
        self.assertGreaterEqual(self.meta["tricky_share"], 0.20)
        for tag in ("net_gt_gross", "hs_6_digit", "currency_mismatch", "dutch_digraph", "tamil_script_name",
                    "edi_resend", "amendment", "code_mixed_remarks", "injected_remarks"):
            self.assertGreater(self.meta["tags"].get(tag, 0), 0, tag)
        by_id = {s["record_id"]: s for s in self.ships}
        for t in self.truth:
            s = by_id[t["record_id"]]
            if "net_gt_gross" in t["tags"]:
                self.assertGreater(float(s["net_kg"]), float(s["gross_kg"]))
            if "hs_6_digit" in t["tags"]:
                self.assertEqual(len(s["hs_code"]), 6)
            if "currency_mismatch" in t["tags"]:
                self.assertNotEqual(s["currency"], s["invoice_currency"])
            if "tamil_script_name" in t["tags"]:
                names = s["consignor"]["name"] + s["consignee"]["name"]
                self.assertTrue(any("஀" <= ch <= "௿" for ch in names))
            if t["expected_action"] == "no_submit":
                self.assertTrue(t["reasons"])

    def test_injections_six_percent_all_twenty_templates_and_hidden_text(self):
        inj = [t for t in self.truth if "injected_remarks" in t["tags"]]
        self.assertAlmostEqual(len(inj) / len(self.truth), 0.06, delta=0.01)
        self.assertEqual({t["template"] for t in inj}, set(range(20)))
        remarks = " ".join(s["remarks"] for s in self.ships)
        self.assertIn("​", remarks)
        self.assertTrue(any(0xE0000 <= ord(ch) <= 0xE007F for ch in remarks))

    def test_duplicates_and_amendments_share_the_filing_key(self):
        seen = {}
        for s, t in zip(self.ships, self.truth):
            key = (s["shipment_id"], s["decl_type"])
            if {"edi_resend", "amendment"} & set(t["tags"]):
                self.assertIn(key, seen)
                self.assertEqual(t["expected_action"], "no_submit")
            seen[key] = s

    def test_container_check_digits(self):
        self.assertEqual(gd.check_digit("CSQU305438"), 3)  # the ISO 6346 worked example
        for s in self.ships:
            self.assertEqual(int(s["container_no"][-1]), gd.check_digit(s["container_no"][:10]))

    def test_adversarial_suite_and_curveball_fixtures(self):
        self.assertGreaterEqual(len(self.adv), 300)
        channels = {a["channel"] for a in self.adv}
        self.assertEqual(channels, {"remarks", "lure", "popup", "goods_desc"})
        self.assertTrue(all(a["label"]["expected_action"] == "no_submit" for a in self.adv
                            if a["channel"] == "goods_desc"))
        self.assertIn("consignee changed to", self.cb["cb2_injected_remark"]["record"]["remarks"])
        self.assertEqual(self.cb["cb1_redesign"]["variant"], "v5")
        self.assertTrue(self.cb["cb3_stepup_mfa"]["stepup"] and self.cb["cb5_submit_timeout"]["force_502_after_lodge"])
        self.assertEqual(sum(t["golden"] for t in self.truth), 60)
        self.assertTrue(all(not t["tags"] for t in self.truth if t["golden"]))


if __name__ == "__main__":
    unittest.main()
