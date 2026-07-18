/**
 * Traces Service
 *
 * Queries ClickHouse for trace search and waterfall data.
 */

import { queryClickHouse } from "@/lib/clickhouse";

export interface Trace {
  TraceId: string;
  SpanId: string;
  ParentSpanId: string;
  ServiceName: string;
  SpanName: string;
  SpanKind: string;
  StatusCode: string;
  Provider: string;
  Model: string;
  InputTokens: number;
  OutputTokens: number;
  DurationMs: number;
  StartTime: string;
}

export interface TraceWaterfall extends Trace {
  depth: number;
  children: TraceWaterfall[];
}

/**
 * Search traces with filters.
 */
export async function searchTraces(params: {
  model?: string;
  provider?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<Trace[]> {
  const { model, provider, status, limit = 50, offset = 0 } = params;

  const conditions: string[] = [];
  const query_params: Record<string, unknown> = {};

  if (model) {
    conditions.push("Model = %(model)s");
    query_params.model = model;
  }
  if (provider) {
    conditions.push("Provider = %(provider)s");
    query_params.provider = provider;
  }
  if (status) {
    conditions.push("StatusCode = %(status)s");
    query_params.status = status;
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  return queryClickHouse<Trace>(`
    SELECT
      TraceId, SpanId, ParentSpanId, ServiceName, SpanName,
      SpanKind, StatusCode, Provider, Model,
      InputTokens, OutputTokens, DurationMs,
      formatDateTime(StartTime, '%Y-%m-%d %H:%M:%S') AS StartTime
    FROM otel_traces
    ${whereClause}
    ORDER BY StartTime DESC
    LIMIT ${limit} OFFSET ${offset}
  `, query_params);
}

/**
 * Get a single trace's waterfall (all spans for a trace_id).
 */
export async function getTraceWaterfall(traceId: string): Promise<Trace[]> {
  return queryClickHouse<Trace>(`
    SELECT
      TraceId, SpanId, ParentSpanId, ServiceName, SpanName,
      SpanKind, StatusCode, Provider, Model,
      InputTokens, OutputTokens, DurationMs,
      formatDateTime(StartTime, '%Y-%m-%d %H:%M:%S') AS StartTime
    FROM otel_traces
    WHERE TraceId = %(traceId)s
    ORDER BY StartTime
  `, { traceId });
}

/**
 * Get available models for filter dropdown.
 */
export async function getAvailableModels(): Promise<string[]> {
  const rows = await queryClickHouse<{ Model: string }>(`
    SELECT DISTINCT Model FROM otel_traces ORDER BY Model
  `);
  return rows.map((r) => r.Model);
}

/**
 * Get available providers for filter dropdown.
 */
export async function getAvailableProviders(): Promise<string[]> {
  const rows = await queryClickHouse<{ Provider: string }>(`
    SELECT DISTINCT Provider FROM otel_traces ORDER BY Provider
  `);
  return rows.map((r) => r.Provider);
}
