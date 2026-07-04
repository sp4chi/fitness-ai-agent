from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdate(BaseModel):
    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goal: Optional[str] = None
    experience_level: Optional[str] = None
    injuries: Optional[str] = None
    dietary_preferences: Optional[str] = None
    days_per_week: Optional[int] = 3


class ProfileOut(ProfileUpdate):
    id: int

    class Config:
        from_attributes = True


class PlanRequest(BaseModel):
    notes: Optional[str] = None  # any extra context user wants to give this run


class PlanOut(BaseModel):
    id: int
    plan_type: str
    content_json: str
    safety_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class WorkoutLogCreate(BaseModel):
    exercise_name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    duration_minutes: Optional[float] = None
    notes: Optional[str] = None


class BodyMetricCreate(BaseModel):
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
