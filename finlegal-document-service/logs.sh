#!/usr/bin/env bash
# Read recent Google Cloud Run logs
PROJECT_ID="learnenglish-462703"
SERVICE_NAME="finlegal-document-service"

echo "Reading recent logs for Google Cloud Run service '${SERVICE_NAME}'..."
gcloud run services logs read "${SERVICE_NAME}" --project "${PROJECT_ID}" --limit 50
