import os, sys, tempfile
import streamlit as st
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.core.controller import agent
from src.core.llm import LLMServiceError

st.set_page_config(page_title="Research AI Agent", page_icon="🔬", layout="wide")

# Load and inject custom premium CSS styles
css_path = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        custom_css = f.read()
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "selected_files" not in st.session_state:
    st.session_state.selected_files = []

def render_sidebar():
    st.sidebar.title("🔬 Research AI Agent")
    st.sidebar.markdown("---")
    st.sidebar.subheader("📤 Upload Tài Liệu")

    uploaded = st.sidebar.file_uploader(
        "PDF, DOCX, TXT", type=["pdf","docx","txt"], accept_multiple_files=True)

    if uploaded:
        for uf in uploaded:
            if st.sidebar.button(f"Xử lý: {uf.name}", key=f"p_{uf.name}"):
                with st.sidebar.status(f"Đang xử lý {uf.name}..."):
                    suffix = os.path.splitext(uf.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uf.read()); tmp_path = tmp.name
                    try:
                        result = agent.ingest_document(tmp_path, file_name=uf.name)
                    finally:
                        os.unlink(tmp_path)
                if result["success"]:
                    st.sidebar.success(
                        f"✅ {result['num_pages']} trang, "
                        f"{result['num_chunks']} chunks, "
                        f"confidence: {result['section_confidence']}")
                else:
                    st.sidebar.error(result.get("error","Lỗi"))

    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Tài Liệu")
    docs = agent.get_documents()
    selected = []
    for doc in docs:
        c1, c2 = st.sidebar.columns([3,1])
        checked = c1.checkbox(doc["file_name"],
                              value=doc["file_name"] in st.session_state.selected_files,
                              key=f"sel_{doc['file_name']}")
        if c2.button("🗑", key=f"del_{doc['file_name']}"):
            agent.delete_document(doc["file_name"]); st.rerun()
        if checked: selected.append(doc["file_name"])
    st.session_state.selected_files = selected
    if selected:
        st.sidebar.success(f"{len(selected)} file đang chọn")
    return selected

def tab_chat(sel):
    st.header("💬 Chat với Tài Liệu")
    if not sel:
        st.info("Chọn tài liệu ở sidebar.")
        return
    st.caption(f"Đang chat với: {', '.join(sel)}")
    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if prompt := st.chat_input("Hỏi gì về tài liệu..."):
        st.session_state.chat_messages.append({"role":"user","content":prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Đang trả lời..."):
                try:
                    result = agent.ask(prompt, file_names=sel)
                except LLMServiceError as exc:
                    result = None
                    st.error(str(exc))
            if result:
                st.markdown(result["answer"])
                if result["sources"]:
                    with st.expander("📎 Nguồn"):
                        for s in result["sources"][:3]:
                            st.caption(f"{s['file_name']} — trang {s['page']} (score: {s['score']})")
                            st.caption(s["text"][:200]+"...")
        if result:
            st.session_state.chat_messages.append(
                {"role":"assistant","content":result["answer"]})
    if st.button("Xóa chat"):
        st.session_state.chat_messages = []
        st.rerun()

def tab_summary(sel):
    st.header("📝 Tóm Tắt")
    if not sel: st.info("Chọn tài liệu ở sidebar."); return
    fn = st.selectbox("Tài liệu:", sel, key="summary_document")
    stype = st.selectbox("Kiểu:", ["short","detailed","method","result","contribution","limitation"],
        format_func=lambda x: {
            "short":"Ngắn","detailed":"Chi tiết","method":"Phương pháp",
            "result":"Kết quả","contribution":"Đóng góp","limitation":"Hạn chế"}[x])
    if st.button("Tóm tắt", type="primary"):
        with st.spinner("Đang tóm tắt..."):
            try:
                summary = agent.summarize(fn, summary_type=stype)
            except LLMServiceError as exc:
                st.error(str(exc))
            else:
                st.markdown(summary)

def tab_card(sel):
    st.header("🃏 Paper Card")
    if not sel: st.info("Chọn tài liệu ở sidebar."); return
    fn = st.selectbox("Tài liệu:", sel, key="paper_card_document")
    c1, c2 = st.columns(2)
    do_extract = c1.button("Trích xuất", type="primary")
    do_refresh = c2.button("🔄 Làm mới")
    if do_extract or do_refresh:
        with st.spinner("Đang phân tích..."):
            try:
                card = agent.get_paper_card(fn, force_refresh=do_refresh)
            except LLMServiceError as exc:
                st.error(str(exc))
                return
        _show_card(card)
    else:
        from src.storage.sqlite_db import get_paper_card
        cached = get_paper_card(fn)
        if cached: st.info("Từ cache."); _show_card(cached)

def _show_card(card):
    fields = [
        ("title","📰 Tiêu đề"),("authors","👤 Tác giả"),("year","📅 Năm"),
        ("problem","❓ Vấn đề"),("objective","🎯 Mục tiêu"),("method","⚙️ Phương pháp"),
        ("dataset","📊 Dataset"),("result","📈 Kết quả"),("contribution","💡 Đóng góp"),
        ("limitation","⚠️ Hạn chế"),("future_work","🔮 Hướng phát triển"),
    ]
    for key, label in fields:
        f = card.get(key, {})
        if not f or not isinstance(f, dict): continue
        badge = {"high":"🟢","medium":"🟡","low":"🔴"}.get(f.get("confidence","low"),"⚪")
        with st.expander(f"{label} {badge}", expanded=key in ["title","method","result"]):
            v = f.get("value")
            st.write(", ".join(str(i) for i in v) if isinstance(v,list) else (v or "*Không tìm thấy*"))
            if f.get("evidence"):
                st.caption(f"📎 trang {f.get('page')}: {f['evidence']}")

def tab_matrix(sel):
    st.header("📊 Literature Review Matrix")
    if len(sel) < 2: st.info("Cần ít nhất 2 tài liệu."); return
    from src.storage.sqlite_db import get_paper_card
    missing = [f for f in sel if not get_paper_card(f)]
    if missing:
        st.warning(f"Chưa có Paper Card: {', '.join(missing)}")
        if st.button("Phân tích tất cả"):
            try:
                for fn in sel:
                    with st.spinner(f"Phân tích {fn}..."): agent.get_paper_card(fn)
            except LLMServiceError as exc:
                st.error(str(exc))
                return
            st.rerun()
        return
    if st.button("Tạo Matrix", type="primary"):
        import pandas as pd
        rows = agent.get_literature_matrix(sel)
        df = pd.DataFrame(rows)
        df.columns = ["File","Title","Year","Objective","Method",
                      "Dataset","Result","Limitation","Future Work"]
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Tải Markdown",
            data=agent.get_literature_matrix_markdown(sel),
            file_name="literature_matrix.md", mime="text/markdown")

def tab_gap(sel):
    st.header("🔍 Research Gap Suggestion")
    if not sel: st.info("Chọn tài liệu ở sidebar."); return
    if len(sel) == 1: st.warning("Chỉ 1 tài liệu — kết quả ít tin cậy hơn.")
    if st.button("Gợi ý Research Gaps", type="primary"):
        with st.spinner("Đang phân tích..."):
            try:
                gaps = agent.suggest_gaps(sel)
            except LLMServiceError as exc:
                st.error(str(exc))
                return
        for i, g in enumerate(gaps, 1):
            badge = {"high":"🟢 High","medium":"🟡 Medium","low":"🔴 Low"}.get(
                g.get("confidence","low"),"⚪")
            with st.expander(f"Gap {i}: {g.get('gap','')} — {badge}", expanded=True):
                st.markdown(f"**Evidence:** {g.get('evidence','N/A')}")
                if g.get("related_papers"):
                    st.markdown(f"**Papers:** {', '.join(g['related_papers'])}")
                st.markdown(f"**Hướng nghiên cứu:** {g.get('suggested_direction','N/A')}")
        st.info("⚠️ Đây là gợi ý dựa trên tài liệu được cung cấp.")

# ── Main ──
sel = render_sidebar()
tabs = st.tabs(["💬 Chat","📝 Tóm Tắt","🃏 Paper Card","📊 Matrix","🔍 Gap"])
with tabs[0]: tab_chat(sel)
with tabs[1]: tab_summary(sel)
with tabs[2]: tab_card(sel)
with tabs[3]: tab_matrix(sel)
with tabs[4]: tab_gap(sel)
