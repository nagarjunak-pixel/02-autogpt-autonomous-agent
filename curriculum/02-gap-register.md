# 02 · Gap Register: What Vol 2 Is Missing (verified, as of 26 September 2026)

This register lists every topic we found that *LLM Training Flow Vol 2* is missing or covers only thinly. It also re-ranks the 23 candidates in the existing gap doc. The detailed entries sit in six area files under [gap-register/](gap-register/).

**How each entry was produced**
1. A research agent searched one area (models, RAG, agents, security and law, FDE practice, horizon). It proposed candidates only after grepping the Vol 2 study guide for coverage, and it backed each one with dated sources, preferring primary ones.
2. A second, adversarial agent tried to refute each candidate:
   - Is it really missing from Vol 2?
   - Is it a duplicate of a gap-doc item?
   - Does the key dated claim hold up on independent re-verification?
   - Is the priority inflated?

   It then rejected, merged, downgraded or corrected candidates, and added any strong gaps the first agent missed.
3. A writer applied every verdict and correction. It added no facts beyond the verified inputs.

**Priority scale**
- **P1**: an FDE meets it in most engagements, or it is legally in force for common deployments.
- **P2**: frequent but situational.
- **P3**: niche or specialist.
- **Watch**: future; covered in [04](04-future-topics-2026-2028.md).

Many candidates were downgraded; the adversarial pass was deliberately hard on P1 claims.

---

## 1. Summary

| | Count |
|---|---|
| Register entries (verified) | **61** unique topics (62 rows; HOR-9 duplicates SEC-1) |
| — deeper, corrected versions of gap-doc items | 7 (gap-doc #2, #5, #7, #13, #14, #16, #18) |
| — **new topics the gap doc missed** | **54** |
| By priority | **10 P1** · 40 P2 · 10 P3 · 1 Watch |
| Gap-doc items kept at P1 without a separate deepened entry | 3 (#1, #4, #8) |
| **Total P1 additions to the curriculum** | **13** |

### The 13 P1 additions (the must-add list)

| # | Topic | Source | Where it goes (see [05](05-revised-syllabus-and-learning-path.md)) |
|---|---|---|---|
| 1 | The FDE operating model and field-to-product loop | [FDE-7](gap-register/E-fde-practice-and-operations.md) | New turn 108a, which opens Section L |
| 2 | Security review, vendor due diligence and AI data-handling terms | [FDE-1](gap-register/E-fde-practice-and-operations.md) | New turn 115a |
| 3 | Integrating agents with systems of record | [FDE-2](gap-register/E-fde-practice-and-operations.md) | New turn 100a |
| 4 | Deploying inside the customer's network (private connectivity, customer-managed keys) | [FDE-3](gap-register/E-fde-practice-and-operations.md) | Extends Turn 92 |
| 5 | Permission-aware retrieval | [RAG-3](gap-register/B-rag-and-data.md) | New turn 50a |
| 6 | Context engineering | [RAG-1](gap-register/B-rag-and-data.md) (gap #7) | New turn 40a |
| 7 | Text-to-SQL and semantic layers | [RAG-5](gap-register/B-rag-and-data.md) (gap #14, **raised from P2**) | New turn 51a |
| 8 | Reasoning controls as an API surface | [MOD-1](gap-register/A-models-and-inference.md) | New turn 21a, or a rewrite of Turn 21 |
| 9 | Agent harness engineering with vendor SDKs | [AGT-1](gap-register/C-agents-and-tooling.md) | Rewrite of Turn 95 |
| 10 | Regulatory incident clocks and mandatory AI records | [SEC-3](gap-register/D-security-and-regulation.md) | Extends Turn 90 |
| 11 | Prompt-injection-resistant architectures | gap #8 (see Template 06 and project P06) | New turn 73a |
| 12 | AI-era security of the orchestration layer | gap #1 (see project P07) | New turn 77a |
| 13 | Regulation as obligations → controls (a global map) | gap #4, deepened by the [regulation map in D](gap-register/D-security-and-regulation.md) and Template 07 | New turn 79a |

**Observation.** 6 of the 13 must-add topics are **FDE practice or delivery** (1–4, 10, 13), and only 2 concern model or agent-SDK features (8, 9). The existing gap doc found only 5 of the 13.

### Area files

| File | Entries | P1 |
|---|---|---|
| [A · Models, inference and customisation](gap-register/A-models-and-inference.md) | 12 | MOD-1 |
| [B · RAG, retrieval and data](gap-register/B-rag-and-data.md) | 10 | RAG-1, RAG-3, RAG-5 |
| [C · Agents, protocols and tooling](gap-register/C-agents-and-tooling.md) | 10 | AGT-1 |
| [D · Security, safety and regulation](gap-register/D-security-and-regulation.md) (includes a 48-row regulation map) | 12 | SEC-3 |
| [E · FDE practice and operations](gap-register/E-fde-practice-and-operations.md) | 11 | FDE-1, FDE-2, FDE-3, FDE-7 |
| [F · Emerging practice](gap-register/F-emerging-practice.md) (horizon items already in practice) | 7 | — |

Each entry includes:
- what it is and why it matters now (with dated, linked evidence);
- what Vol 2 has today (with turn numbers);
- what to teach;
- one idea to remember;
- 2–3 interview questions with answers.

Each area file ends with that area's verified disagreements with Vol 2 and with the gap doc.

---

## 2. The existing gap doc's 23 candidates, re-ranked

Our verdict after fact-checking every candidate ([03 · Errata and fact-check](03-errata-and-fact-check.md), Part B) and adversarially re-testing its priority for an FDE. **Deepened** means this register carries a fuller, corrected entry.

| # | Gap-doc topic | Gap doc | **Ours** | Why we changed it (or agree) | Deepened entry |
|---|---|---|---|---|---|
| 1 | AI-enabled cyber offence and defence | P1 | **P1** | Agree. Frame it as defence: the orchestration layer (agent builders, gateways, MCP servers) is the target, and the job now is to verify AI-found vulnerabilities and patch them at AI speed. All the dated facts check out (GTG-1002, Mythos/Glasswing, Unit 42). | — (see P07) |
| 2 | Computer-use / GUI / browser agents | P1 | **P2** | Situational. Teach the API → MCP → WebMCP → GUI **decision ladder** as P1 inside Turn 61, and computer use itself as P2. OSWorld-Verified scores above 85% are mostly self-reported, and the arXiv citation is wrong. | [AGT-4](gap-register/C-agents-and-tooling.md) |
| 3 | Agentic-browser and computer-use security | P1 | **P2** | Fold into the computer-use turn. The Copilot DLP bug it cites is a permissions failure, not a browser-agent one (it is now cited under RAG-3). | [AGT-4](gap-register/C-agents-and-tooling.md) |
| 4 | Global AI regulation map | P1 | **P1, reframed** | Teach **obligations → controls** (Template 07), not a tour of laws. Rebuild it from statutes and regulators instead of blogs, and add what it missed: EU CRA/PLD, hiring and ADM laws, UK reform, India's sector regulators. | [Section D](gap-register/D-security-and-regulation.md) |
| 5 | Companion-AI, minors and wellbeing law | P1 | **P2 (P1 for consumer products)** | In force, but it applies only to consumer or companion-like products. Tennessee SB 1580 is an "AI therapist" law, not a companion law. | — (see P11) |
| 6 | India IT Rules on synthetically generated information (SGI) | P1 | **P2** | Fold into Turn 84 (provenance) plus an India annex. The duties fall mainly on intermediaries, and the rules cover audio and visual content only. | — (see P14) |
| 7 | Context engineering | P1 | **P1** | Agree. It is now a shipped runtime feature (compaction and context-editing APIs). The OpenClaw incident is real, but the gap doc's arXiv citation for it is wrong. | [RAG-1](gap-register/B-rag-and-data.md) |
| 8 | Prompt-injection-resistant architectures | P1 | **P1** | Strongly agree. This is the highest-leverage engineering addition in either document (CaMeL, dual-LLM, the lethal trifecta). | — (see P06, Template 06) |
| 9 | Frontier safety frameworks and gated release | P2 | **P3** | Deployers do not write these frameworks; they read them. Teach them as vendor due diligence. The US "June 2026 actions" are EO 14409, which is cyber-focused. | — |
| 10 | Sycophancy as a production failure mode | P2 | **P2** | Agree. Put it in the evaluation spine: flip-rate and false-premise evals before every model upgrade. | — (see P11) |
| 11 | Chain-of-thought monitorability | P2 | **P3** | Mostly a lab-side concern. The practical point for FDEs is "do not treat reasoning traces as explanations; set a logging policy for them." | — |
| 12 | Agent memory architectures and products | P2 | **P2** | Agree. Memory ships as framework primitives. Merge with Turns 62 and 130 (see 05); Turn 118 stays Watch (see 04). | — (see P06, P16) |
| 13 | Distribution inside AI assistants | P2 | **P2** | Agree. Fix: MCP Apps became an extension on 26 Jan 2026, and OpenAI's Apps SDK docs now call published units "plugins". | [AGT-5](gap-register/C-agents-and-tooling.md) |
| 14 | Text-to-SQL, semantic layers, analytics agents | P2 | **P1** | Raise it. Enterprise error rates remain high on realistic benchmarks, every major data platform now ships an NL-to-SQL agent, and the gap doc's own claim that it is "the most common request" contradicts its P2 rating. | [RAG-5](gap-register/B-rag-and-data.md) |
| 15 | AI crawler control and content licensing | P2 | **P3** | Niche: it matters to publishers and research agents. Also out of date: Cloudflare moved from pay-per-crawl to pay-per-use pilots in Jul 2026. | — (see P13, P16) |
| 16 | KV-cache offloading, tiering, compression | P2 | **P2** | Agree, extended with prompt-cache retention and cache isolation, which FDEs meet through cost and privacy questions. | [MOD-7](gap-register/A-models-and-inference.md) |
| 17 | TypeScript/JS stack for AI apps | P2 | **P2** | Agree on the need (agent UIs, MCP servers). But its "large share" claim is unsupported: the Python MCP SDK also passed 1B downloads. | — (see P13) |
| 18 | Low-code / visual agent builders | P2 | **P2** | Agree. Teach it together with its security posture. The 647,017 figure came from the attacker's own reconnaissance, not from Unit 42. | [AGT-9](gap-register/C-agents-and-tooling.md) |
| 19 | Web search and web-data APIs for agents | P3 | **P3** | Agree. Date fix: the Responses API has had built-in web search since Mar 2025. | — (see P16) |
| 20 | Multi-token prediction | P3 | **Fold** | One paragraph in Turn 28 (speculative decoding), not a turn. | — |
| 21 | Advertising inside AI assistants | Watch | **P3** | It is live (ChatGPT ads since Feb 2026), not "Watch". The priority stays low because relevance to FDEs is low. | — |
| 22 | Optical/visual context compression | Watch | **Watch** | Research only. Mention it in Turn 120. | — |
| 23 | Tabular and time-series foundation models | Watch | **P3** | Mature (TabPFN v2 in *Nature*, Jan 2025; v2.5 and v3 since), but niche for an LLM curriculum. | — |

**Net effect on the gap doc's P1 list:** 8 P1s become **5 P1s** (#1, #4 reframed, #7, #8, #14). Three drop to P2 (#2, #3, #6), and #5 becomes P2 except for consumer-product tracks.

---

## 3. Master index (all register entries, by priority)

| ID | Topic | Priority | Status | Vol 2 section · placement | Register file |
|---|---|---|---|---|---|
| MOD-1 | Reasoning controls as an API surface: effort levels, thinking budgets and reasoning-state carry-over | **P1** | THIN | B · new turn after Turn 21 (or a substantial rewrite of Turn 21) | [A](gap-register/A-models-and-inference.md) |
| RAG-1 | Gap doc #7 (deepened): Context engineering | **P1** | THIN | D · new turn after Turn 40 (cross-link Turns 31, 55, 58) | [B](gap-register/B-rag-and-data.md) |
| RAG-3 | Permission-aware retrieval: ACL ingestion, permission-sync lag and in-place retrieval | **P1** | THIN | E · new turn after Turn 50 (cross-link Turns 47, 52, 71; co-teach source sync with RAG-4) | [B](gap-register/B-rag-and-data.md) |
| RAG-5 | Gap doc #14 (deepened): Text-to-SQL and semantic layers | **P1** | MISSING | E · new turn after Turn 51 | [B](gap-register/B-rag-and-data.md) |
| AGT-1 | Agent harness engineering with vendor agent SDKs (Claude Agent SDK, OpenAI Agents SDK, Google ADK, Microsoft Agent Framework) | **P1** | THIN | J · extend Turn 95 (rewrite around harness primitives rather than framework brands) | [C](gap-register/C-agents-and-tooling.md) |
| SEC-3 | Regulatory incident clocks and mandatory AI records (EU, India, US) | **P1** | THIN | I · extend Turn 90 (cross-link Turns 78 and 96) | [D](gap-register/D-security-and-regulation.md) |
| FDE-1 | Enterprise security review, vendor due diligence and AI data-handling terms | **P1** | THIN | L · new turn after Turn 115 | [E](gap-register/E-fde-practice-and-operations.md) |
| FDE-2 | Integrating agents with systems of record (Salesforce, ServiceNow, SAP, Workday, Microsoft 365, Slack) | **P1** | THIN | J · new turn after Turn 100 | [E](gap-register/E-fde-practice-and-operations.md) |
| FDE-3 | Deploying inside the customer's network and cloud: private connectivity, customer-managed keys, proxies and self-hosted execution | **P1** | THIN | I · extend Turn 92 | [E](gap-register/E-fde-practice-and-operations.md) |
| FDE-7 | The FDE operating model and the field-to-product feedback loop | **P1** | MISSING | L · new turn after Turn 108 (opening Section L, before Turn 109) | [E](gap-register/E-fde-practice-and-operations.md) |
| MOD-12 | Classifier refusals and cross-model fallback as a production outcome | **P2** | THIN | I · extend Turn 94 (cross-link Turns 26 and 87) | [A](gap-register/A-models-and-inference.md) |
| MOD-13 | Teacher-model terms and safeguards for distillation and synthetic training data | **P2** | THIN | B · extend Turn 23 (cross-link Turns 77 and 85) | [A](gap-register/A-models-and-inference.md) |
| MOD-2 | Open-weight serving fidelity: chat templates, tool-call and reasoning parsers, and cross-provider variance | **P2** | THIN | C · new turn after Turn 29 | [A](gap-register/A-models-and-inference.md) |
| MOD-3 | Uncertainty quantification and selective prediction: calibrated abstain/escalate thresholds, including conformal methods | **P2** | THIN | A · extend Turn 14 (or Turn 64) | [A](gap-register/A-models-and-inference.md) |
| MOD-7 | Gap doc #16 (deepened): KV-cache offloading, prompt-cache retention and cache isolation | **P2** | THIN | C · extend Turn 31 | [A](gap-register/A-models-and-inference.md) |
| MOD-9 | Inference nondeterminism and reproducibility (batch invariance) | **P2** | THIN | C · extend Turn 29 (and correct Turns 87, 93 and 97) | [A](gap-register/A-models-and-inference.md) |
| RAG-10 | Cold-start RAG evaluation: synthetic questions, LLM relevance labels and their biases | **P2** | THIN | E · extend Turn 49 | [B](gap-register/B-rag-and-data.md) |
| RAG-11 | Managed RAG and hosted file search: build vs buy | **P2** | THIN | E · extend Turn 50 (cross-link Turn 72 and RAG-3) | [B](gap-register/B-rag-and-data.md) |
| RAG-4 | Index freshness: incremental (CDC) ingestion, delete propagation, freshness targets and conflicting versions | **P2** | THIN | E · extend Turn 52 (co-teach the change-feed machinery with RAG-3) | [B](gap-register/B-rag-and-data.md) |
| RAG-6 | LLM functions inside the data platform: Snowflake Cortex AISQL, Databricks AI Functions, BigQuery AI | **P2** | MISSING | E · new turn after Turn 52 (cross-link Turns 35, 91; RAG-5, RAG-7) | [B](gap-register/B-rag-and-data.md) |
| RAG-7 | Structured extraction at scale (IDP): confidence-routed review, source grounding and field-level evaluation | **P2** | THIN | E · extend Turn 42 (cross-link Turns 36, 64, 105; threshold calibration taught once in models MOD-3) | [B](gap-register/B-rag-and-data.md) |
| RAG-8 | Agentic retrieval: retrieval as tools, planning cost, and index vs grep for code | **P2** | THIN | E · extend Turns 47 and 56 (cross-link Turn 61) | [B](gap-register/B-rag-and-data.md) |
| RAG-9 | Citation and attribution engineering: span-level citations, citation checking and long-form factuality | **P2** | THIN | E · extend Turns 49 and 14 | [B](gap-register/B-rag-and-data.md) |
| AGT-2 | Multi-agent orchestration patterns (agents-as-tools, handoffs, sequential/concurrent, group chat, magentic) and when not to use them | **P2** | THIN | F · extend Turn 55 (retitle: Subagents, Handoffs and Multi-Agent Orchestration) | [C](gap-register/C-agents-and-tooling.md) |
| AGT-3 | Tool-scale engineering: tool search, code execution over MCP ("code mode") and programmatic tool calling | **P2** | THIN | F · extend Turn 61 | [C](gap-register/C-agents-and-tooling.md) |
| AGT-4 | Gap doc #2 (deepened): Computer-use agents in enterprise operations, the API-to-GUI decision ladder and RPA's agentic successor | **P2** | MISSING | F · new turn after Turn 61 (the gap-doc #2 turn), with a one-paragraph version of the decision ladder inside Turn 61 | [C](gap-register/C-agents-and-tooling.md) |
| AGT-5 | Gap doc #13 (deepened): Distribution inside AI assistants, from public directories to the customer's Microsoft 365 Copilot, Gemini Enterprise and Slack | **P2** | MISSING | J · the gap-doc #13 turn (near Turns 59/101), split into Part A public directories and Part B enterprise-tenant channels, cross-linked to Turn 72 | [C](gap-register/C-agents-and-tooling.md) |
| AGT-6 | Systems-of-record agent platforms (Salesforce Agentforce, ServiceNow, SAP Joule, Workday): integrate, extend or compete | **P2** | MISSING | G · new turn after Turn 72 | [C](gap-register/C-agents-and-tooling.md) |
| AGT-7 | Enterprise agent control planes and agent sprawl (Microsoft Agent 365, ServiceNow AI Control Tower, Gemini Enterprise governance) | **P2** | THIN | G · extend Turn 71 | [C](gap-register/C-agents-and-tooling.md) |
| AGT-8 | Coding-agent governance at team scale: deterministic hooks, managed settings and the plugin supply chain | **P2** | THIN | J · extend Turn 101 | [C](gap-register/C-agents-and-tooling.md) |
| AGT-9 | Gap doc #18 (deepened): Low-code and visual agent builders, their governance, vendor churn and the graduation path to code | **P2** | MISSING | J · new turn after Turn 99 (the gap-doc #18 turn) | [C](gap-register/C-agents-and-tooling.md) |
| SEC-1 | EU Cyber Resilience Act and revised Product Liability Directive for AI software | **P2** | MISSING | H · new turn after Turn 82 (one turn for both laws; the horizon lens's HOR-9 proposes the same pair, so keep only one) | [D](gap-register/D-security-and-regulation.md) |
| SEC-10 | Shadow-AI discovery and the enterprise AI inventory | **P2** | THIN | H · new turn after Turn 80 | [D](gap-register/D-security-and-regulation.md) |
| SEC-11 | India's sectoral AI governance: RBI (FREE-AI and draft MRM guidance), SEBI, MeitY guidelines and CERT-In | **P2** | MISSING | H · new turn after Turn 81 (or an India BFSI block in Turn 82) | [D](gap-register/D-security-and-regulation.md) |
| SEC-13 | Accessibility law for AI interfaces (EU EAA, US ADA Title II, India's SEBI digital-accessibility circulars) | **P2** | THIN | H · extend Turn 83 (cross-link Turn 59 Agent User Interfaces) | [D](gap-register/D-security-and-regulation.md) |
| SEC-14 | Outbound AI voice and text agents under US telemarketing law (TCPA and FCC AI-voice ruling) | **P2** | THIN | H · extend Turn 60 (cross-link Turn 82) | [D](gap-register/D-security-and-regulation.md) |
| SEC-4 | EU GPAI rules for downstream modifiers and the GPAI Code of Practice | **P2** | THIN | H · extend Turn 79 | [D](gap-register/D-security-and-regulation.md) |
| SEC-5 | Automated-decision and AI-in-hiring rules beyond GDPR Art. 22 (US state and city rules, UK DUAA) | **P2** | THIN | H · new turn after Turn 83 (cross-link Turn 81) | [D](gap-register/D-security-and-regulation.md) |
| SEC-6 | Gap doc #5 (deepened): Companion-AI, minors and age assurance | **P2** | MISSING | H · the gap-doc #5 turn: new turn after Turn 83 (cross-link Turn 26) | [D](gap-register/D-security-and-regulation.md) |
| SEC-7 | Deepfake and voice-clone fraud against identity verification (KYC, call centres, help desks) | **P2** | THIN | H · new turn after Turn 78 (cross-link Turns 60 and 106) | [D](gap-register/D-security-and-regulation.md) |
| SEC-8 | Multi-tenant isolation and LLM side channels (prompt-cache timing, KV-cache sharing, token-length leaks) | **P2** | THIN | H · extend Turn 74 (with a security note in Turn 31) | [D](gap-register/D-security-and-regulation.md) |
| FDE-11 | Records retention, supervision and eDiscovery for AI interactions and agent actions (the opposite of ZDR) | **P2** | THIN | H · extend Turn 82 | [E](gap-register/E-fde-practice-and-operations.md) |
| FDE-4 | Provider capacity engineering: quota dimensions, service tiers, provisioned throughput and spillover | **P2** | THIN | I · extend Turn 94 | [E](gap-register/E-fde-practice-and-operations.md) |
| FDE-5 | Measuring real impact honestly: controlled productivity measurement versus self-report | **P2** | THIN | L · extend Turn 110 (cross-link Turn 88) | [E](gap-register/E-fde-practice-and-operations.md) |
| FDE-8 | Acceptable-use boundaries, provider usage policies and saying no | **P2** | THIN | L · extend Turn 109 | [E](gap-register/E-fde-practice-and-operations.md) |
| FDE-9 | Permission hygiene and oversharing remediation before enterprise knowledge AI | **P2** | THIN | L · extend Turn 115 | [E](gap-register/E-fde-practice-and-operations.md) |
| HOR-1 | Frontier-agent containment (egress paths, live monitoring, tested automatic stop), with automated AI R&D as a Watch note | **P2** | THIN | H · extend Turn 86 and Turn 73; automated-AI-R&D half as a Watch box in Turn 135; co-teach with HOR-11 | [F](gap-register/F-emerging-practice.md) |
| HOR-11 | Goal-driven agent misbehaviour with real credentials: credential misuse, secret-scanning evasion, covert channels and answer-seeking | **P2** | THIN | G · extend Turn 73 with a 2026 incident-case box (cross-link Turns 86, 71 and 132); co-teach with HOR-1 as one "misaligned-agent incidents" extension | [F](gap-register/F-emerging-practice.md) |
| HOR-6 | Workforce-impact evidence and algorithmic-management law (AI in employment decisions) *(overlaps SEC-5 (the law); HOR-6 keeps the workforce-evidence part)* | **P2** | THIN | H · "AI in employment decisions" sub-box in gap #4's US regulation map; P3 Platform Work note in Turn 83; evidence paragraph in Turns 110 and 114 | [F](gap-register/F-emerging-practice.md) |
| HOR-8 | Provenance, attribution and licensing of agent-written code | **P2** | THIN | J · extend Turn 101 (this is the content of the Turn 127 merge; cross-link Turns 85 and 127) | [F](gap-register/F-emerging-practice.md) |
| HOR-9 | EU software liability and cyber-resilience for AI products (new Product Liability Directive + Cyber Resilience Act) *(duplicate of SEC-1; canonical entry there)* | **P2** | MISSING | H · new turn after Turn 82 (Turn 82a, as for SEC-1) | [F](gap-register/F-emerging-practice.md) |
| MOD-10 | Small specialised models inside agent systems (SLM-first, fine-tune-to-replace) | **P3** | THIN | B · extend Turn 23 (one paragraph) | [A](gap-register/A-models-and-inference.md) |
| MOD-11 | Side effects of fine-tuning and distillation: emergent misalignment and subliminal trait transfer | **P3** | THIN | B · extend Turn 26 (one paragraph; cross-reference Turns 23 and 25) | [A](gap-register/A-models-and-inference.md) |
| MOD-4 | Reinforcement fine-tuning (RFT) as a managed service: graders, rubric rewards and platform choice | **P3** | THIN | B · extend Turn 22 (move Turn 135's practical Q&As there; no new turn) | [A](gap-register/A-models-and-inference.md) |
| MOD-6 | Microscaling low-precision formats and quantisation-native model releases | **P3** | THIN | C · extend Turn 30 (one paragraph) | [A](gap-register/A-models-and-inference.md) |
| MOD-8 | Serverless GPU inference: autoscaling, scale-to-zero and cold starts | **P3** | THIN | C · extend Turn 33 (one paragraph plus one Q&A on autoscaling signals) | [A](gap-register/A-models-and-inference.md) |
| SEC-9 | Model extraction and distillation abuse: protecting your model APIs | **P3** | MISSING | H · extend Turn 74 (the terms gate for distilling from someone else's API goes once in Turn 23, via MOD-13) | [D](gap-register/D-security-and-regulation.md) |
| FDE-10 | Multi-tenant architecture for AI features: isolation and per-tenant configuration | **P3** | THIN | J · extend Turn 100 (cross-link Turn 74) | [E](gap-register/E-fde-practice-and-operations.md) |
| FDE-6 | Commercial models for AI features: seats, usage credits and outcome-based pricing | **P3** | THIN | L · extend Turn 116 | [E](gap-register/E-fde-practice-and-operations.md) |
| HOR-2 | LLM-assisted formal verification and automated-reasoning guardrails | **P3** | THIN | J · Automated Reasoning box in Turn 98 (Guardrail Tools); proof-checking paragraph in Turn 101 (ex-Turn 127) | [F](gap-register/F-emerging-practice.md) |
| HOR-5 | Model-origin and compute governance (chip export controls, government evaluations of foreign models) | **P3** | THIN | J · origin-and-controls rows in the Turn 102 model scorecard, as part of the Turn 134 merge into Turns 92/102 (pointer from Turn 33) | [F](gap-register/F-emerging-practice.md) |
| AGT-10 | Generative-UI protocol choice: AG-UI vs A2UI vs MCP Apps | **Watch** | THIN | F · one sentence plus one Q&A in Turn 59 | [C](gap-register/C-agents-and-tooling.md) |

---

## 4. Limitations

- **What we checked coverage against:** we checked against the **study guide** (summaries, 676 Q&As, 228-term index), not the 890-page full book, and we did not have Volume 1. Some "THIN" topics may get more space in the full book.
- **Evidence gaps:** WebSearch quota ran out for several agents partway through, so they finished by fetching primary pages directly. Anything they could not confirm is marked "(unverified)" or "verify before teaching" in the entry.
- **Law:** laws and dates change monthly. Treat the regulation entries as an engineering map, not legal advice, and re-verify them in the quarterly refresh (see [05 §4](05-revised-syllabus-and-learning-path.md#4-keeping-it-true-the-evergreen-core-and-a-dated-annex)).
