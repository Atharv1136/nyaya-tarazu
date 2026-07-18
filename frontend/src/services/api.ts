/**
 * frontend/src/services/api.ts
 * ================================
 * Typed API client for all Nyaya Tarazu backend endpoints.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

// Types mirroring backend schemas
export interface ExtractedFacts {
  parties: Record<string, string[]>
  offence_type: string | null
  intent: string | null
  weapon_or_method: string | null
  injury: string | null
  relationship: string | null
  evidence_available: string[]
  offence_date: string | null
  location: string | null
  code_era: 'old' | 'new' | 'unknown'
  raw_narrative: string
}

export interface LegalSection {
  chunk_id: string
  act_name: string
  section_number: string | null
  section_title: string | null
  chunk_text: string
  code_era: 'old' | 'new'
  page_number: number | null
  cross_references: string[]
  similarity_score?: number
  rank_score?: number
}

export interface BriefSectionData {
  heading: string
  content: string
  citations: string[]
}

export interface CitationVerification {
  citation: string
  verified: boolean
  flag_reason?: string
}

export interface SingleBrief {
  persona: 'prosecution' | 'defense'
  issues: string[]
  applicable_provisions: BriefSectionData[]
  arguments: BriefSectionData[]
  supporting_precedents: BriefSectionData[]
  prayer: string
  citation_verifications: CitationVerification[]
  disclaimer: string
}

export interface BriefResponse {
  prosecution: SingleBrief
  defense: SingleBrief
  retrieval_context: LegalSection[]
}

export interface LookupResponse {
  answer: string
  cited_sections: LegalSection[]
  cross_references: string[]
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export async function extractFacts(
  narrative: string,
  offence_date?: string | null,
): Promise<ExtractedFacts> {
  return post('/extract-facts', { narrative, offence_date })
}

export async function retrieveSections(
  facts: ExtractedFacts,
  top_k = 10,
): Promise<{ sections: LegalSection[]; code_era_used: string; query_used: string }> {
  return post('/retrieve', { facts, top_k })
}

export async function generateBriefs(
  facts: ExtractedFacts,
  sections: LegalSection[],
): Promise<BriefResponse> {
  return post('/generate-brief', { facts, sections })
}

export async function exportBrief(
  brief: SingleBrief,
  format: 'docx' = 'docx',
  case_title?: string,
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ brief, format, case_title }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Export failed: ${res.status}`)
  }
  return res.blob()
}

export async function lookupSection(
  question: string,
  top_k = 5,
): Promise<LookupResponse> {
  return post('/lookup', { question, top_k })
}
