import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
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


@router.post("/plan/generate")
def generate_plan(
    payload: PlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kicks off the full CrewAI crew: Profile -> Workout -> Nutrition -> Safety -> Progress -> Notification.
    This is a synchronous call for simplicity; for production, run it as a background task/queue
    and poll for status instead of blocking the request.
    """
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
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

    result_text = run_fitness_crew(profile_summary, current_user.id, current_user.email)

    plan = Plan(user_id=current_user.id, plan_type="combined", content_json=result_text)
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {"plan_id": plan.id, "result": result_text}


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
