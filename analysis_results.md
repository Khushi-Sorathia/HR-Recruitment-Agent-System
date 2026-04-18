# HR Recruitment Pipeline MVP — Progress Analysis

## Summary

| Area | Scaffolded | Functional | Status |
|---|---|---|---|
| **Resume Ingestion (ATS Agent)** | ✅ | ⚠️ Mocked | ~40% |
| **Technical Interview** | ✅ | ⚠️ Mocked | ~45% |
| **HR Screening** | ✅ | ⚠️ Mocked | ~25% |
| **Interview Scheduling + Email** | ✅ | ❌ Broken | ~20% |
| **HR Dashboard** | ✅ | ⚠️ Hardcoded | ~30% |
| **HR Chatbot** | ✅ | ⚠️ Mocked | ~25% |
| **Infrastructure (Docker, DB, Config)** | ✅ | ⚠️ Partial | ~50% |
| **Frontend Polish & Integration** | ✅ | ❌ Not connected | ~30% |

### **Overall: ~30-35% complete**

---

## Detailed Breakdown

### 1. Resume Ingestion (ATS Agent)

**What's done:**
- [x] `ats_agent.py` — LangGraph `StateGraph` with `ATSState` and `ats_scoring_node`
- [x] Keyword-matching heuristic scoring (mock)
- [x] 80% threshold gate logic
- [x] `POST /api/upload-resume` endpoint exists in `endpoints.py`
- [x] Candidate model saved to DB

**What's missing / broken:**
- [ ] **ATS agent is NOT actually called** from the endpoint — `endpoints.py` hardcodes `ats_score = 85.0` instead of calling `run_ats_pipeline()`
- [ ] No real PDF parsing (just `decode("utf-8")` — PDFs will be garbled)
- [ ] No LLM-based scoring — uses keyword heuristics only
- [ ] No job description matching (just checks if role name appears in resume text)
- [ ] Resume file is not actually sent from the frontend (form exists but `submitResume` mocks `candidateId = 123`)

---

### 2. Technical Interview

**What's done:**
- [x] `interview_agent.py` — LangGraph graph with `generate_question` → `evaluate_answer` nodes
- [x] WebSocket endpoint at `/api/ws/interview/{candidate_id}` in `websockets.py`
- [x] Frontend: 30-second countdown timer with auto-submit
- [x] Frontend: Copy/paste disabled (`onCopy`, `onPaste`, `onCut` handlers)
- [x] WebSocket connection lifecycle managed

**What's missing / broken:**
- [ ] Questions are **template strings**, not LLM-generated based on role/experience
- [ ] Answer evaluation is **mock** — scores by `len(answer) * 2.0`
- [ ] Interview results are **never saved to the database** (no `InterviewQA` writes)
- [ ] No `total_score` update on the `Candidate` model after interview
- [ ] The graph flow has a logic issue — `evaluate_answer` immediately goes to `END`, so it only processes one Q&A per invocation rather than looping properly
- [ ] Frontend doesn't connect after a real resume upload (hardcoded `candidateId = 123`)

---

### 3. HR Screening

**What's done:**
- [x] `screening_agent.py` — LangGraph graph that checks resume for missing info
- [x] Smart question generation: skips "notice period" / "joining date" if already in resume

**What's missing / broken:**
- [ ] **No API endpoint** exposes the screening agent — it's never called
- [ ] **No frontend component** for screening form/interaction
- [ ] No database persistence of screening answers
- [ ] No pipeline stage transition after screening completes
- [ ] Should be conversational (multi-turn) — currently generates questions as a batch

---

### 4. Interview Scheduling + Email

**What's done:**
- [x] `scheduling_email_agent.py` — LangGraph graph with `generate_meeting` → `dispatch_email` nodes
- [x] Gmail API integration code (OAuth flow, send via Gmail API)
- [x] Google dependencies in `requirements.txt`

**What's missing / broken:**
- [ ] **Code has a bug**: `base64.urlsafe_bencode` doesn't exist — should be `base64.urlsafe_b64encode`
- [ ] **No API endpoint** exposes the scheduling agent
- [ ] **No frontend** for collecting candidate availability
- [ ] Meeting link generation is mocked (`mock-meet.com`)
- [ ] No HR simultaneous notification (only sends to candidate)
- [ ] No calendar `.ics` file generation despite `ics` being in requirements
- [ ] No `credentials.json` exists yet (OAuth won't work)

---

### 5. HR Dashboard

**What's done:**
- [x] `HRDashboard.tsx` component with candidate table UI
- [x] Table has columns: Candidate, Role, ATS Score, Stage
- [x] Stage badges with color coding (success, danger)
- [x] Basic layout and styling

**What's missing / broken:**
- [ ] **Data is 100% hardcoded** — two static rows (Jane Doe, John Smith)
- [ ] **No `GET /api/dashboard` call** from the frontend to fetch real data
- [ ] No filtering by role or stage (required by assignment)
- [ ] No candidate detail view or drill-down
- [ ] Missing `total_score` (interview score) column

---

### 6. HR Chatbot

**What's done:**
- [x] `hr_chatbot_agent.py` — LangGraph graph with `parse_intent` → `db_execution` nodes
- [x] WebSocket endpoint at `/api/ws/hr-chatbot`
- [x] Frontend chat UI with send/receive message flow
- [x] Chat log rendering with bot/user message styling

**What's missing / broken:**
- [ ] **Does not actually query the database** — `db_execution_node` returns a hardcoded string
- [ ] Intent parsing is very basic (only handles "how many interviews" and "move candidate")
- [ ] No RAG or LLM-based query understanding
- [ ] Cannot actually change candidate stages via chat
- [ ] No Pydantic validation on chatbot queries

---

### 7. Infrastructure & Tech Stack

**What's done:**
- [x] `docker-compose.yml` with PostgreSQL 16 + FastAPI backend services
- [x] Dockerfile for backend (multi-stage build)
- [x] `.env` files with database and API key config
- [x] Pydantic `Settings` config class
- [x] SQLAlchemy models: `Candidate` and `InterviewQA`
- [x] Pydantic schemas for validation
- [x] CORS middleware configured
- [x] Frontend: Vite + React + TypeScript project initialized
- [x] Frontend: Inter font, dark glassmorphism theme

**What's missing / broken:**
- [ ] Currently falls back to **SQLite** (`sqlite:///./hr_pipeline.db`) — PostgreSQL not connected unless running via Docker
- [ ] Frontend has no production build or Docker service defined
- [ ] No Alembic migrations
- [ ] No test files at all

---

## What Needs to Happen Next (Priority Order)

| Priority | Task | Effort |
|---|---|---|
| 🔴 P0 | Wire `run_ats_pipeline()` into the upload endpoint + add PDF parsing | Small |
| 🔴 P0 | Fix interview agent graph loop to handle multi-question flow correctly | Medium |
| 🔴 P0 | Connect HR Dashboard to `GET /api/dashboard` with real DB data | Small |
| 🔴 P0 | Add filtering (by role, stage) to dashboard endpoint + frontend | Medium |
| 🟡 P1 | Create screening API endpoint + frontend component | Medium |
| 🟡 P1 | Create scheduling API endpoint + frontend for availability | Medium |
| 🟡 P1 | Fix `base64.urlsafe_b64encode` bug in email agent | Tiny |
| 🟡 P1 | Save interview Q&A results to `InterviewQA` table | Small |
| 🟡 P1 | Wire chatbot to actually execute SQL against the DB | Medium |
| 🟢 P2 | Replace mock LLM logic with real OpenAI/Gemini calls | Medium |
| 🟢 P2 | Add `.ics` calendar file generation | Small |
| 🟢 P2 | Add proper PDF text extraction (PyPDF2 or pdfplumber) | Small |
| 🟢 P2 | Polish frontend — make it actually production-worthy | Large |
