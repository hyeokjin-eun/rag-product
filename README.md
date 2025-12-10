# RAG Product

Qdrant 벡터 데이터베이스를 활용한 RAG(Retrieval-Augmented Generation) 프로젝트

## 시작하기

### 1. Qdrant 실행

```bash
docker compose up -d
```

### 2. 접속 정보

| 서비스 | URL | 설명 |
|--------|-----|------|
| REST API | http://localhost:6333 | Qdrant REST API |
| gRPC API | localhost:6334 | Qdrant gRPC API |
| Web UI | http://localhost:6333/dashboard | Qdrant 대시보드 |

### 3. Python 클라이언트 설치

```bash
pip install qdrant-client
```

### 4. 연결 예시

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# 또는 URL로 연결
client = QdrantClient(url="http://localhost:6333")
```

## Docker 명령어

```bash
# 실행
docker compose up -d

# 중지
docker compose down

# 로그 확인
docker compose logs -f qdrant

# 데이터 포함 삭제
docker compose down -v
```

## 프로젝트 구조

```
rag-product/
├── docker-compose.yml  # Qdrant 컨테이너 설정
├── main.py             # 메인 애플리케이션
└── README.md           # 프로젝트 문서
```