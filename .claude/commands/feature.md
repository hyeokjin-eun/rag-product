# Feature 생성 커맨드

스펙 문서를 기반으로 도메인 + API + 테스트를 구현합니다.

## 입력

- $ARGUMENTS: 기능 이름 (예: documents, search, embeddings, rag)

## 작업 흐름

```
[0. 브랜치 확인/생성] ←── 작업 범위 판단
        ↓
[1. 스펙 문서 확인]
        ↓
[2. 코드 재활용 분석] ←── agents/code-analyzer.md
        ↓
[3. 구현 계획 수립]
        ↓
[4. 에이전트 구현] ─────────────────────┐
        │                              │
        ├─→ 📋 schema-builder         │  순차 실행
        ├─→ ⚙️ service-builder        │  (의존성 있음)
        ├─→ 🌐 api-builder            │
        └─→ 🧪 test-builder           │
        ↓  ←───────────────────────────┘
[5. 빌드 및 검증]
        ↓
[6. 문서 최신화] ←── 스펙 문서 업데이트 (필수)
        ↓
[7. 커밋 및 PR]
```

## 사용 에이전트

| 에이전트 | 파일 | 역할 | 의존성 |
|----------|------|------|--------|
| Code Analyzer | `agents/code-analyzer.md` | 기존 코드 재활용 분석 | 스펙 문서 |
| Schema Builder | `agents/schema-builder.md` | Pydantic 스키마 생성 | 재활용 분석 |
| Service Builder | `agents/service-builder.md` | 비즈니스 로직 구현 | schema |
| API Builder | `agents/api-builder.md` | FastAPI 라우터 구현 | schema, service |
| Test Builder | `agents/test-builder.md` | 테스트 코드 작성 | 전체 |

---

## 작업 순서

### 0. 브랜치 확인/생성

#### 현재 브랜치 확인
```bash
git branch --show-current
git status
```

#### 작업 범위 판단

| 작업 규모 | 기준 | 브랜치 전략 |
|-----------|------|-------------|
| 소규모 | 파일 1-3개, 단순 기능 | 현재 feature 브랜치에서 계속 |
| 중규모 | 파일 4-10개, 도메인 1개 | 새 feature 브랜치 생성 |
| 대규모 | 파일 10개+, 여러 도메인 | 브랜치 분리 필요, 사용자와 논의 |

#### 브랜치 생성 (필요시)

```bash
# develop 브랜치에서 분기
git checkout develop
git pull origin develop
git checkout -b feature/$ARGUMENTS-{description}
```

**브랜치 네이밍:** `feature/{domain}-{description}`
- 예: `feature/documents-upload-api`
- 예: `feature/search-vector-query`

#### 대규모 작업 시 분리 제안

작업이 대규모인 경우 사용자에게 분리를 제안하세요:
```markdown
⚠️ 작업 범위가 큽니다. 다음과 같이 분리를 권장합니다:

1. `feature/$ARGUMENTS-schemas` - 스키마 정의
2. `feature/$ARGUMENTS-service` - 비즈니스 로직
3. `feature/$ARGUMENTS-api` - API 엔드포인트

각 브랜치별로 PR을 생성하면 리뷰가 용이합니다.
분리해서 진행할까요?
```

### 1. 스펙 문서 확인

`.claude/specs/$ARGUMENTS.md` 파일을 확인하세요.

**스펙 문서가 있는 경우:**
- 스펙 문서를 읽고 요구사항을 파악
- 바로 구현 단계로 진행

**스펙 문서가 없는 경우:**
- 사용자에게 안내: "스펙 문서가 없습니다. `/spec $ARGUMENTS`를 먼저 실행해주세요."
- 또는 사용자가 원하면 간단히 질문 후 구현 진행 (스펙 문서 없이)

### 2. 코드 재활용 분석

`.claude/agents/code-analyzer.md` 가이드를 참조하여 기존 코드 분석:

**분석 대상:**
```
app/domains/*/schemas.py     # 재활용 가능한 스키마
app/domains/*/service.py     # 재활용 가능한 서비스 로직
app/infrastructure/          # 인프라 클라이언트
app/core/                    # 공통 설정, 예외, 의존성
app/utils/                   # 유틸리티 함수
```

**분석 결과를 사용자에게 보고:**
```markdown
## 코드 재활용 분석 결과

### ✅ 재활용 가능
| 항목 | 위치 | 재활용 방법 |
|------|------|-------------|
| {기존 코드} | {파일:라인} | {import/상속} |

### 🆕 신규 구현 필요
| 항목 | 이유 |
|------|------|
| {신규 요소} | {기존에 없음} |
```

### 3. 가이드 참조

다음 에이전트 가이드를 읽고 구현 패턴을 확인하세요:
- `.claude/agents/domain.md` - 도메인 구현 패턴
- `.claude/agents/api.md` - API 구현 패턴
- `.claude/agents/test.md` - 테스트 작성 패턴

### 4. 구현 계획 수립

스펙 문서의 "9. 구현 체크리스트"를 기반으로 구현 계획을 세우세요.
사용자에게 계획을 보여주고 확인받으세요.

### 5. 도메인 구현

스펙 문서의 내용을 참조하여 구현:

```
app/domains/$ARGUMENTS/
├── __init__.py
├── schemas.py      # 스펙 2장 "데이터 모델" 참조
├── service.py      # 스펙 4장 "비즈니스 로직" 참조
└── repository.py   # 스펙 5장 "외부 연동" 참조
```

#### schemas.py
- 스펙 2장의 엔티티 필드 정의를 Pydantic 모델로 변환
- 스펙 3장의 Request/Response 형식 반영

#### service.py
- 스펙 4장의 비즈니스 규칙 구현
- 스펙 4장의 검증 규칙 구현
- 스펙 6장의 에러 처리 구현

#### repository.py
- 스펙 5장의 인프라 연동 구현

### 6. API 구현

스펙 문서 3장 "API 명세"를 참조하여 구현:

- `app/api/v1/$ARGUMENTS.py` 라우터 생성
  - 각 엔드포인트별 상세 명세대로 구현
  - 에러 응답은 스펙 6장 참조
- `app/api/router.py`에 `include_router` 추가

### 7. 테스트 작성

스펙 문서 8장 "테스트 시나리오"를 참조하여 구현:

```
tests/
├── unit/domains/test_$ARGUMENTS.py         # 8.1 단위 테스트
└── integration/test_$ARGUMENTS_api.py      # 8.2 통합 테스트
```

### 8. Temporal 워크플로우 (해당시)

스펙 문서 5.3장에 워크플로우가 정의된 경우:
- `.claude/agents/_project/temporal.md` 가이드 참조 (프로젝트 특화)
- `workers/workflows/`, `workers/activities/` 에 구현

### 9. 빌드 및 검증

구현 완료 후 다음을 실행하여 검증:

```bash
# 1. 타입 체크 (mypy 또는 pyright 사용 시)
mypy app/domains/$ARGUMENTS/

# 2. 린트 검사
ruff check app/domains/$ARGUMENTS/
ruff check app/api/v1/$ARGUMENTS.py

# 3. 단위 테스트 실행
pytest tests/unit/domains/test_$ARGUMENTS.py -v

# 4. 통합 테스트 실행
pytest tests/integration/test_$ARGUMENTS_api.py -v

# 5. 전체 테스트 (선택)
pytest tests/ -v
```

**검증 실패 시:**
- 에러 메시지 확인 후 해당 코드 수정
- 모든 테스트 통과할 때까지 반복

### 10. 문서 최신화 (필수)

구현 완료 후 관련 문서를 최신화하세요:

**스펙 문서 업데이트** (`.claude/specs/$ARGUMENTS.md`):

| 확인 항목 | 업데이트 내용 |
|-----------|---------------|
| 2장 데이터 모델 | 실제 구현된 필드/타입과 일치하는지 |
| 3장 API 명세 | 실제 엔드포인트/파라미터와 일치하는지 |
| 4장 비즈니스 로직 | 실제 구현된 규칙과 일치하는지 |
| 6장 에러 처리 | 실제 에러 코드와 일치하는지 |
| 10장 구현 체크리스트 | 완료 항목 체크 |

**변경 사항이 있으면:**
```markdown
## 구현 시 변경사항

| 항목 | 스펙 | 실제 구현 | 사유 |
|------|------|-----------|------|
| {항목} | {원래 스펙} | {변경된 내용} | {변경 이유} |
```

### 11. 커밋 및 PR

#### 커밋
```bash
git add .
git commit -m "feat: $ARGUMENTS 도메인 구현

- schemas.py: 데이터 모델 정의
- service.py: 비즈니스 로직 구현
- api/v1/$ARGUMENTS.py: API 엔드포인트
- 단위/통합 테스트 작성"
```

#### PR 생성 (develop 브랜치로)
```bash
git push -u origin feature/$ARGUMENTS-{description}
```

**PR 템플릿:**
```markdown
## 요약
$ARGUMENTS 도메인 신규 구현

## 변경 내용
- 스키마 정의 (schemas.py)
- 비즈니스 로직 (service.py)
- API 엔드포인트 (api/v1/$ARGUMENTS.py)
- 테스트 코드

## 관련 스펙
- `.claude/specs/$ARGUMENTS.md`

## 테스트
- [x] 단위 테스트 통과
- [x] 통합 테스트 통과
- [x] `/review $ARGUMENTS` 실행

## 체크리스트
- [x] 코드 컨벤션 준수
- [x] 타입 힌트 추가
- [x] 문서 최신화 완료
```

### 12. 완료 보고

```
✅ $ARGUMENTS 도메인 구현 완료

## 브랜치
- feature/$ARGUMENTS-{description}

## 생성된 파일
- app/domains/$ARGUMENTS/schemas.py
- app/domains/$ARGUMENTS/service.py
- app/domains/$ARGUMENTS/repository.py
- app/api/v1/$ARGUMENTS.py
- tests/unit/domains/test_$ARGUMENTS.py
- tests/integration/test_$ARGUMENTS_api.py

## 다음 단계
1. PR 리뷰 요청
2. develop 브랜치에 머지
3. 다른 도메인 연동 필요시 해당 도메인 구현
```

## 스펙 문서 섹션 매핑

| 스펙 섹션 | 구현 파일 |
|-----------|-----------|
| 2. 데이터 모델 | schemas.py |
| 3. API 명세 | api/v1/$ARGUMENTS.py |
| 4. 비즈니스 로직 | service.py |
| 5. 외부 연동 | repository.py, dependencies.py |
| 6. 에러 처리 | exceptions.py, service.py |
| 8. 테스트 시나리오 | tests/ |

## 도메인 의존성 규칙

```
rag → search → embeddings
         ↘      ↓
          documents
              ↓
         infrastructure
```

상위 도메인만 하위 도메인을 참조할 수 있습니다.
