"""Evaluation harness for the P12 kit: scores a system against the brief's §5 acceptance criteria, offline.

python3 eval_harness.py [--system baseline|adapter] [--limit N] [--manifest PATH]
§5 has no IDs, so AC-1 ... AC-13 are its 13 rows in order (see README). Prints AC-ID | metric | value | threshold |
PASS/FAIL, writes results/<system>.json and exits 0 even when thresholds fail. Every run of the router uses a
simulated clock, so results are deterministic except the measured gateway overhead (AC-7).
"""
import argparse
import csv
import importlib
import json
import math
import random
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from router import Budget, BudgetExceeded, Deployment, ProviderError, route

HERE = Path(__file__).resolve().parent
ID_LABELS = ("aadhaar", "pan", "card", "iban", "gstin")
UNLIMITED = 1e12


def load(data, limit):
    def j(name):
        return json.loads((data / name).read_text(encoding="utf-8"))

    def rows(name, cut=True):  # --limit trims the sets a real model would be called on
        out = [json.loads(x) for x in (data / name).read_text(encoding="utf-8").splitlines()]
        return out[:limit] if limit and cut else out
    w = {"use_cases": j("use_cases.json"), "registry": j("registry.json"),
         "request_log": rows("request_log.jsonl", False), "discovery": rows("discovery_logs.jsonl", False),
         "directory": j("directory.json"), "truth": j("shadow_ai_truth.json"), "dlp": rows("dlp_set.jsonl"),
         "probes": rows("isolation_probes.jsonl", False),
         "mcp": j("mcp_registry.json"), "mcp_calls": rows("mcp_calls.jsonl"), "loop": j("loop_sim.json"),
         "drill": j("drill.json"), "fx": j("billing/fx.json"), "invoices": j("billing/invoices.json")}
    w["golden"] = {a: rows(f"golden_{a}.jsonl") for a in j("meta.json")["anchors"]}
    w["exports"] = {}
    for name in ("provider_a_ptu", "provider_b_tokens", "provider_c_requests", "onprem_gpu"):
        with open(data / "billing" / f"{name}.csv", encoding="utf-8") as f:
            w["exports"][name] = list(csv.DictReader(f))
    return w


def deployments(registry):
    """Fresh Deployment objects (fresh breakers), addressable by name and by alias."""
    deps = {d["name"]: Deployment(d["name"], d["usd_per_1k_in"], d["usd_per_1k_out"], zone=d["zone"])
            for d in registry["deployments"]}
    deps.update({alias: deps[name] for alias, name in registry["aliases"].items()})
    return deps


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def pct(xs, p):
    s = sorted(xs)
    return s[max(0, math.ceil(p / 100 * len(s)) - 1)] if s else math.inf


def lower_bound(diffs, reps=1000, seed=7):  # one-sided 95% bootstrap lower bound of a mean
    rng, n = random.Random(seed), len(diffs)
    means = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(reps))
    return means[int(0.05 * reps)]


def cascade(system, w, anchor):
    """AC-2: the §7 router with the system's validator, against strong-only, paired on the golden set."""
    uc = next(u for u in w["use_cases"] if u["anchor"] == anchor)
    tier = {d["name"]: d["tier"] for d in w["registry"]["deployments"]}
    tiers = system.tiers_for(uc, deployments(w["registry"]))
    strong_dep = tiers[-1][0]
    cost, strong_cost, ok, strong_ok, false_acc, escalated = [], [], [], [], [], 0
    for it in w["golden"][anchor]:
        budget = Budget(UNLIMITED, UNLIMITED)
        out, _, trace = route(it, tiers, budget, lambda name, item: (tier[name], item["tokens_in"], item["tokens_out"]),
                              lambda t: t == "strong" or system.accept(anchor, it["cheap"]["signals"]),
                              it["tokens_in"], it["tokens_out"], clock=lambda: 0.0)
        cost.append(budget.spent)
        strong_cost.append(strong_dep.cost(it["tokens_in"], it["tokens_out"]))
        ok.append(it["cheap"]["correct"] if out == "cheap" else it["strong"]["correct"])
        strong_ok.append(it["strong"]["correct"])
        escalated += out == "strong"
        if not it["cheap"]["correct"]:
            false_acc.append(out == "cheap")
    change = (sum(cost) / max(1, sum(ok))) / (sum(strong_cost) / max(1, sum(strong_ok))) - 1
    diffs = [int(a) - int(b) for a, b in zip(ok, strong_ok)]
    return {"change": change, "delta_pp": 100 * mean(diffs), "lb_pp": 100 * lower_bound(diffs),
            "false_accept": mean(false_acc), "escalation": escalated / len(ok)}


def drill(system, w, seed, down):
    """AC-6: requests through the router while one provider region is down (or not, for the baseline p95)."""
    cfg, reg, zones = w["drill"], {d["name"]: d for d in w["registry"]["deployments"]}, w["registry"]["zones"]
    mix, chaos, deps, clock = random.Random(seed), random.Random(seed + 100), deployments(w["registry"]), [0.0]
    ucs, results = w["use_cases"], []
    for _ in range(cfg["requests_per_drill"]):
        u = mix.choices(ucs, [x["traffic"]["rpm"] for x in ucs])[0]
        tin = int(math.exp(mix.gauss(u["prompt_tokens"]["mu"], 0.5)))
        tout = int(math.exp(mix.gauss(u["output_tokens"]["mu"], 0.5)))
        clock[0] += cfg["interval_s"]
        spent = [0.0]

        def call_fn(name, request):
            d, r = reg[name], chaos.random()
            if down and d["region"] == cfg["down_region"]:
                spent[0] += cfg["timeout_ms"]
                raise ProviderError("region down")
            if r < cfg["p_5xx"]:
                spent[0] += cfg["error_ms"]
                raise ProviderError("5xx")
            if r < cfg["p_5xx"] + cfg["p_429"]:
                spent[0] += 50
                raise ProviderError("429", retry_after=5)
            spent[0] += d["base_ms"] * math.exp(chaos.gauss(0, 0.25)) + tout * d["ms_per_out_token"]
            return "ok", tin, tout
        try:
            _, name, _ = route(u, system.tiers_for(u, deps), Budget(UNLIMITED, UNLIMITED), call_fn, lambda _: True,
                               tin, tout, clock=lambda: clock[0])
            results.append((True, spent[0], reg[name]["zone"] in zones[u["residency"]]))
        except (RuntimeError, BudgetExceeded):
            results.append((False, spent[0], True))  # no answer: the request queues or fails, but stays in zone
    return {"success": mean(r[0] for r in results), "p95": pct([r[1] for r in results if r[0]], 95),
            "violations": sum(not r[2] for r in results)}


def runaway_loop(system, w):
    """AC-8 and curveball 2: an agent retrying a failing tool call with growing context, on a simulated clock."""
    cfg = w["loop"]
    uc = next(u for u in w["use_cases"] if u["id"] == cfg["use_case"])
    budget, dep = Budget(*system.budget_for(uc)), deployments(w["registry"])[cfg["deployment"]]
    hour_spend, t_cap, t_throttle, last = 0.0, None, None, 0.0
    for step in range(cfg["max_steps"]):
        t, tin = step * cfg["interval_s"], cfg["start_tokens_in"] + step * cfg["growth_per_step"]
        try:
            route({}, [[dep]], budget, lambda n, r: ("tool failed, retrying", tin, cfg["tokens_out"]), lambda _: True,
                  tin, cfg["max_tokens"], clock=lambda: t)
        except BudgetExceeded:
            t_throttle = t
            break
        last = dep.cost(tin, cfg["tokens_out"])
        if t < 3600:
            hour_spend += last
            if t_cap is None and hour_spend > cfg["policy_hourly_cap_usd"]:
                t_cap = t
    after_cap = 0 if t_cap is None else ((t_throttle if t_throttle is not None else math.inf) - t_cap)
    return {"after_cap_s": max(0, after_cap), "overspend_usd": max(0.0, hour_spend - cfg["policy_hourly_cap_usd"]),
            "one_request_usd": last, "spent_usd": budget.spent}


def row(ac, metric, shown, threshold, ok):
    return {"ac": ac, "metric": metric, "value": shown, "threshold": threshold,
            "status": "N/A (not computable offline)" if ok is None else ("PASS" if ok else "FAIL")}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--system", default="baseline", help="module exposing SYSTEM: baseline or adapter")
    ap.add_argument("--limit", type=int, default=0, help="score only the first N rows of each set (saves API spend)")
    ap.add_argument("--manifest", default=str(HERE / "data" / "deploy_manifest.json"), help="deploy manifest to audit")
    ap.add_argument("--data", default=str(HERE / "data"))
    args = ap.parse_args(argv)
    mod = importlib.import_module(args.system)
    getattr(mod, "check_config", lambda: None)()
    system, w = mod.SYSTEM, load(Path(args.data), args.limit)
    ucs, reg = w["use_cases"], w["registry"]
    m = []

    # AC-1 share of LLM spend through the gateway (the synthetic month is mid-pilot: 3 BUs onboarded)
    log = w["request_log"]
    share = sum(r["cost_usd"] for r in log if r["path"] == "gateway") / sum(r["cost_usd"] for r in log)
    m.append(row("AC-1", "share of LLM spend through the gateway (synthetic month)", f"{share:.3f}", ">= 0.90",
                 share >= 0.90))

    # AC-2 cost per successful outcome with non-inferior quality, per anchor
    anchors = {a: cascade(system, w, a) for a in w["golden"]}
    for a, r in anchors.items():
        m.append(row("AC-2", f"{a}: cost/success change; quality delta (LB)",
                     f"{r['change']:+.0%}; {r['delta_pp']:+.1f} pp ({r['lb_pp']:+.1f})", "<= -30%; LB > -2 pp",
                     r["change"] <= -0.30 and r["lb_pp"] > -2))

    # AC-3 chargeback: ledger vs invoices, unallocated share
    alloc = system.allocate(w["exports"], w["request_log"], ucs, w["fx"])
    invoiced = sum(v["total"] * w["fx"][v["currency"]] for v in w["invoices"].values())
    ledger = sum(alloc["by_bu"].values()) + alloc["platform"] + alloc["unallocated"]
    m += [row("AC-3", "ledger total vs invoiced", f"{ledger / invoiced - 1:+.2%}", "within +/-2%",
              abs(ledger / invoiced - 1) <= 0.02),
          row("AC-3", "unallocated share of ledger", f"{alloc['unallocated'] / ledger:.1%}", "<= 3%",
              alloc["unallocated"] / ledger <= 0.03)]

    # AC-4 shadow-AI discovery against the 40 seeded cases
    findings = system.discover(w["discovery"], w["directory"])
    flagged = {lid for f in findings for lid in f["line_ids"]}
    seeded = {lid for c in w["truth"] for lid in c["line_ids"]}
    found = [c for c in w["truth"] if flagged & set(c["line_ids"])]
    complete = mean(all(f.get(k) for k in ("owner", "data_class", "risk_tier")) for f in findings)
    m += [row("AC-4", f"seeded shadow-AI recall ({len(w['truth'])} cases)", f"{len(found) / len(w['truth']):.3f}",
              ">= 0.90", len(found) / len(w["truth"]) >= 0.90),
          row("AC-4", f"findings with owner, data class and risk tier ({len(findings)})", f"{complete:.3f}", "1.00",
              complete == 1 and bool(findings)),
          row("AC-5", "gateway availability", "-", "99.95% monthly", None)]

    # AC-6 failover drill: primary region down, three drills (pass^3), residency held (curveball 4)
    drills = [(drill(system, w, s, False), drill(system, w, s, True)) for s in (1, 2, 3)]
    passed = [d["success"] >= 0.99 and d["p95"] <= 2 * b["p95"] for b, d in drills]
    worst_ratio = max(d["p95"] / b["p95"] for b, d in drills)
    violations = sum(d["violations"] for _, d in drills)
    m += [row("AC-6", "failover drill success, worst of 3", f"{min(d['success'] for _, d in drills):.3f}", ">= 0.99",
              min(d["success"] for _, d in drills) >= 0.99),
          row("AC-6", "failover p95 vs normal p95, worst of 3", f"{worst_ratio:.2f}x", "<= 2x", worst_ratio <= 2),
          row("AC-6", "pass^3 over 3 drills", f"{sum(passed)}/3", "3/3", all(passed)),
          row("AC-6", "requests served outside their residency zone (curveball 4)", violations, "= 0", violations == 0)]

    # AC-9 DLP, and AC-7 gateway overhead measured on the same pass (auth + DLP + cache key + budget)
    key_owner = {u["virtual_key"]: u["bu"] for u in ucs}
    tp = fp = 0
    per_label, by_enc, by_lang = defaultdict(list), defaultdict(list), defaultdict(list)
    blocked_clean, overhead = [], []
    budget = Budget(UNLIMITED, UNLIMITED)
    for it in w["dlp"]:
        t0 = time.perf_counter()
        system.authorise("vk-fmcg-01", "fmcg", key_owner)
        found_labels = system.detect_pii(it["text"])
        system.cache_key("fmcg", it["text"])
        budget.reserve(0.001, 0.0)
        budget.settle(0.001, 0.001)
        overhead.append((time.perf_counter() - t0) * 1000)
        label = it["label"]
        fp += len(found_labels - {label})
        if label == "none":
            blocked_clean.append(bool(found_labels))
        else:
            tp += label in found_labels
            per_label[label].append(label in found_labels)
            by_lang[it["lang"]].append(label in found_labels)
            if label in ID_LABELS:
                by_enc[it["encoding"]].append(label in found_labels)
    id_recall = mean(x for lab in ID_LABELS for x in per_label[lab])
    nh_recall, precision = mean(per_label["name_health"]), tp / max(1, tp + fp)
    limit_ms = 120 if getattr(system, "ML_DLP", False) else 30
    m += [row("AC-7", "gateway overhead p95, policy path (this machine, 1 process)", f"{pct(overhead, 95):.2f} ms",
              f"<= {limit_ms} ms", pct(overhead, 95) <= limit_ms)]

    # AC-8 runaway loop (curveball 2)
    loop = runaway_loop(system, w)
    m += [row("AC-8", "time to throttle after the hourly cap", f"{loop['after_cap_s']:.0f} s", "<= 60 s",
              loop["after_cap_s"] <= 60),
          row("AC-8", "overspend past the hourly cap", f"USD {loop['overspend_usd']:.2f}",
              f"<= 1 request (USD {loop['one_request_usd']:.2f})", loop["overspend_usd"] <= loop["one_request_usd"])]
    m += [row("AC-9", "DLP recall, checksum-valid IDs", f"{id_recall:.3f}", ">= 0.97", id_recall >= 0.97),
          row("AC-9", "DLP recall, names + health", f"{nh_recall:.3f}", ">= 0.90", nh_recall >= 0.90),
          row("AC-9", "DLP precision", f"{precision:.3f}", ">= 0.90", precision >= 0.90),
          row("AC-9", f"false blocks on clean prompts and decoys ({len(blocked_clean)})", f"{mean(blocked_clean):.3%}",
              "<= 0.5%", mean(blocked_clean) <= 0.005)]

    # AC-10 isolation: a fresh cache per probe pair; key use checked against the key's owning BU
    cross_hits = same_hits = same = cross_keys = 0
    for p in w["probes"]:
        if p["kind"] == "cache_pair":
            hit = system.cache_key(p["bu_b"], p["prompt"]) == system.cache_key(p["bu_a"], p["prompt"])
            if p["bu_a"] == p["bu_b"]:
                same, same_hits = same + 1, same_hits + hit
            else:
                cross_hits += hit
        else:
            allowed = system.authorise(p["vkey"], p["caller_bu"], key_owner)
            cross_keys += allowed and key_owner[p["vkey"]] != p["caller_bu"]
    pairs = sum(p["kind"] == "cache_pair" for p in w["probes"])
    m += [row("AC-10", f"cross-BU cache hits ({pairs} probe pairs)", cross_hits, "= 0", cross_hits == 0),
          row("AC-10", "cross-BU virtual-key use accepted", cross_keys, "= 0", cross_keys == 0)]

    # AC-11 lifecycle lint (curveball 1: which use cases hit the retiring model)
    refs = [ref for tiers in system.ROUTES.values() for chain in tiers for ref in chain]
    aliased = mean(ref in reg["aliases"] for ref in refs)
    dated = mean(bool(d["retires"]) for d in reg["deployments"])
    m += [row("AC-11", f"route entries that are registry aliases ({len(refs)})", f"{aliased:.3f}", "1.00",
              aliased == 1),
          row("AC-11", "deployments with a retirement date", f"{dated:.3f}", "1.00", dated == 1)]
    notice = reg["retirement_notices"][0]
    retiring = {d["name"] for d in reg["deployments"] if d["model"] == notice["model"]}
    deps = deployments(reg)
    dependent = [u["id"] for u in ucs if retiring & {d.name for t in system.tiers_for(u, deps) for d in t}]

    # AC-12 supply chain: deploy audit of the manifest (curveball 3: what the mirror served)
    man = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    by_digest = mean(a["ref"].startswith("registry.tavrenhill.internal/") and "@sha256:" in a["ref"]
                     for a in man["artefacts"])
    pinned = mean(x["hash_pinned"] for x in man["lockfiles"])
    hours = [(datetime.fromisoformat(k["patched"]) - datetime.fromisoformat(k["kev_added"])).total_seconds() / 3600
             if k["patched"] else math.inf for k in man["kev_patches"]]
    bad_served = sorted(set(man["mirror"]["served_versions"]) & set(man["known_bad_versions"]))
    m += [row("AC-12", "artefacts deployed by digest from the internal registry", f"{by_digest:.2f}", "1.00",
              by_digest == 1),
          row("AC-12", "lockfiles hash-pinned", f"{pinned:.2f}", "1.00", pinned == 1),
          row("AC-12", "KEV-listed CVEs patched within 72 h", f"{sum(h <= 72 for h in hours)}/{len(hours)}", "all",
              all(h <= 72 for h in hours)),
          row("AC-12", "known-bad versions the mirror served (curveball 3)", len(bad_served), "= 0", not bad_served)]

    # AC-13 MCP tool governance
    verdicts = [(c, system.mcp_allow(c["server"], c["tool"], c["description"], w["mcp"])) for c in w["mcp_calls"]]
    unapproved = sum(allowed for c, allowed in verdicts if c["kind"] == "unapproved")
    poisoned = [not allowed for c, allowed in verdicts if c["kind"] == "poisoned"]
    m += [row("AC-13", "calls allowed to unapproved MCP servers", unapproved, "= 0", unapproved == 0),
          row("AC-13", "poisoned tool descriptions blocked or flagged", f"{sum(poisoned)}/{len(poisoned)}", "all",
              all(poisoned))]

    width = max(len(x["metric"]) for x in m)
    print(f"System: {args.system}   use cases={len(ucs)}, golden={sum(len(v) for v in w['golden'].values())}, "
          f"DLP prompts={len(w['dlp'])}, probe pairs={pairs}, discovery lines={len(w['discovery'])}\n")
    print(f"{'AC-ID':6} | {'metric':{width}} | {'value':27} | {'threshold':26} | PASS/FAIL")
    print("-" * (width + 78))
    for x in m:
        print(f"{x['ac']:6} | {x['metric']:{width}} | {str(x['value']):27} | {x['threshold']:26} | {x['status']}")
    kinds = Counter(c["kind"] for c in w["truth"])
    by_kind = {k: f"{sum(c['kind'] == k for c in found)}/{n}" for k, n in kinds.items()}
    consumer = sum(v for bu, v in alloc["by_bu"].items() if bu == "retail")
    print("\nCascade validator false-accept / escalation rate: "
          + ", ".join(f"{a}: {r['false_accept']:.2f} / {r['escalation']:.2f}" for a, r in anchors.items()))
    print(f"DLP recall by label: { {k: round(mean(v), 3) for k, v in per_label.items()} }")
    print(f"DLP recall by language (all labels): { {k: round(mean(v), 3) for k, v in sorted(by_lang.items())} }")
    print(f"DLP ID recall by encoding: { {k: round(mean(v), 3) for k, v in sorted(by_enc.items())} }")
    print(f"Shadow-AI recall by kind: {by_kind}; findings that hit a seeded case: "
          f"{sum(bool(seeded & set(f['line_ids'])) for f in findings)}/{len(findings)}")
    print(f"Same-BU cache hits (the cache should still work): {same_hits}/{same}")
    print(f"Runaway loop: USD {loop['spent_usd']:.2f} spent before the budget stopped it (policy cap "
          f"USD {w['loop']['policy_hourly_cap_usd']:.0f}/hour)")
    print(f"Curveball 1: {len(dependent)} use cases route to {notice['model']}, retiring {notice['retires']}")
    print(f"Curveball 5: Consumer BU (retail) showback this month USD {consumer:,.0f}; it refuses chargeback")
    summary = dict(Counter(x["status"] for x in m))
    print(f"Summary: {summary}")
    out = HERE / "results" / f"{args.system}.json"
    out.parent.mkdir(exist_ok=True)
    result = {"system": args.system, "run_at": datetime.now().isoformat(timespec="seconds"), "summary": summary,
              "metrics": m, "cascade": anchors, "allocation": alloc, "invoiced_usd": invoiced, "drills": drills,
              "loop": loop, "dlp_id_recall_by_encoding": {k: mean(v) for k, v in by_enc.items()},
              "dlp_recall_by_language": {k: mean(v) for k, v in by_lang.items()},
              "shadow_ai_recall_by_kind": by_kind, "retiring_model_dependents": dependent,
              "mirror_bad_versions": bad_served}
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Wrote {out.relative_to(HERE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
