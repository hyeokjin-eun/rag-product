# Feature 생성 커맨드

스펙 문서를 기반으로 도메인 + API + 테스트를 구현합니다.

## 입력

- $ARGUMENTS: 기능 이름 (예: documents, search, embeddings, rag)

## 작업 흐름

```
[1. 스펙 문서 확인]
        ↓
[2. 구현 계획 수립]
        ↓
[3. 에이전트 구현] ─────────────────────┐
        │                              │
        ├─→ 📋 schema-builder         │  순차 실행
        ├─→ ⚙️ service-builder        │  (의존성 있음)
        ├─→ 🌐 api-builder            │
        └─→ 🧪 test-builder           │
        ↓  ←───────────────────────────┘
[4. 통합 확인]
        ↓
[5. 완료]
```

## 사용 에이전트

| 에이전트 | 파일 | 역할 | 의존성 |
|----------|------|------|--------|
| Schema Builder | `agents/schema-builder.md` | Pydantic 스키마 생성 | - |
| Service Builder | `agents/service-builder.md` | 비즈니스 로직 구현 | schema |
| API Builder | `agents/api-builder.md` | FastAPI 라우터 구현 | schema, service |
| Test Builder | `agents/test-builder.md` | 테스트 코드 작성 | 전체 |

---

## 작업 순서

### 1. 스펙 문서 확인

`.claude/specs/$ARGUMENTS.md` 파일을 확인하세요.

**스펙 문서가 있는 경우:**
- 스펙 문서를 읽고 요구사항을 파악
- 바로 구현 단계로 진행

**스펙 문서가 없는 경우:**
- 사용자에게 안내: "스펙 문서가 없습니다. `/spec $ARGUMENTS`를 먼저 실행해주세요."
- 또는 사용자가 원하면 간단히 질문 후 구현 진행 (스펙 문서 없이)

### 2. 가이드 참조

다음 에이전트 가이드를 읽고 구현 패턴을 확인하세요:
- `.claude/agents/domain.md` - 도메인 구현 패턴
- `.claude/agents/api.md` - API 구현 패턴
- `.claude/agents/test.md` - 테스트 작성 패턴

### 3. 구현 계획 수립

스펙 문서의 "9. 구현 체크리스트"를 기반으로 구현 계획을 세우세요.
사용자에게 계획을 보여주고 확인받으세요.

### 4. 도메인 구현

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

### 5. API 구현

스펙 문서 3장 "API 명세"를 참조하여 구현:

- `app/api/v1/$ARGUMENTS.py` 라우터 생성
  - 각 엔드포인트별 상세 명세대로 구현
  - 에러 응답은 스펙 6장 참조
- `app/api/router.py`에 `include_router` 추가

### 6. 테스트 작성

스펙 문서 8장 "테스트 시나리오"를 참조하여 구현:

```
tests/
├── unit/domains/test_$ARGUMENTS.py         # 8.1 단위 테스트
└── integration/test_$ARGUMENTS_api.py      # 8.2 통합 테스트
```

### 7. Temporal 워크플로우 (해당시)

스펙 문서 5.3장에 워크플로우가 정의된 경우:
- `.claude/agents/temporal.md` 가이드 참조
- `workers/workflows/`, `workers/activities/` 에 구현

### 8. 완료 보고

```
✅ $ARGUMENTS 도메인 구현 완료

생성된 파일:
- app/domains/$ARGUMENTS/schemas.py
- app/domains/$ARGUMENTS/service.py
- app/domains/$ARGUMENTS/repository.py
- app/api/v1/$ARGUMENTS.py
- tests/unit/domains/test_$ARGUMENTS.py
- tests/integration/test_$ARGUMENTS_api.py

다음 단계:
1. 테스트 실행: pytest tests/
2. API 문서 확인: http://localhost:8000/docs
3. 다른 도메인과 연동이 필요하면 해당 도메인 구현
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
