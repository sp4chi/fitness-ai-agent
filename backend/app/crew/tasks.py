from crewai import Task, Agent


def build_tasks(
    profile_agent: Agent,
    workout_agent: Agent,
    nutrition_agent: Agent,
    safety_agent: Agent,
    profile_summary: str,
) -> list[Task]:

    analyze_profile = Task(
        description=(
            f"User profile:\n{profile_summary}\n\n"
            "Extract: goal, equipment, schedule, injuries, diet restrictions. Keep concise."
        ),
        expected_output="Bullet list of constraints (under 100 words).",
        agent=profile_agent,
    )

    plan_workout = Task(
        description=(
            "Using the constraints, design a weekly workout split. Use exercise_database_lookup "
            "to pull 3-4 real exercises per day with sets/reps. Be concise."
        ),
        expected_output="Day-by-day workout plan (under 250 words).",
        agent=workout_agent,
        context=[analyze_profile],
    )

    plan_nutrition = Task(
        description=(
            "Using the constraints, use recipe_and_macro_lookup to build a daily meal plan "
            "(breakfast/lunch/dinner/snack). Show calories and macros per meal. Be concise."
        ),
        expected_output="Daily meal plan with recipe names, calories, and macros (under 250 words).",
        agent=nutrition_agent,
        context=[analyze_profile],
    )

    check_safety = Task(
        description=(
            "Review the workout plan for injury risks. For any risky exercise, use "
            "injury_safety_knowledge_search to modify or replace it. Output the final plan with short safety notes."
        ),
        expected_output="Revised safety-approved workout plan and short safety notes (under 250 words).",
        agent=safety_agent,
        context=[plan_workout],
    )

    return [analyze_profile, plan_workout, plan_nutrition, check_safety]
