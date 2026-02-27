from __future__ import annotations
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="userrole"), nullable=False, default=UserRole.user)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    identity_profile: Mapped[UserIdentityProfile | None] = relationship(
        "UserIdentityProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    body_metrics: Mapped[list[UserBodyMetrics]] = relationship(
        "UserBodyMetrics", back_populates="user", cascade="all, delete-orphan"
    )
    diagnoses: Mapped[list[Diagnosis]] = relationship(
        "Diagnosis", back_populates="user", cascade="all, delete-orphan"
    )
    medications: Mapped[list[Medication]] = relationship(
        "Medication", back_populates="user", cascade="all, delete-orphan"
    )
    tags: Mapped[list[Tag]] = relationship(
        "Tag", back_populates="user", cascade="all, delete-orphan"
    )
    bp_entries: Mapped[list[BPEntry]] = relationship(
        "BPEntry", back_populates="user", cascade="all, delete-orphan"
    )
    symptom_entries: Mapped[list[SymptomEntry]] = relationship(
        "SymptomEntry", back_populates="user", cascade="all, delete-orphan"
    )
    food_entries: Mapped[list[FoodEntry]] = relationship(
        "FoodEntry", back_populates="user", cascade="all, delete-orphan"
    )
    gym_entries: Mapped[list[GymEntry]] = relationship(
        "GymEntry", back_populates="user", cascade="all, delete-orphan"
    )
    food_catalogue: Mapped[list[FoodCatalogueItem]] = relationship(
        "FoodCatalogueItem", back_populates="user", cascade="all, delete-orphan"
    )
    exercise_catalogue: Mapped[list[ExerciseCatalogueItem]] = relationship(
        "ExerciseCatalogueItem", back_populates="user", cascade="all, delete-orphan"
    )
    ai_summaries: Mapped[list[AISummary]] = relationship(
        "AISummary", back_populates="user", cascade="all, delete-orphan"
    )


# Avoid circular import — imported here for type checking only
from .profile import UserIdentityProfile, UserBodyMetrics, Diagnosis, Medication, Tag  # noqa: E402
from .entries import BPEntry, SymptomEntry, FoodEntry, GymEntry, FoodCatalogueItem, ExerciseCatalogueItem, AISummary  # noqa: E402
