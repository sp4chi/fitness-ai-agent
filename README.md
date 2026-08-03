# FitSense AI 

A full-stack multi-agent fitness coaching app built with **CrewAI**, **FastAPI**, and **Next.js**.

🚀 **Live Demo:** [https://fitness-ai-agent-bice.vercel.app/](https://fitness-ai-agent-bice.vercel.app/)

## What it does

Generates a personalized weekly workout + nutrition plan, safety-checks it against
real injury-contraindication documents (RAG), reviews the user's logged training
history, and emails the finished plan — using a collaborative multi-agent pipeline:
- **4 LLM-driven agents** (Profile, Workout, Nutrition, Safety RAG)
- **2 deterministic steps** (Progress trends SQL query & Resend email delivery)

## Architecture

```
frontend/  → Next.js 14 app (auth, profile form, dashboard with live polling)
backend/   → FastAPI + CrewAI (JWT auth, SQLite DB, background tasks, Chroma RAG)
```

| Agent / Step       | Action / Tool Called                               | Type |
| ------------------ | -------------------------------------------------- | ---- |
| Profile agent      | Reasoning only — extracts constraints              | LLM  |
| Workout planner    | ExerciseDB API (RapidAPI)                          | LLM  |
| Nutrition agent    | Spoonacular API                                    | LLM  |
| Safety check agent | Chroma vector search over injury-safety docs (RAG) | LLM  |
| Progress tracker   | SQL Database workout/body-metric history lookup    | Code |
| Email notification | Resend API email delivery                          | Code |

The **Crew's sequential process** acts as the orchestrator, routing each task's output as context into the next agent.

## Quickstart

**Backend**

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your API keys
python scripts/ingest_docs.py   # build the RAG knowledge base
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Visit [fitness-ai-agent-bice.vercel.app](https://fitness-ai-agent-bice.vercel.app/), sign up, fill in your profile, and click **Generate my plan**.

## LLM Providers & API Keys

Supports any LLM provider via CrewAI / LiteLLM:

- **Groq** (`GROQ_API_KEY`): `groq/llama-3.1-8b-instant` *(default, 30k TPM)* or `groq/llama-3.3-70b-versatile`
- **Google Gemini** (`GEMINI_API_KEY`): `gemini/gemini-2.5-flash`, `gemini/gemini-3.1`
- **OpenAI** (`OPENAI_API_KEY`): `gpt-4o-mini`, `gpt-4o`
- **Anthropic** (`ANTHROPIC_API_KEY`): `claude-3-5-sonnet-20241022`

**External Tool APIs:**
- [ExerciseDB (RapidAPI)](https://rapidapi.com/justin-WFnsXH_t6/api/exercisedb)
- [Spoonacular](https://spoonacular.com/food-api)
- [Resend](https://resend.com/) (optional — falls back to a dry-run log if unset)

## Deployment Suggestion

- Frontend → Vercel
- Backend → Render (set env vars, run `uvicorn app.main:app --host 0.0.0.0 --port $PORT` as the start command)
- Swap SQLite for Postgres in `DATABASE_URL` for production
