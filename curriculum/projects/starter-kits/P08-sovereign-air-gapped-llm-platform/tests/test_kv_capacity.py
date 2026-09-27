"""Tests for the §6 capacity maths: the brief's KV-per-token figures, its five-row table, and curveball 1 (budget halved)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import kv_capacity as kv  # noqa: E402

KIB = 1024


class KvCapacityTests(unittest.TestCase):
    def test_kv_bytes_per_token_match_the_brief(self):
        self.assertEqual(kv.kv_bytes_per_token(64, 8, 128), 256 * KIB)         # dense 32B-class GQA, BF16
        self.assertEqual(kv.kv_bytes_per_token(64, 8, 128, 1), 128 * KIB)      # FP8
        self.assertEqual(kv.kv_bytes_per_token(19, 4, 64), 19 * KIB)           # Sarvam-30B
        self.assertEqual(kv.kv_bytes_per_token(18, 8, 64), 36 * KIB)           # gpt-oss-120b, full-attention layers only
        self.assertEqual(kv.kv_bytes_per_token(16, 4, 256), 64 * KIB)          # Qwen3.8-27B, 16 of 64 layers

    def test_per_sequence_footprint(self):
        self.assertAlmostEqual(kv.kv_bytes_per_token(64, 8, 128, 1) * 4500 / 1e9, 0.59, places=2)
        self.assertAlmostEqual(kv.kv_bytes_per_token(19, 4, 64) * 4500 / 1e6, 87.6, places=1)   # "88 MB"

    def test_brief_table_within_tolerance(self):
        expected = [(10, 13, "fails"), (77, 20, "marginal"), (80, 52, "passes"), (80, 35, "passes"), (500, 100, "passes")]
        for got, (seqs, tok_s, verdict) in zip(kv.brief_table(), expected):
            self.assertAlmostEqual(got["seqs_per_replica"], seqs, delta=seqs * 0.3, msg=got["config"])
            self.assertAlmostEqual(got["tok_s_per_stream"], tok_s, delta=tok_s * 0.3, msg=got["config"])
            self.assertEqual(got["verdict"], verdict, got["config"])

    def test_one_h100_down_still_serves_about_41_tok_s(self):
        self.assertAlmostEqual(kv.plan(kv.H100_NVL, kv.DENSE_32B, 1, kv_bytes=1)["tok_s_per_stream"], 41, delta=3)

    def test_curveball_1_half_budget_prefers_small_kv_moe(self):
        by = {r["config"]: r["verdict"] for r in kv.half_budget()}
        self.assertEqual(by["2x L40S, dense 32B-class GQA, 2 replica(s)"], "fails")   # 20 streams, room for 10
        self.assertEqual(by["2x L40S, Sarvam-30B-class MoE, 2 replica(s)"], "passes")

    def test_moe_advantage_shrinks_as_batch_grows(self):
        small = kv.plan(kv.L40S, kv.SARVAM_30B, 4, concurrent=4)["tok_s_per_stream"]
        large = kv.plan(kv.L40S, kv.SARVAM_30B, 4, concurrent=160)["tok_s_per_stream"]
        self.assertGreater(small, 2 * large)


if __name__ == "__main__":
    unittest.main()
