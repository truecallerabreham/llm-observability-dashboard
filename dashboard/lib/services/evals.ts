/**
 * Evals Service
 *
 * Queries ClickHouse for eval score data:
 * - Faithfulness trend
 * - Toxicity breakdown
 * - Model comparison
 */

import { queryClickHouse } from "@/lib/clickhouse";

export interface EvalScore {
  day: string;
  model: string;
  metric: string;
  avg_score: number;
  eval_count: number;
}

/**
 * Get faithfulness trend over time (last 30 days).
 */
export async function getFaithfulnessTrend(): Promise<EvalScore[]> {
  return queryClickHouse<EvalScore>(`
    SELECT
      formatDateTime(day, '%Y-%m-%d') AS day,
      EvaluatedModel AS model,
      MetricName AS metric,
      avg_score,
      eval_count
    FROM eval_scores_mv
    WHERE MetricName = 'faithfulness'
      AND day >= today() - INTERVAL 30 DAY
    GROUP BY day, EvaluatedModel, MetricName, avg_score, eval_count
    ORDER BY day
  `);
}

/**
 * Get toxicity breakdown by category.
 */
export async function getToxicityBreakdown(): Promise<{ category: string; score: number }[]> {
  return queryClickHouse<{ category: string; score: number }>(`
    SELECT
      MetricName AS category,
      avg(Score) AS score
    FROM eval_spans
    WHERE MetricName LIKE 'toxicity_%'
      AND EvaluatedAt >= now() - INTERVAL 30 DAY
    GROUP BY MetricName
    ORDER BY score DESC
  `);
}

/**
 * Get model comparison table.
 */
export async function getModelComparison(): Promise<{
  model: string;
  faithfulness: number;
  toxicity: number;
  answer_relevancy: number;
  eval_count: number;
}[]> {
  return queryClickHouse(`
    SELECT
      EvaluatedModel AS model,
      avgIf(Score, MetricName = 'faithfulness') AS faithfulness,
      avgIf(Score, MetricName = 'toxicity') AS toxicity,
      avgIf(Score, MetricName = 'answer_relevancy') AS answer_relevancy,
      count() AS eval_count
    FROM eval_spans
    WHERE EvaluatedAt >= now() - INTERVAL 30 DAY
    GROUP BY EvaluatedModel
    ORDER BY faithfulness DESC
  `);
}

/**
 * Get total eval count.
 */
export async function getTotalEvals(): Promise<number> {
  const rows = await queryClickHouse<{ count: number }>(`
    SELECT count() AS count FROM eval_spans
    WHERE EvaluatedAt >= now() - INTERVAL 24 HOUR
  `);
  return rows[0]?.count ?? 0;
}
