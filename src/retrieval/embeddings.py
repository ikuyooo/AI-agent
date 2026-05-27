from __future__ import annotations
from src.core.config import EMBEDDING_PROVIDER, EMBEDDING_MODEL, OPENAI_API_KEY

_model = None

def get_embedding(text: str) -> list[float]:
    return _local(text) if EMBEDDING_PROVIDER == "local" else _openai(text)

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    return _local_batch(texts) if EMBEDDING_PROVIDER == "local" else [_openai(t) for t in texts]

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

def _local(text):      return _get_model().encode(text, convert_to_numpy=True).tolist()
def _local_batch(texts): return _get_model().encode(texts, convert_to_numpy=True).tolist()

def _openai(text):
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY).embeddings.create(
        model="text-embedding-3-small", input=text).data[0].embedding