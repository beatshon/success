# 딥러닝 트레이딩 시스템을 위한 Dockerfile
FROM python:3.9-slim

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 패키지 설치를 위한 requirements 파일 복사
COPY requirements_advanced.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements_advanced.txt

# GPU 지원을 위한 TensorFlow GPU 버전 설치 (선택사항)
RUN pip install --no-cache-dir tensorflow-gpu

# 애플리케이션 코드 복사
COPY . .

# 모델 저장 디렉토리 생성
RUN mkdir -p models logs data

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=2

# 포트 노출
EXPOSE 8000 8080 5000

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 기본 명령어 설정
CMD ["python", "integrated_advanced_system.py"] 