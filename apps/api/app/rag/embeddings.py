"""Embedding adapters: BGE-local (fastembed) dense + sparse, a Redis cache wrapper,
and a deterministic fake embedder for tests."""
from __future__ import annotations

import hashlib
import json
import math
from typing import TYPE_CHECKING, Any

from app.rag.types import SparseVector

if TYPE_CHECKING:
    import redis


# ---- BGE local (fastembed) ----
class BgeDenseEmbedder:
    def __init__(self, model: str) -> None:
        from fastembed import TextEmbedding

        self._m = TextEmbedding(model_name=model)
        self.dim = len(next(iter(self._m.embed(["probe"]))))

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, v)) for v in self._m.embed(texts)]


class BgeSparseEmbedder:
    def __init__(self, model: str) -> None:
        from fastembed import SparseTextEmbedding

        self._m = SparseTextEmbedding(model_name=model)

    def embed_sparse(self, texts: list[str]) -> list[SparseVector]:
        out: list[SparseVector] = []
        for v in self._m.embed(texts):
            out.append(
                SparseVector(
                    indices=list(map(int, v.indices)),
                    values=list(map(float, v.values)),
                )
            )
        return out


# ---- Redis cache wrapper ----
class CachedDenseEmbedder:
    def __init__(self, inner: Any, client: redis.Redis, model: str, ttl: int) -> None:
        self._inner = inner
        self._r = client
        self._model = model
        self._ttl = ttl
        self.dim = inner.dim

    def _key(self, text: str) -> str:
        h = hashlib.sha256(f"{self._model}:{text}".encode()).hexdigest()
        return f"cache:embed:{h}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float] | None] = [None] * len(texts)
        misses: list[int] = []
        for i, t in enumerate(texts):
            cached = self._r.get(self._key(t))
            if cached is not None:
                results[i] = json.loads(cached)
            else:
                misses.append(i)
        if misses:
            fresh = self._inner.embed([texts[i] for i in misses])
            for i, vec in zip(misses, fresh, strict=True):
                results[i] = vec
                self._r.setex(self._key(texts[i]), self._ttl, json.dumps(vec))
        return [r for r in results if r is not None]


# ---- Fake embedder (tests) ----
class FakeDenseEmbedder:
    """Feature-hashed bag-of-words → deterministic vectors with meaningful cosine."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        vecs: list[list[float]] = []
        for text in texts:
            v = [0.0] * self.dim
            for tok in text.lower().split():
                idx = int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim
                v[idx] += 1.0
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            vecs.append([x / norm for x in v])
        return vecs
