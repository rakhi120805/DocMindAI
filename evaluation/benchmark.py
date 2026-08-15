"""
Benchmark Runner — the thing you'd actually run to get a report.

WHY A SEPARATE "BENCHMARK CASE" FORMAT INSTEAD OF JUST TESTING WHATEVER
DOCUMENTS COME IN: evaluation needs GROUND TRUTH to compare against
(what chunks SHOULD have been retrieved, what the answer SHOULD say).
Real production documents don't come with that label attached. A
benchmark suite is a small, hand-curated set of documents + questions
+ known-correct answers, built once and reused every time you want to
check "did my last change make retrieval better or worse?" This is
the same idea as a test suite in software engineering, applied to
model/pipeline quality instead of code correctness.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Set

from evaluation.metrics import context_precision, context_recall, token_overlap_score
from evaluation.hallucination import faithfulness_score
from evaluation.latency import compute_latency_stats


@dataclass
class BenchmarkCase:
    case_id: str
    question: str
    expected_answer: str
    relevant_chunk_ids: Set[str] = field(default_factory=set)


@dataclass
class BenchmarkResult:
    case_id: str
    context_precision: float
    context_recall: float
    answer_accuracy: float
    faithfulness: float
    latency_ms: int


def run_benchmark(cases: List[BenchmarkCase], query_fn) -> Dict[str, Any]:
    """
    Runs every benchmark case through `query_fn` (your actual RAG
    pipeline - e.g. backend.services.pipeline_service.run_query_pipeline,
    wrapped to also return retrieved chunk IDs and latency) and scores
    each one.

    `query_fn(question: str) -> {"answer": str, "chunk_ids": List[str],
    "context_texts": List[str], "latency_ms": int}`

    Keeping query_fn as a parameter (dependency injection again) means
    this file has ZERO dependency on FastAPI, the database, or any
    specific LLM - you could run this exact benchmark against a
    completely different pipeline implementation without touching
    this file.
    """
    results: List[BenchmarkResult] = []

    for case in cases:
        output = query_fn(case.question)

        results.append(BenchmarkResult(
            case_id=case.case_id,
            context_precision=context_precision(output["chunk_ids"], case.relevant_chunk_ids),
            context_recall=context_recall(output["chunk_ids"], case.relevant_chunk_ids),
            answer_accuracy=token_overlap_score(output["answer"], case.expected_answer),
            faithfulness=faithfulness_score(output["answer"], output["context_texts"]),
            latency_ms=output["latency_ms"],
        ))

    return _summarize(results)


def _summarize(results: List[BenchmarkResult]) -> Dict[str, Any]:
    n = len(results)
    if n == 0:
        return {"case_count": 0}

    latency_stats = compute_latency_stats([r.latency_ms for r in results])

    return {
        "case_count": n,
        "avg_context_precision": sum(r.context_precision for r in results) / n,
        "avg_context_recall": sum(r.context_recall for r in results) / n,
        "avg_answer_accuracy": sum(r.answer_accuracy for r in results) / n,
        "avg_faithfulness": sum(r.faithfulness for r in results) / n,
        "latency": latency_stats,
        "per_case": [r.__dict__ for r in results],
    }
