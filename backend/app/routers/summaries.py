from __future__ import annotations
from datetime import date, timedelta
import re
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..models.entries import AISummary, SummaryType
from ..schemas.entries import AISummaryOut
from ..services.ai import generate_daily_summary, generate_weekly_summary
from .deps import get_current_user

router = APIRouter()


def _iso_week_to_dates(iso_week: str) -> tuple[date, date]:
    """Parse '2026-W08' into (monday, sunday)."""
    match = re.match(r"(\d{4})-W(\d{2})$", iso_week)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid iso_week format. Expected YYYY-WNN (e.g. 2026-W08)")
    year, week = int(match.group(1)), int(match.group(2))
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


@router.get("/daily/{target_date}", response_model=AISummaryOut | None)
async def get_daily_summary(
    target_date: date,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(AISummary).where(
            AISummary.user_id == user.id,
            AISummary.summary_type == SummaryType.daily,
            AISummary.period_start == target_date,
        ).order_by(AISummary.generated_at.desc())
    )
    return result.scalars().first()


@router.post("/daily/{target_date}/generate", response_model=AISummaryOut, status_code=status.HTTP_201_CREATED)
async def generate_daily(
    target_date: date,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await generate_daily_summary(session, user.id, target_date)
    summary = AISummary(
        user_id=user.id,
        summary_type=SummaryType.daily,
        period_start=target_date,
        period_end=target_date,
        content=content,
    )
    session.add(summary)
    await session.commit()
    await session.refresh(summary)
    return summary


@router.get("/weekly/{iso_week}", response_model=AISummaryOut | None)
async def get_weekly_summary(
    iso_week: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    week_start, week_end = _iso_week_to_dates(iso_week)
    result = await session.execute(
        select(AISummary).where(
            AISummary.user_id == user.id,
            AISummary.summary_type == SummaryType.weekly,
            AISummary.period_start == week_start,
        ).order_by(AISummary.generated_at.desc())
    )
    return result.scalars().first()


@router.post("/weekly/{iso_week}/generate", response_model=AISummaryOut, status_code=status.HTTP_201_CREATED)
async def generate_weekly(
    iso_week: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    week_start, week_end = _iso_week_to_dates(iso_week)
    content = await generate_weekly_summary(session, user.id, week_start, week_end)
    summary = AISummary(
        user_id=user.id,
        summary_type=SummaryType.weekly,
        period_start=week_start,
        period_end=week_end,
        content=content,
    )
    session.add(summary)
    await session.commit()
    await session.refresh(summary)
    return summary
