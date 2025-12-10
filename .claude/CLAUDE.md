# Claude Code 가이드

> 이 문서는 공통 컨벤션과 작업 가이드를 담고 있습니다.
> 프로젝트 특화 정보는 `PROJECT.md`를 참조하세요.

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

---

## Git 컨벤션

### Git Flow

```
main (production)
  ↑
  │ PR + 태그 (v1.0.0)
  │
release/*  ←─────────────────┐
  ↑                          │
  │ PR                       │ hotfix/* (긴급)
  │                          │
develop ←────────────────────┤
  ↑                          │
  │ PR                       │
  │                          │
feature/*  ───────────────────┘
```

| 브랜치 | 용도 | 배포 환경 | 보호 |
|--------|------|-----------|------|
| `main` | 프로덕션 릴리즈 | production | O |
| `develop` | 개발 통합 | development | O |
| `release/*` | 릴리즈 준비/QA | staging | - |
| `feature/*` | 기능 개발 | local | - |
| `hotfix/*` | 긴급 수정 | - | - |

### 브랜치 네이밍

```
{type}/{domain}-{description}
```

| 타입 | 용도 | 예시 |
|------|------|------|
| `feature` | 새 기능 | `feature/documents-upload-api` |
| `fix` | 버그 수정 | `fix/embeddings-timeout-error` |
| `refactor` | 리팩토링 | `refactor/search-query-optimization` |
| `hotfix` | 긴급 수정 | `hotfix/auth-token-expired` |
| `release` | 릴리즈 | `release/1.0.0` |

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

### 릴리즈 프로세스

```
1. develop → release/* 브랜치 생성
2. QA/버그 수정 (release/* 에서)
3. release/* → main PR 생성
4. main 머지 후 태그 생성 (v1.0.0)
5. main → develop 역머지
```

---

## 작업 가이드

코딩 작업 시 `.claude/agents/` 하위의 에이전트 가이드를 참조하여 진행한다.

### 커맨드 (워크플로우)

| 커맨드 | 파일 | 용도 | 포함 단계 |
|--------|------|------|-----------|
| `/spec {domain}` | `commands/spec.md` | 도메인 스펙 문서 생성 | 요구사항 → 분석 → 스펙 작성 |
| `/feature {domain}` | `commands/feature.md` | 스펙 기반 신규 기능 구현 | 스펙확인 → **코드재활용분석** → 구현 → **빌드/검증** |
| `/fix {domain}` | `commands/fix.md` | 버그 수정 | 버그분석 → 수정 → **빌드/검증** → 테스트 |
| `/change {domain}` | `commands/change.md` | 기존 기능 변경/개선 | 영향분석 → **코드재활용분석** → 수정 → **빌드/검증** → /review |
| `/review {domain}` | `commands/review.md` | 코드 리뷰 및 품질 검증 | 스펙준수 → 코드품질 → 테스트커버리지 |

#### 커맨드 선택 가이드

| 상황 | 사용 커맨드 |
|------|-------------|
| 새로운 도메인/기능 개발 | `/spec` → `/feature` → `/review` |
| 기존 기능에 새 요소 추가 | `/change` |
| 기존 기능의 동작 변경 | `/change` |
| 버그 수정 (기능 변경 없음) | `/fix` |
| 리팩토링 (기능 변경 없음) | `/change` |
| 코드 품질 점검 | `/review` |

### 분석 에이전트

| 에이전트 | 파일 | 용도 | 사용 시점 |
|----------|------|------|-----------|
| Code Analyzer | `agents/code-analyzer.md` | 기존 코드 재활용 분석 | `/feature`, `/change` 내부 |

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

**신규 개발:**
```
/spec {domain}
    ├─→ risk-analyst      (8장 리스크)
    ├─→ security-analyst  (8.3장 보안)
    └─→ test-designer     (9장 테스트)
            ↓
/feature {domain}
    ├─→ code-analyzer     (코드 재활용 분석)
    ├─→ schema-builder    (schemas.py)
    ├─→ service-builder   (service.py)
    ├─→ api-builder       (api/v1/*.py)
    ├─→ test-builder      (tests/)
    └─→ 빌드/검증         (mypy, ruff, pytest)
            ↓
/review {domain}
    ├─→ spec-reviewer     (스펙 준수)
    ├─→ code-reviewer     (코드 품질)
    └─→ test-reviewer     (테스트 검증)
```

**기존 코드 수정:**
```
/fix {domain}                    /change {domain}
    │                                │
    ├─→ 버그 정보 수집                ├─→ 변경 요구사항 수집
    ├─→ 영향 범위 분석                ├─→ code-analyzer (재활용 분석)
    ├─→ 코드 수정                     ├─→ 스펙 문서 수정
    ├─→ 빌드/검증                     ├─→ 코드 수정
    └─→ 테스트 확인                   ├─→ 테스트 수정
            ↓                        ├─→ 빌드/검증
      커밋 (fix: ...)                └─→ /review 실행
                                           ↓
                                   커밋 (feat/refactor: ...)
```

**빌드/검증 단계:**
```bash
# 1. 타입 체크
mypy app/domains/{domain}/

# 2. 린트 검사
ruff check app/domains/{domain}/

# 3. 테스트 실행
pytest tests/ -k "{domain}" -v
```
