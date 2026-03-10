import os
import uuid
from datetime import datetime
from sqlalchemy import (Column, String, DateTime, Boolean, Date, func,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine

# ---------------------------------------------------------------------------
# Database URL handling with auto‑fix for legacy schemes
# ---------------------------------------------------------------------------
raw_url = os.getenv("DATABASE_URL", os.getenv("POSTGRES_URL", "sqlite:///./app.db"))
if raw_url.startswith("postgresql+asyncpg://"):
    raw_url = raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
elif raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg://")

# Add SSL mode when connecting to a remote Postgres (not localhost) and not SQLite
if raw_url.startswith("postgresql+psycopg://") and "localhost" not in raw_url and "127.0.0.1" not in raw_url:
    if "?" in raw_url:
        raw_url += "&sslmode=require"
    else:
        raw_url += "?sslmode=require"

engine = create_engine(raw_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# ---------------------------------------------------------------------------
# Table name prefix – all tables start with "sl_" (StreakLite)
# ---------------------------------------------------------------------------
TABLE_PREFIX = "sl_"

class Session(Base):
    __tablename__ = f"{TABLE_PREFIX}sessions"
    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    habits = relationship("Habit", back_populates="session")

    __table_args__ = (
        Index("idx_sessions_last_active", "last_active_at"),
    )

class Habit(Base):
    __tablename__ = f"{TABLE_PREFIX}habits"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey(f"{TABLE_PREFIX}sessions.session_id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_premium = Column(Boolean, server_default="false", nullable=False)

    session = relationship("Session", back_populates="habits")
    checks = relationship("HabitCheck", back_populates="habit", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("session_id", "name", name="uq_habit_name_per_session"),
        Index("idx_habits_session", "session_id"),
    )

class HabitCheck(Base):
    __tablename__ = f"{TABLE_PREFIX}habit_checks"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    habit_id = Column(String, ForeignKey(f"{TABLE_PREFIX}habits.id"), nullable=False)
    check_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    habit = relationship("Habit", back_populates="checks")

    __table_args__ = (
        UniqueConstraint("habit_id", "check_date", name="uq_habit_check_per_day"),
        Index("idx_habit_checks_habit", "habit_id"),
        Index("idx_habit_checks_date", "check_date"),
    )
