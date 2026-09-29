# Template 04 · Solution Design Document and ADRs

Curriculum links: Turns 112 (architecture documents and ADRs), 117 (system design), 61 (ACI), 100 (gateways).

## Part A: Solution design document (6–12 pages)

1. **Context and goals.** Include explicit non-goals.
2. **Requirements:**
   - Functional
   - Quality targets (taken from the SOW acceptance criteria)
   - Latency, throughput and cost envelope
   - Security, privacy and regulatory requirements
3. **Architecture:**
   - A diagram (Mermaid is fine) showing the **trust boundaries**, i.e. where untrusted content enters and where data leaves to third parties.
   - A component table: component, responsibility, technology, owner.
4. **Data flows.** For every flow: data classification, where it is stored, retention, residency, and which identity is used.
5. **Model strategy.** Model(s) per task, the routing policy, the pinned versions and the fallback chain (Turns 87, 94, 102).
6. **Retrieval and context strategy.** Sources, chunking, permission enforcement, context budget and what is pinned in context (context engineering).
7. **Tools and agency.** Each tool with its scope, side effects, limits enforced inside the tool, and approval requirements (least agency).
8. **Evaluation plan.** Summarise template 05.
9. **Security and privacy.** Summarise template 06 and the compliance mapping (template 07).
10. **Operations.** SLOs, observability, runbooks and DR (template 09).
11. **Cost model.** Cost per task at expected volume, sensitivity analysis and budget guards.
12. **Risks and open questions.** Give each an owner and a date.
13. **Rollout plan.** Shadow → canary → staged → general availability, with rollback triggers.

## Part B: ADR template (one decision per file, numbered, kept in the repo)

```markdown
# ADR-007: <Decision title>
Status: Proposed | Accepted | Superseded by ADR-0xx
Date: YYYY-MM-DD
Deciders: <names/roles>

## Context
What forces are at play (requirements, constraints, evidence from evals, costs)?

## Options considered
1. Option A: pros / cons / cost / risk
2. Option B: …
3. Option C: …

## Decision
We choose … because … (cite eval numbers and cost numbers).

## Consequences
Positive, negative, and what we must now monitor. Also state what would make us revisit this decision.
```

### ADRs that almost every project needs
- Build vs buy vs a platform-native agent (for example Copilot Studio, Agentforce or ServiceNow versus a custom agent)
- Model and provider choice, and the region/residency route
- Retrieval approach (RAG vs long context vs caching; vector store choice)
- Where permissions are enforced (in the index, at query time, or both)
- Workflow vs agent, and the level of autonomy with the approval gates
- Hosting (SaaS API vs VPC vs on-prem/air-gapped)
- Evaluation gating policy (what blocks a release)
