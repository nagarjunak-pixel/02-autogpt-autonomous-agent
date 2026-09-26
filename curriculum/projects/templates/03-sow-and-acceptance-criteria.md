# Template 03 · Statement of Work (SOW) and Acceptance Criteria

AI work is contracted **in phases**, because uncertainty shrinks only as you learn. Each phase has its own acceptance criteria measured on an agreed, frozen test set.
Curriculum links: Turn 116 (scoping and SOWs), 111 (playbook), 110 (ROI), 91 (FinOps).

## 1. Parties, background and objective
State the objective in one paragraph and repeat the baseline numbers from the Discovery Memo.

## 2. Phases

| Phase | Question it answers | Duration (range) | Exit criteria | Decision owner |
|---|---|---|---|---|
| Discovery | Is this worth doing, and is it feasible? | 1–2 weeks | Discovery memo accepted | Sponsor |
| POC | Does the riskiest assumption hold on real data? | 2–4 weeks | Offline metrics meet POC thresholds on the frozen test set | Sponsor and product owner |
| Pilot | Does it create value in the real workflow with real users? | 4–8 weeks | Online metrics beat the baseline; no unresolved Sev-1/Sev-2 risks | Sponsor, security, legal |
| Production | Can it run reliably, safely and economically at scale? | 4–8 weeks | SLOs met for 2+ weeks; runbooks drilled; handover done | Customer ops owner |

## 3. In scope / out of scope
List both explicitly. Out-of-scope items prevent later disputes.

## 4. Acceptance criteria (make every one measurable)

| ID | Metric | Threshold | Test set / method | Measured by |
|---|---|---|---|---|
| AC-1 | Task accuracy (e.g. field-level F1) | ≥ 0.92 | Frozen set v1.0 (n = 400, stratified), scored by script | Joint |
| AC-2 | Critical-error rate (e.g. wrong amount, wrong person) | ≤ 0.5% | Same set; errors judged by 2 experts | Customer SME |
| AC-3 | Reliability pass^k (k = 3) on agent tasks | ≥ 0.85 | Simulation suite v1 | Vendor |
| AC-4 | p95 latency | ≤ X s | Load test at Y RPS | Vendor |
| AC-5 | Cost per successful task | ≤ ₹/$ Z | FinOps dashboard, 2-week window | Joint |
| AC-6 | Security | No open High findings | Pen test / red-team report | Customer security |

## 5. Assumptions (every failed assumption goes through change control)
- Access to sources A and B within 5 business days of kickoff.
- Customer SMEs are available for 4 h/week of labelling and review.
- Approved model providers and regions: …
- Volumes: …

## 6. Running costs (show these explicitly)
Model and API usage (with ranges), hosting, vector DB, observability, human review hours, and the maintenance FTE.

## 7. Change control, IP and data terms
- Change-request process and turnaround.
- IP ownership of prompts, evaluation sets, fine-tuned weights and code.
- Data processing: DPA, subprocessors, retention, zero-data-retention, whether customer data may be used for training (default: **no**).

## 8. Commercial model
Choose one: fixed price per phase, time and materials, or outcome-based. Outcome-based works only when the baseline and the measurement method are stable (Turn 110, Q578).
