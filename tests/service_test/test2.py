import json
from pathlib import Path
from paddleocr import PPStructureV3

_tests_dir = Path(__file__).resolve().parent.parent
input_file = _tests_dir / "resources_test" / "sperated_small.pdf"
output_path = Path(__file__).resolve().parent / "results_test"
output_path.mkdir(parents=True, exist_ok=True)

pipeline = PPStructureV3(lang="de")
output = pipeline.predict(input=str(input_file))

markdown_list = []
footnote_data = []

for res in output:
    markdown_list.append(res.markdown)

    blocks = res.json["res"]["parsing_res_list"]

    number = next(
        (b["block_content"] for b in blocks if b["block_label"] == "number"),
        None
    )
    footnotes = [
        b["block_content"]
        for b in blocks
        if b["block_label"] == "footnote"
    ]

    if footnotes:
        footnote_data.append({"number": number, "footnote": footnotes})

# 본문 마크다운 저장
markdown_result = pipeline.concatenate_markdown_pages(markdown_list)
markdown_texts = markdown_result.markdown["markdown_texts"]

mkd_file_path = output_path / f"{input_file.stem}.md"
with open(mkd_file_path, "w", encoding="utf-8") as f:
    f.write(markdown_texts)

print(f"마크다운 저장 완료: {mkd_file_path}")

# footnote JSON 저장
json_file_path = output_path / f"{input_file.stem}_footnotes.json"
with open(json_file_path, "w", encoding="utf-8") as f:
    json.dump(footnote_data, f, ensure_ascii=False, indent=4)

print(f"각주 JSON 저장 완료: {json_file_path}")
