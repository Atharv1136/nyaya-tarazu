# Task for Antigravity: Nyaya Tarazu — Full Project Build

## Before you start: a scope note on "all laws in India"

India has 800+ central acts alone, plus thousands of state-level acts, so there's no single finite "all laws" file — but for a criminal-law-focused product, you don't need all of them. Below is a curated, verified set across the domains this product actually touches: core criminal law (the primary focus), plus the handful of adjacent civil/commercial/cyber acts that come up constantly in real practice (cheque-bounce cases under the Negotiable Instruments Act, cyber offences under the IT Act, contract disputes, consumer matters, corporate offences). If a specific act is needed later that isn't here, the India Code portal (indiacode.nic.in) is the full, authoritative catalog to search.

## Step 1 — Download the law corpus

Create the folder and download every file below. Run this on Windows (PowerShell/Git Bash with `curl` available, or WSL):

```bash
mkdir "D:\be project\nyaya_tarazu_laws" && cd "D:\be project\nyaya_tarazu_laws"

:: --- Core criminal law: old codes (govern any offence before 1 July 2024) ---
curl -L -o IPC_1860.pdf "https://www.indiacode.nic.in/bitstream/123456789/2263/1/A1860-45.pdf"
curl -L -o CrPC_1973.pdf "https://www.indiacode.nic.in/bitstream/123456789/15272/1/the_code_of_criminal_procedure,_1973.pdf"
curl -L -o Evidence_Act_1872.pdf "https://www.indiacode.nic.in/bitstream/123456789/4218/1/THE-INDIAN-EVIDENCE-ACT-1872.pdf"

:: --- Core criminal law: new codes (govern offences on/after 1 July 2024) ---
curl -L -o BNS_2023.pdf "https://ncert.nic.in/pdf/module/New_Laws_2023/BNS-2023E.pdf"
curl -L -o BNSS_2023.pdf "https://ncert.nic.in/pdf/module/New_Laws_2023/BNSS-2023E.pdf"
curl -L -o BSA_2023.pdf "https://ncert.nic.in/pdf/module/New_Laws_2023/BAS-2023E.pdf"

:: --- Old-to-new code mapping tables (Corpus B — critical, do not skip) ---
curl -L -o BNS_with_IPC_mapping_NCRB.pdf "https://www.ncrb.gov.in/uploads/SankalanPortal/DownloadPDF/BNS2023.pdf"
curl -L -o BNSS_with_CrPC_mapping_NCRB.pdf "https://www.ncrb.gov.in/uploads/SankalanPortal/DownloadPDF/BNSS2023.pdf"
curl -L -o BNS_to_IPC_comparison_BPRD.pdf "https://bprd.nic.in/uploads/pdf/COMPARISON%20SUMMARY%20BNS%20to%20IPC%20.pdf"
curl -L -o BNSS_to_CrPC_comparison_BPRD.pdf "https://bprd.nic.in/uploads/pdf/Comparison%20summary%20BNSS%20to%20CrPC.pdf"
curl -L -o BSA_to_IEA_comparison_BPRD.pdf "https://bprd.nic.in/uploads/pdf/Comparison%20Summary%20BSA%20to%20IEA.pdf"

:: --- Adjacent civil/commercial/cyber acts that come up constantly in criminal practice ---
curl -L -o Consumer_Protection_Act_2019.pdf "https://www.indiacode.nic.in/bitstream/123456789/16939/1/a2019-35.pdf"
curl -L -o Indian_Contract_Act_1872.pdf "https://www.indiacode.nic.in/bitstream/123456789/2187/2/A187209.pdf"
curl -L -o Negotiable_Instruments_Act_1881.pdf "https://www.indiacode.nic.in/bitstream/123456789/15327/1/negotiable_instruments_act,_1881.pdf"
curl -L -o IT_Act_2000.pdf "https://www.indiacode.nic.in/bitstream/123456789/13116/1/it_act_2000_updated.pdf"
curl -L -o Companies_Act_2013.pdf "https://www.indiacode.nic.in/bitstream/123456789/15198/1/the_companies_act,_2013_no._18_of_2013_date_29.08.2013.pdf"
```

If any individual `curl` call fails (some government sites rate-limit scripted requests), retry it with a browser-like header: `curl -L -A "Mozilla/5.0" -o <file> "<url>"`. Report back which files (if any) failed to download rather than silently skipping them.

## Step 2 — Convert every PDF with OpenDataLoader

Install and use `opendataloader-pdf` for the PDF-to-RAG conversion step — this is the required tool for this project, don't substitute a different PDF library:

```bash
pip install -U opendataloader-pdf
```

It wraps a Java CLI, so confirm Java 11+ is available first (`java -version`); install a JDK if missing and tell me if that step was needed.

```python
import opendataloader_pdf

opendataloader_pdf.convert(
    input_path=[r"D:\be project\nyaya_tarazu_laws"],
    output_dir="ingest/output/",
    format="markdown,json",
)
```

Batch all files into this single call rather than looping per file, since each `convert()` call spawns its own JVM process.

## Step 3 — Build the full ingestion → RAG pipeline

Follow `architecture.md` (included in this project) for the exact pipeline shape. In order:

1. **Section-aware chunking** — split the converted Markdown/JSON by legal section/heading (never mid-section), and tag each chunk with `source_file`, `act_name`, `section_number`, `page_number`, `bounding_box`, and `code_era` (`old` for IPC/CrPC/Evidence Act/Contract Act/NI Act/IT Act/Companies Act/Consumer Protection Act, `new` for BNS/BNSS/BSA).
2. **Supabase schema** — enable `pgvector`, create a `legal_sections` table (and a separate `judgments` table for future case-law ingestion) per the schema in `architecture.md`. Show me the SQL before running it against the live project.
3. **Embeddings** — Gemini Embedding API, batched, with retry/backoff and a log of anything that fails.
4. **Hybrid retrieval** — BM25/keyword + pgvector cosine similarity, combined ranking. Pure semantic search under-retrieves exact section-number queries, so both matter.
5. **Retrieval test** — run at least 10 sample queries (mixing old-code phrasing like "IPC 302" and new-code phrasing like "BNS 103") and show me the results before moving on.

## Step 4 — Build the backend

FastAPI service with these endpoints (see `architecture.md` for the full request/response shape):
- `POST /extract-facts` — structures a free-text case narrative into parties, offence type, intent, weapon/method, injury, relationship, evidence available, and offence date.
- `POST /retrieve` — hybrid search against the vector DB using the extracted facts; route to `old` or `new` code corpus based on offence date.
- `POST /generate-brief` — two parallel LLM calls (prosecution persona / defense persona), grounded only in retrieved context, returning structured briefs (issues, provisions, arguments, precedents, prayer).
- Citation verification — check every generated section/case citation against the retrieval corpus; flag anything unverifiable rather than silently dropping it.
- `POST /export` — generate a Word/PDF document from a structured brief.
- `POST /lookup` — lightweight direct Q&A mode for quick statute questions, skipping brief generation.

## Step 5 — Build the frontend

Follow `flow.md` for the exact screens and states, and `design.md` + `dos-and-donts.md` for every visual decision — palette, type, the 3D scale-of-justice hero, and the explicit list of things not to do (no purple, no generic AI-look, no green, no purple gradients, nothing that looks like a templated AI-generated website). Build:
- Landing page with the 3D animated scale-of-justice hero (React Three Fiber), dark-ink background, saffron/brass palette
- Auth (Supabase Auth)
- Case intake screen
- Fact confirmation screen (editable, not a black box)
- Results screen: literal split view, Prosecution (saffron) | Defense (brass), with citations in the mono type
- Export flow
- Section Lookup Chat screen

Build both backend and frontend fully — this is not a prototype-only pass. Wire the frontend to the real backend endpoints, not mocked data.

## Reference documents in this project

Read these before building anything, they contain the full spec:
- `architecture.md` — system design, data flow, repo structure
- `flow.md` — every screen, state, and error/empty case
- `design.md` — full visual design system and the 3D signature element
- `dos-and-donts.md` — hard constraints on what the UI must never look like

## Verification / done criteria

- All 16 PDFs downloaded and converted without silent failures
- `legal_sections` table populated, row count roughly matches expected section counts
- Retrieval test passes on at least 8/10 sample queries
- All 6 backend endpoints working against real data, not stubs
- Frontend fully wired end-to-end: paste a case, get two real cited briefs, export one
- 3D hero renders and tips correctly on scroll/interaction, with a working reduced-motion fallback
- No purple, no green, no generic AI-template look anywhere — spot-check against `dos-and-donts.md` before calling this done
- Give me a final summary: what was built, what's stubbed vs real, and anything that needs my review before this is demo-ready
