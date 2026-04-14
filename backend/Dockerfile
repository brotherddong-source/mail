FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# pip 업그레이드 및 의존성 직접 설치
RUN pip install --upgrade pip

# 의존성 설치
COPY pyproject.toml .
RUN pip install fastapi uvicorn[standard] sqlalchemy alembic pydantic pydantic-settings \
    asyncpg psycopg2-binary msal httpx redis anthropic python-dotenv \
    python-multipart python-jose[cryptography] passlib[bcrypt] celery jinja2

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
