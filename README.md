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
│       │   ├── Initial_translate.py      # 번역 LLM 호출 로직
│       │   └── TranslationDbService.py   # has_untranslated_sentences, fetch, save
│       └── prompts/
│           └── prompts.py
├── app.py                        # NiceGUI 기반 철학 번역 DB 뷰어 (웹 UI)
├── app_utils.py                  # 뷰어용 DB 헬퍼 (DB_PATH, fetch_books 등)
├── run.sh                        # 가상환경 기반 뷰어 실행 스크립트
├── config.py                     # OS별 기본 PDF 경로 (DEFAULT_PDF_PATH)
├── requirements.txt
└── README.md
```

---

## 웹 뷰어 (NiceGUI 기반 UI)

`app.py`는 `processed_sentences` DB를 시각적으로 탐색하고, 새로운 PDF를 업로드해서 **전처리 + 번역을 한 번에 수행**하는 웹 인터페이스를 제공합니다.

- **메인 페이지 (`/`)**
  - **책 선택 탭**: DB에 저장된 `(저자, 책 제목)` 목록을 불러와 선택하면, 해당 책의 문장 매핑 페이지(`/mapping`)로 이동합니다.
  - **DB 관리 탭**
    - PDF 업로드 + 저자/책 제목 입력 → 전처리 그래프(`create_preprocessing_workflow`)와 후처리 그래프(`create_translation_workflow`)를 순차 실행하여 DB에 저장 및 번역까지 진행합니다.
    - 이미 동일한 `(저자, 책 제목)`이 있을 경우 중복 추가를 막습니다.
    - 등록된 책 목록과 각 책의 문장 수를 보여주고, 선택한 책의 모든 문장을 DB에서 삭제할 수 있습니다.

- **문장 매핑 페이지 (`/mapping`)**
  - 선택한 책의 **독일어–한국어 문장 1:1 카드 뷰**를 무한 스크롤로 제공합니다.
  - 상단 입력창에 **문장 번호**를 입력하면 해당 위치까지 자동으로 추가 로딩 후, 해당 카드로 스크롤 이동합니다.

웹 뷰어는 내부적으로 `main.pre_process.graph`, `main.post_process.graph`, `TranslationDbService`, `Initial_translate` 등을 그대로 사용하므로, CLI에서의 플로우와 UI에서의 플로우가 일치합니다.

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

## 사용 방법 (CLI 파이프라인)

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

## 사용 방법 (웹 뷰어)

### 1. 가상환경에서 실행

프로젝트 루트에 `.venv`(예: `python -m venv .venv`)를 만든 뒤, 의존성을 설치합니다.

```bash
pip install -r requirements.txt
```

이후 아래 스크립트로 웹 앱을 실행합니다.

```bash
./run.sh
```

또는 가상환경을 활성화한 상태에서 직접 실행할 수도 있습니다.

```bash
python app.py
```

성공적으로 실행되면 NiceGUI 서버가 기동되고, 브라우저에서 기본 주소(예: `http://localhost:8080` 또는 콘솔에 출력된 URL)를 열어 **철학 번역 뷰어**에 접속할 수 있습니다.

### 2. 뷰어에서 할 수 있는 일

- **기존 데이터 탐색**
  - 상단의 **책 선택 탭**에서 DB에 저장된 책을 선택해 1:1 문장 매핑을 살펴볼 수 있습니다.
  - 문장 번호로 특정 위치로 점프하거나, 무한 스크롤로 전체 문장을 내려보며 확인할 수 있습니다.
- **새 책 추가 + 번역**
  - **DB 관리 탭**에서 PDF를 업로드하고 저자/책 제목을 입력한 뒤 **추가** 버튼을 누르면,
    - 전처리 그래프가 PDF에서 문장을 추출·정제 후 DB에 저장하고,
    - 이어서 후처리 그래프가 미번역 문장을 번역하여 `korean_sentence` 컬럼을 채웁니다.
- **책 데이터 삭제**
  - 더 이상 필요 없는 책은 DB 관리 탭에서 선택 후 **삭제** 버튼을 통해 해당 책의 모든 문장을 DB에서 제거할 수 있습니다.

### 3. Docker / EC2 배포 시

- `app.py`를 수정한 뒤에는 **반드시 Docker 이미지를 다시 빌드**한 다음 컨테이너를 재기동해야 합니다.  
  (예: `docker build -t trans-ai . && docker stop trans-ai-service; docker run -d ...`)
- PDF 업로드 시 `RuntimeError: The client this element belongs to has been deleted` 가 나오면,  
  `reconnect_timeout=7200` 이 적용된 최신 `app.py` 로 이미지를 다시 빌드·배포했는지 확인하세요.

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
