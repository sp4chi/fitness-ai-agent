"""
Deterministic (no-LLM) pipeline steps.

Progress tracking and notification sending are both simple, rule-based
operations — query the DB / call an email API and format a string — so
routing them through an LLM agent adds latency and burns rate-limit budget
for no real benefit. They still perform genuine tool calls (DB queries,
Resend API), just invoked directly in Python instead of via agent reasoning.
"""

import json

from app.crew.tools import (
    WorkoutHistoryTool,
    BodyMetricHistoryTool,
    SendNotificationTool,
)

# Goal-based multiplier on a rough activity-adjusted TDEE. Replace with a real
# Mifflin-St Jeor calc (needs age/height/sex) as soon as the profile collects those;
# this is a deterministic placeholder so the LLM never has to guess a calorie number.
_GOAL_MULTIPLIER = {"cut": 0.8, "lose": 0.8, "maintain": 1.0, "bulk": 1.15, "gain": 1.15}


def compute_nutrition_targets(profile_data: dict | str) -> dict:
    """
    Pure Python — no LLM call. Calculates BMR via Mifflin-St Jeor, TDEE,
    and target calories & macros (protein, carbs, fat).
    """
    if isinstance(profile_data, str):
        try:
            p = json.loads(profile_data)
        except Exception:
            p = {}
    else:
        p = profile_data or {}

    age = int(p.get("age") or 30)
    sex = str(p.get("sex") or "male").lower()
    height_cm = float(p.get("height_cm") or 175)
    weight_kg = float(p.get("weight_kg") or 70)
    goal = str(p.get("goal") or "maintain").lower()

    # Mifflin-St Jeor BMR calculation
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if sex == "male" else -161)
    tdee = bmr * 1.375  # Light/moderate activity factor

    if "lose" in goal or "cut" in goal or "weight_loss" in goal:
        kcal = round(tdee - 400)
    elif "build" in goal or "gain" in goal or "muscle" in goal:
        kcal = round(tdee + 300)
    else:
        kcal = round(tdee)

    kcal = max(kcal, 1200)  # Safe lower bound
    protein_g = round(weight_kg * 2.0)
    fat_g = round((kcal * 0.25) / 9)
    carbs_g = round(max(kcal - (protein_g * 4 + fat_g * 9), 0) / 4)

    return {
        "kcal": kcal,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
    }

_workout_history_tool = WorkoutHistoryTool()
_body_metric_tool = BodyMetricHistoryTool()
_notification_tool = SendNotificationTool()


def compute_progress_summary(user_id: int) -> str:
    """Pulls real workout and body-metric logs from the database and formats a trend summary."""
    workouts = json.loads(_workout_history_tool._run(user_id=user_id, limit=20))
    metrics = json.loads(_body_metric_tool._run(user_id=user_id, limit=20))

    if not workouts and not metrics:
        return "No workout or body-metric history yet — this is your first plan."

    lines = []

    if workouts:
        exercise_counts: dict[str, int] = {}
        for w in workouts:
            exercise_counts[w["exercise"]] = exercise_counts.get(w["exercise"], 0) + 1
        top_exercise = max(exercise_counts, key=exercise_counts.get)
        lines.append(
            f"Logged {len(workouts)} recent workout entries, most frequently: {top_exercise}."
        )
    else:
        lines.append("No workouts logged yet.")

    if len(metrics) >= 2:
        newest, oldest = metrics[0], metrics[-1]
        if newest.get("weight_kg") is not None and oldest.get("weight_kg") is not None:
            delta = newest["weight_kg"] - oldest["weight_kg"]
            direction = "down" if delta < 0 else "up" if delta > 0 else "unchanged"
            lines.append(
                f"Weight trend: {direction} {abs(delta):.1f} kg over the last {len(metrics)} entries."
            )
    elif len(metrics) == 1:
        lines.append(
            f"Only one body-metric entry logged so far ({metrics[0].get('weight_kg')} kg) — not enough for a trend yet."
        )
    else:
        lines.append("No body-metric entries logged yet.")

    return " ".join(lines)


def send_plan_email(to_email: str, plan_summary: str, progress_summary: str) -> str:
    """Templates the final plan into an email and sends it via the real Resend API tool."""
    subject = "Your updated fitness plan is ready"
    body = (
        "Hi,\n\n"
        "Here is your latest AI-generated fitness plan:\n\n"
        f"{plan_summary}\n\n"
        "Progress summary:\n"
        f"{progress_summary}\n\n"
        "Stay consistent!\n"
        "— Your AI Fitness Coach"
    )
    return _notification_tool._run(to_email=to_email, subject=subject, body=body)
