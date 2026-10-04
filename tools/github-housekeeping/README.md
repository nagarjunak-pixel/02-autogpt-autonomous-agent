# GitHub account housekeeping

This folder captures an **audit of all 36 public repositories** under [nagarjunak-pixel](https://github.com/nagarjunak-pixel) and scripts to apply the same hygiene everywhere.

The Cloud Agent token can only push to **02-autogpt-autonomous-agent**. Run the scripts below from your machine (or any environment with `gh auth login` and write access to your repos).

## Audit summary (October 2026)

| Issue | Repositories |
| --- | --- |
| Committed `.venv/` | `antigravity-sdk`, `localaitv-mcp-server`, `operdai-backend`, `tokens-eat-up` |
| Committed `node_modules/` | `spring-boot-mcp` |
| Committed `*.egg-info/` | `operdai-backend` |
| No root `.gitignore` | `02-autogpt-autonomous-agent` (fixed in this repo), `ai-calc`, `pytorch-interactive-demo` |
| No `README.md` | `noah-animal-clinic`, `venkatesh-llm` |
| Thin / auto-generated README | Several Vite and Python prototypes (e.g. `fable-5`, `agentforge`, `operdai-backend`) |

## Quick commands

```bash
# 1. Install GitHub CLI and authenticate
gh auth login

# 2. Stop tracking virtualenvs (run once per affected repo)
./tools/github-housekeeping/strip-tracked-venv.sh operdai-backend antigravity-sdk localaitv-mcp-server tokens-eat-up

# 3. Stop tracking node_modules
./tools/github-housekeeping/strip-tracked-node-modules.sh spring-boot-mcp

# 4. Update your profile index (review, then copy)
cp tools/github-housekeeping/profile-README.md /path/to/nagarjunak-pixel/README.md
```

## Profile index

See [profile-README.md](profile-README.md) for a complete grouped index of all public repositories (teaching, AY Automate, products, experiments, forks).

## Suggested GitHub descriptions

Run with `gh repo edit nagarjunak-pixel/<name> --description "..."`:

| Repository | Suggested description |
| --- | --- |
| `operdai-backend` | OperdAI FastAPI backend — white-label autonomous inbound-lead agent platform |
| `operdai-dashboard` | OperdAI web dashboard for agencies and lead workflows |
| `fable-5` | React + Vite UI experiment (Fable 5) |
| `agentforge` | AgentForge — React dashboard prototype for agent tooling |
| `agentic-academy` | Agentic Academy course harness and agent loops |
| `ai-workforce` | Multi-agent workforce simulation harness |
| `smart-marketing-assistant` | Smart marketing assistant prototype |
| `tokens-eat-up` | Token usage visualization experiment |
| `loop-engineering-trading` | Loop engineering patterns for trading experiments |
| `anti-gravity-game` | Browser anti-gravity game demo |
| `spring-boot-mcp` | Spring Boot sample exposing MCP tools |
| `antigravity-sdk` | Antigravity SDK experiments and samples |
