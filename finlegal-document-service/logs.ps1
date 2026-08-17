# Read recent Google Cloud Run logs
$PROJECT_ID = "learnenglish-462703"
$SERVICE_NAME = "finlegal-document-service"

Write-Host "Reading recent logs for Google Cloud Run service finlegal-document-service..." -ForegroundColor Cyan
gcloud run services logs read finlegal-document-service --project learnenglish-462703 --limit 50
