# Manual Test Walkthrough (Weeks 1–7)

A beginner-friendly checklist to verify everything built so far by hand.
Each step has: the command, **what you should see**, and *what it proves*.

Open **two** PowerShell windows: one for the API, one for the web.
Keep a third for one-off commands.

---

## 0. Prerequisites (one-time check)

```powershell
cd D:\CareerGuide
docker --version
```
**See:** a version number. *Proves Docker is installed.*

Make sure Docker Desktop is running (whale icon → "Engine running").

Check your `.env` has the dev LLM set:
```powershell
Select-String -Path .env -Pattern "^LLM_PROVIDER"
```
**See:** `LLM_PROVIDER=groq`. *This is the free LLM used for chat.*

---

## 1. Start the datastores (databases)

```powershell
cd D:\CareerGuide
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml ps
```
**See:** 5 rows, each `STATUS = Up ... (healthy)`:
`postgres, redis, qdrant, neo4j, minio`.

*What these are (plain English):*
- **postgres** – main database (users, profiles, skills).
- **qdrant** – vector database (RAG search).
- **redis** – cache. **neo4j** – graph DB (used later). **minio** – file storage (used later).

*Proves:* your whole data layer is running.

---

## 2. Load the RAG knowledge base (one-time per fresh Qdrant)

```powershell
cd D:\CareerGuide\apps\api
.venv\Scripts\python -m data_seed.seed_taxonomy
.venv\Scripts\python -m data_seed.seed_rag
```
**See (taxonomy):** `seeded 46 skills, 8 roles, 60 requirements`.
**See (rag):** `ingested 6 chunks ...` then two `Q:` blocks where the top result
for "become an ML engineer" is **ML Engineer Roadmap**.

*Proves:* skills/roles are in Postgres, and the career knowledge base is searchable in Qdrant.

---

## 3. Start the backend API

```powershell
cd D:\CareerGuide\apps\api
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```
**See:** `Application startup complete.` (leave this window running)

Open in a browser: **http://localhost:8000/api/v1/health**
**See:** `{"status":"ok"}`.

Open **http://localhost:8000/docs** — this is the interactive API explorer (Swagger).
*Proves:* the backend is up. You'll use `/docs` to test the chatbot later.

---

## 4. Start the frontend (web app)

New PowerShell window:
```powershell
cd D:\CareerGuide\apps\web
npm run dev
```
**See:** `Ready in ...` and `Local: http://localhost:3000`.

Open **http://localhost:3000**.
**See:** landing page "AI Career Copilot" with a "Get started" button.
*Proves:* the frontend is up and talking to the API.

---

## 5. Test auth + onboarding + dashboard (in the browser)

1. Click **Get started** → you're on the login page.
2. Click **"Need an account? Register"**.
3. Enter an email (e.g. `me@test.com`) and a password (8+ chars) → **Create account**.
   **See:** you land on the **Dashboard**, showing your email.
   *Proves:* registration, login, and JWT auth work.

4. On the dashboard click **Start onboarding**.
5. Walk the 6 steps:
   - **Education**: type anything → Next.
   - **Skills**: Languages = `Python, SQL`; Frameworks = `PyTorch, scikit-learn` → Next.
   - **Goal**: pick `ML Engineer`; Interests = `NLP, MLOps` → Next.
   - **Time**: drag hours; pick a learning style → Next.
   - **Targets**: optional company/salary/GitHub → Next.
   - **Review** → **Build my Career Twin**.
   **See:** back on the Dashboard, now populated:
   - a **Career Readiness** gauge with a number (e.g. ~48) and `ml-engineer`,
   - a **Skill Radar** with several axes (Languages, Frameworks, AI/ML…),
   - a **Skills** list showing your skills with numbers.
   *Proves:* the Career Twin is built, skills are canonicalized, and the readiness score is computed.

> Note: "readiness" here is skills-only for now (how well your skills cover the
> target role's requirements). Resume/GitHub/interview parts come in later weeks.

---

## 6. Test the AI chatbot (via /docs — no chat UI yet)

The streaming chat **UI** is Week 8. For now test the chat **API**.

1. Get a token: on the dashboard you're already logged in, but for `/docs` we need
   the token. Easiest: in `/docs`, expand **POST /api/v1/auth/login** → **Try it out**
   → body `{"email":"me@test.com","password":"yourpassword"}` → **Execute**.
   **See:** a response with `access_token`. Copy its value (the long string).

2. Click the green **Authorize** button (top-right of `/docs`), paste the
   `access_token`, click **Authorize** → **Close**.

3. Expand **POST /api/v1/chat/ask** → **Try it out** → body:
   ```json
   { "query": "I know Python and SQL. How do I become an ML Engineer?" }
   ```
   → **Execute**.
   **See:** a JSON response with:
   - `"answer"`: a real, sensible answer written by the LLM,
   - `"intent": "skill_path"`,
   - `"citations"`: a list with titles like `"ML Engineer Roadmap"`.
   *Proves:* the full AI pipeline works — planner routed the question, the retriever
   found relevant knowledge, and the LLM (Groq) wrote a **grounded, cited** answer.

Try another: `{ "query": "What should I learn to build apps with LLMs and RAG?" }`
**See:** an answer citing the AI Engineer Roadmap.

---

## 6b. Test the chat UI (Week 8+)

There's now a real chat page (no more `/docs` needed for chatting).

1. On the Dashboard, click **Chat with mentor** (top-right).
2. Type: `I know Python and SQL. How do I become an ML Engineer?` → **Send**.
   **See:** the answer **types out live, word by word**, then a **Sources** box lists
   `[1] ML Engineer Roadmap`.
3. Click **+ New chat**, ask something else. Refresh the page.
   **See:** both conversations in the left **sidebar**; click one to reopen its history.
   *Proves:* streaming, conversation persistence, citations, and the verification gate
   all work in the real UI.

---

## 7. (Optional) Check retrieval quality + run the tests

RAG eval baseline:
```powershell
cd D:\CareerGuide\apps\api
.venv\Scripts\python -m data_seed.eval_rag
```
**See:** `hit@1 1.0 / mrr 1.0 / recall@5 1.0`. *Proves the search ranks the right role first.*

Automated test suite:
```powershell
.venv\Scripts\python -m pytest -q
```
**See:** `32 passed`. *Proves all backend logic is covered and green.*

---

## Shutting down
- Stop API / web: press `Ctrl+C` in their windows.
- Stop databases (keeps your data): `docker compose -f infra/docker-compose.yml stop`
- Or remove containers (data persists in volumes): `... down`

## If something fails
- API window shows a red error → copy it.
- Chat returns 500 → the LLM key/provider; check `LLM_PROVIDER=groq` and `GROQ_API_KEY` in `.env`,
  and that step 2 (seed_rag) ran so Qdrant has data.
- Dashboard empty after onboarding → make sure the API window is running and shows no errors.
