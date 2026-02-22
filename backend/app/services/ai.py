from __future__ import annotations
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import anthropic
from ..config import get_settings
from ..models.entries import BPEntry, SymptomEntry, FoodEntry, GymEntry
from ..models.profile import Diagnosis, Medication


def _bp_category(systolic: int, diastolic: int) -> str:
    if systolic > 180 or diastolic > 120:
        return "Hypertensive Crisis"
    if systolic >= 140 or diastolic >= 90:
        return "High Stage 2"
    if systolic >= 130 or diastolic >= 80:
        return "High Stage 1"
    if 120 <= systolic <= 129 and diastolic < 80:
        return "Elevated"
    if systolic < 90 and diastolic < 60:
        return "Low (Hypotension)"
    return "Normal"


async def _get_daily_context(session: AsyncSession, user_id, target_date: date) -> str:
    lines = [f"Date: {target_date.isoformat()}"]

    bp_result = await session.execute(
        select(BPEntry).where(BPEntry.user_id == user_id, BPEntry.entry_date == target_date)
    )
    bp_entries = bp_result.scalars().all()
    if bp_entries:
        lines.append("\n## Blood Pressure Readings")
        for entry in bp_entries:
            for r in entry.readings:
                cat = _bp_category(r.systolic, r.diastolic)
                pulse_str = f", pulse {r.pulse} bpm" if r.pulse else ""
                lines.append(f"- {r.recorded_at.strftime('%H:%M')}: {r.systolic}/{r.diastolic} mmHg{pulse_str} ({cat})")
            if entry.notes:
                lines.append(f"  Notes: {entry.notes}")

    sym_result = await session.execute(
        select(SymptomEntry).where(SymptomEntry.user_id == user_id, SymptomEntry.entry_date == target_date)
    )
    symptoms = sym_result.scalars().all()
    if symptoms:
        lines.append("\n## Symptoms")
        for s in symptoms:
            sev = f" (severity {s.severity}/10)" if s.severity else ""
            lines.append(f"- {s.entry_time.strftime('%H:%M')}: {s.description}{sev}")

    food_result = await session.execute(
        select(FoodEntry).where(FoodEntry.user_id == user_id, FoodEntry.entry_date == target_date)
    )
    foods = food_result.scalars().all()
    if foods:
        lines.append("\n## Food & Drink")
        for f in foods:
            lines.append(f"- {f.entry_time.strftime('%H:%M')} [{f.meal_type.value}]: {f.description}")

    gym_result = await session.execute(
        select(GymEntry).where(GymEntry.user_id == user_id, GymEntry.entry_date == target_date)
    )
    gyms = gym_result.scalars().all()
    if gyms:
        lines.append("\n## Gym Sessions")
        for g in gyms:
            lines.append(f"- Session on {g.entry_date}")
            for ex in g.exercises:
                if ex.duration_min:
                    lines.append(f"  - {ex.machine}: {ex.duration_min} min")
                else:
                    lines.append(f"  - {ex.machine}: {ex.sets}×{ex.reps} @ {ex.weight_kg} kg")

    return "\n".join(lines)


async def _get_user_medical_context(session: AsyncSession, user_id) -> str:
    diag_result = await session.execute(select(Diagnosis).where(Diagnosis.user_id == user_id))
    diagnoses = diag_result.scalars().all()
    med_result = await session.execute(select(Medication).where(Medication.user_id == user_id, Medication.is_active == True))
    medications = med_result.scalars().all()

    lines = []
    if diagnoses:
        lines.append("Diagnoses: " + ", ".join(d.condition_name for d in diagnoses))
    if medications:
        meds = ", ".join(f"{m.name} {m.dosage} {m.frequency}" for m in medications)
        lines.append(f"Current medications: {meds}")
    return "\n".join(lines)


async def generate_daily_summary(session: AsyncSession, user_id, target_date: date) -> str:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    diary_context = await _get_daily_context(session, user_id, target_date)
    medical_context = await _get_user_medical_context(session, user_id)

    prompt = f"""You are a clinical GP assistant generating a daily health diary summary for {target_date.isoformat()}.

Patient medical context:
{medical_context}

Today's diary entries:
{diary_context}

Write a concise, professional daily summary suitable for sharing with a GP. Include:
- Blood pressure status and any notable readings or patterns
- Symptoms reported and their significance
- Food and drink intake overview if relevant
- Exercise if recorded
- Any flagged concerns

Tone: clinical but readable. Do not be alarmist. Be factual and specific."""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def generate_weekly_summary(session: AsyncSession, user_id, week_start: date, week_end: date) -> str:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    medical_context = await _get_user_medical_context(session, user_id)

    # Collect all BP readings for the week
    from datetime import timedelta
    bp_lines = []
    bp_result = await session.execute(
        select(BPEntry).where(
            BPEntry.user_id == user_id,
            BPEntry.entry_date >= week_start,
            BPEntry.entry_date <= week_end,
        )
    )
    for entry in bp_result.scalars().all():
        for r in entry.readings:
            cat = _bp_category(r.systolic, r.diastolic)
            pulse_str = f", pulse {r.pulse} bpm" if r.pulse else ""
            bp_lines.append(f"{entry.entry_date} {r.recorded_at.strftime('%H:%M')}: {r.systolic}/{r.diastolic}{pulse_str} — {cat}")

    sym_result = await session.execute(
        select(SymptomEntry).where(
            SymptomEntry.user_id == user_id,
            SymptomEntry.entry_date >= week_start,
            SymptomEntry.entry_date <= week_end,
        )
    )
    sym_lines = [f"{s.entry_date} {s.entry_time}: {s.description}" + (f" (severity {s.severity}/10)" if s.severity else "") for s in sym_result.scalars().all()]

    gym_result = await session.execute(
        select(GymEntry).where(
            GymEntry.user_id == user_id,
            GymEntry.entry_date >= week_start,
            GymEntry.entry_date <= week_end,
        )
    )
    gym_lines = [f"{g.entry_date}: {len(g.exercises)} exercise(s)" for g in gym_result.scalars().all()]

    prompt = f"""You are a clinical GP assistant generating a weekly health summary for the week of {week_start.isoformat()} to {week_end.isoformat()}.

Patient medical context:
{medical_context}

Blood pressure readings this week:
{chr(10).join(bp_lines) if bp_lines else 'None recorded'}

Symptoms this week:
{chr(10).join(sym_lines) if sym_lines else 'None recorded'}

Gym sessions:
{chr(10).join(gym_lines) if gym_lines else 'None recorded'}

Write a structured weekly summary including:
1. Blood pressure trends (morning vs evening averages if identifiable, overall trend, any concerning readings)
2. Symptom highlights and patterns
3. Lifestyle notes (exercise, any notable food patterns if relevant)
4. Key observations and any recommendations to raise with a GP

Format: clear sections with headings. Tone: clinical, professional, suitable for sharing with a doctor."""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
