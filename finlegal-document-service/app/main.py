import os
import time
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from app.models.document import ExtractionRequest, ParsedDocument
from app.services.document_processor import DocumentProcessor

app = FastAPI(
    title="FinLegal Document Processing Service",
    description="Dedicated Document Understanding Microservice on Google Cloud Run (PyMuPDF + Quality Assessment + 300 DPI OCR)",
    version="1.0.0"
)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "service": "finlegal-document-service",
        "status": "online",
        "engine": "PyMuPDF Native + Tesseract OCR @ 300 DPI",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": int(time.time())}

@app.post("/extract", response_model=ParsedDocument)
async def extract_document(request: ExtractionRequest, x_api_token: str = Header(None)):
    """
    Primary Document Parsing Endpoint (Cloud Run Scale-to-Zero).
    Downloads binary stream from R2 signed URL, executes quality assessment & OCR fallback, returns ParsedDocument.
    """
    secret_token = os.getenv("SERVICE_SECRET_TOKEN")
    if secret_token and x_api_token != secret_token:
        raise HTTPException(status_code=401, detail="Unauthorized API Token.")

    try:
        start_time = time.time()
        parsed_doc = await DocumentProcessor.process_document(request)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        parsed_doc.metadata["latencyMs"] = elapsed_ms
        return parsed_doc
    except Exception as e:
        print(f"[Document Processing Error] docId={request.documentId}: {e}")
        raise HTTPException(status_code=500, detail=f"Bóc tách tài liệu thất bại: {str(e)}")

@app.post("/extract/file", response_model=ParsedDocument)
async def extract_document_file(
    file: UploadFile = File(...),
    documentId: str = Form(...),
    x_api_token: str = Header(None)
):
    """
    Direct Binary File Upload Fallback Endpoint.
    """
    secret_token = os.getenv("SERVICE_SECRET_TOKEN")
    if secret_token and x_api_token != secret_token:
        raise HTTPException(status_code=401, detail="Unauthorized API Token.")

    try:
        content = await file.read()
        request = ExtractionRequest(documentId=documentId, fileName=file.filename)
        start_time = time.time()
        parsed_doc = await DocumentProcessor.process_document(request, file_bytes=content)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        parsed_doc.metadata["latencyMs"] = elapsed_ms
        return parsed_doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tải trực tiếp file thất bại: {str(e)}")
