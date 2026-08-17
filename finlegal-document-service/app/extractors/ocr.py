try:
    import fitz
except ImportError:
    import pymupdf as fitz
import io
from typing import List, Tuple
from PIL import Image
from app.models.document import PageBlock

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

class OCRExtractor:
    @staticmethod
    def extract_page_ocr(doc: fitz.Document, page_index: int, dpi: int = 300) -> Tuple[str, List[PageBlock]]:
        """
        Renders PDF page to a high-resolution 300 DPI pixmap image and runs Tesseract OCR.
        """
        page = doc.load_page(page_index)
        
        # Render page to high-res image
        zoom = dpi / 72  # 72 DPI is standard 1.0 zoom
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        ocr_text = ""
        page_blocks: List[PageBlock] = []

        if HAS_TESSERACT:
            try:
                # Run OCR with English + Vietnamese language support
                ocr_text = pytesseract.image_to_string(image, lang="eng+vie").strip()
            except Exception as ocr_err:
                print(f"[OCR Notice] Tesseract execution fallback: {ocr_err}")
                ocr_text = ""

        # Build fallback block structure from line breaks
        if ocr_text:
            lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
            for idx, line in enumerate(lines):
                page_blocks.append(PageBlock(
                    blockIndex=idx,
                    text=line,
                    bbox=[0.0, 0.0, 0.0, 0.0],
                    blockType="heading" if len(line) < 50 and line.isupper() else "paragraph"
                ))

        return ocr_text, page_blocks
