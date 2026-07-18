"""
Google Gemini SDK Client with OpenLLMetry auto-instrumentation.

Uses the Gemini free tier for real API calls. This gives authentic
traces with real response text, token counts, and latency.

Requirements:
  - GOOGLE_API_KEY set in environment
  - google-genai package installed
"""

import os
import time
import random

OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")


def setup_otel():
    """Initialize OpenTelemetry with OTLP HTTP exporter."""
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return provider


PROMPTS = [
    "What is the capital of France?",
    "Explain quantum computing in one sentence.",
    "Write a haiku about debugging code.",
    "What are the three laws of thermodynamics?",
    "How does a neural network learn?",
    "What is the difference between TCP and UDP?",
    "Explain the concept of eventual consistency.",
    "What is garbage collection in programming?",
]


def run_gemini_requests(num_requests: int = 5) -> list[dict]:
    """Send real requests to Gemini free tier."""
    from google import genai

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")

    client = genai.Client(api_key=api_key)
    results = []

    for i in range(num_requests):
        prompt = random.choice(PROMPTS)
        model = "gemini-2.0-flash"  # Cheapest free tier model

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            # Extract token counts from usage metadata
            usage = response.usage_metadata or {}
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0

            results.append({
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "response_text": response.text[:100] if response.text else "",
                "success": True,
            })

        except Exception as e:
            results.append({
                "model": model,
                "error": str(e),
                "success": False,
            })

        # Respect rate limits: ~15 RPM on free tier
        time.sleep(4)

    return results


if __name__ == "__main__":
    print("Setting up OpenTelemetry for Gemini...")
    provider = setup_otel()

    print("Running 5 real Gemini free-tier requests...")
    results = run_gemini_requests(5)

    for i, r in enumerate(results, 1):
        if r["success"]:
            print(f"  [{i}] model={r['model']} "
                  f"tokens={r['input_tokens']}+{r['output_tokens']} "
                  f"response={r['response_text'][:50]}...")
        else:
            print(f"  [{i}] ERROR: {r.get('error', 'unknown')}")

    print("\nDone! Spans should appear in ClickHouse within 10 seconds.")
    print("Query: SELECT * FROM otel_traces WHERE Provider = 'gcp.gen_ai'")
