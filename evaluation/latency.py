"""
Latency Aggregation.

WHY PERCENTILES, NOT JUST AVERAGE (a genuinely important distinction
to be able to explain): average latency can look fine while your
worst-case user experience is terrible. If 95 requests take 500ms and
5 requests take 8 seconds, the AVERAGE is only ~870ms - looks OK - but
5% of your users are having a bad time. p95/p99 latency surfaces that
tail, which is what actually matters for user experience and for
catching problems like "the 10th page of a PDF makes OCR much slower."

Every query's latency is already being recorded in QueryLog
(backend/database/models.py, populated by backend/routers/query.py) -
this module just aggregates that raw data into something you can
report on.
"""

from typing import List, Dict


def compute_latency_stats(latencies_ms: List[int]) -> Dict[str, float]:
    if not latencies_ms:
        return {"count": 0, "mean_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}

    sorted_latencies = sorted(latencies_ms)
    n = len(sorted_latencies)

    return {
        "count": n,
        "mean_ms": sum(sorted_latencies) / n,
        "p50_ms": _percentile(sorted_latencies, 50),
        "p95_ms": _percentile(sorted_latencies, 95),
        "p99_ms": _percentile(sorted_latencies, 99),
    }


def _percentile(sorted_values: List[int], p: float) -> float:
    """
    Nearest-rank percentile. For small sample sizes (a handful of
    test queries) this is simpler and more transparent than
    interpolated percentile methods - worth swapping for numpy's
    interpolated version once you have enough production query volume
    for the difference to matter.
    """
    if not sorted_values:
        return 0.0
    k = max(0, min(len(sorted_values) - 1, int(round(p / 100 * len(sorted_values))) - 1))
    return float(sorted_values[k])
