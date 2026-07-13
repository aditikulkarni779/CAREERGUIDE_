# 04 — Data Model & Schemas

Project: **AI Career Copilot** · Draft v1.0
Covers: PostgreSQL (app), Neo4j (knowledge graph), Qdrant (vectors).

---

## 1. PostgreSQL (relational core)

### ER Overview
```
users ─1:1─ profiles ─1:N─ user_skills ─N:1─ skills
  │            │
  │            ├─1:N─ roadmaps ─1:N─ roadmap_items
  │            ├─1:N─ resumes ─1:N─ resume_scores
  │            ├─1:1─ github_profiles ─1:N─ github_repos
  │            ├─1:N─ recommendations
  │            ├─1:N─ readiness_scores
  │            └─1:N─ goals
  ├─1:N─ conversations ─1:N─ messages
  ├─1:N─ interview_sessions ─1:N─ interview_questions
  ├─1:N─ notifications
  └─1:N─ gamification_events
roles ─1:N─ role_skill_requirements ─N:1─ skills
learning_resources (catalog)   job_postings (market)
```

### Key Tables (columns abbreviated)

**users**
`id uuid pk · email unique · auth_provider · role enum(user,admin) · created_at · last_login`

**profiles** (the Career Twin core)
`id · user_id fk · education jsonb · learning_style · weekly_hours int · target_companies text[] · expected_salary int · interests text[] · career_goal · twin_version int · updated_at`

**skills** (canonical taxonomy)
`id · name · slug unique · category enum(language,framework,library,db,tool,cloud,ai,soft,cert) · esco_id · onet_id`

**user_skills** (edge w/ evidence)
`id · profile_id fk · skill_id fk · proficiency smallint(0-100) · source enum(resume,github,linkedin,chat,manual) · evidence jsonb · confidence float · last_seen_at`

**roles** & **role_skill_requirements**
`roles: id · name · slug` · `role_skill_requirements: role_id · skill_id · importance smallint · typical_proficiency · difficulty`

**roadmaps** / **roadmap_items**
`roadmaps: id · profile_id · target_role_id · version int · status · rationale jsonb · created_at`
`roadmap_items: id · roadmap_id · skill_id · order_index · est_hours · status enum(todo,doing,done,skipped) · resources jsonb · completed_at`

**resumes** / **resume_scores**
`resumes: id · profile_id · file_key · parsed jsonb · created_at`
`resume_scores: id · resume_id · ats_score · sections jsonb · missing_keywords text[] · weak_bullets jsonb · suggestions jsonb`

**github_profiles** / **github_repos**
`github_profiles: id · profile_id · username · health_score · diversity_score · recruiter_score · fetched_at`
`github_repos: id · github_profile_id · name · lang · stars · complexity_score · readme_score · doc_score · metrics jsonb`

**recommendations**
`id · profile_id · type enum(course,book,project,repo,cert,paper,...) · ref_id · title · url · score float · explanation jsonb(why,gap_skill_id,impact,confidence) · status · created_at`

**readiness_scores**
`id · profile_id · overall smallint · components jsonb(skills,resume,github,projects,learning,interview,market) · computed_at`

**conversations** / **messages**
`conversations: id · user_id · title · created_at`
`messages: id · conversation_id · role enum(user,assistant,system,tool) · content · citations jsonb · tokens int · agent_trace jsonb · created_at`

**interview_sessions** / **interview_questions**
`sessions: id · user_id · kind enum(technical,hr,coding,system_design,ml) · company · score · created_at`
`questions: id · session_id · prompt · expected · user_answer · feedback jsonb · score`

**learning_resources** (recommendation catalog)
`id · type · title · provider · url · skills text[] · difficulty · duration_hours · rating · embedding_ref · meta jsonb`

**job_postings** (market snapshot)
`id · title · company · location · skills text[] · salary_min · salary_max · source · posted_at · ingested_at · embedding_ref`

**goals**
`id · profile_id · description · target_date · progress smallint · status`

**notifications**
`id · user_id · type · payload jsonb · read bool · created_at`

**gamification_events**
`id · user_id · type enum(xp,badge,streak,milestone) · value int · meta jsonb · created_at`

### Indexing / integrity
- FKs with `ON DELETE CASCADE` for user-owned data (privacy delete).
- Partial + GIN indexes on `text[]`/`jsonb` (skills, keywords).
- `updated_at` triggers; `twin_version` bumped on profile-affecting writes.
- Soft-delete flag optional; hard delete supported for GDPR export/delete.

---

## 2. Neo4j (Knowledge Graph)

### Node labels
`(:Skill)`, `(:Course)`, `(:Project)`, `(:Job)`, `(:Company)`, `(:Technology)`, `(:Role)`, `(:Certification)`

### Relationships
```
(:Skill)-[:PREREQUISITE_OF]->(:Skill)
(:Skill)-[:RELATED_TO {weight}]->(:Skill)
(:Course)-[:TEACHES {coverage}]->(:Skill)
(:Project)-[:REQUIRES]->(:Skill)
(:Project)-[:DEMONSTRATES]->(:Skill)
(:Role)-[:NEEDS {importance}]->(:Skill)
(:Job)-[:AT]->(:Company)
(:Job)-[:DEMANDS {count}]->(:Skill)
(:Company)-[:HIRES_FOR]->(:Role)
(:Technology)-[:USED_IN]->(:Project)
(:Certification)-[:VALIDATES]->(:Skill)
(:Skill)-[:TRENDING {momentum, updated_at}]->(:Market)
```

### Why graph
- Path queries: shortest prerequisite chain from user's known skills → target-role skills.
- "Skills co-demanded with X at company Y" → project/course recommendations.
- Market momentum edges refreshed nightly to bias recommendations toward rising tech.

---

## 3. Qdrant (Vector Store)

Collections (dense + sparse hybrid, cosine):

| Collection | Payload filters |
|------------|-----------------|
| `resources` | type, skills[], difficulty, provider, duration |
| `jobs` | company, location, skills[], salary, posted_at |
| `roadmap_kb` | source, role, skill, difficulty |
| `interview_kb` | kind, company, topic, difficulty |
| `docs_kb` | source, topic (blogs/books/papers/docs) |
| `user_memory` | user_id, kind (long-term chat memory) |

- Named vectors: `dense` (Voyage) + `sparse` (BM25/SPLADE) for hybrid.
- Payload-indexed fields for fast pre-filtering.
- `embedding_ref` in Postgres links relational rows ↔ Qdrant point ids.

---

## 4. Redis (ephemeral)
- Keys: `cache:embed:*`, `cache:rag:*`, `cache:score:*`, `session:*`, `ratelimit:*`, Celery queues.
- TTLs tuned per type; semantic LLM cache keyed by normalized prompt hash.
