"""
Docling Integration Service.
Provides structured document understanding and layout analysis.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


class DoclingService:
    """
    Service for document structure analysis using Docling.
    Handles PDF parsing, layout detection, and structured content extraction.
    """

    def __init__(self):
        """Initialize Docling converter with optimal settings."""
        # Initialize converter with default options
        # Docling 2.61.1+ has good defaults built-in
        self.converter = DocumentConverter()
        logger.info("Docling service initialized")

    async def analyze_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyze PDF document structure.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Document structure analysis including pages, tables, forms
        """
        try:
            # Convert document
            result = self.converter.convert(pdf_path)

            # Extract document structure
            analysis = {
                "total_pages": len(result.document.pages),
                "pages": [],
                "tables": [],
                "form_fields": [],
                "text_blocks": [],
                "images": [],
                "metadata": {}
            }

            # Process each page
            for page_idx, page in enumerate(result.document.pages):
                page_info = {
                    "page_number": page_idx + 1,
                    "width": page.size.width if hasattr(page, 'size') else 0,
                    "height": page.size.height if hasattr(page, 'size') else 0,
                    "elements": []
                }

                # Extract page elements
                if hasattr(page, 'elements'):
                    for element in page.elements:
                        element_info = {
                            "type": element.__class__.__name__,
                            "bbox": self._extract_bbox(element),
                            "content": self._extract_content(element)
                        }
                        page_info["elements"].append(element_info)

                        # Categorize elements
                        if "Table" in element.__class__.__name__:
                            analysis["tables"].append({
                                "page": page_idx + 1,
                                "bbox": element_info["bbox"],
                                "content": element_info["content"]
                            })
                        elif "Text" in element.__class__.__name__:
                            analysis["text_blocks"].append({
                                "page": page_idx + 1,
                                "bbox": element_info["bbox"],
                                "text": element_info["content"]
                            })

                analysis["pages"].append(page_info)

            # Extract metadata
            if hasattr(result.document, 'metadata'):
                analysis["metadata"] = {
                    "title": getattr(result.document.metadata, 'title', ''),
                    "author": getattr(result.document.metadata, 'author', ''),
                    "creation_date": getattr(result.document.metadata, 'creation_date', ''),
                    "modification_date": getattr(result.document.metadata, 'modification_date', '')
                }

            logger.info(f"Document analysis complete: {analysis['total_pages']} pages, "
                       f"{len(analysis['tables'])} tables, {len(analysis['text_blocks'])} text blocks")

            return analysis

        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            raise

    async def detect_form_fields(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Detect form fields in PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of detected form fields with metadata
        """
        try:
            analysis = await self.analyze_document(pdf_path)
            form_fields = []

            # Analyze text blocks to identify potential form fields
            for page_info in analysis["pages"]:
                for element in page_info["elements"]:
                    # Heuristic: fields often have labels followed by blank spaces or underscores
                    if self._is_likely_form_field(element):
                        form_fields.append({
                            "page": page_info["page_number"],
                            "type": self._infer_field_type(element),
                            "label": self._extract_field_label(element),
                            "bbox": element["bbox"],
                            "confidence": 0.8  # Placeholder confidence score
                        })

            logger.info(f"Detected {len(form_fields)} form fields")
            return form_fields

        except Exception as e:
            logger.error(f"Form field detection failed: {e}")
            return []

    async def extract_tables(self, pdf_path: str, page_numbers: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF.

        Args:
            pdf_path: Path to PDF file
            page_numbers: Specific pages to extract from (None = all pages)

        Returns:
            List of extracted tables with structure
        """
        try:
            analysis = await self.analyze_document(pdf_path)
            tables = analysis["tables"]

            # Filter by page numbers if specified
            if page_numbers:
                tables = [t for t in tables if t["page"] in page_numbers]

            logger.info(f"Extracted {len(tables)} tables")
            return tables

        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return []

    async def export_to_markdown(self, pdf_path: str) -> str:
        """
        Convert PDF to Markdown format.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Markdown representation of the document
        """
        try:
            result = self.converter.convert(pdf_path)

            # Export to markdown
            markdown_content = result.document.export_to_markdown()

            logger.info("Document exported to Markdown")
            return markdown_content

        except Exception as e:
            logger.error(f"Markdown export failed: {e}")
            raise

    def _extract_bbox(self, element: Any) -> Dict[str, float]:
        """Extract bounding box from element."""
        if hasattr(element, 'bbox'):
            bbox = element.bbox
            return {
                "x": bbox.l if hasattr(bbox, 'l') else 0,
                "y": bbox.t if hasattr(bbox, 't') else 0,
                "width": bbox.r - bbox.l if hasattr(bbox, 'r') and hasattr(bbox, 'l') else 0,
                "height": bbox.b - bbox.t if hasattr(bbox, 'b') and hasattr(bbox, 't') else 0
            }
        return {"x": 0, "y": 0, "width": 0, "height": 0}

    def _extract_content(self, element: Any) -> str:
        """Extract text content from element."""
        if hasattr(element, 'text'):
            return element.text
        elif hasattr(element, 'content'):
            return str(element.content)
        return ""

    def _is_likely_form_field(self, element: Dict[str, Any]) -> bool:
        """Heuristic to determine if element is likely a form field."""
        content = element.get("content", "")
        if not content:
            return False

        # Check for common field indicators
        field_indicators = [
            "name:", "date:", "address:", "email:", "phone:",
            "signature:", "_____", "[ ]", "(  )"
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in field_indicators)

    def _infer_field_type(self, element: Dict[str, Any]) -> str:
        """Infer form field type from content."""
        content = element.get("content", "").lower()

        if "[ ]" in content or "checkbox" in content:
            return "checkbox"
        elif "signature" in content:
            return "signature"
        elif "date" in content:
            return "date"
        else:
            return "text"

    def _extract_field_label(self, element: Dict[str, Any]) -> str:
        """Extract field label from element content."""
        content = element.get("content", "")

        # Remove common field indicators
        for indicator in ["_____", "[ ]", "(  )", ":"]:
            content = content.replace(indicator, "")

        return content.strip()


# Singleton instance
docling_service = DoclingService()
