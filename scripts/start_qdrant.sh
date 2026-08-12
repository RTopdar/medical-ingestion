#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/../docker-compose.qdrant.yml"

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
    if docker ps -a --format '{{.Names}}' | grep -q '^medical-ingestion-qdrant$'; then
        docker start medical-ingestion-qdrant
    else
        docker run -d \
            --name medical-ingestion-qdrant \
            -p 6333:6333 -p 6334:6334 \
            -v qdrant_storage:/qdrant/storage \
            --restart unless-stopped \
            qdrant/qdrant:latest
    fi
fi

echo "Qdrant up. Dashboard: http://localhost:6333/dashboard"
