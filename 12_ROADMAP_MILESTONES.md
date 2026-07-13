# 12 — Development Roadmap & Milestones

Project: **AI Career Copilot** · Draft v1.0
Approach: incremental, vertical slices. Each phase ships something demoable + tested. Durations are estimates for a small team; adjust to capacity.

---

## Phase 0 — Foundations (Week 1–2)
**Goal:** repo, infra, skeleton run locally.
- Monorepo scaffold ([03_TECH_STACK.md](./03_TECH_STACK.md) layout), Docker Compose, `.env` config.
- FastAPI skeleton + health, Next.js skeleton, Postgres + Alembic baseline.
- CI: lint/typecheck/unit; pre-commit hooks.
- Auth (register/login/JWT/OAuth) + `/auth/me`.
**Exit:** `compose up` runs web+api+db; auth works; CI green.

## Phase 1 — Career Twin & Onboarding (Week 3–4)
- Profile/skills schema; onboarding wizard UI; `POST /profile/onboarding`.
- Skill taxonomy seed (ESCO/O*NET subset); canonicalization service.
- Career Twin build + versioning; readiness score v1 (skills-only).
**Exit:** user onboards → Twin persisted → dashboard shows skill radar + readiness.

## Phase 2 — RAG Core (Week 5–6)
- Qdrant + Voyage embedder + hybrid search + reranker (behind ports).
- Ingest first KB (roadmaps.sh + course sample + O*NET role reqs).
- Retriever + citation assembly; RAG eval harness (Ragas) + golden set.
**Exit:** `retrieve()` returns grounded, cited chunks; eval baseline recorded.

## Phase 3 — Agent Orchestrator + Chat (Week 7–9)
- LangGraph state machine; Planner + Chat + Citation + Verification.
- Streaming chat (SSE) end-to-end; conversation persistence + long-term memory.
- Skill Gap + Roadmap agents; skill-path sub-workflow.
**Exit:** "How do I become an ML Engineer?" → streamed answer + roadmap + citations + explanations. Journey #2 e2e passes.

## Phase 4 — Frontend Depth (Week 9–11, overlaps 3)
- Dashboard widgets (radar, gap heatmap, roadmap timeline, score gauges).
- Chat UI polish (reasoning steps, recommendation cards, Why? popover).
- Roadmap page w/ status toggles + versions; skills graph view.
**Exit:** startup-quality dashboard + chat; responsive + a11y pass.

## Phase 5 — Resume & GitHub Intelligence (Week 12–14)
- Resume upload → MinIO → Celery parse → Skill Extraction → ATS scorer + rewrite (Resume agent).
- GitHub agent: fetch + 4 scores; cache 24h.
- Feed both into Twin evidence + readiness components.
**Exit:** journeys #3, #4 e2e pass; readiness score uses resume+github.

## Phase 6 — Recommendations + Data Pipelines (Week 15–17)
- Hybrid recommendation engine (content+semantic+graph+collab+LLM) w/ explanations.
- Neo4j knowledge graph populated; graph-based recs.
- Celery-beat ingestion: nightly jobs + weekly courses; trend/demand signals.
- Recommendation feedback loop (👍/👎).
**Exit:** `/recommendations` ranked + explained; nightly pipeline healthy; market trends on dashboard.

## Phase 7 — Adaptive & Engagement (Week 18–20)
- Adaptive re-plan (event-driven on completion/market shift).
- Weekly AI Mentor report (Report agent, Opus) + PDF export.
- Notifications + gamification (XP/badges/streaks).
- Interview prep module (generation + scoring).
**Exit:** roadmap re-plans automatically; weekly report + notifications + interview flow live.

## Phase 8 — Hardening & Launch (Week 21–24)
- Project Recommendation + Architect; company-specific prep.
- Full observability (Grafana dashboards, alerts), load + security testing.
- LLMOps: prompt versioning, eval gates, cost dashboard.
- Docs (MkDocs), README, demo data, deploy to staging→prod.
**Exit:** all MVP acceptance criteria ([01_SRS.md](./01_SRS.md) §7) met; prod deploy; runbooks ready.

---

## Post-MVP Backlog
Voice AI · recruiter view · leaderboards · LinkedIn deep integration · mobile app · Airflow migration · multi-region · fine-tuned rerankers · A/B rec-weight optimization.

---

## Milestone Summary
| M | Deliverable | Phase |
|---|-------------|-------|
| M1 | Infra + auth running | 0 |
| M2 | Career Twin + onboarding | 1 |
| M3 | Grounded RAG w/ citations | 2 |
| M4 | Chat + roadmap agents (flagship demo) | 3 |
| M5 | Dashboard + chat UI polished | 4 |
| M6 | Resume + GitHub intelligence | 5 |
| M7 | Recommendations + live pipelines | 6 |
| M8 | Adaptive + engagement + interview | 7 |
| M9 | Hardened, observable, deployed | 8 |

---

## Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| Scope creep (14 modules) | Vertical slices; strict phase exits; backlog park |
| LLM cost | Tiering, caching, token budgets, cost alerts |
| Hallucinated advice | RAG grounding + citation + verification + eval gates |
| Dataset ToS/quality | Provenance, licensed/public only, quality checks |
| Vendor lock-in | Ports/adapters; swap-able embeddings + vector store |
| Solo-dev velocity | Prioritize M1–M4 (the demo core); rest incremental |

---

## Immediate Next Actions (on approval)
1. Confirm stack + scope (this doc set).
2. Scaffold repo (Phase 0) + Compose + CI.
3. Seed skill taxonomy + first KB for RAG.
4. Build flagship slice: onboarding → Twin → skill-path chat + roadmap (M2–M4).
