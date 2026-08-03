"""
Real tool implementations used by the CrewAI agents.
Each tool performs an actual external call (HTTP API, database, vector store,
or email) rather than just letting an LLM "talk" about doing it.
"""

import os
import json
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import WorkoutLog, BodyMetricLog


# ---------------------------------------------------------------------------
# 1. Exercise database lookup (Workout Planner agent)
# ---------------------------------------------------------------------------
class ExerciseSearchInput(BaseModel):
    muscle_group: str = Field(
        ..., description="Target muscle group, e.g. 'chest', 'quads', 'back'"
    )
    equipment: str = Field(
        default="body_weight",
        description="Available equipment, e.g. 'dumbbell', 'body_weight', 'barbell'",
    )


class ExerciseDBTool(BaseTool):
    name: str = "exercise_database_lookup"
    description: str = (
        "Look up 1-3 real exercises for a muscle group + equipment (e.g. 'chest', "
        "'dumbbell'). Everyday terms are auto-mapped; invalid ones return valid options."
    )
    args_schema: type[BaseModel] = ExerciseSearchInput

    # Common everyday terms mapped to ExerciseDB's exact accepted values
    _ALIASES = {
        "chest": "pectorals",
        "arms": "biceps",
        "legs": "quads",
        "back": "lats",
        "shoulders": "delts",
        "core": "abs",
        "cardio": "cardiovascular system",
    }

    _VALID_TARGETS = {
        "abductors",
        "abs",
        "adductors",
        "biceps",
        "calves",
        "cardiovascular system",
        "delts",
        "forearms",
        "glutes",
        "hamstrings",
        "lats",
        "levator scapulae",
        "pectorals",
        "quads",
        "serratus anterior",
        "spine",
        "traps",
        "triceps",
        "upper back",
    }

    def _run(self, muscle_group: str, equipment: str = "body_weight") -> str:
        api_key = os.getenv("EXERCISEDB_API_KEY")
        normalized = muscle_group.strip().lower()
# Simple in-memory LRU cache for external API calls to avoid duplicate payload tokens
_TOOL_CACHE: dict[str, str] = {}


class ExerciseDBTool(BaseTool):
    name: str = "exercise_database_lookup"
    description: str = (
        "Looks up real exercises for a target muscle group. "
        "muscle_group MUST be one of: abductors, abs, adductors, biceps, calves, "
        "cardiovascular system, delts, forearms, glutes, hamstrings, lats, "
        "levator scapulae, pectorals, quads, serratus anterior, spine, traps, "
        "triceps, upper back."
    )
    args_schema: type[BaseModel] = ExerciseSearchInput

    _ALIASES = {
        "chest": "pectorals",
        "arms": "biceps",
        "legs": "quads",
        "back": "lats",
        "shoulders": "delts",
        "core": "abs",
        "cardio": "cardiovascular system",
    }

    _VALID_TARGETS = {
        "abductors", "abs", "adductors", "biceps", "calves",
        "cardiovascular system", "delts", "forearms", "glutes",
        "hamstrings", "lats", "levator scapulae", "pectorals",
        "quads", "serratus anterior", "spine", "traps", "triceps", "upper back"
    }

    def _run(self, muscle_group: str, equipment: str = "body_weight") -> str:
        normalized = muscle_group.strip().lower()
        normalized = self._ALIASES.get(normalized, normalized)

        if normalized not in self._VALID_TARGETS:
            return json.dumps({"error": f"Invalid target '{muscle_group}'"}, separators=(",", ":"))

        cache_key = f"ex_{normalized}_{equipment}"
        if cache_key in _TOOL_CACHE:
            return _TOOL_CACHE[cache_key]

        api_key = os.getenv("EXERCISEDB_API_KEY")
        url = f"https://exercisedb.p.rapidapi.com/exercises/target/{normalized}"
        headers = {
            "X-RapidAPI-Key": api_key or "",
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            filtered = [
                {
                    "name": ex.get("name"),
                    "target": ex.get("target"),
                    "equipment": ex.get("equipment"),
                }
                for ex in data
                if equipment.lower() in ex.get("equipment", "").lower()
                or equipment == "any"
            ][:3]
            if not filtered:
                filtered = [
                    {"name": ex.get("name"), "target": ex.get("target"), "equipment": ex.get("equipment")}
                    for ex in data[:3]
                ]
            res_str = json.dumps(filtered, separators=(",", ":"))
            _TOOL_CACHE[cache_key] = res_str
            return res_str
        except Exception as e:
            return json.dumps({"error": f"Lookup failed: {e}"}, separators=(",", ":"))


# ---------------------------------------------------------------------------
# 2. Nutrition / recipe API lookup (Nutrition agent)
# ---------------------------------------------------------------------------
class RecipeSearchInput(BaseModel):
    diet: str = Field(
        ..., description="Diet type, e.g. 'vegetarian', 'high-protein', 'balanced'"
    )
    target_calories: int = Field(..., description="Target calories for this meal")
    exclude: str = Field(
        default="",
        description="Comma-separated ingredients to exclude, e.g. 'peanuts,shellfish'",
    )


class NutritionAPITool(BaseTool):
    name: str = "recipe_and_macro_lookup"
    description: str = (
        "Searches Spoonacular API for recipes matching diet and calorie targets. "
        "Returns recipe name, calories, protein/carbs/fat."
    )
    args_schema: type[BaseModel] = RecipeSearchInput

    def _run(self, diet: str, target_calories: int, exclude: str = "") -> str:
        cache_key = f"nut_{diet}_{target_calories}_{exclude}"
        if cache_key in _TOOL_CACHE:
            return _TOOL_CACHE[cache_key]

        api_key = os.getenv("SPOONACULAR_API_KEY")
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "apiKey": api_key,
            "diet": diet,
            "maxCalories": target_calories + 150,
            "minCalories": max(target_calories - 150, 0),
            "excludeIngredients": exclude,
            "addRecipeNutrition": True,
            "number": 3,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("results", [])
            wanted = {"Calories": "kcal", "Protein": "protein_g", "Carbohydrates": "carbs_g", "Fat": "fat_g"}
            simplified = []
            for r in data[:3]:
                out = {"title": r.get("title")}
                for n in r.get("nutrition", {}).get("nutrients", []):
                    if n["name"] in wanted:
                        out[wanted[n["name"]]] = round(n["amount"])
                simplified.append(out)
            res_str = json.dumps(simplified, separators=(",", ":"))
            _TOOL_CACHE[cache_key] = res_str
            return res_str
        except Exception as e:
            return json.dumps({"error": f"Nutrition lookup failed: {e}"}, separators=(",", ":"))


# ---------------------------------------------------------------------------
# 3. RAG lookup over injury / exercise-safety documents (Safety Check agent)
# ---------------------------------------------------------------------------
class SafetyLookupInput(BaseModel):
    query: str = Field(
        ...,
        description="Exercise or condition to check, e.g. 'squats prior ACL surgery'",
    )


class InjurySafetyRAGTool(BaseTool):
    name: str = "injury_safety_knowledge_search"
    description: str = (
        "Searches injury-contraindication knowledge base to verify exercise safety."
    )
    args_schema: type[BaseModel] = SafetyLookupInput

    def _run(self, query: str) -> str:
        cache_key = f"rag_{query.strip().lower()}"
        if cache_key in _TOOL_CACHE:
            return _TOOL_CACHE[cache_key]

        import chromadb
        from chromadb.utils import embedding_functions

        default_persist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chroma_store"))
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", default_persist_dir)
        client = chromadb.PersistentClient(path=persist_dir)
        embed_fn = embedding_functions.DefaultEmbeddingFunction()
        collection = client.get_or_create_collection(
            name="injury_safety_docs", embedding_function=embed_fn
        )

        if collection.count() == 0:
            return json.dumps({"warning": "Knowledge base empty"}, separators=(",", ":"))

        results = collection.query(query_texts=[query], n_results=2)
        passages = [p[:150] for p in results.get("documents", [[]])[0]]
        res_str = json.dumps({"passages": passages}, separators=(",", ":"))
        _TOOL_CACHE[cache_key] = res_str
        return res_str


# ---------------------------------------------------------------------------
# 4. Database read/write (Profile + Progress Tracker agents)
# ---------------------------------------------------------------------------
class LogQueryInput(BaseModel):
    user_id: int = Field(..., description="The user's database ID")
    limit: int = Field(default=20, description="How many recent log rows to fetch")


class WorkoutHistoryTool(BaseTool):
    name: str = "workout_history_query"
    description: str = "Queries the database for a user's recent workout logs to analyze training trends."
    args_schema: type[BaseModel] = LogQueryInput

    def _run(self, user_id: int, limit: int = 20) -> str:
        db: Session = SessionLocal()
        try:
            logs = (
                db.query(WorkoutLog)
                .filter(WorkoutLog.user_id == user_id)
                .order_by(WorkoutLog.date.desc())
                .limit(limit)
                .all()
            )
            result = [
                {
                    "date": log.date.isoformat(),
                    "exercise": log.exercise_name,
                    "sets": log.sets,
                    "reps": log.reps,
                    "weight_kg": log.weight_kg,
                    "duration_minutes": log.duration_minutes,
                }
                for log in logs
            ]
            return json.dumps(result)
        finally:
            db.close()


class BodyMetricHistoryTool(BaseTool):
    name: str = "body_metric_history_query"
    description: str = "Queries the database for a user's recent weight/body-fat measurements to compute trends."
    args_schema: type[BaseModel] = LogQueryInput

    def _run(self, user_id: int, limit: int = 20) -> str:
        db: Session = SessionLocal()
        try:
            logs = (
                db.query(BodyMetricLog)
                .filter(BodyMetricLog.user_id == user_id)
                .order_by(BodyMetricLog.date.desc())
                .limit(limit)
                .all()
            )
            result = [
                {
                    "date": m.date.isoformat(),
                    "weight_kg": m.weight_kg,
                    "body_fat_pct": m.body_fat_pct,
                }
                for m in logs
            ]
            return json.dumps(result)
        finally:
            db.close()


# ---------------------------------------------------------------------------
# 5. Notification / email tool (Notification agent)
# ---------------------------------------------------------------------------
class NotificationInput(BaseModel):
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Plain text email body")


class SendNotificationTool(BaseTool):
    name: str = "send_email_notification"
    description: str = "Sends a real email notification (e.g. workout reminder, plan summary) via Resend."
    args_schema: type[BaseModel] = NotificationInput

    def _run(self, to_email: str, subject: str, body: str) -> str:
        api_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("NOTIFICATION_FROM_EMAIL", "onboarding@resend.dev")
        if not api_key:
            return json.dumps(
                {
                    "warning": "RESEND_API_KEY not set — email not actually sent (dry run)."
                }
            )
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": from_email,
                    "to": [to_email],
                    "subject": subject,
                    "text": body,
                },
                timeout=10,
            )
            resp.raise_for_status()
            return json.dumps(
                {"status_code": resp.status_code, "id": resp.json().get("id")}
            )
        except Exception as e:
            return json.dumps({"error": f"Notification send failed: {e}"})
