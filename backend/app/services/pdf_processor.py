import io
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
from PIL import Image

class PDFPageData:
    def __init__(self, page_number: int, text: str, width: float, height: float, image_bytes: bytes, is_scanned: bool):
        self.page_number = page_number
        self.text = text
        self.width = width
        self.height = height
        self.image_bytes = image_bytes
        self.is_scanned = is_scanned

class PDFProcessor:
    @staticmethod
    def process_pdf(pdf_bytes: bytes) -> List[PDFPageData]:
        """
        Extracts text, dimensions, and renders page snapshots for viewing.
        Flags pages as scanned if extracted text density is sparse (< 30 characters).
        """
        pages_data: List[PDFPageData] = []
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            rect = page.rect
            width = float(rect.width)
            height = float(rect.height)
            
            # Extract digital text
            text = page.get_text("text").strip()
            
            # Render page as PNG image for provenance viewing
            pix = page.get_pixmap(dpi=150)
            image_bytes = pix.tobytes("png")
            
            # If digital text is very sparse, it is likely a scanned PDF page requiring OCR
            is_scanned = len(text) < 40

            pages_data.append(PDFPageData(
                page_number=page_num,
                text=text,
                width=width,
                height=height,
                image_bytes=image_bytes,
                is_scanned=is_scanned,
            ))

        doc.close()
        return pages_data

    @staticmethod
    def process_image(image_bytes: bytes) -> PDFPageData:
        """
        Wraps a standalone image file (JPG/PNG) into a single page representation.
        """
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        # Render image to standard PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        return PDFPageData(
            page_number=1,
            text="",  # Standalone images have no digital text layer
            width=float(width),
            height=float(height),
            image_bytes=png_bytes,
            is_scanned=True,
        )
