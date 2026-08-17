try:
    import fitz
except ImportError:
    import pymupdf as fitz
import httpx
from typing import List, Dict, Any
from app.models.document import ExtractionRequest, ParsedDocument, DocumentPage, PageBlock
from app.extractors.pdf_native import PyMuPDFNativeExtractor
from app.extractors.ocr import OCRExtractor
from app.quality.assessor import QualityAssessor

class DocumentProcessor:
    @staticmethod
    async def download_file(file_url: str) -> bytes:
        """Downloads document binary stream from pre-signed R2 URL."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(file_url)
            response.raise_for_status()
            return response.content

    @staticmethod
    def merge_ocr_header_if_missing(native_text: str, ocr_text: str) -> str:
        """
        Merges graphical headers (like candidate name/title in Canva/Figma PDFs) captured by 300 DPI OCR
        into PyMuPDF native text if native text missed the top header lines.
        """
        if not ocr_text or not ocr_text.strip():
            return native_text
        if not native_text or not native_text.strip():
            return ocr_text

        import re
        words = [w.strip() for w in re.split(r'[\s\n\r,.;:]+', native_text) if len(w.strip()) >= 3]
        if not words:
            return native_text

        ocr_lower = ocr_text.lower()
        pos = -1

        for word in words[:5]:
            w_lower = word.lower()
            idx = ocr_lower.find(w_lower)
            if idx != -1:
                pos = idx
                break

        if pos > 10:
            header_lines = ocr_text[:pos].strip().splitlines()
            valid_header_lines = [l.strip() for l in header_lines if l.strip()]
            if valid_header_lines:
                header_prefix = "\n".join(valid_header_lines)
                return header_prefix + "\n\n" + native_text

        return native_text

    @classmethod
    async def process_document(cls, request: ExtractionRequest, file_bytes: bytes = None) -> ParsedDocument:
        """
        Executes complete Tiered Processing Flow:
        PyMuPDF Native -> Quality Assessor -> OCR Fallback (@ 300 DPI) -> Hybrid Header Merger -> ParsedDocument Output
        """
        if not file_bytes and request.fileUrl:
            file_bytes = await cls.download_file(request.fileUrl)

        if not file_bytes:
            raise ValueError("Không thể tải file nhị phân (fileUrl hoặc file_bytes trống).")

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        print(f"[Cloud Run Extractor] Processing docId='{request.documentId}' | Name='{request.fileName or 'document.pdf'}' | Total Pages={page_count} | Size={len(file_bytes)} bytes")

        pages: List[DocumentPage] = []
        full_text_chunks: List[str] = []

        total_words = 0
        total_chars = 0
        methods_used: Dict[str, int] = {}

        for page_idx in range(page_count):
            # Step 1: Try PyMuPDF Native Extraction
            native_text, native_blocks = PyMuPDFNativeExtractor.extract_page_native(doc, page_idx)
            quality_score = QualityAssessor.assess_page_quality(native_text)

            chosen_text = native_text
            chosen_blocks = native_blocks
            method = "native_pymupdf"

            print(f"  * [Page #{page_idx + 1}/{page_count}] PyMuPDF Native: {len(native_text.split())} words, {len(native_text)} chars | Quality Score = {quality_score:.2f}")

            # Step 2: On Page 1 or low quality, run 300 DPI OCR to check for missing graphical headers (Canva/Figma PDFs)
            is_page_1 = (page_idx == 0)
            if quality_score < 0.60 or is_page_1 or request.options.get("forceOcr", False):
                print(f"    -> [Page #{page_idx + 1}] Running 300 DPI OCR Engine to check graphical headers...")
                ocr_text, ocr_blocks = OCRExtractor.extract_page_ocr(doc, page_idx, dpi=300)
                ocr_quality = QualityAssessor.assess_page_quality(ocr_text)

                if ocr_text:
                    if quality_score < 0.60:
                        chosen_text = ocr_text
                        chosen_blocks = ocr_blocks if ocr_blocks else native_blocks
                        quality_score = ocr_quality
                        method = "ocr_tesseract_300dpi"
                        print(f"    [OK] [Page #{page_idx + 1}] OCR Fallback Selected! {len(ocr_text.split())} words | Quality Score = {quality_score:.2f}")
                    else:
                        # Check if OCR captured missing top header lines
                        merged_text = cls.merge_ocr_header_if_missing(native_text, ocr_text)
                        if len(merged_text) > len(native_text):
                            chosen_text = merged_text
                            method = "hybrid_pymupdf_ocr"
                            print(f"    [HYBRID] [Page #{page_idx + 1}] Hybrid Merge Success! Prepend OCR top header lines to native text. Total: {len(chosen_text.split())} words")

            methods_used[method] = methods_used.get(method, 0) + 1
            full_text_chunks.append(chosen_text)

            words = len(chosen_text.split())
            total_words += words
            total_chars += len(chosen_text)

            print(f"  [PAGE #{page_idx + 1} EXTRACTED TEXT CONTENT]:\n{'='*70}\n{chosen_text}\n{'='*70}")

            pages.append(DocumentPage(
                pageNumber=page_idx + 1,
                text=chosen_text,
                method=method,
                qualityScore=quality_score,
                blocks=chosen_blocks
            ))

        doc.close()
        print(f"[OK] [Cloud Run Extractor Complete] Extracted {total_words} words ({total_chars} chars) across {page_count} pages. Methods: {methods_used}")

        full_document_text = "\n\n".join(full_text_chunks).strip()

        return ParsedDocument(
            documentId=request.documentId,
            pages=pages,
            fullText=full_document_text,
            tables=[],
            metadata={
                "pageCount": len(pages),
                "totalWords": total_words,
                "totalChars": total_chars,
                "methodsUsed": methods_used,
                "fileName": request.fileName or ""
            }
        )
