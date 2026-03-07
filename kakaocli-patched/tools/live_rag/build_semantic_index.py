"""Build or update the local semantic sidecar."""

from __future__ import annotations

import argparse
import json
import sys
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
    batch_size: int = 200,
    progress: bool = False,
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

    if mode == "rebuild":
        store.clear_semantic_index()

    cursor = None if mode == "rebuild" else (existing["last_indexed_log_id"] if existing else None)
    remaining = limit
    processed_messages = 0
    indexed_messages = 0
    indexed_chunks = 0
    batches = 0
    last_log_id = cursor or 0

    while True:
        fetch_limit = batch_size if remaining is None else min(batch_size, remaining)
        if fetch_limit <= 0:
            break

        messages = store.iter_messages_for_embedding(after_log_id=cursor, limit=fetch_limit)
        if not messages:
            break

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
        for embed_batch in batched([chunk["chunk_text"] for chunk in chunks], DEFAULT_EMBED_BATCH_SIZE):
            vectors.extend(client.embed_documents(embed_batch))
        if len(vectors) != len(chunks):
            raise RuntimeError("Embedding response count did not match the number of chunks.")

        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk["vector"] = normalize_vector(vector)

        upsert_result = store.upsert_semantic_chunks(chunks)
        cursor = int(messages[-1]["log_id"])
        last_log_id = cursor
        processed_messages += len(messages)
        indexed_messages += upsert_result["messages_indexed"]
        indexed_chunks += upsert_result["chunks_indexed"]
        batches += 1
        if remaining is not None:
            remaining -= len(messages)

        store.set_runtime_state("semantic_config_signature", config_signature)
        store.set_runtime_state("semantic_embedding_model", embedding_model)
        store.set_runtime_state("semantic_embedding_provider", embedding_provider or "")
        store.set_runtime_state("semantic_chunk_chars", str(chunk_chars))
        store.set_runtime_state("semantic_chunk_overlap", str(chunk_overlap))
        store.set_runtime_state("semantic_last_indexed_log_id", str(last_log_id))

        if progress:
            print(
                json.dumps(
                    {
                        "stage": "build_index_progress",
                        "batch": batches,
                        "processed_messages": processed_messages,
                        "indexed_messages": indexed_messages,
                        "embedded_chunks": indexed_chunks,
                        "last_log_id": last_log_id,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                file=sys.stderr,
            )

        if remaining is not None and remaining <= 0:
            break

    return {
        "status": "ok",
        "mode": mode,
        "messages_considered": processed_messages,
        "embedded_chunks": indexed_chunks,
        "indexed_messages": indexed_messages,
        "updated_from_log_id": last_log_id,
        "model": embedding_model,
        "provider": embedding_provider,
        "config_signature": config_signature,
        "batches": batches,
        "batch_size": batch_size,
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
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--progress", action="store_true")
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
            batch_size=args.batch_size,
            progress=args.progress,
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
