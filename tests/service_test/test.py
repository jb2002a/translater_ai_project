from pathlib import Path
from paddleocr import PPStructureV3

# 프로젝트 루트 기준 경로 (실행 위치에 무관하게 동작)
_tests_dir = Path(__file__).resolve().parent.parent
input_file = _tests_dir / "resoruces_test" / "test_seperated.pdf"
output_path = Path(__file__).resolve().parent / "results_test"

pipeline = PPStructureV3()
output = pipeline.predict(input=str(input_file))

markdown_list = []
markdown_images = []

for res in output:
    md_info = res.markdown
    markdown_list.append(md_info)
    markdown_images.append(md_info.get("markdown_images", {}))

markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)

mkd_file_path = output_path / f"{input_file.stem}.md"
mkd_file_path.parent.mkdir(parents=True, exist_ok=True)

with open(mkd_file_path, "w", encoding="utf-8") as f:
    f.write(markdown_texts)

for item in markdown_images:
    if item:
        for path, image in item.items():
            file_path = output_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(file_path)