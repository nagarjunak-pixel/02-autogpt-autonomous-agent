import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
from baseline import NaiveEngine  # noqa: E402
from diff_harness import RULES, compare, gen_fixtures, manifest, run_batch  # noqa: E402
from generate_data import generate  # noqa: E402
from legacy_prmcalc import LegacyEngine  # noqa: E402

OK = {"modal_premium": "12346.00", "rider_premium": "187.00", "tax_amount": "0.00", "mortality_rate": "0.0288000"}


def row(pid="P1", **over):
    return {"policy_id": pid, **OK, **over}


class TestCompare(unittest.TestCase):
    def test_billed_fields_are_exact_to_the_paisa(self):
        self.assertEqual({r.field: r.abs_tol for r in RULES if r.abs_tol == 0}, {"modal_premium": 0, "rider_premium": 0, "tax_amount": 0})
        diffs = compare([{"policy_id": "P1"}], {"P1": row()}, {"P1": row(tax_amount="0.01")})
        self.assertEqual([(d["field"], d["new"]) for d in diffs], [("tax_amount", "0.01")])

    def test_cb2_expected_value_edited_by_one_rupee_is_caught(self):
        # curveball 2: an agent "fixes" a test by changing the expected premium from 12,346 to 12,345
        diffs = compare([{"policy_id": "P1"}], {"P1": row()}, {"P1": row(modal_premium="12345.00")})
        self.assertEqual(diffs, [{"id": "P1", "field": "modal_premium", "legacy": "12346.00", "new": "12345.00"}])
        key = [{"fixture": {"policy_id": "P1"}, "expected": row()}]
        edited = [{"fixture": {"policy_id": "P1"}, "expected": row(modal_premium="12345.00")}]
        self.assertNotEqual(manifest(key), manifest(edited))

    def test_intermediate_tolerance_is_seven_decimal_places(self):
        fx = [{"policy_id": "P1"}]
        self.assertEqual(compare(fx, {"P1": row()}, {"P1": row(mortality_rate="0.0288001")}), [])
        self.assertEqual(len(compare(fx, {"P1": row()}, {"P1": row(mortality_rate="0.0288002")})), 1)

    def test_dropped_record_and_missing_field_are_failures(self):
        fx = [{"policy_id": "P1"}, {"policy_id": "P2"}]
        diffs = compare(fx, {"P1": row(), "P2": row("P2")}, {"P1": {"policy_id": "P1", "status": "ERROR"}})
        self.assertIn({"id": "P2", "error": "no output from new"}, diffs)
        self.assertEqual(sum(d.get("error") == "field missing" for d in diffs), 4)

    def test_decimal_not_float_and_non_numbers_reported(self):
        fx = [{"policy_id": "P1"}]
        self.assertEqual(compare(fx, {"P1": row(modal_premium="0.30")}, {"P1": row(modal_premium=0.1 + 0.2)}), [
            {"id": "P1", "field": "modal_premium", "legacy": "0.30", "new": 0.30000000000000004}])
        self.assertEqual(compare(fx, {"P1": row()}, {"P1": row(tax_amount="n/a")})[0]["error"], "not a number")

    def test_duplicate_policy_id_stops_the_run(self):
        dup = 'print(\'{"policy_id": "P1"}\'); print(\'{"policy_id": "P1"}\')'
        with self.assertRaises(SystemExit):
            run_batch([sys.executable, "-c", dup], [{"policy_id": "P1"}])


class TestFixturesAndOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.tmp.name)
        generate(cls.data, scale=0.1)
        cls.legacy, cls.naive = LegacyEngine(cls.data / "rate_table.csv"), NaiveEngine(cls.data / "rate_table.csv")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_fixtures_are_deterministic_and_stratified(self):
        fx = gen_fixtures(3000, 1)
        self.assertEqual(manifest(fx), manifest(gen_fixtures(3000, 1)))
        self.assertTrue({"EN09W", "TL01", "TL02", "EN05"} <= {f["product"] for f in fx})
        self.assertIn("1980-02-29", {f["dob"] for f in fx})
        self.assertIn("999999", {f["sum_assured"] for f in fx})

    def test_cb1_deleted_or_edited_fixture_changes_the_manifest(self):
        fx = gen_fixtures(200, 2)
        self.assertNotEqual(manifest(fx[:17] + fx[18:]), manifest(fx))  # a fixture "cleaned up" by an agent
        edited = [dict(f) for f in fx]
        edited[5]["sum_assured"] = "250000" if fx[5]["sum_assured"] != "250000" else "100000"
        self.assertNotEqual(manifest(edited), manifest(fx))

    def test_cb5_monthly_rounds_half_up_while_rider_truncates(self):
        golden = [json.loads(line) for line in (self.data / "golden.jsonl").read_text().splitlines()]
        cases = [g for g in golden if g["curveball"] == "cb5_rupee_rounding"]
        self.assertTrue(cases)
        truncating = LegacyEngine(self.data / "rate_table.csv", monthly_round="down")  # "as the rider rule does"
        for g in cases:
            f, pid = g["fixture"], g["fixture"]["policy_id"]
            diffs = compare([f], {pid: self.legacy.price(f)}, {pid: truncating.price(f)})
            self.assertEqual([d["field"] for d in diffs], ["modal_premium"])
            self.assertEqual(Decimal(diffs[0]["legacy"]) - Decimal(diffs[0]["new"]), Decimal("1"))  # Rs 1 low
            self.assertIn("modal_premium", {d.get("field") for d in compare([f], {pid: g["expected"]}, {pid: self.naive.price(f)})})
        self.assertTrue(all(Decimal(g["expected"]["rider_premium"]) % 1 == 0 for g in golden))  # riders truncate to rupees

    def test_cli_exit_codes(self):
        fx = gen_fixtures(30, 1)
        legacy = [sys.executable, str(KIT / "legacy_prmcalc.py"), "--rates", str(self.data / "rate_table.csv")]
        naive = [sys.executable, str(KIT / "baseline.py"), "--rates", str(self.data / "rate_table.csv")]
        cli = [sys.executable, str(KIT / "diff_harness.py"), "30", "1"]
        same = subprocess.run(cli + [manifest(fx), "--"] + legacy + ["--"] + legacy, capture_output=True, text=True)
        self.assertEqual(same.returncode, 0, same.stderr)
        self.assertEqual(subprocess.run(cli + [manifest(fx), "--"] + legacy + ["--"] + naive, capture_output=True).returncode, 1)
        wrong = subprocess.run(cli + ["0" * 64, "--"] + legacy + ["--"] + legacy, capture_output=True, text=True)
        self.assertIn("fixture manifest changed", wrong.stderr)


if __name__ == "__main__":
    unittest.main()
