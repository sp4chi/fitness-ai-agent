import time

from crewai import Crew, Process
from litellm.exceptions import RateLimitError

from app.crew.agents import (
    build_profile_agent,
    build_workout_planner_agent,
    build_nutrition_agent,
    build_safety_agent,
)
from app.crew.tasks import build_tasks
from app.crew.deterministic import compute_progress_summary, send_plan_email


def run_fitness_crew(profile_summary: str, user_id: int, user_email: str) -> str:
    """
    Runs the 4 LLM-driven agents sequentially via CrewAI:
    Profile -> Workout Planner -> Nutrition -> Safety Check.

    Progress tracking and notification sending are deterministic (no LLM call) —
    see app/crew/deterministic.py — since they're simple DB queries / API calls
    with no judgment involved. This keeps LLM calls (and rate-limit exposure)
    down to the 4 steps that actually need reasoning.

    Retries the crew run on a transient LLM rate-limit error (e.g. Groq's
    free-tier tokens-per-minute cap), since that clears on its own within seconds.
    """
    profile_agent = build_profile_agent()
    workout_agent = build_workout_planner_agent()
    nutrition_agent = build_nutrition_agent()
    safety_agent = build_safety_agent()

    tasks = build_tasks(
        profile_agent, workout_agent, nutrition_agent, safety_agent, profile_summary
    )

    crew = Crew(
        agents=[profile_agent, workout_agent, nutrition_agent, safety_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    max_attempts = 3
    backoff_seconds = 15
    last_error: Exception | None = None
    plan_summary = None

    for attempt in range(1, max_attempts + 1):
        try:
            plan_summary = str(crew.kickoff())
            break
        except RateLimitError as e:
            last_error = e
            if attempt == max_attempts:
                raise RuntimeError(
                    f"Crew run failed after {max_attempts} attempts due to LLM rate limiting: {last_error}"
                )
            time.sleep(backoff_seconds)

    progress_summary = compute_progress_summary(user_id)
    notification_result = send_plan_email(user_email, plan_summary, progress_summary)

    return (
        f"{plan_summary}\n\n"
        f"--- Progress summary (deterministic) ---\n{progress_summary}\n\n"
        f"--- Notification result (deterministic) ---\n{notification_result}"
    )
