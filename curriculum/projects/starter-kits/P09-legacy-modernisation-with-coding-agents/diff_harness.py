#!/usr/bin/env python3
"""Differential characterisation harness: the control from brief P09 §7.

The legacy engine is the oracle, the tolerance table is an owned artefact, and dropped or duplicated records
and edited fixtures fail loudly. Kept from the reviewed sketch (tests/test_diff_harness.py covers each):
- billed and statutory fields are exact to the paisa; only the 7-dp intermediate has a tolerance;
- a dropped record is a failure, never a skip; a missing field is a failure;
- a duplicate policy_id in an engine's output stops the run;
- the fixture manifest is a committed hash, so a deleted or edited fixture fails;
- values are compared as Decimal(str(x)), never as floats.
One addition: a value that is not a number is reported as a diff instead of crashing the run.

    python3 diff_harness.py N SEED EXPECTED_SHA256 -- legacy cmd... -- new cmd...
"""
import hashlib
import json
import random
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Rule:
    field: str
    abs_tol: Decimal  # 0 = exact. This table is CODEOWNED by the Appointed Actuary's delegate.
    reason: str


RULES = [Rule(f, Decimal("0"), "billed or statutory: exact to the paisa") for f in ("modal_premium", "rider_premium", "tax_amount")]
RULES.append(Rule("mortality_rate", Decimal("0.0000001"), "intermediate; legacy holds 7 dp in COMP-3"))
VALUATION = date(2026, 10, 1)


def gen_fixtures(n: int, seed: int) -> list[dict]:
    rng, out = random.Random(seed), []
    for i in range(n):
        age = rng.choice([18, 44, 45, 59, 60, 65]) if rng.random() < 0.3 else rng.randint(18, 65)
        shift = rng.choice([-183, -182, 0, 182, 183, rng.randint(-364, 364)])  # age-nearest vs last-birthday
        dob = date(1980, 2, 29) if rng.random() < 0.01 else date(VALUATION.year - age, 10, 1) + timedelta(days=shift)
        out.append({"policy_id": f"FX{seed}-{i:07d}", "valuation_date": VALUATION.isoformat(), "dob": dob.isoformat(),
                    "product": rng.choice(["TL01", "TL02", "EN05", "EN09W"]),  # EN09W: withdrawn, still in force
                    "term": rng.choice([5, 10, 15, 20, 25, 30]), "mode": rng.choice(["A", "H", "Q", "M"]),
                    "sum_assured": str(rng.choice([100000, 250000, 999999, 5000000])), "smoker": rng.random() < 0.2})
    return out


def manifest(fixtures: list[dict]) -> str:  # committed hash: a deleted or edited fixture fails CI
    return hashlib.sha256(json.dumps(fixtures, sort_keys=True).encode()).hexdigest()


def run_batch(cmd: list[str], fixtures: list[dict]) -> dict[str, dict]:
    stdin = "".join(json.dumps(f) + "\n" for f in fixtures)  # both engines speak JSONL on stdin/stdout
    out = subprocess.run(cmd, input=stdin, capture_output=True, text=True, check=True, timeout=3600).stdout
    rows = [json.loads(line) for line in out.splitlines() if line.strip()]
    if len({r["policy_id"] for r in rows}) != len(rows):  # a duplicate row could hide a wrong premium
        sys.exit(f"duplicate policy_id in output of {' '.join(cmd)}")
    return {r["policy_id"]: r for r in rows}


def compare(fixtures: list[dict], legacy: dict[str, dict], new: dict[str, dict]) -> list[dict]:
    diffs = []
    for pid in (fx["policy_id"] for fx in fixtures):
        old, cand = legacy.get(pid), new.get(pid)
        if old is None or cand is None:  # a dropped record is a failure, never a skip
            diffs.append({"id": pid, "error": "no output from " + ("legacy" if old is None else "new")})
            continue
        for r in RULES:
            if r.field not in old or r.field not in cand:
                diffs.append({"id": pid, "field": r.field, "error": "field missing"})
                continue
            try:
                delta = abs(Decimal(str(cand[r.field])) - Decimal(str(old[r.field])))
            except InvalidOperation:
                diffs.append({"id": pid, "field": r.field, "error": "not a number", "new": cand[r.field]})
                continue
            if delta > r.abs_tol:
                diffs.append({"id": pid, "field": r.field, "legacy": old[r.field], "new": cand[r.field]})
    return diffs


def main(argv: list[str]) -> int:
    n, seed, expected = int(argv[1]), int(argv[2]), argv[3]
    s1, s2 = [i for i, a in enumerate(argv) if a == "--"][:2]
    if manifest(fixtures := gen_fixtures(n, seed)) != expected:
        sys.exit("fixture manifest changed: generator or seed edited without review")
    diffs = compare(fixtures, run_batch(argv[s1 + 1:s2], fixtures), run_batch(argv[s2 + 1:], fixtures))
    print(json.dumps({"fixtures": n, "mismatches": len(diffs), "sample": diffs[:20]}, indent=2))
    return 1 if diffs else 0


if __name__ == "__main__":  # diff_harness.py N SEED EXPECTED_SHA256 -- legacy cmd... -- new cmd...
    sys.exit(main(sys.argv))
