# Marker를 사용한 PDF → 텍스트(마크다운) 추출 서비스.
# PyMuPDF 대신 Marker를 사용해 테이블·수식·레이아웃 보존이 필요한 경우 활용.

import sys
from pathlib import Path

# 스크립트로 직접 실행할 때 패키지 루트를 path에 추가 (상대 import 대신 main.* 사용 가능하게)
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

from main.exceptions import InvalidPdfError


def extract_text(doc_path: str | Path) -> str:
    """
    Marker를 사용해 PDF에서 텍스트(마크다운)를 추출합니다.
    테이블·수식·멀티컬럼 등 복잡한 레이아웃에 강합니다.

    Args:
        doc_path: PDF 파일 경로

    Returns:
        전체 텍스트(마크다운)

    Raises:
        InvalidPdfError: PDF 열기/변환 실패 시
    """
    doc_path = Path(doc_path)
    if not doc_path.exists():
        raise InvalidPdfError(f"PDF 파일 없음: {doc_path}")

    try:
        converter = PdfConverter(artifact_dict=create_model_dict())
        rendered = converter(str(doc_path))
        text, _, _ = text_from_rendered(rendered)
        if text is None:
            text = ""
        return text
    except InvalidPdfError:
        raise
    except Exception as e:
        raise InvalidPdfError(f"Marker PDF 변환 실패: {doc_path}", cause=e) from e


# --- 파일에서 바로 테스트할 때만 실행 ---
if __name__ == "__main__":
    # 사용법: python -m main.pre_process.service.ExtractServiceMarker [PDF경로]
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not pdf_path or not Path(pdf_path).exists():
        print("사용법: python -m main.pre_process.service.ExtractServiceMarker <PDF경로>")
        print("예: python -m main.pre_process.service.ExtractServiceMarker ./sample.pdf")
        sys.exit(1)

    print(f"Marker 추출 테스트: {pdf_path}\n")
    try:
        text = extract_text(pdf_path)
        print(f"--- 추출된 텍스트 (처음 2000자) ---\n{text[:2000]}")
        if len(text) > 2000:
            print(f"\n... (총 {len(text)}자)")
        else:
            print(f"\n(총 {len(text)}자)")
    except InvalidPdfError as e:
        print(f"오류: {e}")
        sys.exit(1)
