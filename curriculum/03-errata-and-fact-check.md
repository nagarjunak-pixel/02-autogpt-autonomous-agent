# 03 · Errata and Fact-Check (as of 26 September 2026)

We ran two independent checks, each against dated sources, primary sources wherever they exist:
1. **Vol 2 itself.** We checked 50 of the most interview-relevant time-sensitive claims: product versions, spec dates, regulatory obligations, benchmark figures and ownership. Topics already re-checked by the existing gap doc were skipped.
2. **The existing gap doc** (*Coverage Gaps and Fact-Check*). We checked the load-bearing claims behind each of its 23 candidates, its 9 "secondary check" corrections, its "verified as stated" items and its headline claims.

| Document | Claims checked | Correct | Needs nuance | Outdated | Wrong | Unverifiable |
|---|---|---|---|---|---|---|
| Vol 2 study guide | 50 + 5 follow-ups | **41** | 11 | 3 | 0 | 0 |
| Gap doc | 57 | **30** | 17 | 2 | 5 | 3 |

**What this says:**
- Vol 2 has 3 outdated claims, and they are serious: US bank model-risk guidance changed in April 2026 (A1), AP2's mandate model changed in v0.2 (A10), and OpenAI is closing its fine-tuning platform (A13). The other 11 corrections add nuance. A1–A9 come from the main check. A10–A14 are follow-ups that later research agents found and verifiers confirmed. For a fast-moving field, the rest of Vol 2 is accurate.
- The gap doc's facts are mostly right, but its *citations* are weaker than its conclusions. Two arXiv IDs point to unrelated papers, one statistic is misattributed, and several legal claims rest on blogs where statutes or regulator pages exist.
- This is a fact-check for teaching, not legal advice. Re-verify legal points before each cohort, and confirm them with counsel before relying on them in an engagement.
- We spot-checked the two most consequential findings ourselves against primary sources: the SR 11-7 replacement (Federal Reserve SR 26-2; OCC Bulletin 2026-13) and the arXiv 2606.29175 mis-citation. Both held.

---

## Part A · Corrections to Vol 2 (ranked by damage if repeated in an interview or to a customer)

### A1. Turn 82, Q406 and the index: SR 11-7 has been superseded (OUTDATED, high impact)
- **Vol 2 says:** US bank model-risk management follows SR 11-7, and LLM systems should be validated "like any other model".
- **Correct as of Sept 2026:** On **17 Apr 2026** the Fed, OCC and FDIC issued *Revised Guidance on Model Risk Management* (Fed **SR 26-2**, OCC **Bulletin 2026-13**). It "supersedes and replaces SR letter 11-7". The OCC bulletin also rescinds Bulletin 2011-12, and the guidance states twice: *"Generative AI and agentic AI models are novel and rapidly evolving. As such, they are not within the scope of this guidance."* The agencies plan a separate request for information on AI.
- **Teach instead:** US bank MRM guidance no longer formally covers LLM or agent systems. Banks must govern them through their own risk-management frameworks, and many still apply MRM-style inventory, validation and monitoring voluntarily. That remains good practice, and customers will expect it. Watch for the AI RFI.
- Sources: [federalreserve.gov SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm) · [OCC Bulletin 2026-13](https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html)

### A2. Turn 85, Q419: the copyright answer is one-sided (NEEDS NUANCE)
- **Correct:** Bartz v. Anthropic (23 Jun 2025) and Kadrey v. Meta (25 Jun 2025) found training to be fair use on their records, and Bartz settled for $1.5B. The Q&A leaves out the other side:
  - *Thomson Reuters v. Ross* (D. Del., Feb 2025): copying headnotes to train a non-generative tool was **not** fair use. The Third Circuit heard argument on 11 Jun 2026, and no decision had been issued as of Sept 2026.
  - *GEMA v. OpenAI* (Munich Regional Court I, 11 Nov 2025): lyrics memorised in a model are a reproduction.
  - *Getty v. Stability AI* ([2025] EWHC 2863 (Ch), 4 Nov 2025): model weights are not an infringing copy.
- **Teach:** outputs can infringe, memorised weights can infringe (at least in Germany), and the key US appellate ruling is pending.

### A3. Turn 83, Q408: the four-fifths rule's federal footing has eroded (NEEDS NUANCE)
- The impact-ratio definition is right, and NYC Local Law 144 bias audits still require impact ratios.
- But Executive Order 14281 (23 Apr 2025) directs federal agencies to minimise disparate-impact liability, and on **9 Jun 2026** the DOJ Office of Legal Counsel concluded that the EEOC's disparate-impact guidelines are unconstitutional. They have not been formally rescinded, and Title VII itself is unchanged.
- **Teach:** the four-fifths rule as a screening heuristic that state and local audits and private litigation still use, paired with statistical-significance tests. Do not teach it as an actively enforced federal test.
- Source: [DOJ press release](https://www.justice.gov/opa/pr/justice-department-concludes-eeoc-disparate-impact-guidelines-violate-constitution)

### A4. Turn 96, Q475: the OTel GenAI conventions are not stable (NEEDS NUANCE)
- The conventions moved to a separate repository, `semantic-conventions-genai`, and are still at **Development** status. Attribute names have changed between versions.
- "Switching tools becomes configuration" is the goal, not today's reality. Pin the semconv version you emit and check each back end's support.
- Sources: [opentelemetry.io](https://opentelemetry.io/docs/specs/semconv/gen-ai/) · [GitHub repo](https://github.com/open-telemetry/semantic-conventions-genai)

### A5. Turn 97, index: Promptfoo is now owned by a model vendor (NEEDS NUANCE)
- OpenAI announced its acquisition of Promptfoo on **9 Mar 2026**. Promptfoo remains open source and multi-provider.
- This matters when a customer needs a *vendor-neutral* evaluation or red-team harness. Mention the ownership, and offer DeepEval, Inspect (UK AISI) or an in-house harness as alternatives.
- Source: [Promptfoo blog](https://www.promptfoo.dev/blog/promptfoo-joining-openai/)

### A6. Turn 34, Q165: Ollama's default context now depends on VRAM (NEEDS NUANCE)
- The Ollama docs now set the default context by detected VRAM: under 24 GiB → 4k tokens; 24–48 GiB → 32k; 48 GiB or more → 256k.
- The silent failure is therefore hardware-dependent. Laptops still truncate long prompts, while big GPUs can allocate a very large KV cache and spill to CPU.
- **Teach:** always set `num_ctx` / `OLLAMA_CONTEXT_LENGTH` explicitly and verify it with `ollama ps`.
- Source: [docs.ollama.com/context-length](https://docs.ollama.com/context-length). The version and date come from secondary sources; verify them before teaching.

### A7. Turn 80: NIST AI RMF 1.0 is under revision (NEEDS NUANCE)
- NIST's page states that AI RMF 1.0 "is being revised as part of the White House AI Action Plan". A concept note for a critical-infrastructure profile followed on 7 Apr 2026.
- Cite it as "AI RMF 1.0 (under revision)" and expect control mappings built on it to change.
- Source: [nist.gov](https://www.nist.gov/itl/ai-risk-management-framework)

### A8. Turn 84, Q416: "green list" describes one watermarking scheme, not all of them (NEEDS NUANCE)
- The green/red-list method is the Kirchenbauer et al. (KGW) scheme. SynthID-Text (Nature, Oct 2024), which is deployed in Gemini, instead uses tournament sampling with keyed g-functions.
- Reword the answer to "for example, in the green-list (KGW) scheme…" and add one line on tournament sampling.
- Source: [Nature](https://www.nature.com/articles/s41586-024-08025-4)

### A9. Turn 93, Q460: Kubernetes GPU scheduling now includes DRA (NEEDS NUANCE)
- Dynamic Resource Allocation went GA in Kubernetes **v1.34** (Sept 2025). Workloads request devices by attributes through ResourceClaims, which also enables better sharing and MIG partitioning.
- Device plugins still work, but a 2026 answer should name DRA.
- Source: [kubernetes.io](https://kubernetes.io/blog/2025/09/01/kubernetes-v1-34-dra-updates/)

### A10. Turn 70, Q344: AP2 mandate types changed in v0.2 (OUTDATED)
- **Vol 2 says:** an AP2 mandate records "intent, the exact cart, and the payment".
- **Correct as of Sept 2026:** those were the **v0.1** (Sept 2025) names. **AP2 v0.2, released 28 Apr 2026**, defines two SD-JWT mandate types:
  - a **Checkout Mandate**, which covers what is bought and is shared with the merchant;
  - a **Payment Mandate**, which covers the payment and is shared with the credential provider, network and processor.

  Each mandate is either **open** (the user's constraints, for human-not-present purchases) or **closed** (bound to one final checkout and amount). Google contributed AP2 to the **FIDO Alliance** on the same day.
- Sources: [AP2 specification](https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/specification.md) · [AP2 changelog](https://github.com/google-agentic-commerce/AP2/blob/main/CHANGELOG.md) · [Google blog](https://blog.google/products-and-platforms/platforms/google-pay/agent-payments-protocol-fido-alliance/)
- Checked in the same pass, **no correction needed:**
  - Vol 2's WebMCP text names no entry point. The spec moved to `document.modelContext` on 27 May 2026, so any code sample in the full book that uses `navigator.modelContext` needs updating.
  - Vol 2 says nothing specific about ChatGPT apps or checkout. For the record: OpenAI's Apps SDK docs now redirect to **"Plugins"**, and third-party plugins must use external checkout except in beta programmes.

### A11. Turns 87, 93 and 97 (Q429, Q461, Q480): "low temperature and pinning make outputs reproducible" (NEEDS NUANCE)
- **Problem 1: temperature is not always available.** Some current reasoning models reject a non-default `temperature` with an HTTP 400. Examples: Claude Opus 4.7 and later, and the GPT-5.x and o-series models on Azure. Other current models (the GPT-6 family, Gemini 3) accept it. So Q480's first remedy, "low temperature", can simply fail.
- **Problem 2: temperature 0 is not deterministic.** Thinking Machines (10 Sep 2025) sampled one prompt 1,000 times at temperature 0 on a standard serving stack and got **80 unique completions**. The cause is batch-dependent numerics. Batch-invariant kernels made all 1,000 identical, at roughly 1.6–2× the cost. Hosted-API users cannot switch this on.
- **Teach instead:**
  - Pinning makes behaviour *stable and deliberate*, not *bitwise reproducible*.
  - In CI, rely on repeated runs, tolerance bands, confidence intervals and pinned judges.
  - Store outputs so failures can be replayed.
- Sources: [Thinking Machines](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) · provider model docs (check the current model's parameter support before teaching).

### A12. Turn 23, Q110: distillation "works even when only a text API is available" (NEEDS NUANCE)
- It is technically true, but it leaves out the **provider's terms**. Many commercial terms restrict using outputs to train competing models, and providers monitor for distillation.
- **Teach:**
  - Check the teacher's output-use terms before distilling or generating synthetic training data.
  - Prefer an open-weight teacher whose licence allows it.
  - Record which licence terms flow down to the student model.
- See gap register entry MOD-13.

### A13. Turn 135: managed reinforcement fine-tuning is consolidating, and OpenAI's platform is closing (OUTDATED framing)
- OpenAI is **winding down its self-serve fine-tuning platform, including RFT**:
  - **7 May 2026:** announced; new users are already blocked.
  - **6 Jan 2027:** no customer can create new fine-tuning jobs.
  - **23 Oct 2026:** o4-mini, OpenAI's only RFT model, shuts down.
  - Inference on already fine-tuned models continues until their base model is deprecated.
- Managed RFT continues elsewhere, for example Amazon Bedrock (from 3 Dec 2025), Microsoft Foundry and Tinker (GA 12 Dec 2025).
- **Teach:** "post-training as a service" is real but provider-dependent. Keep training data and graders portable.
- Sources: [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations) · [OpenAI RFT guide](https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning)

### A14. Turns 94 and 103 (Q464, Q510): retry guidance for HTTP 429 is incomplete (NEEDS NUANCE)
- "Retry rate limits with exponential backoff and jitter" is right *after* two more rules:
  1. **Honour `Retry-After` first.** Anthropic's normal 429s send it; Microsoft Graph recommends backoff only when it is absent.
  2. **Classify 429s: some are not retryable.** For example, Anthropic's spend-cap 429 (`enforced_spend_limit_reached`) carries no `Retry-After` and keeps failing until access is restored. Aggressive retries against SharePoint/Graph count against the quota and prolong throttling.
- **Teach:** honour `Retry-After` → classify → back off with jitter within a retry budget → stop and alert on quota or spend-cap errors.

### Also update: Turn 134, Q668 (open-weight lag)
- Epoch AI's 29 May 2026 data insight reports that open models lag the closed frontier by **~4 months (8 ECI points)** since Jan 2026. The ~3 months in Vol 2 covered Jan 2023–Oct 2025.
- Teach it as a range; the figure comes from one index over a short window.
- Source: [epoch.ai](https://epoch.ai/data-insights/open-closed-eci-gap)

### Checked and correct (highlights)
The following all hold:
- The Section G protocol and commerce claims: A2A bindings and signed cards, AP2 mandates, SPT, x402, UCP/ACP, XAA/ID-JAG, MCP Apps and the WebMCP APIs.
- The EU GPAI Code of Practice status.
- The OWASP Agentic Top 10.
- The "250 documents can poison a model" result, AlphaEvolve, and Titans/Nested Learning.
- The EU AI Act high-risk dates as amended (2 Dec 2027 stand-alone; 2 Aug 2028 embedded).
- The arithmetic in Q63, Q283, Q436, Q444 and Q585 (for example, a 99.5% SLO allows ~216 min/month of downtime).

---

## Part B · Corrections to the existing gap doc

### B1. Wrong
| Ref | Gap doc says | Correct |
|---|---|---|
| #2 | "Frontier agents exceed 85% on OSWorld-Verified by July 2026 (arXiv 2607.26041)" | **Mis-cited.** 2607.26041 is *Desktop-Delta Bench* and reports no OSWorld-Verified scores. Scores of 85% or more appear only on third-party aggregators in Sept 2026 and are mostly self-reported. The Q&A also mixes up OSWorld and OSWorld-Verified. |
| #7 | "OpenClaw agent lost its constraint during compaction… (cited in arXiv 2606.29175)" | **Mis-cited; we verified this ourselves.** 2606.29175 is an international-humanitarian-law paper. The incident itself is real (23 Feb 2026: a "suggest, don't act" instruction was lost in compaction and 200+ emails were deleted), but it is documented only in secondary post-mortems ([vectara/awesome-agent-failures](https://github.com/vectara/awesome-agent-failures/blob/main/docs/case-studies/openclaw-email-deletion.md)). Label it "reported". Separately, its THIN note "no compaction" is slightly off: Turn 58 (Q284) mentions compaction, though it does not teach it. |
| #18 | "Unit 42 counted 647,017 exposed n8n instances" | **Misattributed.** The figure is a FOFA search run by the *attacker's* AI agent during reconnaissance, which Unit 42 quoted (30 Jul 2026). Independent counts measure different things: Shadowserver ~105,753 instances vulnerable to CVE-2026-21858; Censys ~103,476. "Actively targeted" is right: CISA KEV added n8n CVE-2025-68613 (Mar 2026) and Langflow (Jul–Aug 2026). |
| Dating | "as of 27 September 2026" | The document is dated after the actual check date (26 Sept 2026). Several of its figures were already stale (see B2). |
| Internal counts | "Four need fixing"; "Add as P1" lists 7; "(a), (b), (i), (k) verified" | The document contradicts itself: it lists **9** problems, its table has **8** P1s (agentic-browser security is missing from the P1 list), and item (i) is never shown. Its (a)–(m) letters refer to a claim list the reader never sees. |

### B2. Outdated
| Ref | Correct as of Sept 2026 |
|---|---|
| #2 OSWorld 2.0 "tops out at 20.6%" | This was the paper's best result at publication (arXiv 2606.29537, 28 Jun 2026). The hosted leaderboard showed a top entry of about 44% on 26 Sept 2026. Timestamp every leaderboard figure. The mis-scoring paper the doc alludes to is arXiv 2607.28367: 15.3% of FAIL verdicts were wrong. |
| #15 Cloudflare pay-per-crawl | Pay-per-crawl was in private beta from 1 Jul 2025. On 1 Jul 2026 Cloudflare began piloting **pay-per-use**: publishers are paid when their content is cited in AI answers. RSL 1.0 became an official spec in Dec 2025. The IETF aipref vocabulary was still a draft when last checked. |

### B3. Needs nuance (the facts are mostly right, but the framing misleads)
- **#3:** The Microsoft Copilot Chat bug (advisory CW1226324, Jan–Feb 2026) was a DLP/sensitivity-label failure in which confidential emails were summarised. It says nothing about agentic browsers; cite it under **permission-aware retrieval and data governance** instead.
- **#5:** Tennessee SB 1580 (effective 1 Jul 2026) is **not** a companion-chatbot or minors law. It bars claiming an AI is a qualified mental-health professional, so it belongs to the adjacent "AI therapist" category. Washington's companion law is HB 2225, effective 1 Jan 2027, like Oregon SB 1546.
- **#9:** The "June 2026 US executive actions" are **EO 14409** (signed 2 Jun 2026): a classified NSA/CISA cyber-capability benchmark that designates "covered frontier models", plus voluntary pre-release government access. It is cyber-focused, not a general frontier-safety regime. For FDEs, frontier safety frameworks are **P3** (vendor due diligence), not P2.
- **#13:** MCP Apps became the first official MCP extension on **26 Jan 2026**. The 2026-07-28 release formalised the extensions framework. The real gap is distribution and review in app directories.
- **#17:** Both dated facts hold, but "a large share of production agent UIs and MCP servers are TypeScript" is unsupported: the Python MCP SDK also passed 1B downloads.
- **#19:** The Responses API has had built-in web search since its launch on **11 Mar 2025**, not "2026".
- **#21:** Ads in ChatGPT are live, not "Watch": US tests were announced 16 Jan 2026, ads went live around 9 Feb 2026, and pilots in Canada, Australia and New Zealand were announced 26 Mar 2026. The low priority is still justified, but by low FDE relevance rather than maturity.
- **#23:** Tabular foundation models are mature, not "early": TabPFN v2 was published in *Nature* in Jan 2025, followed by TabPFN-2.5 (Nov 2025) and the TabPFN-3 report (May 2026).
- **Regulation scope:** "Regulation stops at the EU and India" overstates the gap. Vol 2 already covers NIST AI RMF, ISO/IEC 42001, HIPAA and (now outdated) SR 11-7. What is genuinely missing is US preemption, US state AI statutes, Korea, China, and more (see the gap register).
- **Secondary (e), the Digital Omnibus (Reg. (EU) 2026/1744):** The dates hold. Add that the new **Article 5 ban on non-consensual intimate imagery and CSAM generation applies from 2 Dec 2026**, with no grace period for systems already on the market. The Art. 50(2) marking grace period to 2 Dec 2026 applies only to systems placed on the market before 2 Aug 2026.
- **Secondary (f), DPDP:** Teach the dates as "12 and 18 months from notification (Nov 2026, May 2027)"; sources disagree on the exact day.
- **Secondary (g), ANI v. OpenAI:** Both documents miss that **ANI has appealed**; Bar & Bench reported on 7 Sep 2026 that the appeal is pending before the Delhi High Court.
- **Secondary (c) and (d):** A2A v1.0 was released on 12 Mar 2026, and A2A joined AAIF on 17 Aug 2026 (AAIF's own post). Vol 2 never states a wrong date for either, so these are not errors in the guide.
- **Secondary (m):** The ~4-month open-weight lag is confirmed (see A-list). Epoch's "probably understated" remark could not be confirmed.

### B4. Unverifiable
- The headline **"coverage is roughly 85–90%"** has no taxonomy, denominator or scoring rule behind it. Treat it as an impression. [01-curriculum-review.md](01-curriculum-review.md) replaces it with specific, checkable gaps.
- Item (i) in "verified as stated" is never shown.
- **#14:** The MISSING label for text-to-SQL is right, but "most common enterprise FDE request" has no supporting evidence. Either support it or drop the superlative. Note also that the gap doc ranks it only P2 while calling it the most common request, which is inconsistent.

### Verified as stated (30 items), for the record
- **Cyber:** GTG-1002 (Nov 2025); Claude Mythos Preview withheld and released via Project Glasswing (7 Apr 2026) with $100M in credits; the 22 May 2026 Glasswing update (1,752 findings reviewed, 90.6% valid, 62.4% high or critical); Glasswing expanded in June 2026; Unit 42 and GTIG orchestration-layer targeting.
- **US law:** EO 14365 and the DOJ AI Litigation Task Force; the White House National Policy Framework (non-binding); xAI v. Colorado and Colorado SB 26-189; California SB 53; SB 243 and New York's companion law.
- **Other jurisdictions:** Korea's AI Basic Act (22 Jan 2026); China's labelling measures (Sept 2025); India's G.S.R. 120(E) (in force 20 Feb 2026).
- **Research and incidents:** CaMeL (77% vs 84% in AgentDojo); the lethal trifecta (16 Jun 2025); the GPT-4o sycophancy rollback (25–28 Apr 2025); CoT monitorability (arXiv 2507.11473); DeepSeek-OCR; multi-token prediction in DeepSeek-V3.
- **Products and specs:** KV-cache offloading support; MAF 1.0 memory primitives and harness compaction; both MCP SDKs passing 1B downloads; the MCP 2026-07-28 details; the LiteLLM PyPI compromise (24 Mar 2026); the WebMCP origin trial (Chrome 149); the Assistants API sunset (26 Aug 2026); ANS as "intent to launch" (23 Jun 2026).

---

## Part C · Keeping the curriculum true: a process, not a one-off

1. **Tag every volatile fact** with an as-of date, a source URL, an owner and a review-by date.
2. **Quarterly re-verification sprint** covering the dated annex, the regulation map and the calendar in [04-future-topics-2026-2028.md](04-future-topics-2026-2028.md).
3. **Citation hygiene.** Open every arXiv ID before citing it, and never cite a benchmark leaderboard without a date. For law, cite the statute or regulator page, or a law firm; avoid blogs.
4. **Keep interview answers durable.** Teach the principle (for example, "pin the semconv version you emit") and put the volatile fact in a footnote.
