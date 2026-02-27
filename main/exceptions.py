"""
프로젝트 공통 예외 정의.
모든 에러는 한 곳에서 정의하고, 발생 지점에서 raise 후 상위(노드/진입점)에서 try/except로 처리한다.
"""


class TranslaterAIError(Exception):
    """프로젝트 전체 예외의 부모 클래스."""

    def __init__(self, message: str, cause: Exception | None = None):
        self.message = message
        self.cause = cause
        super().__init__(message)

    def __str__(self):
        if self.cause:
            return f"{self.message} (원인: {self.cause})"
        return self.message


# --- 입력/파일 ---


class InvalidPdfError(TranslaterAIError):
    """PDF 경로 없음, 손상된 PDF, 권한 문제 등."""


class FileWriteError(TranslaterAIError):
    """파일 쓰기 실패 (디스크 풀, 권한, 인코딩 등)."""


# --- DB ---


class DatabaseError(TranslaterAIError):
    """DB 연결/실행/커밋 실패."""


# --- 외부 API (LLM) ---


class LLMProviderError(TranslaterAIError):
    """LLM API 호출 실패 (API 키 없음, rate limit, 타임아웃, 응답 파싱 등)."""


# --- 워크플로/상태 ---


class InvalidStateError(TranslaterAIError):
    """GraphState 필수 키 누락 또는 타입 불일치."""


# --- 동시 처리 ---


class CleanupChunkError(TranslaterAIError):
    """병렬 cleanup 중 일부 청크 처리 실패."""

    def __init__(self, message: str, chunk_index: int | None = None, cause: Exception | None = None):
        super().__init__(message, cause)
        self.chunk_index = chunk_index


# --- 세그멘테이션 ---


class SegmentError(TranslaterAIError):
    """SoMaJo 등 문장 분리 실패."""


# --- 환경/설정 ---


class MissingConfigError(TranslaterAIError):
    """필수 환경변수/설정 누락 (API 키, 경로 등)."""
