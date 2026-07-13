# 02 — System Architecture

Project: **AI Career Copilot** · Draft v1.0

---

## 1. Architectural Style
- **Clean/Hexagonal** core (domain independent of frameworks).
- **Modular monolith** for MVP → service extraction later (chat, ingestion, scoring already isolated as modules to split cleanly).
- **Event-driven** background work via Redis + Celery.
- **12-factor** config; stateless API; externalized state.

---

## 2. C4 — Level 1: System Context

```
                         ┌─────────────────────────┐
        Student ────────▶│                         │
     (web browser)       │   AI Career Copilot     │◀──── Admin (dashboard)
                         │        (SaaS)           │
                         └───────────┬─────────────┘
                                     │ integrates
   ┌──────────────┬──────────────────┼───────────────┬───────────────┐
   ▼              ▼                  ▼               ▼               ▼
Anthropic     Voyage AI          GitHub API     Job/Market      Datasets
 (Claude)     (embeddings)      (repos/commits)  data APIs    (Coursera, ESCO,
                                                              O*NET, arXiv…)
```

---

## 3. C4 — Level 2: Container Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│ FRONTEND  — Next.js (SSR/CSR), TypeScript, Tailwind, shadcn/ui          │
│  • Auth pages • Onboarding wizard • Chat UI (streaming) • Dashboard     │
└───────────────┬───────────────────────────────────────────────────────┘
                │ HTTPS / WSS (JSON, SSE stream)
┌───────────────▼───────────────────────────────────────────────────────┐
│ API GATEWAY — FastAPI                                                   │
│  • Auth/JWT • Rate limit • Request validation • REST + WebSocket/SSE    │
└───┬─────────────┬──────────────┬───────────────┬──────────────┬────────┘
    │             │              │               │              │
┌───▼───┐   ┌─────▼─────┐  ┌─────▼──────┐  ┌─────▼──────┐  ┌────▼───────┐
│Profile│   │ Agent     │  │ RAG /      │  │ Scoring    │  │ Ingestion  │
│Service│   │ Orchestr. │  │ Retrieval  │  │ Services   │  │ (Celery)   │
│(Twin) │   │(LangGraph)│  │ Service    │  │(ATS/GitHub)│  │ workers    │
└───┬───┘   └─────┬─────┘  └─────┬──────┘  └─────┬──────┘  └────┬───────┘
    │             │              │               │              │
────┼─────────────┼──────────────┼───────────────┼──────────────┼─────────
    ▼             ▼              ▼               ▼              ▼
┌────────┐  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Postgres│  │  Redis   │   │  Qdrant  │   │  Neo4j   │   │ MinIO/S3 │
│(app DB)│  │cache/queue│  │(vectors) │   │  (KG)    │   │ (files)  │
└────────┘  └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

Cross-cutting: **LangSmith** (LLM tracing), **Prometheus/Grafana** (metrics), **structured logging**, **OpenTelemetry** traces.

---

## 4. Core Modules (Level 3)

### 4.1 Profile / Career Twin Service
- Owns user profile, skill graph snapshot, readiness score.
- Publishes `TwinUpdated` events → triggers re-scoring + roadmap re-plan.

### 4.2 Agent Orchestrator (LangGraph)
- Hosts the multi-agent graph (see [05_AGENT_WORKFLOWS.md](./05_AGENT_WORKFLOWS.md)).
- Planner routes requests to specialist agents; Verification + Citation agents gate output.
- Streams tokens to client via SSE.

### 4.3 RAG / Retrieval Service
- Hybrid search (dense Qdrant + sparse BM25) + metadata filter + reranking.
- Serves grounded context to agents; returns citations. See [06_RAG_PIPELINE.md](./06_RAG_PIPELINE.md).

### 4.4 Scoring Services
- Resume ATS scorer, GitHub scorer, Readiness aggregator. Deterministic + LLM-assisted; cached.

### 4.5 Ingestion / Data Engineering (Celery)
- Scheduled dataset + market pipelines → normalize → embed → Qdrant/Neo4j/Postgres. See [08_DATA_ENGINEERING.md](./08_DATA_ENGINEERING.md).

### 4.6 Recommendation Engine
- Hybrid signal fusion (content/collab/semantic/graph/LLM). Explanation attached to each item.

---

## 5. Request Flows

### 5.1 Chat (skill-path question)
```
Client ─WS─▶ API ─▶ Planner Agent
   Planner ─▶ Skill Gap Agent ─▶ (reads Twin, Neo4j role reqs)
   Planner ─▶ RAG Service ─▶ Qdrant hybrid + rerank
   Planner ─▶ Roadmap Agent ─▶ draft plan
   Citation Agent attaches sources · Verification Agent checks claims
   ─▶ stream answer + roadmap + explanations ─▶ Client
   Async: persist conversation, update Twin evidence
```

### 5.2 Resume Upload
```
Upload ─▶ MinIO ─▶ Celery parse job ─▶ Skill Extraction Agent
      ─▶ ATS scorer + weak-section detector ─▶ Resume Agent rewrites
      ─▶ persist scores + update Twin ─▶ notify client
```

### 5.3 Nightly Market Refresh
```
Cron ─▶ Ingestion workers ─▶ fetch job/market data ─▶ normalize
     ─▶ embed + upsert Qdrant + update Neo4j demand edges
     ─▶ recompute trend signals ─▶ enqueue roadmap re-plan for active users
```

---

## 6. Cross-Cutting Concerns
- **Auth**: JWT access + refresh; OAuth (Google/GitHub); RBAC middleware.
- **Config**: pydantic-settings from env; secrets via vault/`.env` (never committed).
- **Resilience**: retries + exponential backoff; circuit breaker on external APIs; graceful LLM fallback tier.
- **Caching**: Redis for embeddings, retrieval results, scores, LLM response cache (semantic key).
- **Idempotency**: job dedup keys; upsert semantics in vector/graph stores.
- **Rate limiting**: per-user + per-IP token bucket.

---

## 7. LLM Cost/Latency Tiering
| Task | Model |
|------|-------|
| Routing, extraction, classification, short rewrites | Haiku 4.5 |
| Chat, gap analysis, recommendations, roadmap | Sonnet 5 |
| Deep reasoning, weekly mentor report, hard verification | Opus 4.8 |

Semantic response cache + prompt caching to cut cost. Token budget enforced per request.

---

## 8. Deployment Topology (MVP)
Single Docker Compose stack (dev) → container platform (prod: ECS/Fly/K8s). See [11_DEPLOYMENT_MLOPS.md](./11_DEPLOYMENT_MLOPS.md).

## 9. Key Architectural Decisions (ADR summary)
1. Modular monolith over microservices for MVP — lower ops cost, clean seams for later split.
2. Neo4j for the knowledge graph — relationship-heavy recommendation queries.
3. Qdrant over pgvector — first-class hybrid search + payload filtering at scale.
4. LangGraph over ad-hoc chains — explicit, testable, resumable agent state machine.
5. Voyage embeddings behind an interface — swap-able (BGE fallback) to avoid lock-in.
