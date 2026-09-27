# Starter kits

One offline kit per project brief. Each kit gives a team a working day-one scaffold, so the course build starts from measured failure instead of a blank repo.

**What each kit contains:**
- `generate_data.py`: a deterministic synthetic-data generator. It follows the brief's §3 spec, with the tricky cases and curveball fixtures labelled so they can be scored separately.
- The brief's §7 control as an importable module, with the reviewer fixes kept and tested.
- `baseline.py`: a deliberately simple, non-LLM baseline behind the same interface a real system would use.
- `adapter.py`: a stub for plugging in a real model through any OpenAI-compatible endpoint (Ollama, vLLM or a hosted API).
- `eval_harness.py`: scores the baseline against the brief's §5 acceptance criteria and prints `AC-ID | metric | value | threshold | result`.

**What the kits are not:**
- **Not solutions.** Every baseline fails several acceptance criteria. That is by design: students replace the baseline and watch the numbers move.
- **Not complete.** Criteria that need humans, real users or production traffic are printed as "not computable offline" rather than faked.
- **Not networked.** No default path makes a network call or needs an API key. `adapter.py` runs only with `--system adapter` and environment variables.

## Run a kit

Requirements: Python 3.11 with the standard library only. Two exceptions: P02 also needs `duckdb` and `sqlglot`; P13 is TypeScript and needs Node 22, with no `npm install`.

From inside a kit folder:

```bash
python3 generate_data.py                  # writes ./data/ in seconds; --scale N for larger runs
python3 -m unittest discover -s tests -v  # the control and the generator
python3 eval_harness.py                   # scores the baseline; writes ./results/; exits 0 even when thresholds fail
```

P13:

```bash
node --experimental-strip-types generate_data.ts
node --experimental-strip-types --test tests/*.test.ts
node --experimental-strip-types eval_harness.ts
```

`data/` and `results/` are git-ignored. Each kit's README maps every harness metric to the brief's acceptance-criterion ID and threshold. It also says what to build next, by phase and week.

## The kits

| Kit | Brief | §7 control | Tests |
|---|---|---|---|
| [P01](P01-permission-aware-knowledge-assistant/README.md) | [Permission-aware knowledge assistant](../P01-permission-aware-knowledge-assistant.md) | `permission_trim.py` | 17 |
| [P02](P02-text-to-sql-analytics-agent/README.md) | [Text-to-SQL analytics agent](../P02-text-to-sql-analytics-agent.md) | `sql_guard.py`, `semantic_layer.py` | 20 |
| [P03](P03-claims-intake-document-ai/README.md) | [Claims-intake document AI](../P03-claims-intake-document-ai.md) | `review_router.py` | 27 |
| [P04](P04-contact-centre-voice-agent/README.md) | [Contact-centre voice agent](../P04-contact-centre-voice-agent.md) | `turn_manager.py` | 24 |
| [P05](P05-computer-use-agent-replacing-rpa/README.md) | [Computer-use agent replacing RPA](../P05-computer-use-agent-replacing-rpa.md) | `action_gate.py`, `mock_portal.py` | 27 |
| [P06](P06-injection-resistant-inbox-agent/README.md) | [Injection-resistant inbox agent](../P06-injection-resistant-inbox-agent.md) | `dataflow_policy.py` | 25 |
| [P07](P07-ai-vulnerability-triage-and-patch-pipeline/README.md) | [AI vulnerability triage and patch pipeline](../P07-ai-vulnerability-triage-and-patch-pipeline.md) | `cra_clock.py` | 30 |
| [P08](P08-sovereign-air-gapped-llm-platform/README.md) | [Sovereign, air-gapped LLM platform](../P08-sovereign-air-gapped-llm-platform.md) | `bundle_verifier.py`, `kv_capacity.py` | 36 |
| [P09](P09-legacy-modernisation-with-coding-agents/README.md) | [Legacy modernisation with coding agents](../P09-legacy-modernisation-with-coding-agents.md) | `diff_harness.py`, `legacy_prmcalc.py` | 16 |
| [P10](P10-ambient-clinical-documentation/README.md) | [Ambient clinical documentation](../P10-ambient-clinical-documentation.md) | `note_verifier.py` | 21 |
| [P11](P11-teen-safe-study-companion-compliance/README.md) | [Teen-safe study companion](../P11-teen-safe-study-companion-compliance.md) | `flip_rate.py` | 24 |
| [P12](P12-enterprise-ai-gateway-finops-platform/README.md) | [Enterprise AI gateway and FinOps](../P12-enterprise-ai-gateway-finops-platform.md) | `router.py` | 27 |
| [P13](P13-agent-ready-commerce-mcp/README.md) | [Agent-ready commerce (TypeScript)](../P13-agent-ready-commerce-mcp.md) | `add_to_cart.ts` | 16 |
| [P14](P14-multilingual-citizen-services-assistant/README.md) | [Multilingual citizen-services assistant](../P14-multilingual-citizen-services-assistant.md) | `language_gate.py`, `mock_status_api.py` | 22 |
| [P15](P15-distilled-domain-small-model-offline/README.md) | [Distilled domain small model](../P15-distilled-domain-small-model-offline.md) | `synth_filter.py` | 23 |
| [P16](P16-due-diligence-deep-research-agent/README.md) | [Due-diligence deep-research agent](../P16-due-diligence-deep-research-agent.md) | `citation_verifier.py` | 16 |

That is 371 tests in total. All kits were verified from a fresh clone: data generation, tests and harness pass for each.

## Known limitations

- **Size.** Kits run to about 900–1,700 lines of code each (tests included), above the 700-line target. Most of the excess is tests and curveball fixtures. They were kept because they pin the bugs the review pass found in the brief sketches.
- **Offline proxies.** Several metrics use lexical proxies. For example, faithfulness is token overlap with the cited text, so P01's extractive baseline passes AC-5 trivially. Treat a proxy PASS as a smoke test, not evidence; the briefs' §8 evaluation plans, with calibrated judges, still apply.
- **P04.** The §7 turn manager has a known gap, noted in its README: when a model stream dies mid-sentence, it still speaks the fragment it holds. Deciding whether to drop the fragment and apologise instead is left to students.
