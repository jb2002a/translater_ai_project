# Translater AI Project

독일어 철학·학술 문헌을 PDF에서 추출하고, 전처리한 뒤 문장 단위로 DB에 저장하며, 필요 시 한국어로 번역하는 **LangGraph 기반 파이프라인** 프로젝트입니다.

고전 독일어 철학 텍스트의 OCR 품질 개선과 학술 번역에 최적화되어 있습니다.

---

## 개요

| 구분 | 내용 |
|------|------|
| **입력** | PDF 파일 경로, 저자명, 책/문헌 제목 |
| **전처리** | PDF 추출 → SoMaJo 문장 분리 → 배치 묶기 → LLM 정제(탈하이픈, 정서법, 노이즈 제거) → 문장 평탄화 → DB 저장 |
| **후처리(번역)** | DB에서 미번역 문장 조회 → Claude 번역 → DB 업데이트 (반복 루프) |

---

## 전체 플로우

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  전처리 (pre_process)                                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   [extract] → [chunking] → [re_chunking] → [cleanup] → [flatten_sentences]     │
│       │            │              │              │                │              │
│       ▼            ▼              ▼              ▼                ▼              │
│   raw_text    raw_chunks    batched_chunks  cleaned_batches  german_sentences   │
│   (PyMuPDF)   (SoMaJo)     (1.5만 토큰/배치)  (Gemini 병렬)   (SoMaJo 재분리)     │
│       │                                                              │          │
│       └──────────────────────────────────────────────────────────────┼──────────┘
│                                                                      ▼          │
│                                                              [save_db] → END    │
│                                                                  │              │
└──────────────────────────────────────────────────────────────────┼──────────────┘
                                                                   │
                                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  후처리 (post_process)                                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   [fetch_sentences] → [translate] → [save_translations] → [END]                 │
│          │                    │                    │                           │
│          ▼                    ▼                    ▼                           │
│   current_pk부터         Claude로            korean_sentence                    │
│   5000토큰 이내          문장별 번역           컬럼 업데이트                      │
│   미번역 문장 조회                                                               │
│                                                                                 │
│   ※ 미번역 문장이 남아 있으면 스크립트를 반복 실행하여 배치별 번역 진행           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 주요 노드 설명

### 전처리 (Pre-processing)

| 노드 | 설명 | 입력 → 출력 |
|------|------|-------------|
| **extract** | PyMuPDF로 PDF에서 텍스트 추출 | `pdf_path` → `raw_text` |
| **chunking** | SoMaJo로 독일어 문장 경계 분리 | `raw_text` → `raw_chunks` |
| **re_chunking** | LLM 호출용 1.5만 토큰 단위 배치 묶기 | `raw_chunks` → `batched_chunks` |
| **cleanup** | 청크별 병렬 Gemini 전처리 (탈하이픈, 정서법, 노이즈 제거) | `batched_chunks` → `cleaned_batches` |
| **flatten_sentences** | 정제된 배치를 SoMaJo로 재분리 후 문장 리스트 생성 | `cleaned_batches` → `german_sentences` |
| **save_db** | SQLite `processed_sentences` 테이블에 저장 | `german_sentences` → DB |

### 후처리 (Translation)

| 노드 | 설명 | 입력 → 출력 |
|------|------|-------------|
| **fetch_sentences** | `current_pk`부터 5000토큰 이내 문장 조회 | state → `pending_items`, `current_pk` |
| **translate** | Claude로 문장별 독일어→한국어 학술 번역 | `pending_items` → `translated_items` |
| **save_translations** | `korean_sentence` 컬럼 업데이트 | `translated_items` → DB |

---

## 프로젝트 구조

```
translater_ai_project/
├── main/
│   ├── TranslationState.py       # GraphState, PostTranslationState
│   ├── exceptions.py             # 예외 클래스
│   ├── read_db_sentences.py      # DB 문장 조회 스크립트 (id 1~100 출력)
│   ├── models/
│   │   └── models.py             # Gemini(전처리), Claude(번역) LLM 래퍼
│   ├── pre_process/
│   │   ├── graph.py              # 전처리 그래프 (create_preprocessing_workflow)
│   │   ├── node/
│   │   │   ├── ExtractNode.py
│   │   │   └── PreProcessingNode.py
│   │   ├── service/
│   │   │   ├── ExtractService.py
│   │   │   ├── SegmentService.py      # SoMaJo 문장 분리
│   │   │   ├── PreProcessingService.py
│   │   │   └── Utils.py
│   │   └── prompts/
│   │       └── prompts.py
│   └── post_process/
│       ├── graph.py              # 번역 그래프 (create_translation_workflow)
│       ├── node/
│       │   └── TranslateNode.py
│       ├── service/
│       │   ├── Initial_translate.py
│       │   └── TranslationDbService.py   # has_untranslated_sentences, fetch, save
│       └── prompts/
│           └── prompts.py
├── config.py                     # OS별 기본 PDF 경로 (DEFAULT_PDF_PATH)
├── requirements.txt
└── README.md
```

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| **오케스트레이션** | LangGraph (StateGraph) |
| **PDF** | PyMuPDF (`fitz`) |
| **문장 분리** | SoMaJo (독일어 `de_CMC`) |
| **전처리 LLM** | LangChain + Google Gemini 2.5 Flash |
| **번역 LLM** | LangChain + Anthropic Claude Sonnet 4.5 |
| **저장소** | SQLite (`philosophy_translation.db`) |

---

## 환경 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

주요 패키지: `langgraph`, `langchain-google-genai`, `langchain-anthropic`, `pymupdf`, `SoMaJo`, `python-dotenv`, `langsmith`

### 2. 환경 변수 (.env)

프로젝트 루트에 `.env` 파일 생성:

| 변수명 | 용도 |
|--------|------|
| `GOOGLE_API_KEY` | 전처리용 Gemini API |
| `ANTHROPIC_API_KEY` | 번역용 Claude API |
| `LANGCHAIN_TRACING_V2` | `true` 시 LangSmith 트레이싱 활성화 (선택) |
| `LANGSMITH_API_KEY` | LangSmith API 키 (선택) |

---

## 사용 방법

### 전처리만 실행 (PDF → DB)

```bash
python -m main.pre_process.graph
```

또는 코드에서:

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
```

전처리 실행 시 `flatten_sentences_top100.txt`에 `german_sentences` 샘플(인덱스 100~199, 100개)이 저장됨.

**경로 설정**: `config.py`에서 `DEFAULT_PDF_PATH` 수정. Windows: `D:\Pdf\test.pdf`, macOS: `/Users/leejaebin/Desktop/test.pdf`.

---

### 번역 실행 (DB → 한국어 저장)

```bash
python -m main.post_process.graph
```

스크립트 실행 시 `has_untranslated_sentences`로 미번역 문장 존재 여부를 확인한 뒤, `korean_sentence IS NULL` 조건의 문장을 id 순으로 5000토큰 단위 배치 번역함. 미번역 문장이 없으면 종료함.

```python
from main.post_process.graph import create_translation_workflow
from main.post_process.service.TranslationDbService import has_untranslated_sentences
import config

app = create_translation_workflow()
db_path = getattr(config, "DEFAULT_DB_PATH", "philosophy_translation.db")
author = "Dilthey, Wilhelm"
book_title = "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. ..."

if has_untranslated_sentences(db_path, author, book_title):
    initial_state = {
        "db_path": db_path,
        "author": author,
        "book_title": book_title,
    }
    app.invoke(initial_state)
```

---

### DB 문장 조회

```bash
python -m main.read_db_sentences
```

`processed_sentences` 테이블의 `id` 1~100 행을 조회하여 전체 컬럼을 콘솔에 출력함.

---

## 데이터베이스

- **파일**: `philosophy_translation.db` (프로젝트 루트)
- **테이블**: `processed_sentences`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER | PK, 자동 증가 |
| `pdf_path` | TEXT | 원본 PDF 경로 |
| `author` | TEXT | 저자명 |
| `book_title` | TEXT | 문헌 제목 |
| `german_sentence` | TEXT | 전처리된 독일어 문장 |
| `korean_sentence` | TEXT | 번역된 한국어 (후처리 시 업데이트) |
| `status` | TEXT | 기본값 `'pending'` |

---

## 라이선스 및 기여

저장소 설정에 따라 라이선스가 정해집니다. 이슈/PR로 기여를 제안할 수 있습니다.
