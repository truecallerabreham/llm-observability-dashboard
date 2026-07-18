-- ============================================================
-- ClickHouse: Eval Spans Table
-- ============================================================
-- Eval spans are linked to their parent trace via trace_id.
-- Each eval produces one row per metric (faithfulness, toxicity, etc.).
--
-- Why ReplacingMergeTree? Re-evaluations may overwrite previous
-- scores for the same trace+metric combination. ReplacingMergeTree
-- deduplicates on (trace_id, metric_name) keeping the latest insert.

CREATE TABLE IF NOT EXISTS eval_spans
(
    -- Link to parent trace
    TraceId          String,
    SpanId           String,
    ParentSpanId     String,

    -- Eval metadata
    MetricName       LowCardinality(String),   -- faithfulness, toxicity, answer_relevancy, pii_leak, etc.
    Score            Float64,                   -- 0.0 to 1.0
    Reason           String,                    -- LLM judge explanation
    ModelUsed        LowCardinality(String),    -- Which model performed the eval

    -- Provider context (which model was being evaluated)
    EvaluatedProvider LowCardinality(String),
    EvaluatedModel   LowCardinality(String),

    -- Timing
    EvaluatedAt      DateTime64(3),

    -- Ingestion metadata
    InsertedAt       DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(InsertedAt)
PARTITION BY toYYYYMM(EvaluatedAt)
ORDER BY (TraceId, MetricName)
TTL EvaluatedAt + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;
