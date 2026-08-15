"""
Indexer — runs the Chunk -> Embed -> Store steps of the pipeline
(Steps 5-7 in the original architecture diagram).

WHY THIS ISN'T CALLED AN "AGENT" LIKE THE OTHERS:
It doesn't call an LLM and doesn't make any judgment calls - it's
pure, deterministic data pipeline work (split text, convert to
vectors, save them). Keeping it in rag/ rather than agents/ reflects
that distinction: agents reason, the indexer just processes. That
said, it exposes the same `.run(input) -> output` shape as an agent
so the Supervisor can call it identically - consistency in the
interface, even though this one holds no AI logic.
"""

from typing import Any, Dict, List
from rag.chunker import chunk_pages


class Indexer:
    def __init__(self, embedder, vector_store):
        self.embedder = embedder
        self.vector_store = vector_store

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pages = input_data["pages"]
        file_id = input_data["file_id"]

        chunks = chunk_pages(pages)
        if not chunks:
            return {"chunks": []}

        texts = [c["text"] for c in chunks]
        vectors = self.embedder.embed_batch(texts)

        # Each chunk's metadata travels alongside its vector so a
        # search hit can be traced back to file_id/page/text later.
        metadata: List[Dict[str, Any]] = [
            {
                "file_id": file_id,
                "chunk_index": c["chunk_index"],
                "page": c["page"],
                "text": c["text"],
            }
            for c in chunks
        ]

        self.vector_store.add(vectors, metadata)

        return {"chunks": metadata}
