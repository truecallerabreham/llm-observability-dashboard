"""
OpenAI SDK Client with OpenLLMetry auto-instrumentation.

This client sends mocked completions to avoid real API costs.
The OTel SDK emits canonical GenAI spans for every request.
"""

import os
import json
import time
import random
from pathlib import Path
from unittest.mock import patch

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.trace import get_tracer_provider

# ============================================================
# OTel Setup
# ============================================================

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")


def setup_otel():
    """Initialize OpenTelemetry with OTLP HTTP exporter."""
    exporter = OTLPSpanExporter(
        endpoint=f"{OTEL_ENDPOINT}/v1/traces",
    )
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    OpenAIInstrumentor().instrument(tracer_provider=provider)
    return provider


# ============================================================
# Mock Data
# ============================================================

MOCK_DIR = Path(__file__).parent.parent.parent / "mocks" / "openai"


def load_mock(model: str) -> dict:
    """Load a pre-recorded mock response for the given model."""
    if "mini" in model:
        mock_file = MOCK_DIR / "chat_completion_mini.json"
    else:
        mock_file = MOCK_DIR / "chat_completion.json"

    with open(mock_file) as f:
        return json.load(f)


# ============================================================
# Client
# ============================================================

MODELS = ["gpt-4o", "gpt-4o-mini"]


def run_openai_requests(num_requests: int = 10) -> list[dict]:
    """
    Send N mocked OpenAI chat completion requests.
    Each request emits an OTel span via OpenLLMetry.
    """
    import openai

    results = []
    for i in range(num_requests):
        model = random.choice(MOCKS := MODELS)
        mock_response = load_mock(model)

        with patch(
            "openai.resources.chat.completions.Completions.create",
            return_value=type("MockResponse", (), mock_response)(),
        ):
            client = openai.OpenAI(api_key="sk-mock-not-real")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Test message {i + 1}: What is {random.randint(1, 100)} + {random.randint(1, 100)}?"},
                ],
            )

            results.append({
                "model": model,
                "input_tokens": mock_response["usage"]["prompt_tokens"],
                "output_tokens": mock_response["usage"]["completion_tokens"],
                "response_id": mock_response["id"],
            })

        time.sleep(0.1)  # Brief pause between requests

    return results


if __name__ == "__main__":
    print("Setting up OpenTelemetry...")
    provider = setup_otel()

    print(f"Running {10} mocked OpenAI requests...")
    results = run_openai_requests(10)

    for i, r in enumerate(results, 1):
        print(f"  [{i}] model={r['model']} "
              f"tokens={r['input_tokens']}+{r['output_tokens']} "
              f"response={r['response_id']}")

    print("\nDone! Spans should appear in ClickHouse within 10 seconds.")
    print("Query: SELECT * FROM otel_traces WHERE Provider = 'openai'")
