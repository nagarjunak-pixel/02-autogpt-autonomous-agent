"""Tests for generate_data.py: determinism, and every tricky case and curveball fixture is present and labelled."""
import hashlib
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb  # noqa: E402

import generate_data  # noqa: E402


def digest(folder):
    files = sorted(p for p in Path(folder).rglob("*") if p.suffix in {".csv", ".jsonl", ".json", ".sql"})
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = generate_data.main(["--out", str(Path(cls.tmp.name) / "a")])
        cls.con = duckdb.connect(str(cls.out / "annavara.duckdb"), read_only=True)
        cls.meta = json.loads((cls.out / "meta.json").read_text(encoding="utf-8"))
        cls.golden = [json.loads(x) for x in (cls.out / "golden.jsonl").read_text(encoding="utf-8").splitlines()]
        cls.adversarial = [json.loads(x) for x in (cls.out / "adversarial.jsonl").read_text(encoding="utf-8").splitlines()]
        cls.probes = [json.loads(x) for x in (cls.out / "rls_probes.jsonl").read_text(encoding="utf-8").splitlines()]

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        cls.tmp.cleanup()

    def q(self, sql):
        return self.con.execute(sql).fetchall()

    def test_deterministic(self):
        again = generate_data.main(["--out", str(Path(self.tmp.name) / "b")])
        self.assertEqual(digest(self.out), digest(again))

    def test_store_traps(self):
        test = self.q("SELECT s.store_id, COUNT(*) FROM fct_sales_line f JOIN dim_store s USING (store_sk) "
                      "WHERE s.store_id LIKE 'TEST-%' GROUP BY 1")
        normal = self.q("SELECT COUNT(*) / COUNT(DISTINCT store_sk) FROM fct_sales_line WHERE store_sk < 58")[0][0]
        self.assertEqual(len(test), 3)
        self.assertTrue(all(n > 3 * normal for _, n in test))  # huge volumes, no flag column
        self.assertEqual(self.q("SELECT region_id FROM dim_store WHERE store_id = 'ST009' ORDER BY valid_from"), [(1,), (7,)])

    def test_product_traps(self):
        self.assertTrue(self.q("SELECT sku FROM dim_product GROUP BY sku HAVING COUNT(*) > 1"))  # rebrand duplicates
        self.assertEqual(self.q("SELECT COUNT(*) FROM dim_product WHERE name_en LIKE '%ignore previous instructions%'"),
                         [(1,)])

    def test_fact_traps(self):
        self.assertGreater(self.q("SELECT COUNT(*) FROM fct_sales_line WHERE qty < 0")[0][0], 0)  # voids
        per_day = dict(self.q("SELECT date_key::VARCHAR, COUNT(*) FROM fct_sales_line GROUP BY 1"))
        last = per_day.pop(self.meta["freshness"]["partial_date"])
        self.assertLess(last, 0.9 * sum(per_day.values()) / len(per_day))  # last day only ~80% loaded
        lag = self.q("SELECT MIN(r.return_date - f.date_key), MAX(r.return_date - f.date_key), MAX(r.return_date)::VARCHAR "
                     "FROM fct_returns r JOIN fct_sales_line f ON r.original_bill_id = f.bill_id AND r.product_id = f.product_id")
        self.assertEqual((lag[0][0] >= 0, lag[0][1] <= 30, lag[0][2] <= self.meta["freshness"]["partial_date"]), (True,) * 3)
        paise = self.q("SELECT t.TXN_AMT_2, f.gross_amount FROM legacy_pos.txn t JOIN fct_sales_line f "
                       "ON t.TXN_DT = f.date_key LIMIT 1")
        self.assertIsInstance(paise[0][0], int)
        self.assertEqual(self.q("SELECT COUNT(*) FROM dim_date")[0][0], 730)
        self.assertEqual(len(self.q("SELECT DISTINCT iso_week FROM dim_date WHERE festival = 'Diwali'")), 2)

    def test_golden_mix_and_labels(self):
        self.assertEqual(len(self.golden), 150)
        langs = Counter(it["lang"] for it in self.golden)
        self.assertEqual((langs["en"], langs["hi"], langs["hinglish"]), (60, 45, 45))
        cats = Counter(it["category"] for it in self.golden)
        self.assertAlmostEqual(cats["ambiguous"] / 150, 0.15, delta=0.01)
        self.assertAlmostEqual(cats["out_of_scope"] / 150, 0.10, delta=0.01)
        self.assertTrue(any("ऀ" <= ch <= "ॿ" for it in self.golden for ch in it["question"]))
        self.assertTrue(all(it["gold_sql"] for it in self.golden if it["expected"] == "answer"))

    def test_curveball_fixtures_present(self):
        tags = Counter(t for it in self.golden + self.adversarial + self.probes for t in it["tags"])
        for cb in ("cb1", "cb2", "cb3", "cb5"):
            self.assertGreater(tags[cb], 0, cb)
        self.assertIn("RENAME COLUMN net_amount TO net_sales_inr",
                      (self.out / "curveballs" / "cb4_schema_v2_migration.sql").read_text(encoding="utf-8"))
        cross_scope = sum(p["kind"] == "rls" for p in self.probes) + sum(
            a["category"] in ("cross_scope", "injection") for a in self.adversarial)
        self.assertGreaterEqual(cross_scope, 1000)  # AC-5 needs >= 1,000 cross-scope attempts
        self.assertEqual({a["category"] for a in self.adversarial}, {"dml", "cross_scope", "injection"})


if __name__ == "__main__":
    unittest.main()
