# Translater AI Project

독일어 철학·학술 문헌을 PDF에서 추출하고, 전처리한 뒤 문장 단위로 DB에 저장하며, 필요 시 한국어로 번역하는 **LangGraph 기반 파이프라인** 프로젝트입니다.

고전 독일어 철학 텍스트의 OCR 품질 개선과 학술 번역에 최적화되어 있으며, **NiceGUI 웹 뷰어**로 DB 탐색·PDF 업로드·번역을 수행하고, **PDF 내보내기**로 독일어–한국어 1:1 대응 PDF를 생성할 수 있습니다.

---

## 개요

| 구분 | 내용 |
|------|------|
| **입력** | PDF 파일 경로, 저자명, 책/문헌 제목 |
| **전처리** | PDF 추출 → SoMaJo 문장 분리 → 1.5만 토큰 배치 묶기 → Gemini 전처리(탈하이픈, 정서법, 노이즈 제거) → SoMaJo 재분리 → DB 저장 |
| **후처리(번역)** | DB에서 미번역 문장 조회(1만 토큰·최대 2청크) → Claude 번역 → DB 업데이트 (미번역 있으면 반복) |
| **내보내기** | DB의 `(author, book_title)`별 문장 쌍을 ReportLab으로 1:1 대응 PDF 생성 |

---

## 전체 플로우

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  전처리 (pre_process)                                                             │
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
│                                                              [save_db] → END     │
│                                                                  │              │
└──────────────────────────────────────────────────────────────────┼──────────────┘
                                                                   │
                                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  후처리 (post_process)                                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   [fetch_sentences] → [translate] → [save_translations] → [fetch_sentences] …   │
│          │                    │                    │                           │
│          ▼                    ▼                    ▼                           │
│   current_pk부터         Claude로            korean_sentence                    │
│   1만 토큰·최대 2청크     문장별 번역           컬럼 업데이트                      │
│   미번역 문장 조회                                                               │
│                                                                                 │
│   ※ 미번역 문장이 없을 때까지 루프; 없으면 END                                    │
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
| **fetch_sentences** | 미번역 문장을 id 순으로 1만 토큰·최대 2청크 조회 | state → `pending_items` |
| **translate** | Claude로 청크별 독일어→한국어 학술 번역 (구조화 출력) | `pending_items` → `translated_items` |
| **save_translations** | `korean_sentence`, `status` 컬럼 업데이트 | `translated_items` → DB |

후처리 그래프는 `fetch_sentences` → (미번역 있으면) `translate` → `save_translations` → 다시 `fetch_sentences` 로 순환하며, 미번역이 없으면 종료합니다.

---

## 프로젝트 구조

```
translater_ai_project/
├── main/
│   ├── TranslationState.py       # GraphState, PostTranslationState
│   ├── exceptions.py             # TranslaterAIError 및 세부 예외
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
│   ├── post_process/
│   │   ├── graph.py              # 번역 그래프 (create_translation_workflow)
│   │   ├── node/
│   │   │   └── TranslateNode.py
│   │   ├── service/
│   │   │   ├── Initial_translate.py   # 번역 LLM 호출 (Anthropic)
│   │   │   └── TranslationDbService.py
│   │   └── prompts/
│   │       └── prompts.py
│   └── export/
│       ├── __init__.py           # TranslationPdfExporter, DiltheyEinleitungPdfExport
│       └── pdf_exporter.py       # DB → 1:1 대응 PDF (ReportLab)
├── app.py                        # NiceGUI 기반 철학 번역 DB 뷰어 (웹 UI)
├── app_utils.py                  # 뷰어용 DB 헬퍼 (DB_PATH, fetch_books 등)
├── config.py                     # OS별 기본 PDF 경로 (DEFAULT_PDF_PATH)
├── export_dilthey_pdf.py         # Dilthey Einleitung PDF 내보내기 진입점
├── run.sh                        # 가상환경 기반 뷰어 실행
├── dockerfile                    # Docker 이미지 빌드 (Python 3.12)
├── scripts/
│   └── build-from-github.sh      # GitHub 최신 코드로 Docker 이미지 빌드
├── tests/
│   └── test_segment_service.py   # SegmentService(SoMaJo) 테스트
├── requirements.txt
└── README.md
```

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| **오케스트레이션** | LangGraph (StateGraph) |
| **PDF 추출** | PyMuPDF (`fitz`) |
| **문장 분리** | SoMaJo (독일어 `de_CMC`) |
| **전처리 LLM** | LangChain + Google Gemini 2.5 Flash |
| **번역 LLM** | LangChain + Anthropic Claude Opus 4 (구조화 출력) |
| **PDF 생성** | ReportLab (한글 폰트: Windows 맑은 고딕/굴림) |
| **저장소** | SQLite (`philosophy_translation.db`) |
| **웹 UI** | NiceGUI, FastAPI |

---

## 웹 뷰어 (NiceGUI)

`app.py`는 `processed_sentences` DB를 탐색하고, PDF 업로드로 **전처리 + 후처리(번역)** 를 한 번에 실행하는 웹 인터페이스를 제공합니다.

- **메인 페이지 (`/`)**
  - **책 선택**: DB의 `(저자, 책 제목)` 목록에서 선택 시 문장 매핑 페이지(`/mapping`)로 이동.
  - **DB 관리**
    - PDF 업로드 + 저자/책 제목 입력 → 전처리 그래프 실행 후 후처리 그래프 실행 (중복 `(저자, 책 제목)` 방지).
    - 등록된 책 목록·문장 수 표시, 선택 책 전체 문장 삭제.
- **문장 매핑 (`/mapping`)**
  - 선택한 책의 **독일어–한국어 1:1 카드** 무한 스크롤.
  - 문장 번호 입력 시 해당 위치까지 로딩 후 스크롤 이동.

---

## PDF 내보내기

DB에 저장된 번역을 **독일어–한국어 1:1 대응 PDF**로 내보낼 수 있습니다.

- **공통**: `main.export.TranslationPdfExporter(db_path)` 로 DB 연결 후 `generate_pdf(output_path, author, book_title)` 호출.  
  `author`/`book_title`을 지정하면 해당 책만, 둘 다 `None`이면 DB 전체를 단일 PDF 또는 디렉터리 내 책별 PDF로 생성.
- **Dilthey 전용**: `main.export.DiltheyEinleitungPdfExport(db_path).run(output_path)` 또는 프로젝트 루트에서:

```bash
python export_dilthey_pdf.py
```

기본 출력 파일: `Dilthey_Einleitung_Geisteswissenschaften.pdf`. DB의 `author`/`book_title`이 `DiltheyEinleitungPdfExport`에서 사용하는 값과 일치해야 합니다.

---

## 환경 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

주요 패키지: `langgraph`, `langchain-google-genai`, `langchain-anthropic`, `pymupdf`, `SoMaJo`, `python-dotenv`, `langsmith`, `nicegui`, `reportlab`, `pydantic`

### 2. 환경 변수 (.env)

프로젝트 루트에 `.env` 파일 생성:

| 변수명 | 용도 |
|--------|------|
| `GOOGLE_API_KEY` | 전처리용 Gemini API |
| `ANTHROPIC_API_KEY` | 번역용 Claude API |
| `LANGCHAIN_TRACING_V2` | `true` 시 LangSmith 트레이싱 (선택) |
| `LANGSMITH_API_KEY` | LangSmith API 키 (선택) |

---

## 사용 방법 (CLI)

### 전처리만 실행 (PDF → DB)

```bash
python -m main.pre_process.graph
```

또는 코드에서:

```python
import config
from main.pre_process.graph import create_preprocessing_workflow
from main.TranslationState import GraphState

app = create_preprocessing_workflow()
initial_state: GraphState = {
    "pdf_path": config.DEFAULT_PDF_PATH,
    "author": "Dilthey, Wilhelm",
    "book_title": "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. ...",
    "db_path": "philosophy_translation.db",
}
final_output = app.invoke(initial_state)
```

전처리 실행 시 `flatten_sentences_top100.txt`에 `german_sentences` 샘플(인덱스 100~199)이 저장됩니다.

**경로**: `config.py`의 `DEFAULT_PDF_PATH` 수정 (Windows/macOS 예시 포함).

---

### 번역 실행 (DB → 한국어 저장)

```bash
python -m main.post_process.graph
```

`has_untranslated_sentences`로 미번역 존재 여부를 확인한 뒤, 미번역 문장을 1만 토큰·최대 2청크 단위로 번역·저장합니다. 미번역이 없으면 종료합니다.

```python
from main.post_process.graph import create_translation_workflow
from main.post_process.service.TranslationDbService import has_untranslated_sentences
from main.TranslationState import PostTranslationState

app = create_translation_workflow()
db_path = getattr(config, "DEFAULT_DB_PATH", "philosophy_translation.db")
author = "Dilthey, Wilhelm"
book_title = "..."

if has_untranslated_sentences(db_path, author, book_title):
    app.invoke({"db_path": db_path, "author": author, "book_title": book_title})
```

---

### DB 문장 조회

```bash
python -m main.read_db_sentences
```

`processed_sentences` 테이블의 id 1~100 행을 전체 컬럼으로 콘솔에 출력합니다.

---

## 사용 방법 (웹 뷰어)

### 실행

가상환경(`.venv`) 생성 후:

```bash
pip install -r requirements.txt
./run.sh
```

또는 `python app.py`. NiceGUI 서버 기동 후 브라우저에서 표시된 URL(예: `http://localhost:8080`)로 접속합니다.

### 기능 요약

- **책 선택**: DB에 저장된 책 목록에서 선택 → 1:1 문장 매핑 보기, 문장 번호로 점프, 무한 스크롤.
- **DB 관리**: PDF 업로드 + 저자/책 제목 입력 후 추가 → 전처리·후처리 순차 실행. 동일 저자/책 제목 중복 방지, 책별 문장 삭제.

---

## 데이터베이스

- **파일**: `philosophy_translation.db` (기본값: `app_utils.py` 기준 프로젝트 루트)
- **테이블**: `processed_sentences`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | INTEGER | PK, 자동 증가 |
| `pdf_path` | TEXT | 원본 PDF 경로 |
| `author` | TEXT | 저자명 |
| `book_title` | TEXT | 문헌 제목 |
| `german_sentence` | TEXT | 전처리된 독일어 문장 |
| `korean_sentence` | TEXT | 번역된 한국어 (후처리 시 업데이트) |
| `status` | TEXT | 기본값 `'pending'`, 번역 저장 시 `'complete'` |

---

## 테스트

SoMaJo 기반 문장 분리:

```bash
python -m pytest tests/test_segment_service.py -v
```

또는 해당 테스트 모듈을 직접 실행.

---

## Docker / 배포

- **빌드·실행**: 프로젝트 루트에서 `dockerfile`로 이미지 빌드 후 컨테이너 실행. 포트 8080 노출.
- **코드 반영**: `app.py` 등 수정 후에는 이미지 재빌드 및 컨테이너 재기동 필요.
- **GitHub 최신 코드로 빌드** (EC2 등):

```bash
bash scripts/build-from-github.sh
```

환경 변수: `REPO_URL`, `GITHUB_BRANCH`, `IMAGE_NAME`, `BUILD_DIR`. 기본 이미지 이름: `trans-ai-app`.

---

## 라이선스 및 기여

저장소 설정에 따라 라이선스가 정해집니다. 이슈/PR로 기여를 제안할 수 있습니다.
