"""
ingest/embed_and_load.py
========================
Step 5: Read chunks.jsonl, embed each chunk via the Gemini embedding API,
and batch-insert rows into the Supabase `legal_sections` table.

Features
--------
• Gemini text-embedding-004 at 768 dimensions (MRL truncation)
• Batch embedding: up to 100 texts per API call
• Batch DB insert: 100 rows per Supabase insert
• tenacity retry + exponential backoff for transient failures
• Progress logging to stdout
• Failed chunks written to ingest/output/failed_chunks.jsonl

Usage
-----
    python -m ingest.embed_and_load

Requirements
------------
    SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY in .env
"""

import sys
# Force UTF-8 stdout on Windows to handle unicode progress bar characters
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from supabase import create_client, Client
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
CHUNKS_FILE = ROOT / "ingest" / "output" / "chunks.jsonl"
FAILED_FILE = ROOT / "ingest" / "output" / "failed_chunks.jsonl"

EMBEDDING_MODEL = "models/gemini-embedding-2"  # confirmed available model
EMBEDDING_DIM = 768          # matches the vector(768) column
EMBED_BATCH = 100            # texts per batch
INSERT_BATCH = 100           # rows per Supabase insert call
TABLE_NAME = "legal_sections"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
    log.error(
        "Missing env vars. Copy .env.example → .env and fill in "
        "SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY."
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# Retry-wrapped helpers
# ---------------------------------------------------------------------------

@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(log, logging.WARNING),
)
def embed_single_with_retry(text: str) -> list[float]:
    """Embed a single text with tenacity retry/exponential backoff."""
    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=genai_types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIM,
        ),
    )
    emb = list(response.embeddings[0].values)
    # Pad or truncate to EMBEDDING_DIM
    if len(emb) < EMBEDDING_DIM:
        emb = emb + [0.0] * (EMBEDDING_DIM - len(emb))
    elif len(emb) > EMBEDDING_DIM:
        emb = emb[:EMBEDDING_DIM]
    return emb


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts sequentially using gemini-embedding-004."""
    embeddings = []
    for i, text in enumerate(texts):
        emb = embed_single_with_retry(text)
        embeddings.append(emb)
        if i < len(texts) - 1:
            time.sleep(0.5)  # 0.5s delay between calls to respect API rate limits
    return embeddings



@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(log, logging.WARNING),
)
def insert_batch(rows: list[dict]) -> None:
    """Insert a batch of rows into Supabase."""
    supabase.table(TABLE_NAME).insert(rows).execute()


# ---------------------------------------------------------------------------
# Progress bar helper
# ---------------------------------------------------------------------------

def progress_bar(done: int, total: int, width: int = 30) -> str:
    filled = int(width * done / total) if total else 0
    bar = "█" * filled + "░" * (width - filled)
    pct = 100 * done // total if total else 0
    return f"[{bar}] {done}/{total} ({pct}%)"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not CHUNKS_FILE.exists():
        log.error("chunks.jsonl not found. Run chunk_sections.py first.")
        sys.exit(1)

    # Load all chunks
    with open(CHUNKS_FILE, encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f if line.strip()]

    total = len(chunks)
    log.info(f"Loaded {total} chunks from {CHUNKS_FILE}")

    failed: list[dict] = []
    processed = 0
    t0 = time.perf_counter()

    # Process in batches
    for batch_start in range(0, total, EMBED_BATCH):
        batch_chunks = chunks[batch_start: batch_start + EMBED_BATCH]
        texts = [c["chunk_text"] for c in batch_chunks]

        # --- Embed ---
        try:
            embeddings = embed_batch(texts)
        except Exception as exc:
            log.error(f"Embedding failed for batch {batch_start}–{batch_start+len(texts)-1}: {exc}")
            failed.extend(batch_chunks)
            processed += len(batch_chunks)
            print(progress_bar(processed, total))
            continue

        # --- Build rows ---
        rows = []
        for chunk, emb in zip(batch_chunks, embeddings):
            row = {
                "source_file":    chunk.get("source_file"),
                "act_name":       chunk.get("act_name"),
                "section_number": chunk.get("section_number"),
                "section_title":  chunk.get("section_title"),
                "page_number":    chunk.get("page_number"),
                "bounding_box":   chunk.get("bounding_box"),
                "code_era":       chunk.get("code_era"),
                "cross_references": chunk.get("cross_references", []),
                "extraction_method": chunk.get("extraction_method", "heading_split"),
                "chunk_text":     chunk.get("chunk_text"),
                "embedding":      emb,
            }
            rows.append(row)

        # --- Insert in sub-batches (rows already ≤ INSERT_BATCH) ---
        for sub_start in range(0, len(rows), INSERT_BATCH):
            sub = rows[sub_start: sub_start + INSERT_BATCH]
            try:
                insert_batch(sub)
            except Exception as exc:
                log.error(f"Insert failed for rows {batch_start+sub_start}–: {exc}")
                failed.extend(batch_chunks[sub_start: sub_start + len(sub)])

        processed += len(batch_chunks)
        elapsed = time.perf_counter() - t0
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (total - processed) / rate if rate > 0 else 0
        print(
            f"\r{progress_bar(processed, total)}  "
            f"{rate:.1f} chunks/s  ETA {eta:.0f}s     ",
            end="",
            flush=True,
        )

    print()  # newline after progress bar

    # Write failed chunks for manual review
    if failed:
        with open(FAILED_FILE, "w", encoding="utf-8") as f:
            for c in failed:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        log.warning(f"{len(failed)} chunks failed — written to {FAILED_FILE}")
    else:
        log.info("All chunks embedded and loaded successfully — no failures.")

    # Final count
    elapsed = time.perf_counter() - t0
    log.info(
        f"Done: {processed - len(failed)}/{total} rows inserted "
        f"in {elapsed:.1f}s ({(processed-len(failed))/elapsed:.1f} rows/s)"
    )

    # Verify row count in Supabase
    try:
        result = supabase.table(TABLE_NAME).select("id", count="exact").execute()
        db_count = result.count
        log.info(f"Supabase {TABLE_NAME} now has {db_count} rows (expected ~{total})")
    except Exception as exc:
        log.warning(f"Could not verify row count: {exc}")

    print("\nDone. Next step: python -m ingest.test_retrieval")


if __name__ == "__main__":
    main()
