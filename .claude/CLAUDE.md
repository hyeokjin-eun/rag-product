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

## Git 컨벤션

### 브랜치 네이밍

```
{type}/{domain}-{description}
```

| 타입 | 용도 | 예시 |
|------|------|------|
| `feature` | 새 기능 | `feature/documents-upload-api` |
| `fix` | 버그 수정 | `fix/embeddings-timeout-error` |
| `refactor` | 리팩토링 | `refactor/search-query-optimization` |
| `docs` | 문서 | `docs/api-documentation` |
| `test` | 테스트 | `test/documents-integration` |

### 커밋 메시지

```
{type}: {설명}

{본문 (선택)}
```

| 타입 | 용도 |
|------|------|
| `feat` | 새 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `refactor` | 코드 리팩토링 (기능 변경 없음) |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정 등 기타 |

예시:
```
feat: documents 도메인 업로드 API 구현

- POST /api/v1/documents 엔드포인트 추가
- 파일 검증 로직 구현
- 청킹 서비스 연동
```

### PR 템플릿

```markdown
## 요약
{1줄 설명}

## 변경 내용
- {변경사항 1}
- {변경사항 2}

## 관련 스펙
- `.claude/specs/{domain}.md`

## 테스트
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] `/review {domain}` 실행

## 체크리스트
- [ ] 코드 컨벤션 준수
- [ ] 타입 힌트 추가
- [ ] 문서 업데이트 (해당시)
```

## 작업 가이드

코딩 작업 시 `.claude/agents/` 하위의 에이전트 가이드를 참조하여 진행한다.

### 커맨드 (워크플로우)

| 커맨드 | 파일 | 용도 |
|--------|------|------|
| `/spec {domain}` | `commands/spec.md` | 도메인 스펙 문서 생성 |
| `/feature {domain}` | `commands/feature.md` | 스펙 기반 기능 구현 |
| `/review {domain}` | `commands/review.md` | 코드 리뷰 및 품질 검증 |

### 구현 에이전트 (Builder)

| 에이전트 | 파일 | 용도 | 사용 시점 |
|----------|------|------|-----------|
| Schema Builder | `agents/schema-builder.md` | Pydantic 스키마 생성 | `/feature` 내부 |
| Service Builder | `agents/service-builder.md` | 서비스 레이어 구현 | `/feature` 내부 |
| API Builder | `agents/api-builder.md` | FastAPI 라우터 구현 | `/feature` 내부 |
| Test Builder | `agents/test-builder.md` | 테스트 코드 작성 | `/feature` 내부 |

### 단축 가이드 (직접 참조용)

| 에이전트 | 파일 | 용도 |
|----------|------|------|
| API 개발 | `agents/api.md` | FastAPI 엔드포인트 구현 요약 |
| 도메인 개발 | `agents/domain.md` | 비즈니스 로직 구현 요약 |
| 임베딩 확장 | `agents/embedding.md` | 새 임베딩 모델 추가 |
| Temporal | `agents/temporal.md` | 워크플로우/액티비티 구현 |
| 테스트 | `agents/test.md` | 테스트 코드 작성 요약 |

### 분석/검토 에이전트

| 에이전트 | 파일 | 용도 | 사용 시점 |
|----------|------|------|-----------|
| Risk Analyst | `agents/risk-analyst.md` | 리스크/장애 분석 | `/spec` 내부 |
| Security Analyst | `agents/security-analyst.md` | 보안 검토 | `/spec` 내부 |
| Test Designer | `agents/test-designer.md` | 테스트 시나리오 설계 | `/spec` 내부 |
| Spec Reviewer | `agents/spec-reviewer.md` | 스펙 준수 검증 | `/review` 내부 |
| Code Reviewer | `agents/code-reviewer.md` | 코드 품질 검증 | `/review` 내부 |
| Test Reviewer | `agents/test-reviewer.md` | 테스트 커버리지 검증 | `/review` 내부 |

### 에이전트 사용 흐름

```
/spec {domain}
    ├─→ risk-analyst      (8장 리스크)
    ├─→ security-analyst  (8.3장 보안)
    └─→ test-designer     (9장 테스트)
            ↓
/feature {domain}
    ├─→ schema-builder    (schemas.py)
    ├─→ service-builder   (service.py)
    ├─→ api-builder       (api/v1/*.py)
    └─→ test-builder      (tests/)
            ↓
/review {domain}
    ├─→ spec-reviewer     (스펙 준수)
    ├─→ code-reviewer     (코드 품질)
    └─→ test-reviewer     (테스트 검증)
```

## 향후 계획

- [ ] 패키지 구조 생성
- [ ] Temporal 서비스 docker-compose에 추가
- [ ] 임베딩 추상화 및 OpenAI 구현
- [ ] 문서 처리 파이프라인 구축
- [ ] API 서버 구현
- [ ] 테스트 코드 작성