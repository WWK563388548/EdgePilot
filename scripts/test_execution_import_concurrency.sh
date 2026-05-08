#!/usr/bin/env bash
set -euo pipefail

POSTGRES_USER="${POSTGRES_USER:-edgepilot}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-edgepilot}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
TEST_DB_NAME="${EDGEPILOT_CONCURRENCY_TEST_DB:-edgepilot_execution_import_concurrency_test}"
TEST_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${TEST_DB_NAME}"

cleanup() {
  docker compose exec -T postgres dropdb --if-exists --force -U "${POSTGRES_USER}" "${TEST_DB_NAME}" >/dev/null 2>&1 || true
}

trap cleanup EXIT

docker compose up -d postgres

until docker compose exec -T postgres pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB:-edgepilot}" >/dev/null 2>&1; do
  sleep 1
done

cleanup
docker compose exec -T postgres createdb -U "${POSTGRES_USER}" "${TEST_DB_NAME}"

EDGEPILOT_DISPOSABLE_TEST_DATABASE_URL="${TEST_URL}" \
  .venv/bin/pytest \
  backend/tests/test_execution_import_service.py::test_import_csv_concurrent_duplicate_uploads_are_idempotent \
  -q
