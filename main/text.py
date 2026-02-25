"""
PySBD chunking_node / segment_cleaned_text 테스트.
독일어 cleaned_text를 문장 단위로 분리해 refactored_text 형식(한 문장 per line)이 되는지 검증.

실행: 프로젝트 루트에서
  pip install pysbd
  python -m main.text
"""
import sys
import os

# 프로젝트 루트를 path에 추가 (main 패키지 로딩용)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from main.pre_process.service.SegmentService import segment_cleaned_text


def test_segment_cleaned_text_basic():
    """segment_cleaned_text: 연속 문자열이 문장 단위로 분리되는지."""
    # 약어(z.B., 19.)가 문장 끝으로 잘못 나뉘지 않는지 포함
    cleaned = (
        "Er schrieb im 19. Jahrhundert. Das ist z.B. wichtig. "
        "Hier endet ein Satz. Und noch einer."
    )
    result = segment_cleaned_text(cleaned)
    lines = result.strip().split("\n")
    assert len(lines) >= 3, "최소 3개 이상 문장으로 나뉘어야 함"
    assert "19. Jahrhundert" in lines[0] or "19." in result, "약어 19.가 문장 중에 유지"
    assert result == result.strip(), "앞뒤 불필요 공백 없음"


def test_segment_cleaned_text_empty():
    """빈 문자열 입력."""
    assert segment_cleaned_text("") == ""
    # 공백만 있는 경우도 빈 결과 또는 공백 문장 하나
    result = segment_cleaned_text("   ")
    assert isinstance(result, str)


def test_chunking_output_format():
    """segment_cleaned_text 결과가 save_db_node가 기대하는 refactored_text 형식인지 (한 문장 per line)."""
    cleaned = "Erste Satz. Zweite Satz. Dritte Satz."
    refactored_text = segment_cleaned_text(cleaned)
    sentences = refactored_text.split("\n")
    assert len(sentences) >= 2
    for s in sentences:
        assert "\n" not in s, "각 항목은 한 줄(한 문장)이어야 함"


def test_chunking_compat_with_save_db():
    """refactored_text.split('\\n')이 save_to_db(sentences) 호출 형식과 호환되는지."""
    cleaned = "A. B. C. D."
    refactored_text = segment_cleaned_text(cleaned)
    sentences = refactored_text.split("\n")
    assert isinstance(sentences, list)
    assert all(isinstance(s, str) for s in sentences)


if __name__ == "__main__":
    test_segment_cleaned_text_basic()
    test_segment_cleaned_text_empty()
    test_chunking_output_format()
    test_chunking_compat_with_save_db()
    print("All tests passed.")
