import os, json
from src.storage.sqlite_db import get_paper_card
from src.core.llm import call_llm_json

def _v(f): return str(f.get("value","")) if f and isinstance(f,dict) and f.get("value") else ""

def suggest_gaps(file_names):
    summaries = []
    for fn in file_names:
        card = get_paper_card(fn)
        if not card: continue
        lim, fw = _v(card.get("limitation")), _v(card.get("future_work"))
        if lim or fw:
            summaries.append({"file":fn,"title":_v(card.get("title")),
                               "limitation":lim,"future_work":fw})
    if not summaries:
        return [{"gap":"Chưa đủ dữ liệu","evidence":"Hãy tạo Paper Card trước.",
                 "related_papers":[],"confidence":"low","suggested_direction":""}]
    path = os.path.join(os.path.dirname(__file__), "../prompts/gap_suggestion_prompt.md")
    prompt = open(path, encoding="utf-8").read().replace("{paper_cards}",
              json.dumps(summaries, ensure_ascii=False, indent=2))
    result = call_llm_json(prompt)
    gaps = result if isinstance(result,list) else result.get("gaps",[])
    return [{"gap":g.get("gap",""),"evidence":g.get("evidence",""),
             "related_papers":g.get("related_papers",[]),"confidence":g.get("confidence","low"),
             "suggested_direction":g.get("suggested_direction","")}
            for g in gaps if isinstance(g,dict)]