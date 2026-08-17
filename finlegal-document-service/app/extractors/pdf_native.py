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
        page_text = page.get_text("text").strip()
        
        # Extract structured blocks with bounding boxes
        blocks_data = page.get_text("blocks")
        page_blocks: List[PageBlock] = []

        for idx, b in enumerate(blocks_data):
            # b format: (x0, y0, x1, y1, "text", block_no, block_type)
            block_text = b[4].strip() if len(b) > 4 else ""
            if not block_text:
                continue

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

        return page_text, page_blocks
