from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ExtractionRequest(BaseModel):
    documentId: str = Field(..., description="Unique document ID (e.g. doc_1786954046077)")
    fileUrl: Optional[str] = Field(None, description="Pre-signed R2 URL to download raw document binary")
    fileName: Optional[str] = Field(None, description="File name with extension")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parsing options (dpi, forceOcr, etc.)")

class PageBlock(BaseModel):
    blockIndex: int
    text: str
    bbox: List[float] = Field(default_factory=list, description="[x0, y0, x1, y1] coordinates")
    blockType: str = Field("paragraph", description="heading, paragraph, list, table, code")

class DocumentPage(BaseModel):
    pageNumber: int
    text: str
    method: str = Field(..., description="native_pymupdf | ocr_tesseract | layout_docling")
    qualityScore: float = Field(..., description="Quality score between 0.00 and 1.00")
    blocks: List[PageBlock] = Field(default_factory=list)

class ParsedDocument(BaseModel):
    documentId: str
    pages: List[DocumentPage]
    fullText: str
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
