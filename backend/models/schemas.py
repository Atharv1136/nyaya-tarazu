"""
backend/models/schemas.py
=========================
All Pydantic request/response models for the Nyaya Tarazu API.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared / sub-models
# ---------------------------------------------------------------------------

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class CitationVerificationResult(BaseModel):
    citation: str
    verified: bool
    flag_reason: Optional[str] = None  # e.g. "not found in corpus, verify manually"


class LegalSection(BaseModel):
    """A retrieved legal section chunk from the DB."""
    chunk_id: str
    act_name: str
    section_number: Optional[str]
    section_title: Optional[str]
    chunk_text: str
    code_era: Literal["old", "new"]
    page_number: Optional[int]
    cross_references: List[str] = []
    similarity_score: Optional[float] = None
    rank_score: Optional[float] = None


# ---------------------------------------------------------------------------
# /extract-facts
# ---------------------------------------------------------------------------

class CaseNarrativeRequest(BaseModel):
    narrative: str = Field(..., description="Free-text case narrative from the lawyer")
    offence_date: Optional[date] = Field(None, description="Offence date if known (determines old/new code)")


class ExtractedFacts(BaseModel):
    parties: dict = Field(
        default_factory=dict,
        description="e.g. {'accused': ['Ramesh Kumar'], 'victim': ['Sita Devi']}"
    )
    offence_type: Optional[str] = Field(None, description="e.g. 'murder', 'theft', 'cheating'")
    intent: Optional[str] = Field(None, description="mens rea / intent described")
    weapon_or_method: Optional[str] = Field(None, description="e.g. 'knife', 'poison', 'deception'")
    injury: Optional[str] = Field(None, description="Nature and extent of harm")
    relationship: Optional[str] = Field(None, description="Relationship between accused and victim")
    evidence_available: List[str] = Field(default_factory=list, description="Evidence mentioned in the narrative")
    offence_date: Optional[date] = Field(None)
    location: Optional[str] = Field(None)
    code_era: Literal["old", "new", "unknown"] = Field("unknown", description="Determined by offence_date")
    raw_narrative: str = Field("", description="Original narrative for reference")


# ---------------------------------------------------------------------------
# /retrieve
# ---------------------------------------------------------------------------

class RetrievalRequest(BaseModel):
    facts: ExtractedFacts
    top_k: int = Field(10, ge=1, le=50)
    force_code_era: Optional[Literal["old", "new"]] = None  # override auto-detection


class RetrievalResponse(BaseModel):
    sections: List[LegalSection]
    code_era_used: Literal["old", "new"]
    query_used: str


# ---------------------------------------------------------------------------
# /generate-brief
# ---------------------------------------------------------------------------

class BriefRequest(BaseModel):
    facts: ExtractedFacts
    sections: List[LegalSection]


class BriefSection(BaseModel):
    """A single section in a legal brief."""
    heading: str
    content: str
    citations: List[str] = []


class SingleBrief(BaseModel):
    persona: Literal["prosecution", "defense"]
    issues: List[str]
    applicable_provisions: List[BriefSection]
    arguments: List[BriefSection]
    supporting_precedents: List[BriefSection]
    prayer: str
    citation_verifications: List[CitationVerificationResult] = []
    disclaimer: str = (
        "AI-generated draft. Verify against original sources before "
        "relying on this in any proceeding."
    )


class BriefResponse(BaseModel):
    prosecution: SingleBrief
    defense: SingleBrief
    retrieval_context: List[LegalSection] = []


# ---------------------------------------------------------------------------
# /export
# ---------------------------------------------------------------------------

class ExportRequest(BaseModel):
    brief: SingleBrief
    format: Literal["docx", "pdf"] = "docx"
    case_title: Optional[str] = None


# ---------------------------------------------------------------------------
# /lookup
# ---------------------------------------------------------------------------

class LookupRequest(BaseModel):
    question: str = Field(..., description="Direct statute question e.g. 'BNS equivalent of IPC 302?'")
    top_k: int = Field(5, ge=1, le=20)


class LookupResponse(BaseModel):
    answer: str
    cited_sections: List[LegalSection]
    cross_references: List[str] = []


# ---------------------------------------------------------------------------
# Error response
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
