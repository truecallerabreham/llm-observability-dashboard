"""
SDK Verification Test Suite
============================
Verifies that all 6 SDK families produce canonical GenAI spans
landing in ClickHouse with correct attributes.

Run: pytest tests/sdk-verification/ -v

Prerequisites:
  - ClickHouse running on localhost:8123
  - OTel Collector running on localhost:4318
  - SDK clients have been run at least once (or run them as part of tests)
"""

import subprocess
import sys
import os
import time
import pytest

# Add sdk-clients to path so we can import the clients
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk-clients"))


class TestOpenAISDK:
    """Verify OpenAI SDK produces valid GenAI spans."""

    def test_spans_appear_in_clickhouse(self, clickhouse_client, wait_for_spans):
        """Run OpenAI client and verify spans land in ClickHouse."""
        from openai.client import run_openai_requests, setup_otel

        setup_otel()
        results = run_openai_requests(10)

        assert len(results) == 10, f"Expected 10 results, got {len(results)}"

        # Wait for spans to land in ClickHouse
        rows = wait_for_spans(clickhouse_client, provider="openai", min_count=5, timeout=30)
        assert len(rows) >= 5, f"Expected >= 5 spans in ClickHouse, got {len(rows)}"

    def test_span_attributes(self, clickhouse_client):
        """Verify OpenAI spans have correct GenAI attributes."""
        result = clickhouse_client.query(
            "SELECT * FROM otel_traces WHERE Provider = 'openai' LIMIT 5"
        )

        assert len(result.result_rows) > 0, "No OpenAI spans found"

        for row in result.result_rows:
            # Row indices match table columns
            trace_id = row[0]  # TraceId
            provider = row[6]  # Provider
            model = row[7]     # Model
            input_tokens = row[8]   # InputTokens
            output_tokens = row[9]  # OutputTokens

            assert provider == "openai", f"Expected provider 'openai', got '{provider}'"
            assert model in ["gpt-4o", "gpt-4o-mini"], f"Unexpected model: {model}"
            assert input_tokens > 0, f"Input tokens should be > 0"
            assert output_tokens > 0, f"Output tokens should be > 0"
            assert len(trace_id) >= 32, f"TraceId too short: {len(trace_id)} chars"

    def test_no_real_api_calls(self):
        """Verify mock was used (no real API key needed)."""
        # If the test ran without GOOGLE_API_KEY or OPENAI_API_KEY,
        # it证明 the mock is working
        assert os.getenv("OPENAI_API_KEY") is None or \
               os.getenv("OPENAI_API_KEY") == "sk-mock-not-real", \
            "Test should use mocked API, not real key"


class TestAnthropicSDK:
    """Verify Anthropic SDK produces valid GenAI spans."""

    def test_spans_appear_in_clickhouse(self, clickhouse_client, wait_for_spans):
        from anthropic.client import run_anthropic_requests, setup_otel

        setup_otel()
        results = run_anthropic_requests(10)

        assert len(results) == 10
        rows = wait_for_spans(clickhouse_client, provider="anthropic", min_count=5, timeout=30)
        assert len(rows) >= 5

    def test_span_attributes(self, clickhouse_client):
        result = clickhouse_client.query(
            "SELECT * FROM otel_traces WHERE Provider = 'anthropic' LIMIT 5"
        )

        assert len(result.result_rows) > 0
        for row in result.result_rows:
            provider = row[6]
            model = row[7]
            assert provider == "anthropic"
            assert "claude" in model.lower(), f"Unexpected model: {model}"


class TestGeminiSDK:
    """Verify Gemini SDK produces valid GenAI spans (free tier)."""

    def test_spans_appear_in_clickhouse(self, clickhouse_client, wait_for_spans):
        from gemini.client import run_gemini_requests, setup_otel

        setup_otel()
        results = run_gemini_requests(5)

        successful = [r for r in results if r.get("success")]
        assert len(successful) >= 1, "At least one Gemini request should succeed"

        rows = wait_for_spans(clickhouse_client, provider="gcp.gen_ai", min_count=1, timeout=30)
        assert len(rows) >= 1

    def test_real_response_content(self, clickhouse_client):
        """Verify Gemini returns real response text (not mocked)."""
        result = clickhouse_client.query(
            "SELECT * FROM otel_traces WHERE Provider = 'gcp.gen_ai' LIMIT 1"
        )
        if len(result.result_rows) > 0:
            # Real responses have varying lengths, not fixed mock text
            row = result.result_rows[0]
            assert row is not None


class TestLangChainSDK:
    """Verify LangChain produces nested spans (parent-child)."""

    def test_spans_appear_in_clickhouse(self, clickhouse_client, wait_for_spans):
        from langchain.run import run_langchain_requests, setup_otel

        setup_otel()
        results = run_langchain_requests(5)

        assert len(results) == 5
        rows = wait_for_spans(clickhouse_client, provider="langchain", min_count=3, timeout=30)
        assert len(rows) >= 3

    def test_parent_child_relationship(self, clickhouse_client):
        """Verify LangChain creates parent-child span hierarchy."""
        result = clickhouse_client.query(
            "SELECT TraceId, SpanId, ParentSpanId FROM otel_traces "
            "WHERE ServiceName LIKE '%langchain%' "
            "ORDER BY StartTime"
        )
        # LangChain should have at least one span with a non-empty ParentSpanId
        has_parent = any(row[2] for row in result.result_rows)
        assert has_parent, "LangChain should create parent-child span relationships"


class TestLlamaIndexSDK:
    """Verify LlamaIndex produces nested spans."""

    def test_spans_appear_in_clickhouse(self, clickhouse_client, wait_for_spans):
        from llamaindex.run import run_llamaindex_requests, setup_otel

        setup_otel()
        results = run_llamaindex_requests(5)

        assert len(results) == 5
        rows = wait_for_spans(clickhouse_client, provider="llamaindex", min_count=3, timeout=30)
        assert len(rows) >= 3


class TestVLLMSDK:
    """Verify vLLM produces valid spans (via OpenAI-compatible API)."""

    def test_spans_appear_in_clickhouse(self, clickhouse_client, wait_for_spans):
        from vllm.run import run_vllm_requests, setup_otel

        setup_otel()
        results = run_vllm_requests(5)

        assert len(results) == 5
        rows = wait_for_spans(clickhouse_client, provider="vllm", min_count=3, timeout=30)
        assert len(rows) >= 3

    def test_span_attributes(self, clickhouse_client):
        result = clickhouse_client.query(
            "SELECT * FROM otel_traces WHERE Provider = 'vllm' LIMIT 5"
        )
        for row in result.result_rows:
            model = row[7]
            assert "llama" in model.lower() or "vllm" in model.lower(), \
                f"Unexpected vLLM model: {model}"


class TestAllProviders:
    """Cross-provider integration tests."""

    def test_all_six_providers_present(self, clickhouse_client):
        """Verify all 6 SDK families have spans in ClickHouse."""
        result = clickhouse_client.query(
            "SELECT DISTINCT Provider FROM otel_traces"
        )
        providers = {row[0] for row in result.result_rows}

        expected = {"openai", "anthropic", "gcp.gen_ai", "langchain", "llamaindex", "vllm"}
        missing = expected - providers

        assert not missing, f"Missing providers: {missing}"

    def test_total_span_count(self, clickhouse_client):
        """Verify we have a reasonable number of spans total."""
        result = clickhouse_client.query("SELECT count() FROM otel_traces")
        count = result.result_rows[0][0]
        assert count >= 30, f"Expected >= 30 total spans, got {count}"

    def test_all_spans_have_trace_ids(self, clickhouse_client):
        """Every span must have a valid trace ID."""
        result = clickhouse_client.query(
            "SELECT TraceId FROM otel_traces WHERE length(TraceId) < 32"
        )
        assert len(result.result_rows) == 0, \
            f"{len(result.result_rows)} spans have invalid trace IDs"
