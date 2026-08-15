"""
Retrieval & Answer Quality Metrics.

WHY WE SEPARATE "DID RETRIEVAL FIND THE RIGHT STUFF" FROM "DID THE LLM
ANSWER WELL" (this is the single most important idea in this file):
A RAG system can fail in two completely different places:
  1. Retrieval finds the WRONG chunks -> even a perfect LLM can't
     answer correctly from bad context.
  2. Retrieval finds the RIGHT chunks, but the LLM ignores them or
     hallucinates anyway.
Measuring them separately tells you WHICH part to fix. Context
Precision/Recall measure #1. Faithfulness (see hallucination.py)
measures #2. Conflating them into one "did the answer seem OK" score
would hide which half of the system is actually broken.
"""

from typing import List, Set


def context_precision(retrieved_chunk_ids: List[str], relevant_chunk_ids: Set[str]) -> float:
    """
    Of the chunks we retrieved, what fraction were actually relevant?

    EXAMPLE: retrieved 5 chunks, only 3 were actually relevant to the
    question -> precision = 3/5 = 0.6. Low precision means retrieval
    is pulling in noise alongside the useful context, wasting prompt
    space and giving the LLM more chances to get distracted.
    """
    if not retrieved_chunk_ids:
        return 0.0
    hits = sum(1 for cid in retrieved_chunk_ids if cid in relevant_chunk_ids)
    return hits / len(retrieved_chunk_ids)


def context_recall(retrieved_chunk_ids: List[str], relevant_chunk_ids: Set[str]) -> float:
    """
    Of all the chunks that WERE actually relevant, what fraction did
    we manage to retrieve?

    EXAMPLE: 4 chunks in the document were truly relevant, we only
    retrieved 2 of them -> recall = 2/4 = 0.5. Low recall means the
    answer might be incomplete even if what we DID retrieve was
    accurate - e.g. missing a chunk that had the actual invoice total.
    """
    if not relevant_chunk_ids:
        return 1.0  # nothing was relevant, so we didn't miss anything
    hits = sum(1 for cid in retrieved_chunk_ids if cid in relevant_chunk_ids)
    return hits / len(relevant_chunk_ids)


def exact_match_accuracy(predicted: str, expected: str) -> float:
    """
    Strict metric for fields with one correct answer (invoice number,
    PAN, date) - normalized for case/whitespace but nothing fuzzier
    than that. Good for Metadata Extraction accuracy, NOT for
    open-ended QA answers (those need a softer comparison - see
    token_overlap_score below).
    """
    return 1.0 if predicted.strip().lower() == expected.strip().lower() else 0.0


def token_overlap_score(predicted: str, expected: str) -> float:
    """
    Softer accuracy metric for open-ended answers, where exact string
    matching is too strict (e.g. "The total is $1,200" vs "$1200 is
    the total amount" should both count as correct). Uses simple word
    overlap (a lightweight stand-in for something like ROUGE/BLEU) -
    good enough to catch obviously-wrong answers, not a substitute for
    a real NLP metric library or human review at scale.
    """
    pred_words = set(predicted.lower().split())
    expected_words = set(expected.lower().split())
    if not expected_words:
        return 1.0 if not pred_words else 0.0
    overlap = pred_words & expected_words
    return len(overlap) / len(expected_words)


def character_error_rate(ocr_text: str, ground_truth: str) -> float:
    """
    Standard OCR quality metric: what fraction of characters would
    need to be inserted/deleted/substituted to turn the OCR output
    into the correct text (Levenshtein edit distance / length of
    ground truth). 0.0 = perfect, higher = worse. This is the metric
    actual OCR benchmarks (and the architecture doc's "OCR Accuracy"
    line) use in practice - not just "does it look right."
    """
    if not ground_truth:
        return 0.0 if not ocr_text else 1.0

    distance = _levenshtein_distance(ocr_text, ground_truth)
    return distance / len(ground_truth)


def _levenshtein_distance(a: str, b: str) -> int:
    """Classic dynamic-programming edit distance, O(len(a) * len(b))."""
    if len(a) < len(b):
        a, b = b, a  # ensure `a` is the longer string, minor optimization

    previous_row = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current_row = [i] + [0] * len(b)
        for j, char_b in enumerate(b, start=1):
            insert_cost = current_row[j - 1] + 1
            delete_cost = previous_row[j] + 1
            substitute_cost = previous_row[j - 1] + (char_a != char_b)
            current_row[j] = min(insert_cost, delete_cost, substitute_cost)
        previous_row = current_row

    return previous_row[-1]
