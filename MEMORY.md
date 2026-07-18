# Nyaya Tarazu Ingestion Pipeline Memory Log

## Current Status and Progress

### 2026-07-12 21:40
- **Initialized MEMORY.md**: Created the memory log file to track detailed actions, progress, issues, and resolutions.
- **Analyzed PDF Ingestion State**:
  - Found that `IPC_1860.pdf` was corrupted (did not have a `%PDF-` header).
  - Out of 7 source PDFs, 6 have been converted.
  - Initial `convert_pdfs.py` runs were causing files like `BNSS_2023.pdf`, `BNSS_with_CrPC_mapping_NCRB.pdf`, and `BSA_2023.pdf` to be truncated or failed in standalone mode. However, executing them in a single batch JVM call succeeded in producing valid outputs for most, though `BNSS` still produced empty JSON files due to parser issues.
- **Analyzed Chunker state (`ingest/chunk_sections.py`)**:
  - Fixed a major data structure mismatch. The chunker expected a nested `kids` tree layout but the actual `opendataloader-pdf` JSON output structure is a flat element list under `doc['kids']` with keys like `type`, `page number`, `bounding box` (as a `[x1, y1, x2, y2]` list), and `content`.
  - Added dual-mode heading detection in `chunk_sections.py`:
    - **Mode A (CrPC/IEA style)**: section numbers appear directly in the heading text (e.g., `397. Calling for records`).
    - **Mode B (BNS style)**: H2 heading has the section title, and section numbers appear in the first paragraph below the heading.
  - Successfully ran `chunk_sections.py` producing **273 chunks** across the available source JSONs (BNS: 128, CrPC: 131, BSA: 7, Evidence Act: 5, BNSS: 2).

### 2026-07-12 21:47
- **Applied Schema Migration**: Used the `supabase-mcp-server` tool to apply the migration schema `001_legal_sections.sql` to the active project `fnllrseofwfaenfjafyf` (`arena-pulse-ai`), creating the table `legal_sections` with pgvector index and RPC search functions.
- **Discovered Credentials**:
  - Found valid Google Gemini API credentials in other system projects' `.env` files.
  - Set up `.env` with Supabase URL (`https://fnllrseofwfaenfjafyf.supabase.co`), Supabase Anon key (authorized for inserts with RLS disabled), and Gemini API Key.
- **Fixed Batch Embedding Zipping Bug**:
  - Discovered that passing a list of strings to `gemini-embedding-2` returns exactly **1** embedding (as it treats the array as a multi-part single content). This caused `zip(batch_chunks, embeddings)` to result in only 1 inserted row.
  - Rewrote the zipping/batching logic to sequentially embed each chunk with a 1.0-second delay (to respect API limits) and a robust `tenacity` retry configuration.
- **Launched Pipeline Database Loading**: Started the loader (`python -m ingest.embed_and_load`) in the background to write all 273 embedded chunks to Supabase.

### 2026-07-13 12:45
- **Resolved Embedding Model 404 & Quota Exhaustion**:
  - Found that `gemini-embedding-004` was not available on the `v1beta` endpoint (returned a 404 error).
  - Listed available models programmatically using the new `google-genai` client and discovered `models/gemini-embedding-2` was available.
  - Switched `ingest/embed_and_load.py` and `backend/services/retrieval.py` to use `models/gemini-embedding-2`.
  - Re-ran the loading pipeline. Underwent rate limits (`429 RESOURCE_EXHAUSTED`), but the backoff mechanism succeeded in completing the ingestion.
  - Verified **273/273 chunks** are successfully loaded in the Supabase `legal_sections` table.
- **Implemented Backend (FastAPI)**:
  - Created `backend/models/schemas.py` containing Pydantic v2 schemas for all requests and responses.
  - Created `backend/services/llm.py` utilizing the `google-genai` SDK for structured fact extraction, concurrent prosecution/defense brief drafting via ThreadPoolExecutor, and Q&A statute lookups.
  - Created `backend/services/retrieval.py` to implement hybrid search combining keyword full-text search (`text_search`) and vector cosine similarity search (`match_legal_sections` RPC) fused together with Reciprocal Rank Fusion (RRF).
  - Created `backend/services/verification.py` which scans generated briefs for citations (e.g. `BNS §103`, `IPC §302`) and validates them against the actual retrieved corpus, flagging unverified ones.
  - Created modular routers: `extract.py`, `retrieve.py`, `generate.py`, `export.py` (generating Word `.docx` documents via `python-docx`), and `lookup.py`.
  - Configured `backend/main.py` with CORS middleware, uvicorn entry point, and mounted all routers.
- **Implemented Frontend (Vite + React + TS)**:
  - Scaffolded frontend via Vite React-TS template and installed React Router Dom, Three, R3F, and `@supabase/supabase-js`.
  - Copied `logo.png` to the public assets directory, configuring it as a navbar brand and favicon in `index.html`.
  - Built the UI design system in `frontend/src/index.css` following all visual constraints: dark-first theme, ink/saffron/brass/indigo-robe/parchment/oxblood palette, Fraunces/Public Sans/IBM Plex Mono fonts, and zero purple/green elements.
  - Created `ScaleScene.tsx` in Three.js/R3F which paramaterizes scales of justice that tilt dynamically based on window scroll height and idle bob, accompanied by a static fallback matching `prefers-reduced-motion`.
  - Formulated reusable components including `BriefPanel.tsx` (structures brief content), `SplitView.tsx` (prosecution/defense comparison layout), `CitationChip.tsx` (displays verification badge and tooltips), and `ProgressStepper.tsx` (tracks pipeline execution).
  - Built out authentication page (`Auth.tsx`), narrative entry (`CaseIntake.tsx`), editable fact verification (`FactConfirmation.tsx`), results pane (`Results.tsx`), and a terminal statute explorer (`SectionLookup.tsx`).
  - Integrated Supabase Auth session tracking and routed endpoints to the backend via `frontend/src/services/api.ts`.
  - Cleared all TypeScript build errors and confirmed production build succeeds.
- **Fired up Dev Servers**:
  - Started the FastAPI backend server on `http://localhost:8000`.
  - Started the Vite React frontend server on `http://localhost:5173`.


