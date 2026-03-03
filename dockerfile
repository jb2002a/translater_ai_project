FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 시스템 패키지 (PDF 처리 등 추가 의존성이 필요하면 여기에서 설치)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# NiceGUI 포트
EXPOSE 8000

# 환경 변수는 docker run 시 --env / --env-file 로 주입하는 것을 권장

# 애플리케이션 실행
CMD ["python", "app.py"]

