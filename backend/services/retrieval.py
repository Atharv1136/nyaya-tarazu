"""
backend/services/retrieval.py
==============================
Hybrid retrieval: Postgres full-text search (BM25-like) + pgvector cosine similarity.
Results are combined using Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import logging
import os
from datetime import date
from typing import List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from supabase import create_client, Client

from backend.models.schemas import LegalSection

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
ROOT_ENV = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(ROOT_ENV)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

EMBEDDING_MODEL = "models/gemini-embedding-2"  # confirmed available
EMBEDDING_DIM = 768
OLD_CODE_CUTOFF = date(2024, 7, 1)  # BNS/BNSS/BSA effective date

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Query embedding
# ---------------------------------------------------------------------------

def embed_query(query: str) -> list[float]:
    """Embed a retrieval query using gemini-embedding-2."""
    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config=genai_types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIM,
        ),
    )
    emb = list(response.embeddings[0].values)
    if len(emb) < EMBEDDING_DIM:
        emb = emb + [0.0] * (EMBEDDING_DIM - len(emb))
    elif len(emb) > EMBEDDING_DIM:
        emb = emb[:EMBEDDING_DIM]
    return emb


# ---------------------------------------------------------------------------
# Old/new code era routing
# ---------------------------------------------------------------------------

def resolve_code_era(offence_date: Optional[date], force: Optional[str] = None) -> str:
    if force in ("old", "new"):
        return force
    if offence_date is None:
        return "new"  # default to new code if unknown
    return "old" if offence_date < OLD_CODE_CUTOFF else "new"


# ---------------------------------------------------------------------------
# Vector search via Supabase RPC
# ---------------------------------------------------------------------------

def vector_search(
    query_embedding: list[float],
    code_era: str,
    top_k: int = 15,
) -> List[dict]:
    """Run pgvector cosine similarity search via Supabase RPC."""
    try:
        response = supabase.rpc(
            "match_legal_sections",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.3,
                "match_count": top_k,
                "p_code_era": code_era,
            },
        ).execute()
        return response.data or []
    except Exception as exc:
        log.warning(f"Vector search failed: {exc}")
        return []


# ---------------------------------------------------------------------------
# Full-text (keyword) search via Postgres ts_query
# ---------------------------------------------------------------------------

def keyword_search(
    query: str,
    code_era: str,
    top_k: int = 15,
) -> List[dict]:
    """Run Postgres full-text search on the section text column."""
    try:
        # Convert plain text query to OR-spaced tsquery for fts to avoid strict AND matching and syntax errors
        words = [w.strip() for w in query.split() if len(w.strip()) > 3]
        stopwords = {"with", "from", "that", "this", "these", "those", "their", "them", "cause", "clear", "fatal", "severe", "and", "the"}
        words = [w for w in words if w.lower() not in stopwords]
        ts_query = " | ".join(words) if words else "criminal"

        response = (
            supabase.table("legal_sections")
            .select(
                "id, act_name, section_number, section_title, "
                "chunk_text, code_era, page_number, cross_references"
            )
            .eq("code_era", code_era)
            .limit(top_k)
            .text_search("chunk_text", ts_query, options={"config": "english"})
            .execute()
        )
        return response.data or []
    except Exception as exc:
        log.warning(f"Keyword search failed: {exc}")
        return []


# ---------------------------------------------------------------------------
# RRF fusion
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    id_key: str = "id",
    k: int = 60,
) -> list[dict]:
    """
    Combine multiple ranked result lists using Reciprocal Rank Fusion.
    Returns a single merged, re-ranked list with a 'rrf_score' field.
    """
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked):
            doc_id = doc.get(id_key, "")
            if not doc_id:
                continue
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
            docs[doc_id] = doc

    # Sort by descending RRF score
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    result = []
    for doc_id in sorted_ids:
        doc = docs[doc_id].copy()
        doc["rrf_score"] = scores[doc_id]
        result.append(doc)
    return result


# ---------------------------------------------------------------------------
# Public hybrid search function
# ---------------------------------------------------------------------------

def hybrid_search(
    query: str,
    code_era: str,
    top_k: int = 10,
) -> List[LegalSection]:
    """
    Perform hybrid retrieval: keyword + vector, fused with RRF.
    Returns top_k LegalSection objects ordered by combined relevance.
    """
    log.info(f"Hybrid search: query='{query[:80]}' era={code_era} top_k={top_k}")

    # 1. Embed query
    try:
        query_emb = embed_query(query)
    except Exception as exc:
        log.error(f"Query embedding failed: {exc}")
        query_emb = None

    # 2. Vector search (if embedding succeeded)
    vector_results = []
    if query_emb:
        vector_results = vector_search(query_emb, code_era, top_k=top_k * 2)
        log.info(f"  Vector results: {len(vector_results)}")

    # 3. Keyword search
    keyword_results = keyword_search(query, code_era, top_k=top_k * 2)
    log.info(f"  Keyword results: {len(keyword_results)}")

    # 4. RRF fusion
    fused = reciprocal_rank_fusion([vector_results, keyword_results])
    top_fused = fused[:top_k]

    # 5. Convert to LegalSection models
    sections: List[LegalSection] = []
    for doc in top_fused:
        try:
            sections.append(LegalSection(
                chunk_id=str(doc.get("id", "")),
                act_name=doc.get("act_name", ""),
                section_number=doc.get("section_number"),
                section_title=doc.get("section_title"),
                chunk_text=doc.get("chunk_text", ""),
                code_era=doc.get("code_era", code_era),
                page_number=doc.get("page_number"),
                cross_references=doc.get("cross_references", []) or [],
                similarity_score=doc.get("similarity", doc.get("similarity_score")),
                rank_score=doc.get("rrf_score"),
            ))
        except Exception as exc:
            log.warning(f"Could not parse LegalSection from {doc}: {exc}")

    log.info(f"  Returning {len(sections)} sections after RRF fusion")
    return sections
