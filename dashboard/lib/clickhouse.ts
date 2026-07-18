/**
 * ClickHouse Client Singleton
 *
 * Uses the official @clickhouse/client package.
 * The singleton pattern reuses the HTTP connection pool
 * across all queries — creating a new connection per query
 * is expensive.
 */

import { createClient, type ClickHouseClient } from "@clickhouse/client";

let client: ClickHouseClient | null = null;

export function getClickHouseClient(): ClickHouseClient {
  if (client) return client;

  const url = process.env.CLICKHOUSE_URL || "http://localhost:8123";
  const user = process.env.CLICKHOUSE_USER || "admin";
  const password = process.env.CLICKHOUSE_PASSWORD || "changeme";
  const database = process.env.CLICKHOUSE_DATABASE || "otel";

  client = createClient({
    url,
    username: user,
    password,
    database,
  });

  return client;
}

/**
 * Helper: run a query and return parsed rows.
 */
export async function queryClickHouse<T = Record<string, unknown>>(
  sql: string,
  params?: Record<string, unknown>
): Promise<T[]> {
  const client = getClickHouseClient();
  const result = await client.query({
    query: sql,
    query_params: params,
    format: "JSONEachRow",
  });
  const text = await result.text();
  return JSON.parse(text) as T[];
}

/**
 * Helper: insert rows into a table.
 */
export async function insertClickHouse(
  table: string,
  rows: Record<string, unknown>[]
): Promise<void> {
  const client = getClickHouseClient();
  await client.insert({
    table,
    values: rows,
    format: "JSONEachRow",
  });
}
