import os
from src.retrieval.vector_store import query_chunks
from src.core.llm import call_llm_json

QUERIES = ["title authors year","research problem objective",
           "methodology method","dataset benchmark",
           "results performance","contribution novelty",
           "limitation drawback","future work"]

def extract_paper_card(file_name):
    seen, chunks = set(), []
    for q in QUERIES:
        for c in query_chunks(q, file_names=[file_name], top_k=3):
            if c["text"] not in seen:
                seen.add(c["text"]); chunks.append(c)
    if not chunks: return _empty(file_name, "Không có nội dung.")
    content, wc = [], 0
    for c in chunks:
        w = len(c["text"].split())
        if wc + w > 3000: break
        content.append(f"[Page {c['page']}, {c['section']}]\n{c['text']}"); wc += w
    path = os.path.join(os.path.dirname(__file__), "../prompts/paper_extraction_prompt.md")
    prompt = open(path, encoding="utf-8").read().replace("{content}", "\n\n---\n\n".join(content))
    card = call_llm_json(prompt)
    card["file_name"] = file_name
    return card

def _empty(fn, reason):
    nf = {"value":None,"evidence":None,"page":None,"confidence":"low"}
    return {"file_name":fn,"error":reason,**{k:nf for k in
            ["title","authors","year","problem","objective","method",
             "dataset","result","contribution","limitation","future_work"]}}