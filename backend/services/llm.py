"""
backend/services/llm.py
========================
Gemini API wrappers for all LLM calls: fact extraction, brief generation, lookup.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Optional, List

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel, Field

from backend.models.schemas import (
    ExtractedFacts,
    SingleBrief,
    BriefSection,
    LegalSection,
)

import os
ROOT_ENV = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(ROOT_ENV)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Schemas for Structured Gemini Outputs
# ---------------------------------------------------------------------------

class PartiesSchema(BaseModel):
    accused: List[str] = Field(default_factory=list, description="Names of the accused parties if mentioned")
    victim: List[str] = Field(default_factory=list, description="Names of the victim(s) if mentioned")
    witnesses: List[str] = Field(default_factory=list, description="Names of the witness(es) if mentioned")


class FactExtractionSchema(BaseModel):
    parties: PartiesSchema = Field(default_factory=PartiesSchema)
    offence_type: Optional[str] = Field(None, description="e.g. murder / theft / cheating / assault")
    intent: Optional[str] = Field(None, description="mens rea / intent described")
    weapon_or_method: Optional[str] = Field(None, description="e.g. knife, poison, deception, fire")
    injury: Optional[str] = Field(None, description="nature and extent of harm")
    relationship: Optional[str] = Field(None, description="relationship between accused and victim")
    evidence_available: List[str] = Field(default_factory=list, description="list of evidence items mentioned")
    offence_date: Optional[str] = Field(None, description="ISO date YYYY-MM-DD or null")
    location: Optional[str] = Field(None, description="city, state or null")


# ---------------------------------------------------------------------------
# Fact extraction
# ---------------------------------------------------------------------------

EXTRACT_SYSTEM_PROMPT = """You are a legal fact-extraction assistant for Indian criminal law.
Given a case narrative in English (or Hindi transliterated), extract these facts into the specified JSON schema.
If a field cannot be determined from the narrative, use null or an empty list."""


def extract_facts(narrative: str, hint_date: Optional[date] = None) -> ExtractedFacts:
    """Extract structured facts from a free-text case narrative using Gemini."""
    prompt = f"Case narrative:\n\n{narrative}"
    if hint_date:
        prompt += f"\n\nNote: The offence date was provided as: {hint_date.isoformat()}"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=EXTRACT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=FactExtractionSchema,
                temperature=0.1
            )
        )
        data = json.loads(response.text)
    except Exception as exc:
        log.error(f"Fact extraction failed completely: {exc}")
        raise exc

    # Determine code era from offence date
    offence_date_str = data.get("offence_date")
    offence_date_obj: Optional[date] = None
    if offence_date_str:
        try:
            offence_date_obj = date.fromisoformat(offence_date_str)
        except ValueError:
            pass
    if hint_date:
        offence_date_obj = hint_date

    OLD_CUTOFF = date(2024, 7, 1)
    if offence_date_obj:
        code_era = "old" if offence_date_obj < OLD_CUTOFF else "new"
    else:
        code_era = "unknown"

    return ExtractedFacts(
        parties=data.get("parties", {}),
        offence_type=data.get("offence_type"),
        intent=data.get("intent"),
        weapon_or_method=data.get("weapon_or_method"),
        injury=data.get("injury"),
        relationship=data.get("relationship"),
        evidence_available=data.get("evidence_available") or [],
        offence_date=offence_date_obj,
        location=data.get("location"),
        code_era=code_era,
        raw_narrative=narrative,
    )


# ---------------------------------------------------------------------------
# Brief generation
# ---------------------------------------------------------------------------

PROSECUTION_SYSTEM = """You are a Senior Public Prosecutor in an Indian criminal court.
Your task is to draft a legal brief for the PROSECUTION side only.
Be direct, cite only the sections and case laws provided in the context.
Do not invent section numbers not in the provided context.
Flag any section you're unsure about by appending [UNVERIFIED] to its citation."""

DEFENSE_SYSTEM = """You are a Senior Defense Advocate in an Indian criminal court.
Your task is to draft a legal brief for the DEFENSE side only.
Be direct, cite only the sections and case laws provided in the context.
Do not invent section numbers not in the provided context.
Flag any section you're unsure about by appending [UNVERIFIED] to its citation."""


def _build_context(facts: ExtractedFacts, sections: list[LegalSection]) -> str:
    """Build the context string for brief generation."""
    ctx_parts = []
    ctx_parts.append(f"=== CASE FACTS ===")
    ctx_parts.append(f"Offence type: {facts.offence_type or 'Unknown'}")
    ctx_parts.append(f"Parties: {facts.parties}")
    ctx_parts.append(f"Intent: {facts.intent or 'Not stated'}")
    ctx_parts.append(f"Weapon/method: {facts.weapon_or_method or 'Not stated'}")
    ctx_parts.append(f"Injury: {facts.injury or 'Not stated'}")
    ctx_parts.append(f"Relationship: {facts.relationship or 'Not stated'}")
    ctx_parts.append(f"Evidence: {', '.join(facts.evidence_available) if facts.evidence_available else 'None listed'}")
    ctx_parts.append(f"Applicable code: {'Old code (IPC/CrPC/Evidence Act)' if facts.code_era == 'old' else 'New code (BNS/BNSS/BSA)'}")
    ctx_parts.append("\n=== RETRIEVED LEGAL SECTIONS ===")
    for s in sections[:12]:  # cap at 12 sections
        ctx_parts.append(
            f"\n[{s.act_name}] Section {s.section_number or '?'}: {s.section_title or ''}\n"
            f"{s.chunk_text[:800]}"
        )
        if s.cross_references:
            ctx_parts.append(f"Cross-references: {', '.join(s.cross_references)}")
    return "\n".join(ctx_parts)


def _call_llm(system_prompt: str, user_content: str, persona: str) -> SingleBrief:
    """Single LLM call to generate a brief using Gemini."""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_content,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=SingleBrief,
                temperature=0.3
            )
        )
        brief = SingleBrief.model_validate_json(response.text)
        brief.persona = persona
        return brief
    except Exception as exc:
        log.error(f"Brief generation failed ({persona}): {exc}")
        return SingleBrief(
            persona=persona,
            issues=[f"Brief generation failed: {str(exc)[:200]}"],
            applicable_provisions=[],
            arguments=[],
            supporting_precedents=[],
            prayer="",
        )


def generate_briefs(
    facts: ExtractedFacts,
    sections: list[LegalSection],
) -> tuple[SingleBrief, SingleBrief]:
    """
    Generate prosecution and defense briefs in parallel (using threading).
    Returns (prosecution_brief, defense_brief).
    """
    import concurrent.futures

    context = _build_context(facts, sections)
    user_msg = f"Generate a legal brief based on the following case context:\n\n{context}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        pros_future = executor.submit(_call_llm, PROSECUTION_SYSTEM, user_msg, "prosecution")
        def_future = executor.submit(_call_llm, DEFENSE_SYSTEM, user_msg, "defense")
        prosecution = pros_future.result()
        defense = def_future.result()

    return prosecution, defense


# ---------------------------------------------------------------------------
# Section lookup chat
# ---------------------------------------------------------------------------

LOOKUP_SYSTEM = """You are a legal research assistant for Indian criminal law.
Answer the user's question directly and concisely using only the provided legal section context.
Always cite sections in this format: ActName §SectionNumber (e.g. BNS §103, IPC §302).
If you reference an old code section, always mention its new code equivalent if one exists in the context.
Do NOT make up section numbers not in the context."""


def answer_lookup(question: str, sections: list[LegalSection]) -> str:
    """Answer a direct statute question using retrieved context using Gemini."""
    ctx = "\n\n".join(
        f"[{s.act_name}] §{s.section_number or '?'}: {s.section_title or ''}\n{s.chunk_text[:600]}"
        for s in sections[:8]
    )
    user_msg = f"Question: {question}\n\nContext:\n{ctx}"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_msg,
            config=genai_types.GenerateContentConfig(
                system_instruction=LOOKUP_SYSTEM,
                temperature=0.2
            )
        )
        return response.text.strip()
    except Exception as exc:
        log.error(f"Lookup failed: {exc}")
        return f"Could not generate answer: {str(exc)[:200]}"
