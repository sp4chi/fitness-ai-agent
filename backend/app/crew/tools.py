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
        "Looks up real exercises for a given muscle group and equipment type from the "
        "ExerciseDB API. Returns exercise name, target muscle, equipment, and instructions. "
        "muscle_group MUST be one of: abductors, abs, adductors, biceps, calves, "
        "cardiovascular system, delts, forearms, glutes, hamstrings, lats, "
        "levator scapulae, pectorals, quads, serratus anterior, spine, traps, "
        "triceps, upper back. Use 'pectorals' for chest, 'quads' or 'hamstrings' for legs, "
        "'lats' or 'upper back' for back, 'delts' for shoulders."
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
        normalized = self._ALIASES.get(normalized, normalized)

        if normalized not in self._VALID_TARGETS:
            return json.dumps(
                {
                    "error": f"'{muscle_group}' is not a valid ExerciseDB target.",
                    "valid_targets": sorted(self._VALID_TARGETS),
                }
            )

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
                    "equipment": ex.get("equipment"),
                    "target": ex.get("target"),
                    "instructions": ex.get("instructions", [])[:2],
                }
                for ex in data
                if equipment.lower() in ex.get("equipment", "").lower()
                or equipment == "any"
            ][:8]
            if not filtered:
                filtered = data[:5]
            return json.dumps(filtered)
        except requests.exceptions.HTTPError as e:
            return json.dumps(
                {
                    "error": f"ExerciseDB lookup failed: {e}",
                    "response_body": resp.text[:300] if "resp" in dir() else None,
                }
            )
        except Exception as e:
            return json.dumps({"error": f"ExerciseDB lookup failed: {e}"})


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
        "Searches the Spoonacular API for real recipes matching a diet type, calorie target, "
        "and ingredient exclusions. Returns recipe name, calories, protein/carbs/fat, and a source link."
    )
    args_schema: type[BaseModel] = RecipeSearchInput

    def _run(self, diet: str, target_calories: int, exclude: str = "") -> str:
        api_key = os.getenv("SPOONACULAR_API_KEY")
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "apiKey": api_key,
            "diet": diet,
            "maxCalories": target_calories + 150,
            "minCalories": max(target_calories - 150, 0),
            "excludeIngredients": exclude,
            "addRecipeNutrition": True,
            "number": 5,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("results", [])
            simplified = []
            for r in data:
                nutrients = {
                    n["name"]: n["amount"]
                    for n in r.get("nutrition", {}).get("nutrients", [])
                    if n["name"] in ("Calories", "Protein", "Carbohydrates", "Fat")
                }
                simplified.append(
                    {
                        "title": r.get("title"),
                        "nutrients": nutrients,
                        "sourceUrl": r.get("sourceUrl"),
                    }
                )
            return json.dumps(simplified)
        except Exception as e:
            return json.dumps({"error": f"Nutrition lookup failed: {e}"})


# ---------------------------------------------------------------------------
# 3. RAG lookup over injury / exercise-safety documents (Safety Check agent)
# ---------------------------------------------------------------------------
class SafetyLookupInput(BaseModel):
    query: str = Field(
        ...,
        description="Description of exercise(s) or condition to check, e.g. 'squats with prior ACL surgery'",
    )


class InjurySafetyRAGTool(BaseTool):
    name: str = "injury_safety_knowledge_search"
    description: str = (
        "Searches a vector database of exercise-science and injury-contraindication documents "
        "to check whether a proposed exercise is safe given a user's stated injury or condition. "
        "Returns the most relevant guidance passages."
    )
    args_schema: type[BaseModel] = SafetyLookupInput

    def _run(self, query: str) -> str:
        import chromadb
        from chromadb.utils import embedding_functions

        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
        client = chromadb.PersistentClient(path=persist_dir)
        embed_fn = embedding_functions.DefaultEmbeddingFunction()
        collection = client.get_or_create_collection(
            name="injury_safety_docs", embedding_function=embed_fn
        )

        if collection.count() == 0:
            return json.dumps(
                {
                    "warning": "Knowledge base is empty. Run scripts/ingest_docs.py first."
                }
            )

        results = collection.query(query_texts=[query], n_results=4)
        passages = results.get("documents", [[]])[0]
        return json.dumps({"query": query, "passages": passages})


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
