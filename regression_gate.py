# regression_gate.py
# CI/CD-la intha thresholds fail aana deployment block aagum!
# "Quality gate" - bad code production-la pogaama thadukurom

from src.database.db import get_all_traces
from src.monitoring.metrics import get_latency_metrics, get_quality_metrics
import sys

# ─── THRESHOLDS ─── ithuku mela pona fail!
THRESHOLDS = {
    "p95_latency_ms": 10000,  # 10 seconds-ku mela pogakoodathu
    "avg_quality_score": 0.5,  # Quality 0.5-ku keela pogakoodathu
    "citation_rate": 0.7,  # 70% answers-la citation irukanum
    "error_rate": 0.1  # 10%-ku mela errors varakoodathu
}


def run_regression_checks():
    """
    # ella checks run pannu
    # Fail aana exit code 1 return pannum → CI fail aagum
    """

    print("🔍 Running Regression Checks...")
    print("=" * 50)

    traces = get_all_traces()

    if not traces:
        print("⚠️  No traces found - skipping checks")
        return True

    all_passed = True

    # Check 1: p95 Latency
    lat_metrics = get_latency_metrics()
    p95 = lat_metrics.get("total", {}).get("p95", 0)
    threshold = THRESHOLDS["p95_latency_ms"]

    if p95 > threshold:
        print(f"❌ p95 Latency FAIL: {p95:.0f}ms > {threshold}ms")
        all_passed = False
    else:
        print(f"✅ p95 Latency PASS: {p95:.0f}ms ≤ {threshold}ms")

    # Check 2: Quality Score
    quality = get_quality_metrics()
    avg_quality = quality.get("avg_quality_score", 0)
    threshold = THRESHOLDS["avg_quality_score"]

    if avg_quality < threshold:
        print(f"❌ Quality Score FAIL: {avg_quality:.2f} < {threshold}")
        all_passed = False
    else:
        print(f"✅ Quality Score PASS: {avg_quality:.2f} ≥ {threshold}")

    # Check 3: Citation Rate
    citation_rate = quality.get("citation_rate", 0)
    threshold = THRESHOLDS["citation_rate"]

    if citation_rate < threshold:
        print(f"❌ Citation Rate FAIL: {citation_rate:.1%} < {threshold:.1%}")
        all_passed = False
    else:
        print(f"✅ Citation Rate PASS: {citation_rate:.1%} ≥ {threshold:.1%}")

    # Check 4: Error Rate
    error_count = sum(1 for t in traces if t["status"] == "error")
    error_rate = error_count / len(traces)
    threshold = THRESHOLDS["error_rate"]

    if error_rate > threshold:
        print(f"❌ Error Rate FAIL: {error_rate:.1%} > {threshold:.1%}")
        all_passed = False
    else:
        print(f"✅ Error Rate PASS: {error_rate:.1%} ≤ {threshold:.1%}")

    print("=" * 50)

    if all_passed:
        print("🎉 All checks PASSED! Safe to deploy.")
    else:
        print("🚫 Some checks FAILED! Deployment blocked.")

    return all_passed


if __name__ == "__main__":
    passed = run_regression_checks()
    sys.exit(0 if passed else 1)  # CI-la exit code 1 = fail