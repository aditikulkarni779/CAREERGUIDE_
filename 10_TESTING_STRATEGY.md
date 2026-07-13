# 10 — Testing & Evaluation Strategy

Project: **AI Career Copilot** · Draft v1.0

---

## 1. Test Pyramid

```
        ▲  E2E (Playwright) — few, critical journeys
       ▲▲  Integration (API + DB + vector/graph, testcontainers)
      ▲▲▲  Unit (domain logic, scorers, parsers) — many, fast
   ───────  LLM/Agent Evals (offline, gated in CI)
```

---

## 2. Unit Tests (pytest)
- Domain entities, value objects, readiness/ATS/GitHub scoring math (deterministic, mocked LLM).
- Skill canonicalization + dedup.
- RAG chunkers, filter builders, RRF fusion.
- Target: >80% on `domain/` + `services/` scoring.

## 3. Integration Tests
- FastAPI routers via `httpx.AsyncClient`.
- Real Postgres/Qdrant/Neo4j/Redis via **testcontainers** (ephemeral).
- Celery tasks tested with eager mode + a broker container.
- Auth/RBAC, rate limiting, idempotency, error contract (problem+json).

## 4. E2E (Playwright)
Critical journeys:
1. Register → onboarding → Twin built → dashboard renders.
2. Chat skill-path → roadmap appears w/ citations + explanations.
3. Resume upload → ATS score + rewrite.
4. GitHub analyze → scores.
5. Roadmap item complete → re-plan + notification.

## 5. LLM / Agent Evaluation
- **Frameworks**: Ragas + DeepEval; LangSmith datasets for regression.
- **RAG metrics**: context precision/recall, faithfulness, answer relevancy, citation coverage.
- **Agent metrics**: routing accuracy (intent), task success rate, rationale completeness (every recommendation has why/gap/impact/confidence), hallucination rate.
- **Golden sets**: curated Q/A per role; run on any prompt/model/retrieval change.
- **LLM-as-judge** (Opus) for rubric scoring of roadmaps/resume rewrites, human spot-check calibration.
- **Release gates**: faithfulness ≥ target, hallucination ≤ threshold, routing accuracy ≥ target — CI fails otherwise.

## 6. Non-Functional Testing
- **Load**: Locust/k6 on chat + retrieval; verify p95 SLAs, autoscale behavior.
- **Security**: dependency scan (pip-audit, npm audit), SAST (bandit, semgrep), secret scanning (gitleaks), OWASP ZAP baseline, authz tests (horizontal/vertical access).
- **Data quality**: pipeline freshness/nulls/row-count assertions (Great Expectations-style checks).
- **Cost regression**: track tokens/request in eval; alert on >X% drift.

## 7. Test Data & Fixtures
- Synthetic profiles/resumes/GitHub fixtures (no real PII).
- Seed catalogs for deterministic recommendation tests.
- Frozen embedding fixtures (recorded) to keep unit tests offline.

## 8. CI Wiring
```
push/PR → lint (ruff, mypy, eslint, tsc)
        → unit → integration (testcontainers)
        → LLM eval (subset, cached) on prompt/rag/model changes
        → build images → e2e (compose) on main
        → security scans
Coverage + eval reports uploaded as artifacts; gates enforced.
```

## 9. Definition of Done (per feature)
Code + unit/integration tests + docs + OpenAPI updated + eval pass (if LLM-facing) + observability (logs/metrics/trace) + reviewed.
