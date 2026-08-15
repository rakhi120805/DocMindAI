"""
Tests for the Evaluation module. Run with: pytest tests/test_evaluation.py -v

These are the same checks used to verify the metrics during
development - kept here so they run automatically (e.g. in CI) rather
than living only as one-off scratch commands.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.metrics import (
    context_precision, context_recall, token_overlap_score, character_error_rate,
)
from evaluation.hallucination import faithfulness_score, flag_potential_hallucination
from evaluation.latency import compute_latency_stats
from evaluation.benchmark import BenchmarkCase, run_benchmark


def test_context_precision_and_recall():
    retrieved = ["c1", "c2", "c3", "c4", "c5"]
    relevant = {"c1", "c3", "c6", "c7"}
    assert context_precision(retrieved, relevant) == 0.4   # 2 of 5 retrieved were relevant
    assert context_recall(retrieved, relevant) == 0.5      # 2 of 4 relevant were found


def test_token_overlap_score():
    assert token_overlap_score("the total amount is 1200 rupees", "total amount 1200") == 1.0
    assert token_overlap_score("completely unrelated text here", "total amount 1200") == 0.0


def test_character_error_rate():
    assert character_error_rate("Invoice Total 1200", "Invoice Total 1200") == 0.0
    cer = character_error_rate("Invoice T0tal 1200", "Invoice Total 1200")
    assert abs(cer - 1 / 18) < 1e-9  # exactly one substituted character


def test_faithfulness_distinguishes_grounded_from_hallucinated():
    context = ["The invoice total is 1200 rupees dated 15 January 2026."]
    grounded = "The total is 1200 rupees."
    hallucinated = "The total is 50000 rupees paid via cryptocurrency wallet."

    assert faithfulness_score(grounded, context) > faithfulness_score(hallucinated, context)
    assert flag_potential_hallucination(hallucinated, context) is True
    assert flag_potential_hallucination(grounded, context) is False


def test_latency_percentiles_surface_outliers():
    latencies = [100, 120, 110, 105, 5000]  # one slow outlier among fast requests
    stats = compute_latency_stats(latencies)
    assert stats["mean_ms"] == sum(latencies) / 5
    assert stats["p95_ms"] == 5000  # outlier shows up in the tail, not hidden by the mean


def test_benchmark_distinguishes_good_from_bad_answers():
    def fake_query_fn(question):
        if "total" in question.lower():
            return {
                "answer": "The total amount is 1200 rupees.",
                "chunk_ids": ["c1", "c2"],
                "context_texts": ["Invoice total: 1200 rupees, dated 15 Jan 2026."],
                "latency_ms": 250,
            }
        return {
            "answer": "The document was signed by aliens on Mars.",
            "chunk_ids": ["c5"],
            "context_texts": ["This is an employment contract between two parties."],
            "latency_ms": 400,
        }

    cases = [
        BenchmarkCase("q1_total", "What is the total?", "total amount 1200 rupees", {"c1", "c2"}),
        BenchmarkCase("q2_signee", "Who signed the document?", "employer and employee", {"c5", "c6"}),
    ]
    report = run_benchmark(cases, fake_query_fn)
    per_case = {c["case_id"]: c for c in report["per_case"]}

    assert report["case_count"] == 2
    assert per_case["q1_total"]["faithfulness"] > per_case["q2_signee"]["faithfulness"]


if __name__ == "__main__":
    # Allows running `python tests/test_evaluation.py` directly too,
    # without needing pytest installed.
    test_context_precision_and_recall()
    test_token_overlap_score()
    test_character_error_rate()
    test_faithfulness_distinguishes_grounded_from_hallucinated()
    test_latency_percentiles_surface_outliers()
    test_benchmark_distinguishes_good_from_bad_answers()
    print("All evaluation tests passed.")
