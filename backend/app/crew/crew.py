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


def _format_token_usage(crew: Crew) -> str:
    """Extracts and logs token usage metrics from CrewAI execution."""
    try:
        metrics = getattr(crew, "usage_metrics", None)
        if not metrics:
            return "Token usage metrics unavailable."

        if hasattr(metrics, "model_dump"):
            data = metrics.model_dump()
        elif isinstance(metrics, dict):
            data = metrics
        else:
            data = {
                "total_tokens": getattr(metrics, "total_tokens", 0),
                "prompt_tokens": getattr(metrics, "prompt_tokens", 0),
                "completion_tokens": getattr(metrics, "completion_tokens", 0),
                "successful_requests": getattr(metrics, "successful_requests", 0),
            }

        total = data.get("total_tokens", 0)
        prompt = data.get("prompt_tokens", 0)
        completion = data.get("completion_tokens", 0)
        requests = data.get("successful_requests", 0)

        usage_str = (
            f"Total Tokens: {total:,} | "
            f"Prompt (Input) Tokens: {prompt:,} | "
            f"Completion (Output) Tokens: {completion:,} | "
            f"Successful Requests: {requests}"
        )
        print(f"\n================ [TOKEN USAGE DEBUG] ================")
        print(usage_str)
        print("======================================================\n")
        return usage_str
    except Exception as err:
        error_msg = f"Could not extract token usage: {err}"
        print(f"[TOKEN USAGE DEBUG] {error_msg}")
        return error_msg


def _task_delay_callback(task_output):
    """Pauses briefly between task executions to space out sliding-window TPM requests."""
    time.sleep(6)


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
        task_callback=_task_delay_callback,
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

    token_usage_debug = _format_token_usage(crew)
    progress_summary = compute_progress_summary(user_id)
    notification_result = send_plan_email(user_email, plan_summary, progress_summary)

    return (
        f"{plan_summary}\n\n"
        f"--- Token Usage Debug ---\n{token_usage_debug}\n\n"
        f"--- Progress summary (deterministic) ---\n{progress_summary}\n\n"
        f"--- Notification result (deterministic) ---\n{notification_result}"
    )
