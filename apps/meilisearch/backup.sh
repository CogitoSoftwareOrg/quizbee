#!/usr/bin/env sh
set -eu

MEILI_URL="${MEILI_URL:-http://meilisearch:7700}"
AUTH="Authorization: Bearer ${MEILI_MASTER_KEY}"

# 0) Ждём готовность Meili (перестраховка вместо depends_on:healthy)
echo "[0/4] Waiting for Meilisearch health..."
for i in $(seq 1 60); do
  if curl -fsS "${MEILI_URL}/health" >/dev/null 2>&1; then break; fi
  sleep 2
done
curl -fsS "${MEILI_URL}/health" >/dev/null

# 1) S3 alias
mc alias set s3 "${S3_ENDPOINT}" "${S3_ACCESS_KEY_ID}" "${S3_SECRET_ACCESS_KEY}" --api S3v4 >/dev/null
mc mb --ignore-existing "s3/${S3_BUCKET}" >/dev/null 2>&1 || true

ts="$(date -u +"%Y%m%dT%H%M%SZ")"
prefix="${BACKUP_PREFIX:-prod}"
obj="meili_dump_${prefix}_${ts}.dump"

echo "[1/4] Requesting Meilisearch dump..."
task_uid="$(curl -sS -X POST -H "${AUTH}" "${MEILI_URL}/dumps" | jq -r '.taskUid // .uid')"
[ -n "${task_uid}" ] && [ "${task_uid}" != "null" ] || { echo "Failed to create dump task"; exit 1; }

echo "[2/4] Waiting for task #${task_uid}..."
status="enqueued"
for i in $(seq 1 180); do
  status_json="$(curl -sS -H "${AUTH}" "${MEILI_URL}/tasks/${task_uid}")"
  status="$(echo "${status_json}" | jq -r '.status')"
  [ "${status}" = "failed" ] && { echo "Dump task failed: ${status_json}"; exit 1; }
  [ "${status}" = "succeeded" ] || [ "${status}" = "finished" ] && break
  sleep 2
done

dump_file="$(echo "${status_json}" | jq -r '.result.file // empty')"
if [ -z "${dump_file}" ] || [ "${dump_file}" = "null" ]; then
  dump_file="$(ls -t /meili_data/dumps/*.dump 2>/dev/null | head -n1 || true)"
else
  dump_file="/meili_data/dumps/${dump_file}"
fi
[ -f "${dump_file}" ] || { echo "Dump file not found"; exit 1; }

echo "[3/4] Uploading to S3: s3/${S3_BUCKET}/${prefix}/${obj}"
export AWS_REGION="${S3_REGION}"
mc cp "${dump_file}" "s3/${S3_BUCKET}/${prefix}/${obj}"

echo "[4/4] Prune local old dumps (keep 5)..."
ls -1t /meili_data/dumps/*.dump 2>/dev/null | tail -n +6 | xargs -r rm -f

echo "Backup finished: ${obj}"
