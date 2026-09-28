# Template 01 · Discovery Questionnaire and Qualification Scorecard

Use this template in the first one or two weeks of every project, before anyone writes a prompt.
Output: a one- or two-page **Discovery Memo** that ends with a qualification decision: **Go**, **Go with conditions** or **No-go**.

Curriculum links: Turns 109 (discovery), 110 (ROI), 115 (data readiness), 111 (POC→pilot→prod).

---

## 1. Process map (fill in with the people who do the work, not only with their managers)

| Step | Who does it | System(s) used | Volume / week | Time per item | Error / rework rate | Pain quote (verbatim) |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |

**Baseline** (you must measure it; an estimate you were told does not count): cycle time, cost per item, error rate and backlog.
Record how you measured each number and on which dates.

## 2. Questions to ask

### Business owner / sponsor
1. What decision or outcome will change if this works? Who signs off that it worked?
2. What happens today when the process fails? What does one failure cost?
3. What is the deadline, and what drives it? (A regulator, a budget cycle, a board meeting?)
4. Who loses something if this succeeds? (Headcount, control, a vendor contract)
5. What would make you stop this project?

### Users (the people doing the work)
1. Walk me through the last three cases you handled. Where did you get stuck?
2. Which cases are easy, and which are hard? What makes a case hard?
3. What do you double-check today, and why?
4. If a tool drafted this for you, what would you need to see before trusting it?

### IT, data and security
1. Where does the data live? Who owns each source? How do we get read access, and how long does that take?
2. Which identity provider is used? Can we act *on behalf of* users (OBO) or only with a service account?
3. Is outbound traffic restricted? Which model providers and regions are approved? Is zero-data-retention required?
4. What is the change-management process for production (CAB, release windows, pen-test requirements)?
5. Which security questionnaire will we have to complete (SIG, CAIQ, the customer's own AI questionnaire)?

### Legal, risk and compliance
1. Which laws apply to this data and this decision? (DPDP/GDPR, sector rules, AI-specific laws such as the EU AI Act, US state laws, India's IT Rules)
2. Does the system make or influence decisions about people (hiring, credit, claims, health)? If it does, you are probably in high-risk or automated-decision territory.
3. Are there contractual limits on the data (licences, client confidentiality, ethical walls)?
4. Who must approve the go-live?

## 3. Qualification scorecard

Score each criterion from 1 to 5 and agree the weights with the sponsor **before** you score.

| Criterion | Weight | Score | Evidence |
|---|---|---|---|
| Value (size of the measured pain) | 25% | | |
| Feasibility (data exists and is accessible; the task is within model capability on real samples) | 20% | | |
| Measurability (an agreed correct answer exists; experts agree with each other) | 20% | | |
| Time to value | 10% | | |
| Risk (legal, safety, reputational); a higher score means lower risk | 15% | | |
| Adoption (users want it; the workflow can change) | 10% | | |

**Lowest rung that works** (Turn 109): rules → classic ML → single LLM call → LLM workflow → agent.
Write down which rung you chose and why the lower rungs are not enough.

## 4. Discovery memo outline (at most two pages)

1. Problem, in the customer's words and with baseline numbers
2. Proposed scope and non-goals
3. Riskiest assumption, and how the POC will test it
4. Data readiness summary (use Template 02)
5. Success metric, target and guardrail metrics
6. Known constraints (regulatory, infrastructure, security)
7. Decision (Go, Go with conditions or No-go) with the conditions spelled out

## Common mistakes
- Treating the sponsor's estimate as the baseline.
- Skipping the users and interviewing only managers.
- Choosing an agent when a workflow would do.
- Leaving security and legal until the pilot. This is how projects get stuck in "pilot purgatory".
