# AI Fitness Coach — Hackathon 2.0 submission

A full-stack multi-agent fitness coaching app built with **CrewAI**, **FastAPI**, and **Next.js**.

## What it does

Generates a personalized weekly workout + nutrition plan, safety-checks it against
real injury-contraindication documents (RAG), reviews the user's logged training
history, and emails the finished plan — using a crew of 6 collaborating agents that
each call a real external tool (API, database, or vector store), not just LLM chat.

## Architecture

```
frontend/  → Next.js 14 app (auth, profile form, plan dashboard)
backend/   → FastAPI + CrewAI (JWT auth, SQLite DB, 6-agent crew, Chroma RAG)
```

| Agent | Tool it calls |
|---|---|
| Profile agent | (reasoning only — extracts constraints) |
| Workout planner | ExerciseDB API |
| Nutrition agent | Spoonacular API |
| Safety check agent | Chroma vector search over injury-safety docs (RAG) |
| Progress tracker | SQLite query (workout & body-metric logs) |
| Notification agent | SendGrid email API |

The **Crew's sequential process** acts as the orchestrator, routing each task's
output as context into the next agent.

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

Visit `http://localhost:3000`, sign up, fill in your profile, and click
**Generate my plan**.

## Required API keys

- An LLM key for CrewAI (OpenAI or Anthropic via litellm)
- [ExerciseDB (RapidAPI)](https://rapidapi.com/justin-WFnsXH_t6/api/exercisedb)
- [Spoonacular](https://spoonacular.com/food-api)
- [SendGrid](https://sendgrid.com/) (optional — falls back to a dry-run log if unset)

## Deployment suggestion

- Frontend → Vercel
- Backend → Railway / Render (set env vars, run `uvicorn` as the start command)
- Swap SQLite for Postgres in `DATABASE_URL` for production
