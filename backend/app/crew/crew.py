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

    max_attempts = 5
    last_error: Exception | None = None
    plan_summary = None

    for attempt in range(1, max_attempts + 1):
        try:
            plan_summary = str(crew.kickoff())
            break
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = (
                isinstance(e, RateLimitError)
                or "rate_limit" in err_str
                or "rate limit" in err_str
                or "429" in err_str
                or "tpm" in err_str
                or "resource_exhausted" in err_str
                or "quota" in err_str
            )
            if is_rate_limit:
                last_error = e
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"Crew run failed after {max_attempts} attempts due to LLM rate/quota limiting: {last_error}"
                    )
                # Wait longer (30s, 60s, 90s...) to allow Google AI Studio / Groq 60-second sliding quota windows to reset cleanly.
                wait_seconds = 30 * attempt
                time.sleep(wait_seconds)
            else:
                raise e

    progress_summary = compute_progress_summary(user_id)
    notification_result = send_plan_email(user_email, plan_summary, progress_summary)

    return (
        f"{plan_summary}\n\n"
        f"--- Progress summary (deterministic) ---\n{progress_summary}\n\n"
        f"--- Notification result (deterministic) ---\n{notification_result}"
    )
