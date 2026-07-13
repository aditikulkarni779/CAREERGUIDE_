# API — AI Career Copilot

FastAPI backend. Clean architecture: `domain` (framework-free) ← `services` ← `adapters`/`api`.

## Dev
```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
# http://localhost:8000/api/v1/health  ·  /docs
pytest -q
ruff check . && mypy app
```
