"""
Form filling endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import logging

from ...services import pdf_processor
from ...models import FillFormRequest, FillFormResponse, UserTier
from ...core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(settings.UPLOAD_DIR)


@router.post("/fill", response_model=FillFormResponse)
async def fill_form(request: FillFormRequest) -> FillFormResponse:
    """
    Fill a PDF form using natural language instructions.

    Args:
        request: Form filling request with document ID and instructions

    Returns:
        Result with filled PDF information
    """
    file_path = UPLOAD_DIR / f"{request.document_id}.pdf"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        start_time = datetime.utcnow()

        # Process form filling
        result = await pdf_processor.fill_form(
            str(file_path),
            request.instructions,
            UserTier.FREE
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Form filling failed")
            )

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Generate download URL
        filled_pdf_path = result.get("filled_pdf_path")
        download_url = f"/api/download/{request.document_id}_filled.pdf"

        return FillFormResponse(
            document_id=request.document_id,
            filled_document_url=download_url,
            fields_filled=result.get("fields_filled", 0),
            fields_total=result.get("fields_total", 0),
            processing_time_ms=int(processing_time)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Form filling failed for {request.document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Form filling failed: {str(e)}")


@router.get("/preview/{document_id}")
async def preview_filled_form(document_id: str):
    """
    Preview filled form fields without downloading.

    Returns metadata about filled fields.
    """
    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Analyze to get current field values
        analysis = await pdf_processor.analyze_pdf(str(file_path), UserTier.FREE)

        return {
            "document_id": document_id,
            "total_fields": len(analysis.get("form_fields", [])),
            "fields": analysis.get("form_fields", [])
        }

    except Exception as e:
        logger.error(f"Preview failed for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")
