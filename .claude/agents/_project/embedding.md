# 임베딩 확장 에이전트

새 임베딩 모델 추가 가이드

## 작업 흐름

```
1. 제공자(Provider) 정보 확인
   ↓
2. Provider 클래스 구현
   ↓
3. 팩토리에 등록
   ↓
4. 설정 추가
   ↓
5. 테스트 작성
```

## 파일 위치

| 구분 | 경로 |
|------|------|
| 추상 클래스 | `app/domains/embeddings/base.py` |
| 팩토리 서비스 | `app/domains/embeddings/service.py` |
| 제공자 구현 | `app/domains/embeddings/providers/{provider}.py` |
| 설정 | `app/core/config.py` |

## 지원 예정 모델

| Provider | 모델 |
|----------|------|
| OpenAI | text-embedding-ada-002, text-embedding-3-small/large |
| HuggingFace | sentence-transformers/* |
| Ollama | nomic-embed-text, mxbai-embed-large |
| Bedrock | amazon.titan-embed-text-v1 |

## 구현 패턴

### 1. 추상 클래스 (이미 정의됨)

```python
# app/domains/embeddings/base.py
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """임베딩 제공자 추상 클래스"""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """임베딩 벡터 차원"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """모델 이름"""
        pass

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """텍스트를 벡터로 변환"""
        pass

    async def embed_single(self, text: str) -> list[float]:
        """단일 텍스트 임베딩"""
        results = await self.embed([text])
        return results[0]
```

### 2. 새 Provider 구현

```python
# app/domains/embeddings/providers/ollama.py
from app.domains.embeddings.base import EmbeddingProvider
import httpx


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama 로컬 임베딩"""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
    ):
        self._model = model
        self._base_url = base_url
        self._dimensions = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
        }

    @property
    def dimension(self) -> int:
        return self._dimensions.get(self._model, 768)

    @property
    def model_name(self) -> str:
        return f"ollama/{self._model}"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        async with httpx.AsyncClient() as client:
            for text in texts:
                response = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={"model": self._model, "prompt": text},
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["embedding"])
        return embeddings
```

### 3. 팩토리 서비스에 등록

```python
# app/domains/embeddings/service.py
from enum import Enum
from app.domains.embeddings.base import EmbeddingProvider
from app.domains.embeddings.providers.openai import OpenAIEmbeddingProvider
from app.domains.embeddings.providers.ollama import OllamaEmbeddingProvider
from app.core.config import settings


class EmbeddingProviderType(str, Enum):
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    BEDROCK = "bedrock"


class EmbeddingService:
    """임베딩 서비스 팩토리"""

    _providers: dict[str, type[EmbeddingProvider]] = {
        EmbeddingProviderType.OPENAI: OpenAIEmbeddingProvider,
        EmbeddingProviderType.OLLAMA: OllamaEmbeddingProvider,
        # 새 provider 여기에 등록
    }

    @classmethod
    def create(
        cls,
        provider_type: EmbeddingProviderType | None = None,
        **kwargs,
    ) -> EmbeddingProvider:
        """Provider 인스턴스 생성"""
        provider_type = provider_type or settings.default_embedding_provider

        if provider_type not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(**kwargs)

    @classmethod
    def register(
        cls,
        provider_type: str,
        provider_class: type[EmbeddingProvider],
    ) -> None:
        """새 provider 런타임 등록"""
        cls._providers[provider_type] = provider_class
```

### 4. 설정 추가

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from app.domains.embeddings.service import EmbeddingProviderType


class Settings(BaseSettings):
    # Embedding
    default_embedding_provider: EmbeddingProviderType = EmbeddingProviderType.OPENAI
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    model_config = {"env_file": ".env"}


settings = Settings()
```

## 체크리스트

- [ ] `EmbeddingProvider` 추상 클래스 상속
- [ ] `dimension` 프로퍼티 구현 (벡터 차원)
- [ ] `model_name` 프로퍼티 구현
- [ ] `embed()` 메서드 async로 구현
- [ ] 팩토리 `_providers` 딕셔너리에 등록
- [ ] 필요한 설정 `config.py`에 추가
- [ ] 테스트 작성

## 주의사항

- 배치 처리 시 API rate limit 고려
- 에러 발생 시 적절한 예외 raise
- dimension은 Qdrant 컬렉션 생성 시 필요
