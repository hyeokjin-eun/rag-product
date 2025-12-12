# RAG Product

Qdrant 벡터 데이터베이스를 활용한 RAG(Retrieval-Augmented Generation) 시스템

## 요구사항

- Python 3.12+ (pyenv 권장)
- Docker & Docker Compose
- uv (패키지 관리자)

## 환경 설정

### pyenv + uv 설치 (최초 1회)

```bash
# pyenv 설치
brew install pyenv

# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# shell 재시작
source ~/.zshrc
```

## 빠른 시작

```bash
# 1. 인프라 서비스 실행
docker compose up -d

# 2. 의존성 설치
uv sync

# 3. 개발 의존성 포함 설치
uv sync --all-extras

# 4. 애플리케이션 실행
uv run uvicorn app.main:app --reload
```

## 서비스 접속 정보

| 서비스 | URL |
|--------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Qdrant REST | http://localhost:26333 |
| Qdrant Dashboard | http://localhost:26333/dashboard |
| Temporal UI | http://localhost:28080 |
| Redis | localhost:26379 |

## 개발 명령어

```bash
# 타입 체크
uv run mypy app/

# 린트 검사
uv run ruff check app/

# 테스트 실행
uv run pytest

# Temporal 워커 실행
uv run python -m workers.main
```

## 라이선스

MIT
