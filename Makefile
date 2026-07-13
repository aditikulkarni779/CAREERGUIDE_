.PHONY: help up down api web lint fmt test install

help:
	@echo "up      - start local datastores (docker compose)"
	@echo "down    - stop datastores"
	@echo "api     - run FastAPI dev server"
	@echo "web     - run Next.js dev server"
	@echo "install - install api + web deps"
	@echo "lint    - lint api + web"
	@echo "fmt     - format api + web"
	@echo "test    - run api tests"

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down

install:
	cd apps/api && pip install -e ".[dev]"
	cd apps/web && npm install

api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

lint:
	cd apps/api && ruff check . && mypy app
	cd apps/web && npm run lint

fmt:
	cd apps/api && ruff format . && ruff check --fix .
	cd apps/web && npm run format

test:
	cd apps/api && pytest -q
