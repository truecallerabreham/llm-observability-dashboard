/**
 * Drift Service
 *
 * Queries ClickHouse for PSI and KL divergence data.
 */

import { queryClickHouse } from "@/lib/clickhouse";

export interface DriftScore {
  date: string;
  metric_type: string;
  avg_score: number;
  max_score: number;
}

export interface DriftEvent {
  date: string;
  psi_value: number;
  alert_level: string;
}

/**
 * Get PSI trend over time (last 90 days).
 */
export async function getPSITrend(): Promise<DriftScore[]> {
  return queryClickHouse<DriftScore>(`
    SELECT
      formatDateTime(ScoreDate, '%Y-%m-%d') AS date,
      MetricType AS metric_type,
      avg(Score) AS avg_score,
      max(Score) AS max_score
    FROM drift_scores
    WHERE MetricType = 'psi'
      AND ScoreDate >= today() - INTERVAL 90 DAY
    GROUP BY ScoreDate, MetricType
    ORDER BY ScoreDate
  `);
}

/**
 * Get drift events (PSI > 0.2 threshold breaches).
 */
export async function getDriftEvents(): Promise<DriftEvent[]> {
  return queryClickHouse<DriftEvent>(`
    SELECT
      formatDateTime(ScoreDate, '%Y-%m-%d') AS date,
      avg(Score) AS psi_value,
      CASE
        WHEN avg(Score) > 0.25 THEN 'critical'
        WHEN avg(Score) > 0.2 THEN 'warning'
        ELSE 'normal'
      END AS alert_level
    FROM drift_scores
    WHERE MetricType = 'psi'
      AND ScoreDate >= today() - INTERVAL 90 DAY
    GROUP BY ScoreDate
    HAVING psi_value > 0.2
    ORDER BY ScoreDate DESC
  `);
}

/**
 * Get latest PSI score.
 */
export async function getLatestPSI(): Promise<{ score: number; date: string } | null> {
  const rows = await queryClickHouse<{ score: number; date: string }>(`
    SELECT
      avg(Score) AS score,
      formatDateTime(max(ScoreDate), '%Y-%m-%d') AS date
    FROM drift_scores
    WHERE MetricType = 'psi'
      AND ScoreDate = (SELECT max(ScoreDate) FROM drift_scores WHERE MetricType = 'psi')
  `);
  return rows[0] ?? null;
}
