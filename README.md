# 특허사무소 메일 자동화 시스템

Microsoft Graph API + Claude AI를 활용한 특허사무소 Outlook 메일 처리 자동화 시스템

## 아키텍처

```
[Outlook 수신] → [사건 매칭] → [AI 분석] → [초안 생성] → [수동 승인 발송]
```

## 빠른 시작

### 1. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 필요한 값 입력
```

### 2. Docker로 실행
```bash
docker-compose up -d
```

### 3. DB 마이그레이션
```bash
cd backend
alembic upgrade head
```

### 4. 프론트엔드 실행
```bash
cd frontend
npm install
npm run dev
```

## 개발 환경 직접 실행

### 백엔드
```bash
cd backend
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Celery 워커
```bash
cd backend
celery -A app.worker worker --loglevel=info
```

## 환경변수

| 변수 | 설명 |
|------|------|
| `AZURE_TENANT_ID` | Azure Active Directory 테넌트 ID |
| `AZURE_CLIENT_ID` | Entra 앱 클라이언트 ID |
| `AZURE_CLIENT_SECRET` | Entra 앱 클라이언트 시크릿 |
| `GRAPH_WEBHOOK_NOTIFICATION_URL` | Webhook 수신 공개 URL |
| `DATABASE_URL` | PostgreSQL 연결 문자열 (asyncpg) |
| `REDIS_URL` | Redis 연결 문자열 |
| `ANTHROPIC_API_KEY` | Claude API 키 |

## MVP Phase 1 기능

- [x] 프로젝트 초기화
- [ ] DB 스키마 + ORM 모델
- [ ] Microsoft Graph API 연동
- [ ] 사건 매칭 엔진
- [ ] AI 메일 분석
- [ ] 회신 초안 생성
- [ ] 인박스 대시보드 UI
