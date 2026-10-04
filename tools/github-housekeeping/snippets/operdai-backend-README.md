# OperdAI Backend

FastAPI backend for **OperdAI**, a white-label autonomous inbound-lead agent platform: agencies, clients, leads, knowledge base, agent runs, billing, and webhooks.

## Stack

- Python 3.11+, FastAPI, SQLAlchemy (async), Alembic, Celery, Anthropic SDK
- PostgreSQL + pgvector (see `.env.example`)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # edit database and API keys
alembic upgrade head
```

## Run API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Tests

```bash
pytest
```

## Related

- Dashboard: [operdai-dashboard](https://github.com/nagarjunak-pixel/operdai-dashboard)
- Profile index: [nagarjunak-pixel](https://github.com/nagarjunak-pixel/nagarjunak-pixel)
