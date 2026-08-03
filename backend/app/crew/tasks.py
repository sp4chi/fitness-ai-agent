from typing import List, Optional
from crewai import Task, Agent
from pydantic import BaseModel


class ProfileConstraints(BaseModel):
    goal: str
    equipment: str
    days: int
    injuries: List[str] = []
    diet: str
    experience: str
    weight_kg: Optional[float] = None


def build_profile_task(profile_agent: Agent, profile_summary: str) -> Task:
    """Standalone task — run this crew alone first so its JSON output can drive
    the deterministic nutrition-target calc before the remaining tasks are built."""
    return Task(
        description=(
            f"Profile:\n{profile_summary}\n\n"
            "Extract goal, equipment, days/week, injuries, diet, experience as JSON."
        ),
        expected_output="JSON matching the schema. No prose.",
        agent=profile_agent,
        output_pydantic=ProfileConstraints,
    )


def build_downstream_tasks(
    workout_agent: Agent,
    nutrition_agent: Agent,
    safety_agent: Agent,
    constraints: ProfileConstraints,
    nutrition_targets: dict,
) -> list[Task]:
    """Workout/Nutrition/Safety tasks, built after the profile JSON + deterministic
    nutrition targets are already known — no need to re-pass the full profile context."""

    plan_workout = Task(
        description=(
            f"Constraints: goal={constraints.goal}, equipment={constraints.equipment}, "
            f"days={constraints.days}, experience={constraints.experience}.\n"
            "Build a weekly split. Use exercise_database_lookup for 3-4 exercises/day with sets/reps."
        ),
        expected_output="Day-by-day plan, under 250 words.",
        agent=workout_agent,
    )

    plan_nutrition = Task(
        description=(
            f"Diet={constraints.diet}. Daily targets: {nutrition_targets['kcal']} kcal, "
            f"{nutrition_targets['protein_g']}g protein, {nutrition_targets['carbs_g']}g carbs, "
            f"{nutrition_targets['fat_g']}g fat.\n"
            "Use recipe_and_macro_lookup per meal (breakfast/lunch/dinner/snack) to hit these targets."
        ),
        expected_output="Meal plan: recipe names + kcal/macros per meal, under 250 words.",
        agent=nutrition_agent,
    )

    check_safety = Task(
        description=(
            f"Injuries: {constraints.injuries or 'none stated'}.\n"
            "Check the workout plan with injury_safety_knowledge_search. Fix/replace risky exercises."
        ),
        expected_output="Revised plan + brief safety notes, under 250 words.",
        agent=safety_agent,
        context=[plan_workout],
    )

    return [plan_workout, plan_nutrition, check_safety]
