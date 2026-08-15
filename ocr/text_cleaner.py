"""
Text Cleaner — fixes common OCR artifacts before the text goes
anywhere near an LLM or gets chunked/embedded.

CONCRETE EXAMPLE of why this matters:
Raw PaddleOCR output for a real invoice line might look like:
    "Tot al  Amo unt  :  1,2 0 0 . 0 0  |||"
After cleaning:
    "Total Amount: 1,200.00"
Feeding the raw, noisy version into an LLM wastes tokens, and worse,
can cause the LLM to genuinely misread the amount. Cleaning text is a
cheap, deterministic step that meaningfully improves everything
downstream, which is why it's worth being a separate, testable
function rather than an afterthought.
"""

import re


def clean_text(raw_text: str) -> str:
    text = raw_text

    text = _collapse_broken_words(text)
    text = _remove_junk_lines(text)
    text = _normalize_whitespace(text)

    return text.strip()


def _collapse_broken_words(text: str) -> str:
    """
    OCR sometimes inserts stray spaces inside words/numbers due to
    slightly-separated characters in the scan ("Tot al", "1,2 0 0").
    We can't perfectly undo this without a dictionary/language model,
    but collapsing single-character "words" back into their neighbors
    catches a large share of these cases cheaply.
    """
    # Collapse a lone single character surrounded by spaces into the
    # word before it, e.g. "Tot al" -> "Total" is too aggressive to do
    # generically and safely, so we keep this targeted: only collapse
    # spacing WITHIN numbers (very common in amounts/dates), e.g.
    # "1,2 0 0 . 0 0" -> "1,200.00"
    text = re.sub(r"(?<=\d)\s+(?=\d)", "", text)          # "1 2 3" -> "123"
    text = re.sub(r"(?<=\d)\s*([.,])\s*(?=\d)", r"\1", text)  # "1 . 2" -> "1.2"
    return text


def _remove_junk_lines(text: str) -> str:
    """Drop lines that are pure noise: only symbols/pipes, or empty."""
    lines = text.split("\n")
    cleaned_lines = [
        line for line in lines
        if line.strip() and not re.fullmatch(r"[|_\-=~.\s]*", line)
    ]
    return "\n".join(cleaned_lines)


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)      # multiple spaces -> one
    text = re.sub(r"\n{3,}", "\n\n", text)   # 3+ blank lines -> one blank line
    return text
