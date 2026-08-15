"""
OCR Agent — Step 2 of the pipeline.

JOB: Turn a PDF or image file into clean, machine-readable text.

PIPELINE (matches the architecture doc exactly):
  PDF or image file
    -> ocr/preprocess.py renders each page as an image + enhances it
    -> ocr/paddleocr_engine.py reads text from each page image
    -> ocr/text_cleaner.py removes OCR noise (stray characters, broken lines)
    -> returns [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}]

WHY THIS IS ITS OWN AGENT AND NOT JUST A UTILITY FUNCTION:
Because OCR quality directly determines the quality of everything
downstream (classification, extraction, answers). Treating it as a
first-class agent means we can independently measure and improve its
accuracy (see evaluation/metrics.py) without touching any LLM logic.

WHY THIS AGENT IS THIN (just orchestration, no real logic of its own):
Notice this file barely does anything besides call three functions in
order. That's deliberate — the actual image processing lives in
ocr/preprocess.py, the actual OCR model lives in
ocr/paddleocr_engine.py, and the actual text cleaning lives in
ocr/text_cleaner.py. This agent's only job is SEQUENCING them and
shaping the output into what the Supervisor expects. If asked in an
interview "why isn't the OCR logic just inside the agent file?" —
the answer is testability: each of those three pieces can be unit
tested in isolation (feed a known-noisy string into text_cleaner and
assert the exact output) without needing a real PDF or a loaded OCR
model.
"""

from agents.base_agent import BaseAgent
from typing import Any, Dict, List

from ocr.preprocess import load_pages_as_images, enhance_image
from ocr.paddleocr_engine import PaddleOCREngine
from ocr.text_cleaner import clean_text


class OCRAgent(BaseAgent):
    name = "ocr_agent"

    def __init__(self, lang: str = "en"):
        self.engine = PaddleOCREngine(lang=lang)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        file_path = input_data["file_path"]

        images = load_pages_as_images(file_path)
        results: List[Dict[str, Any]] = []

        for page_number, image in enumerate(images, start=1):
            enhanced = enhance_image(image)
            raw_text = self.engine.extract_text(enhanced)
            cleaned = clean_text(raw_text)
            results.append({"page": page_number, "text": cleaned})

        return {"pages": results}
