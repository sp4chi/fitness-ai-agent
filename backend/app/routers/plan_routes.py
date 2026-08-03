import json
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import User, Profile, Plan, WorkoutLog, BodyMetricLog
from app.schemas import (
    ProfileUpdate,
    ProfileOut,
    PlanRequest,
    PlanOut,
    WorkoutLogCreate,
    BodyMetricCreate,
)
from app.auth import get_current_user
from app.crew.crew import run_fitness_crew

router = APIRouter(tags=["fitness"])

# In-memory store for background job status
JOBS: Dict[str, Dict[str, Any]] = {}


def _run_crew_job(job_id: str, profile_summary: str, user_id: int, user_email: str):
    JOBS[job_id]["status"] = "running"
    try:
        result_text = run_fitness_crew(profile_summary, user_id, user_email)
        
        db = SessionLocal()
        try:
            plan = Plan(user_id=user_id, plan_type="combined", content_json=result_text)
            db.add(plan)
            db.commit()
            db.refresh(plan)
            plan_id = plan.id
        finally:
            db.close()
            
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["plan_id"] = plan_id
        JOBS[job_id]["result"] = result_text
    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)


@router.put("/profile", response_model=ProfileOut)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    return profile


@router.post("/plan/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_plan(
    payload: PlanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kicks off the multi-agent CrewAI crew as a background task.
    Returns a job_id immediately so the client can poll /plan/status/{job_id}.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please complete your profile before generating a plan.")

    profile_summary = json.dumps(
        {
            "age": profile.age,
            "sex": profile.sex,
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            "goal": profile.goal,
            "experience_level": profile.experience_level,
            "injuries": profile.injuries,
            "dietary_preferences": profile.dietary_preferences,
            "days_per_week": profile.days_per_week,
            "extra_notes": payload.notes,
        }
    )

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "plan_id": None,
        "result": None,
        "error": None,
    }

    background_tasks.add_task(_run_crew_job, job_id, profile_summary, current_user.id, current_user.email)

    return {"job_id": job_id, "status": "pending"}


@router.get("/plan/status/{job_id}")
def get_plan_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/plan/history", response_model=list[PlanOut])
def plan_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Plan).filter(Plan.user_id == current_user.id).order_by(Plan.created_at.desc()).all()


@router.post("/logs/workout")
def log_workout(payload: WorkoutLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = WorkoutLog(user_id=current_user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    return {"status": "logged"}


@router.post("/logs/body-metric")
def log_body_metric(payload: BodyMetricCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    log = BodyMetricLog(user_id=current_user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    return {"status": "logged"}
