# Tail live Google Cloud Run logs in real-time
$PROJECT_ID = "learnenglish-462703"
$SERVICE_NAME = "finlegal-document-service"

Write-Host "📜 Tailing live logs for Google Cloud Run service '$SERVICE_NAME'..." -ForegroundColor Cyan
gcloud run services logs tail $SERVICE_NAME --project $PROJECT_ID
