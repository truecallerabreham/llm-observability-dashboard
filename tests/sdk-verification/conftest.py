"""
Pytest fixtures for SDK verification tests.

Provides a ClickHouse client fixture and helper functions
for querying spans and waiting for eventual consistency.
"""

import os
import time
import pytest

CLICKHOUSE_URL = os.getenv("CLICKHOUSE_URL", "http://localhost:8123")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "admin")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "changeme")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DATABASE", "otel")


@pytest.fixture(scope="session")
def clickhouse_client():
    """Create a ClickHouse client for test assertions."""
    import clickhouse_connect

    client = clickhouse_connect.get_client(
        host="localhost",
        port=8123,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def wait_for_spans():
    """
    Factory fixture: returns a function that polls ClickHouse
    until spans appear or timeout is reached.
    """
    def _wait(client, provider: str, min_count: int = 1, timeout: int = 30) -> list[dict]:
        """Poll ClickHouse until at least `min_count` spans appear."""
        start = time.time()
        while time.time() - start < timeout:
            result = client.query(
                "SELECT * FROM otel_traces WHERE Provider = %(provider)s",
                parameters={"provider": provider},
            )
            if len(result.result_rows) >= min_count:
                return result.result_rows
            time.sleep(1)

        raise TimeoutError(
            f"Timed out waiting for {min_count} spans from provider '{provider}' "
            f"after {timeout}s"
        )

    return _wait


def assert_valid_trace_id(trace_id: str):
    """Assert that a trace ID is a valid hex string."""
    assert isinstance(trace_id, str), f"TraceId must be string, got {type(trace_id)}"
    assert len(trace_id) >= 32, f"TraceId too short: {len(trace_id)} chars"
    assert all(c in "0123456789abcdef" for c in trace_id.lower()), \
        f"TraceId contains non-hex characters: {trace_id}"


def assert_tokens_positive(row: dict, input_col: str = 7, output_col: int = 8):
    """Assert that token counts are positive."""
    input_tokens = row.get(input_col, 0) if isinstance(row, dict) else row[input_col]
    output_tokens = row.get(output_col, 0) if isinstance(row, dict) else row[output_col]
    assert input_tokens > 0, f"Input tokens should be > 0, got {input_tokens}"
    assert output_tokens > 0, f"Output tokens should be > 0, got {output_tokens}"
