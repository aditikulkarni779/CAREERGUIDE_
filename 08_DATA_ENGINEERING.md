# 08 — Data Engineering & Datasets

Project: **AI Career Copilot** · Draft v1.0

---

## 1. Dataset Inventory

| Domain | Sources | Use |
|--------|---------|-----|
| Learning | Coursera, Udemy, edX catalogs | Course/cert recommendations |
| Employment | LinkedIn/Glassdoor/Kaggle job datasets | Market demand, salary, skills |
| Dev trends | Stack Overflow Survey, GitHub Trending, Kaggle | Framework popularity, project ideas |
| Research | arXiv, Semantic Scholar metadata | Paper recommendations, deep topics |
| Skills taxonomy | ESCO, O*NET | Canonical skill normalization, role reqs |
| Roadmaps | roadmaps.sh, awesome-* repos, career guides | Roadmap knowledge base |

Respect each source's license/ToS + rate limits. Store provenance per record.

---

## 2. Ingestion Architecture

```
Scheduler (Celery beat)
   └─▶ Extract (source adapters, paginated, rate-limited, retry/backoff)
        └─▶ Land raw (MinIO/S3, partitioned by source/date)  [bronze]
             └─▶ Transform (clean, dedup, language filter, schema map) [silver]
                  └─▶ Enrich (skill-tag via Skill Extraction, canonicalize) 
                       └─▶ Load
                            ├─▶ Postgres (learning_resources, job_postings, roles reqs)
                            ├─▶ Qdrant (embed + upsert)
                            └─▶ Neo4j (nodes + demand/teaches/needs edges)
```

Medallion (bronze/silver/gold) layout keeps raw reproducible, transforms idempotent.

---

## 3. Pipelines & Cadence

| Pipeline | Cadence | Output |
|----------|---------|--------|
| Course catalog sync | Weekly | `resources` collection + `learning_resources` |
| Job market ingest | Nightly | `jobs` collection + `job_postings` + Neo4j demand edges |
| Trend computation | Nightly | Skill momentum scores → Neo4j `TRENDING` edges |
| Research metadata | Weekly | `docs_kb` |
| Skills taxonomy refresh | Quarterly | `skills` table + `roles`/`role_skill_requirements` |
| Roadmap KB | Monthly | `roadmap_kb` |
| GitHub (per user) | On-demand + cached 24h | `github_*` tables |

---

## 4. Normalization & Quality
- **Skill canonicalization**: map raw strings → ESCO/O*NET ids via embedding match + alias table; unknowns queued for review.
- **Dedup**: minhash on titles/descriptions; URL canonicalization.
- **Validation**: pydantic schemas per source; reject/quarantine malformed rows.
- **Data quality checks**: row counts, null ratios, freshness SLA; alert on breach.
- **Provenance**: every record stores `source`, `fetched_at`, `license`.

---

## 5. Trend / Demand Signals
- Skill demand = frequency in recent job postings, weighted by recency + salary.
- Momentum = demand delta over rolling windows → drives recommendation boosting + roadmap re-plan triggers.
- Persisted to Neo4j edges + a `market_signals` table for dashboard.

---

## 6. Feature/Signal Store (recommendation)
- Content features: resource skills, difficulty, provider rating, duration.
- Collaborative signal: recommendation feedback (`useful`) aggregated per resource/role cohort.
- Graph features: prerequisite depth, co-demand, company relevance.
- Fused at rank time; weights configurable + A/B-testable.

---

## 7. Orchestration & Reliability
- Celery beat schedules; each task idempotent (upsert + dedup key).
- Retries w/ exponential backoff; dead-letter queue for poison messages.
- Backfill scripts re-run transforms from bronze.
- (Later) migrate heavy DAGs to Airflow/Prefect if complexity grows.

---

## 8. Privacy in Data
- Public datasets only for the KB; user PII (resume, github) stored separately, encrypted, deletable.
- No user PII enters shared collections; `user_memory` is user-scoped + filtered by `user_id`.
