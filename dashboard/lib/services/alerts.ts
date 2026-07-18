/**
 * Alerts Service
 *
 * Queries Alertmanager API and ClickHouse for alert data.
 */

import { queryClickHouse } from "@/lib/clickhouse";

const ALERTMANAGER_URL = process.env.ALERTMANAGER_URL || "http://localhost:9093";

export interface ActiveAlert {
  name: string;
  severity: string;
  status: string;
  description: string;
  startedAt: string;
}

export interface AlertHistoryEntry {
  name: string;
  severity: string;
  status: string;
  description: string;
  firedAt: string;
  resolvedAt: string | null;
}

/**
 * Get active alerts from Alertmanager.
 */
export async function getActiveAlerts(): Promise<ActiveAlert[]> {
  try {
    const response = await fetch(`${ALERTMANAGER_URL}/api/v2/alerts`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return [];
    }

    const alerts = await response.json();
    return alerts.map((alert: Record<string, unknown>) => ({
      name: (alert.labels as Record<string, string>)?.alertname || "Unknown",
      severity: (alert.labels as Record<string, string>)?.severity || "unknown",
      status: alert.status || "firing",
      description: (alert.annotations as Record<string, string>)?.description || "",
      startedAt: alert.startsAt || new Date().toISOString(),
    }));
  } catch {
    return [];
  }
}

/**
 * Get alert history from ClickHouse.
 */
export async function getAlertHistory(): Promise<AlertHistoryEntry[]> {
  return queryClickHouse<AlertHistoryEntry>(`
    SELECT
      AlertName AS name,
      Severity AS severity,
      Status AS status,
      Description AS description,
      formatDateTime(FiredAt, '%Y-%m-%d %H:%M:%S') AS firedAt,
      formatDateTime(ResolvedAt, '%Y-%m-%d %H:%M:%S') AS resolvedAt
    FROM alert_history
    ORDER BY FiredAt DESC
    LIMIT 100
  `);
}
