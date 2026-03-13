# ── 빌드 스테이지 ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# paddleocr(PaddlePaddle) / OpenCV / PyMuPDF 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libfontconfig1 \
    libice6 \
    wget \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt


# ── 런타임 스테이지 ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # PaddleOCR 모델 캐시 경로를 /data 아래로 고정
    PADDLE_HOME=/data/.paddleocr \
    # SQLite DB 경로 (볼륨 마운트 대상)
    APP_DB_PATH=/data/philosophy_translation.db

# 런타임 전용 시스템 패키지 (빌드 도구 제외, 실행에 필요한 .so 만 포함)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libfontconfig1 \
    libice6 \
 && rm -rf /var/lib/apt/lists/*

# 설치된 파이썬 패키지만 빌더에서 복사
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY . .

# 볼륨: DB 파일 및 PaddleOCR 모델 캐시 영속화
VOLUME ["/data"]

# NiceGUI 기본 포트
EXPOSE 8080

# 환경 변수는 docker run --env-file 로 주입 (API 키 등 민감 정보)
# 예: docker run --env-file local.env -v $(pwd)/data:/data -p 8080:8080 translater_ai

CMD ["python", "app.py"]
