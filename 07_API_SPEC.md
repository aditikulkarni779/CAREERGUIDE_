# 07 — API Specification

Project: **AI Career Copilot** · Draft v1.0
Base: `/api/v1` · Auth: Bearer JWT · Format: JSON · Streaming: SSE/WebSocket
Full contract published as OpenAPI 3.1 from FastAPI at `/docs`.

---

## Conventions
- Errors: RFC 7807 problem+json `{type,title,status,detail,instance}`.
- Pagination: `?limit=&cursor=`; responses `{items,next_cursor}`.
- Idempotency: `Idempotency-Key` header on POST that mutate/enqueue.
- Rate limit headers: `X-RateLimit-Remaining/Reset`.

---

## 1. Auth
| Method | Path | Body / notes |
|--------|------|--------------|
| POST | `/auth/register` | `{email,password}` |
| POST | `/auth/login` | `{email,password}` → `{access,refresh}` |
| POST | `/auth/oauth/{provider}` | Google/GitHub callback |
| POST | `/auth/refresh` | `{refresh}` → new access |
| POST | `/auth/logout` | invalidate refresh |
| GET  | `/auth/me` | current user |

## 2. Profile / Career Twin
| Method | Path | Notes |
|--------|------|-------|
| GET  | `/profile` | full Twin |
| PUT  | `/profile` | update onboarding fields |
| POST | `/profile/onboarding` | submit onboarding wizard payload |
| GET  | `/profile/skills` | skill graph (nodes+edges) |
| POST | `/profile/skills` | add/adjust a skill manually |
| GET  | `/profile/readiness` | readiness score + components |

## 3. Chat
| Method | Path | Notes |
|--------|------|-------|
| GET  | `/conversations` | list |
| POST | `/conversations` | create → `{id}` |
| GET  | `/conversations/{id}/messages` | history |
| POST | `/conversations/{id}/messages` | `{content}` → **SSE stream** tokens + `citations` + `trace` |
| WS   | `/ws/chat/{id}` | bidirectional streaming alt |
| DELETE | `/conversations/{id}` | remove |

SSE event types: `token`, `citation`, `agent_step`, `recommendation`, `done`, `error`.

## 4. Skill Gap & Roadmap
| Method | Path | Notes |
|--------|------|-------|
| POST | `/gap-analysis` | `{target_role}` → gaps[] scored |
| GET  | `/roadmap` | current roadmap (latest version) |
| POST | `/roadmap/generate` | `{target_role}` → roadmap |
| PATCH| `/roadmap/items/{id}` | `{status}` (todo/doing/done/skipped) → may trigger re-plan |
| GET  | `/roadmap/versions` | version history + diffs |

## 5. Recommendations
| Method | Path | Notes |
|--------|------|-------|
| GET  | `/recommendations?type=` | ranked items w/ explanations |
| POST | `/recommendations/refresh` | recompute now |
| POST | `/recommendations/{id}/feedback` | `{useful:bool}` (feeds collaborative signal) |

## 6. Resume Intelligence
| Method | Path | Notes |
|--------|------|-------|
| POST | `/resume` | multipart upload → `{resume_id}` (async parse) |
| GET  | `/resume/{id}` | parsed + status |
| GET  | `/resume/{id}/score` | ATS score, weak sections, keywords |
| POST | `/resume/{id}/rewrite` | improved bullets/suggestions |

## 7. GitHub Intelligence
| Method | Path | Notes |
|--------|------|-------|
| POST | `/github/analyze` | `{username}` → job id (async) |
| GET  | `/github/{username}` | scores + per-repo breakdown |

## 8. Job Market
| Method | Path | Notes |
|--------|------|-------|
| GET  | `/market/trends?role=&region=` | trending skills/tech/salary |
| GET  | `/market/companies/{name}` | demand + likely interview topics |

## 9. Projects
| Method | Path | Notes |
|--------|------|-------|
| GET  | `/projects/recommendations` | portfolio-gap projects w/ full spec |
| POST | `/projects/architect` | `{idea|role}` → folder/tech/schema/timeline |

## 10. Interview Prep
| Method | Path | Notes |
|--------|------|-------|
| POST | `/interview/sessions` | `{kind,company?}` → session + questions |
| POST | `/interview/sessions/{id}/answer` | `{question_id,answer}` → feedback+score |
| GET  | `/interview/sessions/{id}` | summary + scoring |

## 11. Dashboard / Analytics
| Method | Path | Notes |
|--------|------|-------|
| GET  | `/dashboard` | aggregated widgets payload |
| GET  | `/analytics/progress` | learning progress series |
| GET  | `/analytics/history` | recommendation history |

## 12. Engagement
| Method | Path | Notes |
|--------|------|-------|
| GET  | `/mentor/weekly` | latest weekly report |
| GET  | `/notifications` / PATCH `/notifications/{id}` | list / mark read |
| GET  | `/gamification` | XP, badges, streaks |
| POST | `/export/{kind}` | pdf: report/roadmap/resume/portfolio → file url |

## 13. Admin
| Method | Path | Notes |
|--------|------|-------|
| GET  | `/admin/ingestion` | pipeline health/status |
| POST | `/admin/ingestion/{source}/run` | trigger ingest |
| GET  | `/admin/metrics` | usage + LLM cost |

---

## Example — chat message (SSE)
```
POST /api/v1/conversations/{id}/messages
{ "content": "I know Python and SQL. How do I become an ML Engineer?" }

event: agent_step  data: {"agent":"planner","intent":"skill_path"}
event: token       data: {"t":"Based on your profile"}
event: recommendation data: {"type":"course","title":"...","explanation":{...}}
event: citation    data: {"title":"O*NET ML Eng","url":"..."}
event: done        data: {"roadmap_id":"...","readiness_delta":+3}
```

## Standard error
```json
{ "type":"/errors/rate-limit","title":"Too Many Requests","status":429,
  "detail":"LLM quota exceeded, retry in 20s" }
```
