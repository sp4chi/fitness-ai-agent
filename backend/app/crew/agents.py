"""
Agent definitions for the AI Fitness Coach crew.
Six specialized agents, each with a distinct role and its own real tool(s).
The CrewAI `Crew`/`Process` layer (see crew.py) acts as the orchestrator that
sequences and routes work between them.
"""

import os
from crewai import Agent, LLM

from app.crew.tools import (
    ExerciseDBTool,
    NutritionAPITool,
    InjurySafetyRAGTool,
)

# Point CrewAI's LLM at whichever provider you're using. litellm (used under
# the hood by crewai's LLM class) auto-detects the right API key based on the
# model name prefix. Default here is Groq's free tier — requires GROQ_API_KEY.
# Swap model= for "claude-sonnet-5" (needs ANTHROPIC_API_KEY) or "gpt-4o-mini"
# (needs OPENAI_API_KEY) if you switch providers later.
llm = LLM(
    model=os.getenv("CREW_LLM_MODEL", "groq/llama-3.3-70b-versatile"), temperature=0.3
)


def build_profile_agent() -> Agent:
    return Agent(
        role="Fitness Profile Analyst",
        goal="Turn the user's raw profile data into a clear set of training and dietary constraints.",
        backstory=(
            "You are a certified intake specialist who reads client profiles and extracts the "
            "hard constraints (injuries, equipment, time, dietary restrictions) other coaches must respect."
        ),
        llm=llm,
        tools=[],
        verbose=True,
        allow_delegation=False,
    )


def build_workout_planner_agent() -> Agent:
    return Agent(
        role="Workout Planner",
        goal="Design a realistic weekly workout plan using real exercise data for the user's goal and equipment.",
        backstory=(
            "You are a strength & conditioning coach. You always look up real exercises via the "
            "exercise database tool rather than inventing exercise names or instructions."
        ),
        llm=llm,
        tools=[ExerciseDBTool()],
        verbose=True,
        allow_delegation=False,
    )


def build_nutrition_agent() -> Agent:
    return Agent(
        role="Nutrition Planner",
        goal="Design a daily meal plan hitting the user's calorie/macro targets using real recipes.",
        backstory=(
            "You are a registered dietitian who always grounds meal suggestions in real recipes "
            "pulled from the nutrition API, respecting dietary restrictions exactly."
        ),
        llm=llm,
        tools=[NutritionAPITool()],
        verbose=True,
        allow_delegation=False,
    )


def build_safety_agent() -> Agent:
    return Agent(
        role="Injury Safety Reviewer",
        goal=(
            "Review the proposed workout plan against the user's stated injuries/conditions using "
            "the injury-safety knowledge base, and flag or modify any risky exercises."
        ),
        backstory=(
            "You are a physiotherapist. You NEVER approve a plan without checking it against the "
            "injury-safety knowledge base tool first. You cite the specific guidance you found."
        ),
        llm=llm,
        tools=[InjurySafetyRAGTool()],
        verbose=True,
        allow_delegation=False,
    )
