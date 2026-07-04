from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    workout_logs = relationship("WorkoutLog", back_populates="user")
    plans = relationship("Plan", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    age = Column(Integer, nullable=True)
    sex = Column(String, nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    goal = Column(String, nullable=True)  # e.g. "lose_weight", "build_muscle", "endurance"
    experience_level = Column(String, nullable=True)  # beginner/intermediate/advanced
    injuries = Column(Text, nullable=True)  # free text, e.g. "left knee ACL surgery 2022"
    dietary_preferences = Column(Text, nullable=True)  # e.g. "vegetarian, no nuts"
    days_per_week = Column(Integer, default=3)

    user = relationship("User", back_populates="profile")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_type = Column(String)  # "workout" or "nutrition"
    content_json = Column(Text)  # serialized plan
    safety_notes = Column(Text, nullable=True)  # output of Safety Check agent
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="plans")


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    exercise_name = Column(String)
    sets = Column(Integer, nullable=True)
    reps = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="workout_logs")


class BodyMetricLog(Base):
    __tablename__ = "body_metric_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    weight_kg = Column(Float, nullable=True)
    body_fat_pct = Column(Float, nullable=True)
