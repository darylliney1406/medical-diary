import uuid
from datetime import date
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload
from ..database import get_db
from ..models.user import User
from ..models.profile import Tag
from ..models.entries import (
    BPEntry, BPReading,
    SymptomEntry,
    FoodEntry,
    GymEntry, GymExercise,
)
from ..schemas.entries import (
    BPEntryCreate, BPEntryUpdate, BPEntryOut,
    SymptomEntryCreate, SymptomEntryUpdate, SymptomEntryOut,
    FoodEntryCreate, FoodEntryUpdate, FoodEntryOut,
    GymEntryCreate, GymEntryUpdate, GymEntryOut,
    CalendarMonthOut, DayEntryCounts,
)
from .deps import get_current_user

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _resolve_tags(session: AsyncSession, user_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> list[Tag]:
    if not tag_ids:
        return []
    result = await session.execute(
        select(Tag).where(Tag.user_id == user_id, Tag.id.in_(tag_ids))
    )
    tags = result.scalars().all()
    if len(tags) != len(tag_ids):
        raise HTTPException(status_code=400, detail="One or more tags not found")
    return list(tags)


# ── Blood Pressure ────────────────────────────────────────────────────────────

@router.get("/bp", response_model=list[BPEntryOut])
async def list_bp_entries(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(BPEntry).options(
        selectinload(BPEntry.readings),
        selectinload(BPEntry.tags),
    ).where(BPEntry.user_id == user.id)
    if start_date:
        q = q.where(BPEntry.entry_date >= start_date)
    if end_date:
        q = q.where(BPEntry.entry_date <= end_date)
    q = q.order_by(BPEntry.entry_date.desc()).offset((page - 1) * limit).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()


@router.post("/bp", response_model=BPEntryOut, status_code=status.HTTP_201_CREATED)
async def create_bp_entry(
    body: BPEntryCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tags = await _resolve_tags(session, user.id, body.tag_ids)
    entry = BPEntry(user_id=user.id, entry_date=body.entry_date, notes=body.notes, tags=tags)
    session.add(entry)
    await session.flush()
    for i, r in enumerate(body.readings):
        reading = BPReading(
            bp_entry_id=entry.id,
            systolic=r.systolic,
            diastolic=r.diastolic,
            pulse=r.pulse,
            recorded_at=r.recorded_at,
            order_index=i,
        )
        session.add(reading)
    await session.commit()
    result = await session.execute(
        select(BPEntry).options(selectinload(BPEntry.readings), selectinload(BPEntry.tags)).where(BPEntry.id == entry.id)
    )
    return result.scalar_one()


@router.get("/bp/{entry_id}", response_model=BPEntryOut)
async def get_bp_entry(
    entry_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(BPEntry).options(selectinload(BPEntry.readings), selectinload(BPEntry.tags)).where(BPEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.patch("/bp/{entry_id}", response_model=BPEntryOut)
async def update_bp_entry(
    entry_id: uuid.UUID,
    body: BPEntryUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(BPEntry).options(selectinload(BPEntry.readings), selectinload(BPEntry.tags)).where(BPEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")

    if body.entry_date is not None:
        entry.entry_date = body.entry_date
    if body.notes is not None:
        entry.notes = body.notes
    if body.tag_ids is not None:
        entry.tags = await _resolve_tags(session, user.id, body.tag_ids)
    if body.readings is not None:
        for old in entry.readings:
            await session.delete(old)
        await session.flush()
        for i, r in enumerate(body.readings):
            session.add(BPReading(bp_entry_id=entry.id, systolic=r.systolic, diastolic=r.diastolic, pulse=r.pulse, recorded_at=r.recorded_at, order_index=i))

    await session.commit()
    result = await session.execute(
        select(BPEntry).options(selectinload(BPEntry.readings), selectinload(BPEntry.tags)).where(BPEntry.id == entry.id)
    )
    return result.scalar_one()


@router.delete("/bp/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bp_entry(
    entry_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entry = await session.get(BPEntry, entry_id)
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    await session.delete(entry)
    await session.commit()


# ── Symptom ───────────────────────────────────────────────────────────────────

@router.get("/symptom", response_model=list[SymptomEntryOut])
async def list_symptom_entries(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(SymptomEntry).options(selectinload(SymptomEntry.tags)).where(SymptomEntry.user_id == user.id)
    if start_date:
        q = q.where(SymptomEntry.entry_date >= start_date)
    if end_date:
        q = q.where(SymptomEntry.entry_date <= end_date)
    q = q.order_by(SymptomEntry.entry_date.desc(), SymptomEntry.entry_time.desc()).offset((page - 1) * limit).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()


@router.post("/symptom", response_model=SymptomEntryOut, status_code=status.HTTP_201_CREATED)
async def create_symptom_entry(
    body: SymptomEntryCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tags = await _resolve_tags(session, user.id, body.tag_ids)
    entry = SymptomEntry(user_id=user.id, entry_date=body.entry_date, entry_time=body.entry_time, description=body.description, severity=body.severity, notes=body.notes, tags=tags)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.get("/symptom/{entry_id}", response_model=SymptomEntryOut)
async def get_symptom_entry(entry_id: uuid.UUID, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await session.execute(select(SymptomEntry).options(selectinload(SymptomEntry.tags)).where(SymptomEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.patch("/symptom/{entry_id}", response_model=SymptomEntryOut)
async def update_symptom_entry(entry_id: uuid.UUID, body: SymptomEntryUpdate, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await session.execute(select(SymptomEntry).options(selectinload(SymptomEntry.tags)).where(SymptomEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in body.model_dump(exclude_unset=True, exclude={"tag_ids"}).items():
        setattr(entry, field, value)
    if body.tag_ids is not None:
        entry.tags = await _resolve_tags(session, user.id, body.tag_ids)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.delete("/symptom/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_symptom_entry(entry_id: uuid.UUID, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    entry = await session.get(SymptomEntry, entry_id)
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    await session.delete(entry)
    await session.commit()


# ── Food & Drink ──────────────────────────────────────────────────────────────

@router.get("/food", response_model=list[FoodEntryOut])
async def list_food_entries(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(FoodEntry).options(selectinload(FoodEntry.tags)).where(FoodEntry.user_id == user.id)
    if start_date:
        q = q.where(FoodEntry.entry_date >= start_date)
    if end_date:
        q = q.where(FoodEntry.entry_date <= end_date)
    q = q.order_by(FoodEntry.entry_date.desc(), FoodEntry.entry_time.desc()).offset((page - 1) * limit).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()


@router.post("/food", response_model=FoodEntryOut, status_code=status.HTTP_201_CREATED)
async def create_food_entry(body: FoodEntryCreate, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    tags = await _resolve_tags(session, user.id, body.tag_ids)
    data = body.model_dump(exclude={"tag_ids"})
    entry = FoodEntry(user_id=user.id, **data, tags=tags)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.get("/food/{entry_id}", response_model=FoodEntryOut)
async def get_food_entry(entry_id: uuid.UUID, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await session.execute(select(FoodEntry).options(selectinload(FoodEntry.tags)).where(FoodEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.patch("/food/{entry_id}", response_model=FoodEntryOut)
async def update_food_entry(entry_id: uuid.UUID, body: FoodEntryUpdate, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await session.execute(select(FoodEntry).options(selectinload(FoodEntry.tags)).where(FoodEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in body.model_dump(exclude_unset=True, exclude={"tag_ids"}).items():
        setattr(entry, field, value)
    if body.tag_ids is not None:
        entry.tags = await _resolve_tags(session, user.id, body.tag_ids)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.delete("/food/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food_entry(entry_id: uuid.UUID, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    entry = await session.get(FoodEntry, entry_id)
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    await session.delete(entry)
    await session.commit()


# ── Gym ───────────────────────────────────────────────────────────────────────

@router.get("/gym", response_model=list[GymEntryOut])
async def list_gym_entries(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(GymEntry).options(selectinload(GymEntry.exercises), selectinload(GymEntry.tags)).where(GymEntry.user_id == user.id)
    if start_date:
        q = q.where(GymEntry.entry_date >= start_date)
    if end_date:
        q = q.where(GymEntry.entry_date <= end_date)
    q = q.order_by(GymEntry.entry_date.desc()).offset((page - 1) * limit).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()


@router.post("/gym", response_model=GymEntryOut, status_code=status.HTTP_201_CREATED)
async def create_gym_entry(body: GymEntryCreate, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    tags = await _resolve_tags(session, user.id, body.tag_ids)
    entry = GymEntry(user_id=user.id, entry_date=body.entry_date, session_notes=body.session_notes, tags=tags)
    session.add(entry)
    await session.flush()
    for i, ex in enumerate(body.exercises):
        session.add(GymExercise(gym_entry_id=entry.id, machine=ex.machine, duration_min=ex.duration_min, sets=ex.sets, reps=ex.reps, weight_kg=ex.weight_kg, order_index=i))
    await session.commit()
    result = await session.execute(select(GymEntry).options(selectinload(GymEntry.exercises), selectinload(GymEntry.tags)).where(GymEntry.id == entry.id))
    return result.scalar_one()


@router.get("/gym/{entry_id}", response_model=GymEntryOut)
async def get_gym_entry(entry_id: uuid.UUID, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await session.execute(select(GymEntry).options(selectinload(GymEntry.exercises), selectinload(GymEntry.tags)).where(GymEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.patch("/gym/{entry_id}", response_model=GymEntryOut)
async def update_gym_entry(entry_id: uuid.UUID, body: GymEntryUpdate, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await session.execute(select(GymEntry).options(selectinload(GymEntry.exercises), selectinload(GymEntry.tags)).where(GymEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    if body.entry_date is not None:
        entry.entry_date = body.entry_date
    if body.session_notes is not None:
        entry.session_notes = body.session_notes
    if body.tag_ids is not None:
        entry.tags = await _resolve_tags(session, user.id, body.tag_ids)
    if body.exercises is not None:
        for ex in entry.exercises:
            await session.delete(ex)
        await session.flush()
        for i, ex in enumerate(body.exercises):
            session.add(GymExercise(gym_entry_id=entry.id, machine=ex.machine, duration_min=ex.duration_min, sets=ex.sets, reps=ex.reps, weight_kg=ex.weight_kg, order_index=i))
    await session.commit()
    result = await session.execute(select(GymEntry).options(selectinload(GymEntry.exercises), selectinload(GymEntry.tags)).where(GymEntry.id == entry.id))
    return result.scalar_one()


@router.delete("/gym/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gym_entry(entry_id: uuid.UUID, session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    entry = await session.get(GymEntry, entry_id)
    if not entry or entry.user_id != user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    await session.delete(entry)
    await session.commit()


# ── Calendar ──────────────────────────────────────────────────────────────────

@router.get("/calendar/{year}/{month}", response_model=CalendarMonthOut)
async def get_calendar(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from datetime import date as date_type
    import calendar

    _, last_day = calendar.monthrange(year, month)

    async def count_by_date(model, col):
        q = select(col, func.count()).where(
            model.user_id == user.id,
            extract("year", col) == year,
            extract("month", col) == month,
        ).group_by(col)
        result = await session.execute(q)
        return {row[0]: row[1] for row in result.all()}

    bp_counts = await count_by_date(BPEntry, BPEntry.entry_date)
    sym_counts = await count_by_date(SymptomEntry, SymptomEntry.entry_date)
    food_counts = await count_by_date(FoodEntry, FoodEntry.entry_date)
    gym_counts = await count_by_date(GymEntry, GymEntry.entry_date)

    days = []
    for day in range(1, last_day + 1):
        d = date_type(year, month, day)
        days.append(DayEntryCounts(date=d, counts={
            "bp": bp_counts.get(d, 0),
            "symptom": sym_counts.get(d, 0),
            "food": food_counts.get(d, 0),
            "gym": gym_counts.get(d, 0),
        }))

    return CalendarMonthOut(year=year, month=month, days=days)
