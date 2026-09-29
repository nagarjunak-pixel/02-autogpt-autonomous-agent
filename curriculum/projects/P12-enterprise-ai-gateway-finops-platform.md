# P12 · Enterprise AI Gateway, FinOps and Model-Lifecycle Platform

> One governed front door for every model call and tool call across 12 business units, with budgets, routing, chargeback, lifecycle management and shadow-AI discovery, built so that the gateway itself does not become the weakest link.
>
> **Customer:** Tavrenhill Holdings (fictional) · **Industry:** Diversified conglomerate (retail, FMCG, cement, logistics, hospitality, diagnostics, an NBFC, real estate, media, chemicals, renewables, IT services) · **Geography:** HQ Mumbai; business units (BUs) in India, the UAE, the UK and Germany · **Real engagement:** 16 weeks; FDE lead, 1 FDE, a part-time security architect, plus Tavrenhill's platform team (4), a FinOps analyst and a BU champion per wave · **Course build:** 5 weeks, team of 3–4 · **Difficulty:** ★★★

**Starter kit:** [`starter-kits/P12-enterprise-ai-gateway-finops-platform/`](starter-kits/P12-enterprise-ai-gateway-finops-platform/README.md). It runs offline with no API key: synthetic data with the tricky cases labelled, the §7 control as `router.py` with tests, a deliberately weak baseline, and an eval harness that scores it against §5.

## 1. Scenario — the customer and the ask

A spend census found AI costs of about **USD 420k/month**, up roughly 4× in a year:

| Spend line | USD/month |
|---|---|
| Pay-as-you-go API usage | 200k |
| Committed and provisioned-throughput contracts | 120k |
| Self-hosted GPU cluster (vLLM, Navi Mumbai data centre) | 60k |
| AI SaaS seats, many on corporate cards | 40k |

Spend spans three model providers and an on-prem open-weight cluster. There are about **300 AI use cases**; central IT knew of 180. Recent incidents:
- **July:** a logistics agent looped over a weekend and spent USD 38k.
- A diagnostics developer pasted lab reports into a consumer chatbot.
- Two apps broke when a provider retired a model.
- Provider keys are shared over chat and unrotated for 14 months.

**The ask (Group CIO):** "Get AI costs and risks under control without slowing teams down."

**What they actually need** is a paved-road platform:
- A **central AI gateway**: virtual keys per team, cascades, fallback chains, budgets, DLP and MCP tool governance.
- **FinOps:** normalised billing, showback then chargeback, and **cost per successful outcome**.
- **Lifecycle:** a model registry, a deprecation calendar, and shadow and canary evaluation for upgrades.
- **Resilience and isolation:** failover drills, quota and provisioned-throughput management, and per-BU isolation.
- **Shadow-AI discovery** feeding a living AI inventory.

The gateway holds every provider key and sees every prompt: the crown jewel, and in 2026 a proven supply-chain and exploitation target (§9).

| Stakeholder | Cares about | Can block |
|---|---|---|
| Group CIO (sponsor) | Visibility, fewer incidents, a platform story | Budget, mandate |
| Group CFO | Predictable spend; chargeback for FY 2027–28 budgets | Chargeback policy |
| Group CISO | Keys, DLP, logging, supply chain | Go-live; egress blocking |
| Group DPO/Legal | DPDP, GDPR, cross-border prompts | Logging scope, providers |
| 12 BU CTOs (esp. the Consumer BU's own AI team) | Autonomy, latency, no "platform tax" | Onboarding waves |
| German works council | Employee monitoring through prompt logs | Logging for German staff |
| Procurement | Committed-spend minimums, renewals | Provider changes |
| Platform/SRE team (future owner) | Operability, on-call | Handover |
| Internal audit | Evidence, inventory completeness | Sign-off |

## 2. Constraints

**Data.** Prompts carry loyalty PII (retail), Aadhaar and PAN (NBFC), lab results (diagnostics) and formulations (FMCG, chemicals). Some BUs must keep prompts in-country or on self-hosted models. Sector rules (e.g. RBI for the NBFC) may add conditions: get each BU's regulatory register rather than assuming.

**Legal and regulatory** (verified as of Sep 2026):

| Instrument | Why it applies | What it means for the platform |
|---|---|---|
| **CERT-In Directions**, 28 Apr 2022 ([PDF](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf)) | Tavrenhill's Indian entities | Report listed incidents within **6 hours**; item (xx) covers attacks on "Artificial Intelligence and Machine Learning" systems. Keep ICT logs for a **rolling 180 days within India** |
| **DPDP Act 2023 + [DPDP Rules 2025](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf)** (G.S.R. 846(E), 13 Nov 2025) | Personal data of Indian customers and staff | Consent-manager rule 12 months, most duties 18 months from notification (May 2027), including Rule 6 safeguards (logs kept **one year**) and Rule 7 breach notice. Build to the standard now |
| **[GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj) / UK GDPR** | German and UK BUs | Minimisation for logs; Art. 28 terms with providers; Chapter V rules for EU prompts routed outside the EEA |
| German co-determination ([BetrVG §87(1) no. 6](https://www.gesetze-im-internet.de/betrvg/__87.html)) | Prompt logs can monitor employees | Works-council agreement needed before identity-linked logging of German staff (confirm with counsel) |
| **EU AI Act** as amended by the Digital Omnibus, Reg. (EU) 2026/1744 of 8 Jul 2026, in force 27 Jul 2026 ([EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202601744)) | EU BU deployers | Art. 5 prohibitions apply (e.g. emotion recognition at work). Annex III high-risk duties move to **2 Dec 2027**. Art. 4 AI-literacy duty softened to "take measures to support". The inventory must flag Annex III candidates (e.g. HR screening in Germany) |
| UAE BU | — | Not researched here; local counsel to confirm |

**Infrastructure.** Azure is the group standard; two BUs use AWS; vLLM runs on-prem. Provider A is used through Azure with provisioned throughput units (PTU), Provider B directly and via Bedrock, Provider C via Google Cloud.

**Security.** Provider master keys live only in the vault; the admin plane never faces the internet.

**Budget and timeline.** USD 1.2M in year 1; target a 20–30% saving on addressable spend with no quality loss. The CFO needs showback by January 2027 for FY 2027–28 budgets (the Indian financial year starts 1 April).

**Politics.** The Consumer BU runs its own stack and refuses chargeback. Developers fear latency. Security wants full prompt logs; the works council and DPO do not. Committed-spend minimums mean the cheapest list price is not always the cheapest route.

## 3. What students are given (course build)

**Synthetic data:**
- **Use-case catalogue (YAML):** 12 BUs × 25 apps, each with model, task type, traffic profile (diurnal, month-end spikes), lognormal prompt and output lengths, data class, residency rule and a **success signal** (e.g. "extraction accepted without correction").
- **Request log:** ~2M metadata records over 30 days, plus 5,000 full prompts for routing and DLP evaluation.
- **Billing exports:** three schemas (per-token, per-PTU-hour, per-request) with credits, a mid-month price change, and INR, USD and EUR, normalised into a FOCUS-shaped ledger (FOCUS 1.4 covers AI, cloud and SaaS billing, [FinOps Foundation](https://www.finops.org/focus/)).
- **Discovery logs (1M lines):** egress, DNS, proxy, SSO/OAuth grants and card lines, with 40 seeded shadow-AI cases: gateway-bypassing SDK calls, consumer chatbots, an exposed n8n instance, a workstation Ollama server, AI features inside approved SaaS, and card-paid subscriptions.
- **DLP set:** 2,000 prompts in English, Hindi, Marathi and code-mixed text with checksum-valid Aadhaar (Verhoeff), PAN, card (Luhn), IBAN (mod-97) and GSTIN values, and patient names with lab values. Add **decoys** (12-digit numbers failing Verhoeff) and spaced, Unicode-digit and base64 encodings.
- **Adversarial inputs:** an MCP tool description with hidden instructions; an agent looping on a failing tool call with growing context; a probe for another BU's cache.

**Mock systems.** Three mock providers (FastAPI) with configurable latency, 429/5xx errors, a "region down" switch, token accounting and a "retired model" switch (404/410); mock MCP servers; a local "self-hosted" tier on Ollama.

**Budget, two paths:**
- **API path (≤ USD 50):** a small and a mid-tier model; use the strong tier only on eval samples.
- **Local path:** two open-weight sizes on Ollama or vLLM (e.g. 3–4B and 8–14B) as cheap and expensive tiers, with mock providers for failover.

**Gateway choice.** Self-host LiteLLM, Agent Router or agentgateway in Docker or kind, or build a thin FastAPI gateway around the §7 sketch.

**Out of scope:** real provider contracts, TLS interception or monitoring of real employees, real multi-region HA (simulate it), and production SSO.

## 4. Discovery — what the FDE does in week 1

**Processes to map:** getting model access (ticket → procurement → a key pasted in chat); paying for AI (enterprise agreement, card, cloud marketplace); choosing and upgrading models; outages; risk review of new use cases, if any.

**Baselines and how to measure them:**
- **Spend census:** 6 months of invoices, card and cloud billing in one ledger.
- **Key census:** secret scanning of repos and CI, plus provider consoles (count, age, owner).
- **Gateway traffic share:** egress logs matched to provider domains (baseline 0%).
- **Cost per successful outcome** for 3 anchors (FMCG invoice extraction, retail email triage, diagnostics summarisation), from the success signal.
- **Latency p50/p95** per anchor; hourly PTU utilisation; 6 months of incidents.

**Sharpest discovery questions:**
1. Which three use cases would the CFO defend in a budget cut, and what shows they work?
2. Where is each provider key, who has it, and when was it last rotated?
3. Which committed-spend and PTU contracts exist, with what minimums and expiry dates?
4. What counts as "success" for each anchor, and where is that signal recorded?
5. Which BUs and data classes must stay in India, in the EU, or on self-hosted models?
6. What did the last model retirement break, and how long did the fix take?
7. In the July loop incident, who noticed, and after how long?
8. What logging will the works council and DPO accept: metadata, redacted, or full?
9. Which MCP servers do agents use, and who approved them?
10. What would make a team bypass the gateway, and how do we make the paved road faster?

**Qualification: the lowest rung that works.** Almost all of this is **not AI**: configuration, policy-as-code, deterministic routing and accounting.
- **Rules:** route tables, budgets, allow-lists, regex-plus-checksum DLP.
- **ML:** a learned router, only after 8–12 weeks of logged outcomes.
- **Single LLM call:** an LLM validator for cascade acceptance, only where no deterministic check (schema, totals, citation) exists.
- **Workflow:** the model-migration pipeline.
- **Agents:** none in the request path.

**Decision: Go, with conditions.** Security controls are mandatory group policy; chargeback is negotiated per BU.

## 5. Success criteria and acceptance tests

| Area | Criterion | Threshold | Test / evidence |
|---|---|---|---|
| Business | Share of LLM spend through the gateway | ≥ 90% by week 15 | Ledger reconciled to invoices; egress blocks |
| Business | Cost per successful outcome, 3 anchors | −30% or better, with quality **non-inferior** (margin 2 pp, one-sided 95%) | Paired on the 1,000-item golden set; live A/B sized for 80% power (≈ 2,300 per arm at 92% accuracy) |
| Business | Chargeback accuracy | Allocated vs invoiced within ±2%; unallocated ≤ 3% | Monthly close |
| Inventory | Shadow-AI discovery | Seeded recall ≥ 90%; every discovered use case has owner, data class and risk tier | 40 seeded cases; inventory audit |
| Reliability | Gateway availability | 99.95% monthly (21.6 min error budget) | Synthetic probes, both regions |
| Reliability | Failover drill: primary region down | ≥ 99% succeed; p95 ≤ 2× baseline; **pass^3** over 3 drills | Game days |
| Latency | Gateway overhead p95 | ≤ 30 ms (rules DLP); ≤ 120 ms on routes with ML DLP | Load test at 3× peak |
| Cost control | Runaway-loop containment | Throttled ≤ 60 s after the hourly cap; overspend ≤ one request | Loop simulator |
| Safety/DLP | PII detection | Recall ≥ 97% on checksum-valid IDs, ≥ 90% on names + health; precision ≥ 90%; false blocks ≤ 0.5% | DLP set (per language) |
| Isolation | Cross-tenant leakage | 0 cross-BU cache hits in 10,000 probe pairs; 0 cross-BU key use | Isolation suite |
| Lifecycle | Model references | All routes use registry aliases; every model has a retirement date | Config lint in CI |
| Supply chain | Gateway artefacts | All deployed by digest from the internal registry; hash-pinned lockfiles; KEV-listed CVEs patched ≤ 72 h | Deploy audit; drill |
| Security | Tool governance | Only approved MCP servers reachable; poisoned description blocked or flagged | Adversarial suite |

A cascade that saves 40% but loses 5 accuracy points moves the cost to the BU's reviewers.

## 6. Reference architecture

```mermaid
flowchart LR
  subgraph BU["BU TENANTS: 12 business units"]
    A1["Apps and agents"]
    A2["Batch jobs"]
  end
  subgraph GW["AI GATEWAY data plane: secret zone"]
    AU["AuthN: virtual key or workload identity"]
    PO["Policy: budget guard, quotas, DLP"]
    RT["Router: cascade, fallback, circuit breakers"]
    CA["Per-tenant cache"]
    MG["MCP governance: allow-list, per-tool policy"]
  end
  subgraph CP["CONTROL plane: admin network only"]
    KV["Vault: provider keys"]
    MR["Model registry + deprecation calendar"]
    PR["Policy repo (GitOps)"]
    AR["Internal artefact registry: digests, cooldown"]
  end
  subgraph OBS["TELEMETRY and FinOps"]
    OT["OTel collector: GenAI spans"]
    LED["Cost ledger (FOCUS-shaped)"]
    CB["Showback, chargeback, cost per outcome"]
  end
  subgraph EXT["EXTERNAL providers: separate trust domain"]
    P1["Provider A: 2 regions, PTU"]
    P2["Provider B"]
    P3["Provider C"]
  end
  subgraph ONP["TAVRENHILL DC"]
    V["vLLM open-weight models"]
  end
  subgraph TL["TOOL plane"]
    M1["Approved MCP servers"]
  end
  subgraph DS["SHADOW-AI discovery"]
    EG["Egress, DNS, SSO, card data"]
    INV["AI inventory"]
  end
  A1 --> AU
  A2 --> AU
  AU --> PO --> RT
  RT --> CA
  RT --> P1
  RT --> P2
  RT --> P3
  RT --> V
  A1 -->|"tool calls"| MG --> M1
  KV -.-> RT
  MR -.-> RT
  PR -.-> PO
  AR -.->|"signed images by digest"| RT
  RT --> OT --> LED --> CB
  EG --> INV
  INV -.->|"onboard or block"| PR
```

| Component | Responsibility | Options (OSS/self-host · managed) | Owner |
|---|---|---|---|
| Gateway data plane | Auth, policy, routing, cache, MCP | **LiteLLM**; **Agent Router** (Envoy AI Gateway, 1.0 on 23 Jun 2026, renamed on joining the Agentic AI Foundation: [announced 9 Sep 2026](https://theagentrouter.ai/blog/envoy-ai-gateway-is-now-agent-router), [GitHub](https://github.com/envoyproxy/ai-gateway)); **agentgateway** (also AAIF, [site](https://agentgateway.dev/)) · **Kong AI Gateway**; **Azure APIM AI gateway** (`llm-token-limit`, `llm-emit-token-metric`, circuit breaker, [docs](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities)); **Prisma AIRS AI Gateway** (Portkey: Palo Alto Networks [closed the acquisition](https://www.paloaltonetworks.com/company/press/2026/palo-alto-networks-completes-acquisition-of-portkey-to-secure-ai-agents) on 29 May 2026; [GA](https://www.paloaltonetworks.com/blog/2026/07/announcing-general-availability-of-prisma-airs-ai-gateway/) 16 Jul 2026; no roadmap has been announced for the open-source [Portkey gateway](https://github.com/Portkey-AI/gateway): Palo Alto Networks' acquisition releases and GA post do not mention it, and its last `main` commit was 25 May 2026, as of 27 Sep 2026); **Cloudflare AI Gateway** | Platform |
| Vault | Provider keys; rotation | OpenBao / HashiCorp Vault · Azure Key Vault | Security |
| DLP | Detect, redact, block | Presidio + checksum validators · Kong AI Sanitizer, Azure AI Content Safety | Security |
| Cache | Exact/semantic cache, per tenant | Redis with tenant namespaces · APIM semantic cache | Platform |
| Self-hosted serving | Cheap tier; residency-bound data | vLLM (`cache_salt` for prefix-cache isolation), SGLang · provider provisioned throughput | Platform |
| Model registry | Aliases → versions, retirement dates, eval evidence | Git + YAML + CI · vendor model catalogue APIs as inputs | Platform |
| Observability | Traces, metrics, cost | OTel Collector + Langfuse / Arize Phoenix + Grafana · Azure Monitor, Datadog | SRE |
| FinOps ledger | Normalise, allocate, report | FOCUS schema in DuckDB/Postgres + dbt · FOCUS-capable FinOps tools | FinOps |
| MCP registry | Approved servers, pinned tool descriptions | Private sub-registry following the official MCP Registry API (preview since 8 Sep 2025, [blog](https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/)) · Azure API Center | Security + Platform |
| Shadow-AI discovery | Find unsanctioned AI | Zeek/DNS logs + domain list + SSO grants · SSE/CASB AI-app discovery, e.g. Defender for Cloud Apps' Generative AI catalogue category with risk scores and sanction/block ([docs](https://learn.microsoft.com/en-us/security/security-for-ai/discover)) and Entra Global Secure Access shadow-AI discovery, which also flags model-provider APIs and SaaS MCP servers ([docs](https://learn.microsoft.com/en-us/entra/global-secure-access/concept-shadow-ai-discovery)); checked 27 Sep 2026 | Security |

**ADRs to write** ([template 04](templates/04-solution-design-and-adr.md)):
1. **Gateway product:** OSS (LiteLLM, Agent Router, agentgateway), commercial (Kong, Prisma AIRS), cloud-native (APIM), or two layers (APIM at the edge, OSS for on-prem and MCP).
2. **Topology:** one central gateway, per-region data planes, or per-BU data planes under a central control plane (this settles the Consumer BU negotiation).
3. **Routing:** static per use case, a cascade with validators, or a learned router.
4. **Logging and retention:** metadata by default; redacted samples; full payloads only in opted-in debug windows. Reconcile CERT-In's 180 days in India, DPDP Rule 6's one-year log retention (from May 2027), GDPR minimisation and the works council.
5. **Chargeback model:** showback only, actuals, or blended rates with PTU amortisation (unused commitment charged to the platform, not the BUs).
6. **Supply chain and upgrades:** pin by digest, internal mirror, a 3–7 day cooldown for new releases, staged rings, and an **expedited path for KEV-listed fixes**.

## 7. Implementation plan — week by week

| Phase (weeks) | Key tasks | Exit criteria | FDE artefacts |
|---|---|---|---|
| Discovery (1–3) | Spend and key census; inventory v0; anchor success signals; works-council consultation opened; gateway bake-off | Signed memo; baselines; SOW | Discovery memo ([template 01](templates/01-discovery-questionnaire.md)), data readiness ([template 02](templates/02-data-readiness-scorecard.md)), SOW ([template 03](templates/03-sow-and-acceptance-criteria.md)) |
| POC (4–6) | Non-prod gateway for 2 BUs; virtual keys; budgets; OTel; cascade on 1 anchor; DLP monitor mode; mirror + digest pinning; drill #1 in staging | Overhead ≤ 30 ms p95; cascade non-inferior on anchor 1; drill passes | ADRs ([template 04](templates/04-solution-design-and-adr.md)), eval plan ([template 05](templates/05-eval-plan.md)), threat model ([template 06](templates/06-threat-model-and-controls.md)) |
| Pilot (7–11) | 3 BUs in production (~60 use cases); showback; DLP enforce for ID classes; MCP allow-list; registry and calendar; shadow-eval harness; game day #2 | §5 met for pilot BUs; showback reconciles ±2% | Obligations map ([template 07](templates/07-compliance-obligations-to-controls.md)), security pack ([template 08](templates/08-security-review-pack.md)), weekly status ([template 10](templates/10-demo-script-and-status-report.md)) |
| Production (12–15) | Onboarding waves for the remaining 9 BUs; direct-egress blocks; chargeback live; two-region HA; gateway pen test; runbooks | SLOs met 2 weeks; ≥ 90% of spend through the gateway | Runbook and SLOs ([template 09](templates/09-runbook-slos-and-handover.md)) |
| Handover (16) | Platform team runs a failover drill and a model migration alone | Customer-run drill passes | Handover pack |

**Course build (5 weeks):** (1) gateway, virtual keys, mock providers and OTel; (2) budgets, cascade and breaker, plus curveball 2; (3) DLP, cache isolation and MCP allow-list, plus curveball 3; (4) FOCUS ledger, showback and discovery, plus curveball 5; (5) shadow/canary migration and failover drill, curveballs 1 and 4, and demo.

**Code sketch: routing cascade with budget guard and circuit breaker** (library-agnostic Python 3.10+; `call_fn` wraps whichever gateway or SDK you use):

```python
import time
from dataclasses import dataclass, field

class BudgetExceeded(Exception): pass

@dataclass
class Breaker:                                   # per deployment (provider x region x model)
    fail_threshold: int = 5; cooldown_s: float = 30.0
    fails: int = 0; opened_at: float | None = None; parked_until: float = 0.0
    def available(self, now: float) -> bool:     # after cooldown: half-open, one failure re-opens
        return now >= self.parked_until and (self.opened_at is None or now - self.opened_at >= self.cooldown_s)
    def record(self, ok: bool, now: float, retry_after: float | None = None) -> None:
        if retry_after is not None: self.parked_until = now + retry_after; return  # 429: honour Retry-After
        if ok: self.fails, self.opened_at = 0, None
        else:
            self.fails += 1
            if self.fails >= self.fail_threshold: self.opened_at = now

@dataclass
class Budget:                                    # per virtual key; money in USD, from a price table
    monthly_usd: float
    hourly_cap_usd: float                        # burn-rate cap: catches runaway agent loops
    spent: float = 0.0; hour_start: float = 0.0; hour_spent: float = 0.0
    def reserve(self, est: float, now: float) -> None:
        if now - self.hour_start >= 3600: self.hour_start, self.hour_spent = now, 0.0
        if self.spent + est > self.monthly_usd: raise BudgetExceeded("monthly budget exhausted")
        if self.hour_spent + est > self.hourly_cap_usd: raise BudgetExceeded("hourly burn-rate cap hit")
        self.spent += est; self.hour_spent += est
    def settle(self, est: float, actual: float) -> None:
        self.spent += actual - est; self.hour_spent += actual - est
    def allowed_tiers(self, tiers: list) -> list:  # soft limit: above 80% spend, drop the priciest tier
        return tiers if self.spent < 0.8 * self.monthly_usd or len(tiers) == 1 else tiers[:-1]

@dataclass
class Deployment:
    name: str
    usd_per_1k_in: float
    usd_per_1k_out: float
    breaker: Breaker = field(default_factory=Breaker)
    def cost(self, tin: int, tout: int) -> float:
        return tin / 1000 * self.usd_per_1k_in + tout / 1000 * self.usd_per_1k_out

def route(request, tiers, budget, call_fn, accept, est_in, est_out, clock=time.monotonic):
    """tiers: cheapest first; each tier is a fallback chain of Deployments (other provider/region).
    call_fn(name, request) -> (text, tokens_in, tokens_out) or raises. accept(text) -> bool.
    On a 429 call_fn's exception carries .retry_after: the Retry-After seconds, or math.inf if not retryable."""
    trace = []
    for tier in budget.allowed_tiers(tiers):
        for dep in tier:
            if not dep.breaker.available(clock()): trace.append((dep.name, "unavailable")); continue
            est = dep.cost(est_in, est_out); budget.reserve(est, clock())   # may raise BudgetExceeded
            try:
                text, tin, tout = call_fn(dep.name, request)
            except Exception as e:                     # timeout, 429, 5xx: try next in chain
                budget.settle(est, 0.0); dep.breaker.record(False, clock(), getattr(e, "retry_after", None))
                trace.append((dep.name, f"error:{type(e).__name__}")); continue
            dep.breaker.record(True, clock()); budget.settle(est, dep.cost(tin, tout))
            if accept(text): trace.append((dep.name, "accepted")); return text, dep.name, trace
            trace.append((dep.name, "rejected:escalate")); break          # quality miss -> next tier
    raise RuntimeError(f"no acceptable answer: {trace}")
```

**429s.** Honour `Retry-After` first: the sketch parks the deployment for that long and moves down the chain. Some 429s are not retryable: Anthropic's spend-cap 429 has no `retry-after` and carries `enforced_spend_limit_reached` ([docs](https://platform.claude.com/docs/en/api/rate-limits#reaching-your-spend-cap)); park it until a human acts and page FinOps. If every deployment is parked, return 429 with the earliest `Retry-After`.

**Production gaps:** distributed counters (atomic Redis/Lua) and a single-probe half-open state; streamed-token accounting with `max_tokens` on every request, so the reservation is an upper bound; prices from the registry; residency filters applied **before** fallback, so an outage never moves Indian health data offshore; the trace as OTel span events.

## 8. Evaluation plan

**Datasets:**
- **Golden:** 1,000 frozen items per anchor, labelled by BU experts.
- **Adversarial:** DLP evasions, the poisoned MCP description, cache probes, the loop script, the 40 seeded shadow-AI cases.
- **Regression:** every escaped PII case, bad cascade acceptance and failed drill.
- **Held-out:** two weeks of pilot traffic, labelled afterwards.

**Metrics per layer:**

| Layer | Metrics |
|---|---|
| Cascade | **Validator false-accept rate** (wrong cheap answer accepted), escalation rate, quality vs strong-only with CIs, cost per success |
| Router/resilience | Fallback success, breaker open time, p95 under chaos (429/5xx/latency/region down), pass^3 |
| Budget | Time-to-throttle, overspend, false throttles on month-end spikes |
| DLP | Precision/recall per entity × language; encoded-evasion recall; added latency |
| Isolation | Cross-tenant hits; prefix-cache timing with and without `cache_salt` |
| Lifecycle | Shadow-eval deltas; canary SLO breaches; rollback time |
| FinOps | Reconciliation error; unallocated share; cost-per-outcome trend |
| Discovery | Seeded-case recall; flagged-domain precision; detection-to-inventory time |

**Judge calibration.** Where an LLM validator is unavoidable, calibrate it on 300 human labels per use case (κ ≥ 0.7), re-check monthly, and treat judge drift after a model upgrade as a canary failure.

**CI gates on the policy repo:**
- Config lint (no raw model IDs, every key has a budget, residency tags present) and policy unit tests.
- A route change is blocked if golden-set quality falls outside the non-inferiority margin.

**Online metrics:** cost per successful outcome; escalation and fallback rates; per-tenant cache hit rate; DLP blocks; budget alerts; gateway traffic share and p95 overhead.

## 9. Security, privacy and compliance

**Case study: LiteLLM on PyPI, 24 Mar 2026 (verified).**
- Versions 1.82.7 and 1.82.8 carried credential-harvesting malware, uploaded straight to PyPI with a token LiteLLM traces to the compromised Trivy scanner in its CI. They were live for about 40 minutes. Version 1.82.8's `litellm_init.pth` ran on any Python start.
- Users of the official Docker image were unaffected because that path "pins dependencies" ([LiteLLM](https://docs.litellm.ai/blog/security-update-march-2026); [GHSA-5mg7-485q-xm76](https://osv.dev/vulnerability/GHSA-5mg7-485q-xm76)).
- Separately, [CISA's KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) added three LiteLLM CVEs in 2026: CVE-2026-42208 (SQL injection in key verification, 8 May), CVE-2026-42271 (command execution by **low-privilege internal-user keys** via MCP test endpoints, 8 Jun) and CVE-2026-59822 (MCP authentication bypass, 2 Sep).
- **Lessons:** pin by hash and deploy by digest from a mirror with a cooldown, **and** keep a 72-hour path for KEV fixes.

**Lethal-trifecta check:**

| Context | Private data | Untrusted content | Exfiltration | Control |
|---|---|---|---|---|
| BU agent with RAG + web tool + email tool (via gateway) | Yes | Yes | Yes | **Break a leg:** per-agent tool policy denies "untrusted-read + external-send" without human confirmation |
| Gateway itself (non-LLM) | All prompts, keys | All prompts | Egress to providers | Egress allow-list; no general internet; admin plane on a separate network |

**Top threats and controls** ([template 06](templates/06-threat-model-and-controls.md)):

| Threat | Control |
|---|---|
| Upstream package compromise | Hash-pinned lockfiles, mirror, 3–7 day cooldown, SBOM per image, egress allow-list |
| Exploited gateway CVE | KEV watch; 72 h patch path; no internet-facing admin UI; least-privilege internal keys |
| Provider-key theft | Vault, short-lived fetch, rotation runbook; only virtual keys in apps |
| Cross-tenant cache leakage | Tenant-scoped cache keys; vLLM `cache_salt` per BU. Gu et al. found cross-user cache sharing at seven API providers ([arXiv 2502.07776](https://arxiv.org/abs/2502.07776)). Provider scope varies: Anthropic isolates caches per workspace on its API but only per organisation on Bedrock and Google Cloud ([docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)), so map BUs to workspaces or accounts |
| Denial of wallet | Hourly caps, per-run step limits, repeated-call detection |
| DLP evasion | Normalise before detection; checksums; adversarial set in CI |
| MCP tool poisoning / rug pull | Allow-list; pinned tool-description hashes; re-approval on change |
| Log store as breach target | Metadata-only default; redaction; retention per ADR-004, then deletion |
| Bypass | Direct-provider egress blocked; exceptions logged |

**Obligations → controls** ([template 07](templates/07-compliance-obligations-to-controls.md)):

| Obligation | Control | Evidence |
|---|---|---|
| CERT-In 6 h report; 180-day logs in India | Incident runbook with a CERT-In step; log store in an Indian region | Drill record; retention config |
| DPDP Rules 6–7 (from May 2027): safeguards, one-year logs, breach notice | Encryption, access control, DLP, log retention, breach runbook | Security pack; retention config |
| GDPR minimisation and transfers | Metadata-only default; residency routing; SCCs with providers | ADR-004; DPA register |
| BetrVG §87(1) no. 6 | Works-council agreement on logging scope | Signed agreement |
| EU AI Act Art. 5 and Annex III (from 2 Dec 2027) | Inventory screening questions; high-risk flag triggers review | Inventory records |
| EU AI Act Art. 4 (as amended) | Literacy module required before a virtual key is issued | Training records |

## 10. Operations and cost model

**SLOs.** Availability 99.95% per month; gateway-attributable errors ≤ 0.05%; overhead p95 ≤ 30 ms; spend data fresh within 5 minutes; chargeback closed by working day 5.

**Observability.** Emit OTel GenAI spans with `gen_ai.request.model`, `gen_ai.usage.input_tokens` and `gen_ai.usage.output_tokens`, plus `tavrenhill.bu`, `tavrenhill.use_case`, `tavrenhill.tier` and `tavrenhill.outcome`. The GenAI conventions are still at **Development** status in a separate repository ([OTel](https://opentelemetry.io/docs/specs/semconv/gen-ai/)): pin the version.

**Capacity.** 25M requests a month ≈ 10 req/s average, ~100 req/s peak; with ~8 s streams, ~800 concurrent streams at peak. Plan 3–6 replicas per region.

**Quotas and reserved capacity.** Set per-key TPM/RPM quotas at the gateway, below provider quotas; route PTU spillover to pay-as-you-go; handle 429s as in §7. Reserved options differ: Azure PTU capacity is fungible across provisioned deployments ([Microsoft](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/model-retirements)); Bedrock Provisioned Throughput has no-commitment, 1-month and 6-month terms ([AWS](https://docs.aws.amazon.com/bedrock/latest/userguide/prov-throughput.html)); Google sells fixed-term subscriptions ([Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput/overview)). Review utilisation weekly against commitment minimums.

**Cost model.** Ranges only: prices change monthly, so recompute from current price pages. Batch APIs typically cost about half the synchronous price.

| Lever | Assumption | Saving (USD/month) |
|---|---|---|
| Cascade on eligible work (~40% of PAYG, now strong tier) | Cheap tier accepts 60–80% at 10–25% of strong cost; new cost = 80k × (cheap cost share + escalation share) | 28–56k |
| Caching (per tenant) + provider prompt caching | 3–10% of PAYG | 6–20k |
| Batch for offline jobs | 15–25% of PAYG at ~50% discount | 15–25k |
| PTU right-sizing | Utilisation 55% → 75–80%; spillover to PAYG | 20–35k |
| SaaS seat consolidation | 20–40% of USD 40k | 8–16k |
| **Gross saving** (levers overlap: compute in sequence in the real model) | | **≈ 77–152k (18–36%)** |
| Platform run cost | Infra 6–15k + 5 FTE (platform team of 4 + FinOps analyst) 20–35k | −26–50k |
| **Net** | | **≈ +27k to +126k** |

At the low end this is a governance programme that pays for itself, not a cost-cutting miracle; say so in the business case.

**Worked cost per outcome, FMCG invoice extraction (illustrative):**
- Strong-only: USD 0.012 per invoice at 92% success = **USD 0.0130 per success**.
- Cascade: cheap tier at USD 0.001; the validator (schema + line totals reconcile) passes 80% and escalates 20%. Cost 0.001 + 0.2 × 0.012 = 0.0034 per invoice at 93% success = **USD 0.0037 per success**.

**Runbooks:** RB-1 provider or region outage; RB-2 runaway spend; RB-3 gateway package or CVE emergency; RB-4 model retirement; RB-5 key compromise; RB-6 DLP false-block storm (monitor mode, with CISO approval).

**DR.** Active-active gateways in two Azure regions, on-prem as a third path for self-hosted routes; configuration rebuilt from Git and digests. **Break-glass** direct-provider keys stay in the vault for Sev-1 only (time-boxed, dual-approved, audited). Key rotation is drilled quarterly.

## 11. Curveballs (instructor-injected events)

1. **Week 10: a provider announces a model retirement with 60 days' notice.**
   - Anthropic and Microsoft Foundry both give at least 60 days' notice for GA models ([Anthropic](https://platform.claude.com/docs/en/about-claude/model-deprecations), [Microsoft](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/model-retirements)); Foundry dates are not extendable and provisioned deployments are **not** auto-upgraded.
   - Query the registry for dependent aliases (say 43 use cases).
   - **Shadow**-evaluate on 5% mirrored traffic, then canary 5% → 25% → 100% with SLO-based rollback.
   - Check API contracts as well as quality: Claude Opus 4.7 and later return a 400 for non-default `temperature`/`top_p`/`top_k`.
   - Re-check PTU capacity; finish by day 40.
2. **Week 5: an agent loop burns a month's budget overnight.**
   - Throttle or revoke the key; confirm spend has flattened.
   - Trace the cause (e.g. a failing tool call retried with growing context); add the hourly cap, per-run step limits, repeated-call detection and spend-velocity alerts against a 7-day baseline.
   - Blameless review. Provider credits are not guaranteed; ADR-005 decides who pays.
3. **Week 8: the gateway package is compromised upstream (a LiteLLM-style event).**
   - Compare deployed digests with the bad versions; check whether the mirror ever served them (the cooldown should have blocked them).
   - Hunt for the `.pth` IoC in dev and CI. If the package ran anywhere with provider keys, **rotate every provider key** and revoke sessions.
   - Check egress to the exfiltration domain (`models.litellm.cloud` in the real incident).
   - File with CERT-In within 6 hours if Indian systems are affected; assess GDPR; brief the CISO with the timeline.
4. **Week 11, during pilot traffic: a provider has a regional outage.**
   - Breakers open and fallback chains engage **within residency rules**: diagnostics routes may use only in-country or self-hosted tiers, so they queue rather than cross a border.
   - Measure fallback quality against pre-evaluated pairs; post the drill metrics.
5. **Week 13: the Consumer BU refuses chargeback.**
   - Separate **mandatory controls** (vault keys, DLP, logging, inventory; group CISO policy) from **commercial terms**.
   - Offer a federated data plane under the central control plane, starting with showback of the BU's own cost per outcome.
   - Take a decision memo to the CFO; record the compromise in ADR-002 and ADR-005.

## 12. Deliverables and grading rubric

**Deliverables:** discovery census, memo and SOW · POC gateway config, tested router, OTel, ADR-001 to ADR-004, threat model · pilot DLP and isolation reports, showback, registry and calendar, drill report, compliance map, security pack · runbooks, SLO dashboards, chargeback and a customer-run drill.

| Criterion | Weight | Excellent | Weak |
|---|---|---|---|
| Working system | 25% | Budgets, cascade, fallback and isolation proven under chaos | A proxy that forwards requests |
| Evaluation rigour | 20% | Non-inferiority tests with CIs; validator false-accept rate; pass^3 drills | "Savings 40%" with no quality check |
| Security and compliance | 15% | Supply-chain controls with a KEV fast path; residency-aware fallback; logging agreement | Keys in environment variables; full prompt logs by default |
| FDE artefacts | 20% | ADRs with rejected options; honest net-savings model | Vendor feature lists |
| Demo and communication | 10% | Live outage and runaway-loop drill | Slides |
| Curveball handling | 10% | Calm, evidence-based, recorded in ADRs | Ad-hoc config edits in production |

## 13. Stretch goals

- A learned router trained on logged outcomes, compared with the rule cascade.
- PTU vs pay-as-you-go break-even analysis from hourly utilisation.
- An MCP sub-registry with signed tool manifests.
- A prefix-cache timing experiment on vLLM with and without `cache_salt`.

## 14. Curriculum map

| Turn | Title | How it is exercised |
|---|---|---|
| 29, 31, 33, 35 | Serving Engines; Prefix Caching; Capacity Planning; Batch | Self-hosted tier; `cache_salt`; PTU sizing; batch savings |
| 38, 57, 58 | Evaluator Loops; Always-On Agents; Long-Horizon Execution | Cascade validators; spend caps; stuck-loop detection |
| 65, 66, 71 | MCP Specification; MCP Authorization; Agent Identity | Pinned tool descriptions; MCP auth at the gateway; per-agent keys |
| 68 | The Agentic AI Foundation | agentgateway and Agent Router governance |
| 73, 74, 77 | OWASP Agentic and LLM Top 10s; Model Supply Chain | Denial of wallet, tool poisoning, pinning and KEV patching |
| 78 | PII Detection and DLP | Checksum validators; multilingual evaluation |
| 79–81 | EU AI Act; NIST AI RMF and ISO/IEC 42001; GDPR and DPDP | Inventory screening and risk tiers; logging scope |
| 87, 88 | Model Upgrades and Deprecation; A/B Testing and Canary | Registry, calendar, shadow → canary |
| 90, 94 | SLOs and Incident Response; Provider Failover and DR | Breakers, `Retry-After` handling, drills, error budgets |
| 91, 100 | LLM FinOps; AI Gateways | The core build; ledger, chargeback, cost per outcome |
| 92, 93 | On-Prem and Sovereign Deployment; IaC | Residency tiers; GitOps policy |
| 96–98 | Observability; Evaluation; Guardrail Tools | OTel GenAI spans; golden-set harness; DLP tooling |
| 102 | Model Provider Landscape | Multi-provider fallback pairs |
| 109–116 | FDE practice | Census, ROI, ADRs, change management, SOW |
| 128 | Governance-as-Code | Policy repo with tests |

**New/gap topics exercised:** #1 orchestration-layer security (LiteLLM supply chain, KEV CVEs); #8 injection-resistant architecture; MOD-7 cache isolation; FDE-4 provider capacity engineering (quotas, PTU, spillover, 429s); FDE-10 multi-tenant isolation; FDE-11 log retention; FDE-1 security review; AGT-7 agent sprawl and inventory; AGT-9 low-code builders (exposed n8n); SEC-10 shadow-AI inventory; SEC-8 multi-tenant side channels; SEC-3 incident clocks and record retention.

## 15. What reviewers look for / common failure modes

- **Savings without quality.** No non-inferiority test or validator false-accept rate.
- **Pinning without patching.** A cooldown with no KEV fast path.
- **Fallback that ignores residency.** An outage moves health or KYC prompts offshore.
- **Shared caches across BUs.** Semantic or prefix caches keyed only on prompt text.
- **Full prompt logging by default,** or logs outside India when CERT-In applies.
- **Monthly budget alerts only.** No hourly burn-rate cap, so the July incident repeats.
- **Raw model IDs in app code.** Every retirement becomes a 12-team fire drill.
- **Chargeback as a technical problem.** It is a negotiation; bring the BU's own numbers. Charging BUs for unused PTU invites bypass.
