import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..models.profile import UserIdentityProfile, UserBodyMetrics, Diagnosis, Medication
from ..schemas.profile import (
    IdentityProfileUpdate, IdentityProfileOut,
    BodyMetricsCreate, BodyMetricsOut,
    DiagnosisCreate, DiagnosisUpdate, DiagnosisOut,
    MedicationCreate, MedicationUpdate, MedicationOut,
    FullProfileOut,
)
from .deps import get_current_user

router = APIRouter()


@router.get("", response_model=FullProfileOut)
async def get_profile(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    identity_result = await session.execute(
        select(UserIdentityProfile).where(UserIdentityProfile.user_id == user.id)
    )
    identity = identity_result.scalar_one_or_none()

    metrics_result = await session.execute(
        select(UserBodyMetrics).where(UserBodyMetrics.user_id == user.id).order_by(UserBodyMetrics.recorded_at.desc())
    )
    latest_metrics = metrics_result.scalars().first()

    diag_result = await session.execute(select(Diagnosis).where(Diagnosis.user_id == user.id))
    med_result = await session.execute(select(Medication).where(Medication.user_id == user.id))

    return FullProfileOut(
        identity=IdentityProfileOut.model_validate(identity) if identity else None,
        body_metrics=BodyMetricsOut.model_validate(latest_metrics) if latest_metrics else None,
        diagnoses=[DiagnosisOut.model_validate(d) for d in diag_result.scalars().all()],
        medications=[MedicationOut.model_validate(m) for m in med_result.scalars().all()],
    )


@router.patch("/identity", response_model=IdentityProfileOut)
async def update_identity(
    body: IdentityProfileUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await session.execute(select(UserIdentityProfile).where(UserIdentityProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserIdentityProfile(user_id=user.id)
        session.add(profile)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.post("/body-metrics", response_model=BodyMetricsOut, status_code=status.HTTP_201_CREATED)
async def add_body_metrics(
    body: BodyMetricsCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    metrics = UserBodyMetrics(user_id=user.id, **body.model_dump())
    session.add(metrics)
    await session.commit()
    await session.refresh(metrics)
    return metrics


# ── Diagnoses ────────────────────────────────────────────────────────────────

@router.get("/diagnoses", response_model=list[DiagnosisOut])
async def list_diagnoses(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await session.execute(select(Diagnosis).where(Diagnosis.user_id == user.id))
    return result.scalars().all()


@router.post("/diagnoses", response_model=DiagnosisOut, status_code=status.HTTP_201_CREATED)
async def create_diagnosis(
    body: DiagnosisCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    diag = Diagnosis(user_id=user.id, **body.model_dump())
    session.add(diag)
    await session.commit()
    await session.refresh(diag)
    return diag


@router.patch("/diagnoses/{diag_id}", response_model=DiagnosisOut)
async def update_diagnosis(
    diag_id: uuid.UUID,
    body: DiagnosisUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    diag = await session.get(Diagnosis, diag_id)
    if not diag or diag.user_id != user.id:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(diag, field, value)
    await session.commit()
    await session.refresh(diag)
    return diag


@router.delete("/diagnoses/{diag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diagnosis(
    diag_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    diag = await session.get(Diagnosis, diag_id)
    if not diag or diag.user_id != user.id:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    await session.delete(diag)
    await session.commit()


# ── Medications ───────────────────────────────────────────────────────────────

@router.get("/medications", response_model=list[MedicationOut])
async def list_medications(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await session.execute(select(Medication).where(Medication.user_id == user.id))
    return result.scalars().all()


@router.post("/medications", response_model=MedicationOut, status_code=status.HTTP_201_CREATED)
async def create_medication(
    body: MedicationCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    med = Medication(user_id=user.id, **body.model_dump())
    session.add(med)
    await session.commit()
    await session.refresh(med)
    return med


@router.patch("/medications/{med_id}", response_model=MedicationOut)
async def update_medication(
    med_id: uuid.UUID,
    body: MedicationUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    med = await session.get(Medication, med_id)
    if not med or med.user_id != user.id:
        raise HTTPException(status_code=404, detail="Medication not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(med, field, value)
    await session.commit()
    await session.refresh(med)
    return med


@router.delete("/medications/{med_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(
    med_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    med = await session.get(Medication, med_id)
    if not med or med.user_id != user.id:
        raise HTTPException(status_code=404, detail="Medication not found")
    await session.delete(med)
    await session.commit()
