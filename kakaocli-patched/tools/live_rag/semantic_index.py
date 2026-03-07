"""Helpers for semantic chunking, filtering, and rank fusion."""

from __future__ import annotations

import hashlib
import json
import re
from itertools import islice
from typing import Any, Iterable

import numpy as np


DEFAULT_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-8B"
DEFAULT_SEMANTIC_TOP_K = 24
DEFAULT_CHUNK_CHARS = 400
DEFAULT_CHUNK_OVERLAP = 80
DEFAULT_EMBED_BATCH_SIZE = 16
DEFAULT_FUSION_K = 60
SEMANTIC_TEXT_TEMPLATE_VERSION = "v2"
EMBEDDING_RULE_VERSION = "v1-member-count-cap"
DEFAULT_MAX_MEMBER_COUNT = 30


def build_config_signature(
    *,
    embedding_model: str,
    embedding_provider: str | None,
    chunk_chars: int,
    chunk_overlap: int,
    max_member_count: int,
) -> str:
    payload = {
        "embedding_model": embedding_model,
        "embedding_provider": embedding_provider or "",
        "chunk_chars": chunk_chars,
        "chunk_overlap": chunk_overlap,
        "semantic_text_template": SEMANTIC_TEXT_TEMPLATE_VERSION,
        "embedding_rule_version": EMBEDDING_RULE_VERSION,
        "max_member_count": max_member_count,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def is_semantic_message(message: dict[str, Any]) -> bool:
    if int(message.get("message_type") or 0) != 1:
        return False

    text = str(message.get("text") or "").strip()
    if not text:
        return False
    if text.startswith("{") and text.endswith("}"):
        return False

    meaningful_tokens = re.findall(r"[0-9A-Za-z가-힣]+", text)
    if not meaningful_tokens:
        return False

    return sum(len(token) for token in meaningful_tokens) >= 2


def chunk_message(
    message: dict[str, Any],
    *,
    config_signature: str,
    embedding_model: str,
    embedding_provider: str | None,
    chunk_chars: int = DEFAULT_CHUNK_CHARS,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    if not is_semantic_message(message):
        return []

    text = str(message.get("text") or "").strip()
    source_signature = hashlib.sha256(
        f"{message['log_id']}:{message.get('timestamp')}:{text}".encode("utf-8")
    ).hexdigest()
    chunks = _split_text(text, chunk_chars=chunk_chars, chunk_overlap=chunk_overlap)
    records: list[dict[str, Any]] = []
    for chunk_index, chunk_text in enumerate(chunks):
        semantic_text = _build_semantic_text(message, chunk_text)
        chunk_id = hashlib.sha256(
            f"{config_signature}:{message['log_id']}:{chunk_index}:{semantic_text}".encode("utf-8")
        ).hexdigest()
        records.append(
            {
                "chunk_id": chunk_id,
                "log_id": int(message["log_id"]),
                "chat_id": int(message["chat_id"]),
                "chat_name": message.get("chat_name"),
                "sender": message.get("sender"),
                "timestamp": str(message["timestamp"]),
                "chunk_index": chunk_index,
                "chunk_text": semantic_text,
                "embedding_model": embedding_model,
                "embedding_provider": embedding_provider,
                "config_signature": config_signature,
                "source_signature": source_signature,
            }
        )
    return records


def normalize_vector(vector: Any) -> list[float]:
    array = np.asarray(vector, dtype=np.float32)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("Expected a one-dimensional embedding vector.")
    norm = float(np.linalg.norm(array))
    if norm == 0.0:
        raise ValueError("Expected a non-zero embedding vector.")
    return (array / norm).astype(float).tolist()


def reciprocal_rank_fuse(
    lexical_hits: list[dict[str, Any]],
    semantic_hits: list[dict[str, Any]],
    *,
    limit: int,
    fusion_k: int = DEFAULT_FUSION_K,
) -> list[dict[str, Any]]:
    fused: dict[int, dict[str, Any]] = {}
    for hits, source in ((lexical_hits, "lexical"), (semantic_hits, "semantic")):
        for rank, hit in enumerate(hits, start=1):
            log_id = int(hit["message"]["log_id"])
            fused_score = 1.0 / (fusion_k + rank)
            existing = fused.get(log_id)
            if existing is None:
                clone = {
                    "score": fused_score,
                    "message": hit["message"],
                    "context_before": hit.get("context_before", []),
                    "context_after": hit.get("context_after", []),
                    "sources": [source],
                }
                fused[log_id] = clone
                continue
            existing["score"] = float(existing["score"]) + fused_score
            sources = set(existing.get("sources", []))
            sources.add(source)
            existing["sources"] = sorted(sources)

    ranked = sorted(
        fused.values(),
        key=lambda item: (
            -float(item["score"]),
            item["message"].get("timestamp", ""),
            int(item["message"]["log_id"]),
        ),
    )
    return ranked[:limit]


def batched(items: Iterable[Any], batch_size: int) -> Iterable[list[Any]]:
    iterator = iter(items)
    while True:
        batch = list(islice(iterator, batch_size))
        if not batch:
            break
        yield batch


def _split_text(text: str, *, chunk_chars: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_chars:
        return [text]

    chunks: list[str] = []
    step = max(1, chunk_chars - chunk_overlap)
    start = 0
    while start < len(text):
        chunk = text[start : start + chunk_chars].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_chars >= len(text):
            break
        start += step
    return chunks


def _build_semantic_text(message: dict[str, Any], chunk_text: str) -> str:
    parts = []

    chat_name = str(message.get("chat_name") or "").strip()
    if chat_name:
        parts.append(f"대화방: {chat_name}")

    sender = str(message.get("sender") or "").strip()
    if sender:
        parts.append(f"보낸 사람: {sender}")

    direction = "내가 받은 메시지" if not bool(message.get("is_from_me")) else "내가 보낸 메시지"
    parts.append(f"방향: {direction}")
    parts.append(f"내용: {chunk_text}")
    return "\n".join(parts)
