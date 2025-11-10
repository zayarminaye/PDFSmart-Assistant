"""
PDF Processing Service.
Orchestrates PDF operations including form filling and content extraction.
"""
from typing import Dict, List, Any, Optional, BinaryIO
from pathlib import Path
import io
import logging
from datetime import datetime
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image

from .ocr_orchestrator import ocr_orchestrator
from .docling_service import docling_service
from .gemini_service import gemini_service
from ..models.schemas import UserTier, OutputFormat

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Main PDF processing service that orchestrates all operations.
    Handles form filling and content extraction workflows.
    """

    def __init__(self):
        self.ocr = ocr_orchestrator
        self.docling = docling_service
        self.gemini = gemini_service
        logger.info("PDF Processor initialized")

    async def analyze_pdf(
        self,
        pdf_path: str,
        user_tier: UserTier = UserTier.FREE
    ) -> Dict[str, Any]:
        """
        Comprehensive PDF analysis.

        Args:
            pdf_path: Path to PDF file
            user_tier: User's subscription tier

        Returns:
            Complete analysis including structure, forms, and text
        """
        logger.info(f"Starting PDF analysis: {pdf_path}")

        try:
            # Get document structure from Docling
            doc_structure = await self.docling.analyze_document(pdf_path)

            # Check if document is scanned (needs OCR)
            is_scanned = await self._is_scanned_pdf(pdf_path)

            # If scanned, perform OCR
            ocr_text = None
            ocr_engine_used = None
            if is_scanned:
                logger.info("PDF appears to be scanned, running OCR")
                ocr_engine = self.ocr.select_engine(user_tier)
                ocr_result = await self._ocr_full_document(pdf_path, ocr_engine)
                ocr_text = ocr_result.get("text", "")
                ocr_engine_used = ocr_result.get("engine_used")

            # Detect form fields
            form_fields = await self.docling.detect_form_fields(pdf_path)

            # Compile complete analysis
            analysis = {
                "document_structure": doc_structure,
                "is_scanned": is_scanned,
                "ocr_text": ocr_text,
                "ocr_engine_used": ocr_engine_used,
                "form_fields": form_fields,
                "has_forms": len(form_fields) > 0,
                "total_pages": doc_structure.get("total_pages", 0),
                "total_tables": len(doc_structure.get("tables", [])),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"PDF analysis complete: {analysis['total_pages']} pages, "
                       f"{len(form_fields)} form fields, scanned={is_scanned}")

            return analysis

        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")
            raise

    async def fill_form(
        self,
        pdf_path: str,
        instructions: str,
        user_tier: UserTier = UserTier.FREE,
        ocr_engine: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fill PDF form based on natural language instructions.

        Args:
            pdf_path: Path to PDF file
            instructions: Natural language filling instructions
            user_tier: User's subscription tier
            ocr_engine: OCR engine to use (tesseract or google_vision)

        Returns:
            Result with filled PDF and metadata
        """
        logger.info(f"Starting form fill: {pdf_path}")

        try:
            # Analyze the PDF
            analysis = await self.analyze_pdf(pdf_path, user_tier)

            if not analysis["has_forms"]:
                logger.warning("No form fields detected in PDF")
                return {
                    "success": False,
                    "error": "No form fields detected in this PDF",
                    "fields_filled": 0
                }

            # Parse instructions using Gemini
            field_mappings = await self.gemini.parse_fill_instructions(
                instructions,
                analysis["form_fields"]
            )

            if not field_mappings:
                logger.warning("Could not parse any field mappings from instructions")
                return {
                    "success": False,
                    "error": "Could not understand filling instructions",
                    "fields_filled": 0
                }

            # Fill the PDF
            filled_pdf_path = await self._fill_pdf_fields(
                pdf_path,
                analysis["form_fields"],
                field_mappings
            )

            result = {
                "success": True,
                "filled_pdf_path": filled_pdf_path,
                "fields_filled": len(field_mappings),
                "fields_total": len(analysis["form_fields"]),
                "field_mappings": field_mappings,
                "processing_time_ms": 0  # TODO: Add timing
            }

            logger.info(f"Form fill complete: {result['fields_filled']}/{result['fields_total']} fields filled")
            return result

        except Exception as e:
            logger.error(f"Form filling failed: {e}")
            raise

    async def extract_content(
        self,
        pdf_path: str,
        extraction_query: str,
        output_format: OutputFormat = OutputFormat.TEXT,
        user_tier: UserTier = UserTier.FREE,
        pages: Optional[List[int]] = None,
        ocr_engine: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract content from PDF based on natural language query.

        Args:
            pdf_path: Path to PDF file
            extraction_query: Natural language extraction query
            output_format: Desired output format
            user_tier: User's subscription tier
            pages: Specific pages to extract from
            ocr_engine: OCR engine to use (tesseract or google_vision)

        Returns:
            Extracted content in requested format
        """
        logger.info(f"Starting content extraction: {pdf_path}, query='{extraction_query}'")

        try:
            # Analyze the PDF
            analysis = await self.analyze_pdf(pdf_path, user_tier)

            # Interpret extraction query using Gemini
            extraction_params = await self.gemini.interpret_extraction_query(
                extraction_query,
                analysis["document_structure"]
            )

            # Determine target pages
            target_pages = pages or extraction_params.get("target_pages", "all")
            if target_pages == "all":
                target_pages = list(range(1, analysis["total_pages"] + 1))

            # Extract based on content type
            content_type = extraction_params.get("content_type", "all")
            extracted_content = ""

            if content_type == "table" or "table" in extraction_query.lower():
                # Extract tables
                tables = await self.docling.extract_tables(pdf_path, target_pages)
                extracted_content = await self._format_tables(tables, output_format)

            elif content_type == "text" or content_type == "all":
                # Extract text
                if analysis["is_scanned"]:
                    # Use OCR for scanned documents
                    ocr_engine = self.ocr.select_engine(user_tier)
                    ocr_result = await self._ocr_specific_pages(pdf_path, target_pages, ocr_engine)
                    extracted_content = ocr_result.get("text", "")
                else:
                    # Use Docling for digital PDFs
                    markdown = await self.docling.export_to_markdown(pdf_path)
                    extracted_content = markdown

            # Format output
            formatted_content = await self._format_output(
                extracted_content,
                output_format
            )

            result = {
                "success": True,
                "content": formatted_content,
                "content_type": content_type,
                "output_format": output_format.value,
                "pages_processed": len(target_pages) if isinstance(target_pages, list) else analysis["total_pages"],
                "extraction_params": extraction_params,
                "processing_time_ms": 0  # TODO: Add timing
            }

            logger.info(f"Content extraction complete: {len(str(formatted_content))} chars extracted")
            return result

        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            raise

    async def _is_scanned_pdf(self, pdf_path: str) -> bool:
        """
        Heuristic to determine if PDF is scanned.
        Checks if extractable text is minimal compared to page count.
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_text = ""

                # Sample first few pages
                pages_to_check = min(3, len(reader.pages))
                for i in range(pages_to_check):
                    total_text += reader.pages[i].extract_text()

                # If very little text extracted, likely scanned
                words_per_page = len(total_text.split()) / pages_to_check
                is_scanned = words_per_page < 50  # Threshold: less than 50 words per page

                logger.debug(f"Scanned detection: {words_per_page:.1f} words/page, scanned={is_scanned}")
                return is_scanned

        except Exception as e:
            logger.error(f"Scanned detection failed: {e}")
            return False  # Assume not scanned if detection fails

    async def _ocr_full_document(self, pdf_path: str, ocr_engine: str) -> Dict[str, Any]:
        """Run OCR on entire document."""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)

            all_text = []
            total_confidence = 0.0

            for i, image in enumerate(images):
                logger.debug(f"OCR processing page {i+1}/{len(images)}")
                result = await self.ocr.extract_text(image, ocr_engine)
                all_text.append(result.get("text", ""))
                total_confidence += result.get("confidence", 0.0)

            avg_confidence = total_confidence / len(images) if images else 0.0

            return {
                "text": "\n\n".join(all_text),
                "engine_used": ocr_engine,
                "confidence": avg_confidence,
                "pages_processed": len(images)
            }

        except Exception as e:
            logger.error(f"Full document OCR failed: {e}")
            return {"text": "", "engine_used": ocr_engine, "confidence": 0.0}

    async def _ocr_specific_pages(
        self,
        pdf_path: str,
        page_numbers: List[int],
        ocr_engine: str
    ) -> Dict[str, Any]:
        """Run OCR on specific pages."""
        try:
            # Convert specific pages to images
            images = convert_from_path(pdf_path, first_page=min(page_numbers), last_page=max(page_numbers))

            page_texts = []
            for i, page_num in enumerate(page_numbers):
                if i < len(images):
                    result = await self.ocr.extract_text(images[i], ocr_engine)
                    page_texts.append(result.get("text", ""))

            return {
                "text": "\n\n".join(page_texts),
                "engine_used": ocr_engine,
                "pages_processed": len(page_numbers)
            }

        except Exception as e:
            logger.error(f"Specific pages OCR failed: {e}")
            return {"text": "", "engine_used": ocr_engine}

    async def _fill_pdf_fields(
        self,
        pdf_path: str,
        form_fields: List[Dict[str, Any]],
        field_mappings: Dict[str, str]
    ) -> str:
        """
        Fill PDF form fields with mapped values.
        Returns path to filled PDF.
        """
        # TODO: Implement actual PDF form filling
        # This requires a library like pypdf or pdfrw
        # For now, return original path as placeholder
        logger.warning("PDF form filling not yet implemented - returning original PDF")
        return pdf_path

    async def _format_tables(self, tables: List[Dict[str, Any]], output_format: OutputFormat) -> str:
        """Format extracted tables based on output format."""
        if output_format == OutputFormat.JSON:
            import json
            return json.dumps(tables, indent=2)
        elif output_format == OutputFormat.CSV:
            # TODO: Convert tables to CSV
            return str(tables)
        elif output_format == OutputFormat.MARKDOWN:
            # TODO: Convert tables to markdown
            return str(tables)
        else:
            return str(tables)

    async def _format_output(self, content: str, output_format: OutputFormat) -> str:
        """Format extracted content based on output format."""
        if output_format == OutputFormat.JSON:
            import json
            return json.dumps({"content": content}, indent=2)
        elif output_format == OutputFormat.MARKDOWN:
            return content  # Already markdown from Docling
        else:
            return content


# Singleton instance
pdf_processor = PDFProcessor()
