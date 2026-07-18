"""
vLLM SDK Client with OpenLLMetry auto-instrumentation.

vLLM exposes an OpenAI-compatible API, so we use the OpenAI SDK
pointing to the vLLM endpoint. This demonstrates how self-hosted
models integrate into the observability pipeline.

For demo purposes, vLLM runs locally or can be mocked.
"""

import os
import time
import random
from unittest.mock import patch

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")


def setup_otel():
    """Initialize OpenTelemetry with OTLP HTTP exporter."""
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor

    exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    # vLLM uses OpenAI-compatible API, so we instrument with OpenAI
    OpenAIInstrumentor().instrument(tracer_provider=provider)
    return provider


PROMPTS = [
    "Explain the transformer architecture.",
    "What is attention mechanism?",
    "How does gradient descent work?",
    "What is fine-tuning?",
    "Explain tokenization in NLP.",
]


def run_vllm_requests(num_requests: int = 5) -> list[dict]:
    """Send requests to vLLM (OpenAI-compatible API)."""
    import openai

    results = []
    for i in range(num_requests):
        prompt = random.choice(PROMPTS)
        model = "meta-llama/Llama-3.1-8B-Instruct"  # Common vLLM model

        # For demo: mock the response since vLLM may not be running
        mock_response = {
            "id": f"chatcmpl-vllm-{i+1:03d}",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"vLLM response to: {prompt}",
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()) + 8,
                "completion_tokens": 18,
                "total_tokens": len(prompt.split()) + 26,
            },
        }

        try:
            with patch(
                "openai.resources.chat.completions.Completions.create",
                return_value=type("MockResponse", (), mock_response)(),
            ):
                client = openai.OpenAI(
                    api_key="not-needed",
                    base_url=VLLM_BASE_URL,
                )
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                )

                results.append({
                    "provider": "vllm",
                    "model": model,
                    "prompt": prompt,
                    "input_tokens": mock_response["usage"]["prompt_tokens"],
                    "output_tokens": mock_response["usage"]["completion_tokens"],
                })

        except Exception as e:
            results.append({
                "provider": "vllm",
                "model": model,
                "error": str(e),
            })

        time.sleep(0.1)

    return results


if __name__ == "__main__":
    print("Setting up OpenTelemetry for vLLM...")
    provider = setup_otel()

    print("Running 5 vLLM requests...")
    results = run_vllm_requests(5)

    for i, r in enumerate(results, 1):
        if "error" in r:
            print(f"  [{i}] ERROR: {r['error']}")
        else:
            print(f"  [{i}] provider={r['provider']} model={r['model']} "
                  f"tokens={r['input_tokens']}+{r['output_tokens']}")

    print("\nDone! Spans should appear in ClickHouse.")
    print("Query: SELECT * FROM otel_traces WHERE Provider = 'vllm'")
