# Nyaya Tarazu — System Architecture

## Overview

Nyaya Tarazu is a RAG-grounded legal drafting assistant. The architecture has five layers: ingestion (offline), retrieval, generation, verification, and delivery (frontend + export). Nothing about "training a model" happens here in the fine-tuning sense — the LLM stays general-purpose; all domain grounding comes from the retrieval layer, exactly as scoped in the PRD.

## High-level diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         INGESTION (offline)                       │
│                                                                    │
│  Law PDFs (all_laws/)  ──▶  opendataloader-pdf  ──▶  Markdown/JSON │
│                                     │                              │
│                                     ▼                              │
│                     Section-aware chunker (by heading)             │
│                                     │                              │
│                                     ▼                              │
│                        Gemini Embedding API (per chunk)            │
│                                     │                              │
│                                     ▼                              │
│                 Supabase Postgres + pgvector (legal_sections table)│
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                              RUNTIME                               │
│                                                                    │
│  React/TS frontend                                                │
│        │  case narrative (free text)                              │
│        ▼                                                          │
│  FastAPI: POST /extract-facts  ──▶ Gemini/Claude (structured JSON) │
│        │  structured facts                                        │
│        ▼                                                          │
│  FastAPI: POST /retrieve ──▶ Hybrid search (BM25 + pgvector cosine)│
│        │  top-k sections + judgments, each with metadata           │
│        ▼                                                          │
│  FastAPI: POST /generate-brief  (x2, parallel)                     │
│        │        │                                                  │
│   prosecution   defense                                            │
│   persona LLM   persona LLM                                        │
│   call          call                                               │
│        │        │                                                  │
│        ▼        ▼                                                  │
│  Citation verification layer (checks every cited section/case      │
│  against the retrieval corpus; flags/strips unverifiable ones)     │
│        │                                                           │
│        ▼                                                          │
│  Two structured, cited briefs returned to frontend                │
│        │                                                           │
│        ▼                                                          │
│  Export service (Word/PDF generation) + Section lookup chat mode  │
└──────────────────────────────────────────────────────────────────┘
```

## Layers in detail

### 1. Ingestion (offline / re-run when acts are amended)
- **Input:** raw PDFs (bare acts, mapping tables, judgments) in a local folder.
- **Parser:** `opendataloader-pdf` — chosen because it preserves heading hierarchy, table structure, and per-element bounding boxes, all of which matter for legal text (multi-column layouts, numbered sections, tables of punishments).
- **Chunking:** split by legal section/heading, not fixed token windows — a chunk boundary should always fall between sections, never mid-section.
- **Metadata per chunk:** `source_file`, `act_name`, `section_number`, `page_number`, `bounding_box`, `code_era` (`old` vs `new`).
- **Embedding:** Gemini Embedding API, batched.
- **Storage:** Supabase Postgres with the `pgvector` extension; one `legal_sections` table holds bare-act chunks, one `judgments` table holds case law chunks (same schema shape, different metadata: `case_name`, `citation`, `court`, `year`, `outcome`).

### 2. Retrieval
- **Hybrid search:** keyword (BM25 or Postgres full-text search) combined with vector cosine similarity. Pure semantic search under-retrieves exact section-number queries (e.g. a query containing "302" needs keyword matching, not just semantic similarity); pure keyword search misses paraphrased fact patterns. Combine and re-rank.
- **Old/new code awareness:** retrieval should be aware of `code_era` — if the case facts include a date before 1 July 2024, bias retrieval toward `old` (IPC/CrPC/Evidence Act); otherwise bias toward `new` (BNS/BNSS/BSA). Always surface the mapping-table cross-reference alongside the primary result.

### 3. Generation
- Two independent LLM calls per case, sharing the same retrieved context but different system personas ("prosecution counsel" / "defense counsel").
- Output format is structured (issues, applicable provisions, arguments, precedents, prayer/relief sought) — enforce this with a JSON schema or structured-output prompting, not free-form prose, so the frontend and export service can render it consistently.

### 4. Verification
- Every section number and case citation in the generated output is checked against the retrieval corpus (a simple lookup, not another LLM call).
- Unverifiable citations are flagged in the UI (not silently removed) so the lawyer knows exactly what to double-check.

### 5. Delivery
- **Frontend:** React + TypeScript, per `design.md`.
- **Export:** Word/PDF generation from the structured brief JSON, in a courtroom-drafting format.
- **Section lookup chat:** a lighter-weight endpoint that skips dual-brief generation and just answers direct statute questions (e.g. "BNS equivalent of IPC 302?") using the same retrieval layer.

## Suggested repo structure

```
nyaya-tarazu/
├── ingest/
│   ├── convert_pdfs.py
│   ├── chunk_sections.py
│   ├── embed_and_load.py
│   └── test_retrieval.py
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── routers/
│   │   ├── extract.py
│   │   ├── retrieve.py
│   │   ├── generate.py
│   │   └── export.py
│   ├── services/
│   │   ├── retrieval.py        # hybrid search
│   │   ├── verification.py     # citation checker
│   │   └── llm.py              # Gemini/Claude wrappers
│   └── models/                 # pydantic schemas
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── three/               # the 3D scale-of-justice scene
│   └── ...
├── supabase/
│   └── migrations/
├── docs/
│   ├── architecture.md          # this file
│   ├── flow.md
│   ├── design.md
│   └── dos-and-donts.md
└── .env.example
```

## Deployment

- Frontend: Netlify or Vercel.
- Backend: any container host reachable from Supabase (Railway/Render/Fly.io are reasonable defaults for a solo build); Supabase itself hosts Postgres + pgvector + Auth.
- Secrets (Supabase keys, Gemini/Claude API keys) live in environment variables only, never committed.
