"""Tests for router.py, including the behaviour the brief's critic pass fixed and curveballs 1, 2 and 4."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from router import Breaker, Budget, BudgetExceeded, Deployment, ProviderError, filter_residency, route  # noqa: E402


def dep(name, zone="india", usd_in=0.001, usd_out=0.002):
    return Deployment(name, usd_in, usd_out, zone=zone)


def caller(behaviour=None):
    """call_fn that answers "<name> answer" unless behaviour[name] is an exception; records every call."""
    def call_fn(name, request):
        call_fn.calls.append(name)
        outcome = (behaviour or {}).get(name)
        if isinstance(outcome, Exception):
            raise outcome
        return f"{name} answer", 1000, 200
    call_fn.calls = []
    return call_fn


def run(tiers, call_fn, budget=None, accept=lambda text: True, now=0.0):
    return route({"q": "x"}, tiers, budget or Budget(1000, 100), call_fn, accept, 1000, 500, clock=lambda: now)


class BreakerTests(unittest.TestCase):
    def test_opens_at_threshold_then_half_opens_after_cooldown(self):
        b = Breaker(fail_threshold=3, cooldown_s=30)
        for _ in range(3):
            b.record(False, 0)
        self.assertFalse(b.available(10))
        self.assertTrue(b.available(30))  # half-open
        b.record(False, 30)  # one failure while half-open re-opens it
        self.assertFalse(b.available(31))
        b.record(True, 61)
        self.assertEqual((b.fails, b.opened_at), (0, None))

    def test_success_resets_the_failure_count(self):
        b = Breaker(fail_threshold=3)
        for ok in (False, False, True, False, False):
            b.record(ok, 0)
        self.assertEqual(b.fails, 2)
        self.assertTrue(b.available(0))

    def test_429_parks_for_retry_after_without_counting_a_failure(self):
        b = Breaker()
        b.record(False, 0, retry_after=10)
        self.assertEqual(b.fails, 0)
        self.assertFalse(b.available(9.9))
        self.assertTrue(b.available(10))

    def test_spend_cap_429_without_retry_after_parks_until_a_human_acts(self):
        b = Breaker()
        b.record(False, 0, retry_after=math.inf)
        self.assertFalse(b.available(1e9))


class BudgetTests(unittest.TestCase):
    def test_hourly_cap_refuses_before_spending_and_resets_after_an_hour(self):
        b = Budget(monthly_usd=100, hourly_cap_usd=1)
        b.reserve(0.6, 0)
        with self.assertRaises(BudgetExceeded):
            b.reserve(0.6, 10)
        self.assertAlmostEqual(b.spent, 0.6)  # a refused reservation leaves no partial charge
        b.reserve(0.6, 3600)  # new hour window
        self.assertAlmostEqual(b.hour_spent, 0.6)

    def test_monthly_budget_exhausted(self):
        b = Budget(monthly_usd=1, hourly_cap_usd=100)
        b.reserve(0.9, 0)
        with self.assertRaisesRegex(BudgetExceeded, "monthly"):
            b.reserve(0.2, 5000)

    def test_settle_trues_up_to_the_actual_cost(self):
        b = Budget(100, 100)
        b.reserve(1.0, 0)
        b.settle(1.0, 0.25)
        self.assertAlmostEqual(b.spent, 0.25)
        self.assertAlmostEqual(b.hour_spent, 0.25)

    def test_soft_limit_drops_the_priciest_tier_above_80_percent_but_keeps_a_single_tier(self):
        b = Budget(100, 100, spent=80)
        self.assertEqual(b.allowed_tiers([["cheap"], ["strong"]]), [["cheap"]])
        self.assertEqual(b.allowed_tiers([["only"]]), [["only"]])


class RouteTests(unittest.TestCase):
    def test_cheap_tier_answer_accepted_and_strong_never_called(self):
        call = caller()
        text, name, trace = run([[dep("cheap")], [dep("strong")]], call)
        self.assertEqual((name, call.calls), ("cheap", ["cheap"]))
        self.assertEqual(trace[-1], ("cheap", "accepted"))

    def test_quality_miss_escalates_to_the_next_tier_not_the_next_in_chain(self):
        call = caller()
        _, name, trace = run([[dep("cheap-1"), dep("cheap-2")], [dep("strong")]], call,
                             accept=lambda text: not text.startswith("cheap"))
        self.assertEqual(call.calls, ["cheap-1", "strong"])
        self.assertIn(("cheap-1", "rejected:escalate"), trace)

    def test_error_falls_back_within_the_chain_and_refunds_the_reservation(self):
        call, budget = caller({"primary": ProviderError("503")}), Budget(1000, 100)
        backup = dep("backup")
        _, name, _ = run([[dep("primary"), backup]], call, budget)
        self.assertEqual(name, "backup")
        self.assertAlmostEqual(budget.spent, backup.cost(1000, 200))  # the failed call costs nothing

    def test_budget_exceeded_propagates_before_any_call(self):
        call = caller()
        with self.assertRaises(BudgetExceeded):
            run([[dep("cheap")]], call, Budget(1000, hourly_cap_usd=0.0001))
        self.assertEqual(call.calls, [])

    def test_open_breaker_is_skipped_without_a_call(self):
        broken, call = dep("broken"), caller()
        broken.breaker.opened_at, broken.breaker.fails = 0.0, 5
        _, name, trace = run([[broken, dep("ok")]], call, now=1.0)
        self.assertEqual((name, call.calls), ("ok", ["ok"]))
        self.assertIn(("broken", "unavailable"), trace)

    def test_everything_failing_raises_with_the_trace(self):
        call = caller({"a": ProviderError("5xx"), "b": ProviderError("429", retry_after=30)})
        with self.assertRaisesRegex(RuntimeError, "no acceptable answer"):
            run([[dep("a"), dep("b")]], call)


class CurveballTests(unittest.TestCase):
    def test_cb1_retired_model_returns_410_and_the_chain_moves_to_the_successor(self):
        old, new = dep("model-2025-10"), dep("model-2026-06")
        _, name, _ = run([[old, new]], caller({"model-2025-10": ProviderError("410 Gone: model retired")}))
        self.assertEqual(name, "model-2026-06")
        self.assertEqual(old.breaker.fails, 1)

    def test_cb2_runaway_loop_is_throttled_before_it_overspends_the_hourly_cap(self):
        def loop(budget):  # a failing tool call retried every 3 s with context growing by 1,500 tokens
            big = dep("large", usd_in=0.003, usd_out=0.015)
            for step in range(3000):
                tin = 4000 + 1500 * step
                try:
                    route({}, [[big]], budget, lambda n, r: ("retry", tin, 400), lambda t: True, tin, 1024,
                          clock=lambda: step * 3)
                except BudgetExceeded:
                    return step * 3
            return None
        capped = Budget(monthly_usd=3000, hourly_cap_usd=20)
        stopped_at = loop(capped)
        self.assertIsNotNone(stopped_at)
        self.assertLess(stopped_at, 3600)
        self.assertLessEqual(capped.hour_spent, 20)  # the reservation stops it before the cap, not after
        monthly_only = Budget(monthly_usd=3000, hourly_cap_usd=3000)  # the July incident: no burn-rate cap
        self.assertGreater(loop(monthly_only), 3000)

    def test_cb4_regional_outage_opens_the_breaker_and_later_requests_skip_it(self):
        west, south = dep("in-west"), dep("in-south")
        call = caller({"in-west": ProviderError("region down")})
        for i in range(8):
            run([[west, south]], call, now=float(i))
        self.assertEqual(call.calls.count("in-west"), 5)  # five failures open it; the rest skip it
        self.assertEqual(call.calls.count("in-south"), 8)

    def test_cb4_residency_filter_keeps_health_data_in_india_even_when_it_must_queue(self):
        tiers = [[dep("in-west"), dep("us-east", zone="us")], [dep("self-14b", zone="self_hosted")]]
        kept = filter_residency(tiers, {"india", "self_hosted"})
        self.assertEqual([[d.name for d in t] for t in kept], [["in-west"], ["self-14b"]])
        call = caller({"in-west": ProviderError("region down"), "self-14b": ProviderError("maintenance")})
        with self.assertRaises(RuntimeError):  # queue rather than cross a border
            run(kept, call)
        self.assertNotIn("us-east", call.calls)
        self.assertEqual(filter_residency([[dep("us-east", zone="us")]], {"india"}), [])


if __name__ == "__main__":
    unittest.main()
