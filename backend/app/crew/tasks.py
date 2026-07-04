from crewai import Task, Agent


def build_tasks(
    profile_agent: Agent,
    workout_agent: Agent,
    nutrition_agent: Agent,
    safety_agent: Agent,
    tracker_agent: Agent,
    notification_agent: Agent,
    profile_summary: str,
    user_id: int,
    user_email: str,
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

    track_progress = Task(
        description=(
            f"The user's database ID is {user_id}. Use workout_history_query and "
            "body_metric_history_query to pull their recent logs and summarize training trends "
            "(volume, consistency, weight trend) in 3-5 sentences. If there is no history yet, say so."
        ),
        expected_output="A short progress summary grounded in actual queried log data (or a note that there is none yet).",
        agent=tracker_agent,
    )

    send_notification = Task(
        description=(
            f"Compose a friendly summary of the final safety-approved workout plan, meal plan, and "
            f"progress summary above. Send it via send_email_notification to {user_email} with subject "
            "'Your updated fitness plan is ready'. Confirm whether the send succeeded."
        ),
        expected_output="Confirmation of whether the email notification was sent successfully.",
        agent=notification_agent,
        context=[check_safety, plan_nutrition, track_progress],
    )

    return [analyze_profile, plan_workout, plan_nutrition, check_safety, track_progress, send_notification]
