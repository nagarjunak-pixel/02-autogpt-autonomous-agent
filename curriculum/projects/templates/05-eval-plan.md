# Template 05 · Evaluation Plan

Evaluation is the spine of every FDE project. A claim you cannot measure cannot go into an SOW, a demo or a go-live decision.

Curriculum links: Turns 13, 49, 63, 97, 104, 132 (evaluation), 88 (A/B and canaries), 89 (flywheel), 64 (trust calibration).

## 1. What we evaluate, at which layer

| Layer | Question | Example metrics |
|---|---|---|
| Components | Does retrieval, parsing or extraction work? | recall@k, context precision, field-level F1, WER |
| End-to-end task | Is the final answer or action correct? | task success, exact match, execution accuracy (SQL), human-graded quality |
| Reliability | Does it succeed *every* time? | pass^k, variance across seeds and model versions |
| Safety and security | Does it refuse, escalate and resist attacks? | attack success rate, over-refusal rate, PII leakage rate |
| Behaviour under pressure | Does it hold the truth when the user pushes back? | "are you sure?" flip rate, false-premise acceptance rate (sycophancy) |
| Cost and latency | Is it affordable and fast enough? | cost per successful task, p50/p95 latency, tokens per task |
| Human + AI system | Do reviewers catch errors? | seeded-error catch rate, override rate, time per review |

## 2. Datasets
- **Golden set.** Real, de-identified cases, stratified by difficulty, language and segment. Record its size, who labelled it and the inter-annotator agreement. Freeze a version for the SOW acceptance tests.
- **Adversarial set.** Prompt injections (direct and indirect), jailbreaks, out-of-scope requests, and data that crosses permissions.
- **Regression set.** Every confirmed production failure becomes a permanent test case.
- **Synthetic set.** Only if it is validated against real samples, and always labelled as synthetic.
- **Held-out set.** Never used for prompt tuning. It exists to stop you overfitting the golden set.

## 3. Scoring
- Programmatic checks first (schema, exact match, SQL execution, unit tests).
- Use LLM-as-judge only with a written rubric, **calibrated against human labels** (report the agreement rate), and with the judge model pinned.
- Report confidence intervals and the number of repeats; do not quote a single run.

## 4. Gates

| Gate | When | Blocks release if |
|---|---|---|
| PR / CI | Every change to prompts, tools, models or retrieval | Golden-set score drops by more than X, or any critical safety regression |
| Pre-release | Before canary | Acceptance criteria not met; red-team High findings open |
| Canary | 1–5% of traffic | Online guardrail metric breaches the threshold |
| Model upgrade | A provider announces a new version or a deprecation | Behaviour diff not reviewed; golden-set regression |

## 5. Online measurement
Shadow mode, canary, and A/B tests with the sample size fixed in advance. Collect outcome metrics (not only thumbs-up); sample production traffic for human review every week.

## 6. Ownership and cadence
Name who owns each dataset, who reviews the weekly failure triage, and who can approve a gate override.
