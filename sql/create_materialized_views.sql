-- ============================================================
-- ClickHouse: Materialized Views for Dashboard Performance
-- ============================================================
-- Materialized views pre-compute aggregations so the dashboard
-- doesn't recalculate from raw data every time.
--
-- Why SummingMergeTree? It automatically sums numeric columns
-- when rows with the same ORDER BY key merge. Perfect for
-- counters (count, sum, p95 approximation).

-- ============================================================
-- 1. Spans Per Second + Latency + Cost (per minute per model)
-- ============================================================
-- This view powers the Overview page KPI cards and time-series charts.
-- It aggregates every minute: span count, p95 latency, total cost.

CREATE MATERIALIZED VIEW IF NOT EXISTS spans_per_min_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(minute)
ORDER BY (minute, Provider, Model)
AS
SELECT
    toStartOfMinute(StartTime)        AS minute,
    Provider,
    Model,
    count()                           AS span_count,
    sum(InputTokens)                  AS total_input_tokens,
    sum(OutputTokens)                 AS total_output_tokens,
    sum(TotalTokens)                  AS total_tokens,
    sum(CostUsd)                      AS total_cost,
    quantile(0.95)(DurationMs)        AS p95_latency_ms,
    countIf(StatusCode = 'ERROR')     AS error_count
FROM otel_traces
GROUP BY minute, Provider, Model;

-- ============================================================
-- 2. Hourly aggregates for longer time ranges
-- ============================================================
-- Powers the Overview page when viewing 24h+ time ranges.
-- Coarser granularity = faster queries over larger windows.

CREATE MATERIALIZED VIEW IF NOT EXISTS spans_per_hour_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, Provider, Model)
AS
SELECT
    toStartOfHour(StartTime)          AS hour,
    Provider,
    Model,
    count()                           AS span_count,
    sum(InputTokens)                  AS total_input_tokens,
    sum(OutputTokens)                 AS total_output_tokens,
    sum(TotalTokens)                  AS total_tokens,
    sum(CostUsd)                      AS total_cost,
    quantile(0.95)(DurationMs)        AS p95_latency_ms,
    countIf(StatusCode = 'ERROR')     AS error_count
FROM otel_traces
GROUP BY hour, Provider, Model;

-- ============================================================
-- 3. Eval score aggregates (per model per metric)
-- ============================================================
-- Powers the Evals page: faithfulness trend, model comparison.

CREATE MATERIALIZED VIEW IF NOT EXISTS eval_scores_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, EvaluatedModel, MetricName)
AS
SELECT
    toDate(EvaluatedAt)               AS day,
    EvaluatedModel,
    MetricName,
    count()                           AS eval_count,
    sum(Score)                        AS total_score,
    avg(Score)                        AS avg_score,
    min(Score)                        AS min_score,
    max(Score)                        AS max_score
FROM eval_spans
GROUP BY day, EvaluatedModel, MetricName;

-- ============================================================
-- 4. Drift scores table (PSI + KL divergence over time)
-- ============================================================
-- The drift detector job writes PSI scores here.
-- The Drift page reads from this table.

CREATE TABLE IF NOT EXISTS drift_scores
(
    ScoreDate       Date,
    MetricType      LowCardinality(String),   -- psi, kl_divergence
    DimensionIndex  UInt16,                    -- Which embedding dimension
    Score           Float64,
    BaselinePeriod  String,                    -- e.g., "2026-06-01 to 2026-06-28"
    CurrentPeriod   String,                    -- e.g., "2026-06-29 to 2026-07-05"
    InsertedAt      DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(ScoreDate)
ORDER BY (ScoreDate, MetricType, DimensionIndex)
TTL ScoreDate + INTERVAL 365 DAY;

-- ============================================================
-- 5. Alert history table
-- ============================================================
-- The dashboard reads alert history from Alertmanager, but we
-- also store a local copy for historical queries.

CREATE TABLE IF NOT EXISTS alert_history
(
    AlertName       LowCardinality(String),
    Severity        LowCardinality(String),   -- warning, critical
    Status          LowCardinality(String),   -- firing, resolved
    Description     String,
    FiredAt         DateTime,
    ResolvedAt      Nullable(DateTime),
    InsertedAt      DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(FiredAt)
ORDER BY (FiredAt, AlertName)
TTL FiredAt + INTERVAL 180 DAY;

-- ============================================================
-- 6. Triage queue for PII-flagged responses
-- ============================================================
-- The PII judge writes high-score responses here.
-- The dashboard shows these for manual review.

CREATE TABLE IF NOT EXISTS pii_triage_queue
(
    TraceId         String,
    Score           Float64,
    DetectedItems   String,           -- JSON array of detected PII items
    ResponseText    String,
    EvaluatedAt     DateTime,
    Resolved        UInt8 DEFAULT 0,  -- 0 = pending, 1 = resolved
    InsertedAt      DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(EvaluatedAt)
ORDER BY (EvaluatedAt, TraceId)
TTL EvaluatedAt + INTERVAL 90 DAY;
