# GitHub account housekeeping

Audit and automation for all **36 public repositories** under [nagarjunak-pixel](https://github.com/nagarjunak-pixel).

The Cloud Agent token can only push to **02-autogpt-autonomous-agent**. Run **`apply-all.sh`** on your machine after `gh auth login` (your user account, not the bot).

## One command (recommended)

```bash
./tools/github-housekeeping/apply-all.sh
```

This runs, in order:

1. Strip committed `.venv/` from four Python repos  
2. Strip committed `node_modules/` from `spring-boot-mcp`  
3. Add READMEs (`noah-animal-clinic`, `venkatesh-llm`, `operdai-backend`)  
4. Add Python `.gitignore` to `ai-calc` and `pytorch-interactive-demo`  
5. Publish [profile-README.md](profile-README.md) to the profile repo  
6. Apply [descriptions.tsv](descriptions.tsv)  
7. Apply [topics.tsv](topics.tsv)  
8. Print [audit-remote.sh](audit-remote.sh) summary  

## Check status without changing anything

```bash
./tools/github-housekeeping/audit-remote.sh
```

## Audit summary (October 2026)

| Issue | Repositories |
| --- | --- |
| Committed `.venv/` | `antigravity-sdk`, `localaitv-mcp-server`, `operdai-backend`, `tokens-eat-up` |
| Committed `node_modules/` | `spring-boot-mcp` |
| Committed `*.egg-info/` | `operdai-backend` |
| No root `.gitignore` | `ai-calc`, `pytorch-interactive-demo` (**fixed** in `02-autogpt-autonomous-agent`) |
| No `README.md` | `noah-animal-clinic`, `venkatesh-llm` |
| Thin / auto-generated README | Several Vite and Python prototypes |

## Individual scripts

| Script | Purpose |
| --- | --- |
| [strip-tracked-venv.sh](strip-tracked-venv.sh) | `git rm --cached` for `.venv/` |
| [strip-tracked-node-modules.sh](strip-tracked-node-modules.sh) | `git rm --cached` for `node_modules/` |
| [add-missing-readmes.sh](add-missing-readmes.sh) | Copy from [snippets/](snippets/) |
| [add-python-gitignore.sh](add-python-gitignore.sh) | Append [snippets/python-gitignore](snippets/python-gitignore) |
| [publish-profile-index.sh](publish-profile-index.sh) | Update `nagarjunak-pixel` profile README |
| [set-descriptions.sh](set-descriptions.sh) | `gh repo edit --description` from TSV |
| [set-topics.sh](set-topics.sh) | `gh repo edit --add-topic` from TSV |

## Optional next steps

- [ARCHIVE-CANDIDATES.md](ARCHIVE-CANDIDATES.md) — repos you may want to archive  
- [profile-README.md](profile-README.md) — full grouped index (also published by `publish-profile-index.sh`)  
- **CI on this repo:** `.github/workflows/starter-kits.yml` runs Python + P13 tests on kit changes  

## Granting the Cloud Agent write access

To let a Cloud Agent open PRs on every repo automatically, add the agent installation or a fine-grained PAT with **Contents: write** on `nagarjunak-pixel/*`, then re-run this agent with “continue account cleanup.”
