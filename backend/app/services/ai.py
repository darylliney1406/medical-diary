from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import anthropic
from ..config import get_settings
from ..models.entries import BPEntry, SymptomEntry, FoodEntry, GymEntry
from ..models.profile import UserIdentityProfile, UserBodyMetrics, Diagnosis, Medication


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
        select(BPEntry).options(selectinload(BPEntry.readings)).where(
            BPEntry.user_id == user_id, BPEntry.entry_date == target_date
        )
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
        select(GymEntry).options(selectinload(GymEntry.exercises)).where(
            GymEntry.user_id == user_id, GymEntry.entry_date == target_date
        )
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
    identity_result = await session.execute(
        select(UserIdentityProfile).where(UserIdentityProfile.user_id == user_id)
    )
    identity = identity_result.scalar_one_or_none()

    metrics_result = await session.execute(
        select(UserBodyMetrics).where(UserBodyMetrics.user_id == user_id)
        .order_by(UserBodyMetrics.recorded_at.desc())
    )
    metrics = metrics_result.scalars().first()

    diag_result = await session.execute(select(Diagnosis).where(Diagnosis.user_id == user_id))
    diagnoses = diag_result.scalars().all()

    med_result = await session.execute(
        select(Medication).where(Medication.user_id == user_id, Medication.is_active == True)
    )
    medications = med_result.scalars().all()

    lines = []

    if identity:
        if identity.date_of_birth:
            today = date.today()
            age = today.year - identity.date_of_birth.year - (
                (today.month, today.day) < (identity.date_of_birth.month, identity.date_of_birth.day)
            )
            lines.append(f"Age: {age}")
        if identity.allergies:
            lines.append(f"Allergies / intolerances: {identity.allergies}")

    if metrics:
        m_parts = []
        if metrics.gender:
            m_parts.append(f"gender {metrics.gender}")
        if metrics.height_cm:
            m_parts.append(f"height {metrics.height_cm} cm")
        if metrics.weight_kg:
            m_parts.append(f"weight {metrics.weight_kg} kg")
        if metrics.height_cm and metrics.weight_kg:
            bmi = round(metrics.weight_kg / ((metrics.height_cm / 100) ** 2), 1)
            m_parts.append(f"BMI {bmi}")
        if metrics.activity_level:
            m_parts.append(f"activity level {metrics.activity_level.value.replace('_', ' ')}")
        if m_parts:
            lines.append("Body metrics: " + ", ".join(m_parts))

    if diagnoses:
        lines.append("Diagnoses: " + ", ".join(d.condition_name for d in diagnoses))
    if medications:
        meds = ", ".join(f"{m.name} {m.dosage} {m.frequency}".strip() for m in medications)
        lines.append(f"Current medications: {meds}")

    return "\n".join(lines) if lines else "No profile information recorded."


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
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def _collect_weekly_data(session: AsyncSession, user_id, week_start: date, week_end: date) -> dict:
    """Collect all weekly diary data once, shared by both summary generators."""
    medical_context = await _get_user_medical_context(session, user_id)

    bp_lines = []
    bp_result = await session.execute(
        select(BPEntry).options(selectinload(BPEntry.readings)).where(
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
        select(GymEntry).options(selectinload(GymEntry.exercises)).where(
            GymEntry.user_id == user_id,
            GymEntry.entry_date >= week_start,
            GymEntry.entry_date <= week_end,
        )
    )
    gym_lines = [f"{g.entry_date}: {len(g.exercises)} exercise(s)" for g in gym_result.scalars().all()]

    return {
        "medical_context": medical_context,
        "bp_lines": bp_lines,
        "sym_lines": sym_lines,
        "gym_lines": gym_lines,
    }


def _build_professional_prompt(week_start: date, week_end: date, data: dict) -> str:
    return f"""You are a clinical GP assistant generating a weekly health summary for the week of {week_start.isoformat()} to {week_end.isoformat()}.

Patient medical context:
{data["medical_context"]}

Blood pressure readings this week:
{chr(10).join(data["bp_lines"]) if data["bp_lines"] else 'None recorded'}

Symptoms this week:
{chr(10).join(data["sym_lines"]) if data["sym_lines"] else 'None recorded'}

Gym sessions:
{chr(10).join(data["gym_lines"]) if data["gym_lines"] else 'None recorded'}

Write a structured weekly summary including:
1. Blood pressure trends (morning vs evening averages if identifiable, overall trend, any concerning readings)
2. Symptom highlights and patterns
3. Lifestyle notes (exercise, any notable food patterns if relevant)
4. Key observations and any recommendations to raise with a GP

Format: clear sections with headings. Tone: clinical, professional, suitable for sharing with a doctor."""


def _build_patient_prompt(week_start: date, week_end: date, data: dict) -> str:
    return f"""You are a friendly, supportive health assistant writing a weekly health summary for a patient to read themselves, for the week of {week_start.isoformat()} to {week_end.isoformat()}.

Patient medical context:
{data["medical_context"]}

Blood pressure readings this week:
{chr(10).join(data["bp_lines"]) if data["bp_lines"] else 'None recorded'}

Symptoms this week:
{chr(10).join(data["sym_lines"]) if data["sym_lines"] else 'None recorded'}

Gym sessions:
{chr(10).join(data["gym_lines"]) if data["gym_lines"] else 'None recorded'}

Write a warm, encouraging weekly summary for the patient. Include:
1. How they're doing overall — highlight positives and progress
2. Blood pressure insights in plain language (avoid medical jargon — e.g. say "a little high" not "stage 1 hypertension")
3. Any symptoms and what they might mean, reassuringly but honestly
4. Exercise and lifestyle — celebrate effort and encourage consistency
5. Practical, actionable tips (e.g. "try reducing salt", "staying hydrated can help with headaches", "great job keeping up your gym routine")
6. Gentle reminders to speak to their GP about anything that needs attention

Tone: supportive, warm, easy to understand. Use simple language — imagine you are writing for someone with no medical background. Be encouraging but honest. Do not be alarmist.
Format: clear sections with headings."""


async def generate_weekly_summaries(session: AsyncSession, user_id, week_start: date, week_end: date) -> dict[str, str]:
    """Generate both patient and professional weekly summaries. Returns dict with 'patient' and 'professional' keys."""
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    data = await _collect_weekly_data(session, user_id, week_start, week_end)

    professional_prompt = _build_professional_prompt(week_start, week_end, data)
    patient_prompt = _build_patient_prompt(week_start, week_end, data)

    import asyncio
    loop = asyncio.get_running_loop()

    def _call_professional():
        return client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": professional_prompt}],
        )

    def _call_patient():
        return client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": patient_prompt}],
        )

    professional_msg, patient_msg = await asyncio.gather(
        loop.run_in_executor(None, _call_professional),
        loop.run_in_executor(None, _call_patient),
    )

    return {
        "professional": professional_msg.content[0].text,
        "patient": patient_msg.content[0].text,
    }


async def generate_weekly_summary(session: AsyncSession, user_id, week_start: date, week_end: date) -> str:
    """Generate only the professional weekly summary (backwards compat)."""
    results = await generate_weekly_summaries(session, user_id, week_start, week_end)
    return results["professional"]
