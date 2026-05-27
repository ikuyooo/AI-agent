import os
from src.retrieval.vector_store import query_chunks
from src.core.llm import call_llm

def answer_question(question, file_names=None, top_k=5):
    chunks = query_chunks(question, file_names=file_names, top_k=top_k)
    if not chunks:
        return {"answer": "Không tìm thấy thông tin trong tài liệu.", "sources": []}
    context = "\n\n---\n\n".join(
        f"[{i}] File: {c['file_name']}, Page: {c['page']}\n{c['text']}"
        for i, c in enumerate(chunks, 1))
    path = os.path.join(os.path.dirname(__file__), "../prompts/qa_prompt.md")
    prompt = open(path, encoding="utf-8").read().replace("{context}", context).replace("{question}", question)
    return {"answer": call_llm(prompt), "sources": chunks}