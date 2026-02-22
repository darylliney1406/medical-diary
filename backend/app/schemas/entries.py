from __future__ import annotations
import uuid
from datetime import datetime, date, time
from pydantic import BaseModel, ConfigDict, field_validator
from ..models.entries import MealType, CatalogueCategory, SummaryType
from .profile import TagOut


# ── Blood Pressure ──────────────────────────────────────────────────────────

class BPReadingCreate(BaseModel):
    systolic: int
    diastolic: int
    pulse: int | None = None
    recorded_at: datetime
    order_index: int = 0

    @field_validator("systolic")
    @classmethod
    def systolic_range(cls, v: int) -> int:
        if not 50 <= v <= 300:
            raise ValueError("Systolic must be between 50 and 300")
        return v

    @field_validator("diastolic")
    @classmethod
    def diastolic_range(cls, v: int) -> int:
        if not 30 <= v <= 200:
            raise ValueError("Diastolic must be between 30 and 200")
        return v


class BPReadingOut(BPReadingCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bp_entry_id: uuid.UUID


class BPEntryCreate(BaseModel):
    entry_date: date
    notes: str | None = None
    tag_ids: list[uuid.UUID] = []
    readings: list[BPReadingCreate]

    @field_validator("readings")
    @classmethod
    def max_readings(cls, v: list) -> list:
        if len(v) > 3:
            raise ValueError("A BP entry can have at most 3 readings")
        if len(v) == 0:
            raise ValueError("At least one reading is required")
        return v


class BPEntryUpdate(BaseModel):
    entry_date: date | None = None
    notes: str | None = None
    tag_ids: list[uuid.UUID] | None = None
    readings: list[BPReadingCreate] | None = None


class BPEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    entry_date: date
    notes: str | None
    readings: list[BPReadingOut]
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime


# ── Symptom ─────────────────────────────────────────────────────────────────

class SymptomEntryCreate(BaseModel):
    entry_date: date
    entry_time: time
    description: str
    severity: int | None = None
    notes: str | None = None
    tag_ids: list[uuid.UUID] = []

    @field_validator("severity")
    @classmethod
    def severity_range(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 10:
            raise ValueError("Severity must be between 1 and 10")
        return v


class SymptomEntryUpdate(BaseModel):
    entry_date: date | None = None
    entry_time: time | None = None
    description: str | None = None
    severity: int | None = None
    notes: str | None = None
    tag_ids: list[uuid.UUID] | None = None


class SymptomEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    entry_date: date
    entry_time: time
    description: str
    severity: int | None
    notes: str | None
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime


# ── Food & Drink ─────────────────────────────────────────────────────────────

class FoodCatalogueItemCreate(BaseModel):
    name: str
    category: CatalogueCategory
    typical_portion: str | None = None
    notes: str | None = None


class FoodCatalogueItemUpdate(BaseModel):
    name: str | None = None
    category: CatalogueCategory | None = None
    typical_portion: str | None = None
    notes: str | None = None


class FoodCatalogueItemOut(FoodCatalogueItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class FoodEntryCreate(BaseModel):
    entry_date: date
    entry_time: time
    meal_type: MealType
    description: str
    quantity: str | None = None
    catalogue_item_id: uuid.UUID | None = None
    notes: str | None = None
    tag_ids: list[uuid.UUID] = []


class FoodEntryUpdate(BaseModel):
    entry_date: date | None = None
    entry_time: time | None = None
    meal_type: MealType | None = None
    description: str | None = None
    quantity: str | None = None
    catalogue_item_id: uuid.UUID | None = None
    notes: str | None = None
    tag_ids: list[uuid.UUID] | None = None


class FoodEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    entry_date: date
    entry_time: time
    meal_type: MealType
    description: str
    quantity: str | None
    catalogue_item_id: uuid.UUID | None
    notes: str | None
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime


# ── Gym ─────────────────────────────────────────────────────────────────────

class GymExerciseCreate(BaseModel):
    machine: str
    duration_min: int | None = None
    sets: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    order_index: int = 0


class GymExerciseOut(GymExerciseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    gym_entry_id: uuid.UUID


class GymEntryCreate(BaseModel):
    entry_date: date
    session_notes: str | None = None
    tag_ids: list[uuid.UUID] = []
    exercises: list[GymExerciseCreate] = []


class GymEntryUpdate(BaseModel):
    entry_date: date | None = None
    session_notes: str | None = None
    tag_ids: list[uuid.UUID] | None = None
    exercises: list[GymExerciseCreate] | None = None


class GymEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    entry_date: date
    session_notes: str | None
    exercises: list[GymExerciseOut]
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime


# ── AI Summary ───────────────────────────────────────────────────────────────

class AISummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    summary_type: SummaryType
    period_start: date
    period_end: date
    content: str
    generated_at: datetime


# ── Calendar ─────────────────────────────────────────────────────────────────

class DayEntryCounts(BaseModel):
    date: date
    counts: dict[str, int]


class CalendarMonthOut(BaseModel):
    year: int
    month: int
    days: list[DayEntryCounts]


# ── Export ───────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    type: str  # 'day', 'week', 'range'
    start_date: date
    end_date: date
    tag_ids: list[uuid.UUID] = []
    include_summary: bool = False
