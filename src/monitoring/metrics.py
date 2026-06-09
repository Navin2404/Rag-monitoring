# src/monitoring/metrics.py
# p50, p95 latency calculate panrom
#
# p50 = 50th percentile = median
#       "50% of requests intha time-la mudiyum"
# p95 = 95th percentile
#       "95% of requests intha time-la mudiyum"
#       "worst case" indicator mathiri

import numpy as np
from src.database.db import get_all_traces


def calculate_percentiles(latencies: list) -> dict:
    """
    # Latency list kudu → p50, p95, p99 return pannum
    #
    # Udharanam:
    # latencies = [100, 200, 150, 500, 120, 800, 110]
    # p50 = 150ms (middle value)
    # p95 = 800ms (worst 5% ithuku mela poguthu)
    """

    if not latencies:
        return {"p50": 0, "p95": 0, "p99": 0, "avg": 0, "min": 0, "max": 0}

    arr = np.array(latencies)

    return {
        "p50": round(float(np.percentile(arr, 50)), 2),  # Median
        "p95": round(float(np.percentile(arr, 95)), 2),  # 95th percentile
        "p99": round(float(np.percentile(arr, 99)), 2),  # 99th percentile
        "avg": round(float(np.mean(arr)), 2),  # Average
        "min": round(float(np.min(arr)), 2),  # Fastest
        "max": round(float(np.max(arr)), 2)  # Slowest
    }


def get_latency_metrics() -> dict:
    """
    # Database-la irukara ella traces-um eduthu
    # Overall + component-wise latency metrics return pannum
    """

    traces = get_all_traces()

    if not traces:
        return {}

    # Different latency types extract pannu
    total_latencies = [t["total_latency_ms"] for t in traces if t["total_latency_ms"]]
    retrieval_latencies = [t["retrieval_latency_ms"] for t in traces if t["retrieval_latency_ms"]]
    generation_latencies = [t["generation_latency_ms"] for t in traces if t["generation_latency_ms"]]

    return {
        "total": calculate_percentiles(total_latencies),
        "retrieval": calculate_percentiles(retrieval_latencies),
        "generation": calculate_percentiles(generation_latencies),
        "sample_size": len(traces)
    }


def get_cost_metrics() -> dict:
    """
    # Total cost, average cost per query calculate panrom
    """
    traces = get_all_traces()

    if not traces:
        return {}

    costs = [t["cost_usd"] for t in traces if t["cost_usd"]]
    total_cost = sum(costs)

    return {
        "total_cost_usd": round(total_cost, 4),
        "avg_cost_per_query": round(total_cost / len(costs), 6) if costs else 0,
        "total_queries": len(traces),
        "estimated_monthly": round(total_cost * 30, 2)  # Rough estimate
    }


def get_quality_metrics() -> dict:
    """
    # Quality scores, citation rate calculate panrom
    """
    traces = get_all_traces()

    if not traces:
        return {}

    quality_scores = [t["quality_score"] for t in traces if t["quality_score"]]
    citation_count = sum(1 for t in traces if t["has_citation"])

    return {
        "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 3) if quality_scores else 0,
        "citation_rate": round(citation_count / len(traces), 3) if traces else 0,
        "total_queries": len(traces)
    }