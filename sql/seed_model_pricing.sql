-- ============================================================
-- ClickHouse: Model Pricing Table
-- ============================================================
-- Used to compute per-span cost from token counts.
-- Prices are 2026 estimates and should be updated quarterly.

CREATE TABLE IF NOT EXISTS model_pricing
(
    ModelName       LowCardinality(String),
    Provider        LowCardinality(String),
    InputCostPer1kTokens   Float64,
    OutputCostPer1kTokens  Float64,
    Currency        LowCardinality(String) DEFAULT 'USD',
    UpdatedAt       DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(UpdatedAt)
ORDER BY (Provider, ModelName);

INSERT INTO model_pricing (ModelName, Provider, InputCostPer1kTokens, OutputCostPer1kTokens) VALUES
('gpt-4o', 'openai', 0.00250, 0.01000),
('gpt-4o-mini', 'openai', 0.00015, 0.00060),
('gpt-4-turbo', 'openai', 0.01000, 0.03000),
('gpt-3.5-turbo', 'openai', 0.00050, 0.00150),
('o1', 'openai', 0.01500, 0.06000),
('o1-mini', 'openai', 0.00300, 0.01200),
('claude-3.5-sonnet', 'anthropic', 0.00300, 0.01500),
('claude-3.5-haiku', 'anthropic', 0.00025, 0.00125),
('claude-3-opus', 'anthropic', 0.01500, 0.07500),
('claude-3-sonnet', 'anthropic', 0.00300, 0.01500),
('claude-3-haiku', 'anthropic', 0.00025, 0.00125),
('gemini-1.5-pro', 'gcp.gen_ai', 0.00125, 0.00500),
('gemini-1.5-flash', 'gcp.gen_ai', 0.000075, 0.00030),
('gemini-2.0-flash', 'gcp.gen_ai', 0.00010, 0.00040),
('gemini-2.5-pro', 'gcp.gen_ai', 0.00125, 0.01000),
('gemini-2.5-flash', 'gcp.gen_ai', 0.00015, 0.00060),
('llama-3.1-8b', 'vllm', 0.00000, 0.00000),
('llama-3.1-70b', 'vllm', 0.00000, 0.00000),
('llama-3.1-405b', 'vllm', 0.00000, 0.00000),
('mixtral-8x7b', 'vllm', 0.00000, 0.00000);
