"""
철학 번역 DB 뷰어 - 책 선택 + 1:1 매핑 (NiceGUI, 무한 스크롤)
"""
import asyncio
import logging
import os
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import quote_plus, unquote_plus

from fastapi import Request
from nicegui import ui

from app_utils import (
    DB_PATH,
    PAGE_SIZE,
    check_duplicate_book,
    count_sentences,
    delete_book,
    fetch_books,
    fetch_sentences,
    get_db_connection,
    get_id_by_seq,
    get_offset_by_seq,
)

try:
    from main.exceptions import TranslaterAIError
except ImportError:
    TranslaterAIError = Exception

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _sentence_card(container: ui.column, row_id: int, german: str, korean: str, seq: int) -> None:
    """문장 카드 하나를 container에 추가 (id=sentence-{row_id}로 스크롤 이동 가능)"""
    with container:
        with ui.card().classes("w-full p-4 my-2 bg-slate-50 border border-slate-200 rounded-lg").props(
            f"id=sentence-{row_id}"
        ):
            ui.label(f"문장 {seq} · ID: {row_id}").classes("text-xs text-slate-400")
            ui.label("독일어").classes("text-xs text-slate-500")
            ui.label(german or "").classes("text-base leading-relaxed whitespace-pre-wrap")
            ui.label("한국어").classes("text-xs text-slate-500 mt-3")
            ui.label(korean or "").classes("text-base leading-relaxed whitespace-pre-wrap")


def _run_preprocess(pdf_path: str, author: str, book_title: str, db_path: str):
    """전처리 그래프 동기 실행 (asyncio.to_thread에서 호출)."""
    from main.pre_process.graph import create_preprocessing_workflow
    from main.TranslationState import GraphState

    app = create_preprocessing_workflow()
    initial_state: GraphState = {
        "pdf_path": pdf_path,
        "author": author,
        "book_title": book_title,
        "db_path": db_path,
    }
    return app.invoke(initial_state)


def _run_postprocess(db_path: str, author: str, book_title: str):
    """후처리(번역) 그래프 동기 실행 (asyncio.to_thread에서 호출)."""
    from main.post_process.graph import create_translation_workflow
    from main.post_process.service.TranslationDbService import has_untranslated_sentences
    from main.TranslationState import PostTranslationState

    if not has_untranslated_sentences(db_path, author, book_title):
        return None
    app = create_translation_workflow()
    initial_state: PostTranslationState = {
        "db_path": db_path,
        "author": author,
        "book_title": book_title,
    }
    return app.invoke(initial_state)


@ui.page("/")
def book_select():
    """메인 페이지: 책 선택 탭 + DB 관리 탭"""
    ui.label("철학 번역 뷰어").classes("text-2xl font-bold")
    ui.label("독일어 ↔ 한국어 문장 1:1 매핑").classes("text-slate-500 text-sm")

    if not DB_PATH.exists():
        ui.notify(f"DB 파일을 찾을 수 없습니다: {DB_PATH}", type="negative")
        return

    books_state: dict = {"books": []}
    db_path_str = str(DB_PATH)

    with ui.tabs().classes("w-full mt-4") as tabs:
        tab_books = ui.tab("책 선택")
        tab_manage = ui.tab("DB 관리")
    with ui.tab_panels(tabs, value=tab_books).classes("w-full"):
        # ----- 책 선택 탭 -----
        with ui.tab_panel(tab_books):
            select = ui.select(
                options=[],
                label="보고 싶은 책을 선택하세요",
            ).classes("w-full max-w-md")

            empty_msg = ui.label("등록된 책이 없습니다. DB 관리 탭에서 PDF를 추가하세요.").classes(
                "text-amber-600 mt-2"
            )

            def refresh_book_list():
                conn = get_db_connection()
                try:
                    books_state["books"] = fetch_books(conn)
                except sqlite3.Error as e:
                    books_state["books"] = []
                    ui.notify(f"책 목록 조회 실패: {e}", type="warning")
                finally:
                    conn.close()
                labels = [f"{a} — {t} ({c}문장)" for a, t, c in books_state["books"]]
                select.options = labels
                select.update()
                empty_msg.set_visibility(not books_state["books"])

            def open_book():
                label = select.value
                if not label:
                    ui.notify("책을 선택하세요.", type="warning")
                    return
                for a, t, c in books_state["books"]:
                    if f"{a} — {t} ({c}문장)" == label:
                        ui.navigate.to(
                            f"/mapping?author={quote_plus(a)}&book_title={quote_plus(t)}"
                        )
                        return
                ui.notify("선택한 책을 찾을 수 없습니다.", type="warning")

            ui.button("이 책 보기", on_click=open_book).props(
                "unelevated color=primary"
            ).classes("mt-2")
            refresh_book_list()

        # ----- DB 관리 탭 -----
        with ui.tab_panel(tab_manage):
            # DB 추가
            ui.label("DB 추가").classes("text-lg font-semibold mt-2")
            ui.label(
                "PDF를 업로드하고 저자·책 제목을 입력한 뒤 추가하세요. "
                "전처리(문장 추출·정리)와 후처리(번역)가 순서대로 실행되며, "
                "파일 크기에 따라 수십 분이 걸릴 수 있습니다."
            ).classes("text-slate-600 text-sm mb-2")

            pdf_path_holder: dict = {"path": None}

            with ui.card().classes("w-full max-w-lg p-4 mb-4"):
                author_input = ui.input("저자").classes("w-full").props("outlined dense")
                book_title_input = ui.input("책 제목").classes("w-full").props(
                    "outlined dense"
                )

                async def on_upload(e):
                    name = e.file.name
                    suffix = Path(name).suffix or ".pdf"
                    fd, path = tempfile.mkstemp(suffix=suffix)
                    fd_closed = False
                    try:
                        content = await e.file.read()
                        if not content:
                            ui.notify("업로드된 파일이 비어 있습니다.", type="warning")
                            os.close(fd)
                            fd_closed = True
                            try:
                                os.unlink(path)
                            except OSError:
                                pass
                            return
                        os.write(fd, content)
                    finally:
                        if not fd_closed:
                            os.close(fd)
                    pdf_path_holder["path"] = path
                    ui.notify(f"업로드 완료: {name}", type="positive")

                upload = ui.upload(
                    label="PDF 파일",
                    on_upload=on_upload,
                    auto_upload=True,
                ).classes("w-full").props("accept=.pdf")

                progress_log = ui.log(max_lines=20).classes("w-full h-32 mt-2")
                progress_spinner = ui.spinner(size="lg")
                progress_spinner.set_visibility(False)

                async def do_add():
                    author_val = (author_input.value or "").strip()
                    book_val = (book_title_input.value or "").strip()
                    if not author_val or not book_val:
                        ui.notify("저자와 책 제목을 모두 입력하세요.", type="warning")
                        return
                    if not pdf_path_holder.get("path"):
                        ui.notify("PDF 파일을 업로드하세요.", type="warning")
                        return

                    conn = get_db_connection()
                    try:
                        if check_duplicate_book(conn, author_val, book_val):
                            ui.notify(
                                "이미 동일한 저자·책 제목이 DB에 있습니다. 중복 추가할 수 없습니다.",
                                type="negative",
                            )
                            return
                    finally:
                        conn.close()

                    add_btn.set_visibility(False)
                    progress_spinner.set_visibility(True)
                    pdf_path = pdf_path_holder["path"]
                    try:
                        progress_log.push("전처리 시작... (수십 분 걸릴 수 있습니다)")
                        await asyncio.to_thread(
                            _run_preprocess, pdf_path, author_val, book_val, db_path_str
                        )
                        progress_log.push("전처리 완료. 후처리(번역) 시작...")
                        await asyncio.to_thread(
                            _run_postprocess, db_path_str, author_val, book_val
                        )
                        progress_log.push("후처리 완료.")
                        ui.notify("DB 추가 및 번역이 완료되었습니다.", type="positive")
                        refresh_book_list()
                    except TranslaterAIError as e:
                        progress_log.push(f"오류: {e}")
                        ui.notify(f"처리 실패: {e}", type="negative")
                    except Exception as e:
                        progress_log.push(f"오류: {e}")
                        ui.notify(f"처리 중 오류: {e}", type="negative")
                    finally:
                        if pdf_path and Path(pdf_path).exists():
                            try:
                                Path(pdf_path).unlink()
                            except OSError:
                                pass
                        pdf_path_holder["path"] = None
                        progress_spinner.set_visibility(False)
                        add_btn.set_visibility(True)

                add_btn = ui.button("추가", on_click=do_add).props(
                    "unelevated color=primary"
                ).classes("mt-2")

            # DB 삭제
            ui.label("DB 삭제").classes("text-lg font-semibold mt-4")
            ui.label("삭제할 책을 선택한 뒤 삭제 버튼을 누르세요.").classes(
                "text-slate-600 text-sm mb-2"
            )

            book_list_container = ui.column().classes("w-full")

            def render_book_list():
                book_list_container.clear()
                with book_list_container:
                    conn = get_db_connection()
                    try:
                        books = fetch_books(conn)
                    finally:
                        conn.close()
                    if not books:
                        ui.label("등록된 책이 없습니다.").classes("text-slate-500")
                        return
                    for author, book_title, cnt in books:
                        with ui.row().classes("items-center gap-2 w-full mb-2"):
                            ui.label(f"{author} — {book_title} ({cnt}문장)").classes(
                                "flex-1"
                            )

                            def make_delete(a, t):
                                def delete_confirm():
                                    with ui.dialog() as dialog, ui.card():
                                        ui.label(
                                            f"다음 책을 DB에서 삭제하겠습니까?\n{a} — {t}"
                                        )
                                        with ui.row():
                                            ui.button("취소", on_click=dialog.close)
                                            ui.button(
                                                "삭제",
                                                on_click=lambda: do_delete(a, t, dialog),
                                            ).props("color=negative")

                                    dialog.open()

                                return delete_confirm

                            def do_delete(a, t, dialog):
                                conn = get_db_connection()
                                try:
                                    n = delete_book(conn, a, t)
                                    dialog.close()
                                    ui.notify(f"삭제 완료: {n}개 문장 삭제됨.", type="positive")
                                    refresh_book_list()
                                    render_book_list()
                                except sqlite3.Error as e:
                                    ui.notify(f"삭제 실패: {e}", type="negative")
                                finally:
                                    conn.close()

                            ui.button("삭제", on_click=make_delete(author, book_title)).props(
                                "flat color=negative dense"
                            )

            render_book_list()


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

    ui.label(f"총 {total}개 문장").classes("text-slate-500 text-sm mb-2")

    # 문장 번호 검색 후 해당 위치로 스크롤
    with ui.row().classes("items-center gap-2 mb-4"):
        seq_input = ui.input("문장 번호", placeholder=f"1 ~ {total}").classes("w-36").props("type=number outlined dense")

        def go_to_seq():
            try:
                seq = int((seq_input.value or "").strip() or "0")
            except ValueError:
                ui.notify("올바른 문장 번호를 입력하세요.", type="warning")
                return
            if seq <= 0:
                ui.notify("올바른 문장 번호를 입력하세요.", type="warning")
                return
            conn = get_db_connection()
            target = get_offset_by_seq(conn, author, book_title, seq)
            sid = get_id_by_seq(conn, author, book_title, seq)
            conn.close()
            if target is None or sid is None:
                ui.notify(f"문장 번호는 1 ~ {total} 범위여야 합니다.", type="warning")
                return
            while offset["value"] <= target and has_more["value"]:
                load_more()
            ui.run_javascript(
                f"var el = document.getElementById('sentence-{sid}'); "
                "if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });"
            )

        ui.button("이동", on_click=go_to_seq).props("unelevated")

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

    # 오른쪽 하단 Top 버튼
    def scroll_to_top():
        ui.run_javascript("window.scrollTo({ top: 0, behavior: 'smooth' });")

    ui.button("Top", on_click=scroll_to_top).props("round unelevated").classes(
        "fixed bottom-6 right-6 z-10 shadow-lg"
    ).style("position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 1000;")


def main():
    ui.run(
        title="철학 번역 뷰어",
        favicon="📖",
        storage_secret="philosophy-viewer-secret",
        host="0.0.0.0",   # Docker 컨테이너 외부 접근 허용
        port=int(os.environ.get("APP_PORT", 8080)),
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
