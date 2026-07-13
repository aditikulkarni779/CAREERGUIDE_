# 03 — Technology Stack & Rationale

Project: **AI Career Copilot** · Draft v1.0

---

## Summary Table

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | Next.js 14+ (App Router), TypeScript | SSR + streaming UI, strong ecosystem, hiring-relevant |
| UI kit | Tailwind CSS + shadcn/ui + Radix | Fast, accessible, consistent design system |
| Charts | Recharts / visx | Dashboard radar, heatmap, timelines |
| State/data | TanStack Query + Zustand | Server-cache + light client state |
| Auth (client) | Auth.js (NextAuth) | Google/GitHub OAuth + session |
| Backend | Python 3.12, FastAPI | Async, typed, OpenAPI, ML-ecosystem native |
| Validation | Pydantic v2 | Schema + settings + LLM structured output |
| Agents | LangGraph + LangChain | Stateful, resumable multi-agent graphs |
| LLM | Anthropic Claude (Opus 4.8 / Sonnet 5 / Haiku 4.5) | Reasoning quality, tool use, tiering |
| Embeddings | Voyage AI (`voyage-3`), fallback BAAI/bge | High-quality retrieval; interface-abstracted |
| Reranker | Voyage rerank / bge-reranker | Precision boost on retrieval |
| Vector DB | Qdrant | Hybrid search, payload filters, scalable |
| Graph DB | Neo4j | Skills↔Courses↔Jobs↔Companies knowledge graph |
| App DB | PostgreSQL 16 | Relational core, JSONB flexibility |
| ORM/migrations | SQLAlchemy 2 + Alembic | Typed models, versioned schema |
| Cache/broker | Redis | Cache + Celery broker + rate limits |
| Task queue | Celery (+ beat) | Scheduled ingestion, async scoring |
| Object store | MinIO (dev) / S3 (prod) | Resume + PDF storage |
| LLM tracing | LangSmith | Prompt/agent observability + evals |
| Metrics | Prometheus + Grafana | System + business metrics |
| Logging | structlog + OpenTelemetry | Structured, correlated traces |
| Containers | Docker + Compose | Reproducible local + prod images |
| CI/CD | GitHub Actions | Lint, test, build, deploy |
| Testing | pytest, Playwright, Ragas/DeepEval | Unit/integration/e2e + LLM eval |
| Docs | OpenAPI/Swagger + MkDocs | API + project docs |

---

## Rationale Notes

- **FastAPI + Python** keeps AI/ML libs, agents, and API in one language; native async fits streaming + concurrent LLM calls.
- **LangGraph** turns the "15 agents" requirement into an explicit, testable state machine with checkpoints (resumable, debuggable, evaluable) instead of brittle prompt chains.
- **Qdrant + Neo4j split**: Qdrant answers "what is semantically similar", Neo4j answers "what is connected/why". Recommendations fuse both.
- **Claude tiering** is the primary cost lever; Haiku handles high-volume extraction/routing, Opus reserved for deep reasoning.
- **Embeddings behind an interface** avoid vendor lock-in and allow offline/open-source fallback (BGE) for cost or air-gapped runs.
- Everything is **swap-able behind ports** (Clean Architecture) — the domain never imports a vendor SDK directly.

---

## Repository Layout (planned monorepo)

```
career-copilot/
├── apps/
│   ├── web/                 # Next.js frontend
│   └── api/                 # FastAPI backend
│       ├── app/
│       │   ├── domain/      # entities, value objects (framework-free)
│       │   ├── services/    # use-cases
│       │   ├── agents/      # LangGraph nodes + graph
│       │   ├── rag/         # retrieval, embedding, rerank
│       │   ├── adapters/    # db, vector, graph, llm, github, storage
│       │   ├── api/         # routers (REST + WS)
│       │   ├── workers/     # celery tasks
│       │   └── core/        # config, logging, security
│       └── tests/
├── packages/
│   └── shared-types/        # TS types generated from OpenAPI
├── data/                    # dataset ingestion scripts + samples
├── infra/                   # docker, compose, ci, k8s manifests
├── docs/                    # mkdocs
└── README.md
```

---

## Environment / Config Keys (illustrative)
```
ANTHROPIC_API_KEY, VOYAGE_API_KEY
DATABASE_URL, REDIS_URL, QDRANT_URL, NEO4J_URI/USER/PASSWORD
S3_ENDPOINT/KEY/SECRET/BUCKET
GITHUB_TOKEN, JOB_API_KEYS...
JWT_SECRET, NEXTAUTH_SECRET, OAUTH_GOOGLE_*, OAUTH_GITHUB_*
LANGSMITH_API_KEY, LOG_LEVEL, ENV
```
All loaded via pydantic-settings; never committed.
