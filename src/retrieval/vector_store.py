from __future__ import annotations
import hashlib
import re
import chromadb
from src.core.config import CHROMA_DB_PATH
from src.ingestion.chunker import Chunk
from src.retrieval.embeddings import get_embeddings_batch, get_embedding

_client = None

def _get(): 
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _client

def _legacy_name(fn: str) -> str:
    n = re.sub(r"[^a-zA-Z0-9_-]", "_", fn)[:60]
    return n if len(n) >= 3 else n + "___"

def _name(fn: str) -> str:
    stem = _legacy_name(fn)[:48]
    digest = hashlib.sha256(fn.encode("utf-8")).hexdigest()[:12]
    return f"{stem}_{digest}"

def _collection_names(file_name: str) -> list[str]:
    current, legacy = _name(file_name), _legacy_name(file_name)
    return [current] if current == legacy else [current, legacy]

def add_chunks(chunks: list[Chunk]) -> None:
    from collections import defaultdict
    by_file = defaultdict(list)
    for c in chunks: by_file[c["file_name"]].append(c)
    for fn, fc in by_file.items():
        delete_document(fn)
        coll = _get().get_or_create_collection(_name(fn), metadata={"hnsw:space":"cosine"})
        texts = [c["text"] for c in fc]
        coll.upsert(
            ids=[c["chunk_id"] for c in fc],
            embeddings=get_embeddings_batch(texts),
            documents=texts,
            metadatas=[{"file_name":c["file_name"],"page":c["page"],
                        "section":c["section"],"chunking_strategy":c["chunking_strategy"]}
                       for c in fc])

def query_chunks(query: str, file_names=None, top_k: int = 5) -> list[dict]:
    emb = get_embedding(query)
    names = ([name for f in file_names for name in _collection_names(f)]
             if file_names else [c.name for c in _get().list_collections()])
    results = []
    for name in names:
        try:
            coll = _get().get_collection(name)
            res = coll.query(query_embeddings=[emb], n_results=min(top_k, coll.count()),
                             include=["documents","metadatas","distances"])
            for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
                results.append({"text":doc, "file_name":meta.get("file_name",""),
                                 "page":meta.get("page",0), "section":meta.get("section","unknown"),
                                 "score":round(1-dist,4)})
        except Exception: continue
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

def delete_document(file_name: str) -> None:
    for name in _collection_names(file_name):
        try: _get().delete_collection(name)
        except Exception: pass
