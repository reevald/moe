# Makefile for MOE Project
# Simplifies common development tasks

.PHONY: help install run-api run-worker run-migrations \
        docker-build-api docker-build-worker \
        docker-build-migration docker-build-all \
        docker-run-api docker-run-worker \
        docker-test-db docker-migrate docker-seed \
        clean test

help:
	@echo "MOE Project - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install          - Install dependencies"
	@echo "  make run-api          - Run API service locally"
	@echo "  make run-worker       - Run worker service locally"
	@echo "  make run-migrations   - Run database migrations"
	@echo ""
	@echo "Docker Build:"
	@echo "  make docker-build-all - Build all Docker images"
	@echo "  make docker-build-api - Build API Docker image"
	@echo "  make docker-build-worker - Build Worker image"
	@echo "  make docker-build-migration - Build Migration image"
	@echo ""
	@echo "Docker Migration:"
	@echo "  make docker-migration-up   - Start migration container with volume"
	@echo "  make docker-migration-down - Stop and remove migration container"
	@echo "  make docker-test-db        - Test database connection"
	@echo "  make docker-migrate        - Run migrations"
	@echo "  make docker-seed FILE=<file> [LIMIT=<n>] [UPSERT=true|FORCE=true]"
	@echo "      Seed database with different modes:"
	@echo "      - Default: INSERT only (fails on duplicates)"
	@echo "      - UPSERT=true: Update existing, insert new"
	@echo "      - FORCE=true: Clear table before seeding"
	@echo ""
	@echo "Alembic Migration Management (Pure Alembic - Schema Only):"
	@echo "  make docker-alembic-autogenerate MSG=\"description\" - Auto-generate migration from models"
	@echo "  make docker-alembic-revision MSG=\"description\" - Create empty migration"
	@echo "  make docker-alembic-upgrade       - Apply all pending migrations"
	@echo "  make docker-alembic-downgrade     - Rollback last migration"
	@echo "  make docker-alembic-history       - Show migration history"
	@echo "  make docker-alembic-current       - Show current migration version"
	@echo "  make docker-reset-db              - Drop all tables and clear version history"
	@echo ""
	@echo "Examples:"
	@echo "  make docker-seed FILE=/app/wkbk_lean.sql LIMIT=100"
	@echo "  make docker-seed FILE=/app/wkbk_lean.sql UPSERT=true"
	@echo "  make docker-seed FILE=/app/wkbk_lean.sql FORCE=true"
	@echo "  make docker-alembic-revision MSG=\"add_difficulty_column\""
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            - Clean cache files"
	@echo "  make test             - Run tests"

install:
	poetry install

run-api:
	set -a && \
	. .env.common && \
	. .env.api && \
	set +a && \
	poetry run uvicorn api.main:app --reload --host 0.0.0.0 \
	--port 8000

run-worker:
	set -a && \
	. .env.common && \
	. .env.worker && \
	set +a && \
	poetry run celery -A worker.celery_app worker \
	--loglevel=info

run-migrations:
	set -a && \
	. .env.common && \
	set +a && \
	poetry run alembic -c migration/alembic.ini upgrade head

docker-build-api:
	docker build -f Dockerfile.api -t moe-api:latest .

docker-build-worker:
	docker build -f Dockerfile.worker -t moe-worker:latest .

docker-build-migration:
	docker build -f Dockerfile.migration -t moe-migration:latest .

docker-build-all: docker-build-api docker-build-worker \
                  docker-build-migration
	@echo "All Docker images built successfully"

# Start migration container with volume mounted (stateless)
docker-migration-up:
	@echo "Starting migration container..."
	@docker run -d --name moe-migration \
		--env-file .env.migration \
		-v $(PWD)/wkbk_lean.sql:/app/wkbk_lean.sql:ro \
		-v $(PWD)/migration/versions:/app/migration/versions \
		moe-migration:latest
	@echo "✓ Container started: moe-migration"
	@echo "  Data file mounted: wkbk_lean.sql (read-only)"
	@echo "  Migration versions: migration/versions (read-write)"

# Stop and remove migration container
docker-migration-down:
	@echo "Stopping migration container..."
	@docker stop moe-migration 2>/dev/null || true
	@docker rm moe-migration 2>/dev/null || true
	@echo "✓ Container stopped and removed"

# Test database connection using docker exec (Hybrid)
docker-test-db:
	@echo "Testing database connections..."
	@docker exec moe-migration python migration/migrate.py test

# Run database migrations using docker exec (DATABASE_URL)
docker-migrate:
	@echo "Running database migrations via DATABASE_URL..."
	@docker exec moe-migration python migration/migrate.py migrate

# Seed database using docker exec (REST API)
# Usage: 
#   make docker-seed FILE=/app/wkbk_lean.sql [LIMIT=100]
#   make docker-seed FILE=/app/wkbk_lean.sql LIMIT=100 UPSERT=true
#   make docker-seed FILE=/app/wkbk_lean.sql FORCE=true
# FILE is required, LIMIT/UPSERT/FORCE are optional
docker-seed:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter is required"; \
		echo "Usage: make docker-seed FILE=/app/wkbk_lean.sql [LIMIT=100] [UPSERT=true|FORCE=true]"; \
		echo ""; \
		echo "Modes:"; \
		echo "  Default       INSERT only (fails on duplicates)"; \
		echo "  UPSERT=true   Update existing, insert new"; \
		echo "  FORCE=true    Clear table before seeding"; \
		exit 1; \
	fi
	@echo "Seeding database via REST API..."
	@echo "  File: $(FILE)"
	@# Build command with optional parameters
	@CMD="python migration/migrate.py seed $(FILE)"; \
	if [ -n "$(LIMIT)" ]; then \
		echo "  Limit: $(LIMIT) rows"; \
		CMD="$$CMD $(LIMIT)"; \
	else \
		echo "  Limit: All rows"; \
	fi; \
	if [ "$(UPSERT)" = "true" ]; then \
		echo "  Mode: UPSERT (update existing, insert new)"; \
		CMD="$$CMD --upsert"; \
	elif [ "$(FORCE)" = "true" ]; then \
		echo "  Mode: FORCE (clear table first)"; \
		CMD="$$CMD --force"; \
	else \
		echo "  Mode: INSERT (fail on duplicates)"; \
	fi; \
	docker exec moe-migration $$CMD

# Alembic migration management commands
docker-alembic-revision:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG parameter is required"; \
		echo "Usage: make docker-alembic-revision MSG=\"description\""; \
		exit 1; \
	fi
	@echo "Creating new alembic revision: $(MSG)"
	@docker exec moe-migration alembic -c migration/alembic.ini revision -m "$(MSG)"

docker-alembic-autogenerate:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG parameter is required"; \
		echo "Usage: make docker-alembic-autogenerate MSG=\"description\""; \
		exit 1; \
	fi
	@echo "Auto-generating alembic revision from models: $(MSG)"
	@docker exec moe-migration alembic -c migration/alembic.ini revision --autogenerate -m "$(MSG)"

docker-alembic-upgrade:
	@echo "Running alembic upgrade head..."
	@docker exec moe-migration alembic -c migration/alembic.ini upgrade head

docker-alembic-downgrade:
	@echo "Running alembic downgrade -1..."
	@docker exec moe-migration alembic -c migration/alembic.ini downgrade -1

docker-alembic-history:
	@echo "Alembic migration history:"
	@docker exec moe-migration alembic -c migration/alembic.ini history --verbose

docker-alembic-current:
	@echo "Current alembic version:"
	@docker exec moe-migration alembic -c migration/alembic.ini current

docker-reset-db:
	@echo "WARNING: This will DROP ALL TABLES and DELETE ALL DATA!"
	@read -p "Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	@docker exec moe-migration python migration/reset_db.py

# One-command migration workflow
docker-migration-full: docker-migration-up
	@echo ""
	@echo "Waiting for container to be ready..."
	@sleep 2
	@echo ""
	$(MAKE) docker-test-db
	@echo ""
	@read -p "Press Enter to continue with migrations..." dummy
	@echo ""
	$(MAKE) docker-migrate
	@echo ""
	@read -p "Press Enter to continue with seeding..." dummy
	@echo ""
	$(MAKE) docker-seed
	@echo ""
	@echo "Migration workflow complete! Run 'make docker-migration-down' to cleanup."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned cache files"

test:
	poetry run pytest tests/ -v
