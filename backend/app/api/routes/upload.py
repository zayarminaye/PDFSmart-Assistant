"""
PDF upload and analysis endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import aiofiles
import os
import uuid
from pathlib import Path
from datetime import datetime, timedelta
import logging

from ...services import pdf_processor
from ...models import DocumentUploadResponse, FormAnalysisResponse, UserTier
from ...core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


# Temporary storage for uploaded files (in-memory for testing)
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """
    Upload a PDF file for processing.

    Returns document ID and metadata.
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Check file size
    contents = await file.read()
    file_size = len(contents)
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )

    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())

        # Save file temporarily
        file_path = UPLOAD_DIR / f"{document_id}.pdf"
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(contents)

        logger.info(f"File uploaded: {file.filename} ({file_size} bytes) -> {document_id}")

        # Calculate expiration
        upload_time = datetime.utcnow()
        expires_at = upload_time + timedelta(hours=settings.FILE_RETENTION_HOURS)

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            upload_timestamp=upload_time,
            expires_at=expires_at
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/analyze/{document_id}", response_model=FormAnalysisResponse)
async def analyze_pdf(document_id: str) -> FormAnalysisResponse:
    """
    Analyze an uploaded PDF to detect form fields and structure.

    Args:
        document_id: Document ID from upload

    Returns:
        Analysis results including detected form fields
    """
    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Analyze PDF
        analysis = await pdf_processor.analyze_pdf(str(file_path), UserTier.FREE)

        # Convert to response format
        detected_fields = []
        for field in analysis.get("form_fields", []):
            detected_fields.append({
                "field_name": field.get("label", ""),
                "field_type": field.get("type", "text"),
                "coordinates": field.get("bbox", {}),
                "page_number": field.get("page", 1),
                "current_value": None
            })

        return FormAnalysisResponse(
            document_id=document_id,
            total_pages=analysis.get("total_pages", 0),
            detected_fields=detected_fields,
            is_scanned=analysis.get("is_scanned", False),
            ocr_engine_used=analysis.get("ocr_engine_used")
        )

    except Exception as e:
        logger.error(f"Analysis failed for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "ocr": "available",
            "docling": "available",
            "gemini": "available" if settings.GEMINI_API_KEY else "not_configured"
        }
    }
