"""markdown_result 객체의 타입·속성을 확인하기 위한 디버그 스크립트 (test2.py와 동일한 로직)."""
from pathlib import Path
from paddleocr import PPStructureV3

_tests_dir = Path(__file__).resolve().parent.parent
input_file = _tests_dir / "resources_test" / "sperated_small.pdf"

pipeline = PPStructureV3(lang="de")
output = pipeline.predict(input=str(input_file))

markdown_list = []
for res in output:
    markdown_list.append(res.markdown)

# test2.py와 동일: concatenate_markdown_pages 호출
markdown_result = pipeline.concatenate_markdown_pages(markdown_list)

# --- markdown_result 형식만 출력 ---
print("=== type ===")
print(type(markdown_result))
print()

print("=== dir(markdown_result) (public 속성/메서드) ===")
for name in sorted(dir(markdown_result)):
    if not name.startswith("_"):
        print(f"  {name}")
print()

print("=== __dict__ (있을 경우) ===")
if hasattr(markdown_result, "__dict__"):
    for k, v in markdown_result.__dict__.items():
        val_preview = repr(v)[:80] + ("..." if len(repr(v)) > 80 else "")
        print(f"  {k}: {val_preview}")
else:
    print("  (없음)")
print()

# 일반적으로 있을 수 있는 이름들로 값 미리보기
for attr in ("markdown_texts", "markdown", "text", "content", "result", "concatenated"):
    if hasattr(markdown_result, attr):
        val = getattr(markdown_result, attr)
        preview = repr(val)[:120] + ("..." if len(repr(val)) > 120 else "")
        print(f"  markdown_result.{attr} = {preview}")
