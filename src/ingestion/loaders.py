from __future__ import annotations
import os, re
from pathlib import Path
from typing import TypedDict

class PageDoc(TypedDict):
    file_name: str
    page: int
    text: str

def load_document(file_path: str, file_name: str | None = None) -> list[PageDoc]:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":       return _load_pdf(file_path, file_name)
    elif ext in (".docx",): return _load_docx(file_path, file_name)
    elif ext == ".txt":     return _load_txt(file_path, file_name)
    else: raise ValueError(f"Không hỗ trợ: {ext}")

def _load_pdf(file_path, file_name=None):
    import fitz
    pages, file_name = [], file_name or os.path.basename(file_path)
    doc = fitz.open(file_path)
    for i, page in enumerate(doc, 1):
        text = _clean(page.get_text("text"))
        if text.strip():
            pages.append({"file_name": file_name, "page": i, "text": text})
    doc.close()
    return pages

def _load_docx(file_path, file_name=None):
    from docx import Document
    file_name = file_name or os.path.basename(file_path)
    paras = [p.text for p in Document(file_path).paragraphs if p.text.strip()]
    return [{"file_name": file_name, "page": (i//50)+1,
             "text": _clean("\n".join(paras[i:i+50]))}
            for i in range(0, len(paras), 50)]

def _load_txt(file_path, file_name=None):
    file_name = file_name or os.path.basename(file_path)
    with open(file_path, encoding="utf-8", errors="ignore") as source:
        lines = source.read().splitlines()
    return [{"file_name": file_name, "page": (i//60)+1,
             "text": _clean("\n".join(lines[i:i+60]))}
            for i in range(0, len(lines), 60)
            if "\n".join(lines[i:i+60]).strip()]

def _clean(text: str) -> str:
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(l.rstrip() for l in text.splitlines()).strip()
