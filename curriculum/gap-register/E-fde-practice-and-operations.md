# Gap Register · E · FDE Practice and Operations

> Part of the [Gap Register](../02-gap-register.md). Verified as of 26 September 2026. Every entry was proposed by a research agent, then adversarially re-checked (coverage in Vol 2, evidence, priority) by a second agent; corrections were applied. Priorities: **P1** = most FDE engagements meet it, or it is legally in force for common deployments · **P2** = frequent but situational · **P3** = niche · **Watch** = future. **Law and contract terms change often: re-verify them before teaching, and never treat this as legal advice.**


*11 entries after adversarial verification: 4 P1, 5 P2, 2 P3. Nothing was rejected or merged. FDE-5 (P1 to P2), FDE-6 (P2 to P3) and FDE-10 (P2 to P3) were downgraded. FDE-10's noisy-neighbour and capacity material now sits in FDE-4. The verifier's added item FDE-M1 is renumbered FDE-11.*

### FDE-1 · Enterprise security review, vendor due diligence and AI data-handling terms  — **P1** · THIN · Section L · new turn after Turn 115

*Overlaps gap doc:* none

**What it is.** This is the procurement and third-party risk management (TPRM) workstream that gates almost every enterprise AI deployment. The FDE answers security questionnaires, supplies audit evidence from a trust centre, negotiates data processing agreements (DPAs) and sub-processor terms, and maps retention, zero-data-retention (ZDR) and training-use terms for each feature and data flow.

**Why now.** AI-specific questionnaires are now standard: on 10 Jul 2025 the Cloud Security Alliance (CSA) released its AI Controls Matrix (243 control objectives in 18 domains) with an AI version of its CAIQ (Consensus Assessments Initiative Questionnaire), though mappings to ISO 42001 and the EU AI Act were only announced for later release ([CSA, 10 Jul 2025](https://cloudsecurityalliance.org/blog/2025/07/10/introducing-the-csa-ai-controls-matrix-a-comprehensive-framework-for-trustworthy-ai)). ZDR covers less than buyers assume: Anthropic enables it per organisation; the Files API, code execution, the Model Context Protocol (MCP) connector, Agent Skills and Batch are not ZDR-eligible; some "Covered Models" need 30-day retention; and flagged content may be kept for up to 2 years ([Anthropic docs, accessed Sep 2026](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)). In The New York Times v. OpenAI (NYT v. OpenAI), a May 2025 preservation order covered consumer ChatGPT and API output logs but excluded ChatGPT Enterprise/Edu and ZDR customers, so the contract tier decided legal exposure ([eWeek, 9 Jun 2025](https://www.eweek.com/news/openai-privacy-appeal-new-york-times-copyright/)). On 9 Oct 2025 the court ended the duty to preserve new logs (effective 26 Sep 2025), but logs already preserved and NYT-flagged accounts stay held ([Engadget, Oct 2025](https://www.engadget.com/ai/openai-no-longer-has-to-preserve-all-of-its-chatgpt-data-with-some-exceptions-192422093.html)).

**What Vol 2 has today.** Turn 82 defines SOC 2 Type I vs Type II (Q403) and HIPAA's Business Associate Agreement (BAA, Q405), Turn 80 Q395 defines ISO/IEC 42001 and Turn 111 Q552 lists "security and privacy sign-offs", but nothing covers questionnaires, DPAs, sub-processors, ZDR scope or trust centres.

**What to teach.**
- Run security review as a planned workstream with an owner from week one, not as a gate to wait out.
- Build a reusable security pack: a data-flow diagram with trust boundaries, the sub-processor list, a retention/ZDR matrix, pen-test summaries, and SOC 2 Type II, ISO 27001 and ISO 42001 evidence from the trust centre.
- Answer standard questionnaires from that pack: SIG (Standardized Information Gathering), CSA's CAIQ and its AI version, and sector guides such as the tiered generative-AI vendor questionnaires from FS-ISAC (Financial Services Information Sharing and Analysis Center) ([FS-ISAC, Feb 2024](https://www.fsisac.com/hubfs/Knowledge/AI/FSISAC_GenerativeAI-VendorEvaluation&QualitativeRiskAssessment.pdf)). Point model-provider questions to the provider's own documentation.
- Build one retention row per feature and data flow. Each row records provider retention, ZDR eligibility, your own traces and logs, and the records the customer must keep (FDE-11).
- Treat a new model or tool vendor as a contract change. Under Art. 28 of the EU General Data Protection Regulation (GDPR), a sub-processor needs written authorisation, and the DPA must cover breach notice (Art. 33), deletion and audits ([GDPR Art. 28](https://gdpr-info.eu/art-28-gdpr/)).
- Keep the pilot moving on synthetic or approved data while review items are open, and track each item with an owner and a date.

**Idea to remember.** Security review is a deliverable you plan, not a hurdle you wait out, so ship a reusable security pack in week one.

**Interview questions.**
1. A bank sends a 600-question SIG plus an AI addendum two weeks into the pilot. How do you keep the pilot moving? — Give it an owner and answer from a prepared security pack (trust-centre evidence, data-flow diagram, sub-processor list, retention/ZDR matrix). Meanwhile, run the pilot on synthetic or approved data and track open items with owners and dates.
2. The customer says "we have ZDR, so any feature is fine". What do you check? — ZDR is enabled per organisation, and under ZDR "the API does not block these features; using one is a choice to step outside your ZDR arrangement for that specific data", so files, code execution, the MCP connector, skills and Batch (29-day retention) each need their own row. Also check Covered Models that need 30-day retention (currently Claude Fable 5/5.1 and Mythos 5/5.1), flagged content, legal holds, and whether the route runs through Bedrock or Google Cloud, where the cloud provider is the processor.
3. Why is adding a new model or tool vendor a contract change and not just a config change? — Under GDPR Art. 28 the vendor becomes a sub-processor, which needs written authorisation, and the controller must be told about changes so it can object. A gateway route to a new provider can therefore breach the DPA even when the code works.

### FDE-2 · Integrating agents with systems of record (Salesforce, ServiceNow, SAP, Workday, Microsoft 365, Slack)  — **P1** · THIN · Section J · new turn after Turn 100

*Overlaps gap doc:* #14 covers analytic reads (text-to-SQL over warehouses). This entry adds transactional read/write against software-as-a-service (SaaS) systems of record: quotas, sandboxes, integration identities, vendor API terms and build-vs-extend. #18 touches integration platforms only as a security topic.

**What it is.** Reading from and writing to the customer's transactional SaaS systems of record, such as CRM (customer relationship management), ITSM (IT service management), ERP (enterprise resource planning) and HR platforms. It covers integration identities and on-behalf-of access, per-tenant API quotas, sandboxes with masked data, idempotent write-back, API terms that restrict AI use, and whether to build your own agent or extend the vendor's (Agentforce, Joule, Now Assist, Copilot).

**Why now.** From 29 May 2025, Slack limits conversations.history and conversations.replies to 1 request per minute and 15 objects for commercially distributed non-Marketplace apps (new apps and new installations), while internal customer-built apps keep 50+ requests per minute and 1,000 objects ([Slack changelog, 29 May 2025](https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps)). SharePoint Online meters each app per tenant in resource units, caps app-only search at 25 requests per second, and counts throttled calls against the quota ([Microsoft Learn, updated 10 Aug 2026](https://learn.microsoft.com/en-us/sharepoint/dev/general-development/how-to-avoid-getting-throttled-or-blocked-in-sharepoint-online)). At the same time vendors are shipping their own agent layers: Salesforce's Agentforce 3 added a native MCP client and MuleSoft MCP connectors ([Salesforce, 23 Jun 2025](https://www.salesforce.com/news/press-releases/2025/06/23/agentforce-3-announcement/)), and SAP launched Business Data Cloud with Joule agents ([SAP News, 13 Feb 2025](https://news.sap.com/2025/02/sap-business-data-cloud-databricks-turbocharge-business-ai/)). Fortune wrote that MIT NANDA's research "points to flawed enterprise integration" behind stalled pilots, but the report itself calls the cause a "learning gap", and it rests on interviews, a survey and public deployments ([Fortune, 18 Aug 2025](https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/)).

**What Vol 2 has today.** Only generic mechanisms: Turn 71 Q349's token exchange ("the new token names the user as subject and the agent as actor"), idempotent activities in Turn 99 and Turn 111 Q551's "early security and integration work", with no hits for SAP, Salesforce, ServiceNow, Workday, SharePoint, Slack or write-back.

**What to teach.**
- Settle identity first: a dedicated integration user, or on-behalf-of tokens with least-privilege scopes.
- Budget API quotas per org and per app, and honour `Retry-After`. Use delta queries, batching and lower concurrency, and do not spread load over extra app IDs, because they share the tenant's quota.
- For bulk or continuous extraction from Microsoft 365, use Graph Data Connect or change notifications instead of crawling. Graph Data Connect is not subject to Graph REST throttling ([Microsoft Learn](https://learn.microsoft.com/en-us/graph/throttling)).
- Get a sandbox with masked data and a refresh plan, and agree change windows with the platform owner.
- Make write-back safe to retry. Key idempotent writes by external IDs, enforce business rules in the tool rather than the prompt, and fill the audit fields in the system of record.
- Decide whether to build or extend by comparing where data and permissions live, the vendor's API terms and third-party rate limits, cost, customisation depth and lock-in.

**Idea to remember.** The system of record sets the pace: design around its identity model, quotas, sandbox and API terms first, then decide whose agent layer owns the workflow.

**Interview questions.**
1. An agent must read and update ServiceNow incidents and Salesforce cases. What do you settle before writing code? — Settle identity (an integration user, or on-behalf-of tokens with least privilege), quota budgets, a masked sandbox, idempotent writes keyed by external IDs and change windows with the platform owner. Also check whether the vendor's MCP server or native agent already covers the use case.
2. Your SharePoint indexer for retrieval-augmented generation (RAG) keeps getting 429s. What do you change? — Honour `Retry-After` (Microsoft says "we require using the Retry-After HTTP header"), because throttled calls still count against quota, and switch to delta queries with tokens (1 resource unit each), batching and lower concurrency without adding AppIDs. For bulk or continuous extraction, move to Graph Data Connect or change notifications.
3. Should you build a custom agent or extend the vendor's (Agentforce, Joule, Now Assist)? — Compare where data and permissions live, the vendor's API terms and third-party rate limits (for example, Slack's 2025 limits), cost, customisation and lock-in. A common answer is a hybrid: the vendor agent handles in-app tasks, and your orchestrator works across systems through MCP or A2A (Agent2Agent), with the system of record as the source of truth.

### FDE-3 · Deploying inside the customer's network and cloud: private connectivity, customer-managed keys, proxies and self-hosted execution  — **P1** · THIN · Section I · extend Turn 92

*Overlaps gap doc:* none

**What it is.** The middle ground between public SaaS and air-gapped deployment, which is where most regulated enterprises actually sit. Models are reached over private endpoints, stored data is encrypted with customer-managed keys (CMK), tools work through TLS-inspecting proxies, custom certificate authorities (CAs), mutual TLS (mTLS) and egress allowlists, and tool execution can run on customer infrastructure while the model stays hosted.

**Why now.** Bedrock documents AWS PrivateLink interface endpoints for runtime, agent and Mantle APIs, plus FIPS (US Federal Information Processing Standards) endpoints and endpoint policies ([AWS docs, accessed Sep 2026](https://docs.aws.amazon.com/bedrock/latest/userguide/vpc-interface-endpoints.html)). Azure OpenAI CMK covers training data and fine-tuned models only, needs a Key Vault in the same region and Entra tenant with Soft Delete and "Do Not Purge", and supports only 2048-bit RSA or RSA-HSM (hardware security module) keys; revoking the key blocks fine-tuning and deployment of fine-tuned models, while existing deployments keep serving until deleted ([Microsoft Learn, 26 Nov 2025, updated 5 Jun 2026](https://learn.microsoft.com/en-us/azure/foundry-classic/openai/encrypt-data-at-rest)). Anthropic's first-party `inference_geo` offers only "us" or "global" (US-only costs 1.1x on Claude 4.6+) and workspace geo is currently "us" only, so an EU-resident Claude deployment goes through Bedrock, Google Cloud or Foundry regional endpoints; its self-hosted sandboxes keep tool execution on customer infrastructure while memory stores stay with Anthropic ([Anthropic docs, accessed Sep 2026](https://platform.claude.com/docs/en/manage-claude/data-residency)). Claude Code's "Enterprise network configuration" page lists the proxy, custom-CA and mTLS settings and the required hosts, including telemetry hosts that `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` turns off ([Claude Code docs, accessed Sep 2026](https://code.claude.com/docs/en/corporate-proxy)).

**What Vol 2 has today.** Turn 92 covers residency vs sovereignty (Q454), the "cross-region inference trap" (Q455) and air-gapped updates, and Turn 93 Q462 sets the policy intent ("allowed regions, no public model endpoints, egress denied by default"), but nothing covers PrivateLink, private endpoints, CMK/BYOK (bring your own key), proxies or mTLS.

**What to teach.**
- Reach hosted models over private endpoints, for example Bedrock PrivateLink with an endpoint policy that limits actions and models, or through the customer's gateway.
- Route all other traffic through an allowlisting egress proxy. Handle TLS inspection with custom CAs and mTLS client certificates, and mirror package registries.
- List every host and data type that still leaves: prompts and outputs, memory stores and telemetry. Disable non-essential traffic where you can, and prove the list with a network test.
- Set up and rehearse CMK: the key-vault prerequisites, rotation, revocation, and what revocation does and does not stop.
- Pick the route by residency need, and record which platform is the data processor, because that decides which retention terms apply.
- Run tools and sandboxes (MCP servers, code execution) inside the customer boundary, and send the model only the minimum context.

**Idea to remember.** Most regulated customers need neither public SaaS nor an air gap, but a hosted model reached privately, their own keys on anything stored, and a written list of every host that still leaves.

**Interview questions.**
1. Security says the AI app may have no public internet egress. How do you still use a frontier model? — Call the model through the cloud's private endpoint with an endpoint policy, or through the customer's gateway, and send all other traffic through an allowlisting egress proxy with mirrored package registries. Disable or allowlist telemetry hosts, prove it with a network test, and record which platform is the data processor.
2. What does customer-managed key encryption protect on Azure OpenAI, and what can break? — It covers stored training data and fine-tuned models, not prompts in flight. Revoking the key blocks fine-tuning and deploying fine-tuned models, but existing deployments keep serving until deleted, and setup fails without Soft Delete and "Do Not Purge" or with a vault in another region or tenant.
3. A customer needs EU data residency for Claude. What are the options? — Anthropic's first-party `inference_geo` offers only "us" or "global", so use a Bedrock, Google Cloud or Foundry regional endpoint, where the endpoint sets the region. On Bedrock and Google Cloud the cloud provider is also the data processor, so its data terms apply.

### FDE-7 · The FDE operating model and the field-to-product feedback loop  — **P1** · MISSING · Section L · new turn after Turn 108 (opening Section L, before Turn 109)

*Overlaps gap doc:* none

**What it is.** A forward deployed engineer (FDE) embeds with a customer, ships production code in the customer's environment, and is expected to codify repeatable patterns and send evidence (eval cases, traces, product gaps) back to product and research. Palantir, for example, separates product engineers ("Dev") from forward deployed engineers ("Delta") ([Palantir Blog](https://blog.palantir.com/dev-versus-delta-demystifying-engineering-roles-at-palantir-ad44c2a6e87)).

**Why now.** Monthly FDE job listings rose more than 800% from Jan to Sep 2025, according to the Financial Times ([PYMNTS, 10 Mar 2026](https://www.pymnts.com/news/artificial-intelligence/2026/forward-deployed-engineers-emerge-as-one-of-ais-fastest-growing-jobs/)). In May 2026 Anthropic launched a joint venture with Blackstone, Hellman & Friedman and Goldman Sachs valued at $1.5 billion, and OpenAI launched The Deployment Company, raising $4 billion from 19 investors at a $10 billion valuation; both adopt the Palantir-style FDE model ([TechCrunch, 4 May 2026](https://techcrunch.com/2026/05/04/anthropic-and-openai-are-both-launching-joint-ventures-for-enterprise-ai-services/)). AWS put $1 billion into a new unit that embeds engineers with customers ([CNBC, 30 Jun 2026](https://www.cnbc.com/2026/06/30/aws-amazon-ai-forward-deployed-engineers.html)) ([AWS](https://www.aboutamazon.com/news/aws/aws-1-billion-forward-deployed-ai-engineers)), and Microsoft committed $2.5 billion and 6,000 employees to a new AI implementation unit, Microsoft Frontier Co. ([CNBC, 2 Jul 2026](https://www.cnbc.com/2026/07/02/microsoft-commits-2point5-billion-6000-employees-ai-implementation-unit.html)). Anthropic's FDE posting asks for delivering "MCP servers, sub-agents, and agent skills", and for FDEs to "Identify and codify repeatable deployment patterns and contribute insights back to our Product and Engineering teams" ([Anthropic job posting, accessed Sep 2026](https://job-boards.greenhouse.io/anthropic/jobs/5302966008)).

**What Vol 2 has today.** "Forward deployed" appears only as the Section L heading, and no turn defines the role, the engagement model or the product feedback loop (Turn 89's flywheel concerns the customer's own system and Turn 111 Q553 covers handover), though Vol 1 may introduce the role since several Section L turns are marked THIN.

**What to teach.**
- Define the role against its neighbours. A solutions engineer works mostly pre-sale, a consultant delivers bespoke work and leaves, and an FDE embeds, ships production systems, owns the outcome and feeds the product.
- Give every piece of custom code a fate: productise it, turn it into a template, skill or MCP server, or keep it bespoke with a named owner.
- Track each customer's deltas from the core product.
- Write field-to-product feedback as evidence: a reproducible failing eval case with traces, the customer impact, the workaround, how many customers hit it and the revenue at stake.
- Explain the services-margin trade-off. a16z argues that services-led growth can pay off, citing ServiceNow's gross margin rising from 63.2% at IPO to 79% by 2024 and Workday's from 54.1% to 75% ([a16z, 4 Jun 2025](https://a16z.com/services-led-growth/)). Custom work with no path into the product still traps a company in services.

**Idea to remember.** An FDE ships production code for one customer while harvesting reusable patterns and evidence for all customers; if nothing flows back to the product, you are running a consultancy.

**Interview questions.**
1. How is an FDE different from a solutions engineer or a consultant? — A solutions engineer works mostly pre-sale, and a consultant delivers bespoke work and leaves. An FDE embeds, ships production systems in the customer's environment, owns the outcome, and is also measured on what returns to the product.
2. How do you stop forward-deployed work from turning your company into a services business? — Give every piece of custom code a fate (productise it, make it a template, skill or MCP server, or keep it bespoke with a named owner), and track each customer's deltas from the core product. Send field issues to product as evidence, not anecdotes.
3. What makes good field-to-product feedback? — A reproducible failing eval case with traces, the customer impact, the workaround used and how many other customers hit the same pattern. Once the issue is fixed, the case becomes a regression test.

### FDE-4 · Provider capacity engineering: quota dimensions, service tiers, provisioned throughput and spillover  — **P2** · THIN · Section I · extend Turn 94

*Overlaps gap doc:* none

**What it is.** Treating model capacity as a resource you plan and buy, not only as a retry problem. It covers rate-limit dimensions (requests and input/output tokens per minute, cache-aware limits), acceleration limits, spend caps, per-workspace limits, fair sharing between apps or tenants, and the choice between on-demand, priority, flex/batch and reserved or provisioned capacity with spillover.

**Why now.** Bedrock now offers Reserved, Priority, Standard and Flex tiers; Reserved targets 99.5% uptime on 1- or 3-month terms with a minimum of 100k input and 10k output tokens per minute, is sized on input plus cache-write tokens, and is billed until the reservation is deleted ([AWS docs, accessed Sep 2026](https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html)). Azure OpenAI "spillover" sends traffic from provisioned (PTU, provisioned throughput unit) deployments to standard deployments on 429 errors, long-context 400 errors and 500/503 errors ([Microsoft Learn, 18 Jun 2026](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/spillover-traffic-management)). On most models Anthropic counts only uncached input toward input-token limits and applies acceleration limits to sharp ramps; ordinary 429s carry a `retry-after` header, but the tier spend-cap 429 (`error_code` "enforced_spend_limit_reached") has none and pauses usage until 00:00 UTC on the 1st of the next month unless the tier is raised, while a customer-set spend limit returns HTTP 400 ([Anthropic docs, accessed Sep 2026](https://platform.claude.com/docs/en/api/rate-limits)). Anthropic's Priority Tier commitments are "no longer available for purchase" ([Anthropic docs, accessed Sep 2026](https://platform.claude.com/docs/en/api/service-tiers)).

**What Vol 2 has today.** Turn 94 Q464 retries transient errors "with exponential backoff, jitter and a retry budget" (Q465 adds circuit breakers), Turn 103 Q510 uses semaphores, Turn 35 Q170 notes throughput is "capped by rate limits", and Turn 91 Q451 and Turn 102 Q507 mention "batch tiers" and "capacity limits", but nothing covers provisioned or reserved capacity, spillover, acceleration limits or spend caps.

**What to teach.**
- Classify 429s: rate limits (honour `retry-after`), acceleration limits, quota or spend caps (non-retryable, so alert rather than retry), and capacity.
- Share one retry budget across concurrent workers, so a semaphore pool does not multiply retries.
- Size capacity from load tests with real prompts, measuring peak input/output tokens per minute and the cache hit rate. Request quota increases early and ramp traffic gradually.
- Choose between reserved/provisioned and on-demand capacity with a break-even calculation. Add spillover for bursts, and send non-urgent work to batch or flex.
- Isolate apps and tenants with separate workspaces or keys that have their own spend and rate limits. Add fair queuing and reserved capacity for premium tiers (material moved here from FDE-10).
- Keep a tested fallback model.

**Idea to remember.** Retry with backoff handles short-lived contention but cannot create capacity, so size capacity, buy what must never fail, spill over what may, and alert on 429s that retries cannot clear.

**Interview questions.**
1. You launch to 20,000 users in three weeks. How do you avoid a wall of 429s? — Load-test with real prompts to measure peak token rates and the cache hit rate, request quota increases early, and ramp gradually because of acceleration limits. Decide between reserved capacity and on-demand with spillover, give each app its own workspace or key with limits, and keep a tested fallback model.
2. When is retrying a 429 pointless or harmful? — It is pointless on Anthropic's spend-cap 429, where "Retrying, including the SDKs' automatic retries, fails until access resumes". It is harmful on SharePoint or Graph before `Retry-After` has elapsed, because throttled calls count against usage and prolong throttling, so classify the error, honour `Retry-After`, circuit-break and alert a person.
3. Provisioned or on-demand? — Provisioned capacity suits steady, latency-critical volume at high utilisation, but you pay for idle time, so compute the break-even and add spillover for bursts. Bursty traffic suits on-demand, and work that can wait suits flex or batch.

### FDE-5 · Measuring real impact honestly: controlled productivity measurement versus self-report  — **P2** · THIN · Section L · extend Turn 110 (cross-link Turn 88)

*Overlaps gap doc:* none

**What it is.** Evidence standards for productivity and return-on-investment (ROI) claims. Self-reported time savings and adoption surveys are biased upper bounds, so workforce-level claims need controlled designs, such as staggered (stepped-wedge) rollouts, holdouts and difference-in-differences on task-level outcomes.

**Why now.** In METR's randomised controlled trial (RCT) with 16 experienced open-source developers and 246 tasks, the developers were 19% slower with early-2025 AI tools but afterwards believed they had been 20% faster ([METR, 10 Jul 2025](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)). METR's follow-up (57 developers, 800+ tasks) found a non-significant speed-up of about 18% less task time for returning developers (confidence interval −38% to +9%), and warned that selection effects make this "only very weak evidence" ([METR, 24 Feb 2026](https://metr.org/blog/2026-02-24-uplift-update/)). The 2025 DORA (DevOps Research and Assessment) report found that 90% of respondents use AI and more than 80% perceive productivity gains, yet AI adoption is negatively related to delivery stability ([Google Cloud/DORA, 23 Sep 2025](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)). Careful measurement can still show real gains: +14% issues resolved per hour across 5,179 support agents, and +34% for novices ([NBER, Apr 2023; QJE 2025](https://www.nber.org/papers/w31161)).

**What Vol 2 has today.** Turn 88 teaches randomised A/B tests, sample sizing and the peeking problem (Q434, Q436, Q437), Turn 109 Q543 requires "a measured baseline, a target, a measurement method and guardrail metrics", Turn 110 Q546 explains why hours saved are not always money saved and Turn 101 Q503 lists delivery metrics, but none of them warns that perceived or self-reported gains are unreliable.

**What to teach.**
- Treat surveys and self-reported time savings as a ceiling, not a result.
- Design workforce-level studies with staggered (stepped-wedge) rollouts by team, holdouts or difference-in-differences, and reuse Turn 88's sample sizing.
- Pre-register a primary outcome metric (throughput, cycle time, quality or rework) and guardrail metrics.
- Segment by tenure or experience, because gains can concentrate among novices.
- Watch for selection effects: opt-in pilots and self-selected tasks bias the estimates.
- Convert time into money only where capacity is actually redeployed (Turn 110).

**Idea to remember.** People cannot reliably feel their own AI speed-up, so measure outcomes against a control and treat survey savings as a ceiling.

**Interview questions.**
1. The customer's survey says the assistant saves 5 hours per person per week. Do you put it in the business case? — Only as an upper bound, because METR's 2025 trial found developers believed they were 20% faster while they measured 19% slower. Replace it with task-level measurement against a staggered rollout or holdout, and convert time into money only where capacity is redeployed.
2. Design an impact study for a 300-agent contact centre. — Use a staggered rollout by team with a pre-registered primary metric (resolutions per hour or handle time) and guardrails (customer satisfaction, escalations, compliance errors). Segment by tenure, since Brynjolfsson et al. found +34% for novices but little for experienced agents, and run the study long enough to get past novelty effects.
3. Why did METR call its Feb 2026 follow-up weak evidence? — Because of selection effects: developers increasingly refused to work without AI and withheld the tasks they most wanted AI for, so the sample probably missed the biggest gains. Opt-in pilots and self-selected tasks bias customer impact estimates in the same way.

### FDE-8 · Acceptable-use boundaries, provider usage policies and saying no  — **P2** · THIN · Section L · extend Turn 109

*Overlaps gap doc:* #4 and #5 cover statutes (the global regulation map and companion-AI/minors law). This entry adds the general screening workflow: the provider usage policy, a prohibited-practice screen, statutory scope tests, and a documented path to decline or reshape a request.

**What it is.** Screening a requested use case against the model provider's usage policy, outright legal prohibitions such as EU AI Act Art. 5, and statutory scope tests. The FDE then escalates, declines or reshapes the request through a documented path while keeping the customer relationship.

**Why now.** Anthropic's updated Usage Policy (announced 15 Aug 2025, effective 15 Sep 2025) requires human-in-the-loop oversight and AI disclosure for consumer-facing high-risk uses, such as legal, financial and employment decisions, but not for B2B interactions ([Anthropic, 15 Aug 2025](https://www.anthropic.com/news/usage-policy-update)). EU AI Act Art. 5(1)(f), in force since 2 Feb 2025, bans inferring the emotions of workers or students from biometric data (face, voice, physiology), except for medical or safety reasons ([EU AI Act Art. 5](https://artificialintelligenceact.eu/article/5/)). The Commission's guidelines of 4 Feb 2025 put text sentiment analysis and the inference of customers' emotions outside the ban ([FPF](https://fpf.org/blog/red-lines-under-eu-ai-act-unpacking-the-prohibition-of-emotion-recognition-in-the-workplace-and-education-institutions/); [Lewis Silkin, 17 Feb 2025](https://www.lewissilkin.com/insights/2025/02/17/understanding-the-eu-ai-acts-prohibited-practices-key-workplace-and-advertising-102k011)), yet customers still ask for voice- or video-based emotion scoring of employees. California SB 243 (signed 13 Oct 2025) shows why scope tests matter: it excludes bots used only for customer service, business operations, productivity or technical assistance ([California Legislature, 13 Oct 2025](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB243)).

**What Vol 2 has today.** Turn 79 Q388 lists "Prohibited" as an AI Act risk category and Turn 114 Q568 says to "avoid covert monitoring", but nothing covers provider usage policies, acceptable-use screening or how to decline a request.

**What to teach.**
- Separate the customer's goal from the method they request, and screen the method.
- Check three layers: the provider's usage policy (including its high-risk-use duties), prohibited practices (EU Art. 5 and its exact scope) and statutory scope tests (for example, SB 243's exclusions).
- Read the scope precisely. Biometric emotion inference on workers is banned in the EU, while transcript-only sentiment is not, but it still needs checks against GDPR employee-monitoring rules (Art. 88), works-council rules and the provider's policy.
- Offer one or two compliant alternatives with their trade-offs, in writing, citing the rule.
- Escalate through the agreed channel, involve the customer's legal or risk owner, and record the decision in an architecture decision record (ADR, Turn 112).

**Idea to remember.** Separate the customer's goal from the requested method, screen the method against law, the provider's usage policy and scope tests, and offer a compliant alternative in writing.

**Interview questions.**
1. A customer wants to score sales reps by detecting their emotions on recorded calls. What do you do? — If the system infers reps' emotions from their voice or face, it is prohibited in the EU unless it serves medical or safety reasons. Transcript-only sentiment analysis is outside Art. 5, but you still check GDPR (Art. 88, employee monitoring), works-council rules and the provider's usage policy, then propose a compliant alternative and record the decision in an ADR.
2. What extra duties does Anthropic's 2025 usage policy put on high-risk uses? — For consumer-facing uses in areas such as legal, financial and employment decisions, it requires human-in-the-loop oversight and disclosure that AI is involved. These duties do not apply to B2B interactions.
3. How do you say no without losing the account? — Say it early and in writing, cite the rule, restate the business goal and offer compliant options with their trade-offs. Involve the customer's legal or risk owner, so the decision is theirs rather than your veto.

### FDE-9 · Permission hygiene and oversharing remediation before enterprise knowledge AI  — **P2** · THIN · Section L · extend Turn 115

*Overlaps gap doc:* none

**What it is.** A permission-readiness gate before assistants or RAG are connected to SharePoint, Drive, Confluence and similar systems. The FDE finds over-broad sharing, stale sites and unlabelled sensitive content, restricts discovery for a while, fixes access control lists (ACLs) and sensitivity labels, and verifies with persona-based test queries, because permission-aware retrieval faithfully reproduces broken permissions (P1 inside Copilot or enterprise-search engagements).

**Why now.** Microsoft's "Secure & Governed Data Foundation" blueprint for Copilot (current as of Aug 2026) makes "Remediate oversharing" its first pillar, alongside "Set up guardrails" and "Meet regulations". It also says SharePoint Advanced Management is "included with your Microsoft Copilot license" ([Microsoft Learn, updated 18 Aug 2026](https://learn.microsoft.com/en-us/microsoft-365/copilot/secure-govern-copilot-foundational-deployment-guidance)). SharePoint's guidance says that an app-only Sites.Read.All search "is allowed to query all your SharePoint Online content (including the user's private OneDrive for Business content)" ([Microsoft Learn, updated 10 Aug 2026](https://learn.microsoft.com/en-us/sharepoint/dev/general-development/how-to-avoid-getting-throttled-or-blocked-in-sharepoint-online)). OWASP (Open Worldwide Application Security Project) LLM08:2025 calls for permission-aware vector stores and strict partitioning to prevent cross-context leakage ([OWASP GenAI, 2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)).

**What Vol 2 has today.** Turn 50 Q244 covers post-filtering with permission filters, Turn 115 Q569 lists "access, quality, ownership, legal usability, sensitivity" and Turn 78 covers data-loss prevention (DLP), but all of them assume the source ACLs are correct (no hits for oversharing, ACL, sensitivity label or Purview).

**What to teach.**
- Run a permission-readiness check: broadly shared sites and links, stale or ownerless sites, sensitivity-label coverage, and the index's ACL-sync latency.
- Restrict discovery of high-risk sites straight away. Then fix permissions with the site owners, and apply sensitivity labels and DLP.
- Add persona-based leakage tests to the eval suite (for example, "can a contractor find board minutes?"), with go/no-go thresholds agreed with the data owners.
- Avoid app-only indexers with tenant-wide read access unless per-user ACLs are stored and enforced at query time with low sync lag. Prefer delegated access or ACL-synced indexing with least privilege.

**Idea to remember.** Permission-aware retrieval is only as safe as the permissions it copies, so fix who can see what before you make everything searchable in plain language.

**Interview questions.**
1. Retrieval enforces ACLs, yet the assistant surfaces salary spreadsheets to interns. Why, and what now? — The ACLs themselves are over-broad (org-wide links, "everyone" groups, stale sites), and the assistant only made the files findable. Restrict discovery of high-risk sites now, fix permissions with the owners, apply labels and DLP, and add persona-based leakage tests.
2. Why is an app-only indexer with Sites.Read.All risky? — It can read all content, including private OneDrive files. Unless the index stores and enforces per-user ACLs at query time with low sync lag, it becomes a single point of oversharing.
3. What goes into a permission-readiness check? — Counts of broadly shared sites and links, stale or ownerless sites, label coverage, the index's ACL-sync latency and red-team queries run as different personas, with go/no-go thresholds agreed with the data owners.

### FDE-11 · Records retention, supervision and eDiscovery for AI interactions and agent actions (the opposite of ZDR)  — **P2** · THIN · Section H · extend Turn 82

*Overlaps gap doc:* none

**What it is.** Designing AI systems so that prompts, outputs, model versions and agent actions are kept, searchable and holdable wherever law or regulation requires it. This covers books-and-records and communications supervision, litigation and eDiscovery (electronic discovery) holds, and defensible deletion, all reconciled with zero retention at the model vendor.

**Why now.** In Regulatory Notice 24-09, FINRA (the US Financial Industry Regulatory Authority) said its rules are technology-neutral and "continue to apply when member firms use AI", including Rule 2210 for chatbot and AI-created communications ([FINRA, 27 Jun 2024](https://www.finra.org/rules-guidance/notices/24-09)). FINRA's 2026 oversight report suggests "storing prompt and output logs for accountability and troubleshooting; tracking which model version was used and when", and tracking "agent actions and decisions" ([FINRA, Dec 2025](https://www.finra.org/rules-guidance/guidance/reports/2026-finra-annual-regulatory-oversight-report/gen-ai)). Microsoft Purview applies retention policies to interactions in Microsoft 365 Copilot, Copilot Studio, Foundry, Entra-registered AI apps and ChatGPT Enterprise; that content is eDiscoverable, and a Litigation Hold or eDiscovery hold suspends its deletion ([Microsoft Learn, 23 Sep 2025, updated 25 Jun 2026](https://learn.microsoft.com/en-us/purview/retention-policies-copilot)). The NYT v. OpenAI preservation order (May 2025, lifted for new logs on 9 Oct 2025) showed that litigation holds can override deletion promises ([Engadget, Oct 2025](https://www.engadget.com/ai/openai-no-longer-has-to-preserve-all-of-its-chatgpt-data-with-some-exceptions-192422093.html)).

**What Vol 2 has today.** Turn 52 covers deletion propagation (Q254: "caches, memories, logs ... and backups hold copies"; Q257: deletion logs), Turn 74 mentions "immutable audit logs" and Turn 82 Q406 covers model-risk inventory and documentation, but nothing covers legally required retention, supervision or holds for AI communications (no hits for eDiscovery, records management, legal hold, FINRA or 17a-4).

**What to teach.**
- Work with compliance to map which AI interactions are regulated records (client communications, advice, agent actions), and set their retention periods.
- Keep ZDR at the provider, and write the regulated record from the gateway to an archive the customer controls. The record holds the prompt, the response, the model and prompt versions, the sources and the agent's actions.
- Make sure that archive supports supervision workflows, legal holds and eDiscovery search.
- Keep as little data as possible everywhere else, and make deletion defensible: holds suspend deletion, and retention jobs take time to run.
- Put the must-keep rows next to the must-delete rows in the same retention matrix (link to FDE-1).

**Idea to remember.** Zero retention at the model provider and full retention in the customer's archive do not conflict: keep the regulated record in a system the customer controls, and keep as little as possible anywhere else.

**Interview questions.**
1. A broker-dealer wants ZDR with the model provider but must supervise and archive client-facing chatbot messages. How do you design it? — Keep ZDR at the provider, and write the regulated record (prompt, response, model/prompt version, sources, agent actions) to the firm's archive through the gateway, with retention and supervision set by compliance. Minimise everything else, and make sure the archive supports legal holds and eDiscovery search.
2. Why can a 1-day delete policy on Copilot interactions take much longer, or never happen? — Purview runs on timer jobs every 1–7 days, so a 1-day delete-only policy can take about 16 days to remove content permanently. Any Litigation Hold, eDiscovery hold or other retain policy on the mailbox suspends permanent deletion.

### FDE-6 · Commercial models for AI features: seats, usage credits and outcome-based pricing  — **P3** · THIN · Section L · extend Turn 116

*Overlaps gap doc:* none

**What it is.** How AI features are billed: per seat, by metered usage or credits, per action, or per outcome (for example, per resolution). For an FDE the relevant part is narrow: defining the billable unit, knowing the cost per billable outcome and preventing bill shock.

**Why now.** Salesforce moved Agentforce from $2 per conversation to Flex Credits at $0.10 per action ($500 per 100,000 credits) ([Salesforce, 15 May 2025](https://www.salesforce.com/news/press-releases/2025/05/15/agentforce-flexible-pricing-news/)). Intercom's Fin charges $0.99 per resolution, defined as "No further help is requested after Fin's last answer" ([Intercom Fin, accessed Sep 2026](https://fin.ai/pricing)). GitHub introduced Copilot premium-request allowances with a $0 default spending budget ([GitHub, 18 Jun 2025](https://github.blog/changelog/2025-06-18-update-to-github-copilot-consumptive-billing-experience/)). Cursor apologised and refunded unexpected charges from 16 Jun to 4 Jul 2025, after it moved Pro from request-based to usage-based pricing without clear communication ([Cursor, 4 Jul 2025](https://cursor.com/blog/june-2025-pricing)).

**What Vol 2 has today.** Turn 91 Q452 names "Cost per successful outcome" as the north-star cost metric, Q453 covers budgets and per-run ceilings, and Turn 116 Q578 says outcome-based pricing needs "a stable, agreed baseline and measurement method", but Vol 2 does not cover packaging choices (seats vs credits vs per-resolution) or how to communicate billing changes.

**What to teach.**
- Define the billable unit precisely and auditably (what counts as a "resolution" or an "action"), and watch for gaming of that definition.
- Measure the cost per billable outcome (Turn 91), and protect margin by routing easy cases to cheaper models and capping tokens and reasoning effort per conversation.
- Prevent bill shock with visible meters, caps, alerts and advance notice of billing changes.
- Write re-pricing triggers into the contract.

**Idea to remember.** Price on what the customer values and cost on what you consume, and never surprise a customer with a variable bill.

**Interview questions.**
1. Seat, usage or outcome pricing for an AI support agent? — Seats fit predictable employee-facing use, and usage or credits fit variable automation but shift risk to the buyer. Per-outcome pricing aligns with value but needs a precise, auditable definition, and many vendors mix models, such as Salesforce's per-user plans plus per-action credits.
2. What did Cursor's mid-2025 pricing episode teach? — Usage-based billing can make sense for long agentic tasks, but it needs clear communication, visible meters, caps and alerts. Cursor had to apologise and refund unexpected charges.
3. How do you protect margin under per-resolution pricing? — Measure the cost per resolved outcome, route easy cases to cheaper models, and cap tokens and reasoning effort. Watch for gaming of the resolution definition, and write re-pricing triggers into the contract.

### FDE-10 · Multi-tenant architecture for AI features: isolation and per-tenant configuration  — **P3** · THIN · Section J · extend Turn 100 (cross-link Turn 74)

*Overlaps gap doc:* none

**What it is.** A single checklist that keeps tenants of a SaaS AI feature from ever sharing context. Every stateful component needs a tenant key, including vector stores, semantic and provider prompt caches, memories, traces, fine-tunes and adapters, tool credentials and eval sets, and per-tenant prompts and configuration are layered and versioned (noisy-neighbour capacity controls are now in FDE-4).

**Why now.** Anthropic isolates prompt caches per workspace on the Claude API, Claude Platform on AWS and Foundry, but only per organisation on Bedrock and Google Cloud ([Anthropic docs, accessed Sep 2026](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)). A Sep–Oct 2024 audit of 17 API providers found global cross-user prompt-cache sharing at 7 of them. The risk is a timing side channel: a cache hit reveals that someone has already sent the same prefix ([Gu et al., arXiv, Feb 2025](https://arxiv.org/abs/2502.07776)). OWASP LLM08:2025 names context leakage in shared vector databases as a top risk ([OWASP GenAI, 2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)).

**What Vol 2 has today.** Vol 2 covers the pieces separately (Turn 50 Q246 vector-database multi-tenancy options, Turn 74 "isolate data by user and tenant", Turn 91 Q450 "Tag every call with tenant", Turn 100 Q495 virtual keys "with their own budgets, limits and allowed models", Turn 88 Q438 cache keying by experiment arm, Turn 25 per-tenant adapters, Turn 67 multi-tenant A2A) but has no single checklist and nothing on how far provider caches are isolated.

**What to teach.**
- List every stateful component and check its tenant key: vector collections, semantic caches, provider prompt caches (workspace vs organisation scope), memories, traces and logs, adapters and fine-tunes, tool credentials, and eval sets built from production traffic.
- Know each platform's cache isolation scope, and give tenants separate workspaces or organisations where isolation matters.
- Layer configuration (global settings first, then tenant overrides) as versioned data, and run per-tenant eval subsets and canary releases before rollout.
- Add cross-tenant leakage tests to the eval suite.

**Idea to remember.** Every stateful component of an AI stack needs a tenant key, so check each one, because the model will reuse whatever context it is given.

**Interview questions.**
1. List the places cross-tenant leakage can occur in an LLM SaaS. — Vector collections without enforced tenant filters, semantic caches keyed without the tenant, shared memories, traces and logs, adapters trained on mixed data, shared tool credentials, and eval sets built from production traffic. A provider prompt cache does not hand one tenant's content to another, but a shared cache can leak through timing.
2. How is Claude's prompt cache isolated across platforms? — Per workspace on the Claude API, Claude Platform on AWS and Foundry, and per organisation on Bedrock and Google Cloud. Tenants that share a Bedrock organisation therefore share a cache scope.
3. How do you manage tenant-specific prompts safely? — Layer the configuration (global settings, then tenant overrides) as versioned data, and run per-tenant eval subsets and canaries on every change. Compare behaviour per tenant before rollout, so one customer's fix does not break another customer.

#### Disagreements with Vol 2 / gap doc (FDE)

- **Gap doc TL;DR ("85–90% of what an AI engineer or FDE needs").** All 23 gap-doc candidates are frontier-technical or regulatory. None covers the enterprise-delivery layer where FDE time goes: security review and data terms, systems-of-record integration, private networking and keys, and provider capacity. Vol 2's own Q539 says projects fail from "no data access ... or no adoption — rarely because the model was too weak", and the fact-check found no method behind the coverage figure. *Change:* drop or lower the FDE coverage estimate for Sections I and L. Add FDE-1, FDE-2, FDE-3 and FDE-7 as P1 ahead of the Watch items (#21–23).
- **Vol 2 Turn 94 Q464 and Turn 103 Q510 (retrying 429s).** These answers are incomplete, not wrong. Backoff with jitter and a retry budget is endorsed practice when no `Retry-After` is given. The answers leave out two things. First, `Retry-After` takes precedence. Second, some 429s cannot be retried: Anthropic's spend-cap 429 has no `retry-after`, and "Retrying, including the SDKs' automatic retries, fails until access resumes" ([Anthropic docs, accessed Sep 2026](https://platform.claude.com/docs/en/api/rate-limits)). For SharePoint, Microsoft says "we require using the Retry-After HTTP header" ([Microsoft Learn](https://learn.microsoft.com/en-us/sharepoint/dev/general-development/how-to-avoid-getting-throttled-or-blocked-in-sharepoint-online)). *Change:* honour `Retry-After` first and fall back to backoff with jitter. Classify non-retryable 429s (the spend cap via `error_code`, quota exhaustion) and alert on them instead of retrying. Share one retry budget across concurrent workers, and link to FDE-4.
- **Gap doc #5 (companion-AI and minors) rated P1.** This is overstated for an enterprise FDE audience. SB 243 excludes bots "used only for customer service, a business' operational purposes, productivity and analysis related to source information, internal research, or technical assistance" ([California Legislature, 13 Oct 2025](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB243)). *Change:* rate it P2, or P1 only for consumer companion or social products. Teach the scope test as part of the acceptable-use screen (FDE-8).
- **Vol 2 Turn 110 (and Turn 101 Q503) on ROI.** The guidance asks for a measured baseline but never warns that perceived speed-ups are unreliable. METR measured developers as 19% slower while they believed they were 20% faster ([METR, 10 Jul 2025](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)). DORA found that more than 80% perceive gains, while AI adoption is negatively related to delivery stability ([Google Cloud/DORA, 23 Sep 2025](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)). *Change:* in Turn 110, treat surveys as upper bounds. Require a controlled design (staggered rollout, holdout or difference-in-differences, reusing Turn 88) for any productivity number in a business case (FDE-5).
- **Vol 2 Turn 102 Q506 ("Direct API or cloud platform?").** The answer lists features, contracts and regional hosting. It misses that the data processor changes with the route. Anthropic's docs say "On Amazon Bedrock and Google Cloud's Agent Platform, the cloud provider is the data processor". On those platforms `inference_geo` does not apply, and prompt-cache isolation is per organisation ([Anthropic docs, accessed Sep 2026](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)). *Change:* add three questions to the route checklist: who is the processor, which retention/ZDR/BAA terms apply, and which residency control applies.
- **Vol 2 Turn 111 Q553 (handover).** The answer defines handover only through people, skills and processes. It omits the account and contract items that break production after the FDE leaves:
  - who owns the provider organisation and workspaces
  - the rate-limit tier and reservations
  - ZDR/BAA enablement ("ZDR is enabled per organization; each new organization requires ZDR to be enabled separately by your account team")
  - key rotation
  - sub-processor notices
  - the model-retirement calendar

  *Change:* add an account-and-contract handover checklist to Turn 111, cross-linked to Turn 87.
- **Vol 2 Turn 90 (incident response).** Incident response here faces inward only: service-level objectives (SLOs), error budgets and on-call levers. It has nothing on customer-facing communication or contractual and legal notice duties. GDPR Art. 33(2) requires a processor to notify the controller "without undue delay", and the controller then has a 72-hour clock ([GDPR Art. 33](https://gdpr-info.eu/art-33-gdpr/)). *Change:* extend Turn 90 with customer incident communications, linked to FDE-1. Cover the status page, notice timelines from the DPA and the service-level agreement (SLA), and the post-incident report.
