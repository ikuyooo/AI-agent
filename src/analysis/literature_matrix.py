from src.storage.sqlite_db import get_paper_card

def _v(f):
    if not f or not isinstance(f,dict): return "N/A"
    v = f.get("value")
    if v is None: return "Không tìm thấy"
    return ", ".join(str(i) for i in v) if isinstance(v,list) else str(v)

def build_matrix(file_names):
    rows = []
    for fn in file_names:
        card = get_paper_card(fn)
        if not card:
            rows.append({k:"Chưa phân tích" for k in
                ["file_name","title","year","objective","method","dataset","result","limitation","future_work"]})
            rows[-1]["file_name"] = fn; continue
        rows.append({"file_name":fn,"title":_v(card.get("title")),"year":_v(card.get("year")),
                     "objective":_v(card.get("objective")),"method":_v(card.get("method")),
                     "dataset":_v(card.get("dataset")),"result":_v(card.get("result")),
                     "limitation":_v(card.get("limitation")),"future_work":_v(card.get("future_work"))})
    return rows

def matrix_to_markdown(rows):
    if not rows: return "Không có dữ liệu."
    headers = ["File","Title","Year","Objective","Method","Dataset","Result","Limitation","Future Work"]
    keys    = ["file_name","title","year","objective","method","dataset","result","limitation","future_work"]
    t = lambda s: s[:60]+"..." if len(s)>60 else s
    lines = ["| "+" | ".join(headers)+" |", "|"+"---|"*len(headers)]
    for r in rows: lines.append("| "+" | ".join(t(str(r.get(k,"N/A"))) for k in keys)+" |")
    return "\n".join(lines)