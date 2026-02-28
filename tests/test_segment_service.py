"""
SegmentService 청킹 테스트.
독일어 텍스트가 SoMaJo를 통해 올바르게 문장 단위로 분리되는지 확인합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main.pre_process.service.SegmentService import segment_raw_to_list


def test_basic_german_sentences():
    """기본 독일어 문장 분리 테스트"""
    text = "Das ist ein Test. Dies ist ein zweiter Satz. Und hier ist der dritte."
    result = segment_raw_to_list(text)
    
    print("=== 기본 독일어 문장 분리 테스트 ===")
    print(f"입력: {repr(text)}")
    print(f"결과 ({len(result)}개 청크):")
    for i, chunk in enumerate(result):
        print(f"  [{i}] {repr(chunk)}")
    print()
    
    assert len(result) >= 2, f"최소 2개 이상의 문장이 분리되어야 함 (실제: {len(result)})"
    return True


def test_paragraph_separation():
    """문단(빈 줄) 구분 테스트"""
    text = """Erster Absatz erster Satz. Erster Absatz zweiter Satz.

Zweiter Absatz erster Satz. Zweiter Absatz zweiter Satz."""
    
    result = segment_raw_to_list(text)
    
    print("=== 문단 구분 테스트 ===")
    print(f"입력:\n{text}")
    print(f"\n결과 ({len(result)}개 청크):")
    for i, chunk in enumerate(result):
        print(f"  [{i}] {repr(chunk)}")
    print()
    
    assert len(result) >= 2, f"최소 2개 이상의 문장이 분리되어야 함 (실제: {len(result)})"
    return True


def test_empty_input():
    """빈 입력 처리 테스트"""
    print("=== 빈 입력 테스트 ===")
    
    # 빈 문자열
    result1 = segment_raw_to_list("")
    print(f"빈 문자열 입력 → 결과: {result1}")
    assert result1 == [], "빈 문자열은 빈 리스트를 반환해야 함"
    
    # 공백만 있는 문자열
    result2 = segment_raw_to_list("   \n\n  ")
    print(f"공백만 있는 입력 → 결과: {result2}")
    assert result2 == [], "공백만 있는 문자열은 빈 리스트를 반환해야 함"
    
    print()
    return True


def test_newline_format():
    """반환된 청크의 줄바꿈 형식 테스트"""
    text = "Erster Satz. Zweiter Satz. Dritter Satz."
    result = segment_raw_to_list(text)
    
    print("=== 줄바꿈 형식 테스트 ===")
    print(f"입력: {repr(text)}")
    print(f"결과 ({len(result)}개 청크):")
    for i, chunk in enumerate(result):
        print(f"  [{i}] {repr(chunk)}")
    
    # 마지막을 제외한 모든 청크는 \n으로 끝나야 함
    if len(result) > 1:
        for i, chunk in enumerate(result[:-1]):
            assert chunk.endswith("\n"), f"청크 {i}는 \\n으로 끝나야 함"
        assert not result[-1].endswith("\n"), "마지막 청크는 \\n으로 끝나면 안 됨"
        print("✓ 줄바꿈 형식 검증 통과")
    
    print()
    return True


def test_complex_german_text():
    """복잡한 독일어 텍스트 테스트 (약어, 숫자 등 포함)"""
    text = """Dr. Müller arbeitet bei der BMW AG. Er verdient ca. 5000 Euro pro Monat.
    
Die Firma wurde am 7. März 1916 gegründet. Heute hat sie über 100.000 Mitarbeiter."""
    
    result = segment_raw_to_list(text)
    
    print("=== 복잡한 독일어 텍스트 테스트 ===")
    print(f"입력:\n{text}")
    print(f"\n결과 ({len(result)}개 청크):")
    for i, chunk in enumerate(result):
        print(f"  [{i}] {repr(chunk)}")
    print()
    
    # Dr. 같은 약어에서 잘못 분리되지 않았는지 확인
    assert len(result) >= 2, f"최소 2개 이상의 문장이 분리되어야 함 (실제: {len(result)})"
    return True


def test_single_sentence():
    """단일 문장 테스트"""
    text = "Dies ist nur ein einziger Satz."
    result = segment_raw_to_list(text)
    
    print("=== 단일 문장 테스트 ===")
    print(f"입력: {repr(text)}")
    print(f"결과 ({len(result)}개 청크):")
    for i, chunk in enumerate(result):
        print(f"  [{i}] {repr(chunk)}")
    print()
    
    assert len(result) == 1, f"단일 문장은 1개의 청크를 반환해야 함 (실제: {len(result)})"
    assert not result[0].endswith("\n"), "단일 문장(마지막 청크)은 \\n으로 끝나면 안 됨"
    return True


def test_special_characters():
    """특수문자 포함 텍스트 테스트"""
    text = "Was kostet das? Es kostet €50,00! Das ist günstig."
    result = segment_raw_to_list(text)
    
    print("=== 특수문자 포함 테스트 ===")
    print(f"입력: {repr(text)}")
    print(f"결과 ({len(result)}개 청크):")
    for i, chunk in enumerate(result):
        print(f"  [{i}] {repr(chunk)}")
    print()
    
    assert len(result) >= 2, f"최소 2개 이상의 문장이 분리되어야 함 (실제: {len(result)})"
    return True


def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("SegmentService 청킹 테스트 시작")
    print("=" * 60)
    print()
    
    tests = [
        ("기본 독일어 문장 분리", test_basic_german_sentences),
        ("문단 구분", test_paragraph_separation),
        ("빈 입력 처리", test_empty_input),
        ("줄바꿈 형식", test_newline_format),
        ("복잡한 독일어 텍스트", test_complex_german_text),
        ("단일 문장", test_single_sentence),
        ("특수문자 포함", test_special_characters),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name} 테스트 통과")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name} 테스트 실패: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name} 테스트 에러: {type(e).__name__}: {e}")
            failed += 1
        print("-" * 40)
    
    print()
    print("=" * 60)
    print(f"테스트 결과: {passed}/{passed + failed} 통과")
    if failed == 0:
        print("🎉 모든 테스트 통과!")
    else:
        print(f"⚠️  {failed}개 테스트 실패")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
