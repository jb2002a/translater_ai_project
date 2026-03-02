"""
철학 번역 DB 뷰어 - 책 선택 + 1:1 매핑
"""
import html
import sqlite3

import streamlit as st

from app_utils import (
    DB_PATH,
    PAGE_SIZE,
    count_sentences,
    fetch_books,
    fetch_sentences,
    get_db_connection,
)


def render_book_select():
    """책 선택 페이지"""
    st.title("📖 철학 번역 뷰어")
    st.caption("독일어 ↔ 한국어 문장 1:1 매핑")

    if not DB_PATH.exists():
        st.error(f"DB 파일을 찾을 수 없습니다: {DB_PATH}")
        return

    conn = get_db_connection()
    try:
        books = fetch_books(conn)
    except sqlite3.Error as e:
        st.error(f"DB 조회 실패: {e}")
        conn.close()
        return
    finally:
        conn.close()

    if not books:
        st.warning("등록된 책이 없습니다.")
        return

    st.subheader("📚 책 선택")

    options = [f"{author} — {book_title} ({cnt}문장)" for author, book_title, cnt in books]
    book_data = {opt: (author, book_title) for opt, (author, book_title, _) in zip(options, books)}

    selected_label = st.selectbox(
        "보고 싶은 책을 선택하세요",
        options=options,
        key="book_select",
    )

    if st.button("📄 이 책 보기", type="primary"):
        if selected_label:
            author, book_title = book_data[selected_label]
            st.session_state["selected_book"] = {"author": author, "book_title": book_title}
            st.session_state["current_page"] = "mapping"
            st.rerun()


def render_mapping():
    """1:1 매핑 페이지"""
    selected = st.session_state.get("selected_book")
    if not selected:
        st.session_state["current_page"] = "select"
        st.rerun()
        return

    author = selected["author"]
    book_title = selected["book_title"]

    st.title("뷰어")
    st.caption(f"{author} — {book_title}")

    if st.button("다른 책 선택"):
        if "selected_book" in st.session_state:
            del st.session_state["selected_book"]
        st.session_state["current_page"] = "select"
        st.rerun()

    st.markdown("---")

    conn = get_db_connection()
    total = count_sentences(conn, author, book_title)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    conn.close()

    mapping_page = st.session_state.get("mapping_page", 1)
    mapping_page = max(1, min(mapping_page, total_pages))
    st.session_state["mapping_page"] = mapping_page

    page = st.number_input(
        "페이지",
        min_value=1,
        max_value=total_pages,
        value=mapping_page,
        step=1,
        format="%d",
    )
    st.session_state["mapping_page"] = page
    offset = (page - 1) * PAGE_SIZE

    st.info(f"총 **{total}**개 문장 (페이지 {page}/{total_pages})")

    conn = get_db_connection()
    rows = fetch_sentences(conn, author, book_title, offset, PAGE_SIZE)
    conn.close()

    if not rows:
        st.warning("문장이 없습니다.")
        return

    st.markdown("""
    <style>
    .sentence-card {
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        border-radius: 8px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
    }
    .sentence-card .label {
        font-size: 0.75rem;
        color: #64748b;
        margin-bottom: 0.25rem;
    }
    .sentence-card .text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #1e293b;
    }
    </style>
    """, unsafe_allow_html=True)

    for i, row in enumerate(rows):
        row_id, german, korean = row
        german = html.escape(german or "").replace("\n", "<br>")
        korean = html.escape(korean or "").replace("\n", "<br>")
        seq = offset + i + 1

        st.markdown(f"""
        <div class="sentence-card">
            <div class="label">문장 {seq} · ID: {row_id}</div>
            <div class="label">독일어</div>
            <div class="text">{german}</div>
            <div class="label" style="margin-top: 0.75rem;">한국어</div>
            <div class="text">{korean}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("이전", key="prev_page", disabled=(page <= 1)):
            st.session_state["mapping_page"] = page - 1
            st.rerun()
    with col_info:
        st.markdown(f"<p style='text-align:center;margin:0.5rem 0;color:#64748b;'>페이지 {page} / {total_pages}</p>", unsafe_allow_html=True)
    with col_next:
        if st.button("다음", key="next_page", disabled=(page >= total_pages)):
            st.session_state["mapping_page"] = page + 1
            st.rerun()


def main():
    st.set_page_config(
        page_title="철학 번역 뷰어",
        page_icon="📖",
        layout="wide",
    )

    if st.session_state.get("current_page") == "mapping":
        render_mapping()
    else:
        render_book_select()


if __name__ == "__main__":
    main()
