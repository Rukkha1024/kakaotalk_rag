"""FastAPI entrypoint for local Kakao Live RAG.

Serves health, stats, ingest, and retrieval endpoints
against the local SQLite-backed message store.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request

try:
    from .embedding_client import ExternalEmbeddingClient
    from .semantic_index import DEFAULT_SEMANTIC_TOP_K, reciprocal_rank_fuse
    from .store import LiveRAGStore
except ImportError:
    from embedding_client import ExternalEmbeddingClient
    from semantic_index import DEFAULT_SEMANTIC_TOP_K, reciprocal_rank_fuse
    from store import LiveRAGStore


DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / ".data" / "live_rag.sqlite3"


def create_app() -> FastAPI:
    app = FastAPI(title="kakaocli live rag", version="0.1.0")
    db_path = Path(os.environ.get("LIVE_RAG_DB_PATH", DEFAULT_DB_PATH))
    app.state.store = LiveRAGStore(db_path)
    app.state.db_path = db_path

    @app.get("/health")
    def health() -> dict[str, Any]:
        stats = app.state.store.stats()
        return {
            "status": "ok",
            "db_path": str(app.state.db_path),
            "message_count": stats.get("message_count", 0),
            "chat_count": stats.get("chat_count", 0),
            "last_ingested_log_id": stats.get("last_ingested_log_id"),
        }

    @app.get("/stats")
    def stats() -> dict[str, Any]:
        return app.state.store.stats()

    @app.post("/kakao")
    async def ingest(request: Request) -> dict[str, Any]:
        payload = await request.json()
        if not isinstance(payload, list):
            raise HTTPException(status_code=400, detail="Expected a JSON array of messages.")
        result = app.state.store.ingest_messages(payload, source="webhook")
        return result

    @app.get("/messages")
    def messages(
        limit: int = 50,
        chat_id: int | None = None,
        speaker: str | None = None,
        since_days: float | None = None,
    ) -> dict[str, Any]:
        return {
            "items": app.state.store.list_messages(
                limit=limit,
                chat_id=chat_id,
                speaker=speaker,
                since_days=since_days,
            )
        }

    @app.post("/retrieve")
    async def retrieve(request: Request) -> dict[str, Any]:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Expected a JSON object.")

        query = str(payload.get("query", "")).strip()
        if not query:
            raise HTTPException(status_code=400, detail="`query` is required.")
        mode = str(payload.get("mode", "lexical")).strip().lower()
        if mode not in {"lexical", "semantic", "hybrid"}:
            raise HTTPException(status_code=400, detail="`mode` must be lexical, semantic, or hybrid.")

        limit = int(payload.get("limit", 8))
        context_before = int(payload.get("context_before", 2))
        context_after = int(payload.get("context_after", 2))
        semantic_top_k = int(payload.get("semantic_top_k", DEFAULT_SEMANTIC_TOP_K))
        since_days_value = payload.get("since_days")
        since_days = float(since_days_value) if since_days_value is not None else None

        lexical_hits: list[dict[str, Any]] = []
        semantic_hits: list[dict[str, Any]] = []
        if mode in {"lexical", "hybrid"}:
            lexical_hits = app.state.store.retrieve_lexical(
                query=query,
                limit=limit,
                chat_id=payload.get("chat_id"),
                speaker=payload.get("speaker"),
                since_days=since_days,
                context_before=context_before,
                context_after=context_after,
            )
        if mode in {"semantic", "hybrid"}:
            settings = app.state.store.get_semantic_settings()
            if settings is None:
                raise HTTPException(status_code=400, detail="Semantic index is not built yet.")
            try:
                client = ExternalEmbeddingClient(
                    model=str(settings["embedding_model"]),
                    provider=settings.get("embedding_provider"),
                )
                query_vector = client.embed_query(query)
            except RuntimeError as error:
                raise HTTPException(status_code=502, detail=str(error)) from error
            semantic_hits = app.state.store.retrieve_semantic(
                query_vector=query_vector,
                limit=limit,
                semantic_top_k=semantic_top_k,
                chat_id=payload.get("chat_id"),
                speaker=payload.get("speaker"),
                since_days=since_days,
                context_before=context_before,
                context_after=context_after,
                config_signature=str(settings["config_signature"]),
            )

        if mode == "lexical":
            hits = lexical_hits
        elif mode == "semantic":
            hits = semantic_hits
        else:
            hits = reciprocal_rank_fuse(lexical_hits, semantic_hits, limit=limit)

        return {"query": query, "mode": mode, "hits": hits}

    return app


app = create_app()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local live RAG webhook server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
