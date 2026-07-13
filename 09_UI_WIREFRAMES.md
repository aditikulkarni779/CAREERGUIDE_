# 09 — UI / UX & Wireframes

Project: **AI Career Copilot** · Draft v1.0
Design goal: startup-quality SaaS. Clean, data-dense-but-calm, explainable-by-default.

---

## 1. Design System
- Tailwind + shadcn/ui + Radix primitives; dark/light themes.
- Type scale: Inter; numeric mono for scores. 8pt spacing grid.
- Accents: readiness score green→amber→red gradient; skill categories color-coded.
- Every recommendation card has a **"Why?"** affordance (expand → explanation).
- Loading = skeletons; streaming chat = token-by-token; optimistic UI on roadmap toggles.

---

## 2. Screen Map
```
/ (landing) → /login → /onboarding (wizard)
/app
 ├── /dashboard        (home)
 ├── /chat             (mentor)
 ├── /roadmap
 ├── /skills           (skill graph)
 ├── /recommendations
 ├── /resume
 ├── /github
 ├── /projects
 ├── /interview
 ├── /market
 └── /settings
```

---

## 3. Onboarding Wizard (multi-step)
```
[Step 1 Education] ─ [2 Skills/Langs] ─ [3 Interests+Goals] ─
[4 Hours+Learning style] ─ [5 Target companies+salary] ─
[6 Connect GitHub / Upload resume / LinkedIn] ─ [Review → Build Twin]
Progress bar top · Skip-optional · autosave per step
```

---

## 4. Dashboard (home)
```
┌───────────────────────────────────────────────────────────┐
│ Career Readiness  ◑ 68/100   ▲+3 this week   [details]     │
├───────────────┬───────────────┬───────────────────────────┤
│ Skill Radar   │ Gap Heatmap   │ Roadmap Timeline (mini)    │
│   (spider)    │  (role grid)  │  ●──●──○──○  next: Docker   │
├───────────────┼───────────────┼───────────────────────────┤
│ Resume  72    │ GitHub  64    │ Interview Ready  55        │
│  [open]       │  [open]       │  [practice]                │
├───────────────┴───────────────┴───────────────────────────┤
│ This Week (AI Mentor): wins · misses · next steps          │
├───────────────────────────────────────────────────────────┤
│ Market Trends: ▲ LangGraph ▲ Rust ▲ vector DBs             │
│ Recommendations feed (cards w/ Why?) · Goals · Streak 🔥12  │
└───────────────────────────────────────────────────────────┘
```

---

## 5. Chat (mentor)
```
┌──────────────┬────────────────────────────────────────────┐
│ Conversations│  ┌──────────────────────────────────────┐  │
│  • ML path   │  │ user: I know Python & SQL...         │  │
│  • Resume Q  │  │ assistant (streaming):               │  │
│  + New       │  │   reasoning ▸ (collapsible steps)    │  │
│              │  │   answer... [1][2] citations         │  │
│              │  │   ┌ Roadmap generated (6 steps) ──┐  │  │
│              │  │   └ Recommended: 3 courses Why? ──┘  │  │
│              │  └──────────────────────────────────────┘  │
│              │  [ ask a follow-up...................] ➤    │
└──────────────┴────────────────────────────────────────────┘
```

---

## 6. Roadmap
```
Target: ML Engineer   version v3  (re-planned 2d ago · why?)
[Milestone 1 Foundations] ✔ ──▶ [2 ML Core] ◐ ──▶ [3 MLOps] ○
 └ items: skill · est hrs · status toggle · resources ▸
Drag to reorder (manual) · "Re-plan" button · version history
```

---

## 7. Skills (graph)
```
Interactive force graph: nodes=skills (size=proficiency, color=category),
edges=prerequisite/related. Filter by category. Click node → evidence + resources.
Toggle: "show target-role gaps" overlays missing skills (dashed).
```

---

## 8. Resume / GitHub / Interview
- **Resume**: upload dropzone → ATS gauge, section checklist, before/after bullet diff, keyword chips.
- **GitHub**: 4 score gauges + per-repo table (lang, complexity, readme) + improvement checklist.
- **Interview**: pick kind/company → question card → answer box → scored feedback + hints; session summary radar.

---

## 9. Recommendations
```
Filter tabs: Courses | Projects | Repos | Certs | Papers | Events
Card: title · provider · match% · [Why?]→{gap skill, impact, confidence}
      · 👍/👎 feedback · Add to roadmap
```

---

## 10. Accessibility & Responsive
- WCAG 2.1 AA: contrast, focus rings, ARIA on charts (data-table fallback).
- Breakpoints: sidebar collapses < md; dashboard grid reflows to single column on mobile.
- Keyboard: full nav, chat send (Enter), command palette (⌘K) for jump-to.

---

## 11. Wireframe Fidelity Plan
Low-fi (this doc) → Figma mid-fi (before Phase 4 frontend) → shadcn components. Component inventory: `ScoreGauge`, `SkillRadar`, `GapHeatmap`, `RoadmapTimeline`, `RecommendationCard`, `WhyPopover`, `ChatStream`, `SkillGraph`.
