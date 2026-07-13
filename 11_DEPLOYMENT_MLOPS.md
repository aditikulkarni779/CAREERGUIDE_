# 11 — Deployment, CI/CD & MLOps

Project: **AI Career Copilot** · Draft v1.0

---

## 1. Environments
| Env | Purpose | Data |
|-----|---------|------|
| local | dev via Docker Compose | seeded/synthetic |
| staging | pre-prod, full pipelines | sampled datasets |
| prod | live | full |

12-factor config via env; secrets from vault/secret manager (never in repo).

---

## 2. Containers (Docker Compose — dev)
Services: `web` (Next.js), `api` (FastAPI/uvicorn), `worker` + `beat` (Celery), `postgres`, `redis`, `qdrant`, `neo4j`, `minio`, `prometheus`, `grafana`.
Each app image multi-stage (build → slim runtime), non-root user, healthchecks.

```
compose up → migrations (alembic) → seed → app ready at :3000/:8000
```

---

## 3. CI/CD (GitHub Actions)
```
CI:  lint+typecheck → unit → integration(testcontainers) → LLM eval(subset)
     → build & scan images → push to registry
CD:  staging auto-deploy on main → smoke/e2e → manual approve → prod
     → run migrations → blue/green or rolling → post-deploy health gate
Rollback: keep previous image; one-command revert; DB migrations backward-safe.
```

Prod target options: managed containers (Fly.io / Render / ECS) for MVP → Kubernetes (Helm) when scale demands. Managed Postgres + managed Qdrant/Neo4j Aura optional.

---

## 4. Observability
- **Logs**: structlog JSON → aggregator (Loki/ELK); request/trace ids correlated.
- **Metrics**: Prometheus (latency, error rate, queue depth, LLM tokens/cost, cache hit) → Grafana dashboards + alerts.
- **Traces**: OpenTelemetry across API→agents→stores.
- **LLM observability**: LangSmith — per-agent traces, token/cost, eval runs, prompt versioning.
- **Alerting**: SLA breach, pipeline freshness, error spikes, cost anomaly → on-call channel.

---

## 5. MLOps / LLMOps
- **Prompt management**: versioned prompts in repo; A/B + canary on prompt changes; LangSmith tracks quality per version.
- **Model registry (light)**: config-driven model/tier selection; pin model ids; changelog on upgrades.
- **Eval-in-CI**: golden-set regression gates (see [10_TESTING_STRATEGY.md](./10_TESTING_STRATEGY.md)) before prompt/model rollout.
- **Data/embedding versioning**: track embedding model + ingestion version; re-embed migration path on model change (dual-write + backfill).
- **Feedback loop**: recommendation 👍/👎 + roadmap outcomes logged → periodic re-tuning of ranking weights.
- **Cost governance**: per-request token budgets, tiering, caching, daily cost dashboard + alerts.

---

## 6. Security & Compliance
- JWT (short access + rotating refresh), OAuth, RBAC middleware.
- Secrets via manager; TLS everywhere; encrypted at rest (resume/PII, MinIO SSE).
- Rate limiting + WAF (managed) + input validation (pydantic) + output sanitization.
- Prompt-injection defenses: retrieved content is untrusted, tool calls schema-constrained, no secret in prompts, allowlist tools.
- GDPR-style data export + hard delete endpoints; audit log of admin actions.
- Regular dependency + image scanning; least-privilege service accounts.

---

## 7. Backups & DR
- Postgres PITR + nightly dumps; Neo4j + Qdrant snapshots; MinIO versioning.
- Restore runbook tested; RPO ≤ 24h, RTO ≤ 4h (MVP targets).

---

## 8. Scaling Path
- Stateless `api` + `web` scale horizontally behind LB.
- Celery workers scale by queue depth.
- Qdrant/Neo4j vertical first → clustered later.
- Semantic + prompt caching absorb LLM load; read replicas for Postgres when needed.
- Extract high-traffic modules (chat, ingestion) to services when the monolith seams strain.
