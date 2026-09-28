# Template 09 · Runbook, SLOs and Handover Checklist

Curriculum links: Turns 90 (SLOs and incidents), 94 (failover and DR), 87 (model upgrades), 96 (observability), 111 (handover), 114 (adoption).

## Part A: SLOs

| SLI | SLO | Error budget / 30 days | Alert (burn rate) |
|---|---|---|---|
| Availability (successful responses / valid requests) | 99.5% | ~216 min | 2%/h fast burn, 5%/6h slow burn |
| p95 end-to-end latency | ≤ X s | 5% of requests above X | |
| Quality (sampled human or judge score on production traffic) | ≥ baseline − δ | | Weekly review |
| Safety (policy-violation rate; PII leaks) | ≤ Y per 10k | | Page on any critical leak |
| Cost per successful task | ≤ Z | | Daily anomaly alert |

## Part B: Runbook entries (one per incident type)

For each entry: symptoms → dashboards/queries → first actions → escalation → communication template → recovery verification.

1. Provider outage or elevated error rate → fail over to a pre-evaluated fallback; degrade honestly.
2. Quality regression after a model or prompt change → roll back the pinned version; run the regression suite.
3. Prompt-injection or data-exfiltration suspicion → disable the affected tool or agent identity; preserve traces; notify security.
4. Cost spike or runaway agent loop → hit the budget kill switch; find the loop signature; add a regression test.
5. Retrieval index stale or corrupted → switch to the last good index snapshot; re-index.
6. Permission leak (a user sees a document they should not) → switch to read-only; purge caches; audit the ACL sync.
7. Provider deprecation notice → follow the upgrade playbook: candidate eval → behaviour diff → shadow → canary.

## Part C: Handover checklist (the customer team must pass these drills without you)

- [ ] Named owners for the service, the eval datasets, prompts and config, and cost.
- [ ] Architecture doc and ADRs current; secrets and IaC in the customer's repositories.
- [ ] The customer team ran: a model rollback drill, a failover drill, a deletion request end-to-end, and a red-team regression run.
- [ ] Eval CI gates run on the customer's CI; the dashboards are theirs.
- [ ] Training delivered to users and ops; adoption metrics baseline captured.
- [ ] Open risks and backlog handed over with priorities.
- [ ] Field-to-product notes written: what the product should change so the next deployment is easier.
