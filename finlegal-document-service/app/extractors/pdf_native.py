try:
    import fitz
except ImportError:
    import pymupdf as fitz
from typing import List, Tuple
from app.models.document import DocumentPage, PageBlock

class PyMuPDFNativeExtractor:
    @staticmethod
    def extract_page_native(doc: fitz.Document, page_index: int) -> Tuple[str, List[PageBlock]]:
        """
        Extracts structured text and layout blocks using PyMuPDF native C engine.
        """
        page = doc.load_page(page_index)
        
        # Extract structured blocks with bounding boxes
        blocks_data = page.get_text("blocks")
        if not blocks_data:
            return "", []

        # Sort blocks visually top-to-bottom (y0) with 10px line tolerance, then left-to-right (x0)
        sorted_blocks = sorted(blocks_data, key=lambda b: (round(float(b[1]) / 10) * 10, float(b[0])))
        
        page_blocks: List[PageBlock] = []
        text_parts: List[str] = []

        for idx, b in enumerate(sorted_blocks):
            # b format: (x0, y0, x1, y1, "text", block_no, block_type)
            block_text = b[4].strip() if len(b) > 4 else ""
            if not block_text:
                continue

            text_parts.append(block_text)

            bbox = [round(float(b[0]), 2), round(float(b[1]), 2), round(float(b[2]), 2), round(float(b[3]), 2)]
            
            # Simple block type classification
            block_type = "paragraph"
            if len(block_text.splitlines()) == 1 and len(block_text) < 60 and (block_text.isupper() or block_text.istitle()):
                block_type = "heading"

            page_blocks.append(PageBlock(
                blockIndex=idx,
                text=block_text,
                bbox=bbox,
                blockType=block_type
            ))

        page_text = "\n\n".join(text_parts).strip()
        return page_text, page_blocks
