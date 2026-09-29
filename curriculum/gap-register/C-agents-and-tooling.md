# Gap Register · C · Agents, Protocols and Tooling

> Part of the [Gap Register](../02-gap-register.md). Verified as of 26 September 2026. Every entry was proposed by a research agent, then adversarially re-checked (coverage in Vol 2, evidence, priority) by a second agent; corrections were applied. Priorities: **P1** = most FDE engagements meet it, or it is legally in force for common deployments · **P2** = frequent but situational · **P3** = niche · **Watch** = future.


Ten entries after verification: 1 P1, 8 P2 and 1 Watch. The verifier merged three items into existing gap-doc items: AGT-4 into #2, AGT-5 into #13 and AGT-9 into #18. Each of these three is written here as a full "deepened" entry that replaces its gap-doc item. The verifier rejected none and added no missed items.

---

### AGT-1 · Agent harness engineering with vendor agent SDKs (Claude Agent SDK, OpenAI Agents SDK, Google ADK, Microsoft Agent Framework)  — **P1** · THIN · Section J · extend Turn 95 (rewrite around harness primitives rather than framework brands)

*Overlaps gap doc:* #7: the gap doc mentions a harness only for compaction and memory. This entry covers the whole harness contract: permissions, hooks, stop conditions, resumable state and version churn.

**What it is.** The harness is the runtime around the model: the tool loop, permission checks and approval callbacks, lifecycle hooks, sessions you can resume or fork, compaction, subagents, hard stop conditions (turns, budget, stalls) and tracing. Since 2025 the model vendors have shipped their own harnesses as software development kits (SDKs) and hosted services, so choosing and configuring one is now core agent engineering.

**Why now.** Anthropic renamed the Claude Code SDK to the Claude Agent SDK ([PyPI, first release 28 Sep 2025](https://pypi.org/pypi/claude-agent-sdk/json)); it exposes hooks, permissions, resumable and forkable sessions, and `maxTurns`/`maxBudgetUsd` stops that end in `error_max_turns` and `error_max_budget_usd` results ([Anthropic docs, accessed 26 Sep 2026](https://code.claude.com/docs/en/agent-sdk/typescript)). Rival SDKs ship the same primitives:
- The OpenAI Agents SDK pauses a run when a tool has `needs_approval` set, and serialises `RunState` so the run can resume after a human decision ([OpenAI Agents SDK docs, accessed 26 Sep 2026](https://github.com/openai/openai-agents-python/blob/main/docs/human_in_the_loop.md)).
- Google's Agent Development Kit (ADK) Go 1.0 added `RequireConfirmation` human-in-the-loop and native OpenTelemetry ([Google Developers Blog, 31 Mar 2026](https://developers.googleblog.com/adk-go-10-arrives/)).
- Microsoft Agent Framework (MAF) 1.0 shipped stable middleware, checkpointing and human-in-the-loop in early April 2026 ([Microsoft, Apr 2026](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)). Its Agent Harness later reached general availability (GA) ([InfoQ, 3 Aug 2026](https://www.infoq.com/news/2026/08/agent-framework-harness-ga/)).

Both model-vendor SDKs are still 0.x: openai-agents is at 0.22.3 ([PyPI, 17 Sep 2026](https://pypi.org/pypi/openai-agents/json)) and claude-agent-sdk at 0.2.160, npm 0.3.283 ([PyPI, 25 Sep 2026](https://pypi.org/pypi/claude-agent-sdk/json)). By contrast google-adk is at 2.10.0 ([PyPI, 25 Sep 2026](https://pypi.org/pypi/google-adk/json)) and agent-framework at 1.19.0 ([PyPI, 18 Sep 2026](https://pypi.org/pypi/agent-framework/json)). Adoption is already large: @anthropic-ai/claude-agent-sdk had 47,719,824 npm downloads from 26 Aug to 24 Sep 2026, CI installs included ([npm registry, 24 Sep 2026](https://api.npmjs.org/downloads/point/2026-08-26:2026-09-24/@anthropic-ai/claude-agent-sdk)).

**What Vol 2 has today.** Turn 95 stays at the level of framework brands: Q469 lists "State and checkpoints, orchestration, human-in-the-loop…", and Q472 says to "treat the framework as an adapter". Budgets and approvals appear only as concepts in Turns 57 (Q280), 58, 59 and 91 (Q453). Searches for the following found nothing:
- "harness" (other than in the evaluation-harness sense);
- Claude Agent SDK;
- `canUseTool`;
- max turns;
- `RunState`;
- ADK.

**What to teach.**
- The harness contract, as a comparison table across the Claude Agent SDK, OpenAI Agents SDK, ADK, MAF and LangGraph. Rows: tool loop, permission callback, hooks, sessions (resume/fork), compaction, subagents, stop conditions and tracing.
- Per-run stops enforced in the harness: max turns, a max budget (such as `maxBudgetUsd`), and stall and reset counters. Handle the error result subtypes as normal outcomes, and keep cross-run budgets per team or tenant in the gateway as the backstop.
- A pausing approval:
  1. Mark the tool as needing approval.
  2. Catch the interruption.
  3. Serialise the run state to durable storage.
  4. Resume from that same state after the decision.

  For multi-day waits, use a durable workflow (Turn 99).
- Enforcement in code rather than in the prompt: permission callbacks and pre-tool hooks (for example `canUseTool` and `PreToolUse`) that deny or rewrite dangerous calls.
- Version churn: pin exact SDK versions, wrap the SDK in a thin adapter, and keep tools, prompts and evals outside it.
- The security-review answer: be able to show where permissions, approvals, budgets and kill switches are enforced in the harness.

**Idea to remember.** Choose the harness before the framework: its permission hooks, stop conditions and resumable state decide safety and cost more than the orchestration style does.

**Interview questions.**
1. What is an agent harness, and what must it provide in production? — It is the runtime around the model: the tool loop, permission checks and approval callbacks, lifecycle hooks, resumable or forkable sessions, compaction, subagents, hard stops (turns, dollars, stalls) and traces. The model reasons; the harness enforces.
2. How do you implement an approval that may take two days? — Mark the tool as needing approval, let the run pause and return its interruptions, and serialise the run state to durable storage (for example `RunState.to_json` in the OpenAI Agents SDK). Resume from that same state after the decision rather than starting a new user turn, and wrap multi-day waits in a durable workflow.
3. Which runaway controls belong in the harness, and which in the gateway? — The harness holds per-run limits: max turns, a max budget (the Claude Agent SDK's `maxBudgetUsd` ends in `error_max_budget_usd`), stall and reset counters, and `PreToolUse` hooks that deny dangerous calls. The gateway holds cross-run budgets per team or tenant as the backstop.

---

### AGT-2 · Multi-agent orchestration patterns (agents-as-tools, handoffs, sequential/concurrent, group chat, magentic) and when not to use them  — **P2** · THIN · Section F · extend Turn 55 (retitle: Subagents, Handoffs and Multi-Agent Orchestration)

*Overlaps gap doc:* none. This entry corrects the gap doc's "already covered: Subagents: Turn 55", which is only half right.

**What it is.** The design choice between several patterns:
- one agent with tools;
- a manager that calls specialist agents as tools;
- routing handoffs;
- fixed sequential or concurrent workflows;
- group chat;
- manager-led dynamic planning ("magentic").

It includes the evidence that multi-agent systems cost many more tokens and fail in ways specific to coordination.

**Why now.** MAF's sequential, concurrent, group-chat, handoff and magentic patterns reached 1.0 in Python and .NET, with the magentic example guarded by `max_round_count=10`, `max_stall_count=3` and `max_reset_count=2` ([Microsoft, 8 Jul 2026](https://devblogs.microsoft.com/agent-framework/agent-frameworks-orchestration-patterns-reach-1-0/)). The OpenAI Agents SDK separates agents-as-tools, where the manager keeps the answer, from handoffs, where the specialist takes over the turn ([OpenAI Agents SDK docs, accessed 26 Sep 2026](https://openai.github.io/openai-agents-python/multi_agent/)).

Anthropic's research system used a Claude Opus 4 lead with Sonnet 4 subagents ([Anthropic, 13 Jun 2025](https://www.anthropic.com/engineering/multi-agent-research-system)):
- It beat single-agent Opus 4 by 90.2% on an internal research eval.
- It used about 15× the tokens of chat.
- On BrowseComp, token usage explained 80% of the variance; tokens, tool calls and model choice together explained 95%.

A day earlier, Cognition argued the opposite case ([Cognition, 12 Jun 2025](https://cognition.com/blog/dont-build-multi-agents)). The MAST taxonomy gives failures a name: 14 failure modes in 3 categories, built from 150 expert-annotated traces ([arXiv, Mar 2025](https://arxiv.org/abs/2503.13657)). Its MAST-Data set now holds 1,600+ traces across 7 frameworks.

**What Vol 2 has today.** Turn 55 teaches why subagents help (Q268), what they cost (Q269) and when not to use them (Q272). Turn 95 Q469 names "multi-agent patterns" only as a framework feature, and Turn 131 covers multi-agent safety (Q653). Searches for handoff, supervisor, magentic, swarm, group chat and agents-as-tools found nothing.

**What to teach.**
- The pattern vocabulary and when each fits:
  - single agent with tools;
  - agent-as-tool, where the manager keeps ownership;
  - handoff, where the specialist owns the rest of the turn;
  - sequential and concurrent workflows;
  - group chat;
  - magentic, where a manager plans and re-plans.
- LLM-driven vs code-driven orchestration. Prefer code-driven flows when the steps are known.
- Round, stall and reset limits on every dynamic pattern, as in MAF's magentic example.
- A cost case before going multi-agent: weigh the token multiple (about 15× chat in Anthropic's system) against the value of the task.
- Debugging with the MAST categories (system design, inter-agent misalignment, task verification). Then share fuller context, add a verifier step, or collapse back to one agent.

**Idea to remember.** Default to one agent with good tools, and add agents only for parallel, separable, read-heavy work whose value covers roughly 15× the tokens.

**Interview questions.**
1. Handoff or agent-as-tool: how do you choose? — Use agent-as-tool when a specialist should solve a bounded subtask while the manager keeps ownership of the final answer. Use a handoff when routing is the workflow and the specialist should own the rest of the turn, as in triage to billing.
2. When does a multi-agent design actually pay off? — For breadth-first, parallelisable, read-heavy work such as research, where the information exceeds one context window; Anthropic measured about 15× chat tokens for its research system. It rarely pays for tightly coupled work like most coding, where parallel agents make conflicting implicit decisions.
3. How do you debug a multi-agent system that does worse than a single agent? — Classify trace failures with a taxonomy such as MAST (system design, inter-agent misalignment, task verification). Then share fuller context or traces, add a verifier step, or collapse the agents back into one.

---

### AGT-3 · Tool-scale engineering: tool search, code execution over MCP ("code mode") and programmatic tool calling  — **P2** · THIN · Section F · extend Turn 61

*Overlaps gap doc:* #7: gap #7 covers compaction, context editing and memory. This entry adds the context bloat that comes from tool definitions and tool results, and code-as-action.

**What it is.** Techniques for agents connected to dozens of Model Context Protocol (MCP) servers and hundreds of tools. Tool definitions are deferred and found by search, or tools are exposed as a code API that the model calls from sandboxed code, so only final results come back into context.

**Why now.** Anthropic reported that 58 tools used about 55k tokens before a conversation started ([Anthropic, 24 Nov 2025](https://www.anthropic.com/engineering/advanced-tool-use)). In the same report:
- its Tool Search Tool raised Opus 4 from 49% to 74% and Opus 4.5 from 79.5% to 88.1% on MCP evals;
- programmatic tool calling cut tokens by 37% (43,588 to 27,297);
- tool-use examples lifted complex-parameter accuracy from 72% to 90%.

Code execution with MCP cut one workflow from 150,000 to 2,000 tokens (98.7%), though it needs sandboxing and monitoring ([Anthropic, 4 Nov 2025](https://www.anthropic.com/engineering/code-execution-with-mcp)). Cloudflare's Code Mode runs model-written TypeScript against MCP bindings in V8 isolates ([Cloudflare, 26 Sep 2025](https://blog.cloudflare.com/code-mode/)). The approach is now cross-vendor:
- OpenAI documents tool search, using `defer_loading: true`, also on MCP server tools and namespaces ([OpenAI docs, accessed 26 Sep 2026](https://developers.openai.com/api/docs/guides/tools-tool-search)).
- OpenAI also documents programmatic tool calling ([OpenAI docs, accessed 26 Sep 2026](https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling)).
- Claude Code exposes `ENABLE_TOOL_SEARCH` ([Anthropic docs, accessed 26 Sep 2026](https://code.claude.com/docs/en/agent-sdk/typescript)).

**What Vol 2 has today.** Only adjacent material exists: Turn 53 Q259 (progressive disclosure for skills), Turn 61 Q299 and Q302 (task-shaped tools; wrong-tool and argument-error rates and output tokens) and Turn 86 (sandboxes). Searches for tool search, defer, code mode, code execution, programmatic tool, many tools and tool count found nothing.

**What to teach.**
- Measuring tool-definition load. Count the schema tokens sent before the first user message, and track wrong-tool and wrong-argument rates as tools are added (the Turn 61 metrics).
- Deferred loading with a tool-search tool, which applies Turn 53's progressive disclosure to tool schemas and whole MCP servers.
- Code mode and programmatic tool calling. Generate a typed API from MCP tools, let the model chain calls in sandboxed code, and return only the final result to context.
- The sandbox cost of code-as-action: Turn 86 isolation, egress limits and monitoring.
- Tool-use examples for tools with complex parameters.
- When to keep direct calls: few tools, per-call human approval or audit, or no sandbox allowed.

**Idea to remember.** When tools run into the hundreds, stop pasting every schema into the prompt: let the agent search for tools, or write sandboxed code against them and return only the result.

**Interview questions.**
1. Why does connecting more MCP servers make an agent worse? — Every tool schema costs context tokens (58 tools used about 55k in Anthropic's example), and the crowding raises wrong-tool and wrong-argument errors. Deferred loading with tool search restores both context and accuracy.
2. What is "code mode", and what does it cost you? — The agent writes code against a typed API generated from MCP tools and runs it in a sandbox, chaining many calls and returning only final results (150k to 2k tokens in Anthropic's example). The cost is that you now execute model-written code, so you need the Turn 86 sandbox controls, egress limits and monitoring.
3. When would you keep plain direct tool calls? — When there are few tools, when each call needs human approval or audit, or when the environment allows no code sandbox.

---

### AGT-4 · Gap doc #2 (deepened): Computer-use agents in enterprise operations, the API-to-GUI decision ladder and RPA's agentic successor  — **P2** · MISSING · Section F · new turn after Turn 61 (the gap-doc #2 turn), with a one-paragraph version of the decision ladder inside Turn 61

*Overlaps gap doc:* #2: this entry replaces #2 and adds the operational layer #2 lacks. It covers per-step pricing, the credential model, the limits of allow-lists, machine isolation, the move from RPA to agents, and the API-first decision ladder. It also corrects the benchmark citations and sets the priority at P2 rather than P1.

**What it is.** Agents that operate desktop and web graphical user interfaces (GUIs) through screenshots and virtual keyboard and mouse input when no API exists. They now ship inside automation platforms such as Copilot Studio computer use and UiPath Maestro, with machine pools, credential vaults, allow-lists and supervised runs.

**Why now.** Headline scores overstate readiness:
- Top OSWorld-Verified rows score about 85–86%, above the 72.36% human baseline ([XLANG Lab, OSWorld](http://osworld-v1.xlang.ai/)). Most of these rows are self-reported ([BenchLM, 22 Sep 2026](https://benchlm.ai/benchmarks/osworld-verified)).
- The best OSWorld 2.0 result at publication was 20.6% binary completion on 108 multi-hour workflows ([arXiv, 28 Jun 2026](https://arxiv.org/abs/2606.29537)). That was Claude Opus 4.8 with maximum thinking over 500 steps, with 54.8% partial credit; GPT-5.5 was near 13%.
- An audit found 15.3% of benchmark FAIL verdicts were themselves wrong ([arXiv, 30 Jul 2026](https://arxiv.org/abs/2607.28367)).

Copilot Studio computer use became generally available (GA) for systems that "lacked APIs" ([Microsoft Copilot Blog, 26 May 2026](https://www.microsoft.com/en-us/copilot/blog/copilot-studio/new-and-improved-computer-using-agents-a-new-workflows-experience-and-real-time-voice-experiences/)). Its terms ([Microsoft Learn, updated 18 Sep 2026](https://learn.microsoft.com/en-us/microsoft-copilot-studio/computer-use)):
- It bills 5 Copilot Credits per step, or 15 on a premium model.
- OpenAI's CUA (computer-using agent) and Claude Sonnet 4.5 are GA; Claude Sonnet 4.6 and Opus 4.6 are Experimental.
- Microsoft warns that shared agents run with the maker's credentials.

OpenAI retired only the computer-use-preview model snapshot, on 23 Jul 2026. The retirement was announced on 22 Apr 2026, with gpt-5.6-terra as the substitute ([OpenAI deprecations, accessed 26 Sep 2026](https://developers.openai.com/api/docs/deprecations)). The Responses API computer tool continues on GPT-5.6 models ([OpenAI computer use guide, accessed 26 Sep 2026](https://developers.openai.com/api/docs/guides/tools-computer-use)). OpenAI now recommends a code-execution mode, in which the model writes Playwright or PyAutoGUI scripts, and keeps the computer tool as a supported alternative.

UiPath launched agentic automation ([UiPath, 30 Apr 2025](https://www.uipath.com/newsroom/uipath-launches-first-enterprise-grade-platform-for-agentic-automation)). At FUSION it split Maestro into Maestro Orchestrate and Maestro Automate and made Coding Agents GA ([UiPath, 23 Sep 2026](https://www.uipath.com/newsroom/uipath-platform-updates-fusion)).

**What Vol 2 has today.** Searches for computer use, OSWorld, screenshot, RPA, UiPath, Playwright and browser automation found nothing. The only adjacent material is Turn 69 on WebMCP (Q338) and Turn 122 on agentic browsers (Q607 and Q611).

**What to teach.**
- The integration ladder, highest rung first:
  1. official API;
  2. MCP server or connector;
  3. WebMCP or site tools;
  4. deterministic robotic process automation (RPA) selectors;
  5. model-written automation scripts (code-execution mode, for example Playwright);
  6. a screenshot-driven computer-use agent.
- Per-step costing. Copilot Studio charges 5 credits per step (15 on premium), so Microsoft's 4-step timesheet costs 20 or 60 credits. Multiply by volume and retries, compare with an RPA bot or an API build, and budget for traces heavy with screenshots.
- Credentials and isolation. Do not run shared agents on maker credentials. Use end-user or vaulted credentials (Key Vault), dedicated machines and HTTPS only.
- The limits of platform controls:
  - Allow-lists don't stop the model from opening other sites.
  - Every screen is untrusted input (Turn 122 Q611).
  - Copilot Studio's human supervision is an Outlook escalation when the agent detects potentially harmful instructions. It is not a per-step approval, so add your own gates for risky steps.
- Critical reading of benchmarks. Prefer verified runs, check step limits and permissions, and measure long-horizon completion. Timestamp every figure, because OSWorld 2.0 leaderboard entries have risen since publication.
- Working alongside an existing RPA estate, where UiPath Maestro orchestrates agents, robots and people. Move hot paths to APIs, MCP or scripts over time.

**Idea to remember.** Driving the GUI is the integration of last resort: price it per step, run it on isolated machines under least-privilege accounts, and move hot paths to APIs, MCP or scripts.

**Interview questions.**
1. A customer wants an agent to file forms on a legacy portal. How do you choose the integration? — Walk the ladder: official API, MCP server or connector, WebMCP or site tools, deterministic RPA selectors, model-written automation scripts, and only then a screenshot-driven computer-use agent. Use the highest rung available, and keep screenshot-driven computer use for the long tail and for UIs that change often.
2. How do you cost a computer-use workflow? — Per step, not per run: on Copilot Studio a 12-step run costs 60 credits on a standard model and 180 on a premium one. Multiply by volume and retries, then compare with an RPA bot or an API build.
3. Name three security pitfalls specific to computer use. — Shared agents that run with the maker's credentials, allow-lists that block actions but not navigation, and screens full of untrusted content that can inject instructions. Mitigate with dedicated machines, end-user or vaulted credentials, HTTPS only and your own approval gates for risky steps.

---

### AGT-5 · Gap doc #13 (deepened): Distribution inside AI assistants, from public directories to the customer's Microsoft 365 Copilot, Gemini Enterprise and Slack  — **P2** · MISSING · Section J · the gap-doc #13 turn (near Turns 59/101), split into Part A public directories and Part B enterprise-tenant channels, cross-linked to Turn 72

*Overlaps gap doc:* #13: this entry replaces #13, which covers public directories (ChatGPT Apps SDK, MCP Registry, plugin marketplaces). It adds four things:
- enterprise-tenant channels (declarative vs custom engine agents);
- admin-approval paths;
- SaaS data-use terms that shape the architecture (Slack);
- concrete directory review rules.

The entry is P2, but treat it as P1 in accounts centred on Microsoft 365.

**What it is.** The build-and-release discipline for agents that live inside an assistant the customer already runs, rather than in a standalone user interface (UI). Each channel has its own packaging, identity, admin approval, review rules and data-use terms: Microsoft 365 Copilot declarative or custom engine agents, Gemini Enterprise, Slack apps and MCP clients, and ChatGPT plugins.

**Why now.** Microsoft's docs split two kinds of agent ([Microsoft Learn, 5 Aug 2026](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/agents-overview)). Declarative agents use "Copilot's AI infrastructure, model, and orchestrator" with "No additional hosting". Custom engine agents "might require you to provide additional hosting", and their builders own compliance. Gemini Enterprise bundles a no-code workbench, prebuilt agents, connectors (Microsoft 365, Salesforce, SAP) and central governance ([Google Cloud, 9 Oct 2025](https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise)).

Slack limits outside apps in three places:
- **MCP access.** "Only directory-published apps or internal apps may use MCP" ([Slack docs, accessed 26 Sep 2026](https://docs.slack.dev/ai/mcp-server/)).
- **API terms** ([Slack, effective 10 Oct 2025](https://slack.com/terms-of-service/api)). Apps offered outside the builder's organisation may not train large language models (LLMs) on API data, bulk-export it or use it across organisations. Third-party providers may not keep persistent indexes of data fetched through the Data Access and Real-Time Search (RTS) APIs.
- **Rate limits** ([Slack changelog, 29 May 2025](https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps/)). History APIs are cut to 1 request per minute (15 objects) for commercially distributed apps that are not in the Marketplace. "Internal customer-built applications are not impacted".

OpenAI now calls submissions "plugins", published to "the universal Plugins Directory shared by ChatGPT and Codex" ([OpenAI, accessed 26 Sep 2026](https://developers.openai.com/apps-sdk/deploy/submission)). Review requires:
- `readOnlyHint`, `openWorldHint` and `destructiveHint` on every MCP tool;
- a Content Security Policy (CSP) for UI;
- domain verification and a verified developer identity;
- "Five positive test cases and three negative test cases".

MCP Apps became the first official MCP extension ([MCP blog, 26 Jan 2026](https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/)).

**What Vol 2 has today.** Searches for Copilot, Microsoft 365, Gemini, Slack, ChatGPT, declarative agent and directory found nothing. The adjacent material is Turn 59 Q291 (MCP Apps as UI), Turn 71 Q350 (Cross App Access) and Turn 72 (hosted runtimes rather than distribution).

**What to teach.**
- Choosing the channel early:
  - A declarative agent reuses the customer's Copilot model, orchestrator and compliance boundary, and needs no hosting.
  - A custom engine agent uses your own models and orchestration, and you own the hosting, security and responsible-AI evidence.
- The admin-approval path for each channel: Microsoft 365 admin, Gemini Enterprise governance, Slack admin approval of MCP clients, and directory review for ChatGPT.
- SaaS data terms before retrieval design. Know whether you ship an internal app or a commercially distributed one. For a third-party app, prefer federated real-time access (the RTS API or MCP server) to bulk copying.
- Passing a directory review:
  - truthful tool annotations;
  - a CSP naming the exact fetch domains;
  - minimal personal data in tool responses;
  - domain verification and demo credentials;
  - positive and negative test cases.
- One core agent with thin channel adapters, so the same tools and evals serve several assistants.

**Idea to remember.** In the enterprise the assistant is the channel: decide early between a declarative agent inside the customer's Copilot, Gemini or Slack and a custom engine you own, because that choice sets your model, auth, data terms and approval path.

**Interview questions.**
1. Declarative agent or custom engine agent in Microsoft 365 Copilot: when is each right? — A declarative agent reuses Copilot's model, orchestrator and compliance boundary, needs no hosting, and suits knowledge plus a few actions. A custom engine agent is for your own orchestration, models or proactive autonomy, and you then own hosting, security and responsible-AI evidence.
2. A customer wants your Slack assistant to index their Slack into a vector store. What do Slack's terms allow? — If you ship a commercially distributed (third-party) app, Slack's API terms bar LLM training on API data, bulk export and persistent indexes of data fetched via the Data Access/RTS APIs, and non-Marketplace apps are throttled. An internal app built in the customer's own workspace is exempt from the throttling and third-party clauses, but still bound by the customer's own data policy.
3. What does ChatGPT's Plugins Directory review check on an MCP-based plugin? — Truthful tool annotations (read-only, open-world, destructive), a CSP naming the exact domains the UI fetches from, and minimal personal data in tool responses. It also checks domain verification, a verified developer identity, demo credentials, and five positive and three negative test cases.

---

### AGT-6 · Systems-of-record agent platforms (Salesforce Agentforce, ServiceNow, SAP Joule, Workday): integrate, extend or compete  — **P2** · MISSING · Section G · new turn after Turn 72

*Overlaps gap doc:* none

**What it is.** System-of-record (SoR) vendors now sell their own agents, builders, data layers and per-action pricing, and increasingly expose governed MCP and Agent2Agent (A2A) endpoints to outside AI. These are the vendors of customer relationship management (CRM), IT service management (ITSM), enterprise resource planning (ERP) and human capital management (HCM) systems. The forward deployed engineer (FDE) must decide whether to build inside the vendor's platform, call it through those endpoints, or build an independent agent that federates across systems.

**Why now.** Salesforce's Agentforce pricing ([Salesforce, accessed 26 Sep 2026](https://www.salesforce.com/agentforce/pricing/)):
- Flex Credits cost USD 500 per 100k, at 20 credits (USD 0.10) per action and 30 per voice action.
- A conversation costs USD 2.
- Add-ons are USD 125 per user per month, and the user licence is USD 5.
- Agentforce 1 starts at USD 550 per user per month.

Salesforce signed to buy Informatica, at about USD 8B equity value ([Salesforce, 27 May 2025](https://www.salesforce.com/news/press-releases/2025/05/27/salesforce-signs-definitive-agreement-to-acquire-informatica/)), and closed the deal ([Salesforce, 18 Nov 2025](https://www.salesforce.com/news/press-releases/2025/11/18/salesforce-completes-acquisition-of-informatica/)). It then announced Headless 360 at TDX ([Salesforce, 15 Apr 2026](https://www.salesforce.com/news/stories/salesforce-headless-360-announcement/)). Headless 360 exposes capabilities "as an API, MCP tool, or CLI command", with 60+ new MCP tools and 30+ coding skills.

ServiceNow made four moves:
- It announced the Moveworks acquisition (USD 2.85B) on 10 Mar 2025 and closed it on 15 Dec 2025 ([ServiceNow, 15 Dec 2025](https://newsroom.servicenow.com/press-releases/details/2025/ServiceNow-completes-acquisition-of-Moveworks/default.aspx)).
- It partnered with OpenAI ([ServiceNow, 20 Jan 2026](https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-and-OpenAI-collaborate-to-deepen-and-accelerate-enterprise-AI-outcomes/default.aspx)).
- It partnered with Anthropic, making Claude the default model for ServiceNow Build Agent ([Anthropic, 28 Jan 2026](https://www.anthropic.com/news/servicenow-anthropic-claude)).
- It opened "its full system of action to any AI agent" through a GA MCP server that names Claude and Copilot ([ServiceNow, 5 May 2026](https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-opens-its-full-system-of-action-to-every-AI-Agent-in-the-enterprise/default.aspx)).

Workday bought Flowise ([Workday, 14 Aug 2025](https://newsroom.workday.com/2025-08-14-Workday-Acquires-Flowise,-Bringing-Powerful-AI-Agent-Builder-Capabilities-to-the-Workday-Platform)). It also completed the Sana deal agreed on 16 Sep 2025 ([Workday, 4 Nov 2025](https://newsroom.workday.com/2025-11-04-Workday-Completes-Acquisition-of-Sana)). SAP says bi-directional A2A for Joule "will be generally available in Q4" 2026, so this is still a plan ([SAP, 13 May 2026](https://news.sap.com/2026/05/future-enterprise-autonomous/)).

**What Vol 2 has today.** Searches for Salesforce, Agentforce, ServiceNow, SAP, Joule, Workday, CRM and ITSM found nothing, and "ERP" appears only inside other words. Turn 76 mentions "systems of record" only as a poisoning defence. Turn 72 covers cloud hosted-agent runtimes, not SaaS vendors' agent platforms.

**What to teach.**
- A map made before building next to an SoR: what its own agent already does, what its data terms allow, and its price per action.
- The build-inside vs build-outside decision:
  - Build inside when the work lives mostly in that vendor's data and permissions and the per-action price fits.
  - Build outside when the work spans systems, needs control over the model or evals, or the volume makes per-action pricing expensive.
- Integration through governed endpoints (ServiceNow's MCP server, Salesforce Headless 360, and later SAP Joule A2A). Always act under the user's identity, never a shared admin token.
- Cost per successful task. Compare vendor per-action pricing with your own tokens, hosting, evaluation and maintenance, using success rates from the customer's eval set.
- Vendor churn (acquisitions, model partnerships, pricing), with tools and evals kept portable.

**Idea to remember.** Integrate through the system-of-record vendor's governed MCP or A2A endpoints under the user's identity, and decide between building inside and building outside on data gravity, data terms and price per successful task.

**Interview questions.**
1. The customer runs Service Cloud. Do you build in Agentforce, or build a custom agent that calls Salesforce? — Build in Agentforce when the work lives mostly inside Salesforce data and permissions and the per-action price fits. Build custom when the work spans many systems, needs model or eval control, or volume makes per-action pricing expensive; the custom agent then calls Salesforce through governed APIs or MCP under the user's identity, never a shared admin token.
2. How do you compare vendor per-action pricing with running your own agent? — Normalise both to cost per successful task: at 20 Flex Credits (USD 0.10) per action, 1M actions a month is about USD 100k before licences. Compare that with your tokens, hosting, evaluation and maintenance, and with success rates on the customer's eval set.
3. How has outside agents' access to SoR data changed in 2026? — Vendors now publish governed agent endpoints: ServiceNow's GA MCP server (May 2026) and Salesforce Headless 360 (Apr 2026), with SAP planning bi-directional A2A for Joule in Q4 2026. Design federated, permission-aware calls through these endpoints under the user's identity, not bulk copies.

---

### AGT-7 · Enterprise agent control planes and agent sprawl (Microsoft Agent 365, ServiceNow AI Control Tower, Gemini Enterprise governance)  — **P2** · THIN · Section G · extend Turn 71

*Overlaps gap doc:* none

**What it is.** Tenant-wide control planes that inventory every agent, whether first-party, low-code, pro-code or third-party. They give each agent an identity, apply access and data loss prevention (DLP) policy, observe its behaviour and can quarantine it. An FDE's custom agent now has to register with them and report into them.

**Why now.** Microsoft announced Agent 365 as "the control plane for AI agents" ([Microsoft, 18 Nov 2025](https://www.microsoft.com/en-us/microsoft-365/blog/2025/11/18/microsoft-agent-365-the-control-plane-for-ai-agents/)). It provides registry, access control, visualisation, interoperability and security. It covers agents built with Copilot Studio, Foundry, MAF, the Agent 365 SDK, open-source frameworks and third-party platforms. Microsoft states: "As of May 1, 2026, Microsoft Agent 365 is generally available for the Commercial segment on a per user basis" ([Microsoft Learn, 19 Aug 2026](https://learn.microsoft.com/en-us/microsoft-agent-365/overview)). It adds that Agent 365 "works best when using Microsoft E5 as a pre-requisite".

Control planes also connect to each other and multiply:
- ServiceNow's AI Control Tower integrates with Foundry, Copilot Studio and Agent 365, and ServiceNow agents are listed in the Agent 365 Marketplace ([ServiceNow, 5 May 2026](https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-expands-AI-agent-governance-through-deeper-integration-with-Microsoft/default.aspx)).
- Gemini Enterprise offers a "central governance framework, so you can visualize, secure, and audit all of your agents from one place" ([Google Cloud, 9 Oct 2025](https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise)).
- UiPath added Runtime Checker, an LLM-as-Judge guardrail, and identity and access policies ([UiPath, 23 Sep 2026](https://www.uipath.com/newsroom/uipath-platform-updates-fusion)).

**What Vol 2 has today.** Turn 71 teaches agent identity governed by the identity provider and recorded in an agent registry (Q351 lists the registry fields; Q352 covers staged autonomy). Turn 100 Q496 teaches a gateway "registry of approved servers". Searches for control plane, Agent 365, Entra and sprawl found nothing.

**What to teach.**
- What a control plane adds over a gateway:
  - an inventory across builders and vendors;
  - per-agent identity and conditional access;
  - DLP and threat policy on agent activity;
  - lifecycle actions (review, disable, quarantine).
- Making a custom agent governable:
  - its own identity (not a shared key);
  - a named owner and purpose;
  - declared scopes and tools;
  - OpenTelemetry traces and audit logs;
  - a kill switch;
  - a registry entry with review dates.
- Finding out early which control plane the customer runs (Agent 365, ServiceNow AI Control Tower, Gemini Enterprise, UiPath) and planning onboarding. Registration can be a go-live gate.
- Federation. One agent may appear in several control planes, so agree which one holds the agent's identity and where telemetry goes.

**Idea to remember.** Your agent is one of hundreds in the customer's tenant: ship it ready to register in their control plane, with an agent ID, owner, scopes and telemetry, because registration can be a go-live gate.

**Interview questions.**
1. What does an enterprise agent control plane give the customer that a gateway does not? — An inventory of every agent across builders and vendors, per-agent identity and conditional access, data-loss and threat policies on agent activity, and lifecycle actions such as review, disable or quarantine. A gateway only sees the model and tool traffic that passes through it.
2. What must a custom agent expose to be governable? — Its own identity (not a shared key), a named owner and purpose, declared scopes and tools, OpenTelemetry traces and audit logs, a kill switch, and a registry entry with review dates.

---

### AGT-8 · Coding-agent governance at team scale: deterministic hooks, managed settings and the plugin supply chain  — **P2** · THIN · Section J · extend Turn 101

*Overlaps gap doc:* #13: #13 names coding-agent plugin marketplaces only as a distribution channel. This entry adds enforcement through hooks and managed policy, and the supply-chain risk of plugins (linked to Turn 77's AI bill of materials).

**What it is.** The layer that makes coding agents safe and repeatable across a customer's engineering organisation. It has three parts: deterministic lifecycle hooks around tool calls, admin-managed settings that override users, and plugins and marketplaces that bundle commands, subagents, MCP servers and hooks. Generic harness primitives such as permission callbacks and stop conditions belong to AGT-1; this entry covers team-scale policy and supply chain.

**Why now.** The Claude Code hooks reference lists 33 events, for example `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolBatch`, `SubagentStop`, `PreCompact`/`PostCompact`, `TaskCreated`, `ConfigChange` and `Elicitation` ([Anthropic docs, accessed 26 Sep 2026](https://code.claude.com/docs/en/hooks)). The same reference sets out the enforcement rules:
- A `PreToolUse` hook can allow, deny or ask, or rewrite a tool's input.
- The managed setting `allowManagedHooksOnly` blocks "user, project, local, and plugin hooks".
- One exception applies: "Hooks from plugins force-enabled in managed settings enabledPlugins are exempt".

Plugins bundle slash commands, subagents, MCP servers and hooks, and are distributed through git-hosted marketplaces ([Anthropic, 9 Oct 2025](https://claude.com/blog/claude-code-plugins)). OpenAI's "harness engineering" account with Codex reports about 1M lines and about 1,500 pull requests over five months from 3, later 7, engineers ([InfoQ, Feb 2026](https://www.infoq.com/news/2026/02/openai-harness-engineering-codex/)). UiPath made Coding Agents GA as automation builders ([UiPath, 23 Sep 2026](https://www.uipath.com/newsroom/uipath-platform-updates-fusion)).

**What Vol 2 has today.** Turn 101 already teaches the spec-driven loop (Q500 "Spec → plan review → small tested steps → diff review → commit") with sandboxed, limited-permission runs. Turn 54 treats AGENTS.md as guidance, not authority. Turn 77 teaches pinning and the AI bill of materials (AI-BOM). Searches found nothing relevant for hook (only "webhook"), plugin (only a GPU device plugin), managed settings or marketplace.

**What to teach.**
- Guidance vs enforcement. AGENTS.md holds conventions. Hooks hold rules that must apply whatever the model does: block destructive commands and writes to protected paths, run formatters and tests after edits, and scan for secrets.
- Writing `PreToolUse` and permission hooks that allow, deny, ask or rewrite input.
- Rolling out managed settings: permission modes, deny rules, `allowManagedHooksOnly` and the `enabledPlugins` exemption.
- Plugins and marketplaces as supply chain: an internal marketplace with pinned, reviewed plugins, an MCP server allow-list, and AI-BOM entries (Turn 77).
- Running agents in sandboxes or cloud workspaces, with agent and hook telemetry sent to the security information and event management (SIEM) system.
- Spec-driven tools (GitHub Spec Kit, Kiro) as brand examples of the Turn 101 loop. Name them; don't re-teach the loop.

**Idea to remember.** Prompts suggest and hooks enforce: put non-negotiable rules in deterministic hooks and admin-managed settings, and treat plugins and marketplaces as supply chain.

**Interview questions.**
1. AGENTS.md vs hooks: what goes where? — AGENTS.md carries guidance the model should follow: commands, conventions and architecture. Hooks carry rules that must hold regardless of the model, such as blocking `rm -rf` or protected-path writes, running formatters and tests after edits, or scanning for secrets, and they run as code at lifecycle events.
2. How would you lock down a coding agent across 500 engineers? — Use admin-managed settings for permission modes, deny rules and managed-only hooks, allow only an internal plugin marketplace with pinned, reviewed plugins, and restrict MCP servers to an allow-list. Run agents in sandboxes or cloud workspaces and send telemetry to the SIEM.
3. `allowManagedHooksOnly` is on, yet a plugin's hook still runs. Why? — Hooks from plugins force-enabled in the managed `enabledPlugins` setting are exempt from that block. Review force-enabled plugins as part of managed policy, because their hooks run despite the managed-only rule.

---

### AGT-9 · Gap doc #18 (deepened): Low-code and visual agent builders, their governance, vendor churn and the graduation path to code  — **P2** · MISSING · Section J · new turn after Turn 99 (the gap-doc #18 turn)

*Overlaps gap doc:* #18: this entry replaces #18, which frames low-code builders only as an n8n exposure risk. It adds four things: vendor-native builders, the risk of vendors retiring products (the OpenAI Agent Builder shutdown), dated CISA KEV entries, and criteria for moving flows into code. It also drops #18's figure of "647,017 exposed n8n instances". That number is the attacker's own FOFA search result, which Unit 42 quoted; it is not a Unit 42 measurement.

**What it is.** Visual and no-code builders used by business teams. Some are vendor-native (Copilot Studio, the Gemini Enterprise workbench, OpenAI Agent Builder); others are self-hosted (n8n, Langflow, Flowise). The FDE's job is to govern and secure them, and to move successful flows into versioned code.

**Why now.** On 3 Jun 2026 OpenAI gave notice that Agent Builder shuts down on 30 Nov 2026, with "Agents SDK or ChatGPT Workspace Agents" as replacements; "ChatKit remains available" ([OpenAI deprecations, accessed 26 Sep 2026](https://developers.openai.com/api/docs/deprecations)).

CISA's Known Exploited Vulnerabilities (KEV) catalog ([CISA KEV, catalog 2026.09.25](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json)) lists several Common Vulnerabilities and Exposures (CVE) entries for these builders, scored with the Common Vulnerability Scoring System (CVSS):
- **Langflow CVE-2025-3248:** CVSS 9.8, unauthenticated remote code execution (RCE). Added 5 May 2025.
- **n8n CVE-2025-68613:** CVSS 10, expression-injection RCE that needs an authenticated user. Added 11 Mar 2026.
- **Langflow, four more entries:** CVE-2026-33017 (25 Mar 2026), CVE-2025-34291 (21 May 2026), CVE-2026-55255 (7 Jul 2026) and CVE-2026-0770 (21 Jul 2026).
- **Langflow CVE-2026-9198:** added 4 Aug 2026, giving Langflow six KEV entries in total.

n8n CVE-2026-21858 (CVSS 10, unauthenticated file access) was published on 7 Jan 2026 ([CVE Program, 7 Jan 2026](https://cveawg.mitre.org/api/cve/CVE-2026-21858)) and is not in KEV. Even so, Unit 42 documented an AI-agent-driven campaign against it, n8n CVE-2025-68613 and Langflow CVE-2026-33017 ([Unit 42, 30 Jul 2026](https://unit42.paloaltonetworks.com/autonomous-ai-cyber-attack-campaign/)). Workday bought Flowise ([Workday, 14 Aug 2025](https://newsroom.workday.com/2025-08-14-Workday-Acquires-Flowise,-Bringing-Powerful-AI-Agent-Builder-Capabilities-to-the-Workday-Platform)). Copilot Studio ([Microsoft Learn, updated 18 Sep 2026](https://learn.microsoft.com/en-us/microsoft-copilot-studio/computer-use)) and the Gemini Enterprise workbench ([Google Cloud, 9 Oct 2025](https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise)) let business users build agents themselves.

**What Vol 2 has today.** Searches for n8n, Langflow, Flowise, low-code, no-code, visual builder, Copilot Studio and citizen found nothing. Turn 95 covers code-first frameworks only.

**What to teach.**
- An inventory of agents built by business users, with each one recorded in the agent registry (Turn 71) and the customer's control plane (AGT-7).
- Hardening self-hosted builders:
  - Patch fast against KEV entries.
  - Keep the editor and webhooks off the open internet unless they sit behind authentication.
  - Isolate the host.
  - Narrow the stored credentials, because one bug exposes every connected system.
- Expression and code nodes treated as code execution. Sandbox them and limit who can edit flows, because CVE-2025-68613 is an insider or stolen-credential path.
- A check on whose credentials a shared no-code agent runs with. Copilot Studio warns that shared agents run with the maker's credentials.
- Planning for vendor churn:
  - Require an export path (code or open formats).
  - Keep prompts and evals outside the builder.
  - Budget for migration, for example from Agent Builder to the Agents SDK or Workspace Agents.
- Criteria for graduating a flow to code:
  - it becomes business-critical;
  - it needs CI evals, version control or review;
  - it crosses trust boundaries (untrusted input plus privileged tools);
  - it needs non-trivial error handling;
  - the builder's roadmap or licence becomes a risk.

**Idea to remember.** Let business teams prototype in builders, but require an export path, a registry entry and a patched, isolated host, and move anything business-critical into versioned code with evals.

**Interview questions.**
1. When do you graduate a builder flow to code? — When it becomes business-critical, needs CI evals, version control or code review, or crosses trust boundaries (untrusted input plus privileged tools). Also when it needs non-trivial error handling, or when the builder's roadmap or licence becomes a risk.
2. Why are self-hosted workflow builders high-value targets? — They hold credentials to many systems, often expose webhooks to the internet and include code or expression nodes, so one bug reaches every connected system. Langflow CVE-2025-3248 is an unauthenticated RCE (in KEV since May 2025), while n8n CVE-2025-68613 (in KEV since Mar 2026) needs an authenticated user, which makes it an insider or stolen-credential path.
3. What does OpenAI's Agent Builder deprecation teach? — A vendor can retire a builder on about six months' notice (notice 3 Jun 2026, shutdown 30 Nov 2026). Insist on exportable definitions, keep evals and prompts outside the tool, and budget a migration path.

---

### AGT-10 · Generative-UI protocol choice: AG-UI vs A2UI vs MCP Apps  — **Watch** · THIN · Section F · one sentence plus one Q&A in Turn 59

*Overlaps gap doc:* none. The gap doc lists "MCP Apps and generative UI: Turn 59" as already covered; this entry adds only the A2UI name. The ChatGPT CSP requirement moved to AGT-5.

**What it is.** Three complementary standards for agent interfaces:
- AG-UI streams events between an agent backend and a front end.
- A2UI is declarative JSON describing native components from a catalogue the client approves.
- MCP Apps delivers server-supplied HTML through `ui://` resources rendered in sandboxed iframes.

**Why now.** Google announced A2UI at v0.8 as "native-first", complementary to AG-UI and carried over A2A ([Google Developers Blog, 15 Dec 2025](https://developers.googleblog.com/introducing-a2ui-an-open-project-for-agent-driven-interfaces/)). Its README still says "Status: Early stage public preview", with v0.9.1 as the current production release and v1.0 a release candidate ([Google, GitHub, accessed 26 Sep 2026](https://github.com/google/A2UI)). MCP Apps was proposed as SEP-1865 ([MCP blog, 21 Nov 2025](https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/)) and became the first official MCP extension ([MCP blog, 26 Jan 2026](https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/)).

**What Vol 2 has today.** Turn 59 Q290 defines AG-UI. Q291 already draws the key distinction: "MCP Apps let a tool server supply its own interface; generative UI lets the model choose which approved components to render". That is A2UI's catalogue model in all but name. A search for A2UI found nothing.

**What to teach.**
- One sentence in Turn 59 naming A2UI as a catalogue-based, native-first spec that is still in public preview.
- Choosing by who owns the look and feel:
  - With A2UI, the host renders its own approved components and runs no agent-supplied code.
  - With MCP Apps, a tool vendor ships sandboxed HTML into many hosts.
- AG-UI as the transport: A2UI payloads, or references to MCP Apps UIs, can travel over it.
- A re-check of A2UI at v1.0 before giving it more space.

**Idea to remember.** AG-UI moves events, A2UI describes native components, MCP Apps ships sandboxed HTML: choose by who owns the look and feel and how much agent-supplied code you are willing to render.

**Interview questions.**
1. A2UI or MCP Apps for an approval form inside the customer's React app? — A2UI, because the agent sends a declarative description that the app renders with its own approved components, so no agent-supplied code runs. MCP Apps fits when a tool vendor must ship its own UI into many hosts, rendered in a sandboxed iframe. (This is the one Q&A to add to Turn 59.)
2. Where does AG-UI fit next to these? — AG-UI is the event transport between an agent backend and a front end, carrying messages, tool calls and state deltas. A2UI payloads, or references to MCP Apps UIs, can travel over it.

---

#### Disagreements with Vol 2 / gap doc (agents)

- **Gap doc #2 (computer use).** The citation for ">85% on OSWorld-Verified" is wrong. arXiv 2607.26041 is "Desktop-Delta Bench" ([arXiv, 28 Jul 2026](https://arxiv.org/abs/2607.26041)). The ~86% figure comes from leaderboard rows that are mostly self-reported ([BenchLM, 22 Sep 2026](https://benchlm.ai/benchmarks/osworld-verified)). The #2 Q&A also mixes up OSWorld and OSWorld-Verified.
  - *Change:* use AGT-4 as the #2 turn at P2, not P1. Cite arXiv 2606.29537 for OSWorld 2.0 (20.6%, "at publication, June 2026") and arXiv 2607.28367 for mis-scoring. Label leaderboard figures as self-reported and timestamp them. Teach a short version of the decision ladder, including the code-execution rung, in Turn 61.
  - **Do not** argue that GUI driving is fading because of OpenAI's 23 Jul 2026 retirement. Only the computer-use-preview snapshot was retired, and the computer tool continues on GPT-5.6 models ([OpenAI, accessed 26 Sep 2026](https://developers.openai.com/api/docs/guides/tools-computer-use)).
- **Vol 2 Turn 95 (agent frameworks).** The turn is framed around framework brands. It misses the 2025–26 shift to vendor harness SDKs, whose permission hooks, stop conditions and resumable state are the safety-critical parts. Both model-vendor SDKs are still 0.x: openai-agents 0.22.3 and claude-agent-sdk 0.2.160 (npm 0.3.283). By contrast, google-adk is at 2.10.0 and agent-framework at 1.19.0 (PyPI, Sep 2026: [openai-agents](https://pypi.org/pypi/openai-agents/json), [claude-agent-sdk](https://pypi.org/pypi/claude-agent-sdk/json), [google-adk](https://pypi.org/pypi/google-adk/json), [agent-framework](https://pypi.org/pypi/agent-framework/json)).
  - *Change:* rewrite Turn 95 around harness primitives (AGT-1), with a comparison table of the Claude Agent SDK, OpenAI Agents SDK, ADK, MAF and LangGraph. Add a Q&A on pinning versions and wrapping 0.x SDKs in an adapter.
- **Gap doc #13 (distribution).** The item is framed around public directories. It misses the enterprise-tenant channels: Microsoft 365 Copilot and Teams, Gemini Enterprise, and Slack.
  - *Change:* keep it at P2 (P1 in accounts centred on Microsoft 365), not the finder's P1. Split it into a public-directory part and an enterprise-tenant part (AGT-5).
  - Use OpenAI's current naming: "plugins", in a Plugins Directory shared by ChatGPT and Codex.
  - Scope Slack's terms correctly: internal customer-built apps are exempt from the third-party clauses and the throttles.
  - Date MCP Apps correctly: it became an official extension on 26 Jan 2026, not "in 2026-07-28" ([MCP blog](https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/)).
- **Gap doc #18 (low-code builders).** The item covers only n8n exposure. It misses vendor-native builders and vendor churn (OpenAI Agent Builder: notice 3 Jun 2026, shutdown 30 Nov 2026), and it gives no KEV dates.
  - *Change:* broaden it as in AGT-9, and cite the KEV entries ([CISA KEV](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json)): Langflow CVE-2025-3248, added 5 May 2025; n8n CVE-2025-68613, added 11 Mar 2026; and Langflow's six entries through CVE-2026-9198 on 4 Aug 2026.
  - Drop the 647,017 figure, or re-attribute it: it is the attacker's FOFA result, quoted by [Unit 42, 30 Jul 2026](https://unit42.paloaltonetworks.com/autonomous-ai-cyber-attack-campaign/).
- **Gap doc "Looks missing but already covered" (Subagents: Turn 55; MCP Apps and generative UI: Turn 59).** This is only partly true. Turn 55 covers context isolation, costs and when not to use subagents, but not orchestration patterns: handoff, agents-as-tools and magentic have zero hits.
  - *Change:* extend Turn 55 with the pattern taxonomy (AGT-2); do not add a new turn. Add only one A2UI sentence and one Q&A to Turn 59 (AGT-10, Watch), because Q291 already teaches the catalogue idea.
- **Gap doc #17 (TypeScript stack).** A new turn would duplicate Turn 103 in another language. The npm evidence of scale is verified for 26 Aug to 24 Sep 2026:
  - 93.5M downloads for `ai`, the Vercel AI SDK ([npm](https://api.npmjs.org/downloads/point/2026-08-26:2026-09-24/ai));
  - 47.7M for `@anthropic-ai/claude-agent-sdk` ([npm](https://api.npmjs.org/downloads/point/2026-08-26:2026-09-24/@anthropic-ai/claude-agent-sdk));
  - 206M for `@modelcontextprotocol/sdk` ([npm](https://api.npmjs.org/downloads/point/2026-08-26:2026-09-24/@modelcontextprotocol/sdk)).

  The AI SDK's current major version is 7, not 6.
  - *Change:* extend Turn 103 into "Python and TypeScript Engineering for AI Apps", with side-by-side patterns for validation, streaming and approvals, and keep it P2. Do not claim a TypeScript majority, since the Python MCP SDK also passed 1B downloads.
- **Gap doc #7 (context engineering).** The OpenClaw compaction incident is cited to arXiv 2606.29175. That paper is about international humanitarian law and is not a primary source for the incident.
  - *Change:* cite a primary source, or a clearly labelled secondary post-mortem, for the 23 Feb 2026 incident. One example is [vectara/awesome-agent-failures](https://github.com/vectara/awesome-agent-failures/blob/main/docs/case-studies/openclaw-email-deletion.md).
- **Vol 2 Turns 57/58/59/91 (loop, cost and approval controls).** This is not a gap. Runaway spend, per-run budgets, stuck-agent detection, approval queues and durable waits are all covered as concepts. Only the harness-level APIs are missing: max-turn and budget stops, and interrupts that can be serialised.
  - *Change:* add no standalone turns for cost-runaway controls, human-in-the-loop or event-driven agents. Fold the API-level mechanics into the rewritten Turn 95 (AGT-1).
