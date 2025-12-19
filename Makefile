.PHONY: help install dev run test docker-up docker-down clean seed

help:
	@echo "Guzo Rideshare Platform"
	@echo ""
	@echo "Commands:"
	@echo "  make install    - Install dependencies with Poetry"
	@echo "  make dev        - Run development server"
	@echo "  make run        - Run production server"
	@echo "  make test       - Run tests"
	@echo "  make docker-up  - Start Docker containers"
	@echo "  make docker-down- Stop Docker containers"
	@echo "  make seed       - Seed database with sample data"
	@echo "  make clean      - Clean up cache files"

install:
	poetry install

dev:
	poetry run uvicorn src.guzo.app:app --reload --host 0.0.0.0 --port 8000

run:
	poetry run uvicorn src.guzo.app:app --host 0.0.0.0 --port 8000

test:
	poetry run pytest

up:
	docker-compose up --build

down:
	docker-compose down

docker-logs:
	docker-compose logs -f

seed:
	poetry run python scripts/seed_db.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

