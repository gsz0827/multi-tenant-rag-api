import hashlib
import random


EMBEDDING_DIMENSION = 1536


def create_fake_embedding(text: str) -> list[float]:
    """
    Create a deterministic fake embedding for development.

    Same text -> same vector.
    Different text -> different vector.

    This is only for testing the database and API flow.
    Later we will replace this with a real embedding model.
    """
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    seed = int(digest[:16], 16)

    rng = random.Random(seed)

    return [rng.uniform(-1.0, 1.0) for _ in range(EMBEDDING_DIMENSION)]
