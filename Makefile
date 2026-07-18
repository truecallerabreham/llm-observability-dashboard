# ============================================================
# LLM Observability Dashboard — Makefile
# ============================================================
# Shortcuts for common operations. Run: make <command>

.PHONY: up down restart logs status build clean

# --------------------------------------------------------
# Start all services
# --------------------------------------------------------
up:
	docker compose up -d
	@echo ""
	@echo "Services starting..."
	@echo "  Dashboard:    http://localhost:3000"
	@echo "  ClickHouse:   http://localhost:8123"
	@echo "  Prometheus:   http://localhost:9090"
	@echo "  Alertmanager: http://localhost:9093"
	@echo ""

# --------------------------------------------------------
# Stop all services
# --------------------------------------------------------
down:
	docker compose down

# --------------------------------------------------------
# Restart all services
# --------------------------------------------------------
restart:
	docker compose restart

# --------------------------------------------------------
# Rebuild and restart (use after code changes)
# --------------------------------------------------------
build:
	docker compose build --no-cache
	docker compose up -d

# --------------------------------------------------------
# View logs (all services)
# --------------------------------------------------------
logs:
	docker compose logs -f

# --------------------------------------------------------
# View logs for a specific service
# --------------------------------------------------------
logs-clickhouse:
	docker compose logs -f clickhouse

logs-nextjs:
	docker compose logs -f nextjs-app

logs-otel:
	docker compose logs -f otel-collector

logs-prometheus:
	docker compose logs -f prometheus

# --------------------------------------------------------
# Check service health
# --------------------------------------------------------
status:
	docker compose ps

# --------------------------------------------------------
# Open ClickHouse shell
# --------------------------------------------------------
clickhouse-shell:
	docker compose exec clickhouse clickhouse-client \
		--user $${CLICKHOUSE_USER:-admin} \
		--password $${CLICKHOUSE_PASSWORD:-changeme}

# --------------------------------------------------------
# Open Postgres shell
# --------------------------------------------------------
postgres-shell:
	docker compose exec postgres psql \
		-U $${POSTGRES_USER:-admin} \
		-d $${POSTGRES_DB:-observability}

# --------------------------------------------------------
# Clean everything (including volumes!)
# --------------------------------------------------------
clean:
	docker compose down -v
	@echo "All containers and volumes removed."

# --------------------------------------------------------
# View Prometheus targets
# --------------------------------------------------------
prometheus-targets:
	@echo "Opening Prometheus targets..."
	@start http://localhost:9090/targets
