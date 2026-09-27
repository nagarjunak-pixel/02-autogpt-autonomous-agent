"""Per-language evaluation gate (brief §7): hit@k and faithfulness per slice, bootstrap CIs, parity against Telugu.

Kept from the reviewed sketch, and covered by tests/test_language_gate.py:
- a slice passes only if the CI LOWER bound clears the floor, not the mean (hit@5 0.85, faithfulness 0.93);
- parity uses independent resampling (different queries per language), and a slice fails parity only when the
  gap to Telugu is CREDIBLY larger than 0.07 (the gap's lower bound is above it);
- a slice with fewer than min_n items fails as "insufficient_n": it is reported, never passed silently;
- unanswerable queries (empty gold_ids) do not count towards hit@k, and escalations (faithful=None) do not count
  towards faithfulness;
- parity is computed only when the reference slice itself has enough items;
- any slice key works ("ur", "ur|voice", "te|S01"), and results are deterministic for a fixed seed.
Added: flatten() turns the report into JSON-friendly rows. Standard library only.
"""
import random
from collections import defaultdict
from statistics import mean

FLOORS = {"hit@k": 0.85, "faithfulness": 0.93}


def hit_at_k(gold_ids, retrieved_ids, k):
    return 1.0 if set(gold_ids) & set(retrieved_ids[:k]) else 0.0


def bootstrap(xs, stat=mean, n_boot=2000, alpha=0.05, seed=13):
    rng = random.Random(seed)
    boots = sorted(stat(rng.choices(xs, k=len(xs))) for _ in range(n_boot))
    return stat(xs), boots[int(n_boot * alpha / 2)], boots[int(n_boot * (1 - alpha / 2)) - 1]


def diff_ci(a, b, n_boot=2000, alpha=0.05, seed=13):
    """CI for mean(a) - mean(b) with independent resampling (different items per language)."""
    rng = random.Random(seed)
    d = sorted(mean(rng.choices(a, k=len(a))) - mean(rng.choices(b, k=len(b))) for _ in range(n_boot))
    return mean(a) - mean(b), d[int(n_boot * alpha / 2)], d[int(n_boot * (1 - alpha / 2)) - 1]


def evaluate(records, k=5, floors=None, ref_lang="te", max_gap=0.07, min_n=100):
    """records: dicts with lang (any slice key, e.g. "ur" or "ur|ivr"), gold_ids (empty = unanswerable),
    retrieved_ids, faithful (1/0 from a calibrated judge or native rater; None if the bot escalated)."""
    floors = floors or FLOORS                      # gate on the CI lower bound
    per = defaultdict(lambda: {"hit@k": [], "faithfulness": []})
    for r in records:
        if r["gold_ids"]:
            per[r["lang"]]["hit@k"].append(hit_at_k(r["gold_ids"], r["retrieved_ids"], k))
        if r.get("faithful") is not None:
            per[r["lang"]]["faithfulness"].append(float(r["faithful"]))
    report, failures = {}, []
    for lang, metrics in sorted(per.items()):
        for name, xs in metrics.items():
            if len(xs) < min_n:                   # too few items: report, never pass silently
                report[(lang, name)] = ("insufficient_n", len(xs)); failures.append((lang, name, "n"))
                continue
            m, lo, hi = bootstrap(xs)
            report[(lang, name)] = (round(m, 3), round(lo, 3), round(hi, 3), len(xs))
            if lo < floors[name]:                  # must be credibly above the floor, not just on average
                failures.append((lang, name, "floor"))
            ref = per.get(ref_lang, {}).get(name, [])
            if lang != ref_lang and len(ref) >= min_n:
                g, glo, ghi = diff_ci(ref, xs)        # parity gap vs the reference language
                report[(lang, name, "gap_vs_" + ref_lang)] = (round(g, 3), round(glo, 3), round(ghi, 3))
                if glo > max_gap:                     # gap is credibly larger than allowed
                    failures.append((lang, name, "parity"))
    return report, failures


def flatten(report, failures):
    """One row per (slice, metric): value, CI, n, parity gap and the reasons it fails (empty list = passes)."""
    rows = {}
    for key, val in report.items():
        lang, name = key[0], key[1]
        row = rows.setdefault((lang, name), {"slice": lang, "metric": name, "fails": []})
        if len(key) == 3:
            row["gap"], row["gap_lo"], row["gap_hi"] = val
        elif val[0] == "insufficient_n":
            row["n"] = val[1]
        else:
            row["mean"], row["lo"], row["hi"], row["n"] = val
    for lang, name, why in failures:
        rows[(lang, name)]["fails"].append(why)
    return [rows[k] for k in sorted(rows)]
