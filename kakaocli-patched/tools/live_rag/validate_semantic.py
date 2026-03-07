"""Validate semantic retrieval against a fixed fixture."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

try:
    from .build_semantic_index import build_semantic_index
    from .embedding_client import ExternalEmbeddingClient
    from .semantic_index import DEFAULT_EMBEDDING_MODEL
    from .store import LiveRAGStore
except ImportError:
    from build_semantic_index import build_semantic_index
    from embedding_client import ExternalEmbeddingClient
    from semantic_index import DEFAULT_EMBEDDING_MODEL
    from store import LiveRAGStore


FIXTURE_MESSAGES = [
    {
        "type": "message",
        "log_id": 101,
        "chat_id": 9001,
        "chat_name": "프로젝트 공지",
        "sender_id": 11,
        "sender": "민지",
        "text": "내일 회의는 다음 주 화요일로 미뤄졌어요.",
        "message_type": 1,
        "timestamp": "2026-03-01T09:00:00Z",
        "is_from_me": False,
    },
    {
        "type": "message",
        "log_id": 102,
        "chat_id": 9001,
        "chat_name": "프로젝트 공지",
        "sender_id": 12,
        "sender": "현우",
        "text": "자료 초안은 오늘 오후까지 올려 주세요.",
        "message_type": 1,
        "timestamp": "2026-03-01T09:03:00Z",
        "is_from_me": False,
    },
    {
        "type": "message",
        "log_id": 103,
        "chat_id": 9001,
        "chat_name": "프로젝트 공지",
        "sender_id": 13,
        "sender": "지연",
        "text": "점심은 12시 30분에 같이 먹어요.",
        "message_type": 1,
        "timestamp": "2026-03-01T09:05:00Z",
        "is_from_me": False,
    },
]

FIXTURE_QUERY = "회의가 연기됐다는 내용"
EXPECTED_LOG_ID = 101
FIXTURE_CHAT_METADATA = [
    {
        "id": 9001,
        "display_name": "프로젝트 공지",
        "member_count": 3,
        "type": "group",
    }
]


def run_validation(db_path: Path, *, embedding_model: str, embedding_provider: str | None) -> dict[str, object]:
    store = LiveRAGStore(db_path)
    store.ingest_messages(FIXTURE_MESSAGES, source="fixture")
    client = ExternalEmbeddingClient(model=embedding_model, provider=embedding_provider)
    build_semantic_index(
        store,
        client,
        mode="rebuild",
        limit=None,
        embedding_model=embedding_model,
        embedding_provider=embedding_provider,
        binary=None,
        chat_metadata=FIXTURE_CHAT_METADATA,
    )
    settings = store.get_semantic_settings()
    if settings is None:
        raise RuntimeError("Semantic settings were not persisted.")
    query_vector = client.embed_query(FIXTURE_QUERY)
    hits = store.retrieve_semantic(
        query_vector=query_vector,
        limit=3,
        semantic_top_k=3,
        config_signature=settings["config_signature"],
    )
    hit_log_ids = [int(hit["message"]["log_id"]) for hit in hits]
    if EXPECTED_LOG_ID not in hit_log_ids:
        raise RuntimeError(
            f"Expected fixture log_id {EXPECTED_LOG_ID} in semantic hits, got {hit_log_ids}"
        )
    return {
        "status": "ok",
        "fixture_query": FIXTURE_QUERY,
        "expected_log_id": EXPECTED_LOG_ID,
        "semantic_hit_log_ids": hit_log_ids,
        "model": embedding_model,
        "provider": embedding_provider,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate semantic Kakao Live RAG retrieval.")
    parser.add_argument("--db-path")
    parser.add_argument("--use-temp-db", action="store_true")
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--embedding-provider")
    args = parser.parse_args()

    try:
        if args.use_temp_db:
            with tempfile.TemporaryDirectory(prefix="live-rag-semantic-") as temp_dir:
                payload = run_validation(
                    Path(temp_dir) / "fixture.sqlite3",
                    embedding_model=args.embedding_model,
                    embedding_provider=args.embedding_provider,
                )
                print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            return

        if not args.db_path:
            raise SystemExit("Provide --db-path or use --use-temp-db.")

        payload = run_validation(
            Path(args.db_path),
            embedding_model=args.embedding_model,
            embedding_provider=args.embedding_provider,
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    except Exception as error:
        payload = {
            "status": "error",
            "stage": "validate_semantic",
            "message": str(error),
            "model": args.embedding_model,
            "provider": args.embedding_provider,
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
