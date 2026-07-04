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
            f"Here is the user's raw profile:\n{profile_summary}\n\n"
            "Extract: (1) training goal, (2) equipment available, (3) days/week, "
            "(4) any injuries/conditions to respect, (5) dietary restrictions. "
            "Output a short structured constraint list other agents can use directly."
        ),
        expected_output="A bulleted constraint list covering goal, equipment, schedule, injuries, and diet.",
        agent=profile_agent,
    )

    plan_workout = Task(
        description=(
            "Using the constraints above, design a weekly workout split. For each training day, "
            "use the exercise_database_lookup tool to pull 4-6 real exercises per muscle group "
            "targeted that day. Include sets/reps appropriate to the user's experience level."
        ),
        expected_output="A day-by-day workout plan (JSON-friendly) listing real exercise names, sets, and reps.",
        agent=workout_agent,
        context=[analyze_profile],
    )

    plan_nutrition = Task(
        description=(
            "Using the constraints above, use the recipe_and_macro_lookup tool to build a daily "
            "meal plan (breakfast/lunch/dinner/snack) that fits the user's calorie target and "
            "dietary restrictions. Show calories and macros per meal from real tool results."
        ),
        expected_output="A daily meal plan (JSON-friendly) with real recipe names, calories, and macros.",
        agent=nutrition_agent,
        context=[analyze_profile],
    )

    check_safety = Task(
        description=(
            "Review the workout plan above against the user's stated injuries/conditions. "
            "For any exercise that looks risky, call the injury_safety_knowledge_search tool "
            "with a specific query (exercise + condition) and use the retrieved guidance to either "
            "approve, modify, or replace that exercise. Produce a final, safety-reviewed workout plan "
            "plus a short list of safety notes citing what you checked."
        ),
        expected_output="A revised, safety-approved workout plan plus a 'Safety notes' section.",
        agent=safety_agent,
        context=[analyze_profile, plan_workout],
    )

    return [analyze_profile, plan_workout, plan_nutrition, check_safety]
