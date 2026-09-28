#!/usr/bin/env python3
"""Stand-in for the legacy PRMCALC COBOL engine at Bhuvika Mutual Life (fictional): the ORACLE.

It reproduces the eight seeded quirks of brief §3 in plain Python `decimal` and speaks the §7 JSONL protocol:
    python3 legacy_prmcalc.py < fixtures.jsonl > legacy_out.jsonl
With GnuCOBOL 3.2 and the course's cobol/PRMCALC*.cbl, swap in the real binary:
    python3 eval_harness.py --legacy-cmd "./prmcalc-jsonl"
Mutants for the oracle-strength metric are LegacyEngine(rates, **overrides) with one knob changed.
Do NOT "fix" anything here. The legacy behaviour defines correct, quirks included (brief §15).
"""
import argparse
import csv
import json
import sys
from datetime import date
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP, Decimal
from pathlib import Path

ROUNDING = {"half_up": ROUND_HALF_UP, "down": ROUND_DOWN, "half_even": ROUND_HALF_EVEN, "up": ROUND_UP}
DEFAULTS = {
    "monthly_round": "half_up",     # quirk 1: monthly-mode premiums round half-up to the rupee,
    "rider_round": "down",          #          rider premiums truncate to the rupee (* PER IRDA CIRC - DO NOT CHANGE)
    "other_round": "half_up",       # annual, half-yearly and quarterly: half-up to the paisa
    "tax_round": "half_up",
    "anb_products": ["TL01", "EN05"],  # quirk 2: these use age nearest birthday; the rest age last birthday
    "anb_days": 183,                # days after the last birthday at which "nearest" rounds up
    "comp3_dp": 7,                  # quirk 3: COMP-3 intermediates hold 7 dp ...
    "comp3_round": "down",          #          ... and are truncated on MOVE
    "leap_birthday": [2, 28],       # quirk 4: a 29 Feb birthday falls on 28 Feb in common years
    "pivot": 50,                    # quirk 5: two-digit years: YY >= 50 -> 19YY, else 20YY
    "price_withdrawn": True,        # quirk 6: withdrawn product EN09W is still priced
    "first_match": True,            # quirk 7: duplicate rate rows; COBOL SEARCH takes the first match
    "gst_switch": "2025-09-22",     # quirk 8: individual life exempt from this due date; group stays at 18%
    "gst_rate": "0.18", "tax_group": True, "tax_on_rider": True,
    "sa_disc_from": 1000000, "sa_disc": "0.02",          # large-sum-assured discount
    "modal": {"A": "1", "H": "0.51", "Q": "0.26", "M": "0.0875"},
    "age_load": "0.0125", "rider_rate": "0.00045", "use_smoker": True, "band_upper_inclusive": True,
}
RATES = Path(__file__).resolve().parent / "data" / "rate_table.csv"


def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


class LegacyEngine:
    def __init__(self, rates_path=RATES, **overrides):
        self.cfg = dict(DEFAULTS, **overrides)
        with open(rates_path, newline="") as f:
            self.rates = list(csv.DictReader(f))

    def dob(self, s):
        if len(s) == 6:  # YYMMDD from the old renewal file
            yy = int(s[:2])
            return date((1900 if yy >= self.cfg["pivot"] else 2000) + yy, int(s[2:4]), int(s[4:6]))
        return date.fromisoformat(s)

    def birthday(self, dob, year):
        if (dob.month, dob.day) == (2, 29) and not is_leap(year):
            return date(year, *self.cfg["leap_birthday"])
        return dob.replace(year=year)

    def age(self, dob, on, product):
        last = self.birthday(dob, on.year)
        if last > on:
            last = self.birthday(dob, on.year - 1)
        alb = last.year - dob.year
        return alb + 1 if product in self.cfg["anb_products"] and (on - last).days >= self.cfg["anb_days"] else alb

    def rate_row(self, product, age, term, smoker):
        inside = (lambda x, lo, hi: int(lo) <= x <= int(hi)) if self.cfg["band_upper_inclusive"] else \
                 (lambda x, lo, hi: int(lo) <= x < int(hi))
        hits = [r for r in self.rates if r["product"] == product and r["smoker"] == ("Y" if smoker else "N")
                and inside(age, r["age_from"], r["age_to"]) and inside(term, r["term_from"], r["term_to"])]
        if not hits:
            raise ValueError(f"NO RATE ROW product={product} age={age} term={term}")
        return hits[0] if self.cfg["first_match"] else hits[-1]

    def price(self, p):
        c, D = self.cfg, Decimal
        if p["product"] == "EN09W" and not c["price_withdrawn"]:
            return {"policy_id": p["policy_id"], "status": "REJECTED", "reason": "product withdrawn"}
        try:
            age = self.age(self.dob(p["dob"]), date.fromisoformat(p["valuation_date"]), p["product"])
            row = self.rate_row(p["product"], age, int(p["term"]), p["smoker"] and c["use_smoker"])
        except ValueError as e:
            return {"policy_id": p["policy_id"], "status": "REJECTED", "reason": str(e)}
        load = 1 + D(c["age_load"]) * (age - int(row["age_from"]))
        mortality = (D(row["rate_per_mille"]) / 1000 * load).quantize(D(1).scaleb(-c["comp3_dp"]), ROUNDING[c["comp3_round"]])
        sa, factor = D(p["sum_assured"]), D(c["modal"][p["mode"]])
        annual = sa * mortality
        if sa >= c["sa_disc_from"]:
            annual *= 1 - D(c["sa_disc"])
        if p["mode"] == "M":
            modal = (annual * factor).quantize(D("1"), ROUNDING[c["monthly_round"]])
        else:
            modal = (annual * factor).quantize(D("0.01"), ROUNDING[c["other_round"]])
        rider = (sa * D(c["rider_rate"]) * factor).quantize(D("1"), ROUNDING[c["rider_round"]])
        due, group = date.fromisoformat(p.get("due_date") or p["valuation_date"]), bool(p.get("group"))
        taxed = c["tax_group"] if group else due < date.fromisoformat(c["gst_switch"])
        base = modal + (rider if c["tax_on_rider"] else 0)
        tax = (base * D(c["gst_rate"])).quantize(D("0.01"), ROUNDING[c["tax_round"]]) if taxed else D("0")
        money = lambda x: f"{x:.2f}"
        return {"policy_id": p["policy_id"], "status": "OK", "age": age, "mortality_rate": str(mortality),
                "modal_premium": money(modal), "rider_premium": money(rider), "tax_amount": money(tax),
                "total_due": money(modal + rider + tax)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Legacy PRMCALC stand-in: JSONL policies on stdin, JSONL premiums on stdout")
    ap.add_argument("--rates", default=str(RATES))
    engine = LegacyEngine(ap.parse_args().rates)
    for line in sys.stdin:
        if line.strip():
            print(json.dumps(engine.price(json.loads(line))))
