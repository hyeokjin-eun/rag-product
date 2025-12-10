# RAG Product - Claude Code 가이드

## 프로젝트 개요

Qdrant 벡터 데이터베이스를 활용한 RAG(Retrieval-Augmented Generation) 시스템

- 여러 도메인의 데이터를 수집하여 벡터화
- 다중 임베딩 모델 지원
- Temporal 기반 워크플로우로 대량 처리

## 기술 스택

| 구분 | 기술 |
|------|------|
| Language | Python 3.x |
| Framework | FastAPI |
| Vector DB | Qdrant |
| Workflow | Temporal |
| Container | Docker Compose |

### 임베딩 모델 (확장 가능)

- OpenAI (text-embedding-ada-002, text-embedding-3-small)
- HuggingFace (sentence-transformers)
- Ollama (로컬 모델)
- AWS Bedrock Titan

### 데이터 소스

- 파일 업로드 (PDF, TXT, MD 등)
- 외부 API 연동

## 패키지 구조 (도메인형)

```
rag-product/
├── .claude/
│   └── CLAUDE.md                   # 프로젝트 컨텍스트 문서
│
├── app/                             # FastAPI 애플리케이션
│   ├── main.py                      # 앱 진입점
│   │
│   ├── api/                         # API 라우터
│   │   ├── router.py                # 라우터 통합
│   │   └── v1/
│   │       ├── documents.py         # 문서 API
│   │       ├── search.py            # 검색 API
│   │       └── collections.py       # 컬렉션 API
│   │
│   ├── domains/                     # 도메인별 비즈니스 로직
│   │   ├── documents/               # 문서 도메인
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   └── repository.py
│   │   │
│   │   ├── embeddings/              # 임베딩 도메인
│   │   │   ├── base.py              # 추상 클래스
│   │   │   ├── service.py           # 팩토리 서비스
│   │   │   └── providers/           # 모델별 구현
│   │   │       ├── openai.py
│   │   │       ├── huggingface.py
│   │   │       ├── ollama.py
│   │   │       └── bedrock.py
│   │   │
│   │   ├── search/                  # 검색 도메인
│   │   │   ├── service.py
│   │   │   └── schemas.py
│   │   │
│   │   └── rag/                     # RAG 파이프라인
│   │       ├── service.py
│   │       └── schemas.py
│   │
│   ├── infrastructure/              # 인프라 계층
│   │   ├── qdrant/
│   │   │   └── client.py            # Qdrant 클라이언트
│   │   └── storage/
│   │       └── local.py             # 파일 저장소
│   │
│   ├── core/                        # 핵심 설정
│   │   ├── config.py                # 환경 설정
│   │   ├── dependencies.py          # FastAPI 의존성
│   │   └── exceptions.py            # 커스텀 예외
│   │
│   └── utils/                       # 유틸리티
│
├── workers/                         # Temporal 워커
│   ├── main.py                      # 워커 진입점
│   ├── workflows/
│   │   ├── embedding_workflow.py    # 임베딩 워크플로우
│   │   └── ingestion_workflow.py    # 데이터 수집 워크플로우
│   └── activities/
│       ├── embedding_activities.py
│       └── document_activities.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── docker-compose.yml               # Qdrant + Temporal
├── requirements.txt
└── pyproject.toml
```

## 개발 환경

### 서비스 실행

```bash
docker compose up -d
```

### 접속 정보

| 서비스 | URL |
|--------|-----|
| Qdrant REST | http://localhost:6333 |
| Qdrant gRPC | localhost:6334 |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| Temporal UI | http://localhost:8080 (예정) |

## 코딩 컨벤션

### Python

- PEP 8 스타일 가이드 준수
- Type hints 필수
- Docstring은 Google 스타일
- async/await 패턴 사용

### 네이밍

- 파일: `snake_case.py`
- 클래스: `PascalCase`
- 함수/변수: `snake_case`
- 상수: `UPPER_SNAKE_CASE`

### Pydantic 모델

- 요청: `*Request` (예: `SearchRequest`)
- 응답: `*Response` (예: `SearchResponse`)
- 내부: `*Schema` (예: `DocumentSchema`)

## 작업 가이드

코딩 작업 시 `.claude/agents/` 하위의 에이전트 가이드를 참조하여 진행한다.

| 에이전트 | 파일 | 용도 |
|----------|------|------|
| API 개발 | `agents/api.md` | FastAPI 엔드포인트 구현 |
| 도메인 개발 | `agents/domain.md` | 비즈니스 로직 구현 |
| 임베딩 확장 | `agents/embedding.md` | 새 임베딩 모델 추가 |
| Temporal | `agents/temporal.md` | 워크플로우/액티비티 구현 |
| 테스트 | `agents/test.md` | 테스트 코드 작성 |

## 향후 계획

- [ ] 패키지 구조 생성
- [ ] Temporal 서비스 docker-compose에 추가
- [ ] 임베딩 추상화 및 OpenAI 구현
- [ ] 문서 처리 파이프라인 구축
- [ ] API 서버 구현
- [ ] 테스트 코드 작성