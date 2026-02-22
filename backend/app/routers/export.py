from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models.user import User
from ..schemas.entries import ExportRequest
from ..services.pdf import generate_pdf
from .deps import get_current_user

router = APIRouter()


@router.post("/pdf")
async def export_pdf(
    body: ExportRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pdf_bytes = await generate_pdf(
        session=session,
        user=user,
        start_date=body.start_date,
        end_date=body.end_date,
        tag_ids=body.tag_ids,
        include_summary=body.include_summary,
    )
    filename = f"medidiary-{body.start_date}-to-{body.end_date}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
