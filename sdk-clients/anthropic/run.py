"""Entry point for Anthropic SDK client."""

from client import run_anthropic_requests, setup_otel

if __name__ == "__main__":
    provider = setup_otel()
    results = run_anthropic_requests(10)
    print(f"Completed {len(results)} requests")
