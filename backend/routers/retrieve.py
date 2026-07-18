"""
backend/routers/retrieve.py
============================
POST /retrieve — hybrid retrieval against the vector DB.
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import RetrievalRequest, RetrievalResponse, ExtractedFacts
from backend.services.retrieval import hybrid_search, resolve_code_era

router = APIRouter(prefix="/retrieve", tags=["retrieval"])


def _facts_to_query(facts: ExtractedFacts) -> str:
    """Build a natural language retrieval query from extracted facts."""
    parts = []
    if facts.offence_type:
        parts.append(facts.offence_type)
    if facts.weapon_or_method:
        parts.append(facts.weapon_or_method)
    if facts.intent:
        parts.append(facts.intent)
    if facts.injury:
        parts.append(facts.injury)
    return " ".join(parts) or "criminal offence India"


@router.post("", response_model=RetrievalResponse)
async def retrieve_endpoint(request: RetrievalRequest) -> RetrievalResponse:
    """
    Hybrid retrieval (BM25 + pgvector) against the legal_sections table.
    Routes to old (IPC/CrPC/IEA) or new (BNS/BNSS/BSA) corpus based on offence date.
    """
    facts = request.facts
    code_era = resolve_code_era(facts.offence_date, request.force_code_era)
    query = _facts_to_query(facts)

    if not query.strip():
        raise HTTPException(
            status_code=422,
            detail="No matching provisions found. This may be outside the current corpus (criminal law only).",
        )

    try:
        sections = hybrid_search(query, code_era, top_k=request.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(exc)[:300]}")

    if not sections:
        raise HTTPException(
            status_code=404,
            detail="No matching provisions found. This may be outside the current corpus (criminal law only).",
        )

    return RetrievalResponse(
        sections=sections,
        code_era_used=code_era,
        query_used=query,
    )
