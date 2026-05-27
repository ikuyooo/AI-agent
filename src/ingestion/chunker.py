from __future__ import annotations
import uuid
from typing import TypedDict
from src.core.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.ingestion.loaders import PageDoc, load_document
from src.ingestion.section_splitter import SectionDoc, detect_sections

class Chunk(TypedDict):
    chunk_id: str; file_name: str; page: int
    section: str; chunking_strategy: str; text: str

def chunk_document(file_path: str, file_name: str | None = None) -> tuple[list[Chunk], float]:
    pages = load_document(file_path, file_name=file_name)
    if not pages: return [], 0.0
    sections, conf = detect_sections(pages)
    return _chunk(sections), conf

def _chunk(sections: list[SectionDoc]) -> list[Chunk]:
    result = []
    for s in sections:
        fallback = s["section"] == "unknown"
        strategy = "page_based_fallback" if fallback else "section_based"
        if len(s["text"].split()) <= CHUNK_SIZE:
            result.append(_make(s, s["text"], strategy))
        else:
            for sub in _slide(s["text"]):
                result.append(_make(s, sub, "sliding_window"))
    return result

def _slide(text: str) -> list[str]:
    words, result, step = text.split(), [], max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    for i in range(0, len(words), step):
        result.append(" ".join(words[i:i+CHUNK_SIZE]))
        if i + CHUNK_SIZE >= len(words): break
    return result or [text]

def _make(s: SectionDoc, text: str, strategy: str) -> Chunk:
    cid = f"{s['file_name'].replace('.','_')}_p{s['page']}_{str(uuid.uuid4())[:8]}"
    return Chunk(chunk_id=cid, file_name=s["file_name"], page=s["page"],
                 section=s["section"], chunking_strategy=strategy, text=text.strip())
