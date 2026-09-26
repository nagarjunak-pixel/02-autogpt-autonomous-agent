# 05 · Revised Syllabus and 16-Week FDE Learning Path

This document turns the review ([01](01-curriculum-review.md)), the gap register ([02](02-gap-register.md)), the errata ([03](03-errata-and-fact-check.md)) and the horizon scan ([04](04-future-topics-2026-2028.md)) into one plan. It covers:
1. a re-tiered priority scheme with an explicit FDE core;
2. merges that make room for new material;
3. where every new topic goes;
4. how to keep dated facts current;
5. a 16-week track with the projects placed in it.

---

## 1. Re-tiered priorities: the FDE core

**Rule.** A topic is **P1 (core)** only if a Forward Deployed Engineer meets it in most engagements, or it is legally in force for common deployments. Everything else is an elective (P2), a specialist topic (P3) or Watch.

Applying that rule to Vol 2's 135 turns plus the verified gap topics gives a **core of 46 topics**. That is about 30% of the expanded syllabus, down from 51% (60 of the 117 non-future turns in Vol 2). "(NEW)" marks a gap-register topic.

| Module | Core topics (P1) |
|---|---|
| **Engage** (11) | FDE operating model and field-to-product loop (NEW, FDE-7) · 109 Discovery (+ acceptable use and saying no, FDE-8) · 110 Business case and ROI (+ honest impact measurement, FDE-5) · 111 POC → pilot → production · 115 Data readiness (+ permission hygiene, FDE-9) · 116 Scoping and SOWs (+ pricing models, FDE-6) · 112 Architecture docs and ADRs · 113 Stakeholder communication and demos · Security review, vendor due diligence and data-handling terms (NEW, FDE-1) · Regulation as obligations → controls (NEW, gap #4 + section D; 79 EU AI Act becomes its worked example) · 81 Privacy law (GDPR, DPDP) |
| **Build** (14) | 42 Parsing and ingestion (+ IDP at scale, RAG-7) · Permission-aware retrieval (NEW, RAG-3; absorbs 50 vector-store choice and RAG-11 managed RAG) · 52 Lineage and deletion (+ index freshness, RAG-4) · Context engineering (NEW, RAG-1 / gap #7) · Text-to-SQL and semantic layers (NEW, RAG-5 / gap #14) · 61 Tool/ACI design (promoted from P2; + the API → MCP → GUI decision ladder and tool-scale patterns, AGT-3/4) · 65 MCP specification · 66 MCP authorisation · 71 Agent identity (absorbs 124; + control planes, AGT-7) · 95 Agent harness engineering (rewritten around harness SDKs, AGT-1) · Systems-of-record integration (NEW, FDE-2; + SoR agent platforms, AGT-6) · 21 Reasoning models and reasoning controls (+ MOD-1) · 105 Vision-language models · 101 Coding agents as daily tools (+ team-scale governance, AGT-8) |
| **Evaluate** (3) | Evaluation strategy (NEW spine turn; absorbs the core of 13, 49, 97, 104 and 132) · 14 Hallucination (+ citations RAG-9, abstention MOD-3) · 63 Simulation, synthetic users and pass^k (promoted from P2) |
| **Harden** (6) | Prompt-injection-resistant architectures (NEW, gap #8) · OWASP LLM + Agentic Top 10 (73 + 74 merged) · 75 Red-teaming · 78 PII and DLP · AI-era security of the orchestration layer (NEW, gap #1; + 77 supply chain; + agent containment and credential misuse, HOR-1/HOR-11) · 76 Data and memory poisoning (nearly every engagement has a RAG corpus or memory that can be poisoned) |
| **Operate** (8) | 87 Model upgrades and deprecation · 88 A/B tests and canaries · 89 Feedback loops and flywheel · 91 FinOps (+ provider capacity engineering, FDE-4) · 96 Observability · 100 AI gateways · 90 SLOs and incident response (promoted; + legal incident-reporting clocks) · 92 Deploying inside the customer's environment: on-prem, sovereign, private networking and customer-managed keys (absorbs 134; + FDE-3) |
| **Model literacy for deployers** (4) | 1 Tokenisation and cost · 29 + 30 Serving engines and quantisation (merged, deployer depth) · 34 Local and on-device inference · 102 Provider landscape (+ 22 "when to fine-tune" decision, with teacher-terms caveat MOD-13) |

**Prerequisite, not a topic:** 103 Python (and TypeScript) engineering for AI apps. Test it on entry.
**Assessed through the projects, not taught as a turn:** 117 Technical interview and system-design readiness. Each project ends with a design defence.

### Demoted from P1 to P2 (still taught, as electives or on demand)

| Turn(s) | Why they leave the core |
|---|---|
| 3, 6, 7 (block anatomy, encoder/decoder, MoE) | The deployer needs the consequences (KV-cache and MoE memory maths, bi- vs cross-encoders), which the literacy module and Build teach. The internals are electives. |
| 16, 17, 20, 23 (SFT, RLHF, RLVR, distillation) | Most FDEs select and adapt models; few post-train them. Fine-tuning decisions stay in core through 22. P15 is the specialist project. |
| 48, 49, 50, 97 | Folded into the evaluation spine and permission-aware retrieval. |
| 53, 54, 55, 57, 58 (skills, AGENTS.md, subagents, background agents, long-horizon) | Advanced agent-engineering elective. P05, P06, P07 and P09 exercise them. |
| 60, 106 (voice, speech) | Voice elective track (P04, P10, P14). Frequent, but not in most engagements. |
| 69, 72 (WebMCP, hosted agent platforms) | Situational. They sit next to AGT-5 distribution. |
| 79 (EU AI Act) | Becomes the main worked example inside "obligations → controls". It is not lost. |

---

## 2. Merges that make room

Seven merges free roughly seven turns of teaching time. That is about what the new P1 and P2 turns need (section 3).

| Merge | Result |
|---|---|
| 71 + 124 | **Agent identity: now and next.** 124's trust-fabric material becomes a "next" annex. |
| 62 + 118 + 130 (+ gap #12 memory) | **Agents that learn and remember.** One turn covering memory architectures, then one on governed learning. |
| 92 + 134 (+ FDE-3) | **Deploying inside the customer's environment.** Covers sovereignty, private connectivity and keys. |
| 27 + 29 + 31 | **Serving for deployers.** Parallelism depth becomes a P3 elective. |
| 21 + 121 (+ MOD-1) | **Reasoning models and reasoning controls.** On-device distillation moves to 34 and 23. |
| 13 + 49 + 97 + 104 + 132 | **Evaluation strategy** spine turn, with tool-specific annexes. |
| 73 + 74 | **OWASP LLM and Agentic Top 10** in one security-checklist turn. |

---

## 3. Where every new topic goes

Priorities and full entries are in the [gap register](02-gap-register.md). "New turn" means a turn inserted with a letter suffix, so existing turn numbers do not change (for example **50a** after Turn 50). "Extend" adds a section, a Q&A set and an annex to an existing turn.

### New turns (P1 and P2)

| New turn | Topic | Register ID | Priority | Module / week |
|---|---|---|---|---|
| 108a | The FDE operating model and field-to-product loop | FDE-7 | P1 | Engage / W1 |
| 115a | Security review, vendor due diligence and data-handling terms | FDE-1 | P1 | Engage / W2 |
| 79a | Regulation as obligations → controls: the global map | gap #4 + section D | P1 | Engage / W2 |
| 40a | Context engineering | RAG-1 (gap #7) | P1 | Build / W3 |
| 50a | Permission-aware retrieval | RAG-3 | P1 | Build / W3 |
| 51a | Text-to-SQL and semantic layers | RAG-5 (gap #14) | P1 | Build / W5 |
| 100a | Integrating agents with systems of record | FDE-2 | P1 | Build / W6 |
| 21a | Reasoning controls as an API surface (or a rewrite of Turn 21) | MOD-1 | P1 | Build / W6 |
| 12a | Evaluation strategy (the spine) | review §2.5 | P1 | Evaluate / W4 |
| 73a | Prompt-injection-resistant architectures | gap #8 | P1 | Harden / W7 |
| 77a | AI-era security of the orchestration layer | gap #1 | P1 | Harden / W8 |
| 29a | Open-weight serving fidelity (chat templates, parsers, cross-provider variance) | MOD-2 | P2 | Literacy / W11 |
| 52a | LLM functions inside the data platform | RAG-6 | P2 | Build elective |
| 61a | Computer-use agents and the decision ladder | AGT-4 (gap #2, #3) | P2 | Frontier practice / W14 |
| 72a | Systems-of-record agent platforms: integrate, extend or compete | AGT-6 | P2 | Build elective / W6 |
| 99a | Low-code and visual agent builders: governance and graduation to code | AGT-9 (gap #18) | P2 | Harden elective / W8 |
| 101a | Distribution inside AI assistants and enterprise tenants | AGT-5 (gap #13) | P2 | Frontier practice / W14 |
| 78a | Deepfake and voice-clone fraud against identity checks | SEC-7 | P2 | Harden elective / W8 (and voice track) |
| 80a | Shadow-AI discovery and the enterprise AI inventory | SEC-10 | P2 | Operate elective / W9 |
| 81a | India's sectoral AI governance (RBI, SEBI, MeitY, CERT-In) | SEC-11 | P2 (India BFSI track: core) | Engage elective / W15 |
| 82a | EU Cyber Resilience Act and revised Product Liability Directive | SEC-1 (= HOR-9) | P2 | Horizon and responsibility / W15 |
| 83a | Automated-decision and AI-in-hiring rules beyond GDPR Art. 22 | SEC-5 (+ HOR-6 workforce evidence) | P2 | Horizon and responsibility / W15 |
| 83b | Companion AI, minors and age assurance | SEC-6 (gap #5) | P2 (P1 for consumer products) | Horizon and responsibility / W15 (core for the consumer/edtech track) |

### Extensions of existing turns

| Turn | Add | Register ID(s) |
|---|---|---|
| 14 | Calibrated abstention and selective prediction; span-level citation checking | MOD-3, RAG-9 |
| 22 / 23 / 26 | Managed RFT status (OpenAI's platform is closing); teacher terms; SLM-first designs; fine-tuning side effects | MOD-4, MOD-13, MOD-10, MOD-11 |
| 28 | One paragraph on multi-token prediction | gap #20 |
| 29 | Inference nondeterminism; correct "reproducible" wording in 87, 93 and 97 | MOD-9 |
| 30 / 31 / 33 | Microscaling formats; prompt-cache retention, KV tiering and cache isolation; serverless GPU cold starts | MOD-6, MOD-7 (gap #16), MOD-8 |
| 42 | IDP at scale: confidence-routed review and field-level evaluation | RAG-7 |
| 47 / 56 | Agentic retrieval; index vs grep for code | RAG-8 |
| 49 | Cold-start evaluation sets and their biases | RAG-10 |
| 50 | Managed RAG and hosted file search (build vs buy) | RAG-11 |
| 52 | Index freshness, CDC and delete propagation | RAG-4 |
| 55 | Orchestration patterns (agents-as-tools, handoffs, magentic) and when not to use them | AGT-2 |
| 59 | One sentence and one Q&A on A2UI vs MCP Apps | AGT-10 |
| 61 | Tool search, code mode and programmatic tool calling | AGT-3 |
| 71 | Enterprise agent control planes and agent sprawl | AGT-7 |
| 82 | Records retention, supervision and eDiscovery for AI interactions | FDE-11 |
| 84 | India's SGI labelling rules | gap #6 |
| 92 | Private connectivity, customer-managed keys, proxies, self-hosted execution | FDE-3 |
| 94 | Quota dimensions, provisioned throughput, spillover; classifier refusals and cross-model fallback; 429 classification | FDE-4, MOD-12 |
| 95 | Rewrite around harness SDK primitives (permission hooks, stop limits, resumable state) | AGT-1 |
| 100 | Multi-tenant isolation for AI features | FDE-10 |
| 101 | Hooks, managed settings and the plugin supply chain | AGT-8 |
| 103 | Python **and TypeScript** patterns side by side | gap #17 |
| 109 / 110 / 115 / 116 | Saying no; honest measurement; permission hygiene; pricing models | FDE-8, FDE-5, FDE-9, FDE-6 |
| 60 | Outbound AI voice agents under US telemarketing law (TCPA) | SEC-14 |
| 73 / 86 | Agent containment (egress paths, live monitoring, a tested automatic stop) and 2026 credential-misuse incidents | HOR-1, HOR-11 |
| 74 | Multi-tenant isolation and LLM side channels; protecting your model APIs from extraction | SEC-8, SEC-9 |
| 79 | GPAI obligations when you fine-tune or modify a model; the GPAI Code of Practice | SEC-4 |
| 83 | Accessibility law for AI interfaces (EU EAA, US ADA Title II, India) | SEC-13 |
| 90 | Regulatory incident clocks (GDPR 72 h, CRA 24/72 h, CERT-In 6 h, DORA) and mandatory AI records | SEC-3 (**P1**) |
| 98 | Automated-reasoning guardrails and LLM-assisted formal verification | HOR-2 |
| 101 | Provenance, attribution and licensing of agent-written code | HOR-8 |
| 102 | Model-origin and compute governance rows in the model scorecard | HOR-5 |

---

## 4. Keeping it true: the evergreen core and a dated annex

1. **Split every turn** into an *evergreen core* (principles, patterns, maths, heuristics) and a *dated annex* (versions, vendors, dates, laws, benchmark numbers).
2. **Stamp every annex fact** with an as-of date, a source URL, an owner and a review-by date.
3. **Run a quarterly refresh sprint**:
   - re-verify the annex, the regulation map and the calendar in [04](04-future-topics-2026-2028.md);
   - fold confirmed changes into [03](03-errata-and-fact-check.md) first, then into the book.
4. **Let the interview Q&As test the principle**, and put the volatile fact in the annex. Example: ask "Why can low temperature fail as a reproducibility strategy?", not "What does model X do with temperature?".

---

## 5. The 16-week FDE track

Each week has roughly 10–12 hours of study plus project work. Projects run in three waves:
- **Project 1** (weeks 3–8): a ★★☆ build-first project.
- **Project 2** (weeks 9–12): a ★★★ hardening/operations project.
- **Capstone** (weeks 13–16): chosen by target industry.

| Week | Module | Topics | Project milestone |
|---|---|---|---|
| 1 | Engage I | FDE operating model (108a) · 109 · 110 · 115 · literacy crash course: 1, 102, 21 | Read all 16 briefs; choose Project 1 |
| 2 | Engage II: trust | 111 · 116 · 115a security review · 79a obligations → controls · 81 privacy | **Discovery memo + data-readiness scorecard + draft SOW** (Templates 01–03) |
| 3 | Build I: retrieval | 42 · 50a permission-aware retrieval · 52 · 40a context engineering · 47 | Project 1 kickoff; security pack skeleton (Template 08) |
| 4 | Evaluate | 12a evaluation strategy · 14 · 63 · (49, 97 annexes) | **Frozen golden and adversarial sets; eval plan** (Template 05) |
| 5 | Build II: data and tools | 51a text-to-SQL · 61 ACI + decision ladder · 36 · 65 · 66 MCP auth | POC build |
| 6 | Build III: agents | 95 harness engineering · 55 orchestration · 71 identity · 100a systems of record · 21a reasoning controls | **POC demo** (Template 10), design doc + ADRs (Template 04) |
| 7 | Harden I | 73a injection-resistant architecture · 73/74 OWASP · 75 red-teaming · 76 poisoning · 74 multi-tenant side channels (SEC-8) | Threat model (Template 06); red-team run |
| 8 | Harden II | 78 DLP · 86 sandboxes · 77a orchestration-layer security + 77 supply chain · 99a low-code builders | **Project 1 final + curveballs**; compliance map (Template 07) |
| 9 | Operate I | 100 gateways · 96 observability · 91 FinOps + capacity · 101 coding agents | Project 2 kickoff (★★★) |
| 10 | Operate II | 87 upgrades · 88 canaries · 89 flywheel · 90 SLOs + legal incident clocks (SEC-3) · 80a shadow-AI inventory | Eval CI gates; SLOs and runbook (Template 09) |
| 11 | Deploy | 92 customer environments + sovereignty · 29/30 serving + quantisation · 29a serving fidelity · 33 capacity · 93 IaC | **Project 2 pilot** |
| 12 | Multimodal | 105 VLMs · 43 multimodal RAG · (elective: 60/106 voice track) | **Project 2 final + curveballs + handover drill** |
| 13 | Customisation | 22 fine-tuning decisions · 23 distillation + teacher terms · 24 · 34 on-device | Capstone kickoff; discovery memo |
| 14 | Frontier practice | 61a computer use · 101a distribution in assistants · 69 WebMCP · 70 commerce protocols · 127 | Capstone POC |
| 15 | Horizon and responsibility | [04](04-future-topics-2026-2028.md) horizon review · 83 responsible AI · 82 sector compliance · 82a CRA/PLD · 83a ADM and hiring laws · 83b companion AI and minors · 81a India sector rules · 114 change management | Capstone pilot |
| 16 | Capstone | — | **Demo, design defence (Turn 117), handover drill** |

### Which projects fit which wave

| Wave | Recommended briefs | Why |
|---|---|---|
| Project 1 (★★☆, weeks 3–8) | [P01](projects/P01-permission-aware-knowledge-assistant.md) · [P02](projects/P02-text-to-sql-analytics-agent.md) · [P03](projects/P03-claims-intake-document-ai.md) · [P09](projects/P09-legacy-modernisation-with-coding-agents.md) · [P11](projects/P11-teen-safe-study-companion-compliance.md) · [P13](projects/P13-agent-ready-commerce-mcp.md) · [P14](projects/P14-multilingual-citizen-services-assistant.md) · [P16](projects/P16-due-diligence-deep-research-agent.md) | They exercise weeks 1–8 (engage, retrieval, evaluation, tools, hardening) without needing ops depth |
| Project 2 (★★★, weeks 9–12) | [P04](projects/P04-contact-centre-voice-agent.md) · [P05](projects/P05-computer-use-agent-replacing-rpa.md) · [P06](projects/P06-injection-resistant-inbox-agent.md) · [P07](projects/P07-ai-vulnerability-triage-and-patch-pipeline.md) · [P08](projects/P08-sovereign-air-gapped-llm-platform.md) · [P10](projects/P10-ambient-clinical-documentation.md) · [P12](projects/P12-enterprise-ai-gateway-finops-platform.md) · [P15](projects/P15-distilled-domain-small-model-offline.md) | Hardening, operations, deployment or real-time constraints |
| Capstone | Any brief not yet done, chosen for the learner's target industry | Portfolio piece plus design defence |

**Coverage.** Across the 16 projects, every core topic above is exercised by at least one project. See the coverage matrix in [projects/README.md](projects/README.md#coverage-matrix).
