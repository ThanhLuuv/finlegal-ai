#!/usr/bin/env bash
# Tail live Google Cloud Run logs in real-time
PROJECT_ID="learnenglish-462703"
SERVICE_NAME="finlegal-document-service"

echo "📜 Tailing live logs for Google Cloud Run service '${SERVICE_NAME}'..."
gcloud run services logs tail "${SERVICE_NAME}" --project "${PROJECT_ID}"
