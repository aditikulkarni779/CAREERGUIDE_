# 13 — Weekly Execution Plan

Project: **AI Career Copilot** · Draft v1.0
Horizon: 24 weeks (6 months) → MVP in prod. Maps [12_ROADMAP_MILESTONES.md](./12_ROADMAP_MILESTONES.md) phases to concrete weekly work.

**Format per week:** Focus · Tasks · Deliverable · Exit check.
**Cadence assumptions:** small team / focused solo dev. Each week ends with: code merged, tests passing, docs + OpenAPI updated, demo-able slice.

---

## PHASE 0 — Foundations

### Week 1 — Repo, infra, config  *(expanded, day-by-day)*
- **Focus:** bootstrap dev env + acquire all free API keys.
- **Goal:** clean clone → one command → full local stack running at zero cost.

#### Day 1 — Repo + tooling
- `git init` monorepo per [03_TECH_STACK.md](./03_TECH_STACK.md): `apps/web`, `apps/api`, `packages/`, `infra`, `data`, `docs`.
- Root `.gitignore` (`.env`, `__pycache__`, `node_modules`, `.venv`, `*.pt` etc.); `README.md`; MIT license.
- `apps/api`: `pyproject.toml` (uv/poetry), Python 3.12 venv, deps: fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, alembic, structlog.
- `apps/web`: `create-next-app` (TS, App Router, Tailwind); add shadcn/ui init.
- **Check:** both apps install + build empty.

#### Day 2 — Free API keys + secrets scaffolding *(see key table below)*
- Sign up + generate every free-tier key from the table.
- `apps/api/app/core/config.py` — `pydantic-settings` `Settings` reading all env vars.
- `.env.example` (committed, placeholders) + local `.env` (gitignored, real keys).
- Verify each key with a tiny smoke script (`data/scripts/check_keys.py`): ping LLM, embeddings, Qdrant, Neo4j, GitHub.
- **Check:** all keys load; each provider responds 200.

#### Day 3 — Docker Compose (local datastores, all free)
- `infra/docker-compose.yml`: `postgres:16`, `redis:7`, `qdrant/qdrant`, `neo4j:5`, `minio` + healthchecks + named volumes.
- `.env` wires service URLs to compose hostnames.
- **Check:** `docker compose up` → all healthy; connect to each from host.

#### Day 4 — Config wiring + lint/format
- Pre-commit: ruff + black + mypy (py), eslint + prettier (ts); run on all files.
- Structured logging (structlog) + settings validation on api startup.
- `Makefile`/`justfile`: `dev`, `up`, `down`, `lint`, `test`, `fmt`.
- **Check:** `make lint` clean; api boots reading config.

#### Day 5 — CI + docs + verify
- GitHub Actions `ci.yml`: install → lint → typecheck → unit (empty) for api + web.
- Branch protection on `main`; PR template.
- `docs/dev-setup.md`: clone → keys → `compose up` → run.
- **Check:** CI green on a test PR.

- **Deliverable:** `compose up` brings up all datastores; both apps boot; all free keys validated; CI green.
- **Exit:** new machine → clone → fill `.env` from free keys → one command → working dev env.

---

#### Free API Keys & Services — Week 1 signup checklist
All zero-cost tiers. No credit card required except where noted. LLM + embeddings are behind ports ([03_TECH_STACK.md](./03_TECH_STACK.md)), so dev runs on **free** providers; swap to Claude/Voyage later without code change.

| Service | Purpose | Free tier | Get key | Card? |
|---------|---------|-----------|---------|-------|
| **Google Gemini API** | Dev LLM (primary free) | 15 RPM / 1M tokens-day free | aistudio.google.com/apikey | No |
| **Groq** | Dev LLM (fast, free Llama/others) | Generous free rate limit | console.groq.com/keys | No |
| **OpenRouter** | LLM router, some `:free` models | Free models available | openrouter.ai/keys | No |
| **Voyage AI** | Embeddings (target) | 200M free tokens | dash.voyageai.com | No |
| **Google Gemini embeddings** | Embeddings (free fallback) | Same Gemini free quota | (same key as above) | No |
| **HuggingFace / BGE (local)** | Offline embeddings, $0 | Unlimited local | huggingface.co/settings/tokens | No |
| **Qdrant Cloud** | Vector DB (or run local docker) | 1GB cluster free forever | cloud.qdrant.io | No |
| **Neo4j Aura Free** | Knowledge graph (or local docker) | 1 free instance | neo4j.com/cloud/aura-free | No |
| **Supabase** | Postgres + storage (or local docker) | 500MB DB + 1GB storage free | supabase.com | No |
| **Neon** | Serverless Postgres (alt) | Free branch/compute | neon.tech | No |
| **Upstash Redis** | Redis (or local docker) | 10k cmds/day free | upstash.com | No |
| **Cloudflare R2** | Object storage (S3-compat, alt to MinIO) | 10GB free/mo | dash.cloudflare.com | Yes* |
| **LangSmith** | LLM tracing/eval | Free personal (5k traces/mo) | smith.langchain.com | No |
| **GitHub OAuth App** | Login + repo analysis | Free | github.com/settings/developers | No |
| **GitHub PAT** | GitHub API (higher rate limit) | 5000 req/hr free | github.com/settings/tokens | No |
| **Google OAuth** | Login | Free | console.cloud.google.com | No |
| **Adzuna Jobs API** | Job market data | Free dev tier | developer.adzuna.com | No |
| **Remotive API** | Remote job listings | Free, no key | remotive.com/api/remote-jobs | No |
| **Kaggle** | Datasets (jobs, SO survey, courses) | Free | kaggle.com/settings (API token) | No |
| **arXiv / Semantic Scholar** | Research metadata | Free public API | api.semanticscholar.org | No |

\* R2 asks for a card but the 10GB tier is free — or skip it entirely and use **local MinIO** in Compose ($0, no signup).

**Zero-signup local path (recommended for Week 1):** run Postgres, Redis, Qdrant, Neo4j, MinIO all in Docker Compose → only keys actually needed are **Gemini/Groq** (LLM) + **GitHub PAT** + **Google/GitHub OAuth**. Cloud tiers above are for staging or if you skip local Docker.

**`.env.example` keys to add this week:**
```
ENV=local
# LLM (free dev)
LLM_PROVIDER=gemini            # gemini | groq | openrouter | anthropic
GEMINI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
ANTHROPIC_API_KEY=            # add later for prod tiering
# Embeddings
EMBED_PROVIDER=gemini          # gemini | voyage | bge_local
VOYAGE_API_KEY=
# Datastores (local docker defaults)
DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/app
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=career-copilot
# Integrations
GITHUB_TOKEN=
OAUTH_GITHUB_ID=
OAUTH_GITHUB_SECRET=
OAUTH_GOOGLE_ID=
OAUTH_GOOGLE_SECRET=
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
# Observability
LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
# Auth
JWT_SECRET=
NEXTAUTH_SECRET=
```

**Security note (do now, not later):** never commit `.env`; add gitleaks to pre-commit; rotate any key accidentally pushed. Only `.env.example` (placeholders) is committed.

### Week 2 — Skeleton apps + auth
- **Focus:** runnable web+api + auth.
- **Tasks:**
  - FastAPI app factory, health/readiness, structured logging, error handler (problem+json).
  - Alembic baseline; `users` table.
  - Auth: register/login, JWT access+refresh, password hashing, OAuth (Google/GitHub), `/auth/me`, RBAC middleware.
  - Next.js skeleton (App Router, Tailwind, shadcn), Auth.js wired, login page.
  - Unit + integration tests for auth (testcontainers Postgres).
- **Deliverable:** login flow web→api works end to end.
- **Exit:** **M1** — infra + auth running, CI runs unit+integration.

---

## PHASE 1 — Career Twin & Onboarding

### Week 3 — Profile schema + skill taxonomy
- **Tasks:**
  - Migrations: `profiles`, `skills`, `user_skills`, `roles`, `role_skill_requirements`.
  - Seed skill taxonomy (ESCO/O*NET subset) + role reqs for 8 target roles.
  - Skill canonicalization service (alias table + embedding match) + unit tests.
  - Profile CRUD endpoints (`GET/PUT /profile`).
- **Deliverable:** seeded taxonomy + profile API.
- **Exit:** can create/read a profile; skills normalize to canonical ids.

### Week 4 — Onboarding + Twin + readiness v1
- **Tasks:**
  - `POST /profile/onboarding`; Career Twin builder + `twin_version`.
  - Readiness score v1 (skills-only) + `readiness_scores` table.
  - Onboarding wizard UI (6 steps, autosave, progress).
  - Dashboard shell + Skill Radar + readiness gauge.
- **Deliverable:** onboarding → Twin persisted → dashboard renders.
- **Exit:** **M2** — Career Twin + onboarding done; e2e journey #1 passes.

---

## PHASE 2 — RAG Core

### Week 5 — Vector infra + embeddings
- **Tasks:**
  - Ports: `Embedder`, `VectorStore`, `Reranker`, `Retriever` ([06_RAG_PIPELINE.md](./06_RAG_PIPELINE.md)).
  - Adapters: Voyage embedder (+BGE fallback), Qdrant hybrid (dense+sparse), reranker.
  - Chunker + normalizer; embedding cache (Redis, content hash).
  - Qdrant collections created w/ payload indexes.
- **Deliverable:** ingest→embed→search working on a sample set.
- **Exit:** hybrid search returns relevant filtered chunks.

### Week 6 — First KB + retriever + eval baseline
- **Tasks:**
  - Ingest roadmaps.sh + sample course catalog + O*NET role reqs → `roadmap_kb`, `resources`.
  - Retriever orchestration (rewrite→hybrid→filter→rerank→assemble) + citation assembly.
  - RAG eval harness (Ragas) + golden Q/A set (per role) in CI.
- **Deliverable:** grounded, cited retrieval + recorded eval baseline.
- **Exit:** **M3** — `retrieve()` cited + faithfulness baseline logged.

---

## PHASE 3 — Agent Orchestrator + Chat

### Week 7 — LangGraph core + Planner/Chat
- **Tasks:**
  - `CopilotState` + `StateGraph`; Planner (intent routing) + Chat agent.
  - LLM adapter w/ tiering (Haiku/Sonnet/Opus) + prompt-cache + token budget.
  - Tools as typed adapters (`retrieve`, `get_twin`, `graph_query` stub).
  - LangSmith tracing wired.
- **Deliverable:** router graph answers general QA over RAG.
- **Exit:** planner routes; chat answers grounded.

### Week 8 — Streaming chat + memory + guards
- **Tasks:**
  - SSE streaming (`token/agent_step/citation/done`); WS alt.
  - `conversations`/`messages` persistence; long-term memory (`user_memory` summarize+embed).
  - Citation + Verification agents (gate output, loop-back max N).
- **Deliverable:** full streaming chat with citations + memory.
- **Exit:** chat persists, remembers, cites; verification blocks unsupported claims.

### Week 9 — Skill Gap + Roadmap agents (flagship)
- **Tasks:**
  - Skill Gap agent (Twin vs role reqs → scored gaps: importance/time/order/difficulty/confidence).
  - Roadmap agent (sequence via Neo4j `PREREQUISITE_OF` + weekly hours); `roadmaps`/`roadmap_items` versioned.
  - Skill-path sub-workflow end to end; `/gap-analysis`, `/roadmap/*`.
- **Deliverable:** "become an ML Engineer" → streamed answer + roadmap + citations + explanations.
- **Exit:** **M4** — flagship demo; e2e journey #2 passes.

---

## PHASE 4 — Frontend Depth

### Week 10 — Dashboard widgets
- **Tasks:** `ScoreGauge`, `SkillRadar`, `GapHeatmap`, `RoadmapTimeline` components (Recharts/visx); wire to `/dashboard`, `/profile/readiness`.
- **Deliverable:** data-rich dashboard.
- **Exit:** dashboard renders real Twin data.

### Week 11 — Chat UI + roadmap + skills pages
- **Tasks:**
  - Chat UI polish: streaming, collapsible reasoning steps, `RecommendationCard`, `WhyPopover`.
  - Roadmap page (status toggles, versions, re-plan button); Skills force-graph view.
  - Responsive + a11y pass (WCAG 2.1 AA, ARIA on charts, ⌘K palette).
- **Deliverable:** startup-quality chat + roadmap + skills UI.
- **Exit:** **M5** — polished UI; a11y + responsive checks pass.

---

## PHASE 5 — Resume & GitHub Intelligence

### Week 12 — Resume pipeline
- **Tasks:**
  - Upload → MinIO → Celery parse (PDF/DOCX); `resumes` table.
  - Skill Extraction agent → update Twin evidence.
  - ATS scorer (deterministic) + weak-section detector (LLM); `resume_scores`.
- **Deliverable:** upload → ATS score + parsed skills.
- **Exit:** resume feeds Twin + score.

### Week 13 — Resume rewrite + GitHub agent
- **Tasks:**
  - Resume agent bullet rewrite / keyword suggestions; before/after diff UI + gauge.
  - GitHub agent: fetch repos/commits, 4 scores (health/repo/diversity/recruiter), cache 24h; `github_*` tables + UI.
- **Deliverable:** resume rewrite + GitHub scores.
- **Exit:** e2e journeys #3, #4 pass.

### Week 14 — Readiness integration + buffer
- **Tasks:**
  - Readiness v2: fold resume + github + learning components; explainable breakdown.
  - Resume/GitHub UI polish; integration tests; **catch-up buffer** for Phase 3–5 slippage.
- **Deliverable:** composite readiness score with component drill-down.
- **Exit:** **M6** — resume + GitHub intelligence complete.

---

## PHASE 6 — Recommendations + Data Pipelines

### Week 15 — Knowledge graph + graph recs
- **Tasks:**
  - Populate Neo4j (Skills/Courses/Projects/Jobs/Companies + edges).
  - Graph queries: prerequisite paths, co-demand, company relevance.
  - Recommendation engine skeleton (content + semantic + graph).
- **Deliverable:** graph-backed recommendations.
- **Exit:** `/recommendations` returns graph+semantic results.

### Week 16 — Hybrid recs + explanations + feedback
- **Tasks:**
  - Add collaborative signal (feedback aggregation) + LLM reasoning fusion; configurable weights.
  - Enforce explanation schema (`why/gap/impact/confidence`); Verification rejects missing rationale.
  - `POST /recommendations/{id}/feedback`; recommendation history.
- **Deliverable:** fully hybrid, explained recommendations.
- **Exit:** every rec card has a Why; feedback loop live.

### Week 17 — Ingestion pipelines + trends
- **Tasks:**
  - Celery-beat: nightly job ingest, weekly course sync (medallion bronze/silver/gold).
  - Trend/demand signals → Neo4j `TRENDING` + `market_signals`; `/market/*` endpoints + dashboard widget.
  - Data-quality checks + provenance; dead-letter queue.
- **Deliverable:** automated pipelines + live market trends.
- **Exit:** **M7** — nightly pipeline healthy; trends on dashboard.

---

## PHASE 7 — Adaptive & Engagement

### Week 18 — Adaptive re-plan
- **Tasks:**
  - `TwinUpdated` events; re-plan on item complete/skip + nightly market shift.
  - Roadmap diff + new version + reason; Notification agent alert.
- **Deliverable:** self-updating roadmap.
- **Exit:** completing/skipping items re-plans with explanation; journey #5 passes.

### Week 19 — Weekly Mentor + notifications + gamification
- **Tasks:**
  - Analytics agent aggregation → Report agent (Opus) weekly report → `/mentor/weekly` + PDF export.
  - Notifications (deadlines/new courses/trends/hackathons/Kaggle) + UI.
  - Gamification: XP/badges/streaks/milestones; `gamification_events`.
- **Deliverable:** weekly report + notifications + gamification.
- **Exit:** report generates; notifications fire; streaks tracked.

### Week 20 — Interview prep
- **Tasks:**
  - Interview session generation (technical/HR/coding/system-design/ML) + scoring + hints (agents).
  - `interview_sessions`/`interview_questions`; UI (question→answer→feedback→summary radar).
- **Deliverable:** interview module.
- **Exit:** **M8** — adaptive + engagement + interview live.

---

## PHASE 8 — Hardening & Launch

### Week 21 — Project recommendation + company prep
- **Tasks:**
  - Project Recommendation (portfolio-gap driven) + AI Project Architect (folder/tech/schema/timeline).
  - Company-specific prep plans (`/market/companies/{name}`).
- **Deliverable:** projects + company prep features.
- **Exit:** project specs + company plans generate.

### Week 22 — Observability + LLMOps + cost
- **Tasks:**
  - Grafana dashboards + alerts (latency, error, queue, tokens/cost, cache).
  - OpenTelemetry traces; LangSmith prompt versioning + eval gates in CI.
  - Cost governance: token budgets, tiering audit, cost dashboard + alerts.
- **Deliverable:** full observability + LLMOps gates.
- **Exit:** dashboards live; eval gates block bad prompt/model rollouts.

### Week 23 — Security + load + data-quality hardening
- **Tasks:**
  - Security: SAST (bandit/semgrep), deps (pip-audit/npm audit), gitleaks, ZAP baseline, authz tests, prompt-injection defenses.
  - Load tests (k6/Locust) on chat+retrieval → verify SLAs + autoscale.
  - Backup/DR runbook tested (Postgres PITR, Qdrant/Neo4j snapshots).
- **Deliverable:** security + load + DR verified.
- **Exit:** SLA targets met; no high/critical vulns; restore tested.

### Week 24 — Docs, deploy, launch
- **Tasks:**
  - MkDocs site + README + demo/seed data; final OpenAPI.
  - Deploy staging→prod (blue/green), smoke + e2e, post-deploy health gate.
  - Verify all SRS §7 acceptance criteria; runbooks + on-call.
- **Deliverable:** MVP in production.
- **Exit:** **M9** — hardened, observable, deployed; acceptance met.

---

## Weekly Operating Rhythm
- **Mon:** plan week, refine tickets from this doc.
- **Daily:** small PRs, CI green before merge.
- **Wed:** mid-week eval run if LLM-facing changes.
- **Fri:** demo the slice, update docs/OpenAPI, retro + adjust next week.

## Definition of Done (every week)
Merged code · unit+integration tests · e2e for the phase journey · docs+OpenAPI updated · LLM eval pass (if applicable) · observability (logs/metrics/trace) · demo recorded.

## Buffers & Risk
- Week 14 is explicit catch-up buffer.
- If behind: protect **M1–M4** (demo core); defer Phase 6–8 breadth to post-MVP backlog.
- Parallelize: frontend (Phase 4) can overlap backend Phase 3 if two devs.

## Solo-Dev Compression (if needed)
Cut to 12–14 weeks by shipping only M1–M5 + minimal recs (Week 15–16) and deferring pipelines/adaptive/interview/hardening breadth. Flagship demo (M4) still lands by ~Week 9.
