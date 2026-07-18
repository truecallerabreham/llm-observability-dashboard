/**
 * Prometheus Metrics Endpoint
 *
 * Exposes eval scores and latency as Prometheus exposition format.
 * Prometheus scrapes this endpoint every 15s.
 *
 * GET /api/metrics → text/plain (Prometheus format)
 */

import { NextResponse } from "next/server";
import { queryClickHouse } from "@/lib/clickhouse";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    // Query current eval scores
    const evalScores = await queryClickHouse<{
      model: string;
      metric: string;
      avg_score: number;
    }>(`
      SELECT
        EvaluatedModel AS model,
        MetricName AS metric,
        avg(Score) AS avg_score
      FROM eval_spans
      WHERE EvaluatedAt >= now() - INTERVAL 1 HOUR
      GROUP BY EvaluatedModel, MetricName
    `);

    // Query latency percentiles
    const latency = await queryClickHouse<{
      model: string;
      p50: number;
      p95: number;
      p99: number;
    }>(`
      SELECT
        Model AS model,
        quantile(0.50)(DurationMs) / 1000 AS p50,
        quantile(0.95)(DurationMs) / 1000 AS p95,
        quantile(0.99)(DurationMs) / 1000 AS p99
      FROM otel_traces
      WHERE StartTime >= now() - INTERVAL 1 HOUR
      GROUP BY Model
    `);

    // Query span count
    const spanCount = await queryClickHouse<{ count: number }>(`
      SELECT count() AS count
      FROM otel_traces
      WHERE StartTime >= now() - INTERVAL 1 HOUR
    `);

    // Build Prometheus text format
    const lines: string[] = [];

    lines.push("# HELP llm_eval_score Eval score from LLM evaluation");
    lines.push("# TYPE llm_eval_score gauge");
    for (const row of evalScores) {
      lines.push(
        `llm_eval_score{model="${row.model}",metric="${row.metric}"} ${row.avg_score}`
      );
    }

    lines.push("");
    lines.push("# HELP llm_request_duration_seconds Request duration in seconds");
    lines.push("# TYPE llm_request_duration_seconds histogram");
    for (const row of latency) {
      lines.push(
        `llm_request_duration_seconds_bucket{model="${row.model}",le="0.5"} ${row.p50}`
      );
      lines.push(
        `llm_request_duration_seconds_bucket{model="${row.model}",le="2.0"} ${row.p95}`
      );
      lines.push(
        `llm_request_duration_seconds_bucket{model="${row.model}",le="5.0"} ${row.p99}`
      );
    }

    lines.push("");
    lines.push("# HELP llm_spans_total Total number of spans");
    lines.push("# TYPE llm_spans_total counter");
    lines.push(`llm_spans_total ${spanCount[0]?.count ?? 0}`);

    return new NextResponse(lines.join("\n"), {
      status: 200,
      headers: {
        "Content-Type": "text/plain; version=0.0.4; charset=utf-8",
      },
    });
  } catch (error) {
    // Return empty metrics on error (Prometheus expects 200)
    return new NextResponse("# No data available\n", {
      status: 200,
      headers: {
        "Content-Type": "text/plain; version=0.0.4; charset=utf-8",
      },
    });
  }
}
