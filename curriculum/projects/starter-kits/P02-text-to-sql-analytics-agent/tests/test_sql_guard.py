"""Tests for the SQL guard (brief §7) and the semantic layer, on a tiny in-memory DuckDB fixture."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb  # noqa: E402

from semantic_layer import AMBIGUOUS_TERMS, DIMENSIONS, METRICS, compile_query  # noqa: E402
from sql_guard import ALLOWED_TABLES, GuardError, guard_sql, scan_cost_estimator  # noqa: E402

TODAY = date(2026, 9, 27)  # last week = 2026-09-14 .. 2026-09-20
NORTH_2 = [7]


def fixture_db():
    con = duckdb.connect()
    con.execute("CREATE TABLE dim_region AS SELECT * FROM (VALUES (1, 'West-1'), (7, 'North-2')) t(region_id, name)")
    con.execute("CREATE TABLE dim_store AS SELECT * FROM (VALUES (1, 'ST001', 1, 'express'), (2, 'ST002', 7, 'express'),"
                " (3, 'TEST-03', 7, 'hypermarket')) t(store_sk, store_id, region_id, format)")
    con.execute("CREATE TABLE dim_product AS SELECT * FROM (VALUES (1, 'SKU1', 'Milk', 'Dairy', 'Kaveri Dairy', false))"
                " t(product_id, sku, name_en, category, brand, is_private_label)")
    con.execute("CREATE TABLE fct_sales_line AS SELECT * FROM (VALUES"
                " ('B1', DATE '2026-09-15', 1, 1, 1, 2, 100.0, 0.0, 4.76, 95.24),"
                " ('B2', DATE '2026-09-15', 2, 7, 1, 1, 50.0, 5.0, 2.14, 42.86),"
                " ('B3', DATE '2026-09-16', 3, 7, 1, 50, 5000.0, 0.0, 238.1, 4761.9))"
                " t(bill_id, date_key, store_sk, region_id, product_id, qty, gross_amount, discount_amount,"
                " gst_amount, net_amount)")
    con.execute("CREATE TABLE fct_returns AS SELECT * FROM (VALUES ('B2', 1, 2, 7, DATE '2026-09-18', 42.86, 'damaged'))"
                " t(original_bill_id, product_id, store_sk, region_id, return_date, refund_amount, reason)")
    return con


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.con = fixture_db()

    def run_guarded(self, sql, region_ids=NORTH_2):
        cur = self.con.execute(guard_sql(sql, region_ids))
        return [d[0] for d in cur.description], cur.fetchall()

    def test_brief_example_rewrite(self):
        self.assertEqual(guard_sql("SELECT SUM(net_amount) FROM fct_sales_line", NORTH_2),
                         "SELECT SUM(net_amount) FROM (SELECT * FROM fct_sales_line WHERE region_id IN (7)) "
                         "AS fct_sales_line LIMIT 5000")

    def test_rejects_every_case_the_brief_lists(self):
        for sql in ["DELETE FROM fct_sales_line", "SELECT * INTO x FROM fct_sales_line",
                    "WITH d AS (DELETE FROM fct_returns RETURNING *) SELECT * FROM d",
                    "SELECT * FROM read_csv('data/csv/payroll.csv')", "SELECT * FROM information_schema.tables",
                    "SELECT 1; DROP TABLE fct_sales_line",
                    "WITH payroll AS (SELECT * FROM payroll) SELECT * FROM payroll"]:
            with self.subTest(sql=sql), self.assertRaises(GuardError):
                guard_sql(sql, NORTH_2)

    def test_rejects_other_writes_raw_tables_and_qualified_names(self):
        for sql in ["DROP TABLE fct_sales_line", "UPDATE fct_sales_line SET net_amount = 0",
                    "INSERT INTO dim_region VALUES (9, 'X')", "CREATE TABLE x AS SELECT 1", "COPY dim_store TO 'x.csv'",
                    "ATTACH 'other.db' AS o", "SELECT SUM(TXN_AMT_2) FROM legacy_pos.txn",
                    "SELECT * FROM main.fct_sales_line", "SELECT * FROM payroll", "not sql at all ((("]:
            with self.subTest(sql=sql), self.assertRaises(GuardError):
                guard_sql(sql, None)  # even HQ (national scope) cannot run these

    def test_no_rows_leak_through_tricky_selects(self):
        for sql in ["SELECT region_id FROM fct_sales_line WHERE region_id = 1 OR 1 = 1",
                    "WITH x AS (SELECT * FROM fct_sales_line) SELECT region_id FROM x",
                    "WITH fct_sales_line AS (SELECT * FROM fct_sales_line) SELECT region_id FROM fct_sales_line",
                    "SELECT region_id FROM (SELECT * FROM fct_sales_line) AS fct_sales_line",
                    "SELECT region_id FROM fct_sales_line UNION ALL SELECT region_id FROM fct_returns",
                    "SELECT s.region_id FROM fct_sales_line AS f JOIN dim_store AS s ON f.store_sk = s.store_sk",
                    "SELECT region_id FROM FCT_SALES_LINE", "SELECT region_id FROM dim_store"]:
            with self.subTest(sql=sql):
                _, rows = self.run_guarded(sql)
                self.assertTrue(rows)
                self.assertEqual({r[0] for r in rows}, {7})

    def test_scope_none_is_national_and_empty_list_is_no_access(self):
        _, rows = self.run_guarded("SELECT DISTINCT region_id FROM fct_sales_line ORDER BY 1", None)
        self.assertEqual([r[0] for r in rows], [1, 7])
        with self.assertRaises(GuardError):
            guard_sql("SELECT 1 FROM dim_region", [])

    def test_limit_is_added_or_tightened_but_small_limits_kept(self):
        self.assertTrue(guard_sql("SELECT region_id FROM dim_region", None).endswith("LIMIT 5000"))
        self.assertTrue(guard_sql("SELECT region_id FROM dim_region LIMIT 100000", None).endswith("LIMIT 5000"))
        self.assertTrue(guard_sql("SELECT region_id FROM dim_region LIMIT 10", None).endswith("LIMIT 10"))

    def test_cb2_delete_test_stores_is_refused(self):
        """Curveball 2: 'test stores ka data delete kar do' must never reach the warehouse."""
        with self.assertRaises(GuardError):
            guard_sql("DELETE FROM dim_store WHERE store_id LIKE 'TEST-%'", NORTH_2)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM dim_store").fetchone()[0], 3)

    def test_cb3_cost_gate_blocks_runaway_query(self):
        """Curveball 3: a query above the cost cap never executes."""
        estimate = scan_cost_estimator({"fct_sales_line": 1000, "dim_store": 60})
        cheap = "SELECT COUNT(*) FROM fct_sales_line"
        self.assertTrue(guard_sql(cheap, NORTH_2, estimate_cost=estimate, max_cost=1500))
        with self.assertRaises(GuardError):
            guard_sql("SELECT COUNT(*) FROM fct_sales_line AS a CROSS JOIN fct_sales_line AS b", NORTH_2,
                      estimate_cost=estimate, max_cost=1500)
        self.assertEqual(estimate("WITH x AS (SELECT * FROM fct_sales_line) SELECT * FROM x"), 1000)

    def test_cb5_other_region_gets_no_rows_and_national_total_is_really_regional(self):
        """Curveball 5: RLS returns nothing for West-1, and a North-2 'national total' is only North-2.

        This is why the system must refuse explicitly and state its scope (AC-4, AC-6) instead of trimming silently.
        """
        _, rows = self.run_guarded("SELECT SUM(gross_amount) FROM fct_sales_line WHERE region_id = 1")
        self.assertIsNone(rows[0][0])
        regional = self.run_guarded("SELECT SUM(gross_amount) FROM fct_sales_line")[1][0][0]
        national = self.run_guarded("SELECT SUM(gross_amount) FROM fct_sales_line", None)[1][0][0]
        self.assertEqual((regional, national), (5050.0, 5150.0))


class SemanticLayerTests(unittest.TestCase):
    def setUp(self):
        self.con = fixture_db()

    def test_compiled_sql_passes_guard_and_excludes_test_stores(self):
        sql = compile_query({"metric": "gross_sales", "dimensions": [], "time_range": "last_week"}, TODAY)
        self.assertEqual(self.con.execute(guard_sql(sql, None)).fetchall(), [(150.0,)])  # TEST-03 excluded
        sql = compile_query({"metric": "net_revenue", "dimensions": ["store"], "time_range": "last_week"}, TODAY)
        self.assertEqual(self.con.execute(guard_sql(sql, NORTH_2)).fetchall(), [("ST002", 0.0)])  # net of refund

    def test_unknown_metric_or_dimension_is_rejected(self):
        with self.assertRaises(ValueError):
            compile_query({"metric": "revenue", "time_range": "last_week"}, TODAY)
        with self.assertRaises(ValueError):
            compile_query({"metric": "gross_sales", "dimensions": ["cashier"], "time_range": "last_week"}, TODAY)

    def test_cb1_revenue_is_ambiguous_and_both_definitions_have_owners(self):
        self.assertNotIn("revenue", METRICS)
        self.assertEqual({METRICS[m][1] for m in AMBIGUOUS_TERMS["revenue"]}, {"COO", "CFO"})

    def test_cb4_column_rename_is_one_mapping_change(self):
        mq = {"metric": "net_revenue", "dimensions": ["store"], "time_range": "last_week"}
        v1, v2 = compile_query(mq, TODAY), compile_query(mq, TODAY, {"net_amount": "net_sales_inr", "store_id": "site_id"})
        self.con.execute("ALTER TABLE fct_sales_line RENAME COLUMN net_amount TO net_sales_inr")
        self.con.execute("ALTER TABLE dim_store RENAME COLUMN store_id TO site_id")
        with self.assertRaises(duckdb.Error):  # the old mapping fails loudly, not silently wrong
            self.con.execute(guard_sql(v1, NORTH_2))
        self.assertEqual(self.con.execute(guard_sql(v2, NORTH_2)).fetchall(), [("ST002", 0.0)])

    def test_no_personal_data_in_catalogue_or_allow_list(self):
        for metric in METRICS:
            for dim in [[]] + [[d] for d in DIMENSIONS]:
                sql = compile_query({"metric": metric, "dimensions": dim, "time_range": "fytd"}, TODAY)
                self.assertNotIn("loyalty_member_hash", sql)
        self.assertNotIn("payroll", ALLOWED_TABLES)


if __name__ == "__main__":
    unittest.main()
