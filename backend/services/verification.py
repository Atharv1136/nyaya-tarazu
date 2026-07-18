"""
backend/services/verification.py
==================================
Citation verification: checks every generated citation against the retrieval corpus.
"""

from __future__ import annotations

import re
from typing import List

from backend.models.schemas import CitationVerificationResult, LegalSection

# Regex to find citations like: BNS §103, IPC 302, CrPC §161, BSA §65
CITATION_PATTERN = re.compile(
    r"\b(BNS|BNSS|BSA|IPC|CrPC|IEA|NI Act|IT Act|Companies Act)\s*[§Ss]?\s*(\d+[A-Z]?)\b",
    re.IGNORECASE,
)

# Canonical act name aliases
ACT_ALIASES: dict[str, list[str]] = {
    "BNS": ["Bharatiya Nyaya Sanhita", "BNS"],
    "BNSS": ["Bharatiya Nagarik Suraksha Sanhita", "BNSS"],
    "BSA": ["Bharatiya Sakshya Adhiniyam", "BSA"],
    "IPC": ["Indian Penal Code", "IPC"],
    "CrPC": ["Code of Criminal Procedure", "CrPC"],
    "IEA": ["Indian Evidence Act", "IEA"],
}


def _normalize_act(raw: str) -> str:
    """Normalize act abbreviation to uppercase canonical form."""
    return raw.strip().upper()


def extract_citations_from_text(text: str) -> List[str]:
    """Extract all citation strings from a piece of text."""
    found = []
    for m in CITATION_PATTERN.finditer(text):
        act = m.group(1).upper()
        sec = m.group(2)
        found.append(f"{act} §{sec}")
    return list(dict.fromkeys(found))  # deduplicate, preserve order


def verify_citations(
    citations: List[str],
    retrieved_sections: List[LegalSection],
) -> List[CitationVerificationResult]:
    """
    Check each citation string against the retrieved corpus.
    
    A citation is 'verified' if a section with matching act abbreviation
    and section_number exists in the retrieved corpus.
    
    Citations flagged as [UNVERIFIED] by the LLM are automatically flagged.
    """
    results: List[CitationVerificationResult] = []

    # Build lookup: (act_abbr, section_number) → True
    corpus_index: set[tuple[str, str]] = set()
    for section in retrieved_sections:
        sec_num = (section.section_number or "").strip()
        act = section.act_name

        # Match act to abbreviations
        for abbr, aliases in ACT_ALIASES.items():
            if any(alias.lower() in act.lower() for alias in aliases):
                corpus_index.add((abbr, sec_num))
                break

    for citation in citations:
        # Check if LLM itself flagged it
        if "[UNVERIFIED]" in citation:
            clean = citation.replace("[UNVERIFIED]", "").strip()
            results.append(CitationVerificationResult(
                citation=clean,
                verified=False,
                flag_reason="Flagged as unverified by generation model — verify manually.",
            ))
            continue

        # Parse the citation
        m = CITATION_PATTERN.match(citation.strip())
        if not m:
            results.append(CitationVerificationResult(
                citation=citation,
                verified=False,
                flag_reason="Citation format not recognized — verify manually.",
            ))
            continue

        act = m.group(1).upper()
        sec = m.group(2)

        if (act, sec) in corpus_index:
            results.append(CitationVerificationResult(
                citation=citation,
                verified=True,
            ))
        else:
            results.append(CitationVerificationResult(
                citation=citation,
                verified=False,
                flag_reason=f"Not found in retrieval corpus — verify manually in {act}.",
            ))

    return results


def attach_verifications(brief_sections: list, retrieved: List[LegalSection]) -> list:
    """
    Walk through brief sections (applicable_provisions, arguments, etc.)
    and verify each citation inline. Attaches verification flags to the sections.
    """
    all_citations: List[str] = []
    for section in brief_sections:
        all_citations.extend(section.citations)

    verifications = verify_citations(all_citations, retrieved)
    return verifications
