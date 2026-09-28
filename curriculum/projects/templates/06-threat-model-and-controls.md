# Template 06 · Threat Model and Controls for LLM and Agent Systems

Curriculum links: Turns 73 (OWASP Agentic Top 10), 74 (OWASP LLM Top 10), 75 (red-teaming), 76 (poisoning), 77 (supply chain), 78 (DLP), 86 (sandboxes), 66 and 71 (auth and identity). See also the gap register entries on prompt-injection-resistant architecture, agentic-browser security and AI-enabled cyber defence.

## 1. System inventory
List the models, prompts, tools (with side effects), data sources, memories, MCP servers, skills and plugins, third-party APIs, identities (user, agent, service) and where secrets live.

## 2. Lethal-trifecta check (run it for every agent context)

| Agent / context | Private data access? | Untrusted content exposure? | External communication / side-effect channel? | All three? → redesign |
|---|---|---|---|---|
| Inbox triage agent | Yes | Yes (inbound email) | Yes (send email) | **Yes: split the design** (see below) |

If any single context has all three, choose one of these patterns:
- **Dual-LLM / quarantine.** A privileged planner never sees untrusted text; a quarantined reader parses it and returns only typed values.
- **Plan-then-execute with capability control (CaMeL-style).** The plan is fixed from the trusted request; data-flow policies decide what untrusted values may reach which tools.
- **Remove a leg.** Remove the external channel, require human approval for sends, or restrict recipients to an allow-list.

## 3. Threat table (STRIDE-style, adapted for AI)

| Threat | Entry point | Impact | Likelihood | Controls (prevent / detect / respond) | Residual risk | Test |
|---|---|---|---|---|---|---|
| Indirect prompt injection via a retrieved document | RAG corpus | Data exfiltration, wrong action | High | Quarantined reader; tool allow-list; output URL filtering; approval for sends | Medium | Red-team suite RT-03 |
| Cross-tenant / cross-matter data leakage | Index, caches, memory | Confidentiality breach | Medium | ACL filtering at query time; per-tenant cache keys; tests that seed canary documents | Low | Canary-doc test |
| Tool misuse / excessive agency | Tool layer | Financial or operational loss | Medium | Limits enforced inside tools; idempotency keys; human approval above a threshold | Low | Abuse cases |
| Memory poisoning | Long-term memory | Persistent wrong behaviour | Medium | Write controls; provenance; review of memory writes; TTLs | Medium | Poisoning test |
| Supply-chain compromise (package, model, MCP server, skill) | Build and runtime | Full compromise | Low–Med | Pin by hash; scan; AI-BOM; internal registry; egress control | Low | Dependency audit |
| Credential / session theft by a browser or computer-use agent | Browser profile | Account takeover | Medium | Isolated profiles; short-lived credentials; domain allow-lists; confirmation for sensitive steps | Medium | Red-team RT-07 |
| Denial of wallet / runaway loops | Agent loop | Cost blow-up | Medium | Per-run budgets; loop detection; rate limits; anomaly alerts | Low | Chaos test |
| Sensitive data in logs and traces | Observability | Privacy breach | High | Redaction before logging; access control on traces; retention limits | Low | Log audit |

## 4. Red-team plan
Scope, attack library (direct, indirect and multi-turn attacks, tool abuse, data exfiltration, jailbreaks), severity rubric, and a rule that every successful attack becomes a regression test.

## 5. Kill switches and incident levers
Model rollback, tool disable flags, per-agent identity revocation, read-only mode and traffic shedding. **Each one must be drilled at least once before go-live.**
