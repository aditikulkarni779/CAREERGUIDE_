# Dev Setup

## Prereqs
- Python 3.10+ · Node 22+ · Docker Desktop (for datastores)

## 1. Clone + env
```bash
git clone <repo> && cd CareerGuide
cp .env.example .env      # fill in free keys (see 13_EXECUTION_PLAN.md Week 1 table)
```
Minimum keys for local dev: `GEMINI_API_KEY` (or `GROQ_API_KEY`), `GITHUB_TOKEN`.

## 2. Datastores (Docker)
```bash
make up          # postgres, redis, qdrant, neo4j, minio
```
Consoles: Qdrant :6333 · Neo4j :7474 · MinIO :9001

## 3. API
```bash
cd apps/api
python -m venv .venv && . .venv/Scripts/activate   # win; use bin/activate on unix
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
# http://localhost:8000/api/v1/health  ·  /docs
pytest -q
```

## 4. Web
```bash
cd apps/web
npm install
npm run dev        # http://localhost:3000
```

## 5. Validate keys
```bash
python data/scripts/check_keys.py
```

## 6. Pre-commit
```bash
pip install pre-commit && pre-commit install
```

## Handy
```bash
make up | down | api | web | lint | fmt | test
```
