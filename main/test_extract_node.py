"""
ExtractNode → ChunkingNode → ReChunkingNode → CleanupNode 연결 테스트 스크립트.
pdf_path로 extract_node → chunking_node → re_chunking_node → cleanup_node를 순서대로 호출하고,
raw_text·raw_chunks·batched_chunks·cleaned_batches 결과를 출력합니다.
"""
from pathlib import Path
import sys

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
import config

from main.TranslationState import GraphState
from main.pre_process.node.ExtractNode import extract_node
from main.pre_process.node.PreProcessingNode import chunking_node, re_chunking_node, cleanup_node

SHOW_TOP_CHUNKS = 30
SHOW_TOP_BATCHES = 10
OUTPUT_FILE = _root / "test_extract_node_result.txt"


def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else config.DEFAULT_PDF_PATH
    path = Path(pdf_path)
    if not path.exists():
        print(f"[오류] PDF 파일을 찾을 수 없습니다: {pdf_path}")
        print("사용법: python -m main.test_extract_node [PDF경로]")
        print("        인자 없으면 config.DEFAULT_PDF_PATH 사용")
        sys.exit(1)

    state: GraphState = {"pdf_path": str(path.resolve())}
    print(f"[테스트] pdf_path: {state['pdf_path']}")

    # 1) extract_node
    state = {**state, **extract_node(state)}
    raw_text = state.get("raw_text", "")

    # 2) chunking_node
    state = {**state, **chunking_node(state)}
    raw_chunks = state.get("raw_chunks", [])

    # 3) re_chunking_node
    state = {**state, **re_chunking_node(state)}
    batched_chunks = state.get("batched_chunks", [])

    # 4) cleanup_node
    state = {**state, **cleanup_node(state)}
    cleaned_batches = state.get("cleaned_batches", [])

    # 텍스트 파일로 저장 (문장 잘림 없이 전체 기록)
    lines = [
        f"pdf_path: {state['pdf_path']}",
        "",
        "[1/4 ExtractNode] raw_text",
        f"길이: {len(raw_text)} 자",
        "-" * 60,
        "",
        f"[2/4 ChunkingNode] raw_chunks 개수: {len(raw_chunks)}",
        "-" * 60,
    ]
    for i, chunk in enumerate(raw_chunks[:SHOW_TOP_CHUNKS], 1):
        lines.append("")
        lines.append("=" * 50)
        lines.append(f"청크 {i} / {min(SHOW_TOP_CHUNKS, len(raw_chunks))}")
        lines.append("=" * 50)
        lines.append(chunk)
    if len(raw_chunks) > SHOW_TOP_CHUNKS:
        lines.append(f"... (이하 생략, 총 {len(raw_chunks)}개)")
    # 청크 끝 \\n 여부 요약 (마지막 청크만 \\n 없음)
    lines.append("-" * 60)
    lines.append("[청크 끝 \\n 여부] (끝 3자 repr)")
    for i, chunk in enumerate(raw_chunks[:SHOW_TOP_CHUNKS], 1):
        tail = repr(chunk[-3:]) if len(chunk) >= 3 else repr(chunk)
        has_nl = "있음" if chunk.endswith("\n") else "없음"
        lines.append(f"  청크 {i}: {has_nl}  끝 3자 = {tail}")
    total = len(raw_chunks)
    if total > SHOW_TOP_CHUNKS:
        last_chunk = raw_chunks[-1]
        has_nl = "있음" if last_chunk.endswith("\n") else "없음"
        lines.append(f"  청크 {total} (전체 마지막): {has_nl}  끝 3자 = {repr(last_chunk[-3:])}")

    # [3/4 ReChunkingNode] batched_chunks
    lines.append("")
    lines.append(f"[3/4 ReChunkingNode] batched_chunks 배치 개수: {len(batched_chunks)}")
    lines.append("-" * 60)
    for b, batch in enumerate(batched_chunks[:SHOW_TOP_BATCHES], 1):
        lines.append(f"  배치 {b}: 청크 {len(batch)}개")
        if batch:
            preview = batch[0][:80].replace("\n", " ") + ("..." if len(batch[0]) > 80 else "")
            lines.append(f"    첫 청크 미리보기: {preview}")
    if len(batched_chunks) > SHOW_TOP_BATCHES:
        lines.append(f"  ... (이하 생략, 총 {len(batched_chunks)}개 배치)")
    # ReChunkingNode 배치별 청크 끝 \n 여부
    lines.append("-" * 60)
    lines.append("[ReChunkingNode 배치별 청크 끝 \\n 여부] (끝 3자 repr)")
    for b, batch in enumerate(batched_chunks[:SHOW_TOP_BATCHES], 1):
        lines.append(f"  배치 {b} (청크 {len(batch)}개):")
        show_per_batch = min(10, len(batch))
        for i, chunk in enumerate(batch[:show_per_batch], 1):
            tail = repr(chunk[-3:]) if len(chunk) >= 3 else repr(chunk)
            has_nl = "있음" if chunk.endswith("\n") else "없음"
            lines.append(f"    청크 {i}: {has_nl}  끝 3자 = {tail}")
        if len(batch) > show_per_batch:
            last_chunk = batch[-1]
            tail = repr(last_chunk[-3:]) if len(last_chunk) >= 3 else repr(last_chunk)
            has_nl = "있음" if last_chunk.endswith("\n") else "없음"
            lines.append(f"    ... 청크 {len(batch)} (배치 마지막): {has_nl}  끝 3자 = {tail}")

    # [4/4 CleanupNode] cleaned_batches
    lines.append("")
    lines.append(f"[4/4 CleanupNode] cleaned_batches 배치 개수: {len(cleaned_batches)}")
    lines.append("-" * 60)
    for b, batch in enumerate(cleaned_batches[:SHOW_TOP_BATCHES], 1):
        lines.append(f"  배치 {b}: 청크 {len(batch)}개")
        if batch:
            preview = batch[0][:80].replace("\n", " ") + ("..." if len(batch[0]) > 80 else "")
            lines.append(f"    첫 청크 미리보기: {preview}")
    if len(cleaned_batches) > SHOW_TOP_BATCHES:
        lines.append(f"  ... (이하 생략, 총 {len(cleaned_batches)}개 배치)")
    # CleanupNode 배치별 청크 끝 \n 여부
    lines.append("-" * 60)
    lines.append("[CleanupNode 배치별 청크 끝 \\n 여부] (끝 3자 repr)")
    for b, batch in enumerate(cleaned_batches[:SHOW_TOP_BATCHES], 1):
        lines.append(f"  배치 {b} (청크 {len(batch)}개):")
        show_per_batch = min(10, len(batch))
        for i, chunk in enumerate(batch[:show_per_batch], 1):
            tail = repr(chunk[-3:]) if len(chunk) >= 3 else repr(chunk)
            has_nl = "있음" if chunk.endswith("\n") else "없음"
            lines.append(f"    청크 {i}: {has_nl}  끝 3자 = {tail}")
        if len(batch) > show_per_batch:
            last_chunk = batch[-1]
            tail = repr(last_chunk[-3:]) if len(last_chunk) >= 3 else repr(last_chunk)
            has_nl = "있음" if last_chunk.endswith("\n") else "없음"
            lines.append(f"    ... 청크 {len(batch)} (배치 마지막): {has_nl}  끝 3자 = {tail}")
    lines.append("-" * 60)
    lines.append("[완료] ExtractNode → ChunkingNode → ReChunkingNode → CleanupNode 테스트 끝.")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"결과 저장: {OUTPUT_FILE}")
    print(f"  raw_text {len(raw_text)}자, raw_chunks {len(raw_chunks)}개, batched_chunks {len(batched_chunks)}개, cleaned_batches {len(cleaned_batches)}개 배치 (상위 {SHOW_TOP_CHUNKS}개 청크·{SHOW_TOP_BATCHES}개 배치 저장)")


if __name__ == "__main__":
    main()
