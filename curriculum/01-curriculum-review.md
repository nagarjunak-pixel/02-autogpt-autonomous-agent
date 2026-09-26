# 01 · Curriculum Review: LLM Training Flow, Volume 2

**Scope:** *LLM Training Flow Volume 2 Study Guide* (135 topics called "Turns" in 13 sections, 676 interview Q&As and a 228-term index), and the separate *Coverage Gaps and Fact-Check (Sept 2026)* document. Both are reviewed as of **26 September 2026**.
**Question asked:** How good is this curriculum for training AI engineers and Forward Deployed Engineers (FDEs), what is missing, and what will be needed over the next 12–24 months?

> **Limitation.** We reviewed the *study guide*, not the 890-page full-depth book, and we do not have Volume 1. Where we say a topic is "missing", we mean the study guide's summaries, Q&As and index do not teach it. The full book may mention it in passing.

---

## Bottom line

1. **The content is mostly accurate and unusually current on the agent-protocol layer.** We checked 50 time-sensitive claims: 41 are correct and 9 need fixing (details in [03-errata-and-fact-check.md](03-errata-and-fact-check.md)). The most damaging error is in Turn 82: it still teaches SR 11-7 as the US bank model-risk standard. SR 11-7 was replaced on 17 Apr 2026, and the replacement guidance puts generative and agentic AI **out of scope**.
2. **As an FDE curriculum it has four structural problems, and they matter more than any single missing topic.**
   - Priority inflation: 51% of the core topics are labelled P1.
   - Effort is inverted relative to the job: model internals get the most pages per topic, and FDE practice gets some of the fewest.
   - Assessment is recall-only: there are 676 short-answer questions and zero projects.
   - Fast-rotting facts are mixed into the core, with no mechanism to refresh them.
3. **The existing gap analysis is a useful peer review, but it has blind spots of its own.**
   - It is driven by news items.
   - It proposes eight new P1 topics without cutting anything.
   - It never examines FDE practice (security reviews, systems-of-record integration, customer environments), which is where FDE time actually goes.
   - Its "85–90% coverage" figure has no stated method.
4. **Fixes, in order of leverage:**
   - Re-tier the priorities to a ~30-topic FDE core.
   - Add the 16 real-world projects in [projects/](projects/README.md) as the assessment backbone.
   - Split dated facts into a versioned annex with owners and review dates.
   - Add the verified gap topics in [02-gap-register.md](02-gap-register.md).
   - Merge overlapping turns to make room (see [05-revised-syllabus-and-learning-path.md](05-revised-syllabus-and-learning-path.md)).

---

## 1. What the curriculum does well (and why)

- **Traceable status labels.** Every topic is tagged MISSING, THIN, NEW, LOST or FUTURE against Volume 1 and has a priority. That lets anyone audit coverage, and this review depends on it.
- **The protocol layer is current and checks out.** MCP 2026-07-28, A2A v1.0, AAIF, WebMCP, the agentic-commerce protocols, and XAA/ID-JAG identity are all taught, and both fact-checks confirmed them against primary sources.
- **The one-sentence summaries are operational heuristics, not definitions.** Examples: "fix data and tools before models" (Turn 89), "when a verifier exists, checking beats voting" (Turn 37), "a limit lives inside the tool, not in the prompt" (Turns 61 and 117). These are the lines engineers actually use in design reviews.
- **It has an FDE section at all** (Turns 109–117), with sensible content on discovery, ROI, the POC→pilot→production path, ADRs, honest demos and SOWs. Few AI curricula have one.
- **Security is treated as architecture, not filters** (for example "guardrails cannot replace permissions", Turn 98).

## 2. Structural problems

### 2.1 Priority inflation: when half of the syllabus is P1, the label carries no signal

| Priority | Topics | Share of the 117 non-future topics |
|---|---|---|
| P1 | 60 | **51%** |
| P2 | 49 | 42% |
| P3 | 8 | 7% |
| Watch (Section M) | 18 | n/a |

A learner with 10–12 weeks cannot cover 60 "most important" topics in depth. Adding the existing gap doc's eight P1 candidates would push P1 to about 68.
**Recommendation:** define a **~30-topic FDE core** (P1), move the rest to P2/P3 electives, and justify each P1 by "an FDE meets this in most engagements, or it is legally required for common deployments". [05-revised-syllabus-and-learning-path.md](05-revised-syllabus-and-learning-path.md) proposes the re-tiering.

### 2.2 Effort is inverted relative to the target role

| Section | Topics | Book pages | Pages/topic | P1 topics |
|---|---|---|---|---|
| A · Architecture & internals | 15 | 135 | **9.0** (highest) | 5 |
| B · Post-training | 11 | 81 | 7.4 | 6 |
| C · Inference & hardware | 10 | 72 | 7.2 | 3 |
| E · RAG & data | 11 | 77 | 7.0 | 6 |
| F · Agent engineering | 12 | 76 | 6.3 | 6 |
| H · Security & compliance | 13 | 82 | 6.3 | 6 |
| I · LLMOps | 8 | 49 | 6.1 | 5 |
| J · Tooling | 10 | 60 | 6.0 | 7 |
| **L · FDE professional skills** | 9 | 52 | **5.8** | 6 |
| **K · Multimodal** | 4 | 21 | **5.2** | 2 |
| M · Future topics | 18 | 88 | 4.9 | 0 |

Section A gets the most depth per topic and includes FlashAttention tiling, distributed-training parallelism, training dynamics and mechanistic interpretability. An FDE almost never pre-trains a model; they need to *reason* about internals (KV-cache memory maths, MoE memory cost, tokenizer cost per language), not rebuild them.
Meanwhile Section L, the role the curriculum is named for, gets 5.8 pages per topic. Vision-language models and speech are both labelled P1, yet all of multimodal gets 21 pages.
**Recommendation:** compress A to "what a deployer must be able to calculate and explain" (about 50% fewer pages) and reinvest the pages in L, K and the new practice topics.

### 2.3 Assessment is recall-only

Each turn ends with 4–8 short-answer interview questions (676 in total). There are **no labs, no design exercises, no graded artefacts and no projects**. FDEs are judged by artefacts: a discovery memo, a frozen eval set, an SOW with measurable acceptance criteria, a threat model, a running system, a handover drill.
**Recommendation:** use the 16 projects in [projects/](projects/README.md) as the backbone. Each exercises 12–25 turns, uses the reusable engagement templates, and is graded on artefacts plus how students handle injected "curveball" incidents.

### 2.4 Dated facts are woven into the core, with no refresh mechanism

Section G ("Latest Developments") is entirely news: spec versions, launch dates, foundation memberships. Sections H, I and J also embed dated facts (regulatory deadlines, product ownership, default settings). They rot fast. Within weeks of publication, the two fact-checks found **13 claims that are outdated or need nuance**: 9 in Vol 2 and 4 in the gap doc's own list of corrections.
**Recommendation:**
- Split every turn into an **evergreen core** (principles, patterns, maths) and a **dated annex** (versions, dates, vendors, laws).
- Stamp each annex item with an *as-of* date, a source link, an owner and a *review-by* date.
- Re-verify the annex quarterly. Use [03-errata-and-fact-check.md](03-errata-and-fact-check.md) as the first run and [04-future-topics-2026-2028.md](04-future-topics-2026-2028.md)'s dated calendar as the watch-list.

### 2.5 Evaluation, the FDE's most important skill, is scattered

Evaluation appears in at least six places: Turns 13 (base-model evaluation), 38 (evaluator loops), 49 (RAG evaluation tooling), 63 (simulation and pass^k), 97 (evaluation tools), 104 (testing AI code) and 132 (the science of agent evaluation). No single turn teaches an **evaluation strategy**: what to measure at which layer, how to build and freeze a golden set, how to calibrate judges, and how to gate releases.
**Recommendation:** make evaluation a spine. Add one early "Evaluation Strategy" turn that the others hang off (Template [05-eval-plan.md](projects/templates/05-eval-plan.md) is a starting point), and make every project deliver an eval plan in week 2.

### 2.6 Overlapping turns that should be merged to make room

| Overlap | Turns | Proposal |
|---|---|---|
| Agent identity | 71 (platforms) + 124 (trust fabric) | One turn with a "now" part and a "next" part |
| Learning after deployment | 62 (self-improving) + 118 (continual learning) + 130 (lifelong memory) | One "agents that learn" turn plus a memory turn (the gap register adds memory architectures) |
| Sovereignty | 92 (on-prem/air-gapped) + 134 (sovereign and open-weight) | One turn; keep the "future" material as an annex |
| Serving | 27 (parallelism for serving) + 29 (serving engines) + 31 (prefix caching and disaggregation) | Two turns; parallelism depth goes to an elective |
| Reasoning | 21 (reasoning models) + 121 (reasoning distillation and on-device) | Keep 21 in core; fold 121 into 34 (local inference) and 23 (distillation) |
| Evaluation | 13, 49, 97, 132 | Evaluation spine (see 2.5) |

These merges free about 6–8 turns of budget, roughly what the verified gap topics need.

### 2.7 Section M is large, unprioritised and partly mislabelled

Section M holds 18 "future" topics, the largest section by count, with the fewest pages per topic, no priorities, no promotion criteria and no review dates. Some are no longer future: parts of 128 (governance-as-code), 132 (agent evaluation science) and 134 (sovereign and open-weight) are already everyday practice.
[04-future-topics-2026-2028.md](04-future-topics-2026-2028.md) re-assesses each one (promote, keep, demote or merge) with dated signals and a *promotion trigger*.

### 2.8 Sequencing is textbook order, not job order

The sections run A→M, bottom-up from tokenizers to future topics. An FDE learner should start where engagements start (discovery, data readiness, RAG, agents, evaluation), then learn to harden and operate, and pull model internals in on demand. [05-revised-syllabus-and-learning-path.md](05-revised-syllabus-and-learning-path.md) gives a 16-week track, **Engage → Build → Evaluate → Harden → Operate → Scale**, with the projects placed in it.

---

## 3. Stress-test of the existing gap analysis

<!-- GAPDOC-CRITIQUE -->

---

## 4. What we added

| Deliverable | What it contains |
|---|---|
| [02-gap-register.md](02-gap-register.md) | Every verified missing or thin topic: the gap doc's 23 candidates re-ranked, plus the new gaps this review found. Each has dated evidence, placement, priority and interview Q&As. |
| [03-errata-and-fact-check.md](03-errata-and-fact-check.md) | Corrections to Vol 2 and to the gap doc, with primary sources. |
| [04-future-topics-2026-2028.md](04-future-topics-2026-2028.md) | Horizon scan: a re-assessment of Section M, new future topics, and a dated calendar of known events up to 2028. |
| [05-revised-syllabus-and-learning-path.md](05-revised-syllabus-and-learning-path.md) | Re-tiered priorities, merges, where new turns go, and a 16-week FDE track with the projects placed in it. |
| [projects/](projects/README.md) | 16 real-world FDE engagement briefs, 10 reusable engagement templates, and a coverage matrix. |
