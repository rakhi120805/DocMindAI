"""
PaddleOCR Engine wrapper.

WHY PADDLEOCR (worth knowing for interviews, not just using it):
- Strong out-of-the-box accuracy on both typed and handwritten text
- Supports 80+ languages, including mixed English/Hindi documents,
  which matters for an India-focused document platform (Aadhaar,
  PAN cards often mix scripts)
- Runs on CPU reasonably fast (no GPU required, unlike some
  transformer-based OCR models) - important since this whole stack
  is designed to run without paid cloud infra

WHY LAZY-LOADED: PaddleOCR downloads and loads model weights on first
use (a few hundred MB). Loading it at import time would slow down
*every* app startup, even for requests that don't need OCR. Loading
it on first actual call means startup stays fast, and the one-time
cost only hits the first document processed.
"""

from typing import Any


class PaddleOCREngine:
    def __init__(self, lang: str = "en"):
        self.lang = lang
        self._engine = None

    def _load(self):
        if self._engine is None:
            from paddleocr import PaddleOCR
            self._engine = PaddleOCR(lang=self.lang, use_angle_cls=True)
            # use_angle_cls=True: detects and corrects text that's
            # rotated 90/180/270 degrees - common with phone-scanned
            # documents where orientation isn't guaranteed.
        return self._engine

    def extract_text(self, image: Any) -> str:
        """
        Returns raw text from a single page image, reading lines in
        the order PaddleOCR detects them (generally top-to-bottom,
        left-to-right, though complex layouts like tables can produce
        out-of-order results - a known limitation worth mentioning if
        asked about edge cases).
        """
        import numpy as np

        engine = self._load()
        result = engine.ocr(np.array(image), cls=True)

        lines = []
        # PaddleOCR's result shape: result[0] is a list of
        # [box_coordinates, (text, confidence)] per detected line.
        for line in result[0] or []:
            text = line[1][0]
            lines.append(text)

        return "\n".join(lines)
