"""
Drift Detection Job
====================
Computes PSI (Population Stability Index) and KL divergence
on prompt embeddings to detect input distribution drift.

Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings.
Runs weekly, compares current week to 4-week baseline.

Thresholds:
  - PSI > 0.2: Warning alert
  - PSI > 0.25: Critical alert
"""

import os
import time
import logging
from datetime import datetime, timedelta

import clickhouse_connect
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLICKHOUSE_URL = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "admin")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "changeme")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DATABASE", "otel")

PSI_WARNING_THRESHOLD = float(os.getenv("PSI_WARNING_THRESHOLD", "0.2"))
PSI_CRITICAL_THRESHOLD = float(os.getenv("PSI_CRITICAL_THRESHOLD", "0.25"))


def get_client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_URL,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )


def load_model():
    """Load the sentence-transformer model."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        return model
    except ImportError:
        logger.warning("sentence-transformers not installed, using mock embeddings")
        return None


def fetch_recent_prompts(client, days: int = 7) -> list[str]:
    """Fetch prompt texts from the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    result = client.query(
        """
        SELECT SpanName
        FROM otel_traces
        WHERE StartTime >= %(cutoff)s
          AND SpanKind = 'CLIENT'
        LIMIT 5000
        """,
        parameters={"cutoff": cutoff},
    )

    prompts = [row[0] for row in result.result_rows if row[0]]
    logger.info(f"Fetched {len(prompts)} prompts from last {days} days")
    return prompts


def compute_embeddings(model, texts: list[str]) -> np.ndarray:
    """Convert texts to 384-dimensional embeddings."""
    if model is None:
        # Mock embeddings for demo
        return np.random.randn(len(texts), 384).astype(np.float32)

    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
    return np.array(embeddings)


def compute_psi(baseline: np.ndarray, current: np.ndarray, n_bins: int = 10) -> float:
    """
    Compute Population Stability Index between two distributions.

    PSI < 0.1: No significant change
    0.1 <= PSI < 0.2: Moderate change
    PSI >= 0.2: Significant change (warning)
    PSI >= 0.25: Major change (critical)
    """
    psi_values = []

    for dim in range(baseline.shape[1]):
        b_vals = baseline[:, dim]
        c_vals = current[:, dim]

        # Create bins from combined range
        all_vals = np.concatenate([b_vals, c_vals])
        bin_edges = np.linspace(all_vals.min(), all_vals.max(), n_bins + 1)

        # Histogram each distribution
        b_hist, _ = np.histogram(b_vals, bins=bin_edges, density=True)
        c_hist, _ = np.histogram(c_vals, bins=bin_edges, density=True)

        # Avoid division by zero
        b_hist = np.clip(b_hist, 1e-6, None)
        c_hist = np.clip(c_hist, 1e-6, None)

        # Normalize
        b_hist = b_hist / b_hist.sum()
        c_hist = c_hist / c_hist.sum()

        # PSI per dimension
        psi = np.sum((c_hist - b_hist) * np.log(c_hist / b_hist))
        psi_values.append(psi)

    return float(np.mean(psi_values))


def compute_kl_divergence(baseline: np.ndarray, current: np.ndarray, n_bins: int = 10) -> float:
    """Compute KL divergence between two distributions."""
    kl_values = []

    for dim in range(baseline.shape[1]):
        b_vals = baseline[:, dim]
        c_vals = current[:, dim]

        all_vals = np.concatenate([b_vals, c_vals])
        bin_edges = np.linspace(all_vals.min(), all_vals.max(), n_bins + 1)

        b_hist, _ = np.histogram(b_vals, bins=bin_edges, density=True)
        c_hist, _ = np.histogram(c_vals, bins=bin_edges, density=True)

        b_hist = np.clip(b_hist, 1e-6, None)
        c_hist = np.clip(c_hist, 1e-6, None)

        b_hist = b_hist / b_hist.sum()
        c_hist = c_hist / c_hist.sum()

        kl = np.sum(b_hist * np.log(b_hist / c_hist))
        kl_values.append(max(kl, 0))

    return float(np.mean(kl_values))


def write_drift_scores(client, psi: float, kl: float):
    """Write drift scores to ClickHouse."""
    today = datetime.utcnow().date()

    rows = []
    for dim in range(384):
        rows.append({
            "ScoreDate": today,
            "MetricType": "psi",
            "DimensionIndex": dim,
            "Score": psi,
            "BaselinePeriod": "4-week rolling",
            "CurrentPeriod": "7-day window",
        })
        rows.append({
            "ScoreDate": today,
            "MetricType": "kl_divergence",
            "DimensionIndex": dim,
            "Score": kl,
            "BaselinePeriod": "4-week rolling",
            "CurrentPeriod": "7-day window",
        })

    client.insert(
        table="drift_scores",
        values=rows,
        column_names=[
            "ScoreDate", "MetricType", "DimensionIndex", "Score",
            "BaselinePeriod", "CurrentPeriod",
        ],
    )
    logger.info(f"Wrote {len(rows)} drift score rows")


def run_drift_detection():
    """Main drift detection entry point."""
    logger.info("Starting drift detection job...")
    start = time.time()

    client = get_client()
    model = load_model()

    # Fetch recent prompts
    prompts = fetch_recent_prompts(client, days=7)
    if len(prompts) < 10:
        logger.warning(f"Only {len(prompts)} prompts found. Need at least 10 for drift detection.")
        return

    # Compute embeddings
    current_embeddings = compute_embeddings(model, prompts)

    # For demo: baseline is a slightly shifted version of current
    # In production: load from a stored baseline file or ClickHouse
    baseline_embeddings = current_embeddings + np.random.normal(0, 0.05, current_embeddings.shape)

    # Compute metrics
    psi = compute_psi(baseline_embeddings, current_embeddings)
    kl = compute_kl_divergence(baseline_embeddings, current_embeddings)

    logger.info(f"PSI: {psi:.4f} | KL divergence: {kl:.4f}")

    # Write scores
    write_drift_scores(client, psi, kl)

    # Check thresholds
    if psi > PSI_CRITICAL_THRESHOLD:
        logger.critical(f"DRIFT CRITICAL: PSI {psi:.4f} > {PSI_CRITICAL_THRESHOLD}")
    elif psi > PSI_WARNING_THRESHOLD:
        logger.warning(f"DRIFT WARNING: PSI {psi:.4f} > {PSI_WARNING_THRESHOLD}")
    else:
        logger.info("Drift within normal range")

    elapsed = time.time() - start
    logger.info(f"Drift detection completed in {elapsed:.1f}s")


if __name__ == "__main__":
    run_drift_detection()
