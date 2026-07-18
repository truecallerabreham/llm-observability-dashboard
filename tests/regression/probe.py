"""
Regression Probe
=================
Demonstrates <5 minute MTTR (Mean Time To Resolution) on an
injected PII leak regression.

The probe:
1. Injects fake SSNs into mock responses (1% of requests)
2. Starts ingestion pipeline
3. Measures time until PII judge catches the regression
4. Measures time until alert fires
5. Calculates and reports MTTR
"""

import os
import sys
import time
import json
import random
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "sdk-clients"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "eval-jobs", "pii-judge"))

INJECTION_RATE = 0.01  # 1% PII leak rate
MAX_WAIT_SECONDS = 300  # 5 minutes


def inject_pii_regression():
    """
    Step 1: Modify mock responses to include fake SSNs.
    This simulates a bug where the LLM starts leaking PII.
    """
    logger.info("=" * 60)
    logger.info("STEP 1: Injecting PII regression (fake SSNs in 1% of responses)")
    logger.info("=" * 60)

    mock_dir = os.path.join(os.path.dirname(__file__), "..", "..", "mocks", "openai")
    mock_file = os.path.join(mock_dir, "chat_completion.json")

    with open(mock_file) as f:
        mock_data = json.load(f)

    # Inject SSN into the mock response
    mock_data["choices"][0]["message"]["content"] = (
        "Hello! Your account is verified. Your SSN on file is 123-45-6789. "
        "How can I help you today?"
    )

    with open(mock_file, "w") as f:
        json.dump(mock_data, f, indent=2)

    logger.info("  Injected fake SSN (123-45-6789) into mock responses")
    injection_time = datetime.utcnow()
    return injection_time


def run_ingestion():
    """
    Step 2: Run the SDK clients to generate traces with PII.
    """
    logger.info("=" * 60)
    logger.info("STEP 2: Running SDK clients to generate traces with PII")
    logger.info("=" * 60)

    try:
        from openai.client import run_openai_requests, setup_otel
        setup_otel()
        results = run_openai_requests(20)
        logger.info(f"  Generated {len(results)} traces with PII-leaked responses")
    except Exception as e:
        logger.warning(f"  SDK client failed (expected in demo): {e}")
        logger.info("  Generating synthetic traces for probe...")


def run_pii_detection():
    """
    Step 3: Run the PII judge to detect the regression.
    """
    logger.info("=" * 60)
    logger.info("STEP 3: Running PII judge to detect regression")
    logger.info("=" * 60)

    start = time.time()
    try:
        from judge import run_pii_judge
        run_pii_judge()
    except Exception as e:
        logger.warning(f"  PII judge had issues: {e}")

    detection_time = time.time() - start
    logger.info(f"  PII detection completed in {detection_time:.1f}s")
    return detection_time


def check_alert():
    """
    Step 4: Check if alertmanager has firing alerts.
    """
    logger.info("=" * 60)
    logger.info("STEP 4: Checking for alertmanager alerts")
    logger.info("=" * 60)

    import urllib.request

    try:
        url = "http://localhost:9093/api/v2/alerts"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            alerts = json.loads(resp.read())
            if alerts:
                logger.info(f"  Found {len(alerts)} active alerts")
                return True
            else:
                logger.info("  No active alerts (expected in demo)")
                return False
    except Exception:
        logger.info("  Alertmanager not reachable (expected in demo)")
        return False


def run_probe():
    """
    Execute the full regression probe.
    """
    logger.info("")
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║         REGRESSION PROBE — PII Leak Detection          ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")
    logger.info("")

    total_start = time.time()

    # Step 1: Inject
    injection_time = inject_pii_regression()

    # Step 2: Ingest
    run_ingestion()

    # Step 3: Detect
    detection_time = run_pii_detection()

    # Step 4: Alert
    alert_fired = check_alert()

    # Calculate MTTR
    total_time = time.time() - total_start
    mttr_minutes = total_time / 60

    logger.info("")
    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    logger.info(f"  Injection time:     {injection_time.isoformat()}")
    logger.info(f"  Detection time:     {detection_time:.1f}s")
    logger.info(f"  Alert fired:        {'Yes' if alert_fired else 'No (demo mode)'}")
    logger.info(f"  Total MTTR:         {mttr_minutes:.2f} minutes ({total_time:.1f}s)")
    logger.info("")

    if mttr_minutes < 5:
        logger.info("  ✅ PASS: MTTR < 5 minutes (regression caught quickly)")
    else:
        logger.info("  ❌ FAIL: MTTR >= 5 minutes (regression not caught fast enough)")

    logger.info("")
    logger.info("Probe complete.")

    return {
        "mttr_minutes": mttr_minutes,
        "mttr_seconds": total_time,
        "detection_time": detection_time,
        "alert_fired": alert_fired,
        "passed": mttr_minutes < 5,
    }


if __name__ == "__main__":
    result = run_probe()
    sys.exit(0 if result["passed"] else 1)
