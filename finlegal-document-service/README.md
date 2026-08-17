# FinLegal Document Processing Service (Google Cloud Run)

Dedicated high-precision document parsing microservice built with **FastAPI**, **PyMuPDF (fitz)**, **Quality Assessor**, and **300 DPI OCR**.

## Architecture Flow

```text
Cloudflare Worker Backend
      │
      ├── Generates R2 Signed URL
      ├── POST /extract { documentId, fileUrl }
      │
      ▼
Google Cloud Run (finlegal-document-service)
  ├── 1. Download document stream from R2 Signed URL
  ├── 2. PyMuPDF Native Extractor (Ultra-fast)
  ├── 3. Quality Assessor (Quality Score < 0.60?)
  │       ├── YES (Good) ──► Return PyMuPDF Parsed Layout
  │       └── NO  (Bad)  ──► Render Page @ 300 DPI + Tesseract OCR ──► Structured Markdown
  └── 4. Return ParsedDocument JSON
```

## Quick Start (Local Run)

```bash
# 1. Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run FastAPI dev server
uvicorn app.main:app --reload --port 8080
```

## Docker Container & Cloud Run Deployment

### 1. Build & Run Docker Container Locally
```bash
docker build -t finlegal-document-service .
docker run -p 8080:8080 finlegal-document-service
```

### 2. Deploy to Google Cloud Run
```bash
# Set Google Cloud Project
gcloud config set project YOUR_GCP_PROJECT_ID

# Build container image on Google Artifact Registry / Cloud Build
gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/finlegal-document-service

# Deploy to Cloud Run (Scale-to-Zero Enabled)
gcloud run deploy finlegal-document-service \
  --image gcr.io/YOUR_GCP_PROJECT_ID/finlegal-document-service \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10
```

## API Endpoints

- `GET /health`: Health check endpoint.
- `POST /extract`: Accepts `{ "documentId": "doc_xxx", "fileUrl": "https://..." }` and returns structured `ParsedDocument` JSON.
- `POST /extract/file`: Accepts direct multipart file upload.
