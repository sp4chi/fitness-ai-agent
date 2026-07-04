from crewai import Crew, Process

from app.crew.agents import (
    build_profile_agent,
    build_workout_planner_agent,
    build_nutrition_agent,
    build_safety_agent,
    build_progress_tracker_agent,
    build_notification_agent,
)
from app.crew.tasks import build_tasks


def run_fitness_crew(profile_summary: str, user_id: int, user_email: str) -> str:
    """
    Assembles the 6-agent crew and runs it sequentially:
    Profile -> Workout Planner -> Nutrition -> Safety Check -> Progress Tracker -> Notification.
    Returns the crew's final textual output (the notification agent's confirmation),
    while each task's intermediate output is available via crew.usage_metrics / task outputs.
    """
    profile_agent = build_profile_agent()
    workout_agent = build_workout_planner_agent()
    nutrition_agent = build_nutrition_agent()
    safety_agent = build_safety_agent()
    tracker_agent = build_progress_tracker_agent()
    notification_agent = build_notification_agent()

    tasks = build_tasks(
        profile_agent,
        workout_agent,
        nutrition_agent,
        safety_agent,
        tracker_agent,
        notification_agent,
        profile_summary,
        user_id,
        user_email,
    )

    crew = Crew(
        agents=[profile_agent, workout_agent, nutrition_agent, safety_agent, tracker_agent, notification_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return str(result)
