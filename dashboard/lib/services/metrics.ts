/**
 * Metrics Service
 *
 * Queries ClickHouse for Overview page KPIs:
 * - Spans per second
 * - Cost per user
 * - P95 latency
 * - Time-series data for charts
 */

import { queryClickHouse } from "@/lib/clickhouse";

export interface KPIMetric {
  label: string;
  value: string;
  change: number; // percentage change
  unit: string;
}

export interface TimeSeriesPoint {
  time: string;
  value: number;
}

/**
 * Get current spans per second (last 5 minutes average).
 */
export async function getSpansPerSecond(): Promise<KPIMetric> {
  const rows = await queryClickHouse<{ spans_per_sec: number }>(`
    SELECT
      sum(span_count) / 300 AS spans_per_sec
    FROM spans_per_min_mv
    WHERE minute >= now() - INTERVAL 5 MINUTE
  `);

  const value = rows[0]?.spans_per_sec ?? 0;

  return {
    label: "Spans/sec",
    value: value.toFixed(1),
    change: 0,
    unit: "span/s",
  };
}

/**
 * Get total cost (last hour).
 */
export async function getTotalCost(): Promise<KPIMetric> {
  const rows = await queryClickHouse<{ total_cost: number }>(`
    SELECT sum(CostUsd) AS total_cost
    FROM otel_traces
    WHERE StartTime >= now() - INTERVAL 1 HOUR
  `);

  const value = rows[0]?.total_cost ?? 0;

  return {
    label: "Cost (1h)",
    value: `$${value.toFixed(4)}`,
    change: 0,
    unit: "USD",
  };
}

/**
 * Get P95 latency (last 5 minutes).
 */
export async function getP95Latency(): Promise<KPIMetric> {
  const rows = await queryClickHouse<{ p95_ms: number }>(`
    SELECT quantile(0.95)(DurationMs) AS p95_ms
    FROM otel_traces
    WHERE StartTime >= now() - INTERVAL 5 MINUTE
  `);

  const value = rows[0]?.p95_ms ?? 0;

  return {
    label: "P95 Latency",
    value: `${value.toFixed(0)}`,
    change: 0,
    unit: "ms",
  };
}

/**
 * Get total traces (last hour).
 */
export async function getTotalTraces(): Promise<KPIMetric> {
  const rows = await queryClickHouse<{ count: number }>(`
    SELECT count() AS count
    FROM otel_traces
    WHERE StartTime >= now() - INTERVAL 1 HOUR
  `);

  const value = rows[0]?.count ?? 0;

  return {
    label: "Traces (1h)",
    value: value.toLocaleString(),
    change: 0,
    unit: "traces",
  };
}

/**
 * Get spans per minute time series (last 24 hours).
 */
export async function getSpansTimeSeries(): Promise<TimeSeriesPoint[]> {
  return queryClickHouse<TimeSeriesPoint>(`
    SELECT
      formatDateTime(minute, '%Y-%m-%d %H:%M:%S') AS time,
      sum(span_count) AS value
    FROM spans_per_min_mv
    WHERE minute >= now() - INTERVAL 24 HOUR
    GROUP BY minute
    ORDER BY minute
  `);
}

/**
 * Get latency time series (last 24 hours).
 */
export async function getLatencyTimeSeries(): Promise<TimeSeriesPoint[]> {
  return queryClickHouse<TimeSeriesPoint>(`
    SELECT
      formatDateTime(minute, '%Y-%m-%d %H:%M:%S') AS time,
      p95_latency_ms AS value
    FROM spans_per_min_mv
    WHERE minute >= now() - INTERVAL 24 HOUR
    GROUP BY minute, p95_latency_ms
    ORDER BY minute
  `);
}

/**
 * Get cost by model (last 24 hours).
 */
export async function getCostByModel(): Promise<{ model: string; cost: number }[]> {
  return queryClickHouse<{ model: string; cost: number }>(`
    SELECT
      Model AS model,
      sum(CostUsd) AS cost
    FROM otel_traces
    WHERE StartTime >= now() - INTERVAL 24 HOUR
    GROUP BY Model
    ORDER BY cost DESC
  `);
}

/**
 * Get all KPI metrics in parallel.
 */
export async function getAllKPIMetrics(): Promise<KPIMetric[]> {
  const [spansPerSec, totalCost, p95Latency, totalTraces] = await Promise.all([
    getSpansPerSecond(),
    getTotalCost(),
    getP95Latency(),
    getTotalTraces(),
  ]);

  return [spansPerSec, totalCost, p95Latency, totalTraces];
}
