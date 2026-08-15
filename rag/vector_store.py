"""
Vector Store — wraps FAISS, a library for fast similarity search over
millions of vectors.

WHY NOT JUST LOOP AND COMPARE VECTORS MANUALLY: with even a few
thousand chunks, brute-force comparing a question's vector against
every chunk's vector one by one becomes slow. FAISS uses optimized
indexing structures to make "find the closest vectors" fast even at
scale — this is the difference between an index taking milliseconds
vs. seconds as your document library grows.

WHY WE ALSO STORE file_id ALONGSIDE EACH VECTOR: a raw FAISS index
only stores vectors, not which document or page they came from. We
keep a parallel metadata list so that after FAISS returns "vector #42
is the closest match", we can map that back to the actual chunk text,
page number, and file_id (this mapping is also mirrored in the
DocumentChunk SQLite table — see backend/database/models.py).

CRITICAL DESIGN NOTE - SINGLETON, NOT PER-REQUEST:
This class must be instantiated ONCE and reused across every request
(see get_vector_store() at the bottom of this file). If a fresh
VectorStore were created per HTTP request, every embedding added
during /upload would vanish before the first /query arrived - the
index would just be empty again. This is a genuinely easy mistake to
make when wiring dependency injection, and worth explicitly checking
for in any service holding in-memory state.
"""

from typing import List, Dict, Any, Optional


class VectorStore:
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self._index = None
        self._metadata: List[Dict[str, Any]] = []  # parallel array to index positions

    def _load_index(self):
        if self._index is None:
            import faiss
            # IndexFlatL2: brute-force exact search using L2 (Euclidean)
            # distance. For a student project's document scale (dozens-
            # hundreds of chunks, not millions), exact search is both
            # fast enough AND simpler to reason about than an
            # approximate index (like IVF or HNSW), which trades a
            # little accuracy for speed at massive scale we don't need
            # here. Worth mentioning if asked "would this scale?" -
            # the answer is "swap IndexFlatL2 for IndexIVFFlat past
            # ~100k vectors," not a rewrite.
            self._index = faiss.IndexFlatL2(self.dimension)
        return self._index

    def add(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]):
        """metadata[i] describes vectors[i]: {file_id, chunk_index, page, text}"""
        if len(vectors) != len(metadata):
            raise ValueError("vectors and metadata must be the same length")
        if not vectors:
            return

        index = self._load_index()
        import numpy as np
        index.add(np.array(vectors).astype("float32"))
        self._metadata.extend(metadata)

    def search(
        self, vector: List[float], top_k: int = 5, filter_file_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        index = self._load_index()

        if index.ntotal == 0:
            return []  # nothing indexed yet - fail gracefully, not with an exception

        import numpy as np
        # Search more than top_k when filtering by file_id, since some
        # of the nearest matches overall might belong to a different
        # document and get filtered out afterward.
        search_k = top_k * 5 if filter_file_id else top_k
        search_k = min(search_k, index.ntotal)

        distances, indices = index.search(
            np.array([vector]).astype("float32"), search_k
        )

        results = []
        for idx in indices[0]:
            if idx == -1:
                continue
            match = self._metadata[idx]
            if filter_file_id and match.get("file_id") != filter_file_id:
                continue
            results.append(match)
            if len(results) >= top_k:
                break

        return results


# --- Singleton accessor ---
# See the class docstring above for why this matters: without it,
# every request would get a fresh, empty vector store.
_shared_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _shared_instance
    if _shared_instance is None:
        _shared_instance = VectorStore()
    return _shared_instance
