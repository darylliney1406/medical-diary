import uuid
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from ..models.profile import ActivityLevel


class IdentityProfileUpdate(BaseModel):
    date_of_birth: date | None = None
    nhs_number: str | None = None
    gp_name: str | None = None
    gp_surgery: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    blood_type: str | None = None
    allergies: str | None = None


class IdentityProfileOut(IdentityProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    updated_at: datetime


class BodyMetricsCreate(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    gender: str | None = None
    fat_percentage: float | None = None
    water_percentage: float | None = None
    muscle_mass_percentage: float | None = None
    activity_level: ActivityLevel | None = None


class BodyMetricsOut(BodyMetricsCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    recorded_at: datetime


class DiagnosisCreate(BaseModel):
    condition_name: str
    diagnosing_clinician: str | None = None
    diagnosed_at: date | None = None
    notes: str | None = None


class DiagnosisUpdate(BaseModel):
    condition_name: str | None = None
    diagnosing_clinician: str | None = None
    diagnosed_at: date | None = None
    notes: str | None = None


class DiagnosisOut(DiagnosisCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class MedicationCreate(BaseModel):
    name: str
    dosage: str
    frequency: str
    prescribing_doctor: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None
    is_active: bool = True


class MedicationUpdate(BaseModel):
    name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    prescribing_doctor: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None
    is_active: bool | None = None


class MedicationOut(MedicationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class TagCreate(BaseModel):
    name: str
    colour: str = "#6366f1"


class TagUpdate(BaseModel):
    name: str | None = None
    colour: str | None = None


class TagOut(TagCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID


class FullProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    identity: IdentityProfileOut | None = None
    body_metrics: BodyMetricsOut | None = None
    diagnoses: list[DiagnosisOut] = []
    medications: list[MedicationOut] = []
