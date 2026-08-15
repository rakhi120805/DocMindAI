"""
Chunker.

WHY CHUNK AT ALL: LLMs have limited context windows, and even when
they don't, stuffing an entire document into every prompt is slow and
expensive. Chunking breaks text into bite-sized pieces so we only feed
the LLM the parts relevant to a given question.

WHY OVERLAP (128 tokens here, matching the architecture doc): if a
sentence describing "the total amount due" gets cut exactly at the
chunk boundary, splitting it in half would destroy its meaning in the
embedding. Overlapping chunks means important context rarely gets cut
cleanly in two.

WHY 512 TOKENS: a common sweet spot — small enough to keep each
chunk's embedding focused on one topic (better retrieval precision),
large enough to preserve enough context for the LLM to answer from.
"""

from typing import List, Dict


def chunk_pages(
    pages: List[Dict], chunk_size: int = 512, overlap: int = 128
) -> List[Dict]:
    """
    Input: [{"page": 1, "text": "..."}, ...]
    Output: [{"page": 1, "chunk_index": 0, "text": "..."}, ...]

    NOTE: this uses a simple word-count approximation for tokens.
    In production, use a real tokenizer (e.g. tiktoken or the
    embedding model's own tokenizer) so chunk boundaries match what
    the model actually "sees" as tokens.
    """
    chunks = []
    chunk_index = 0

    for page in pages:
        words = page["text"].split()
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_text = " ".join(words[start:end])
            chunks.append({
                "page": page["page"],
                "chunk_index": chunk_index,
                "text": chunk_text,
            })
            chunk_index += 1
            start = end - overlap  # step forward, but overlap with previous chunk

    return chunks
