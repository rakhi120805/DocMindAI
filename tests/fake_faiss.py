"""
A minimal fake of faiss.IndexFlatL2, used ONLY to test that
VectorStore's logic (add/search/filter) is correct without the real
faiss library installed. It does REAL L2 distance math - it's not a
dummy that returns fake data, it's a working brute-force
implementation of what faiss does internally, just unoptimized.
"""
import numpy as np


class FakeIndexFlatL2:
    def __init__(self, dimension):
        self.dimension = dimension
        self._vectors = np.empty((0, dimension), dtype="float32")

    @property
    def ntotal(self):
        return len(self._vectors)

    def add(self, vectors):
        self._vectors = np.vstack([self._vectors, vectors])

    def search(self, query, k):
        # Real L2 distance, computed the slow/obvious way on purpose -
        # this is exactly what faiss.IndexFlatL2 does under the hood,
        # just without the optimized C++ implementation.
        distances = np.linalg.norm(self._vectors - query[0], axis=1) ** 2
        k = min(k, len(distances))
        top_k_idx = np.argsort(distances)[:k]
        return (
            np.array([distances[top_k_idx]]),
            np.array([top_k_idx]),
        )


class FakeFaissModule:
    IndexFlatL2 = FakeIndexFlatL2
