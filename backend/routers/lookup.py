"""
backend/routers/lookup.py
==========================
POST /lookup — lightweight section Q&A without full brief generation.
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import LookupRequest, LookupResponse
from backend.services.retrieval import hybrid_search
from backend.services.llm import answer_lookup

router = APIRouter(prefix="/lookup", tags=["lookup"])


@router.post("", response_model=LookupResponse)
async def lookup_endpoint(request: LookupRequest) -> LookupResponse:
    """
    Answer a direct statute question using hybrid retrieval.
    e.g. 'What is the BNS equivalent of IPC 302?'
    Returns a concise answer with cited sections.
    """
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    # Try both old and new code since lookup queries can span both
    sections_new = hybrid_search(request.question, "new", top_k=request.top_k)
    sections_old = hybrid_search(request.question, "old", top_k=request.top_k)

    # Merge and deduplicate by chunk_id
    seen = set()
    combined = []
    for s in sections_new + sections_old:
        if s.chunk_id not in seen:
            seen.add(s.chunk_id)
            combined.append(s)

    top_sections = combined[:request.top_k]

    if not top_sections:
        return LookupResponse(
            answer="No matching provisions found in the corpus for this question.",
            cited_sections=[],
            cross_references=[],
        )

    answer = answer_lookup(request.question, top_sections)

    # Collect cross-references
    xrefs: list[str] = []
    for s in top_sections:
        xrefs.extend(s.cross_references)
    xrefs = list(dict.fromkeys(xrefs))  # deduplicate

    return LookupResponse(
        answer=answer,
        cited_sections=top_sections,
        cross_references=xrefs,
    )
