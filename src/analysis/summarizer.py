import os
from src.retrieval.vector_store import query_chunks
from src.core.llm import call_llm

QUERIES = {
    "short":        ["abstract summary overview", "conclusion"],
    "detailed":     ["abstract introduction", "methodology", "results", "conclusion limitation"],
    "method":       ["methodology method approach"],
    "result":       ["results performance accuracy"],
    "contribution": ["contribution novelty"],
    "limitation":   ["limitation future work"],
}

def summarize(file_name, summary_type="short"):
    seen, chunks = set(), []
    for q in QUERIES.get(summary_type, QUERIES["short"]):
        for c in query_chunks(q, file_names=[file_name], top_k=4):
            if c["text"] not in seen:
                seen.add(c["text"]); chunks.append(c)
    if not chunks: return "Không tìm thấy nội dung."
    content = "\n\n---\n\n".join(f"[Page {c['page']}]\n{c['text']}" for c in chunks[:8])
    path = os.path.join(os.path.dirname(__file__), "../prompts/summary_prompt.md")
    prompt = open(path, encoding="utf-8").read().replace("{content}", content).replace("{summary_type}", summary_type)
    return call_llm(prompt)