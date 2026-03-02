"""
철학 번역 DB 뷰어 - 책 선택 + 1:1 매핑 (NiceGUI, 무한 스크롤)
"""
import sqlite3
from urllib.parse import quote_plus, unquote_plus

from fastapi import Request
from nicegui import ui

from app_utils import (
    DB_PATH,
    PAGE_SIZE,
    count_sentences,
    fetch_books,
    fetch_sentences,
    get_db_connection,
)


def _sentence_card(container: ui.column, row_id: int, german: str, korean: str, seq: int) -> None:
    """문장 카드 하나를 container에 추가"""
    with container:
        with ui.card().classes("w-full p-4 my-2 bg-slate-50 border border-slate-200 rounded-lg"):
            ui.label(f"문장 {seq} · ID: {row_id}").classes("text-xs text-slate-400")
            ui.label("독일어").classes("text-xs text-slate-500")
            ui.label(german or "").classes("text-base leading-relaxed whitespace-pre-wrap")
            ui.label("한국어").classes("text-xs text-slate-500 mt-3")
            ui.label(korean or "").classes("text-base leading-relaxed whitespace-pre-wrap")


@ui.page("/")
def book_select():
    """책 선택 페이지"""
    ui.label("철학 번역 뷰어").classes("text-2xl font-bold")
    ui.label("독일어 ↔ 한국어 문장 1:1 매핑").classes("text-slate-500 text-sm")

    if not DB_PATH.exists():
        ui.notify(f"DB 파일을 찾을 수 없습니다: {DB_PATH}", type="negative")
        return

    conn = get_db_connection()
    try:
        books = fetch_books(conn)
    except sqlite3.Error as e:
        ui.notify(f"DB 조회 실패: {e}", type="negative")
        conn.close()
        return
    finally:
        conn.close()

    if not books:
        ui.label("등록된 책이 없습니다.").classes("text-amber-600")
        return

    options = [
        {"label": f"{author} — {book_title} ({cnt}문장)", "value": (author, book_title)}
        for author, book_title, cnt in books
    ]
    labels = [o["label"] for o in options]
    value_to_pair = {o["label"]: o["value"] for o in options}

    select = ui.select(
        options=labels,
        label="보고 싶은 책을 선택하세요",
    ).classes("w-full max-w-md")

    def open_book():
        label = select.value
        if not label:
            ui.notify("책을 선택하세요.", type="warning")
            return
        author, book_title = value_to_pair[label]
        ui.navigate.to(f"/mapping?author={quote_plus(author)}&book_title={quote_plus(book_title)}")

    ui.button("이 책 보기", on_click=open_book).props("unelevated color=primary").classes("mt-2")


@ui.page("/mapping")
def mapping(request: Request):
    """1:1 매핑 페이지 (무한 스크롤)"""
    author = request.query_params.get("author") or ""
    book_title = request.query_params.get("book_title") or ""
    author = unquote_plus(author)
    book_title = unquote_plus(book_title)

    if not author or not book_title:
        ui.navigate.to("/")
        return

    # 헤더
    with ui.row().classes("w-full items-center justify-between flex-wrap gap-2"):
        ui.label(f"뷰어 — {author} · {book_title}").classes("text-xl font-semibold")
        ui.button("다른 책 선택", on_click=lambda: ui.navigate.to("/")).props("flat")

    conn = get_db_connection()
    total = count_sentences(conn, author, book_title)
    conn.close()

    ui.label(f"총 {total}개 문장").classes("text-slate-500 text-sm mb-4")
    ui.separator()

    # 카드만 담는 컨테이너 (무한 스크롤 시 여기에 추가)
    cards_container = ui.column().classes("w-full")
    offset = {"value": 0}
    has_more = {"value": True}

    def load_more():
        if not has_more["value"]:
            return
        conn = get_db_connection()
        rows = fetch_sentences(conn, author, book_title, offset["value"], PAGE_SIZE)
        conn.close()
        n = len(rows)
        if n == 0:
            has_more["value"] = False
            return
        start_seq = offset["value"] + 1
        for i, (row_id, german, korean) in enumerate(rows):
            _sentence_card(cards_container, row_id, german, korean, start_seq + i)
        offset["value"] += n
        if n < PAGE_SIZE:
            has_more["value"] = False
            sentinel.set_visibility(False)
            end_label.set_visibility(True)
            ui.run_javascript("if (window.__scrollObserver) { window.__scrollObserver.disconnect(); window.__scrollObserver = null; }")

    # 숨겨진 버튼: JS에서 sentinel 진입 시 클릭 유도
    load_more_btn = ui.button("", on_click=load_more).props("id=load-more-btn").style("display: none")
    # sentinel: 스크롤 시 이 요소가 보이면 load_more 트리거
    sentinel = ui.element("div").props("id=scroll-sentinel").classes("h-4 w-full")
    end_label = ui.label("모든 문장을 불러왔습니다.").classes("text-slate-500 text-sm py-4").set_visibility(False)

    # 첫 배치 로드
    load_more()

    # IntersectionObserver: sentinel이 뷰포트에 들어오면 load_more 버튼 클릭
    observer_js = """
    (function() {
        var sentinel = document.getElementById('scroll-sentinel');
        var btn = document.getElementById('load-more-btn');
        if (!sentinel || !btn) return;
        window.__scrollObserver = new IntersectionObserver(function(entries) {
            if (entries[0].isIntersecting) btn.click();
        }, { rootMargin: '100px' });
        window.__scrollObserver.observe(sentinel);
    })();
    """
    ui.run_javascript(observer_js)


def main():
    ui.run(
        title="철학 번역 뷰어",
        favicon="📖",
        storage_secret="philosophy-viewer-secret",
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
