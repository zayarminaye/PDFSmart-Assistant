"""
Content extraction endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pathlib import Path
from datetime import datetime
import logging
import json

from ...services import pdf_processor
from ...models import ExtractionRequest, ExtractionResponse, UserTier, OutputFormat
from ...core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(settings.UPLOAD_DIR)


@router.post("/extract", response_model=ExtractionResponse)
async def extract_content(request: ExtractionRequest) -> ExtractionResponse:
    """
    Extract content from PDF using natural language query.

    Args:
        request: Extraction request with query and parameters

    Returns:
        Extracted content in requested format
    """
    file_path = UPLOAD_DIR / f"{request.document_id}.pdf"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        start_time = datetime.utcnow()

        # Process extraction
        result = await pdf_processor.extract_content(
            str(file_path),
            request.extraction_query,
            request.output_format,
            UserTier.FREE,
            request.pages
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail="Extraction failed"
            )

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Prepare content based on format
        extracted_content = result.get("content", "")
        content_type = f"application/{request.output_format.value}"

        if request.output_format == OutputFormat.JSON:
            content_type = "application/json"
        elif request.output_format == OutputFormat.CSV:
            content_type = "text/csv"
        elif request.output_format == OutputFormat.MARKDOWN:
            content_type = "text/markdown"
        else:
            content_type = "text/plain"

        return ExtractionResponse(
            document_id=request.document_id,
            extracted_content=extracted_content,
            content_type=content_type,
            download_url=f"/api/extract/download/{request.document_id}",
            processing_time_ms=int(processing_time)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed for {request.document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.get("/tables/{document_id}")
async def extract_tables(document_id: str, pages: str = None):
    """
    Extract all tables from a PDF.

    Args:
        document_id: Document ID
        pages: Comma-separated page numbers (e.g., "1,2,3") or None for all

    Returns:
        Extracted tables in JSON format
    """
    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Parse page numbers
        page_numbers = None
        if pages:
            page_numbers = [int(p.strip()) for p in pages.split(",")]

        # Analyze document
        analysis = await pdf_processor.analyze_pdf(str(file_path), UserTier.FREE)

        # Get tables
        tables = analysis["document_structure"].get("tables", [])

        # Filter by pages if specified
        if page_numbers:
            tables = [t for t in tables if t.get("page") in page_numbers]

        return {
            "document_id": document_id,
            "total_tables": len(tables),
            "tables": tables
        }

    except Exception as e:
        logger.error(f"Table extraction failed for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Table extraction failed: {str(e)}")


@router.get("/text/{document_id}")
async def extract_text(document_id: str, pages: str = None):
    """
    Extract raw text from PDF.

    Args:
        document_id: Document ID
        pages: Comma-separated page numbers or None for all

    Returns:
        Extracted text
    """
    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Parse page numbers
        page_numbers = None
        if pages:
            page_numbers = [int(p.strip()) for p in pages.split(",")]

        # Extract text
        result = await pdf_processor.extract_content(
            str(file_path),
            "extract all text",
            OutputFormat.TEXT,
            UserTier.FREE,
            page_numbers
        )

        return {
            "document_id": document_id,
            "text": result.get("content", ""),
            "pages_processed": result.get("pages_processed", 0)
        }

    except Exception as e:
        logger.error(f"Text extraction failed for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")
