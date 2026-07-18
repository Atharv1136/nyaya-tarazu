"""
backend/routers/extract.py
===========================
POST /extract-facts — extract structured facts from a case narrative.
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import CaseNarrativeRequest, ExtractedFacts
from backend.services.llm import extract_facts

router = APIRouter(prefix="/extract-facts", tags=["extraction"])


@router.post("", response_model=ExtractedFacts)
async def extract_facts_endpoint(request: CaseNarrativeRequest) -> ExtractedFacts:
    """
    Extract structured facts from a free-text case narrative.
    Returns parties, offence type, intent, weapon/method, injury,
    relationship, evidence, offence date, and applicable code era.
    """
    if not request.narrative or len(request.narrative.strip()) < 20:
        raise HTTPException(
            status_code=422,
            detail="Couldn't find enough case detail here. Try adding who did what, and when.",
        )
    
    try:
        facts = extract_facts(request.narrative, request.offence_date)
        return facts
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Fact extraction failed: {str(exc)[:300]}",
        )
