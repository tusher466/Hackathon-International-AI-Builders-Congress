PYTHON=python
PIP=pip
FRONTEND_DIR=frontend
FRONTEND_LEGACY_DIR=Fontend
NPM=npm

.PHONY: install train ingest-docs run demo test lint frontend-install frontend-build frontend-dev frontend-preview full-install full-build full-run docker-up docker-down clean

install:
	$(PIP) install -r requirements.txt

train:
	$(PYTHON) scripts/train_models.py --models-dir ./models

ingest-docs:
	$(PYTHON) -m knowledge.ingest_docs --dir ./data/manuals

run:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

run-prod:
	uvicorn api.main:app --host 0.0.0.0 --port 8000

demo:
	$(PYTHON) scripts/run_demo.py

test:
	pytest -v tests/

lint:
	ruff check .

# Frontend targets
frontend-install:
	cd $(FRONTEND_DIR) && $(NPM) install
	@echo "Also installing legacy Fontend if exists"
	@if exist $(FRONTEND_LEGACY_DIR) cd $(FRONTEND_LEGACY_DIR) && $(NPM) install || true

frontend-build:
	cd $(FRONTEND_DIR) && $(NPM) run build
	@echo "Copying build to legacy Fontend/dist for backward compat"
	@py -c "import shutil, pathlib; src=pathlib.Path('frontend/dist'); dst=pathlib.Path('Fontend/dist'); print('Copy dist'); shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)" || echo "Copy skipped"

frontend-dev:
	cd $(FRONTEND_DIR) && $(NPM) run dev

frontend-preview:
	cd $(FRONTEND_DIR) && $(NPM) run preview

# Full stack
full-install: install frontend-install
	@echo "Full stack dependencies installed"

full-build: frontend-build
	@echo "Frontend built to $(FRONTEND_DIR)/dist"
	@echo "Backend will serve frontend automatically when uvicorn runs"

full-run: full-build run
	@echo "Full stack running: frontend served at http://localhost:8000 + API at http://localhost:8000/api/v1"

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

# Clean
clean:
	rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/node_modules
	rm -rf $(FRONTEND_LEGACY_DIR)/dist
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
	@echo "Cleaned"

# Help
help:
	@echo "Available targets:"
	@echo "  install           - Install backend dependencies"
	@echo "  train             - Train ML models (synthetic if datasets missing)"
	@echo "  ingest-docs       - Ingest manuals to vector store"
	@echo "  run               - Run backend dev server with reload"
	@echo "  run-prod          - Run backend prod server"
	@echo "  frontend-install  - Install frontend dependencies"
	@echo "  frontend-build    - Build frontend for production (to frontend/dist)"
	@echo "  frontend-dev      - Run frontend dev server (vite on 3000, proxy to backend 8000)"
	@echo "  full-install      - Install both backend and frontend deps"
	@echo "  full-build        - Build frontend then backend ready to serve"
	@echo "  full-run          - Build frontend + run backend (merged single port 8000)"
	@echo "  docker-up         - Start docker services (mosquitto, backend, frontend)"
	@echo "  docker-down       - Stop docker services"
	@echo "  test              - Run pytest"
	@echo "  lint              - Run ruff"
	@echo "  clean             - Clean caches and builds"
