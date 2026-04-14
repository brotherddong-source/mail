FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# backend 디렉토리의 pyproject.toml 복사
COPY backend/pyproject.toml .

# 의존성 설치
RUN pip install fastapi "uvicorn[standard]" sqlalchemy alembic pydantic pydantic-settings \
    asyncpg psycopg2-binary msal httpx redis anthropic python-dotenv \
    python-multipart "python-jose[cryptography]" "passlib[bcrypt]" celery jinja2 \
    openpyxl pandas

# backend 소스코드만 복사 → /app/app/ 구조가 됨
COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
