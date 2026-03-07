"""Build or update the local semantic sidecar."""

from __future__ import annotations

import argparse
import json
import subprocess
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
        DEFAULT_MAX_MEMBER_COUNT,
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
        DEFAULT_MAX_MEMBER_COUNT,
        batched,
        build_config_signature,
        chunk_message,
        normalize_vector,
    )
    from store import LiveRAGStore


DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / ".data" / "live_rag.sqlite3"
DEFAULT_BINARY = Path(__file__).resolve().parents[2] / ".build" / "release" / "kakaocli"
DEFAULT_CHAT_LIMIT = 5000


def load_chat_metadata(binary: str, *, chat_limit: int = DEFAULT_CHAT_LIMIT) -> list[dict[str, Any]]:
    result = subprocess.run(
        [binary, "chats", "--limit", str(chat_limit), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, list) or not payload:
        raise RuntimeError("`kakaocli chats --json` returned no chat metadata.")
    return payload


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
    max_member_count: int = DEFAULT_MAX_MEMBER_COUNT,
    batch_size: int = 200,
    progress: bool = False,
    binary: str | None = str(DEFAULT_BINARY),
    chat_metadata: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    config_signature = build_config_signature(
        embedding_model=embedding_model,
        embedding_provider=embedding_provider,
        chunk_chars=chunk_chars,
        chunk_overlap=chunk_overlap,
        max_member_count=max_member_count,
    )
    existing = store.get_semantic_settings()
    if mode == "update" and existing and existing["config_signature"] != config_signature:
        raise RuntimeError(
            "Semantic config changed. Run with `--mode rebuild` to replace the old semantic sidecar."
        )

    try:
        refreshed_chat_metadata = chat_metadata
        if refreshed_chat_metadata is None:
            if not binary:
                raise RuntimeError("Chat metadata refresh requires a kakaocli binary path.")
            refreshed_chat_metadata = load_chat_metadata(binary)
        metadata_result = store.upsert_chat_metadata(refreshed_chat_metadata)
    except subprocess.CalledProcessError as error:
        stderr = (error.stderr or "").strip()
        raise RuntimeError(f"Failed to refresh chat metadata via `kakaocli chats --json`: {stderr or error}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError("`kakaocli chats --json` returned invalid JSON.") from error

    missing_metadata_count = store.count_embedding_messages_missing_chat_metadata(
        after_log_id=None if mode == "rebuild" else (existing["last_indexed_log_id"] if existing else None),
        limit=limit,
    )
    if missing_metadata_count > 0:
        raise RuntimeError(
            "Chat metadata refresh was incomplete for semantic embedding candidates. "
            "Aborting before mutating semantic state."
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

        messages = store.iter_messages_for_embedding(
            after_log_id=cursor,
            limit=fetch_limit,
            max_member_count=max_member_count,
        )
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
        store.set_runtime_state("semantic_max_member_count", str(max_member_count))
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
        "chat_metadata_count": metadata_result["chat_count"],
        "excluded_chat_count": len(store.excluded_chat_ids_for_embedding(max_member_count=max_member_count)),
        "max_member_count": max_member_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Kakao Live RAG semantic sidecar.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--binary", default=str(DEFAULT_BINARY))
    parser.add_argument("--mode", choices=("rebuild", "update"), default="update")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--embedding-provider")
    parser.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    parser.add_argument("--max-member-count", type=int, default=DEFAULT_MAX_MEMBER_COUNT)
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
            max_member_count=args.max_member_count,
            batch_size=args.batch_size,
            progress=args.progress,
            binary=args.binary,
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
