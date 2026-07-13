# 01 — Software Requirements Specification (SRS)

Project: **AI Career Copilot**
Status: Draft v1.0 · Planning phase

---

## 1. Introduction

### 1.1 Purpose
Define functional and non-functional requirements for AI Career Copilot, an AI-powered career guidance platform delivering personalized, explainable, data-driven mentorship.

### 1.2 Scope
A multi-tenant SaaS web application. Users create a profile ("Career Twin"), interact via chat and dashboards, and receive continuously adapting recommendations across skills, roadmaps, resumes, GitHub, projects, and interviews, grounded in retrieval over curated career knowledge and live market data.

### 1.3 Definitions
- **Career Twin** — evolving structured representation of a user's skills, goals, progress.
- **Skill Graph** — per-user graph of skills and relationships (not a flat list).
- **Readiness Score** — weighted composite job-readiness index (0–100).
- **Agent** — single-responsibility LLM worker coordinated via LangGraph.
- **RAG** — Retrieval-Augmented Generation.
- **ATS** — Applicant Tracking System.

---

## 2. Stakeholders & Personas

| Persona | Goal | Key needs |
|---------|------|-----------|
| Student (primary) | Land target role | Roadmap, gap analysis, projects, interview prep |
| Career switcher | Pivot into tech/AI | Skill mapping, realistic timeline |
| Recruiter (future) | Assess candidates | Verified readiness signals |
| Admin/Operator | Run the platform | Ingestion health, usage analytics, moderation |

---

## 3. Functional Requirements

### FR-1 Onboarding & Profile
- FR-1.1 Capture education, current skills, languages, frameworks, certifications, interests, learning style, weekly study hours, target companies, expected salary, current projects.
- FR-1.2 Accept GitHub username, optional LinkedIn, resume upload (PDF/DOCX).
- FR-1.3 Build the Career Twin from all sources; persist and version it.
- FR-1.4 Every later recommendation must read from the Career Twin.

### FR-2 AI Career Chatbot
- FR-2.1 Natural-language Q&A over career topics.
- FR-2.2 Persist and use conversation memory (short- and long-term).
- FR-2.3 Reason (plan) before answering; expose a "thinking/steps" trace where useful.
- FR-2.4 Cite retrieved sources with links.
- FR-2.5 Support follow-ups with context carryover.
- FR-2.6 On skill-path questions, trigger gap analysis + roadmap generation rather than generic advice.

### FR-3 Skill Intelligence Engine
- FR-3.1 Extract skills (languages, frameworks, libraries, DBs, tools, cloud, AI frameworks, soft skills, certs) from resume, GitHub, LinkedIn, chat.
- FR-3.2 Normalize to a canonical taxonomy (ESCO/O*NET-aligned).
- FR-3.3 Maintain a per-user dynamic skill graph with proficiency + evidence + recency.

### FR-4 Skill Gap Analyzer
- FR-4.1 Compare user skills vs. target roles (ML Eng, Data Scientist, AI Eng, SWE, Backend, Frontend, Full-Stack, Data Eng).
- FR-4.2 Output per missing skill: importance score, estimated learning time, recommended order, difficulty, confidence.

### FR-5 Adaptive Roadmap Generator
- FR-5.1 Generate a sequenced, milestone-based roadmap from gaps + hours + goals.
- FR-5.2 Re-plan automatically on early completion, skipped topics, or market shift.
- FR-5.3 Persist roadmap versions and diffs.

### FR-6 Hybrid Recommendation Engine
- FR-6.1 Recommend courses, books, articles, videos, certs, coding platforms, OSS projects, repos, Kaggle, internships, papers, hackathons, conferences, communities.
- FR-6.2 Combine content-based, collaborative, semantic/embedding, knowledge-graph, user-history, and LLM-reasoning signals.
- FR-6.3 Each item includes an explanation: why suggested, which gap it addresses, employability impact, confidence.

### FR-7 Resume Intelligence
- FR-7.1 Parse resume; compute ATS score.
- FR-7.2 Detect weak sections, missing keywords, weak projects.
- FR-7.3 Rewrite/strengthen bullets; suggest achievements and formatting.

### FR-8 GitHub Intelligence
- FR-8.1 Analyze repos, commit history, consistency, complexity, README/doc quality, languages, architecture.
- FR-8.2 Produce GitHub Health, Repository, Project Diversity, Recruiter Impression scores.

### FR-9 Job Market Intelligence
- FR-9.1 Scheduled ingestion of job/market signals (trending tech, in-demand skills, hiring companies, salary, certs, interview patterns, framework popularity, regional demand).
- FR-9.2 Continuously refresh recommendations and roadmaps from live signals.

### FR-10 Project Recommendation Engine
- FR-10.1 Recommend projects by current skills, target role, available time, experience, difficulty, portfolio gaps.
- FR-10.2 Each includes learning outcomes, architecture, tech, duration, recruiter impact, GitHub structure.

### FR-11 Interview Preparation
- FR-11.1 Generate technical, HR, coding, system-design, and AI/ML questions.
- FR-11.2 Provide hints, feedback, scoring, improvement suggestions.
- FR-11.3 Company-specific prep plans (Google, Microsoft, Amazon, NVIDIA, startups).

### FR-12 Dashboard & Analytics
- FR-12.1 Skill radar, learning progress, roadmap timeline, gap heatmap, weekly progress, interview readiness, resume score, GitHub score, readiness score, market trends, recommendation history, goal tracking.

### FR-13 Engagement
- FR-13.1 Weekly AI Mentor report.
- FR-13.2 Intelligent notifications (deadlines, new courses, emerging tech, hackathons, Kaggle, internships).
- FR-13.3 Gamification: XP, badges, streaks, milestones, optional leaderboard.

### FR-14 Exports
- FR-14.1 PDF export of reports, roadmap, improved resume, portfolio summary.

### FR-15 Auth & Accounts
- FR-15.1 Email + OAuth (Google, GitHub) sign-in.
- FR-15.2 Role-based access (user, admin).
- FR-15.3 Data export + account deletion (privacy).

---

## 4. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-1 | Performance | Chat first-token < 2s p95; non-LLM API < 300ms p95. |
| NFR-2 | Scalability | Stateless API; horizontal scale; async workers for heavy jobs. |
| NFR-3 | Availability | 99.5% target; graceful LLM/degradation fallbacks. |
| NFR-4 | Security | OWASP Top 10; encrypted secrets; JWT; input validation; rate limiting. |
| NFR-5 | Privacy | GDPR-style export/delete; PII minimization; resume data encrypted at rest. |
| NFR-6 | Observability | Structured logs, traces (LangSmith), metrics (Prometheus), dashboards (Grafana). |
| NFR-7 | Reliability | Idempotent jobs; retries w/ backoff; dead-letter queues. |
| NFR-8 | Maintainability | Clean/modular architecture; typed; documented; >70% core coverage. |
| NFR-9 | Cost | LLM tiering (Haiku→Sonnet→Opus); caching; token budgeting per request. |
| NFR-10 | Accessibility | WCAG 2.1 AA; responsive; keyboard nav. |
| NFR-11 | Explainability | No recommendation without a machine- and human-readable rationale. |
| NFR-12 | Portability | Dockerized; 12-factor config via env. |

---

## 5. Constraints & Assumptions
- LLM provider: Anthropic Claude (Opus 4.8 / Sonnet 5 / Haiku 4.5).
- External data via public datasets + APIs; respect ToS and rate limits.
- Single-region MVP; multi-region deferred.
- Embeddings via Voyage AI (swap-able behind an interface).

## 6. Out of Scope (MVP)
- Native mobile apps (responsive web only).
- Real recruiter marketplace / payments.
- Voice AI (planned post-MVP).
- Real-time collaborative editing.

## 7. Acceptance Criteria (MVP exit)
- User completes onboarding → Career Twin persisted.
- Chat answers with citations and triggers gap+roadmap on skill-path queries.
- Resume upload → ATS score + rewrites.
- GitHub username → scores.
- Dashboard renders readiness score + skill radar + roadmap timeline.
- Every recommendation shows an explanation.
