"""
DB의 author, book_title별 번역 문장을 1:1 대응 PDF로 내보내는 클래스.
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ..exceptions import DatabaseError, FileWriteError


def _register_fonts() -> None:
    """한글 폰트 등록 (시스템 기본 폰트 사용, 실패 시 스킵)."""
    try:
        # Windows 맑은 고딕
        pdfmetrics.registerFont(
            TTFont("Malgun", "C:/Windows/Fonts/malgun.ttf")
        )
    except Exception:
        try:
            # Windows 굴림
            pdfmetrics.registerFont(
                TTFont("Gulim", "C:/Windows/Fonts/gulim.ttc")
            )
        except Exception:
            pass


def _get_internal_name() -> str:
    """등록된 한글 폰트 내부 이름 반환."""
    for name in ("Malgun", "Gulim"):
        if name in pdfmetrics.getRegisteredFontNames():
            return name
    return "Helvetica"


class TranslationPdfExporter:
    """
    philosophy_translation.db에서 author, book_title 기준으로
    german_sentence / korean_sentence를 조회해 1:1 대응 PDF를 생성한다.
    """

    def __init__(self, db_path: str):
        """
        Args:
            db_path: SQLite DB 파일 경로 (processed_sentences 테이블)
        """
        self.db_path = Path(db_path)
        if not self.db_path.is_file():
            raise FileNotFoundError(f"DB 파일을 찾을 수 없습니다: {db_path}")
        _register_fonts()
        self._font_name = _get_internal_name()

    def fetch_books(self) -> List[Tuple[str, str]]:
        """
        DB에 있는 (author, book_title) 목록을 id 순서와 동일한 그룹 기준으로 반환.

        Returns:
            [(author, book_title), ...]
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT author, book_title
                    FROM processed_sentences
                    GROUP BY author, book_title
                    ORDER BY author, book_title
                    """
                )
                return cur.fetchall()
        except sqlite3.Error as e:
            raise DatabaseError(f"DB 조회 실패: {self.db_path}", cause=e) from e

    def fetch_sentences(
        self, author: str, book_title: str
    ) -> List[Tuple[str, str]]:
        """
        해당 author, book_title의 모든 문장 쌍을 id 순으로 반환.

        Returns:
            [(german_sentence, korean_sentence), ...]
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT german_sentence, korean_sentence
                    FROM processed_sentences
                    WHERE author = ? AND book_title = ?
                    ORDER BY id
                    """,
                    (author, book_title),
                )
                rows = cur.fetchall()
                return [
                    (g or "", k or "") for g, k in rows
                ]
        except sqlite3.Error as e:
            raise DatabaseError(f"DB 조회 실패: {self.db_path}", cause=e) from e

    def _build_styles(self, font_name: str) -> dict:
        """PDF용 Paragraph 스타일 dict 생성."""
        styles = getSampleStyleSheet()
        body = ParagraphStyle(
            name="BilingualBody",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=14,
            spaceAfter=6,
            wordWrap="CJK",
        )
        title = ParagraphStyle(
            name="BilingualTitle",
            parent=styles["Heading1"],
            fontName=font_name,
            fontSize=14,
            spaceAfter=12,
            wordWrap="CJK",
        )
        return {
            "body": body,
            "title": title,
        }

    def _escape(self, text: str) -> str:
        """XML/HTML 특수문자 이스케이프 (Paragraph용)."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def generate_pdf(
        self,
        output_path: Optional[str] = None,
        author: Optional[str] = None,
        book_title: Optional[str] = None,
    ) -> str:
        """
        author, book_title 기준으로 데이터를 가져와 1:1 대응 PDF를 생성한다.

        - author, book_title을 모두 지정하면 해당 책 하나만 PDF로 만든다.
        - 둘 다 None이면 DB에 있는 모든 (author, book_title)에 대해
          output_path가 디렉터리면 그 안에 책별 PDF를 생성하고,
          파일 경로면 단일 PDF에 모든 책을 순서대로 합친다.

        Args:
            output_path: 저장 경로 (파일 또는 디렉터리). None이면 현재 디렉터리.
            author: 저자 (None이면 전체)
            book_title: 책 제목 (None이면 전체)

        Returns:
            생성된 PDF 파일 경로(단일) 또는 첫 번째 생성 파일 경로(여러 책일 때).
        """
        output_path = Path(output_path or ".")
        styles = self._build_styles(self._font_name)

        if author is not None and book_title is not None:
            # 단일 책
            pairs = self.fetch_sentences(author, book_title)
            if not pairs:
                raise DatabaseError(
                    f"해당 조건에 맞는 문장이 없습니다: author={author!r}, book_title={book_title!r}"
                )
            if output_path.suffix.lower() != ".pdf":
                output_path = output_path / f"{author}_{book_title[:50]}.pdf".replace(
                    "/", "_"
                )
            return self._write_single_pdf(
                output_path, [(author, book_title, pairs)], styles
            )

        # 전체 책
        books = self.fetch_books()
        if not books:
            raise DatabaseError("DB에 (author, book_title) 데이터가 없습니다.")

        if output_path.suffix.lower() == ".pdf":
            # 한 파일에 모든 책
            all_data = []
            for a, t in books:
                pairs = self.fetch_sentences(a, t)
                all_data.append((a, t, pairs))
            return self._write_single_pdf(output_path, all_data, styles)

        # 디렉터리: 책별 PDF
        output_path.mkdir(parents=True, exist_ok=True)
        first_path = None
        for a, t in books:
            safe_name = f"{a}_{t[:50]}.pdf".replace("/", "_").replace("\\", "_")
            out_file = output_path / safe_name
            path = self._write_single_pdf(out_file, [(a, t, self.fetch_sentences(a, t))], styles)
            if first_path is None:
                first_path = path
        return first_path or str(output_path)

    def _write_single_pdf(
        self,
        output_path: Path,
        books_data: List[Tuple[str, str, List[Tuple[str, str]]]],
        styles: dict,
    ) -> str:
        """한 개의 PDF 파일에 책(들) 내용을 쓴다."""
        try:
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                leftMargin=20 * mm,
                rightMargin=20 * mm,
                topMargin=15 * mm,
                bottomMargin=15 * mm,
            )
            story = []

            for author, book_title, pairs in books_data:
                story.append(
                    Paragraph(
                        f"<b>{self._escape(author)}</b><br/>{self._escape(book_title)}",
                        styles["title"],
                    )
                )
                story.append(Spacer(1, 6 * mm))

                for i, (german, korean) in enumerate(pairs, 1):
                    story.append(
                        Paragraph(
                            f'<b>[{i}]</b> DE: {self._escape(german)}',
                            styles["body"],
                        )
                    )
                    story.append(
                        Paragraph(
                            self._escape(korean),
                            styles["body"],
                        )
                    )
                    story.append(Spacer(1, 4 * mm))

                if (author, book_title) != books_data[-1][:2]:
                    story.append(PageBreak())

            doc.build(story)
            return str(output_path.resolve())
        except OSError as e:
            raise FileWriteError(f"PDF 저장 실패: {output_path}", cause=e) from e
        except Exception as e:
            raise FileWriteError(f"PDF 생성 중 오류: {output_path}", cause=e) from e


# --- Wilhelm Dilthey, Einleitung in die Geisteswissenschaften 전용 ---
# DB에 저장된 author/book_title과 동일해야 함.
DILTHEY_AUTHOR = "Wilhelm Dilthey"
DILTHEY_BOOK_TITLE = "Einleitung in die Geisteswissenschaften"


class DiltheyEinleitungPdfExport:
    """
    TranslationPdfExporter를 사용해
    Wilhelm Dilthey, Einleitung in die Geisteswissenschaften만 PDF로 내보낸다.
    """

    def __init__(self, db_path: str):
        self._exporter = TranslationPdfExporter(db_path)
        self.author = DILTHEY_AUTHOR
        self.book_title = DILTHEY_BOOK_TITLE

    def run(self, output_path: Optional[str] = None) -> str:
        """
        해당 책만 PDF로 생성한다.

        Args:
            output_path: PDF 저장 경로. None이면 현재 디렉터리에
                'Dilthey_Einleitung_Geisteswissenschaften.pdf' 로 저장.

        Returns:
            생성된 PDF 파일 경로.
        """
        if output_path is None:
            output_path = "Dilthey_Einleitung_Geisteswissenschaften.pdf"
        return self._exporter.generate_pdf(
            output_path=output_path,
            author=self.author,
            book_title=self.book_title,
        )


if __name__ == "__main__":
    from pathlib import Path

    project_root = Path(__file__).resolve().parent.parent.parent
    db_path = project_root / "philosophy_translation.db"
    out_path = project_root / "Dilthey_Einleitung_Geisteswissenschaften.pdf"

    exporter = DiltheyEinleitungPdfExport(str(db_path))
    path = exporter.run(str(out_path))
    print(f"PDF 생성 완료: {path}")
