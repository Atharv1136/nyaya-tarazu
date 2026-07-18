"""
backend/routers/generate.py
============================
POST /generate-brief — generate dual prosecution + defense briefs in parallel.
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import BriefRequest, BriefResponse
from backend.services.llm import generate_briefs
from backend.services.verification import extract_citations_from_text, verify_citations

router = APIRouter(prefix="/generate-brief", tags=["generation"])


def _collect_all_text(brief) -> str:
    """Collect all text from a brief for citation extraction."""
    parts = []
    for section_list in [
        brief.applicable_provisions,
        brief.arguments,
        brief.supporting_precedents,
    ]:
        for s in section_list:
            parts.append(s.content)
            parts.extend(s.citations)
    return " ".join(parts)


@router.post("", response_model=BriefResponse)
async def generate_brief_endpoint(request: BriefRequest) -> BriefResponse:
    """
    Generate two parallel legal briefs:
    - Prosecution (saffron side)
    - Defense (brass side)
    Both are grounded in the retrieved sections and have citations verified.
    """
    if not request.sections:
        raise HTTPException(
            status_code=422,
            detail="No retrieved sections provided. Run /retrieve first.",
        )

    try:
        prosecution, defense = generate_briefs(request.facts, request.sections)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Brief generation failed: {str(exc)[:300]}")

    # Citation verification pass
    pros_text = _collect_all_text(prosecution)
    def_text = _collect_all_text(defense)

    pros_citations = extract_citations_from_text(pros_text)
    def_citations = extract_citations_from_text(def_text)

    prosecution.citation_verifications = verify_citations(pros_citations, request.sections)
    defense.citation_verifications = verify_citations(def_citations, request.sections)

    return BriefResponse(
        prosecution=prosecution,
        defense=defense,
        retrieval_context=request.sections,
    )
