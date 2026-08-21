import os
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
from ingest import ingest_folder

load_dotenv()

try:
    embed_model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
except Exception:
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="docs",
    metadata={"hnsw:space": "cosine"},
)

# Module-level BM25 state — built alongside the Chroma index
_all_chunks: list[dict] = []
_bm25: BM25Okapi | None = None


def _build_bm25(chunks: list[dict]):
    """Build the BM25 keyword index from the same chunks used for the
    vector index. Tokenization is simple whitespace split (lowercased)
    — good enough for structured technical docs."""
    global _all_chunks, _bm25
    _all_chunks = chunks
    tokenized = [c["text"].lower().split() for c in chunks]
    _bm25 = BM25Okapi(tokenized)


def _ensure_bm25():
    """Lazy-load BM25 if not yet built (e.g. on import when chroma_db
    already exists from a previous run)."""
    if _bm25 is None:
        chunks = ingest_folder("docs")
        _build_bm25(chunks)


def embed(text: str) -> list[float]:
    return embed_model.encode(text, convert_to_tensor=False).tolist()


def build_index(folder: str = "docs", force_reindex: bool = False):
    """Re-running this without a guard would add duplicate vectors on
    every run. By default, skip if the collection already has data;
    pass force_reindex=True to wipe and rebuild (e.g. after editing docs/)."""
    global collection

    if collection.count() > 0 and not force_reindex:
        print(f"Collection already has {collection.count()} items. Skipping. "
              f"Pass force_reindex=True to rebuild.")
        # Still build BM25 so hybrid_search works
        _ensure_bm25()
        return

    if force_reindex and collection.count() > 0:
        client.delete_collection("docs")
        collection = client.get_or_create_collection(
            name="docs",
            metadata={"hnsw:space": "cosine"},
        )

    chunks = ingest_folder(folder)
    print(f"Embedding {len(chunks)} chunks...")

    if not chunks:
        print("No chunks found to index.")
        return

    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [{"source": c["source"]} for c in chunks]
    embeddings = embed_model.encode(documents, convert_to_tensor=False).tolist()

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    print("Vector index built.")

    # Build BM25 from the same chunks
    _build_bm25(chunks)
    print("BM25 keyword index built.")


def search(query: str, top_k: int = 5) -> list[dict]:
    """Dense-only vector search (original baseline)."""
    if collection.count() == 0:
        return []

    query_embedding = embed(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    return [
        {
            "text": doc,
            "source": meta["source"],
            "distance": dist,
            "match_type": "Dense Vector Match",
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def rrf_score(rank: int, k: int = 60) -> float:
    """Reciprocal Rank Fusion score: 1 / (k + rank).
    k=60 is the standard constant from the original RRF paper."""
    return 1.0 / (k + rank)


def hybrid_search(query: str, top_k: int = 5) -> list[dict]:
    """Combine dense (vector) and sparse (BM25) search using
    Reciprocal Rank Fusion. Each result scores 1/(k+rank) in each
    list it appears in, and scores from both lists get summed."""
    _ensure_bm25()

    # 1. Dense hits — widen the net to top_k*2
    dense_hits = search(query, top_k=top_k * 2)

    # 2. Sparse (BM25) hits
    sparse_scores = _bm25.get_scores(query.lower().split())
    sparse_indices = sorted(
        range(len(sparse_scores)),
        key=lambda i: sparse_scores[i],
        reverse=True,
    )[:top_k * 2]

    # 3. Fuse rankings with RRF
    fused: dict[str, dict] = {}

    for rank, hit in enumerate(dense_hits):
        doc_id = hit["source"] + "_" + hit["text"][:50]
        fused.setdefault(doc_id, {"doc": dict(hit), "score": 0.0, "sources": []})
        fused[doc_id]["score"] += rrf_score(rank + 1)
        fused[doc_id]["sources"].append("dense")

    for rank, idx in enumerate(sparse_indices):
        chunk = _all_chunks[idx]
        doc_id = chunk["source"] + "_" + chunk["text"][:50]
        fused.setdefault(
            doc_id,
            {"doc": {"text": chunk["text"], "source": chunk["source"], "distance": 0.0}, "score": 0.0, "sources": []},
        )
        fused[doc_id]["score"] += rrf_score(rank + 1)
        fused[doc_id]["sources"].append("sparse")

    # 4. Sort by fused score descending, return top_k
    sorted_docs = sorted(fused.values(), key=lambda x: x["score"], reverse=True)
    results = []
    for item in sorted_docs[:top_k]:
        doc = item["doc"]
        sources = item["sources"]
        if "dense" in sources and "sparse" in sources:
            doc["match_type"] = "Hybrid Fused"
        elif "dense" in sources:
            doc["match_type"] = "Dense Vector"
        else:
            doc["match_type"] = "BM25 Keyword"
        doc["rrf_score"] = item["score"]
        results.append(doc)
    return results



if __name__ == "__main__":
    build_index("docs")

    test_query = "What are the four default roles in InfraDocs Cloud Platform RBAC?"
    print(f"\n--- Dense Search ---")
    print(f"Query: {test_query}")
    for r in search(test_query):
        print(f"\n[{r['source']}] (distance={r['distance']:.3f})")
        print(r["text"][:200])

    print(f"\n\n--- Hybrid Search (Dense + BM25 + RRF) ---")
    print(f"Query: {test_query}")
    for r in hybrid_search(test_query):
        print(f"\n[{r['source']}]")
        print(r["text"][:200])

