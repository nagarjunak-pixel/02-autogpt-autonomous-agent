"""The department's application-status API, as the brief's mock (§3): it needs app_id plus the matching registered
mobile, injects 503s, and serves some stale records (an old `as_of`). Latency (p95 1.8 s) is not simulated."""
import random


class ServiceUnavailable(Exception):
    """HTTP 503 from the status API."""


def last10(mobile):
    digits = "".join(ch for ch in str(mobile or "") if ch.isdigit())
    return digits[-10:]


class MockStatusAPI:
    def __init__(self, applications, fault_rate=0.02, seed=0):
        self.apps = {a["app_id"]: a for a in applications}
        self.rng, self.fault_rate = random.Random(seed), fault_rate
        self.calls = self.failures = 0

    def get(self, app_id, mobile):
        self.calls += 1
        if self.rng.random() < self.fault_rate:
            self.failures += 1
            raise ServiceUnavailable("503 Service Unavailable")
        a = self.apps.get(app_id)
        if not a or len(last10(mobile)) != 10 or last10(mobile) != last10(a["mobile"]):
            return {"found": False}  # the same answer for "no such app" and "wrong mobile": no enumeration signal
        return {"found": True, "app_id": app_id, "scheme_id": a["scheme_id"], "status": a["status"],
                "reason_code": a["reason_code"], "as_of": a["as_of"]}
