from __future__ import annotations
import os
from src.storage.sqlite_db import (init_db, save_document, get_all_documents,
    save_paper_card, get_paper_card, delete_document as db_del)
from src.ingestion.chunker import chunk_document
from src.retrieval.vector_store import add_chunks, delete_document as vdb_del
from src.analysis.qa import answer_question
from src.analysis.summarizer import summarize
from src.analysis.paper_extractor import extract_paper_card
from src.analysis.literature_matrix import build_matrix, matrix_to_markdown
from src.analysis.gap_suggester import suggest_gaps

class ResearchAgentController:
    def __init__(self): init_db()

    def ingest_document(self, file_path, file_name=None):
        file_name = file_name or os.path.basename(file_path)
        try:
            chunks, conf = chunk_document(file_path, file_name=file_name)
            if not chunks: return {"success":False,"error":"Không parse được nội dung."}
            add_chunks(chunks)
            pages = len({c["page"] for c in chunks})
            save_document(file_name, "", pages, len(chunks), conf)
            return {"success":True,"file_name":file_name,"num_pages":pages,
                    "num_chunks":len(chunks),"section_confidence":round(conf,2)}
        except Exception as e:
            return {"success":False,"error":str(e)}

    def delete_document(self, fn): db_del(fn); vdb_del(fn)
    def get_documents(self): return get_all_documents()
    def ask(self, q, file_names=None, top_k=5): return answer_question(q, file_names, top_k)
    def summarize(self, fn, summary_type="short"): return summarize(fn, summary_type)

    def get_paper_card(self, fn, force_refresh=False):
        if not force_refresh:
            cached = get_paper_card(fn)
            if cached: return cached
        card = extract_paper_card(fn)
        save_paper_card(fn, card)
        return card

    def get_literature_matrix(self, fns): return build_matrix(fns)
    def get_literature_matrix_markdown(self, fns): return matrix_to_markdown(build_matrix(fns))
    def suggest_gaps(self, fns): return suggest_gaps(fns)

agent = ResearchAgentController()
