# P12 Starter Kit · Enterprise AI Gateway, FinOps and Model Lifecycle for Tavrenhill Holdings

Offline starter kit for the brief [P12 · Enterprise AI Gateway, FinOps and Model-Lifecycle Platform](../../P12-enterprise-ai-gateway-finops-platform.md).
Tavrenhill Holdings, its business units (BUs), people, keys, prompts, bills and providers are all fictional.

In under 10 minutes, with no API key, no network and nothing to install, you can:

1. generate the brief's §3 data: a 300-use-case catalogue, a request log, three billing-export schemas, discovery logs with 40 seeded shadow-AI cases, a multilingual DLP set, golden sets for the three anchors, and the adversarial inputs;
2. run the brief's most important control, the **routing cascade with budget guard and circuit breaker** (§7), with its tests;
3. score a deliberately weak baseline gateway configuration against the §5 acceptance criteria.

The baseline fails 26 of the checks. That is on purpose: replace it with your own system and watch the numbers move.

## Run it

Run these from this folder with Python 3.11. The standard library is all you need.

```bash
python3 generate_data.py                  # about 1 s; --scale N multiplies the volumes
python3 eval_harness.py                   # about 1 s; prints the AC table, writes results/baseline.json
python3 -m unittest discover -s tests -v  # about 3 s; 27 tests
```

Useful flags: `eval_harness.py --limit N` (score only the first N golden items, DLP prompts and MCP calls, which saves money with a real model) and `--manifest PATH` (audit your own deploy manifest instead of the seeded one).

To plug in a real model through any OpenAI-compatible endpoint (Ollama, vLLM or a hosted API):

```bash
LLM_BASE_URL=http://localhost:11434/v1 LLM_MODEL=qwen2.5:7b python3 eval_harness.py --system adapter --limit 200
```

`LLM_API_KEY` is optional and is only ever read from the environment. The tests and the default run never call the adapter.

## What is in the kit

| File | What it is |
|---|---|
| `generate_data.py` | Seeded generator for the §3 data. Writes everything to `data/`. Also holds the checksum functions (Verhoeff, Luhn, mod-97, GSTIN). |
| `router.py` | The §7 cascade, budget guard and circuit breaker, kept as the reviewed sketch. Two marked additions: `Deployment.zone` with `filter_residency()` (the §7 production gap "residency filters applied before fallback") and a `ProviderError` that carries `retry_after`. |
| `baseline.py` | A first-sprint gateway configuration behind the interface every system implements: `ROUTES`, `tiers_for()`, `accept()`, `budget_for()`, `detect_pii()`, `cache_key()`, `authorise()`, `mcp_allow()`, `discover()` and `allocate()`. Each weakness is marked `weak:`. |
| `adapter.py` | A stub that adds a model-based detector for names with health data (the "ML DLP" route). Standard library only (`urllib`). |
| `eval_harness.py` | Runs the router on a simulated clock for the cascade, failover drills and the runaway loop; scores DLP, isolation, discovery, chargeback, lifecycle, supply chain and MCP governance against §5. |
| `tests/` | `unittest` tests for the router and the generator. |

### The synthetic data (`data/`, scale 1)

Volumes are cut down from the brief's so everything runs in seconds; `--scale` multiplies them.

| File | Contents | Tricky cases from brief §3 |
|---|---|---|
| `use_cases.json` | 12 BUs × 25 apps: task, traffic profile, prompt and output lengths, data class, residency, success signal, owner, virtual key | Three anchors; diagnostics and NBFC must stay in India; German and UK BUs stay in the EU zone; an HR-screening app flagged as an EU AI Act Annex III candidate; the Consumer BU (retail) |
| `registry.json` | 11 deployments across three providers and the on-prem cluster, aliases, zones, retirement dates | One model with no retirement date; a retirement notice with 60 days' warning |
| `request_log.jsonl` | 20,000 metadata records for September 2026 (the brief's 2M, scaled down) | Only 3 BUs go through the gateway yet |
| `billing/` | Provider A per-PTU-hour (USD), provider B per-token (USD), provider C per-request (EUR), on-prem GPU (INR), invoices and FX | A 25% price cut on 16 September; account-level credits; untagged spend; PTU at 50–60% utilisation |
| `discovery_logs.jsonl`, `directory.json`, `shadow_ai_truth.json` | 20,000 egress, DNS, proxy, SSO-grant, card and netflow lines with the answer key | 40 seeded cases: gateway-bypassing SDK calls, consumer chatbots, an exposed n8n instance, workstation Ollama servers, AI features inside approved SaaS, card-paid subscriptions. Decoys such as "THAI SPICE RESTAURANT" and `openair-hvac.example` |
| `dlp_set.jsonl` | 2,000 prompts in English, Hindi, Marathi and code-mixed text | Checksum-valid Aadhaar, PAN, card, IBAN and GSTIN values; patient names with lab values; decoys that fail their checksums; spaced, Devanagari-digit and base64 encodings |
| `golden_<anchor>.jsonl` | 1,000 paired items per anchor: what the cheap tier's output shows a validator, and whether each tier was right | Hard items defeat the cheap tier first, so a lax validator costs quality |
| `isolation_probes.jsonl` | 10,000 cache probe pairs (10% same-BU controls) and 300 key-use probes | A third of the key probes present another BU's key |
| `mcp_registry.json`, `mcp_calls.jsonl` | 3 approved MCP servers with pinned description hashes; 60 tool calls | Unapproved servers, a poisoned description with hidden instructions, a benign description change that needs re-approval |
| `loop_sim.json`, `drill.json`, `deploy_manifest.json` | The runaway-loop script, the failover-drill settings and the as-is deploy state | See the curveballs below |

### Curveball fixtures (brief §11)

| Curveball | Fixture | Covered by |
|---|---|---|
| 1. Model retirement with 60 days' notice (week 10) | `registry.json` `retirement_notices`: `a-large-2025-10` retires 2026-11-30 | AC-11 rows, the "Curveball 1" line (use cases that route to it); `test_cb1_*` (a 410 moves the chain to the successor) |
| 2. Agent loop burns a month's budget overnight (week 5) | `loop_sim.json`: a failing tool call retried every 3 s with context growing by 1,500 tokens | AC-8 rows; `test_cb2_*` |
| 3. Gateway package compromised upstream (week 8) | `deploy_manifest.json`: the mirror has no cooldown and served 1.82.7 and 1.82.8; the IoC file and egress domain from the brief's case study | AC-12 rows |
| 4. Provider regional outage (week 11) | `drill.json`: `india-west` is down during three drills | AC-6 rows, including residency; `test_cb4_*` |
| 5. Consumer BU refuses chargeback (week 13) | `use_cases.json` `consumer_bu` (retail) | The "Curveball 5" showback line, for the CFO memo |

## Metrics, acceptance criteria and baseline results

Brief §5 has no IDs, so this kit numbers its 13 rows in order: AC-1 is the first row (spend through the gateway) and AC-13 the last (tool governance). Each AC-ID's first row names the brief's area in the Notes column. Baseline figures come from `python3 eval_harness.py` on the default data.

| AC-ID | Harness metric | Threshold (brief §5) | Baseline | Notes |
|---|---|---|---|---|
| AC-1 | Share of LLM spend through the gateway (synthetic month) | ≥ 90% | 0.148: FAIL | Business. |
| AC-2 | Cost per successful outcome, per anchor; quality delta vs strong-only with a one-sided 95% bootstrap lower bound | ≤ −30%, non-inferior (margin 2 pp) | −87%/−86%/−86% cost but −4.5/−7.0/−4.4 pp quality: FAIL ×3 | Business. |
| AC-3 | Ledger total vs invoiced; unallocated share | within ±2%; ≤ 3% | +6.00%: FAIL; 47.9%: FAIL | Business. |
| AC-4 | Seeded shadow-AI recall; findings with owner, data class and risk tier | ≥ 90%; all | 0.500: FAIL; 0.000: FAIL | Inventory. |
| AC-5 | Gateway availability | 99.95% monthly | not computable offline | Reliability. |
| AC-6 | Failover drill success (worst of 3); p95 vs normal p95; pass^3; requests served outside their residency zone | ≥ 99%; ≤ 2×; 3/3; 0 | 0.797: FAIL; 1.74×: PASS; 0/3: FAIL; 867: FAIL | Reliability. |
| AC-7 | Gateway overhead p95 of the policy path | ≤ 30 ms (rules DLP); ≤ 120 ms (ML DLP) | ≈ 0.01 ms: PASS | Latency. |
| AC-8 | Time to throttle after the hourly cap; overspend past it | ≤ 60 s; ≤ one request | 3,183 s: FAIL; USD 2,979: FAIL | Cost control. |
| AC-9 | DLP recall on checksum-valid IDs; on names + health; precision; false blocks | ≥ 97%; ≥ 90%; ≥ 90%; ≤ 0.5% | 0.505: FAIL; 0.000: FAIL; 0.520: FAIL; 34.9%: FAIL | Safety/DLP. |
| AC-10 | Cross-BU cache hits in 10,000 probe pairs; cross-BU key use | 0; 0 | 9,000: FAIL; 100: FAIL | Isolation. |
| AC-11 | Route entries that are registry aliases; deployments with a retirement date | all; all | 0.500: FAIL; 0.909: FAIL | Lifecycle. |
| AC-12 | Artefacts by digest from the internal registry; hash-pinned lockfiles; KEV CVEs patched ≤ 72 h; known-bad versions the mirror served | all; all; all; 0 | 0.67: FAIL; 0.50: FAIL; 1/3: FAIL; 2: FAIL | Supply chain. |
| AC-13 | Calls allowed to unapproved MCP servers; poisoned descriptions blocked or flagged | 0; all | 0: PASS; 0/10: FAIL | Security. |

How the harness scores:

- **Cascade (AC-2).** Each golden item goes through `router.route()` with the system's tiers for that anchor's use case. The cheap tier's output is accepted only if `accept(anchor, signals)` says so; the strong tier is always accepted. Cost per success = total cost ÷ correct answers, compared with the route's strong deployment alone. Quality is paired per item; the lower bound is the 5th percentile of 1,000 bootstrap means. The extra line shows each validator's false-accept rate (wrong cheap answers accepted) and escalation rate.
- **Chargeback (AC-3).** `allocate()` gets the four raw exports, the request log (for usage shares), the catalogue and FX. The ledger total is everything it returns: BUs, the platform line (unused PTU, per ADR-5) and unallocated. Invoices come from `billing/invoices.json`.
- **Failover drill (AC-6).** 1,000 requests per drill on a simulated clock, with 1% 5xx and 1% 429 chaos. A request to the down region costs a 1 s timeout until its breaker opens. The normal-run p95 uses the same requests without the outage. A request that no in-zone deployment can serve counts as a failure, never as a border crossing.
- **Overhead (AC-7)** is measured on this machine, in one process, for `authorise` + `detect_pii` + `cache_key` + a budget reservation. It is not the brief's load test at 3× peak. A system that sets `ML_DLP = True` (the adapter does) is held to 120 ms.
- **Runaway loop (AC-8)** uses `budget_for()` for the loop's use case. The policy cap is USD 20 an hour (`loop_sim.json`). The baseline sets no burn-rate cap, which repeats the July incident.
- **Isolation (AC-10).** A cache hit is two BUs' prompts mapping to the same `cache_key()`. Same-BU pairs must still hit, so the cache stays useful.
- **AC-1 and AC-11's retirement dates** are properties of the data, not of the system: onboard BUs (`on_gateway` in `BUS`) and fix `DEPLOYMENTS` in `generate_data.py` to move them. AC-12 audits `deploy_manifest.json`; pass `--manifest` to audit yours.

## What you build next

The brief's course plan (§7) runs 5 weeks. The brackets give the real engagement phase each week rehearses.

| Course week (real phase) | Build | Harness rows that should move |
|---|---|---|
| 1 (Discovery, weeks 1–3 → POC, weeks 4–6) | A thin gateway (or LiteLLM, Agent Router or agentgateway) around `router.py`, virtual keys bound to BUs (`authorise`), mock providers and OTel spans. Write ADRs 1–3. | AC-10 (key use) |
| 2 (POC) | Budgets with an hourly burn-rate cap, the cascade with real validators on anchor 1, breaker tuning. Inject curveball 2. POC exit: overhead ≤ 30 ms p95; cascade non-inferior on anchor 1; drill passes. | AC-8, AC-2 |
| 3 (Pilot, weeks 7–11) | DLP with normalisation (Unicode digits, spacing, base64) and checksums, plus a names-and-health detector; tenant-scoped cache keys; an MCP allow-list with pinned description hashes. Inject curveball 3 and fix the manifest and mirror cooldown. | AC-9, AC-10, AC-13, AC-12 |
| 4 (Pilot) | The FOCUS-shaped ledger with PTU amortisation and credits, showback per BU, and shadow-AI discovery that finds owners, data classes and risk tiers. Inject curveball 5. | AC-3, AC-4 |
| 5 (Production, weeks 12–15; Handover, week 16) | Registry aliases and retirement dates in CI, shadow and canary migration, residency-aware fallback chains and three drills, and the demo with a live outage and a runaway loop. Inject curveballs 1 and 4. | AC-11, AC-6 |

## What the kit deliberately does not do

- **No LLM calls.** Plug yours in through `adapter.py`. The brief keeps models out of the request path; the stub only adds a names-and-health detector.
- **No gateway, network or providers.** Provider calls are simulated inside the harness with seeded latencies and faults; there is no HTTP proxy, TLS, vault or OTel collector.
- **No real concurrency.** Budgets and breakers are single-process, as in the sketch. Distributed counters, a single-probe half-open state and streamed-token accounting are yours (§7 production gaps).
- **No production measurements.** Availability (AC-5) needs synthetic probes in both regions, and AC-7 needs a load test at 3× peak.
- **No human labels or judge calibration.** Golden items carry pre-computed correctness; the brief's κ ≥ 0.7 validator calibration and the live A/B are yours.
- **No YAML.** The brief's catalogue is YAML; the kit writes JSON because the standard library cannot parse YAML.
