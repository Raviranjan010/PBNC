import io
import pytesseract
from PIL import Image
from typing import Tuple, List, Optional
import shutil
from backend.app.core.config import settings

class OCRResult:
    def __init__(self, text: str, confidence: float, is_available: bool, warning: Optional[str] = None):
        self.text = text
        self.confidence = confidence
        self.is_available = is_available
        self.warning = warning

class OCRProcessor:
    @staticmethod
    def is_tesseract_installed() -> bool:
        if settings.TESSERACT_CMD and shutil.which(settings.TESSERACT_CMD):
            return True
        return bool(shutil.which("tesseract"))

    @classmethod
    def perform_ocr(cls, image_bytes: bytes) -> OCRResult:
        """
        Executes Tesseract OCR on page image bytes.
        Calculates average word confidence when available.
        Provides honest failure and warnings if OCR fails or binary is unavailable.
        """
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract detailed data with word-level confidences
            ocr_data = pytesseract.image_to_data(image, lang=settings.OCR_LANG, output_type=pytesseract.Output.DICT)
            
            words = []
            confidences = []
            for text, conf in zip(ocr_data.get("text", []), ocr_data.get("conf", [])):
                t = str(text).strip()
                if t:
                    words.append(t)
                    try:
                        c_val = float(conf)
                        if c_val >= 0:
                            confidences.append(c_val)
                    except (ValueError, TypeError):
                        pass

            extracted_text = " ".join(words).strip()
            
            # Compute average confidence (scaled 0.0 - 1.0)
            avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.5
            
            warning = None
            if avg_conf < 0.60:
                warning = f"Low OCR quality detected (average confidence: {avg_conf:.2f}). Scanned text may contain inaccuracies."
            elif not extracted_text:
                warning = "OCR returned empty text. Page may be blank, unreadable, or severely degraded."
                avg_conf = 0.2

            return OCRResult(
                text=extracted_text,
                confidence=round(avg_conf, 2),
                is_available=True,
                warning=warning
            )

        except pytesseract.TesseractNotFoundError:
            return OCRResult(
                text="",
                confidence=0.1,
                is_available=False,
                warning="Tesseract OCR binary is not installed or not found in system PATH. Manual transcription required."
            )
        except Exception as e:
            return OCRResult(
                text="",
                confidence=0.1,
                is_available=False,
                warning=f"OCR processing failed on document page: {str(e)}"
            )
