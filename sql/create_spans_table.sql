-- ============================================================
-- ClickHouse: Spans Table
-- ============================================================
-- This table stores OpenTelemetry GenAI semantic convention spans.
-- The OTel ClickHouse exporter auto-creates a basic schema, but
-- we override it with LLM-specific columns for better analytics.
--
-- Why MergeTree? It's ClickHouse's default engine — fast inserts,
-- fast queries, no overhead. We don't need ReplacingMergeTree
-- here because spans are append-only (never updated).
--
-- Why partition by toYYYYMM? Monthly partitions keep the hot/cold
-- data boundary manageable. Queries over recent data only scan
-- the current partition.

CREATE TABLE IF NOT EXISTS otel_traces
(
    -- Trace identification
    TraceId          String,
    SpanId           String,
    ParentSpanId     String,

    -- Span metadata
    ServiceName      LowCardinality(String),
    SpanName         String,
    SpanKind         LowCardinality(String),   -- CLIENT, SERVER, INTERNAL, etc.
    StatusCode       LowCardinality(String),   -- OK, ERROR, UNSET
    StatusMessage    String,

    -- GenAI semantic convention attributes
    Provider         LowCardinality(String),   -- openai, anthropic, gcp.gen_ai, langchain, etc.
    Model            LowCardinality(String),   -- gpt-4o, claude-3.5-sonnet, gemini-1.5-flash, etc.
    OperationName    LowCardinality(String),   -- chat, completion, embed, etc.
    InputTokens      UInt32,
    OutputTokens     UInt32,
    TotalTokens      UInt32,
    ResponseId       String,
    UserId           String,
    AppId            LowCardinality(String),
    ConversationId   String,

    -- Timing
    StartTime        DateTime64(3),
    EndTime          DateTime64(3),
    DurationMs       Float64,

    -- Cost attribution (computed from model_pricing table)
    CostUsd          Float64 DEFAULT 0,

    -- Raw attributes (JSON blob for anything not extracted above)
    Attributes       String DEFAULT '{}',

    -- Ingestion metadata
    InsertedAt       DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(StartTime)
ORDER BY (Provider, Model, StartTime, TraceId)
TTL StartTime + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- ============================================================
-- Bloom Filter Indexes
-- ============================================================
-- Bloom filters speed up point lookups on high-cardinality
-- columns. They're probabilistic (may have false positives)
-- but never false negatives — perfect for WHERE clauses like
-- `WHERE UserId = 'user-123'`.

ALTER TABLE otel_traces ADD INDEX idx_user_id (UserId) TYPE bloom_filter GRANULARITY 4;
ALTER TABLE otel_traces ADD INDEX idx_app_id (AppId) TYPE bloom_filter GRANULARITY 4;
ALTER TABLE otel_traces ADD INDEX idx_model (Model) TYPE bloom_filter GRANULARITY 4;
ALTER TABLE otel_traces ADD INDEX idx_conversation_id (ConversationId) TYPE bloom_filter GRANULARITY 4;
ALTER TABLE otel_traces ADD INDEX idx_provider (Provider) TYPE bloom_filter GRANULARITY 4;
