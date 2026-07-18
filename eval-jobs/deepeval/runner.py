"""
DeepEval Batch Eval Job
========================
Reads sampled traces from ClickHouse, runs DeepEval metrics,
and writes eval scores back as eval_spans.

Runs every 15 minutes via cron or Docker Compose.

Metrics evaluated:
  - Faithfulness: Is the response grounded in context?
  - Toxicity: Does the response contain harmful content?
  - Answer Relevancy: Does the response address the question?
"""

import os
import time
import random
import logging
from datetime import datetime, timedelta

import clickhouse_connect
from deepeval import evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    ToxicityMetric,
    AnswerRelevancyMetric,
)
from deepeval.test_case import LLMTestCase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# Configuration
# ============================================================

CLICKHOUSE_URL = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "admin")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "changeme")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DATABASE", "otel")

SAMPLE_RATE = float(os.getenv("EVAL_SAMPLE_RATE", "0.15"))  # 15% sampling
LOOKBACK_MINUTES = int(os.getenv("EVAL_LOOKBACK_MINUTES", "15"))


def get_clickhouse_client():
    """Create a ClickHouse client."""
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_URL,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )


def fetch_recent_traces(client, limit: int = 100) -> list[dict]:
    """Fetch traces from the last N minutes, sampled at SAMPLE_RATE."""
    cutoff = datetime.utcnow() - timedelta(minutes=LOOKBACK_MINUTES)

    result = client.query(
        """
        SELECT
            TraceId, SpanId, ServiceName, SpanName,
            Provider, Model, InputTokens, OutputTokens,
            DurationMs, formatDateTime(StartTime, '%Y-%m-%d %H:%M:%S') AS StartTime
        FROM otel_traces
        WHERE StartTime >= %(cutoff)s
          AND SpanKind = 'CLIENT'
        ORDER BY StartTime DESC
        LIMIT %(limit)s
        """,
        parameters={"cutoff": cutoff, "limit": limit},
    )

    traces = []
    for row in result.result_rows:
        # Apply sampling
        if random.random() < SAMPLE_RATE:
            traces.append({
                "trace_id": row[0],
                "span_id": row[1],
                "service_name": row[2],
                "span_name": row[3],
                "provider": row[4],
                "model": row[5],
                "input_tokens": row[6],
                "output_tokens": row[7],
                "duration_ms": row[8],
                "start_time": row[9],
            })

    logger.info(f"Fetched {len(traces)} sampled traces from last {LOOKBACK_MINUTES} minutes")
    return traces


def evaluate_trace(trace: dict) -> list[dict]:
    """Run DeepEval metrics on a single trace."""
    eval_results = []

    # For demo: generate synthetic eval scores
    # In production, you'd use real LLM-as-judge with actual context/response
    test_case = LLMTestCase(
        input=f"User query about {trace['service_name']}",
        actual_output=f"Response from {trace['model']} ({trace['output_tokens']} tokens)",
        expected_output="Expected helpful response",
        context=["Context from knowledge base"],
    )

    metrics = [
        ("faithfulness", FaithfulnessMetric(threshold=0.7)),
        ("toxicity", ToxicityMetric(threshold=0.5)),
        ("answer_relevancy", AnswerRelevancyMetric(threshold=0.7)),
    ]

    for metric_name, metric in metrics:
        try:
            metric.measure(test_case)
            score = metric.score
            reason = metric.reason or f"{metric_name} evaluation"

            eval_results.append({
                "trace_id": trace["trace_id"],
                "span_id": trace["span_id"],
                "metric_name": metric_name,
                "score": score,
                "reason": reason,
                "model_used": "gpt-4o",
                "evaluated_provider": trace["provider"],
                "evaluated_model": trace["model"],
                "evaluated_at": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.warning(f"Metric {metric_name} failed for trace {trace['trace_id']}: {e}")

    return eval_results


def write_eval_spans(client, eval_results: list[dict]):
    """Insert eval results into the eval_spans table."""
    if not eval_results:
        logger.info("No eval results to write")
        return

    client.insert(
        table="eval_spans",
        values=eval_results,
        column_names=[
            "TraceId", "SpanId", "MetricName", "Score", "Reason",
            "ModelUsed", "EvaluatedProvider", "EvaluatedModel", "EvaluatedAt",
        ],
    )
    logger.info(f"Wrote {len(eval_results)} eval spans to ClickHouse")


def run_eval_job():
    """Main eval job entry point."""
    logger.info("Starting DeepEval batch job...")
    start_time = time.time()

    client = get_clickhouse_client()
    traces = fetch_recent_traces(client)

    if not traces:
        logger.info("No traces found. Skipping eval.")
        return

    all_eval_results = []
    for trace in traces:
        results = evaluate_trace(trace)
        all_eval_results.extend(results)

    write_eval_spans(client, all_eval_results)

    elapsed = time.time() - start_time
    logger.info(f"Eval job completed in {elapsed:.1f}s — {len(all_eval_results)} scores written")


if __name__ == "__main__":
    run_eval_job()
