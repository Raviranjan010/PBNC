import io
import fitz  # PyMuPDF
from PIL import Image
from typing import Tuple, Optional
from backend.app.core.config import settings

class DocumentValidationError(Exception):
    pass

class DocumentValidator:
    @staticmethod
    def detect_real_mime_type(content: bytes) -> str:
        """Inspect file signature (magic bytes) to identify the true file format."""
        if not content or len(content) < 4:
            raise DocumentValidationError("File is empty or too small to be a valid document.")
        
        # PDF signature: %PDF-
        if content.startswith(b"%PDF-"):
            return "application/pdf"
        
        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        
        # JPEG signature: FF D8 FF
        if content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        
        raise DocumentValidationError("Unsupported or unrecognized file format. Only PDF, PNG, and JPEG documents are permitted.")

    @classmethod
    def validate_file(cls, filename: str, content: bytes) -> Tuple[str, str, int]:
        """
        Validates file size, detected MIME type against permitted types,
        and ensures the document is readable and not corrupt.
        Returns: (file_type, mime_type, page_count)
        """
        # 1. Size check
        size = len(content)
        if size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise DocumentValidationError(f"File size ({size / (1024*1024):.2f}MB) exceeds the maximum allowed limit of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024)}MB.")
        if size == 0:
            raise DocumentValidationError("Uploaded file is empty (0 bytes).")

        # 2. Magic byte MIME detection
        real_mime = cls.detect_real_mime_type(content)
        if real_mime not in settings.ALLOWED_MIME_TYPES:
            raise DocumentValidationError(f"Detected MIME type '{real_mime}' is not permitted.")

        # 3. Format integrity & page count check
        page_count = 0
        file_type = "pdf" if real_mime == "application/pdf" else "image"

        if file_type == "pdf":
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                page_count = len(doc)
                if page_count == 0:
                    raise DocumentValidationError("PDF contains 0 pages.")
                # Verify first page can be read/rendered
                _ = doc[0].rect
                doc.close()
            except Exception as e:
                raise DocumentValidationError(f"Corrupted or unreadable PDF document: {str(e)}")
        else:
            try:
                img = Image.open(io.BytesIO(content))
                img.verify()  # Verify image integrity
                # Reopen for dimensions
                img = Image.open(io.BytesIO(content))
                width, height = img.size
                if width <= 0 or height <= 0:
                    raise DocumentValidationError("Invalid image dimensions.")
                page_count = 1
            except Exception as e:
                raise DocumentValidationError(f"Corrupted or unreadable image document: {str(e)}")

        return file_type, real_mime, page_count
