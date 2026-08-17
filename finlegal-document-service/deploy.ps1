# Automated Deployment Script for FinLegal Document Processing Service to Google Cloud Run
$ErrorActionPreference = "Stop"

$PROJECT_ID = "learnenglish-462703"
$SERVICE_NAME = "finlegal-document-service"
$REGION = "asia-southeast1"
$IMAGE_TAG = "gcr.io/learnenglish-462703/finlegal-document-service:latest"

Write-Host "Step 1: Building container image on Google Cloud Build..." -ForegroundColor Cyan
gcloud builds submit --tag $IMAGE_TAG --project $PROJECT_ID

Write-Host "Step 2: Deploying updated container to Google Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $SERVICE_NAME --image $IMAGE_TAG --platform managed --region $REGION --allow-unauthenticated --memory 1Gi --cpu 1 --min-instances 0 --max-instances 2 --project $PROJECT_ID

Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
