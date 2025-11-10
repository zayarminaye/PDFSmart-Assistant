"""
Pydantic models for request/response validation.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class UserTier(str, Enum):
    """User subscription tier."""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


class OCREngine(str, Enum):
    """Available OCR engines."""
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"
    PADDLEOCR = "paddleocr"
    RAPIDOCR = "rapidocr"
    GOOGLE_VISION = "google_vision"


class OutputFormat(str, Enum):
    """Output formats for extraction."""
    TEXT = "text"
    MARKDOWN = "markdown"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    document_id: str
    filename: str
    file_size: int
    upload_timestamp: datetime
    expires_at: datetime


class FormField(BaseModel):
    """Detected form field in a PDF."""
    field_name: str
    field_type: str  # text, checkbox, radio, signature
    coordinates: Dict[str, float]  # x, y, width, height
    page_number: int
    current_value: Optional[str] = None


class FormAnalysisResponse(BaseModel):
    """Response from form analysis."""
    document_id: str
    total_pages: int
    detected_fields: List[FormField]
    is_scanned: bool
    ocr_engine_used: Optional[str] = None


class FillFormRequest(BaseModel):
    """Request to fill a form."""
    document_id: str
    instructions: str  # Natural language instructions
    field_mappings: Optional[Dict[str, str]] = None  # Manual field mappings
    ocr_engine: Optional[OCREngine] = OCREngine.TESSERACT  # OCR engine to use


class FillFormResponse(BaseModel):
    """Response after filling a form."""
    document_id: str
    filled_document_url: str
    fields_filled: int
    fields_total: int
    processing_time_ms: int


class ExtractionRequest(BaseModel):
    """Request to extract content from PDF."""
    document_id: str
    extraction_query: str  # Natural language query
    output_format: OutputFormat = OutputFormat.TEXT
    pages: Optional[List[int]] = None  # Specific pages to extract from
    ocr_engine: Optional[OCREngine] = OCREngine.TESSERACT  # OCR engine to use


class ExtractionResponse(BaseModel):
    """Response from extraction."""
    document_id: str
    extracted_content: Any  # Type depends on output_format
    content_type: str
    download_url: Optional[str] = None
    processing_time_ms: int


class DocumentMetadata(BaseModel):
    """Metadata about a processed document."""
    document_id: str
    filename: str
    file_size: int
    total_pages: int
    is_scanned: bool
    has_forms: bool
    upload_timestamp: datetime
    last_accessed: datetime
    user_id: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]  # service_name: status
