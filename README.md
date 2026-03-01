# Translater AI Project

독일어 철학·학술 문헌을 PDF에서 추출하고, 전처리한 뒤 문장 단위로 DB에 저장하며, 필요 시 한국어로 번역하는 **LangGraph 기반 파이프라인** 프로젝트입니다.

---

## 개요

- **입력**: PDF 파일 경로, 저자명, 책/문헌 제목
- **처리**: PDF 텍스트 추출 → 문장 단위 청킹(PySBD) → 청크별 LLM 전처리(탈하이픈, 정서법, 노이즈 제거) → SQLite DB 저장
- **선택**: 저장된 문장을 DB에서 읽어 독일어→한국어 학술 번역(Anthropic Claude)

고전 독일어 철학 텍스트의 OCR 품질 개선과 번역 준비에 최적화되어 있습니다.

---

## 주요 기능

| 단계 | 설명 |
|------|------|
| **Extract** | PyMuPDF(fitz)로 PDF에서 텍스트 추출 |
| **Chunking** | PySBD로 독일어 문장 경계 분리(청크 리스트 생성) |
| **Cleanup** | 청크별 병렬 LLM 전처리(탈하이픈, 정서법, 메타데이터·노이즈 제거) |
| **Save DB** | `processed_sentences` 테이블에 문장 단위 저장 |
| **Translation** | DB/텍스트 기반으로 Claude를 이용한 한국어 번역( post_process ) |

---

## 프로젝트 구조

```
translater_ai_project/
├── main/
│   ├── TranslationState.py     # GraphState(전처리), PostTranslationState(후처리)
│   ├── models/
│   │   └── models.py           # LLM 래퍼 (Google Gemini: 전처리, Anthropic Claude: 번역)
│   ├── pre_process/
│   │   ├── graph.py            # 전처리 그래프 (create_preprocessing_workflow)
│   │   ├── node/
│   │   │   ├── ExtractNode.py      # PDF → raw_text
│   │   │   └── PreProcessingNode.py # chunking_node, cleanup_node, save_db_node
│   │   ├── service/
│   │   │   ├── ExtractService.py   # PDF 텍스트 추출 (PyMuPDF)
│   │   │   ├── SegmentService.py   # SoMaJo 문장 분리 (독일어)
│   │   │   ├── PreProcessingService.py # 청크별 LLM 전처리, DB 저장
│   │   │   └── Utils.py            # DB 읽기, 텍스트 파일 출력
│   │   └── prompts/
│   │       └── prompts.py      # 독일어 OCR 복원/정리 프롬프트
│   └── post_process/
│       ├── graph.py            # 후처리 그래프 (create_translation_workflow)
│       ├── Initial_translate.py # 문장별 한국어 번역 (Claude)
│       ├── prompts.py          # 번역용 시스템 프롬프트
│       └── ToolsForList.py     # 리스트/문장 처리 유틸
├── test.py                     # extract + chunking 워크플로우 테스트
├── requirements.txt
└── README.md
```

---

## 기술 스택

- **오케스트레이션**: LangGraph (StateGraph)
- **PDF**: PyMuPDF (`fitz`)
- **문장 분리**: SoMaJo (독일어)
- **LLM**: LangChain (Google Gemini 2.5 Flash – 전처리, Anthropic Claude – 번역)
- **저장소**: SQLite (`philosophy_translation.db`)

---

## 환경 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

코드에서 사용하는 패키지 예시(필요 시 추가 설치):

- `langgraph`
- `langchain-google-genai`, `langchain-anthropic`, `langchain-core`
- `pymupdf` (fitz)
- `SoMaJo`
- `python-dotenv`

### 2. 환경 변수 (.env)

프로젝트 루트에 `.env` 파일을 두고 다음 키를 설정합니다.

| 변수명 | 용도 |
|--------|------|
| `GOOGLE_API_KEY` | 전처리용 Gemini API |
| `ANTHROPIC_API_KEY` | 번역용 Claude API |

---

## 사용 방법

### 전처리 파이프라인만 실행 (PDF → DB)

전처리 전용 그래프: `main/pre_process/graph.py`

**실행**: `python -m main.pre_process.graph`

**경로 설정**: Windows의 D: 드라이브(보조장치 x31)는 Mac에서 `/Volumes/x31/`로 마운트됩니다. 기본 PDF 경로는 `config.py`에서 OS별로 설정됩니다 (Windows: `D:\Pdf\test.pdf`, macOS: `/Volumes/x31/Pdf/test.pdf`). 다른 경로는 `config.DEFAULT_PDF_PATH`를 수정하거나 실행 시 `pdf_path`를 넘기면 됩니다.

```python
import config
from main.pre_process.graph import create_preprocessing_workflow

app = create_preprocessing_workflow()
initial_state = {
    "pdf_path": config.DEFAULT_PDF_PATH,
    "author": "Dilthey, Wilhelm",
    "book_title": "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. ...",
    "db_path": "philosophy_translation.db",
}
final_output = app.invoke(initial_state)
print(final_output.get("german_sentences", [])[:5])
```

### 후처리(번역) 파이프라인 실행 (DB → 번역 저장)

```bash
python -m main.post_process.graph
```

또는 `from main.post_process.graph import create_translation_workflow`

### extract + chunking만 테스트

```bash
python test.py
```

`test.py`는 PDF 추출 후 PySBD 청킹까지만 수행해 문장 분리 결과를 확인합니다.

### DB에서 문장 읽기

`main/pre_process/service/Utils.py`의 `read_from_db(db_path)`로 `processed_sentences`의 `german_sentence` 목록을 가져올 수 있습니다. 이 데이터를 `post_process/Initial_translate.py`의 `initial_translate(text, author, book_title)` 등과 연동해 번역할 수 있습니다.

---

## 데이터베이스

- **파일**: `philosophy_translation.db` (프로젝트 루트 기준)
- **테이블**: `processed_sentences`
  - `id`, `pdf_path`, `author`, `book_title`, `german_sentence`, `status` (기본값 `'pending'`)

---

## 워크플로우 요약

```
[extract] → [chunking] → [cleanup] → [save_db] → END
```

1. **extract**: `pdf_path`로 PDF 열어 `raw_text` 생성  
2. **chunking**: `raw_text`를 PySBD로 문장 단위 `raw_chunks` 리스트로 분리  
3. **cleanup**: `raw_chunks`를 청크별로 병렬 LLM 전처리 후 `sentences` 리스트로 정리  
4. **save_db**: `pdf_path`, `author`, `book_title`, `sentences`를 DB에 저장  

전처리 프롬프트는 독일어 OCR 복원(탈하이픈, 정서법, 메타데이터·노이즈 제거, 한 줄 연속 텍스트 출력)에 맞춰져 있습니다.

---

## 라이선스 및 기여

저장소 설정에 따라 라이선스가 정해집니다. 기여는 이슈/PR로 제안할 수 있습니다.
