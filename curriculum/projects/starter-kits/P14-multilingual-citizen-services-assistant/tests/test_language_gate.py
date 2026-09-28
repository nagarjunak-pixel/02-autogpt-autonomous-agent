"""Tests for language_gate.py: the reviewed behaviour of the brief's §7 sketch, and curveballs 2 and 3."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from language_gate import bootstrap, diff_ci, evaluate, flatten, hit_at_k  # noqa: E402


def recs(lang, hits, n, faithful=None, gold=("G1",)):
    """n answerable records for a slice: the first `hits` retrieve a gold document, the rest do not."""
    return [{"lang": lang, "gold_ids": list(gold), "retrieved_ids": ["G1" if i < hits else "X"],
             "faithful": None if faithful is None else int(i < faithful)} for i in range(n)]


def fails(failures, lang, metric):
    return sorted(why for f_lang, f_metric, why in failures if (f_lang, f_metric) == (lang, metric))


class Basics(unittest.TestCase):
    def test_hit_at_k_respects_the_cutoff(self):
        self.assertEqual(hit_at_k(["a"], ["x", "y", "z", "w", "v", "a"], 5), 0.0)
        self.assertEqual(hit_at_k(["a", "b"], ["x", "b"], 5), 1.0)
        self.assertEqual(hit_at_k([], ["a"], 5), 0.0)

    def test_bootstrap_is_deterministic_and_brackets_the_mean(self):
        xs = [1.0] * 80 + [0.0] * 20
        m, lo, hi = bootstrap(xs)
        self.assertEqual((m, lo, hi), bootstrap(xs))
        self.assertTrue(lo < m < hi)
        self.assertAlmostEqual(m, 0.8)

    def test_diff_ci_resamples_each_language_independently(self):
        g, lo, hi = diff_ci([1.0] * 90 + [0.0] * 10, [1.0] * 30 + [0.0] * 20)  # different sizes: not paired
        self.assertAlmostEqual(g, 0.3)
        self.assertTrue(lo < g < hi)


class Gate(unittest.TestCase):
    def test_gates_on_the_lower_bound_not_the_mean(self):
        report, failures = evaluate(recs("te", 131, 150))  # mean 0.873, above 0.85
        m, lo, hi, n = report[("te", "hit@k")]
        self.assertGreater(m, 0.85)
        self.assertLess(lo, 0.85)
        self.assertEqual(fails(failures, "te", "hit@k"), ["floor"])

    def test_a_small_slice_fails_as_insufficient_n_instead_of_passing(self):
        report, failures = evaluate(recs("te", 99, 99, faithful=99))  # perfect, but only 99 items
        self.assertEqual(report[("te", "hit@k")], ("insufficient_n", 99))
        self.assertEqual(fails(failures, "te", "hit@k"), ["n"])
        self.assertEqual(fails(failures, "te", "faithfulness"), ["n"])

    def test_unanswerable_and_escalated_items_are_left_out(self):
        rows = recs("en", 150, 150, faithful=150)
        rows += [{"lang": "en", "gold_ids": [], "retrieved_ids": ["X"], "faithful": None} for _ in range(50)]  # unanswerable
        rows += [{"lang": "en", "gold_ids": ["G1"], "retrieved_ids": ["G1"], "faithful": None} for _ in range(30)]  # escalated
        report, failures = evaluate(rows)
        self.assertEqual(report[("en", "hit@k")][3], 180)
        self.assertEqual(report[("en", "faithfulness")][3], 150)
        self.assertEqual(report[("en", "faithfulness")][0], 1.0)
        self.assertEqual(failures, [])

    def test_cb3_urdu_far_below_telugu_fails_floor_and_parity(self):
        report, failures = evaluate(recs("te", 138, 150) + recs("ur", 93, 150))  # 0.92 vs 0.62
        g, glo, ghi = report[("ur", "hit@k", "gap_vs_te")]
        self.assertAlmostEqual(g, 0.3, places=3)
        self.assertTrue(0.15 < glo < 0.25 and 0.35 < ghi < 0.45)  # about 0.3 [0.2, 0.39] (brief §7)
        self.assertEqual(fails(failures, "ur", "hit@k"), ["floor", "parity"])
        self.assertEqual(fails(failures, "te", "hit@k"), [])

    def test_a_gap_that_is_not_credibly_above_0_07_does_not_fail_parity(self):
        report, failures = evaluate(recs("te", 145, 150) + recs("hi", 133, 150))  # 0.967 vs 0.887: mean gap 0.08
        g, glo, _ = report[("hi", "hit@k", "gap_vs_te")]
        self.assertGreater(g, 0.07)
        self.assertLess(glo, 0.07)
        self.assertNotIn("parity", fails(failures, "hi", "hit@k"))

    def test_parity_is_skipped_when_the_reference_slice_is_too_small(self):
        report, failures = evaluate(recs("te", 50, 50) + recs("ur", 150, 150))
        self.assertNotIn(("ur", "hit@k", "gap_vs_te"), report)
        self.assertEqual(fails(failures, "te", "hit@k"), ["n"])
        self.assertEqual(fails(failures, "ur", "hit@k"), [])

    def test_voice_slices_are_gated_separately(self):
        report, failures = evaluate(recs("ur", 145, 150) + recs("ur|voice", 60, 120))
        self.assertEqual(fails(failures, "ur", "hit@k"), [])
        self.assertEqual(fails(failures, "ur|voice", "hit@k"), ["floor"])

    def test_cb2_rerunning_one_scheme_after_a_rule_change_catches_the_stale_answer(self):
        # after the overnight GO, a stale index still ranks the old GO first for 12 of 30 questions on S01
        stale = recs("te|S01", 18, 30)
        _, failures = evaluate(stale, min_n=20)
        self.assertEqual(fails(failures, "te|S01", "hit@k"), ["floor"])
        _, failures = evaluate(stale)  # with the default min_n, a 30-item re-run can never pass silently either
        self.assertEqual(fails(failures, "te|S01", "hit@k"), ["n"])

    def test_flatten_lists_every_slice_with_its_reasons(self):
        report, failures = evaluate(recs("te", 140, 150, faithful=150) + recs("ur", 90, 150))
        rows = {(r["slice"], r["metric"]): r for r in flatten(report, failures)}
        self.assertEqual(rows[("ur", "hit@k")]["fails"], ["floor", "parity"])
        self.assertEqual(rows[("ur", "faithfulness")]["fails"], ["n"])
        self.assertEqual(rows[("te", "hit@k")]["fails"], [])
        self.assertIn("gap_lo", rows[("ur", "hit@k")])


if __name__ == "__main__":
    unittest.main()
