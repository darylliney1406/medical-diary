from __future__ import annotations
import uuid
import enum
from datetime import datetime, date, time
from sqlalchemy import (
    String, Integer, Float, DateTime, Date, Time, ForeignKey,
    Enum as SAEnum, Text, Table, Column, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


# ── Association tables ──────────────────────────────────────────────────────

bp_entry_tags = Table(
    "bp_entry_tags", Base.metadata,
    Column("bp_entry_id", UUID(as_uuid=True), ForeignKey("bp_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

symptom_entry_tags = Table(
    "symptom_entry_tags", Base.metadata,
    Column("symptom_entry_id", UUID(as_uuid=True), ForeignKey("symptom_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

food_entry_tags = Table(
    "food_entry_tags", Base.metadata,
    Column("food_entry_id", UUID(as_uuid=True), ForeignKey("food_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

gym_entry_tags = Table(
    "gym_entry_tags", Base.metadata,
    Column("gym_entry_id", UUID(as_uuid=True), ForeignKey("gym_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


# ── Enums ───────────────────────────────────────────────────────────────────

class MealType(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"
    drink = "drink"


class CatalogueCategory(str, enum.Enum):
    food = "food"
    drink = "drink"


class SummaryType(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"


# ── Blood Pressure ──────────────────────────────────────────────────────────

class BPEntry(Base):
    __tablename__ = "bp_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="bp_entries")
    readings: Mapped[list[BPReading]] = relationship("BPReading", back_populates="bp_entry", cascade="all, delete-orphan", order_by="BPReading.order_index")
    tags: Mapped[list[Tag]] = relationship("Tag", secondary=bp_entry_tags)


class BPReading(Base):
    __tablename__ = "bp_readings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bp_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bp_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    systolic: Mapped[int] = mapped_column(Integer, nullable=False)
    diastolic: Mapped[int] = mapped_column(Integer, nullable=False)
    pulse: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    bp_entry: Mapped[BPEntry] = relationship("BPEntry", back_populates="readings")


# ── Symptom ─────────────────────────────────────────────────────────────────

class SymptomEntry(Base):
    __tablename__ = "symptom_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    entry_time: Mapped[time] = mapped_column(Time, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="symptom_entries")
    tags: Mapped[list[Tag]] = relationship("Tag", secondary=symptom_entry_tags)


# ── Food & Drink ─────────────────────────────────────────────────────────────

class FoodEntry(Base):
    __tablename__ = "food_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    entry_time: Mapped[time] = mapped_column(Time, nullable=False)
    meal_type: Mapped[MealType] = mapped_column(SAEnum(MealType, name="mealtype"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    catalogue_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("food_catalogue_items.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="food_entries")
    catalogue_item: Mapped[FoodCatalogueItem | None] = relationship("FoodCatalogueItem")
    tags: Mapped[list[Tag]] = relationship("Tag", secondary=food_entry_tags)


class FoodCatalogueItem(Base):
    __tablename__ = "food_catalogue_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[CatalogueCategory] = mapped_column(SAEnum(CatalogueCategory, name="cataloguecategory"), nullable=False)
    typical_portion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="food_catalogue")


# ── Exercise Catalogue ───────────────────────────────────────────────────────

class ExerciseCatalogueItem(Base):
    __tablename__ = "exercise_catalogue_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="exercise_catalogue")


# ── Gym ─────────────────────────────────────────────────────────────────────

class GymEntry(Base):
    __tablename__ = "gym_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    session_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="gym_entries")
    exercises: Mapped[list[GymExercise]] = relationship("GymExercise", back_populates="gym_entry", cascade="all, delete-orphan", order_by="GymExercise.order_index")
    tags: Mapped[list[Tag]] = relationship("Tag", secondary=gym_entry_tags)


class GymExercise(Base):
    __tablename__ = "gym_exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gym_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("gym_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    machine: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    gym_entry: Mapped[GymEntry] = relationship("GymEntry", back_populates="exercises")


# ── AI Summary ───────────────────────────────────────────────────────────────

class AISummary(Base):
    __tablename__ = "ai_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    summary_type: Mapped[SummaryType] = mapped_column(SAEnum(SummaryType, name="summarytype"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="ai_summaries")


from .user import User  # noqa: E402
from .profile import Tag  # noqa: E402
