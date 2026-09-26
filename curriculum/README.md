# LLM Training Flow Vol. 2: Curriculum Review, Gap Register, Future Topics and FDE Projects

A critical review of the *LLM Training Flow Volume 2* study guide (135 topics, 676 interview Q&As) and of the separate *Coverage Gaps and Fact-Check* document. It adds what is missing for AI engineers and **Forward Deployed Engineers (FDEs)**, now and over the next two years, and supplies 16 real-world projects that show how an FDE actually delivers.
Everything here is **verified as of 26 September 2026**. Dated facts carry source links.

## Start here

| If you want… | Read |
|---|---|
| The verdict on the curriculum and the existing gap analysis | [01 · Curriculum review](01-curriculum-review.md) |
| What is missing, ranked, with evidence and interview Q&As | [02 · Gap register](02-gap-register.md) → [six area files](gap-register/) |
| What in the current material is wrong or outdated | [03 · Errata and fact-check](03-errata-and-fact-check.md) |
| What is coming in 2026–2028, and a dated calendar | [04 · Future topics and horizon scan](04-future-topics-2026-2028.md) |
| The revised syllabus and a 16-week FDE track | [05 · Revised syllabus and learning path](05-revised-syllabus-and-learning-path.md) |
| Real-world FDE projects and engagement templates | [projects/](projects/README.md) |

## Headline findings

1. **The curriculum is mostly accurate and current on the agent-protocol layer.** 41 of 50 checked claims are correct.
   - A few claims are outdated and matter: US bank model-risk guidance SR 11-7 was replaced in April 2026 and now excludes generative AI; AP2's mandate model changed in v0.2; OpenAI is closing its fine-tuning platform.
   - The rest need nuance. There are 14 corrections in total ([03](03-errata-and-fact-check.md)).
2. **Its structure, not its facts, is the main problem for FDEs.**
   - 51% of topics are P1.
   - Model internals get the most pages per topic, while FDE practice gets some of the fewest.
   - Assessment is recall-only, with no projects.
   - Fast-rotting facts are woven into the core ([01](01-curriculum-review.md)).
3. **The existing gap analysis is useful but news-driven.**
   - Its "85–90% coverage" figure has no stated method.
   - It mis-cites two arXiv papers.
   - It misses the FDE delivery layer entirely.
4. **We add 13 must-have (P1) topics.** Six of them are FDE practice or delivery:
   - security review and data-handling terms;
   - systems-of-record integration;
   - deploying inside customer networks;
   - the FDE operating model;
   - legal incident clocks;
   - regulation as obligations → controls.

   In total the register holds 61 verified topics, 54 of which the gap doc missed ([02](02-gap-register.md)).
5. **Most of Section M ("future topics") no longer belongs in one bucket.**
   - Three of its turns are already core practice.
   - Seven merge into existing turns.
   - Only six stay on the watch list.
   - It also gains five new seeds, and there is a verified 35-event calendar to 2028 ([04](04-future-topics-2026-2028.md)).
6. **16 projects make the course job-shaped.** Each is a fictional customer engagement with discovery, an SOW, an architecture and ADRs, an eval plan, a threat model, a compliance mapping, operations, instructor-injected curveballs and a grading rubric. Each comes in a real-engagement version and a course-scaled version ([projects/](projects/README.md)).

## How this was produced

1. Research agents in six areas proposed gaps with dated, primary-source evidence.
2. A second agent per area adversarially re-checked each one: coverage in Vol 2, duplication, evidence and priority.
3. Two separate agents fact-checked Vol 2 and the gap doc.
4. Every project brief was reviewed by a different agent from the one that wrote it: facts re-verified, code sketches run, curriculum maps made honest.

Limitations are listed in [02 §4](02-gap-register.md#4-limitations). Law and product facts change monthly, so re-verify them before each cohort ([05 §4](05-revised-syllabus-and-learning-path.md#4-keeping-it-true-the-evergreen-core-and-a-dated-annex)).
