# AI Fitness Coach — Backend (FastAPI + CrewAI)

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then fill in your API keys
```

## Ingest the safety knowledge base (RAG)

```bash
python scripts/ingest_docs.py
```

This embeds the markdown files in `data/safety_docs/` into a persistent Chroma
vector store used by the Safety Check agent. Add more `.md`/`.txt` files there
to expand the knowledge base (e.g. shoulder injuries, pregnancy-safe exercise, etc.).

## Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

## Key endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/signup` | Create an account, returns JWT |
| POST | `/auth/login` | Login (OAuth2 form), returns JWT |
| GET/PUT | `/profile` | Read/update fitness profile |
| POST | `/plan/generate` | Dispatches CrewAI pipeline as a background job, returns `job_id` |
| GET | `/plan/status/{job_id}` | Poll background job status (`pending`, `running`, `completed`, `failed`) |
| GET | `/plan/history` | List previously generated plans |
| POST | `/logs/workout` | Log a completed workout |
| POST | `/logs/body-metric` | Log weight/body-fat |

## Agent pipeline (`app/crew/`)

`crew.py` orchestrates a sequential hybrid pipeline:

1. **Profile agent** — turns raw profile data into structured constraints (LLM)
2. **Workout planner agent** — calls the ExerciseDB API tool (LLM + RapidAPI)
3. **Nutrition agent** — calls the Spoonacular API tool (LLM + Spoonacular)
4. **Safety check agent** — RAG lookup against `data/safety_docs/` via Chroma (LLM + Chroma)
5. **Progress tracker** — queries workout/body-metric history directly from SQL DB (Deterministic Python)
6. **Notification sender** — sends the final plan via Resend API (Deterministic Python)

Swap the LLM backing the agents by setting `CREW_LLM_MODEL` in `.env`:
- Groq: `groq/llama-3.1-8b-instant` *(default)* or `groq/llama-3.3-70b-versatile` (`GROQ_API_KEY`)
- Google Gemini: `gemini/gemini-2.5-flash` or `gemini/gemini-3.1` (`GEMINI_API_KEY`)
- OpenAI: `gpt-4o-mini` (`OPENAI_API_KEY`)
- Anthropic: `claude-3-5-sonnet-20241022` (`ANTHROPIC_API_KEY`)

