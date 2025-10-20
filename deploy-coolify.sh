#!/usr/bin/env bash
set -euo pipefail

COOLIFY_URL="${COOLIFY_URL:-https://app.coolify.io/api/v1}"
COOLIFY_TOKEN="${1:-}"  
GIT_SHA="${2:-}"                 
TAG="${3:-quizbee}"

if [[ -z "$GIT_SHA" ]]; then
  echo "❌ Usage: $0 <git_commit_sha>"
  exit 1
fi


echo "🚀 Deploying tag '$TAG' with commit SHA '$GIT_SHA' ..."

echo "🔍 Fetching apps with tag '$TAG'..."
APPS_JSON=$(curl -sS -H "Authorization: Bearer $COOLIFY_TOKEN" \
  "$COOLIFY_URL/applications?tags=$TAG")

APP_UUIDS=$(echo "$APPS_JSON" | jq -r '.[].uuid')

if [[ -z "$APP_UUIDS" ]]; then
  echo "❌ No applications found with tag '$TAG'"
  exit 1
fi

for UUID in $APP_UUIDS; do
  echo "🔧 Setting commit SHA for app $UUID"
  curl -sS -X PATCH "$COOLIFY_URL/applications/$UUID" \
    -H "Authorization: Bearer $COOLIFY_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"git_commit_sha\":\"$GIT_SHA\",\"instant_deploy\":false}" \
    >/dev/null
done

echo "🚀 Triggering deploy for all '$TAG' apps..."
curl -sS -H "Authorization: Bearer $COOLIFY_TOKEN" \
  "$COOLIFY_URL/deploy?tag=$TAG&force=true" >/dev/null

echo "✅ Deployment triggered successfully!"
