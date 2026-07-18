"""
Anthropic SDK Client with OpenLLMetry auto-instrumentation.

Uses mocked completions to control costs. Anthropic's Messages API
has a different shape than OpenAI's Chat Completions API, but
OpenLLMetry normalizes both into the same gen_ai.* attribute schema.
"""

import os
import json
import time
import random
from pathlib import Path
from unittest.mock import patch, MagicMock

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
MOCK_DIR = Path(__file__).parent.parent.parent / "mocks" / "anthropic"


def setup_otel():
    """Initialize OpenTelemetry with OTLP HTTP exporter."""
    exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    AnthropicInstrumentor().instrument(tracer_provider=provider)
    return provider


def load_mock(model: str) -> dict:
    """Load a pre-recorded mock response."""
    if "haiku" in model:
        mock_file = MOCK_DIR / "message_haiku.json"
    else:
        mock_file = MOCK_DIR / "message.json"

    with open(mock_file) as f:
        return json.load(f)


MODELS = ["claude-3.5-sonnet", "claude-3-5-haiku"]


def run_anthropic_requests(num_requests: int = 10) -> list[dict]:
    """Send N mocked Anthropic messages API requests."""
    import anthropic

    results = []
    for i in range(num_requests):
        model = random.choice(MODELS)
        mock_response = load_mock(model)

        mock_client = MagicMock(spec=anthropic.Anthropic)
        mock_client.messages.create.return_value = type(
            "MockMessage", (), mock_response
        )()

        with patch("anthropic.Anthropic", return_value=mock_client):
            client = anthropic.Anthropic(api_key="sk-mock-not-real")
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": f"Test message {i + 1}: Explain the concept of {random.choice(['recursion', 'polymorphism', 'closures', 'event loops'])}."}
                ],
            )

            results.append({
                "model": model,
                "input_tokens": mock_response["usage"]["input_tokens"],
                "output_tokens": mock_response["usage"]["output_tokens"],
                "response_id": mock_response["id"],
            })

        time.sleep(0.1)

    return results


if __name__ == "__main__":
    print("Setting up OpenTelemetry for Anthropic...")
    provider = setup_otel()

    print(f"Running {10} mocked Anthropic requests...")
    results = run_anthropic_requests(10)

    for i, r in enumerate(results, 1):
        print(f"  [{i}] model={r['model']} "
              f"tokens={r['input_tokens']}+{r['output_tokens']} "
              f"response={r['response_id']}")

    print("\nDone! Spans should appear in ClickHouse within 10 seconds.")
    print("Query: SELECT * FROM otel_traces WHERE Provider = 'anthropic'")
