#!/usr/bin/env bash
# start.sh – Start Conway's Game of Life services with Docker Compose
set -euo pipefail

COMPOSE_FILE="$(cd "$(dirname "$0")/.." && pwd)/docker-compose.yml"

echo "==> Conway's Game of Life — Docker Compose startup"
echo "    Config: $COMPOSE_FILE"

# Build images (skipped if already built and unchanged)
echo "==> Building images..."
docker compose -f "$COMPOSE_FILE" build

echo "==> Starting services (detached)..."
docker compose -f "$COMPOSE_FILE" up --detach

echo "==> Service status:"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "==> Ready!"
echo "    Frontend  : http://localhost:3000"
echo "    API docs  : http://localhost:8000/docs"
echo "    API health: http://localhost:8000/health"
echo ""
echo "    To stop:  docker compose down"
echo "    To logs:  docker compose logs -f"
