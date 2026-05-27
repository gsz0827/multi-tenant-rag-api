import hashlib
import random

from openai import OpenAI

from app.core.config import settings


EMBEDDING_DIMENSION = 1536


def create_fake_embedding(text: str) -> list[float]:
    """
    Development fallback embedding.

    Same text -> same vector.
    Different text -> different vector.
    """
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    seed = int(digest[:16], 16)

    rng = random.Random(seed)

    return [rng.uniform(-1.0, 1.0) for _ in range(EMBEDDING_DIMENSION)]


def validate_embedding_dimension(embedding: list[float]) -> list[float]:
    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Embedding dimension mismatch. "
            f"Expected {EMBEDDING_DIMENSION}, got {len(embedding)}. "
            f"Your database column is vector({EMBEDDING_DIMENSION})."
        )

    return embedding


def create_openai_embedding(text: str) -> list[float]:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=text,
    )

    return validate_embedding_dimension(response.data[0].embedding)


def create_aliyun_embedding(text: str) -> list[float]:
    if not settings.ALIYUN_API_KEY:
        raise ValueError("ALIYUN_API_KEY is not configured")

    client = OpenAI(
        api_key=settings.ALIYUN_API_KEY,
        base_url=settings.ALIYUN_BASE_URL,
    )

    response = client.embeddings.create(
        model=settings.ALIYUN_EMBEDDING_MODEL,
        input=text,
        dimensions=settings.ALIYUN_EMBEDDING_DIMENSION,
    )

    return validate_embedding_dimension(response.data[0].embedding)


def create_embedding(text: str) -> list[float]:
    provider = settings.EMBEDDING_PROVIDER.lower().strip()

    if provider == "aliyun":
        return create_aliyun_embedding(text)

    if provider == "openai":
        return create_openai_embedding(text)

    if provider == "fake":
        return create_fake_embedding(text)

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")