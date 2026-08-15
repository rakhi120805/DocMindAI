"""
Embedder — turns text into vectors (lists of numbers) that capture
MEANING, not just words.

CONCRETE EXAMPLE for interviews:
  "total amount due"   -> [0.12, -0.44, 0.81, ...]  (768 numbers)
  "amount payable"      -> [0.13, -0.42, 0.79, ...]  (768 numbers)
These two vectors will be close together in that 768-dimensional
space even though they share no words in common, because the model
was trained so that similar MEANINGS end up close together
geometrically. That's what makes semantic search possible — a keyword
search for "amount payable" would never find "total amount due" in
a plain text search, but vector search does.

WHY SENTENCE TRANSFORMERS specifically: it's a well-established,
lightweight model family (e.g. all-mpnet-base-v2, 768 dimensions)
that runs on CPU reasonably fast — no need for a GPU just to embed
text, unlike running the LLM itself.
"""

from typing import List, Optional


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        self.model_name = model_name
        self._model = None  # lazy-loaded

    def _load_model(self):
        if self._model is None:
            # This download happens ONCE - the model (~420MB for
            # all-mpnet-base-v2) is fetched from the Hugging Face Hub
            # and cached locally (~/.cache/huggingface). Every run
            # after the first loads instantly from that local cache -
            # no network needed, no Hugging Face API calls in the
            # actual request path.
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, text: str) -> List[float]:
        model = self._load_model()
        return model.encode(text).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        model = self._load_model()
        return model.encode(texts).tolist()


# --- Singleton accessor ---
# Not a correctness issue like VectorStore's singleton (Embedder holds
# no data that needs to persist) - this is purely a performance one.
# Loading the model takes real time; doing that on every single
# request instead of once would make every upload/query noticeably
# slower for no benefit.
_shared_instance: Optional[Embedder] = None


def get_embedder() -> Embedder:
    global _shared_instance
    if _shared_instance is None:
        _shared_instance = Embedder()
    return _shared_instance
