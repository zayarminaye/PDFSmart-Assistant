"""
OCR Orchestration Layer - manages multiple OCR engines.
Automatically selects the best OCR engine based on document type and user tier.
"""
from typing import Optional, List, Dict, Any
import pytesseract
from PIL import Image
import numpy as np
from enum import Enum
import logging

from ..core.config import settings
from ..models.schemas import OCREngine, UserTier


logger = logging.getLogger(__name__)


class OCROrchestrator:
    """
    Orchestrates multiple OCR engines to maximize extraction accuracy.
    Automatically selects the best engine based on context.
    """

    def __init__(self):
        self.available_engines = self._detect_available_engines()
        logger.info(f"OCR Orchestrator initialized with engines: {self.available_engines}")

    def _detect_available_engines(self) -> List[str]:
        """Detect which OCR engines are available in the environment."""
        engines = []

        # Check Tesseract
        try:
            pytesseract.get_tesseract_version()
            engines.append(OCREngine.TESSERACT)
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")

        # Check EasyOCR
        try:
            import easyocr
            engines.append(OCREngine.EASYOCR)
        except ImportError:
            logger.warning("EasyOCR not available")

        # Check PaddleOCR
        try:
            from paddleocr import PaddleOCR
            engines.append(OCREngine.PADDLEOCR)
        except ImportError:
            logger.warning("PaddleOCR not available")

        # Check RapidOCR
        try:
            from rapidocr_onnxruntime import RapidOCR
            engines.append(OCREngine.RAPIDOCR)
        except ImportError:
            logger.warning("RapidOCR not available")

        # Check Google Vision API
        if settings.GOOGLE_VISION_API_KEY:
            engines.append(OCREngine.GOOGLE_VISION)

        return engines

    def select_engine(
        self,
        user_tier: UserTier,
        language: str = "eng",
        is_handwritten: bool = False,
        is_multilingual: bool = False
    ) -> str:
        """
        Select the best OCR engine based on context.

        Args:
            user_tier: User's subscription tier
            language: Document language code
            is_handwritten: Whether document contains handwriting
            is_multilingual: Whether document has multiple languages

        Returns:
            Selected OCR engine name
        """
        # Business tier can use Google Vision
        if user_tier == UserTier.BUSINESS and OCREngine.GOOGLE_VISION in self.available_engines:
            return OCREngine.GOOGLE_VISION

        # For handwritten text, prefer EasyOCR
        if is_handwritten and OCREngine.EASYOCR in self.available_engines:
            return OCREngine.EASYOCR

        # For Asian languages (Thai, Chinese, Japanese, Korean), prefer PaddleOCR
        asian_languages = ["tha", "chi_sim", "chi_tra", "jpn", "kor"]
        if language in asian_languages and OCREngine.PADDLEOCR in self.available_engines:
            return OCREngine.PADDLEOCR

        # For multilingual documents, prefer EasyOCR
        if is_multilingual and OCREngine.EASYOCR in self.available_engines:
            return OCREngine.EASYOCR

        # For fast processing, prefer RapidOCR
        if OCREngine.RAPIDOCR in self.available_engines:
            return OCREngine.RAPIDOCR

        # Default to Tesseract (most compatible)
        if OCREngine.TESSERACT in self.available_engines:
            return OCREngine.TESSERACT

        raise ValueError("No OCR engine available")

    async def extract_text(
        self,
        image: Image.Image,
        engine: Optional[str] = None,
        language: str = "eng"
    ) -> Dict[str, Any]:
        """
        Extract text from an image using the specified or auto-selected OCR engine.

        Args:
            image: PIL Image object
            engine: OCR engine to use (auto-selected if None)
            language: Language code for OCR

        Returns:
            Dict with extracted text and metadata
        """
        if engine is None:
            engine = settings.DEFAULT_OCR_ENGINE

        result = {
            "engine_used": engine,
            "text": "",
            "confidence": 0.0,
            "words": [],
            "success": False
        }

        try:
            if engine == OCREngine.TESSERACT:
                result = await self._tesseract_extract(image, language)
            elif engine == OCREngine.EASYOCR:
                result = await self._easyocr_extract(image, language)
            elif engine == OCREngine.PADDLEOCR:
                result = await self._paddleocr_extract(image, language)
            elif engine == OCREngine.RAPIDOCR:
                result = await self._rapidocr_extract(image)
            elif engine == OCREngine.GOOGLE_VISION:
                result = await self._google_vision_extract(image)
            else:
                raise ValueError(f"Unknown OCR engine: {engine}")

            result["success"] = True

        except Exception as e:
            logger.error(f"OCR extraction failed with {engine}: {e}")
            result["error"] = str(e)

        return result

    async def _tesseract_extract(self, image: Image.Image, language: str) -> Dict[str, Any]:
        """Extract text using Tesseract OCR."""
        # Configure tesseract
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

        # Extract text
        text = pytesseract.image_to_string(image, lang=language)

        # Get detailed data with confidence
        data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)

        words = []
        confidences = []
        for i, word in enumerate(data['text']):
            if word.strip():
                words.append({
                    'text': word,
                    'confidence': data['conf'][i],
                    'bbox': {
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    }
                })
                confidences.append(float(data['conf'][i]))

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "engine_used": OCREngine.TESSERACT,
            "text": text,
            "confidence": avg_confidence,
            "words": words
        }

    async def _easyocr_extract(self, image: Image.Image, language: str) -> Dict[str, Any]:
        """Extract text using EasyOCR."""
        import easyocr

        # Initialize reader (cached for performance)
        reader = easyocr.Reader([language])

        # Convert PIL image to numpy array
        image_np = np.array(image)

        # Extract text
        results = reader.readtext(image_np)

        words = []
        confidences = []
        text_parts = []

        for bbox, text, confidence in results:
            words.append({
                'text': text,
                'confidence': confidence,
                'bbox': {
                    'x': bbox[0][0],
                    'y': bbox[0][1],
                    'width': bbox[2][0] - bbox[0][0],
                    'height': bbox[2][1] - bbox[0][1]
                }
            })
            confidences.append(confidence)
            text_parts.append(text)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        full_text = ' '.join(text_parts)

        return {
            "engine_used": OCREngine.EASYOCR,
            "text": full_text,
            "confidence": avg_confidence,
            "words": words
        }

    async def _paddleocr_extract(self, image: Image.Image, language: str) -> Dict[str, Any]:
        """Extract text using PaddleOCR."""
        from paddleocr import PaddleOCR

        # Initialize PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang=language, show_log=False)

        # Convert PIL image to numpy array
        image_np = np.array(image)

        # Extract text
        results = ocr.ocr(image_np, cls=True)

        words = []
        confidences = []
        text_parts = []

        if results and results[0]:
            for line in results[0]:
                bbox, (text, confidence) = line
                words.append({
                    'text': text,
                    'confidence': confidence,
                    'bbox': {
                        'x': bbox[0][0],
                        'y': bbox[0][1],
                        'width': bbox[2][0] - bbox[0][0],
                        'height': bbox[2][1] - bbox[0][1]
                    }
                })
                confidences.append(confidence)
                text_parts.append(text)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        full_text = ' '.join(text_parts)

        return {
            "engine_used": OCREngine.PADDLEOCR,
            "text": full_text,
            "confidence": avg_confidence,
            "words": words
        }

    async def _rapidocr_extract(self, image: Image.Image) -> Dict[str, Any]:
        """Extract text using RapidOCR."""
        from rapidocr_onnxruntime import RapidOCR

        # Initialize RapidOCR
        ocr = RapidOCR()

        # Convert PIL image to numpy array
        image_np = np.array(image)

        # Extract text
        results, _ = ocr(image_np)

        words = []
        confidences = []
        text_parts = []

        if results:
            for result in results:
                bbox, text, confidence = result
                words.append({
                    'text': text,
                    'confidence': confidence,
                    'bbox': {
                        'x': bbox[0][0],
                        'y': bbox[0][1],
                        'width': bbox[2][0] - bbox[0][0],
                        'height': bbox[2][1] - bbox[0][1]
                    }
                })
                confidences.append(confidence)
                text_parts.append(text)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        full_text = ' '.join(text_parts)

        return {
            "engine_used": OCREngine.RAPIDOCR,
            "text": full_text,
            "confidence": avg_confidence,
            "words": words
        }

    async def _google_vision_extract(self, image: Image.Image) -> Dict[str, Any]:
        """Extract text using Google Vision API."""
        try:
            from google.cloud import vision
            import io

            # Initialize Vision API client
            client = vision.ImageAnnotatorClient()

            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Create vision image
            vision_image = vision.Image(content=img_byte_arr)

            # Perform text detection
            response = client.text_detection(image=vision_image)
            annotations = response.text_annotations

            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")

            if not annotations:
                return {
                    "engine_used": OCREngine.GOOGLE_VISION,
                    "text": "",
                    "confidence": 0.0,
                    "words": []
                }

            # First annotation contains full text
            full_text = annotations[0].description

            # Remaining annotations are individual words/blocks
            words = []
            confidences = []

            for annotation in annotations[1:]:  # Skip first (full text)
                vertices = annotation.bounding_poly.vertices
                bbox = {
                    'x': vertices[0].x,
                    'y': vertices[0].y,
                    'width': vertices[2].x - vertices[0].x,
                    'height': vertices[2].y - vertices[0].y
                }

                # Google Vision doesn't provide confidence per word, use 95% as default
                confidence = 0.95

                words.append({
                    'text': annotation.description,
                    'confidence': confidence,
                    'bbox': bbox
                })
                confidences.append(confidence)

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.95

            return {
                "engine_used": OCREngine.GOOGLE_VISION,
                "text": full_text,
                "confidence": avg_confidence,
                "words": words
            }

        except ImportError:
            logger.error("google-cloud-vision not installed")
            raise Exception("Google Cloud Vision library not installed")
        except Exception as e:
            logger.error(f"Google Vision extraction failed: {e}")
            raise


# Singleton instance
ocr_orchestrator = OCROrchestrator()
