# Progress Log

Running log of build progress against [13_EXECUTION_PLAN.md](./13_EXECUTION_PLAN.md).
Newest entries at top. One entry per work session/day.

**Legend:** ✅ done · 🟡 partial · ⛔ blocked · ⏭️ deferred

---

## Status Snapshot
- **Current phase:** Phase 3 (Agent Orchestrator + Chat)
- **Milestones hit:** M1 (infra+auth), M2 (Twin+onboarding), M3 (grounded RAG + citations + eval baseline)
- **Next up:** Week 8 — streaming chat (SSE) + conversation persistence + long-term memory
- **Stack live:** Postgres, Redis, Qdrant, Neo4j, MinIO (Docker, all healthy)
- **Repo:** github.com/aditikulkarni779/CAREERGUIDE_ (main pushed through W4)
- **Test count:** 32 passing (sqlite + in-memory Qdrant + FakeLLM) · ruff + mypy clean
- **Migrations applied:** 0001 (users), 0002 (profiles/skills/roles), 0003 (readiness_scores)
- **Seed data:** 46 skills, 8 roles, 60 role reqs; roadmap_kb: 6 RAG chunks
- **Embeddings:** BGE-local + BM25 + local cross-encoder reranker — offline, no keys
- **LLM:** Gemini (dev) / Anthropic — behind port; ⚠ dev Gemini key returns 429 on generateContent (free quota)
- **RAG eval baseline:** hit@1 1.0, MRR 1.0, recall@5 1.0 (n=10)

---

## Week 7 — LangGraph + Planner/Chat Agents  ✅ (code) · ⚠ live LLM blocked
**Goal:** planner routes; chat answers grounded.

- ✅ LLM port + adapters: Gemini (httpx, retry/backoff on 429/503), Anthropic (httpx), FakeLLM for tests.
- ✅ LLM tiering (fast/balanced/deep) + provider factory.
- ✅ Planner agent: LLM JSON intent classification + keyword heuristic fallback.
- ✅ Chat agent: retrieve → format context → grounded answer with [n] citations.
- ✅ LangGraph StateGraph: planner → chat; role-aware retrieval filter + unfiltered fallback.
- ✅ Orchestrator singleton + `POST /chat/ask` endpoint (authed, non-streaming).
- ✅ 4 agent tests (32 total) with FakeLLM + in-memory Qdrant — full graph verified. ruff + mypy clean.
- ⚠ **Live Gemini blocked:** free-tier `generateContent` returns 429 for the dev key (models.list 200 is a separate looser quota). Pipeline wiring proven by unit tests; live green pending a working LLM key.
- **Exit:** planner routes + chat answers grounded — verified with FakeLLM; live LLM run pending key/quota.

---

## Week 6 — Reranker + Citations + Eval Baseline  ✅ **M3**
**Goal:** grounded, cited retrieval + recorded quality baseline.

- ✅ Reranker adapter: local cross-encoder (`ms-marco-MiniLM-L-6-v2`, fastembed, no key) + fake reranker for tests.
- ✅ Retriever pipeline: rewrite(identity) → hybrid candidate pool → rerank → top-N; `retrieve_with_citations`.
- ✅ Citation assembly: dedup by (title,url), snippet with source — grounding for answers.
- ✅ Retrieval eval harness: golden set (10 q→role), metrics hit@1 / MRR / recall@k; baseline JSON recorded.
- ✅ 3 new tests (28 total). ruff + mypy clean.
- ✅ **Live verified:** real BGE + reranker + Qdrant → hit@1/MRR/recall@5 all 1.0 on golden set.
- **Exit:** **M3** — `retrieve()` cited + baseline logged. ✔
- ⏭️ Faithfulness/answer-relevancy (Ragas) deferred to post-chat (need generation) — honest: current baseline is retrieval-only on a tiny KB.

---

## Week 5 — RAG Core (vector infra + embeddings)  ✅
**Goal:** hybrid retrieval machinery behind ports; local + free.

- ✅ Ports: `DenseEmbedder`, `SparseEmbedder`, `VectorStore`, `Reranker` (interfaces only).
- ✅ Chunker: paragraph-aware, word-budgeted, overlap, payload-carrying.
- ✅ Embeddings: BGE-local dense + BM25 sparse (fastembed); Redis embedding cache; deterministic fake embedder for tests.
- ✅ Qdrant adapter: named dense+sparse vectors, hybrid search via RRF fusion, payload filters.
- ✅ Retriever entrypoint + ingestion pipeline + factory wiring.
- ✅ 4 RAG tests (in-memory Qdrant + fake embedder, no network) — 25 total. ruff + mypy clean.
- ✅ **Live verified:** BGE + Qdrant docker — ingest 6 roadmap chunks, hybrid retrieve ranks correct role #1 for 2 queries.
- **Exit:** `retrieve()` returns ranked, filtered chunks; local + free. ✔ (reranker + eval baseline → Week 6)

---

## Week 4 — Onboarding & Readiness v1  ✅ **M2**
**Goal:** onboarding wizard → Twin persisted → dashboard shows radar + readiness.

- ✅ ReadinessScore model + migration `0003` (applied to Postgres).
- ✅ Readiness v1 (skills-only): role-requirement coverage weighted by importance; component placeholders for resume/github/etc.
- ✅ Onboarding service: build Twin (profile fields + bulk skill canonicalization), skips unknown skills.
- ✅ Endpoints: `POST /profile/onboarding`, `GET /profile/readiness`.
- ✅ Frontend: 6-step onboarding wizard, dashboard with inline-SVG ScoreGauge + SkillRadar (no chart deps), skill chips.
- ✅ 5 onboarding/readiness tests (21 total). ruff + mypy clean. web tsc clean.
- ✅ **Verified in browser end-to-end:** register → onboarding → dashboard shows readiness 48/100 (ml-engineer) + 4-axis radar + 6 skills.
- **Exit:** **M2** — onboarding → Twin → dashboard radar + readiness. ✔

---

## Week 3 — Profile & Skill Taxonomy  ✅ (commit `e59abb1`)
**Goal:** profile schema + skill taxonomy + canonicalization + profile CRUD.

- ✅ Models: Profile, Skill, UserSkill, Role, RoleSkillRequirement (portable JSON cols → sqlite-safe).
- ✅ Migration `0002` created + applied to Postgres.
- ✅ Skill canonicalization: slug normalizer (`C++`→`cpp`, `Node.js`→`nodejs`) + alias match (`py`→Python).
- ✅ Profile CRUD: `GET/PUT /profile` (twin_version bump), `GET/POST /profile/skills` (upsert).
- ✅ Seed script: 46 skills / 9 categories, 8 roles, 60 requirements → loaded into Postgres.
- ✅ 6 profile tests (16 total). ruff + mypy clean.
- ✅ Web: bumped `next` + `eslint-config-next` → `^14.2.33` (patches critical vuln; needs `npm install`).
- ✅ **Verified live on Postgres:** autocreate → update → alias/normalizer skill add → list.
- **Exit:** create/read profile; skills normalize to canonical ids. ✔

---

## Week 2 — Auth  ✅ **M1** (commit `5907259`)
**Goal:** runnable web+api + auth.

- ✅ SQLAlchemy 2.0 (lazy engine) + User model (uuid pk, role, auth_provider).
- ✅ Migration `0001` create_users, applied to Postgres.
- ✅ Password auth: register/login/refresh/logout/me — bcrypt + PyJWT access+refresh.
- ✅ RBAC deps (get_current_user / get_current_admin), HTTPBearer.
- ✅ OAuth scaffold (GitHub/Google via httpx; 503 until creds set).
- ✅ RFC7807 problem+json error handlers; CORS for frontend.
- ✅ 10 auth tests on sqlite (CI-friendly). ruff + mypy clean.
- ✅ Web: API client + token store, login/register page, protected dashboard, landing CTA.
- ✅ **Verified live:** register→login→/me against Postgres AND full browser UI flow (register → dashboard).
- **Exit:** **M1** — infra + auth running. ✔

---

## Week 1 — Foundations  ✅ (commits `faa8fa5`, `776d87b`)
**Goal:** repo + infra + one-command dev env.

### Day 1 — Repo, tooling, skeletons
- ✅ Monorepo scaffold (`apps/web`, `apps/api`, `infra`, `data`, `packages`, `docs`).
- ✅ FastAPI skeleton: app factory, `/health` + `/ready`, pydantic-settings config, structlog, clean-arch dirs.
- ✅ Next.js skeleton (App Router, Tailwind).
- ✅ Tooling: Makefile, .gitignore, .gitattributes, .env.example, MIT license.
- ✅ 2 health tests pass; git init + commit.

### Day 2 — Free API keys + smoke
- ✅ `data/scripts/check_keys.py` — validates keys, live-pings providers, SKIP on missing.
- ✅ `.env.example` with all keys documented (free-tier providers).

### Day 3 — Docker Compose
- ✅ `infra/docker-compose.yml`: postgres, redis, qdrant, neo4j, minio + healthchecks + volumes.

### Day 4 — Lint/format
- ✅ `.pre-commit-config.yaml`: ruff, gitleaks, hygiene hooks.

### Day 5 — CI + docs
- ✅ `.github/workflows/ci.yml`: api (lint/mypy/pytest) + web (lint/build) + gitleaks.
- ✅ PR template, `docs/dev-setup.md`.

### Environment bring-up (user)
- ✅ Docker Desktop installed (AMD64) — resolved ownership + daemon issues.
- ✅ 5 datastores pulled + running healthy.
- ✅ Free keys: GitHub PAT ✅, Anthropic ✅, Qdrant reachable ✅. (Gemini optional — invalid key, using Anthropic for dev.)
- **Exit:** clone → keys → `docker compose up` → working dev env. ✔

---

## Known Notes / Debt
- `JWT_SECRET` is 17 bytes (dev default) → set 32+ before prod.
- User `.env` has inline comments on lines 6–7 → harmless python-dotenv warning; re-copy cleaned `.env.example` to silence.
- Web build not yet run in CI locally (needs `npm install`); UI verified manually.
- OAuth (GitHub/Google) coded but untested — needs `OAUTH_*` creds.
- Dev DB has test users (`smoke@`, `uitest@`, `w3@`, `w4ui@`) — harmless.
- Windows symlink warning on fastembed model cache (dev mode off) — harmless, caching works.
- Reranker port defined but no adapter yet (Week 6).
