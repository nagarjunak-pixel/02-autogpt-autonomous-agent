# Template 08 · Customer Security Review Pack (AI vendor questionnaire answers)

In enterprise deployments the security review, not the model, is often the critical path. Prepare this pack **during discovery**, not after the POC.
The customer will usually send a standard questionnaire (SIG Lite/Core, CAIQ, or its own) plus an AI-specific addendum.

## 1. System description (one page)
Purpose, users, data categories, the architecture diagram with trust boundaries, and hosting and regions.

## 2. The AI-specific questions you will be asked (answer every one precisely)

| # | Question | Your answer (fact, not marketing) | Evidence |
|---|---|---|---|
| 1 | Which model providers and models are used, in which regions? Which versions are pinned? | | Gateway config |
| 2 | Is customer data used to train or improve any model (ours or a provider's)? | Default: No | Contract / provider terms / ZDR agreement |
| 3 | What is retained, where, for how long (prompts, outputs, embeddings, traces, caches)? | | Retention config |
| 4 | Which subprocessors see the data? | | Subprocessor list |
| 5 | How is access controlled? Can the assistant reveal documents a user cannot open? | | ACL test results |
| 6 | How do you defend against prompt injection and data exfiltration? | Architecture-level answer, not "we have a filter" | Threat model + red-team report |
| 7 | What actions can the AI take, and what limits apply? Who approves? | | Tool inventory |
| 8 | How are models, packages, MCP servers and skills vetted? Is there an AI-BOM? | | AI-BOM, scan reports |
| 9 | How do you detect and respond to AI incidents? What are the notification SLAs? | | IR runbook |
| 10 | How are PII, PHI and PCI data detected and redacted in inputs, outputs and logs? | | DLP test metrics |
| 11 | How do you evaluate quality and safety before each change? | | Eval gates in CI |
| 12 | Can the deployment run in our VPC, on-prem or air-gapped? With customer-managed keys? | | Deployment options |
| 13 | Which certifications and attestations apply (SOC 2 Type II, ISO 27001, ISO 42001)? | | Reports under NDA |
| 14 | How do you handle model deprecations and provider outages? | | Upgrade policy, failover drill results |
| 15 | What AI-specific regulations have you assessed (EU AI Act, DPDP, state laws)? | | Template 07 |

## 3. Commercial and legal documents to line up early
DPA, zero-data-retention or equivalent provider terms, IP and indemnity clauses, subprocessor notifications, pen-test letter and insurance certificates.

## 4. Anti-patterns
- Answering "No data is stored" when traces or caches hold prompts.
- Claiming prompt injection is "solved" by a classifier.
- Promising that customer data will never leave a region without checking the provider's actual processing locations.
