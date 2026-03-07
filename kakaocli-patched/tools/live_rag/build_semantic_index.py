"""Build or update the local semantic sidecar."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .embedding_client import ExternalEmbeddingClient
    from .semantic_index import (
        DEFAULT_CHUNK_CHARS,
        DEFAULT_CHUNK_OVERLAP,
        DEFAULT_EMBED_BATCH_SIZE,
        DEFAULT_EMBEDDING_MODEL,
        batched,
        build_config_signature,
        chunk_message,
        normalize_vector,
    )
    from .store import LiveRAGStore
except ImportError:
    from embedding_client import ExternalEmbeddingClient
    from semantic_index import (
        DEFAULT_CHUNK_CHARS,
        DEFAULT_CHUNK_OVERLAP,
        DEFAULT_EMBED_BATCH_SIZE,
        DEFAULT_EMBEDDING_MODEL,
        batched,
        build_config_signature,
        chunk_message,
        normalize_vector,
    )
    from store import LiveRAGStore


DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / ".data" / "live_rag.sqlite3"


def build_semantic_index(
    store: LiveRAGStore,
    client: ExternalEmbeddingClient,
    *,
    mode: str,
    limit: int | None,
    embedding_model: str,
    embedding_provider: str | None,
    chunk_chars: int = DEFAULT_CHUNK_CHARS,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict[str, Any]:
    config_signature = build_config_signature(
        embedding_model=embedding_model,
        embedding_provider=embedding_provider,
        chunk_chars=chunk_chars,
        chunk_overlap=chunk_overlap,
    )
    existing = store.get_semantic_settings()
    if mode == "update" and existing and existing["config_signature"] != config_signature:
        raise RuntimeError(
            "Semantic config changed. Run with `--mode rebuild` to replace the old semantic sidecar."
        )

    after_log_id = None if mode == "rebuild" else (
        existing["last_indexed_log_id"] if existing else None
    )
    messages = store.iter_messages_for_embedding(after_log_id=after_log_id, limit=limit)

    chunks: list[dict[str, Any]] = []
    for message in messages:
        chunks.extend(
            chunk_message(
                message,
                config_signature=config_signature,
                embedding_model=embedding_model,
                embedding_provider=embedding_provider,
                chunk_chars=chunk_chars,
                chunk_overlap=chunk_overlap,
            )
        )

    vectors: list[list[float]] = []
    for batch in batched([chunk["chunk_text"] for chunk in chunks], DEFAULT_EMBED_BATCH_SIZE):
        vectors.extend(client.embed_documents(batch))
    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding response count did not match the number of chunks.")

    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk["vector"] = normalize_vector(vector)

    if mode == "rebuild":
        store.clear_semantic_index()
    upsert_result = store.upsert_semantic_chunks(chunks)
    last_log_id = max((int(message["log_id"]) for message in messages), default=after_log_id or 0)
    store.set_runtime_state("semantic_config_signature", config_signature)
    store.set_runtime_state("semantic_embedding_model", embedding_model)
    store.set_runtime_state("semantic_embedding_provider", embedding_provider or "")
    store.set_runtime_state("semantic_chunk_chars", str(chunk_chars))
    store.set_runtime_state("semantic_chunk_overlap", str(chunk_overlap))
    store.set_runtime_state("semantic_last_indexed_log_id", str(last_log_id))

    return {
        "status": "ok",
        "mode": mode,
        "messages_considered": len(messages),
        "embedded_chunks": upsert_result["chunks_indexed"],
        "indexed_messages": upsert_result["messages_indexed"],
        "updated_from_log_id": last_log_id,
        "model": embedding_model,
        "provider": embedding_provider,
        "config_signature": config_signature,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Kakao Live RAG semantic sidecar.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--mode", choices=("rebuild", "update"), default="update")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--embedding-provider")
    parser.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    args = parser.parse_args()

    store = LiveRAGStore(Path(args.db_path))
    client = ExternalEmbeddingClient(
        model=args.embedding_model,
        provider=args.embedding_provider,
    )
    try:
        payload = build_semantic_index(
            store,
            client,
            mode=args.mode,
            limit=args.limit,
            embedding_model=args.embedding_model,
            embedding_provider=args.embedding_provider,
            chunk_chars=args.chunk_chars,
            chunk_overlap=args.chunk_overlap,
        )
    except Exception as error:
        payload = {
            "status": "error",
            "stage": "build_index",
            "message": str(error),
            "mode": args.mode,
            "model": args.embedding_model,
            "provider": args.embedding_provider,
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        raise SystemExit(1) from error
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
