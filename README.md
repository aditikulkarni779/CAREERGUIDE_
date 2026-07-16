# AI Career Copilot

An intelligent, production-grade career guidance platform: a personal AI mentor that understands who a user is, where they want to go, and guides them with data-driven, explainable recommendations.

Not a chatbot. The chat is one interface into a larger reasoning + recommendation system built on RAG, multi-agent orchestration, a skills knowledge graph, and real-time job-market intelligence.

---

## Documentation Index

| # | Document | Purpose |
|---|----------|---------|
| 00 | [README.md](./README.md) | This overview + index |
| 01 | [01_SRS.md](./01_SRS.md) | Software Requirements Specification |
| 02 | [02_ARCHITECTURE.md](./02_ARCHITECTURE.md) | System & solution architecture |
| 03 | [03_TECH_STACK.md](./03_TECH_STACK.md) | Technology choices + rationale |
| 04 | [04_DATABASE_SCHEMA.md](./04_DATABASE_SCHEMA.md) | Postgres + Neo4j + Qdrant schemas |
| 05 | [05_AGENT_WORKFLOWS.md](./05_AGENT_WORKFLOWS.md) | Multi-agent design (LangGraph) |
| 06 | [06_RAG_PIPELINE.md](./06_RAG_PIPELINE.md) | Retrieval-Augmented Generation design |
| 07 | [07_API_SPEC.md](./07_API_SPEC.md) | REST/WS API specification |
| 08 | [08_DATA_ENGINEERING.md](./08_DATA_ENGINEERING.md) | Datasets + ingestion pipelines |
| 09 | [09_UI_WIREFRAMES.md](./09_UI_WIREFRAMES.md) | Screens, dashboard, wireframes |
| 10 | [10_TESTING_STRATEGY.md](./10_TESTING_STRATEGY.md) | Test pyramid + eval strategy |
| 11 | [11_DEPLOYMENT_MLOPS.md](./11_DEPLOYMENT_MLOPS.md) | Deploy, CI/CD, observability |
| 12 | [12_ROADMAP_MILESTONES.md](./12_ROADMAP_MILESTONES.md) | Phased build plan + milestones |
| 13 | [13_EXECUTION_PLAN.md](./13_EXECUTION_PLAN.md) | Week-by-week execution plan (24 wks) |
| — | [PROGRESS.md](./PROGRESS.md) | Running build progress log (updated each session) |

---

## Elevator Pitch

Students often know *what* career they want but not *what* to learn, *in what order*, *which skills matter*, *which projects to build*, or *whether they are job-ready*. AI Career Copilot answers these continuously and personally, acting like a senior mentor whose advice adapts as the user grows and as the market shifts.

## Core Capabilities

1. **AI Career Chatbot** — reasons before answering, cites sources, remembers history.
2. **Skill Intelligence Engine** — extracts a dynamic skill graph from resume, GitHub, LinkedIn, chat.
3. **Skill Gap Analyzer** — compares user vs. target-role requirements with scored gaps.
4. **Adaptive Roadmap Generator** — a *living* roadmap that re-plans on progress/market change.
5. **Hybrid Recommendation Engine** — content + collaborative + semantic + graph + LLM reasoning, always explained.
6. **Resume Intelligence** — ATS score, weak-section detection, bullet rewriting.
7. **GitHub Intelligence** — health/diversity/recruiter-impression scoring.
8. **Job Market Intelligence** — live trend, demand, salary signals feeding recommendations.
9. **Project Recommendation Engine** — portfolio-gap-driven project ideas with full specs.
10. **Interview Preparation** — technical/HR/system-design generation, scoring, feedback.

## Signature Differentiators

- **AI Career Twin** — an evolving digital model of the user driving every recommendation.
- **Career Readiness Score** — a weighted, explainable job-readiness index.
- **Explainable AI** — every recommendation answers *why this, which gap, what impact, how confident*.
- **AI Weekly Mentor** — personalized weekly report of wins, misses, next steps.
- **Knowledge Graph** — Skills ↔ Courses ↔ Projects ↔ Jobs ↔ Technologies ↔ Companies.

## High-Level Stack

Python/FastAPI · LangGraph + Claude · Qdrant + Voyage (RAG) · PostgreSQL · Neo4j · Redis/Celery · Next.js/TypeScript/Tailwind · Docker · GitHub Actions · LangSmith · Prometheus/Grafana.

See [03_TECH_STACK.md](./03_TECH_STACK.md) for rationale.

## Status

Planning phase. No code yet. Build proceeds per [12_ROADMAP_MILESTONES.md](./12_ROADMAP_MILESTONES.md) after plan approval.
