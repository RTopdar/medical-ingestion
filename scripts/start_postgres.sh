#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/../docker-compose.postgres.yml"

if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon not running. Start Docker first." >&2
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" up -d
elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "$COMPOSE_FILE" up -d
else
    echo "No compose plugin found, fallback to docker run."
    if docker ps -a --format '{{.Names}}' | grep -q '^medical-ingestion-postgres$'; then
        docker start medical-ingestion-postgres
    else
        docker run -d \
            --name medical-ingestion-postgres \
            -p 5432:5432 \
            -e POSTGRES_DB=medical_ingestion \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=postgres \
            -v postgres_storage:/var/lib/postgresql/data \
            --restart unless-stopped \
            postgres:16
    fi
fi

echo "Postgres up on localhost:5432 (db=medical_ingestion, user=postgres)."
