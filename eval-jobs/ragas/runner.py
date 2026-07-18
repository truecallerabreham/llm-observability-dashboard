"""
RAGAS Retrieval Metrics
========================
Evaluates RAG (Retrieval-Augmented Generation) pipeline quality
on traces that carry retrieval context.

Metrics:
  - Context Precision: How relevant is the retrieved context?
  - Context Recall: Does the context cover the needed information?
"""

import os
import time
import random
import logging
from datetime import datetime, timedelta

import clickhouse_connect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLICKHOUSE_URL = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "admin")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "changeme")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DATABASE", "otel")

SAMPLE_RATE = float(os.getenv("RAGAS_SAMPLE_RATE", "0.20"))


def get_client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_URL,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )


def fetch_rag_traces(client) -> list[dict]:
    """Fetch traces that might have retrieval context (LangChain/LlamaIndex)."""
    cutoff = datetime.utcnow() - timedelta(minutes=15)

    result = client.query(
        """
        SELECT TraceId, SpanId, Provider, Model, ServiceName
        FROM otel_traces
        WHERE StartTime >= %(cutoff)s
          AND (ServiceName LIKE '%%langchain%%' OR ServiceName LIKE '%%llamaindex%%')
        ORDER BY StartTime DESC
        LIMIT 100
        """,
        parameters={"cutoff": cutoff},
    )

    sampled = []
    for row in result.result_rows:
        if random.random() < SAMPLE_RATE:
            sampled.append({
                "trace_id": row[0],
                "span_id": row[1],
                "provider": row[2],
                "model": row[3],
                "service_name": row[4],
            })

    logger.info(f"Sampled {len(sampled)} RAG traces for evaluation")
    return sampled


def evaluate_rag_trace(trace: dict) -> list[dict]:
    """
    Evaluate RAG quality for a single trace.

    For demo: generates synthetic scores.
    In production: uses RAGAS metrics with actual context/retrieval data.
    """
    results = []

    # Context Precision: how relevant is retrieved context
    context_precision = random.uniform(0.5, 0.95)
    results.append({
        "trace_id": trace["trace_id"],
        "span_id": trace["span_id"],
        "metric_name": "context_precision",
        "score": context_precision,
        "reason": f"Retrieved context precision: {context_precision:.2f}",
        "model_used": "gpt-4o",
        "evaluated_provider": trace["provider"],
        "evaluated_model": trace["model"],
        "evaluated_at": datetime.utcnow().isoformat(),
    })

    # Context Recall: does context cover the needed information
    context_recall = random.uniform(0.4, 0.9)
    results.append({
        "trace_id": trace["trace_id"],
        "span_id": trace["span_id"],
        "metric_name": "context_recall",
        "score": context_recall,
        "reason": f"Context recall score: {context_recall:.2f}",
        "model_used": "gpt-4o",
        "evaluated_provider": trace["provider"],
        "evaluated_model": trace["model"],
        "evaluated_at": datetime.utcnow().isoformat(),
    })

    return results


def write_eval_spans(client, results: list[dict]):
    """Write RAGAS eval results to ClickHouse."""
    if not results:
        return

    client.insert(
        table="eval_spans",
        values=results,
        column_names=[
            "TraceId", "SpanId", "MetricName", "Score", "Reason",
            "ModelUsed", "EvaluatedProvider", "EvaluatedModel", "EvaluatedAt",
        ],
    )
    logger.info(f"Wrote {len(results)} RAGAS eval spans")


def run_ragas_job():
    """Main RAGAS eval entry point."""
    logger.info("Starting RAGAS retrieval metrics job...")
    start = time.time()

    client = get_client()
    traces = fetch_rag_traces(client)

    all_results = []
    for trace in traces:
        results = evaluate_rag_trace(trace)
        all_results.extend(results)

    write_eval_spans(client, all_results)

    elapsed = time.time() - start
    logger.info(f"RAGAS job completed in {elapsed:.1f}s — {len(all_results)} scores written")


if __name__ == "__main__":
    run_ragas_job()
