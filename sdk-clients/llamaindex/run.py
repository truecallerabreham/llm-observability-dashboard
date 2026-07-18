"""
LlamaIndex SDK Client with OpenLLMetry auto-instrumentation.

LlamaIndex creates nested spans similar to LangChain: a query engine
span (parent) and an LLM span (child). This demonstrates how
orchestration frameworks create hierarchical traces.
"""

import os
import time
import random
from unittest.mock import patch, MagicMock

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")


def setup_otel():
    """Initialize OpenTelemetry with OTLP HTTP exporter."""
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.llamaindex import LlamaIndexInstrumentor

    exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    LlamaIndexInstrumentor().instrument(tracer_provider=provider)
    return provider


QUERIES = [
    "What is retrieval-augmented generation?",
    "How do vector databases work?",
    "Explain embedding models.",
    "What is semantic search?",
    "How does RAG improve LLM accuracy?",
]


def run_llamaindex_requests(num_requests: int = 5) -> list[dict]:
    """Send requests through LlamaIndex with mocked LLM responses."""
    from llama_index.llms.openai import OpenAI
    from llama_index.core import Settings

    results = []
    for i in range(num_requests):
        query = random.choice(QUERIES)

        # Mock the OpenAI API
        mock_response = MagicMock()
        mock_response.text = f"LlamaIndex response to: {query}"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = len(query.split()) + 10
        mock_response.usage.completion_tokens = 25
        mock_response.usage.total_tokens = len(query.split()) + 35

        with patch(
            "openai.resources.chat.completions.Completions.create",
            return_value=type("MockResponse", (), {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"LlamaIndex response to: {query}",
                    },
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": mock_response.usage.prompt_tokens,
                    "completion_tokens": mock_response.usage.completion_tokens,
                    "total_tokens": mock_response.usage.total_tokens,
                },
            })(),
        ):
            llm = OpenAI(model="gpt-4o", api_key="sk-mock-not-real")
            response = llm.complete(query)

            results.append({
                "provider": "llamaindex",
                "model": "gpt-4o",
                "query": query,
                "response_length": len(response.text),
            })

        time.sleep(0.1)

    return results


if __name__ == "__main__":
    print("Setting up OpenTelemetry for LlamaIndex...")
    provider = setup_otel()

    print("Running 5 LlamaIndex requests...")
    results = run_llamaindex_requests(5)

    for i, r in enumerate(results, 1):
        print(f"  [{i}] provider={r['provider']} model={r['model']} "
              f"query='{r['query'][:40]}...'")

    print("\nDone! Spans should appear in ClickHouse (nested parent-child).")
    print("Query: SELECT * FROM otel_traces WHERE ServiceName LIKE '%llamaindex%'")
