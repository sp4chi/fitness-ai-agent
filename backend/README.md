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
| POST | `/plan/generate` | Kicks off the 6-agent CrewAI crew, returns generated plan |
| GET | `/plan/history` | List previously generated plans |
| POST | `/logs/workout` | Log a completed workout |
| POST | `/logs/body-metric` | Log weight/body-fat |

## Agent pipeline (`app/crew/`)

`crew.py` assembles and runs, in sequence:

1. **Profile agent** — turns raw profile data into constraints
2. **Workout planner agent** — calls the ExerciseDB API tool
3. **Nutrition agent** — calls the Spoonacular API tool
4. **Safety check agent** — RAG lookup against `data/safety_docs/` via Chroma
5. **Progress tracker agent** — queries workout/body-metric history from the DB
6. **Notification agent** — sends the final plan via SendGrid email

Swap the LLM backing the agents by setting `CREW_LLM_MODEL` in `.env`
(e.g. `gpt-4o-mini`, or `claude-sonnet-5` if you configure litellm for Anthropic).
