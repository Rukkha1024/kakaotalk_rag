"""Small Hugging Face embedding client wrapper."""

from __future__ import annotations

import os
from typing import Any

from huggingface_hub import InferenceClient

try:
    from .semantic_index import DEFAULT_EMBEDDING_MODEL
except ImportError:
    from semantic_index import DEFAULT_EMBEDDING_MODEL


class ExternalEmbeddingClient:
    """Wrap Hugging Face embedding inference for documents and queries."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_EMBEDDING_MODEL,
        provider: str | None = None,
        token: str | None = None,
    ) -> None:
        self.model = model
        self.provider = provider
        self.token = token or os.environ.get("HF_TOKEN")
        self.auth_source = "HF_TOKEN" if self.token else "cached login credentials"
        client_kwargs: dict[str, Any] = {}
        if self.token:
            client_kwargs["token"] = self.token
        if self.provider:
            client_kwargs["provider"] = self.provider
        self._client = InferenceClient(**client_kwargs)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [self._embed_one(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)

    def _embed_one(self, text: str) -> list[float]:
        return self._coerce_vector(self._call_feature_extraction(text))

    def _call_feature_extraction(self, payload: str) -> Any:
        try:
            return self._client.feature_extraction(text=payload, model=self.model)
        except Exception as error:  # pragma: no cover - network/provider behavior.
            provider = self.provider or "default"
            raise RuntimeError(
                f"Failed to embed text with model `{self.model}` via provider `{provider}` "
                f"using {self.auth_source}: {error}"
            ) from error

    def _coerce_vector(self, payload: Any) -> list[float]:
        if hasattr(payload, "tolist"):
            payload = payload.tolist()
        payload = self._unwrap_payload(payload)
        if isinstance(payload, list) and len(payload) == 1 and self._is_vector(payload[0]):
            payload = payload[0]
        if self._is_vector(payload):
            return self._vector_to_floats(payload)
        raise RuntimeError(
            "Embedding response shape was not a 1D vector. "
            "Try a provider/model pair that serves sentence embeddings."
        )

    def _unwrap_payload(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            for key in ("embeddings", "data", "vector"):
                value = payload.get(key)
                if value is not None:
                    return value
        return payload

    @staticmethod
    def _is_vector(value: Any) -> bool:
        return isinstance(value, list) and bool(value) and all(isinstance(item, (int, float)) for item in value)

    @staticmethod
    def _vector_to_floats(value: list[float]) -> list[float]:
        return [float(item) for item in value]
