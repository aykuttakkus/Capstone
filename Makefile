.PHONY: install run-server run-client run-stack build-index ingest-pdfs test test-unit test-integration test-eval frontend-check compose-check verify docker-dev docker-prod docker-frontend-standalone docker-init-store clean

# --- Installation ---
install:
	@echo "📦 Installing backend dependencies..."
	pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	cd client && npm ci

# --- Execution ---
run-server:
	@echo "🚀 Starting FastAPI server..."
	python -m server.run

run-client:
	@echo "🎨 Starting Vite client..."
	cd client && npm run dev

run-stack:
	@echo "🐳 Starting full stack with Docker Compose..."
	docker compose up --build

docker-dev:
	@echo "🐳 Starting default development stack..."
	docker compose up --build

docker-prod:
	@echo "🐳 Starting clean base stack..."
	docker compose -f compose.yaml up --build

docker-frontend-standalone:
	@echo "🐳 Starting frontend against an external backend..."
	docker compose -f compose.yaml -f compose.frontend-standalone.yaml up --build frontend

docker-init-store:
	@echo "🗂️ Seeding the named runtime store volume..."
	docker compose -f compose.yaml -f compose.tools.yaml run --rm init-store

# --- Data Pipeline ---
build-index:
	@echo "🧠 Building RAG index from PDFs..."
	python -m scripts.build_index

ingest-pdfs:
	@echo "📄 Ingesting PDFs into processing pipeline..."
	python -m scripts.ingest_pdfs

# --- Testing & Quality ---
test:
	@echo "🧪 Running backend test suite..."
	$(MAKE) test-unit
	$(MAKE) test-integration

test-unit:
	@echo "⚡ Running unit tests..."
	pytest -m unit tests/unit

test-integration:
	@echo "🧩 Running integration tests..."
	pytest -m integration tests/integration

test-eval:
	@echo "📊 Running evaluation benchmarks..."
	python3 tests/jtest.py
	python3 -m server.app.evaluation.spec_eval
	python3 -m server.app.evaluation.rag_eval

frontend-check:
	@echo "🎨 Running frontend validation..."
	cd client && npm ci && npm run lint && npm run build

compose-check:
	@echo "🐳 Validating Docker Compose contracts..."
	docker compose config
	docker compose -f compose.yaml config
	docker compose -f compose.yaml -f compose.frontend-standalone.yaml config
	docker compose -f compose.yaml -f compose.tools.yaml config

verify:
	@echo "✅ Running delivery verification gate..."
	$(MAKE) test-unit
	$(MAKE) test-integration
	$(MAKE) frontend-check
	$(MAKE) compose-check

# --- Maintenance ---
clean:
	@echo "🧹 Cleaning up caches and build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf client/dist
