"""Unstructured-data agent: semantic search over phone-call transcripts.

Transcripts are embedded with Voyage AI and stored in a local Chroma
vector store, keyed by client_id so searches can be scoped per client.
"""
from __future__ import annotations

import json

import chromadb
import voyageai

from . import config

_COLLECTION_NAME = "client_transcripts"
_voyage_client: voyageai.Client | None = None
_chroma_collection = None


def _get_voyage() -> voyageai.Client:
    global _voyage_client
    if _voyage_client is None:
        _voyage_client = voyageai.Client(api_key=config.VOYAGE_API_KEY)
    return _voyage_client


def _get_collection():
    """Return the Chroma collection, building the index on first use."""
    global _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection

    chroma_client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    collection = chroma_client.get_or_create_collection(_COLLECTION_NAME)

    manifest = _load_manifest()
    if collection.count() != len(manifest):
        _rebuild_index(chroma_client, collection, manifest)

    _chroma_collection = collection
    return collection


def _load_manifest() -> list[dict]:
    manifest_path = config.TRANSCRIPTS_DIR / "manifest.json"
    with open(manifest_path) as f:
        return json.load(f)


def _rebuild_index(chroma_client, collection, manifest: list[dict]) -> None:
    """Re-embed every transcript and repopulate the collection from scratch."""
    chroma_client.delete_collection(_COLLECTION_NAME)
    collection = chroma_client.get_or_create_collection(_COLLECTION_NAME)

    documents, ids, metadatas = [], [], []
    for entry in manifest:
        text = (config.TRANSCRIPTS_DIR / entry["file"]).read_text()
        documents.append(text)
        ids.append(entry["file"])
        metadatas.append(
            {
                "client_id": entry["client_id"],
                "date": entry["date"],
                "topic": entry["topic"],
            }
        )

    voyage = _get_voyage()
    result = voyage.embed(
        documents, model=config.VOYAGE_EMBED_MODEL, input_type="document"
    )
    collection.add(
        ids=ids,
        embeddings=result.embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    global _chroma_collection
    _chroma_collection = collection


def search_client_conversations(
    query: str, client_id: str | None = None, top_k: int = 5
) -> list[dict]:
    """Semantically search past client phone-call transcripts.

    Args:
        query: What to search for (e.g. "concerns about market volatility").
        client_id: Optional client_id to restrict the search to one client's calls.
        top_k: Max number of matching call excerpts to return.
    """
    collection = _get_collection()
    voyage = _get_voyage()
    query_embedding = voyage.embed(
        [query], model=config.VOYAGE_EMBED_MODEL, input_type="query"
    ).embeddings[0]

    where = {"client_id": client_id.strip().upper()} if client_id else None
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
    )

    matches = []
    for doc, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        matches.append(
            {
                "client_id": meta["client_id"],
                "date": meta["date"],
                "topic": meta["topic"],
                "transcript_excerpt": doc,
                "relevance_score": round(1 - distance, 3),
            }
        )
    return matches
