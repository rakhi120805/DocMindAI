"""
Hallucination / Faithfulness Checking.

WHAT "FAITHFULNESS" MEANS HERE: does the LLM's answer only contain
claims that are actually supported by the retrieved context, or did
it add information that isn't there (hallucinate)?

WHY A WORD-OVERLAP HEURISTIC INSTEAD OF ANOTHER LLM CALL:
The "correct" way to measure this rigorously is LLM-as-judge - asking
a (possibly different, stronger) model "does this answer follow only
from this context? yes/no, cite the unsupported claims." That's more
accurate but costs an extra LLM call per query, adding latency and
(for paid APIs) cost. This heuristic is a cheap first pass: if an
answer's meaningful words barely overlap with the retrieved context
at all, that's a strong signal something was likely invented -
regardless of provider cost. It won't catch subtle hallucinations
(a wrong NUMBER surrounded by correct words scores fine here), which
is an honest limitation worth stating outright, not hiding.

INTERVIEW TALKING POINT: "I started with a cheap heuristic to get
signal immediately, and documented LLM-as-judge as the natural next
step for higher fidelity - this is a normal evaluation engineering
tradeoff, not a shortcut I'm hiding."
"""

from typing import List

# Common English stopwords that would inflate overlap scores without
# meaning anything (nearly every sentence contains "the", "is", "a").
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "to",
    "of", "in", "on", "for", "and", "or", "it", "this", "that", "with",
    "as", "at", "by", "from", "has", "have", "had", "not", "no",
}


def _meaningful_words(text: str) -> set:
    words = text.lower().split()
    return {w.strip(".,:;!?") for w in words if w.strip(".,:;!?") not in _STOPWORDS}


def faithfulness_score(answer: str, context_chunks: List[str]) -> float:
    """
    Returns 0.0-1.0: what fraction of the answer's meaningful words
    also appear somewhere in the retrieved context. A score near 1.0
    means the answer stays close to the source material; a score near
    0.0 is a red flag that the LLM introduced unsupported content.
    """
    answer_words = _meaningful_words(answer)
    if not answer_words:
        return 1.0  # empty/trivial answer, nothing to hallucinate

    context_text = " ".join(context_chunks)
    context_words = _meaningful_words(context_text)

    grounded = answer_words & context_words
    return len(grounded) / len(answer_words)


def flag_potential_hallucination(answer: str, context_chunks: List[str], threshold: float = 0.4) -> bool:
    """
    Convenience wrapper: True if faithfulness falls below threshold,
    meaning this answer is worth a human double-checking. The 0.4
    default is deliberately generous (low false-positive rate) since
    this heuristic is coarse - tune it against real labeled examples
    once you have some, rather than trusting this default blindly.
    """
    return faithfulness_score(answer, context_chunks) < threshold
