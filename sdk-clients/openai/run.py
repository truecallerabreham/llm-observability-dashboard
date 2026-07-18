"""Entry point for OpenAI SDK client."""

from client import run_openai_requests, setup_otel

if __name__ == "__main__":
    provider = setup_otel()
    results = run_openai_requests(10)
    print(f"Completed {len(results)} requests")
