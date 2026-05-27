from __future__ import annotations
import re
from typing import TypedDict
from src.core.config import KNOWN_SECTIONS, SECTION_CONFIDENCE_THRESHOLD
from src.ingestion.loaders import PageDoc

class SectionDoc(TypedDict):
    file_name: str
    page: int
    section: str
    text: str

CORE = {"abstract","introduction","method","methodology","results","conclusion","experiment"}

def detect_sections(pages: list[PageDoc]) -> tuple[list[SectionDoc], float]:
    lines = [(l, p["page"], p["file_name"]) for p in pages for l in p["text"].splitlines()]
    headings = [(i, s) for i, (l,_,_) in enumerate(lines) if (s := _match(l))]
    confidence = len({s for _,s in headings} & CORE) / len(CORE)
    file_name = pages[0]["file_name"] if pages else "unknown"
    if confidence < SECTION_CONFIDENCE_THRESHOLD:
        return [{"file_name":p["file_name"],"page":p["page"],
                 "section":"unknown","text":p["text"]} for p in pages], confidence
    return _split(lines, headings, file_name), confidence

def _match(line: str):
    lc = line.strip().lower()
    if len(lc) > 80 or len(lc) < 3: return None
    for s in KNOWN_SECTIONS:
        if re.match(rf"^(?:\d+[\.\s]+)?{re.escape(s)}s?\s*$", lc): return s
    m = re.match(r"^(?:[ivxIVX\d]+(?:[\.\d]+)*[\.\s]+)(.+)$", lc)
    if m:
        cand = m.group(1).strip().rstrip(".")
        for s in KNOWN_SECTIONS:
            if cand == s or cand.startswith(s): return s
    return None

def _split(lines, headings, file_name):
    result, h = [], headings + [(len(lines), "__end__")]
    for i, (start, name) in enumerate(h[:-1]):
        seg = lines[start:h[i+1][0]]
        text = "\n".join(l for l,_,_ in seg).strip()
        if text:
            result.append({"file_name":file_name,"page":seg[0][1],
                           "section":name,"text":text})
    return result