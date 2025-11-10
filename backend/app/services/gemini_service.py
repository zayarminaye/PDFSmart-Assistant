"""
Google Gemini LLM Integration Service.
Handles natural language understanding for form filling and content extraction.
"""
from typing import Dict, List, Any, Optional
import google.generativeai as genai
import logging
import json

from ..core.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service for Google Gemini AI integration.
    Handles NLP tasks for form filling and extraction queries.
    """

    def __init__(self):
        """Initialize Gemini API client."""
        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured")
            self.model = None
            return

        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            logger.info(f"Gemini service initialized with model: {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None

    async def parse_fill_instructions(
        self,
        instructions: str,
        detected_fields: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Parse natural language instructions for form filling.

        Args:
            instructions: Natural language instructions (e.g., "Fill name as John, address as 123 Main St")
            detected_fields: List of detected form fields

        Returns:
            Dictionary mapping field names to values
        """
        if not self.model:
            raise ValueError("Gemini service not initialized")

        try:
            # Prepare field information
            field_info = "\n".join([
                f"- {field.get('label', f'Field {i+1}')}: {field.get('type', 'text')}"
                for i, field in enumerate(detected_fields)
            ])

            # Create prompt
            prompt = f"""You are a form-filling assistant. Parse the user's instructions and map them to form fields.

Available form fields:
{field_info}

User instructions: "{instructions}"

Return a JSON object mapping field labels to their values. Use exact field labels as keys.
If a date is mentioned as "today", use the current date in YYYY-MM-DD format.
If a field is not mentioned, don't include it in the response.

Example format:
{{
    "Name": "John Doe",
    "Address": "123 Main St",
    "Date": "2024-01-15"
}}

Return only the JSON object, no additional text."""

            # Generate response
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            field_mappings = json.loads(result_text)

            logger.info(f"Parsed {len(field_mappings)} field mappings from instructions")
            return field_mappings

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response was: {result_text}")
            return {}
        except Exception as e:
            logger.error(f"Failed to parse fill instructions: {e}")
            return {}

    async def interpret_extraction_query(
        self,
        query: str,
        document_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Interpret natural language extraction query.

        Args:
            query: Natural language query (e.g., "Extract the price list table")
            document_structure: Document structure from Docling

        Returns:
            Extraction parameters (target elements, output format, etc.)
        """
        if not self.model:
            raise ValueError("Gemini service not initialized")

        try:
            # Prepare document info
            doc_info = f"""
Document has:
- {document_structure.get('total_pages', 0)} pages
- {len(document_structure.get('tables', []))} tables
- {len(document_structure.get('text_blocks', []))} text blocks
"""

            # Create prompt
            prompt = f"""You are a document extraction assistant. Analyze the user's extraction query and determine what they want.

{doc_info}

User query: "{query}"

Determine:
1. What type of content to extract (table, text, image, specific data)
2. Which pages to target (all, specific pages, or auto-detect)
3. What output format would be best (text, markdown, csv, json)
4. Any specific patterns or keywords to look for

Return a JSON object with this structure:
{{
    "content_type": "table|text|data|all",
    "target_pages": [1, 2, 3] or "all",
    "keywords": ["keyword1", "keyword2"],
    "output_format": "text|markdown|csv|json",
    "extraction_focus": "brief description of what to extract"
}}

Return only the JSON object, no additional text."""

            # Generate response
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            extraction_params = json.loads(result_text)

            logger.info(f"Interpreted extraction query: {extraction_params}")
            return extraction_params

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response was: {result_text}")
            return {
                "content_type": "all",
                "target_pages": "all",
                "keywords": [],
                "output_format": "text",
                "extraction_focus": query
            }
        except Exception as e:
            logger.error(f"Failed to interpret extraction query: {e}")
            return {
                "content_type": "all",
                "target_pages": "all",
                "keywords": [],
                "output_format": "text",
                "extraction_focus": query
            }

    async def summarize_extraction(
        self,
        extracted_content: str,
        max_length: int = 200
    ) -> str:
        """
        Generate a summary of extracted content.

        Args:
            extracted_content: Extracted content to summarize
            max_length: Maximum summary length in words

        Returns:
            Summary text
        """
        if not self.model:
            raise ValueError("Gemini service not initialized")

        try:
            prompt = f"""Summarize the following extracted content in {max_length} words or less:

{extracted_content[:5000]}  # Limit input to avoid token limits

Provide a concise summary focusing on the key information."""

            response = self.model.generate_content(prompt)
            summary = response.text.strip()

            logger.info("Generated content summary")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return "Summary generation failed"

    async def validate_field_mapping(
        self,
        field_name: str,
        field_value: str,
        field_type: str
    ) -> Dict[str, Any]:
        """
        Validate if a field value is appropriate for the field.

        Args:
            field_name: Name of the field
            field_value: Proposed value
            field_type: Type of field (text, date, email, etc.)

        Returns:
            Validation result with suggestions if invalid
        """
        if not self.model:
            return {"valid": True, "value": field_value}

        try:
            prompt = f"""Validate if this field value is appropriate:

Field name: {field_name}
Field type: {field_type}
Proposed value: {field_value}

Return a JSON object:
{{
    "valid": true/false,
    "corrected_value": "corrected value if needed",
    "reason": "explanation if invalid"
}}

Return only the JSON object."""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            validation = json.loads(result_text)
            return validation

        except Exception as e:
            logger.error(f"Field validation failed: {e}")
            return {"valid": True, "value": field_value}


# Singleton instance
gemini_service = GeminiService()
