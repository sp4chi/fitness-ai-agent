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

def _get_default_model() -> str:
    model = os.getenv("CREW_LLM_MODEL")
    if model:
        if "gemini" in model.lower():
            return "gemini/gemini-pro"
        return model
    if os.getenv("GEMINI_API_KEY"):
        return "gemini/gemini-pro"
    return "groq/llama-3.1-8b-instant"


# Two LLM configs: the profile agent only extracts fields (small budget needed);
# the other three plan/reason, so they get a bit more completion headroom.
llm_extract = LLM(model=_get_default_model(), temperature=0.1, max_tokens=200)
llm_plan = LLM(model=_get_default_model(), temperature=0.3, max_tokens=400)


def build_profile_agent() -> Agent:
    return Agent(
        role="Profile Analyst",
        goal="Extract training/diet constraints as JSON.",
        backstory="Certified intake specialist. Output structured JSON only, no prose.",
        llm=llm_extract,
        tools=[],
        verbose=True,
        allow_delegation=False,
    )


def build_workout_planner_agent() -> Agent:
    return Agent(
        role="Workout Planner",
        goal="Build a weekly workout split using real exercises from the lookup tool.",
        backstory="Strength coach. Always look up real exercises; never invent names.",
        llm=llm_plan,
        tools=[ExerciseDBTool()],
        verbose=True,
        allow_delegation=False,
    )


def build_nutrition_agent() -> Agent:
    return Agent(
        role="Nutrition Planner",
        goal="Build a daily meal plan hitting the given calorie/macro targets using real recipes.",
        backstory="Dietitian. Always use the recipe lookup tool; respect exclusions exactly.",
        llm=llm_plan,
        tools=[NutritionAPITool()],
        verbose=True,
        allow_delegation=False,
    )


def build_safety_agent() -> Agent:
    return Agent(
        role="Safety Reviewer",
        goal="Flag or fix any workout exercise unsafe for the stated injuries, using the safety tool.",
        backstory="Physiotherapist. Always check the safety knowledge base before approving.",
        llm=llm_plan,
        tools=[InjurySafetyRAGTool()],
        verbose=True,
        allow_delegation=False,
    )
