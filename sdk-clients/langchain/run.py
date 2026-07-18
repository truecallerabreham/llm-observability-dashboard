"""
LangChain SDK Client with OpenLLMetry auto-instrumentation.

LangChain wraps OpenAI under the hood, so spans appear as nested
parent-child relationships: LangChain "chain" span (parent) and
OpenAI "LLM" span (child). This demonstrates the waterfall view.
"""

import os
import time
import random
from unittest.mock import patch

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")


def setup_otel():
    """Initialize OpenTelemetry with OTLP HTTP exporter."""
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.langchain import LangChainInstrumentor

    exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    LangChainInstrumentor().instrument(tracer_provider=provider)
    return provider


PROMPTS = [
    "What is machine learning?",
    "Explain Docker containers.",
    "What is a REST API?",
    "How does DNS work?",
    "What is load balancing?",
]


def run_langchain_requests(num_requests: int = 5) -> list[dict]:
    """Send requests through LangChain (wrapping mocked OpenAI)."""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    results = []
    for i in range(num_requests):
        prompt = random.choice(PROMPTS)

        # Mock the OpenAI API call to avoid real costs
        mock_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"LangChain processed: {prompt}",
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()) + 5,
                "completion_tokens": 20,
                "total_tokens": len(prompt.split()) + 25,
            },
        }

        with patch(
            "openai.resources.chat.completions.Completions.create",
            return_value=type("MockResponse", (), mock_response)(),
        ):
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key="sk-mock-not-real",
            )
            messages = [HumanMessage(content=prompt)]
            response = llm.invoke(messages)

            results.append({
                "provider": "langchain",
                "model": "gpt-4o",
                "prompt": prompt,
                "response_length": len(response.content),
            })

        time.sleep(0.1)

    return results


if __name__ == "__main__":
    print("Setting up OpenTelemetry for LangChain...")
    provider = setup_otel()

    print("Running 5 LangChain requests...")
    results = run_langchain_requests(5)

    for i, r in enumerate(results, 1):
        print(f"  [{i}] provider={r['provider']} model={r['model']} "
              f"prompt='{r['prompt'][:40]}...'")

    print("\nDone! Spans should appear in ClickHouse (parent-child relationships).")
    print("Query: SELECT * FROM otel_traces WHERE ServiceName LIKE '%langchain%'")
