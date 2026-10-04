# Venkatesh LLM

Educational ~1.03M-parameter language model demo: corpus → tokenizer → train → infer → Ollama Q&A.

## Documentation

Full build narrative: [HOW_WE_BUILT_THIS.md](HOW_WE_BUILT_THIS.md) (HTML: `how_we_built_this.html`).

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python ask.py
```

Pretrained weights live in `checkpoints/checkpoint.pt`. Training logs: `loss_log.jsonl`, `loss_curve.svg`.

## Ollama

See the `ollama/` folder for Modelfile and packaging notes.
