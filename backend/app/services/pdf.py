from datetime import date
from io import BytesIO
from weasyprint import HTML
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..models.entries import BPEntry, SymptomEntry, FoodEntry, GymEntry, AISummary, SummaryType
from ..models.user import User
from ..models.profile import UserIdentityProfile


def _bp_category_colour(systolic: int, diastolic: int) -> tuple[str, str]:
    """Returns (label, hex_colour) for a BP reading."""
    if systolic > 180 or diastolic > 120:
        return "Hypertensive Crisis", "#7c3aed"
    if systolic >= 140 or diastolic >= 90:
        return "High Stage 2", "#dc2626"
    if systolic >= 130 or diastolic >= 80:
        return "High Stage 1", "#ea580c"
    if 120 <= systolic <= 129 and diastolic < 80:
        return "Elevated", "#ca8a04"
    if systolic < 90 and diastolic < 60:
        return "Low", "#2563eb"
    return "Normal", "#16a34a"


def _build_html(
    user: User,
    identity: UserIdentityProfile | None,
    start_date: date,
    end_date: date,
    bp_entries: list,
    symptoms: list,
    foods: list,
    gyms: list,
    summary_content: str | None,
) -> str:
    dob = identity.date_of_birth.isoformat() if identity and identity.date_of_birth else "—"
    nhs = identity.nhs_number if identity and identity.nhs_number else "—"
    gp = identity.gp_name if identity and identity.gp_name else "—"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 12px; color: #1f2937; margin: 0; padding: 20px; }}
  h1 {{ font-size: 20px; color: #4f46e5; margin-bottom: 4px; }}
  h2 {{ font-size: 15px; color: #374151; border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; margin-top: 20px; }}
  .header-meta {{ color: #6b7280; font-size: 11px; margin-bottom: 16px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
  th {{ background: #f3f4f6; text-align: left; padding: 6px 8px; font-size: 11px; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid #f3f4f6; font-size: 11px; }}
  .bp-badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; color: white; font-weight: bold; font-size: 10px; }}
  .summary-box {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; white-space: pre-wrap; font-size: 11px; line-height: 1.5; }}
  .entry-block {{ margin-bottom: 12px; }}
  .tag {{ display: inline-block; background: #e0e7ff; color: #4338ca; border-radius: 3px; padding: 1px 5px; font-size: 10px; margin-right: 3px; }}
</style>
</head>
<body>
<h1>MediDiary — Health Record Export</h1>
<div class="header-meta">
  <strong>Name:</strong> {user.name} &nbsp;|&nbsp;
  <strong>Date of Birth:</strong> {dob} &nbsp;|&nbsp;
  <strong>NHS Number:</strong> {nhs} &nbsp;|&nbsp;
  <strong>GP:</strong> {gp}<br>
  <strong>Period:</strong> {start_date.isoformat()} to {end_date.isoformat()} &nbsp;|&nbsp;
  <strong>Generated:</strong> {date.today().isoformat()}
</div>
"""

    if summary_content:
        html += f'<h2>AI-Generated Summary</h2><div class="summary-box">{summary_content}</div>'

    if bp_entries:
        html += "<h2>Blood Pressure</h2><table><tr><th>Date</th><th>Time</th><th>Reading</th><th>Pulse</th><th>Category</th><th>Notes</th></tr>"
        for entry in bp_entries:
            for r in entry.readings:
                label, colour = _bp_category_colour(r.systolic, r.diastolic)
                pulse = f"{r.pulse} bpm" if r.pulse else "—"
                html += f'<tr><td>{entry.entry_date}</td><td>{r.recorded_at.strftime("%H:%M")}</td><td>{r.systolic}/{r.diastolic} mmHg</td><td>{pulse}</td><td><span class="bp-badge" style="background:{colour}">{label}</span></td><td>{entry.notes or ""}</td></tr>'
        html += "</table>"

    if symptoms:
        html += "<h2>Symptoms</h2><table><tr><th>Date</th><th>Time</th><th>Description</th><th>Severity</th></tr>"
        for s in symptoms:
            sev = f"{s.severity}/10" if s.severity else "—"
            html += f"<tr><td>{s.entry_date}</td><td>{s.entry_time}</td><td>{s.description}</td><td>{sev}</td></tr>"
        html += "</table>"

    if foods:
        html += "<h2>Food & Drink</h2><table><tr><th>Date</th><th>Time</th><th>Type</th><th>Description</th></tr>"
        for f in foods:
            html += f"<tr><td>{f.entry_date}</td><td>{f.entry_time}</td><td>{f.meal_type.value.capitalize()}</td><td>{f.description}</td></tr>"
        html += "</table>"

    if gyms:
        html += "<h2>Gym Sessions</h2>"
        for g in gyms:
            html += f'<div class="entry-block"><strong>{g.entry_date}</strong><table><tr><th>Exercise</th><th>Duration</th><th>Sets</th><th>Reps</th><th>Weight</th></tr>'
            for ex in g.exercises:
                html += f"<tr><td>{ex.machine}</td><td>{ex.duration_min or '—'}</td><td>{ex.sets or '—'}</td><td>{ex.reps or '—'}</td><td>{str(ex.weight_kg) + ' kg' if ex.weight_kg else '—'}</td></tr>"
            html += "</table></div>"

    html += "</body></html>"
    return html


async def generate_pdf(
    session: AsyncSession,
    user: User,
    start_date: date,
    end_date: date,
    tag_ids: list,
    include_summary: bool,
) -> bytes:
    identity_result = await session.execute(
        select(UserIdentityProfile).where(UserIdentityProfile.user_id == user.id)
    )
    identity = identity_result.scalar_one_or_none()

    bp_result = await session.execute(
        select(BPEntry).options(
            selectinload(BPEntry.readings),
            selectinload(BPEntry.tags),
        ).where(
            BPEntry.user_id == user.id,
            BPEntry.entry_date >= start_date,
            BPEntry.entry_date <= end_date,
        ).order_by(BPEntry.entry_date)
    )
    bp_entries = bp_result.scalars().all()

    sym_result = await session.execute(
        select(SymptomEntry).options(
            selectinload(SymptomEntry.tags),
        ).where(
            SymptomEntry.user_id == user.id,
            SymptomEntry.entry_date >= start_date,
            SymptomEntry.entry_date <= end_date,
        ).order_by(SymptomEntry.entry_date)
    )
    symptoms = sym_result.scalars().all()

    food_result = await session.execute(
        select(FoodEntry).options(
            selectinload(FoodEntry.tags),
        ).where(
            FoodEntry.user_id == user.id,
            FoodEntry.entry_date >= start_date,
            FoodEntry.entry_date <= end_date,
        ).order_by(FoodEntry.entry_date)
    )
    foods = food_result.scalars().all()

    gym_result = await session.execute(
        select(GymEntry).options(
            selectinload(GymEntry.exercises),
            selectinload(GymEntry.tags),
        ).where(
            GymEntry.user_id == user.id,
            GymEntry.entry_date >= start_date,
            GymEntry.entry_date <= end_date,
        ).order_by(GymEntry.entry_date)
    )
    gyms = gym_result.scalars().all()

    summary_content = None
    if include_summary:
        sum_result = await session.execute(
            select(AISummary).where(
                AISummary.user_id == user.id,
                AISummary.period_start >= start_date,
                AISummary.period_end <= end_date,
            ).order_by(AISummary.generated_at.desc())
        )
        summary = sum_result.scalars().first()
        if summary:
            summary_content = summary.content

    html = _build_html(user, identity, start_date, end_date, list(bp_entries), list(symptoms), list(foods), list(gyms), summary_content)
    buf = BytesIO()
    HTML(string=html).write_pdf(buf)
    return buf.getvalue()
