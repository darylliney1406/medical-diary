"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Enums — checkfirst=True makes each CREATE TYPE idempotent
    postgresql.ENUM("admin", "user", name="userrole").create(bind, checkfirst=True)
    postgresql.ENUM("low", "moderate", "high", "very_high", name="activitylevel").create(bind, checkfirst=True)
    postgresql.ENUM("breakfast", "lunch", "dinner", "snack", "drink", name="mealtype").create(bind, checkfirst=True)
    postgresql.ENUM("food", "drink", name="cataloguecategory").create(bind, checkfirst=True)
    postgresql.ENUM("daily", "weekly", name="summarytype").create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("admin", "user", name="userrole", create_type=False), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("mfa_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("mfa_secret", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "user_identity_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("nhs_number", sa.String(20), nullable=True),
        sa.Column("gp_name", sa.String(255), nullable=True),
        sa.Column("gp_surgery", sa.String(255), nullable=True),
        sa.Column("emergency_contact_name", sa.String(255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(50), nullable=True),
        sa.Column("blood_type", sa.String(10), nullable=True),
        sa.Column("allergies", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "user_body_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("height_cm", sa.Float, nullable=True),
        sa.Column("weight_kg", sa.Float, nullable=True),
        sa.Column("gender", sa.String(50), nullable=True),
        sa.Column("fat_percentage", sa.Float, nullable=True),
        sa.Column("water_percentage", sa.Float, nullable=True),
        sa.Column("muscle_mass_percentage", sa.Float, nullable=True),
        sa.Column("activity_level", postgresql.ENUM("low", "moderate", "high", "very_high", name="activitylevel", create_type=False), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "diagnoses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("condition_name", sa.String(255), nullable=False),
        sa.Column("diagnosing_clinician", sa.String(255), nullable=True),
        sa.Column("diagnosed_at", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "medications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(100), nullable=False),
        sa.Column("prescribing_doctor", sa.String(255), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "tags",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("colour", sa.String(7), nullable=False, server_default="#6366f1"),
    )

    op.create_table(
        "food_catalogue_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", postgresql.ENUM("food", "drink", name="cataloguecategory", create_type=False), nullable=False),
        sa.Column("typical_portion", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "bp_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entry_date", sa.Date, nullable=False, index=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "bp_readings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("bp_entry_id", UUID(as_uuid=True), sa.ForeignKey("bp_entries.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("systolic", sa.Integer, nullable=False),
        sa.Column("diastolic", sa.Integer, nullable=False),
        sa.Column("pulse", sa.Integer, nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "bp_entry_tags",
        sa.Column("bp_entry_id", UUID(as_uuid=True), sa.ForeignKey("bp_entries.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "symptom_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entry_date", sa.Date, nullable=False, index=True),
        sa.Column("entry_time", sa.Time, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "symptom_entry_tags",
        sa.Column("symptom_entry_id", UUID(as_uuid=True), sa.ForeignKey("symptom_entries.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "food_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entry_date", sa.Date, nullable=False, index=True),
        sa.Column("entry_time", sa.Time, nullable=False),
        sa.Column("meal_type", postgresql.ENUM("breakfast", "lunch", "dinner", "snack", "drink", name="mealtype", create_type=False), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("quantity", sa.String(255), nullable=True),
        sa.Column("catalogue_item_id", UUID(as_uuid=True), sa.ForeignKey("food_catalogue_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "food_entry_tags",
        sa.Column("food_entry_id", UUID(as_uuid=True), sa.ForeignKey("food_entries.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "gym_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entry_date", sa.Date, nullable=False, index=True),
        sa.Column("session_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "gym_exercises",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("gym_entry_id", UUID(as_uuid=True), sa.ForeignKey("gym_entries.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("machine", sa.String(255), nullable=False),
        sa.Column("duration_min", sa.Integer, nullable=True),
        sa.Column("sets", sa.Integer, nullable=True),
        sa.Column("reps", sa.Integer, nullable=True),
        sa.Column("weight_kg", sa.Float, nullable=True),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "gym_entry_tags",
        sa.Column("gym_entry_id", UUID(as_uuid=True), sa.ForeignKey("gym_entries.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "ai_summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("summary_type", postgresql.ENUM("daily", "weekly", name="summarytype", create_type=False), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("ai_summaries")
    op.drop_table("gym_entry_tags")
    op.drop_table("gym_exercises")
    op.drop_table("gym_entries")
    op.drop_table("food_entry_tags")
    op.drop_table("food_entries")
    op.drop_table("symptom_entry_tags")
    op.drop_table("symptom_entries")
    op.drop_table("bp_entry_tags")
    op.drop_table("bp_readings")
    op.drop_table("bp_entries")
    op.drop_table("food_catalogue_items")
    op.drop_table("tags")
    op.drop_table("medications")
    op.drop_table("diagnoses")
    op.drop_table("user_body_metrics")
    op.drop_table("user_identity_profiles")
    op.drop_table("users")
    postgresql.ENUM(name="summarytype").drop(bind, checkfirst=True)
    postgresql.ENUM(name="cataloguecategory").drop(bind, checkfirst=True)
    postgresql.ENUM(name="mealtype").drop(bind, checkfirst=True)
    postgresql.ENUM(name="activitylevel").drop(bind, checkfirst=True)
    postgresql.ENUM(name="userrole").drop(bind, checkfirst=True)
