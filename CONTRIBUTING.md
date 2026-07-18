# Contributing to LLM Observability Dashboard

Thank you for your interest in contributing!

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local dashboard development)
- Python 3.11+ (for SDK clients and eval jobs)

### Quick Start

1. **Start infrastructure**
   ```bash
   docker compose up -d clickhouse postgres otel-collector prometheus alertmanager
   ```

2. **Install dashboard dependencies**
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```

3. **Install SDK client dependencies**
   ```bash
   pip install -r sdk-clients/requirements.txt
   ```

4. **Run SDK clients to generate test data**
   ```bash
   python sdk-clients/openai/run.py
   python sdk-clients/anthropic/run.py
   ```

## Project Architecture

- **Infrastructure**: Docker Compose orchestrates all services
- **Storage**: ClickHouse for traces (OLAP), Postgres for metadata (OTLP)
- **Instrumentation**: OpenLLMetry auto-instruments SDK calls
- **Dashboard**: Next.js 15 with Server Components + Client Components
- **Evals**: DeepEval for LLM-as-judge, RAGAS for RAG metrics
- **Alerting**: Prometheus scrapes metrics, Alertmanager routes alerts

## Running Tests

```bash
# SDK verification tests
pytest tests/sdk-verification/ -v

# Regression probe
python tests/regression/probe.py
```

## Code Style

- **TypeScript**: Follow Next.js conventions
- **Python**: Follow PEP 8, use type hints
- **SQL**: Use ClickHouse-specific syntax (MergeTree, etc.)

## Submitting Changes

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Make your changes
3. Run tests: `pytest tests/ -v`
4. Submit a pull request

## Questions?

Open an issue on GitHub or start a discussion.
