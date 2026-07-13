# 05 — Multi-Agent Workflows (LangGraph)

Project: **AI Career Copilot** · Draft v1.0

---

## 1. Design Principles
- **Single responsibility** per agent.
- **Explicit state machine** (LangGraph `StateGraph`) — nodes = agents/tools, edges = routing, checkpoints = resumable state.
- **Structured I/O** — every agent returns a Pydantic model, not free text.
- **Guarded output** — Verification + Citation agents gate anything user-facing.
- **Observable** — every node traced in LangSmith with inputs/outputs/tokens.

---

## 2. Agent Roster

| Agent | Responsibility | Model tier |
|-------|----------------|-----------|
| **Planner** | Interpret intent, route to specialists, assemble final response | Sonnet 5 |
| **Chat** | Conversational answering over retrieved context | Sonnet 5 |
| **Skill Extraction** | Parse resume/GitHub/text → normalized skills | Haiku 4.5 |
| **Skill Gap** | User skills vs. role reqs → scored gaps | Sonnet 5 |
| **Roadmap** | Gaps + hours + goals → sequenced plan | Sonnet 5 |
| **Recommendation** | Fuse signals → ranked items + explanations | Sonnet 5 |
| **Resume** | ATS scoring, weak-section detect, bullet rewrite | Sonnet 5 |
| **GitHub** | Repo/commit analysis → scores | Haiku/Sonnet |
| **Job Trend** | Summarize live market signals into guidance | Sonnet 5 |
| **Research** | Deep retrieval over papers/blogs for a topic | Sonnet 5 |
| **Citation** | Attach + validate source references | Haiku 4.5 |
| **Report** | Compose weekly mentor report / PDF content | Opus 4.8 |
| **Notification** | Decide + format proactive notifications | Haiku 4.5 |
| **Analytics** | Aggregate metrics for dashboard summaries | Haiku 4.5 |
| **Verification** | Fact/consistency check before delivery | Opus 4.8 |

---

## 3. Shared Graph State
```python
class CopilotState(TypedDict):
    user_id: str
    twin: TwinSnapshot            # skills, goals, hours, target role
    intent: Intent                # routed category
    query: str
    retrieved: list[Chunk]        # RAG context
    gaps: list[SkillGap]
    roadmap: Roadmap | None
    recommendations: list[Recommendation]
    citations: list[Citation]
    draft: str                    # candidate answer
    verified: bool
    trace: list[StepLog]
```

---

## 4. Master Router Graph

```
                    ┌──────────┐
        query ─────▶│ Planner  │  classify intent
                    └────┬─────┘
        ┌────────────────┼───────────────┬───────────────┬─────────────┐
        ▼                ▼               ▼               ▼             ▼
   [chat/QA]      [skill-path]      [resume]        [github]     [interview]
        │                │               │               │             │
   ┌────▼────┐    ┌──────▼──────┐  ┌─────▼─────┐   ┌─────▼────┐  ┌─────▼─────┐
   │  RAG    │    │ SkillGap →  │  │  Resume   │   │  GitHub  │  │ Interview │
   │  Chat   │    │ Roadmap  →  │  │  Agent    │   │  Agent   │  │  gen/score│
   └────┬────┘    │ Recommend   │  └─────┬─────┘   └────┬─────┘  └─────┬─────┘
        │         └──────┬──────┘        │              │              │
        └────────────────┼───────────────┴──────────────┴──────────────┘
                         ▼
                   ┌───────────┐
                   │ Citation  │
                   └─────┬─────┘
                         ▼
                   ┌───────────┐   fail ─▶ (loop back to specialist, max N)
                   │Verification│
                   └─────┬─────┘
                         ▼  pass
                    stream to user + persist + Twin update event
```

---

## 5. Key Sub-Workflows

### 5.1 Skill-Path ("how do I become X")
1. Planner → intent=`skill_path`, extract target role.
2. Skill Gap agent: load Twin skills + Neo4j role reqs → compute gaps (importance, time, order, difficulty, confidence).
3. RAG: retrieve resources per gap skill.
4. Roadmap agent: sequence gaps into milestones respecting weekly hours + prerequisites (Neo4j `PREREQUISITE_OF`).
5. Recommendation agent: attach courses/projects/repos w/ explanations.
6. Citation + Verification → deliver; persist roadmap (versioned).

### 5.2 Resume Intelligence
Parse (Celery) → Skill Extraction → ATS deterministic scorer + LLM weak-section detect → Resume agent rewrites bullets → update Twin evidence → Recommendation (gap courses/projects).

### 5.3 Adaptive Re-plan (event-driven, no user prompt)
Trigger: `TwinUpdated` | item completed early | nightly market shift.
→ Skill Gap recompute → Roadmap diff → if changed, new roadmap version + Notification agent alerts user with reason.

### 5.4 Weekly Mentor (scheduled)
Analytics agent aggregates week → Report agent (Opus) drafts wins/misses/next-steps/motivation → Verification → PDF export + notification.

---

## 6. Reasoning & Explainability
- Specialist agents use extended thinking for planning; a compact `trace[]` is stored (not always shown).
- Every recommendation object carries `{why, gap_skill_id, impact, confidence}` — enforced by schema; Verification rejects items missing rationale.

## 7. Failure Handling
- Node timeout / tool error → retry (backoff) → fallback tier model → degrade gracefully (partial answer flagged).
- Verification failure loops back to producing agent up to `N=2`, then returns best-effort with a caveat.
- All transitions checkpointed → resumable after crash.

## 8. Tools Available to Agents
`retrieve(query,filters)` · `graph_query(cypher)` · `get_twin(user_id)` · `github_fetch(user)` · `job_market(query)` · `score_resume(doc)` · `web_search(q)` (Research only) · `persist(entity)`.
Tools are typed adapters; agents never call vendor SDKs directly.
