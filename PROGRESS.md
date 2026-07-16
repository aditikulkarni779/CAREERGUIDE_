# Progress Log

Running log of build progress against [13_EXECUTION_PLAN.md](./13_EXECUTION_PLAN.md).
Newest entries at top. One entry per work session/day.

**Legend:** ✅ done · 🟡 partial · ⛔ blocked · ⏭️ deferred

---

## Status Snapshot
- **Current phase:** Phase 2 (RAG Core) — up next
- **Milestones hit:** M1 (infra + auth), M2 (Career Twin + onboarding)
- **Next up:** Week 5 — RAG core (Qdrant + embeddings + hybrid search)
- **Stack live:** Postgres, Redis, Qdrant, Neo4j, MinIO (Docker, all healthy)
- **Repo:** github.com/aditikulkarni779/CAREERGUIDE_ (main pushed)
- **Latest commit:** (Week 4 — see below)
- **Test count:** 21 passing (sqlite) · ruff + mypy clean
- **Migrations applied:** 0001 (users), 0002 (profiles/skills/roles), 0003 (readiness_scores)
- **Seed data:** 46 skills, 8 roles, 60 role requirements

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
- Dev DB has test users (`smoke@`, `uitest@`, `w3@`) — harmless.
