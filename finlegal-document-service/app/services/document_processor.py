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

    @classmethod
    async def process_document(cls, request: ExtractionRequest, file_bytes: bytes = None) -> ParsedDocument:
        """
        Executes complete Tiered Processing Flow:
        PyMuPDF Native -> Quality Assessor -> OCR Fallback (@ 300 DPI) -> ParsedDocument Output
        """
        if not file_bytes and request.fileUrl:
            file_bytes = await cls.download_file(request.fileUrl)

        if not file_bytes:
            raise ValueError("Không thể tải file nhị phân (fileUrl hoặc file_bytes trống).")

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        print(f"📄 [Cloud Run Extractor] Processing docId='{request.documentId}' | Name='{request.fileName or 'document.pdf'}' | Total Pages={page_count} | Size={len(file_bytes)} bytes")

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

            print(f"  ├─ [Page #{page_idx + 1}/{page_count}] PyMuPDF Native: {len(native_text.split())} words, {len(native_text)} chars | Quality Score = {quality_score:.2f}")

            # Step 2: Fallback to High-Res OCR (@ 300 DPI) if Quality Score < 0.60
            if quality_score < 0.60 or request.options.get("forceOcr", False):
                print(f"  │  ⚡ [Page #{page_idx + 1}] Quality Score ({quality_score:.2f}) < 0.60 -> Triggering 300 DPI OCR Engine...")
                ocr_text, ocr_blocks = OCRExtractor.extract_page_ocr(doc, page_idx, dpi=300)
                ocr_quality = QualityAssessor.assess_page_quality(ocr_text)

                if ocr_text and (ocr_quality > quality_score or len(ocr_text) > len(native_text)):
                    chosen_text = ocr_text
                    chosen_blocks = ocr_blocks if ocr_blocks else native_blocks
                    quality_score = ocr_quality
                    method = "ocr_tesseract_300dpi"
                    print(f"  │  ✅ [Page #{page_idx + 1}] OCR Successful! {len(ocr_text.split())} words | New Quality Score = {quality_score:.2f}")

            methods_used[method] = methods_used.get(method, 0) + 1
            full_text_chunks.append(chosen_text)

            words = len(chosen_text.split())
            total_words += words
            total_chars += len(chosen_text)

            print(f"  📝 [PAGE #{page_idx + 1} EXTRACTED TEXT CONTENT]:\n{'='*70}\n{chosen_text}\n{'='*70}")

            pages.append(DocumentPage(
                pageNumber=page_idx + 1,
                text=chosen_text,
                method=method,
                qualityScore=quality_score,
                blocks=chosen_blocks
            ))

        doc.close()
        print(f"✅ [Cloud Run Extractor Complete] Extracted {total_words} words ({total_chars} chars) across {page_count} pages. Methods: {methods_used}")

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
