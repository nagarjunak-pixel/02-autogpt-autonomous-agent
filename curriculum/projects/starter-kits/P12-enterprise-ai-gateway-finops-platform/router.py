"""Routing cascade with budget guard and circuit breaker: the brief's §7 control, kept as the reviewed sketch.

Library-agnostic: call_fn wraps whichever gateway or SDK you use. Two small additions, both marked:
- Deployment.zone and filter_residency(), the §7 "production gap" that applies residency BEFORE fallback, so an
  outage never moves Indian health data offshore (curveball 4);
- ProviderError, a ready-made exception for call_fn that carries .retry_after (seconds, or math.inf if not retryable).
"""
import time
from dataclasses import dataclass, field


class BudgetExceeded(Exception):
    pass


class ProviderError(Exception):  # addition: timeouts, 5xx, 404/410 (retired model) and 429s
    def __init__(self, message="provider error", retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after  # 429: Retry-After seconds; math.inf for a spend-cap 429 (wait for a human)


@dataclass
class Breaker:  # per deployment (provider x region x model)
    fail_threshold: int = 5
    cooldown_s: float = 30.0
    fails: int = 0
    opened_at: float | None = None
    parked_until: float = 0.0

    def available(self, now: float) -> bool:  # after cooldown: half-open, one failure re-opens
        return now >= self.parked_until and (self.opened_at is None or now - self.opened_at >= self.cooldown_s)

    def record(self, ok: bool, now: float, retry_after: float | None = None) -> None:
        if retry_after is not None:  # 429: honour Retry-After, and do not count it as a failure
            self.parked_until = now + retry_after
            return
        if ok:
            self.fails, self.opened_at = 0, None
        else:
            self.fails += 1
            if self.fails >= self.fail_threshold:
                self.opened_at = now


@dataclass
class Budget:  # per virtual key; money in USD, from a price table
    monthly_usd: float
    hourly_cap_usd: float  # burn-rate cap: catches runaway agent loops
    spent: float = 0.0
    hour_start: float = 0.0
    hour_spent: float = 0.0

    def reserve(self, est: float, now: float) -> None:
        if now - self.hour_start >= 3600:
            self.hour_start, self.hour_spent = now, 0.0
        if self.spent + est > self.monthly_usd:
            raise BudgetExceeded("monthly budget exhausted")
        if self.hour_spent + est > self.hourly_cap_usd:
            raise BudgetExceeded("hourly burn-rate cap hit")
        self.spent += est
        self.hour_spent += est

    def settle(self, est: float, actual: float) -> None:
        self.spent += actual - est
        self.hour_spent += actual - est

    def allowed_tiers(self, tiers: list) -> list:  # soft limit: above 80% spend, drop the priciest tier
        return tiers if self.spent < 0.8 * self.monthly_usd or len(tiers) == 1 else tiers[:-1]


@dataclass
class Deployment:
    name: str
    usd_per_1k_in: float
    usd_per_1k_out: float
    breaker: Breaker = field(default_factory=Breaker)
    zone: str = "global"  # addition: residency zone (india, self_hosted, eu, us)

    def cost(self, tin: int, tout: int) -> float:
        return tin / 1000 * self.usd_per_1k_in + tout / 1000 * self.usd_per_1k_out


def filter_residency(tiers: list, allowed_zones: set) -> list:
    """Addition: keep only deployments in the allowed zones, before any fallback. Empty tiers are dropped, so a
    route whose in-zone deployments are all down fails (and queues) instead of crossing a border."""
    kept = [[d for d in tier if d.zone in allowed_zones] for tier in tiers]
    return [tier for tier in kept if tier]


def route(request, tiers, budget, call_fn, accept, est_in, est_out, clock=time.monotonic):
    """tiers: cheapest first; each tier is a fallback chain of Deployments (other provider/region).
    call_fn(name, request) -> (text, tokens_in, tokens_out) or raises. accept(text) -> bool.
    On a 429 call_fn's exception carries .retry_after: the Retry-After seconds, or math.inf if not retryable."""
    trace = []
    for tier in budget.allowed_tiers(tiers):
        for dep in tier:
            if not dep.breaker.available(clock()):
                trace.append((dep.name, "unavailable"))
                continue
            est = dep.cost(est_in, est_out)
            budget.reserve(est, clock())  # may raise BudgetExceeded
            try:
                text, tin, tout = call_fn(dep.name, request)
            except Exception as e:  # timeout, 429, 5xx: try next in chain
                budget.settle(est, 0.0)
                dep.breaker.record(False, clock(), getattr(e, "retry_after", None))
                trace.append((dep.name, f"error:{type(e).__name__}"))
                continue
            dep.breaker.record(True, clock())
            budget.settle(est, dep.cost(tin, tout))
            if accept(text):
                trace.append((dep.name, "accepted"))
                return text, dep.name, trace
            trace.append((dep.name, "rejected:escalate"))
            break  # quality miss -> next tier
    raise RuntimeError(f"no acceptable answer: {trace}")
