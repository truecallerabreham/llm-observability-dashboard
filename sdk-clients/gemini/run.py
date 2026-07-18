"""Entry point for Gemini SDK client."""

from client import run_gemini_requests, setup_otel

if __name__ == "__main__":
    provider = setup_otel()
    results = run_gemini_requests(5)
    print(f"Completed {len(results)} requests")
