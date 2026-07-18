"""
ingest/test_retrieval.py
========================
Step 6: Basic retrieval test — embed a query and return top-5 matching
chunks from Supabase using pgvector cosine similarity.

Runs 10 sample queries covering both old-code (IPC/CrPC/IEA) and new-code
(BNS/BNSS/BSA) terminology, then prints a results table.

Usage
-----
    python -m ingest.test_retrieval

    # Custom query
    python -m ingest.test_retrieval "dowry death punishment"

Requirements
------------
    SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY in .env
    The `match_legal_sections` RPC function must exist in Supabase.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
EMBEDDING_MODEL = "models/gemini-embedding-2"
EMBEDDING_DIM = 768
TOP_K = 5
MATCH_THRESHOLD = 0.5   # lower threshold for testing — tighten to 0.7 in prod

load_dotenv(ROOT / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
    print("ERROR: Missing env vars — copy .env.example → .env and fill in values.")
    sys.exit(1)

gemini_client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# Sample queries
# ---------------------------------------------------------------------------
SAMPLE_QUERIES = [
    ("punishment for murder",                    "IPC 302 / BNS 103"),
    ("IPC 302 murder punishment",                "IPC 302 (old code phrasing)"),
    ("BNS section 103",                          "BNS 103 (new code phrasing)"),
    ("theft in a dwelling house",                "IPC 380 / BNS 305"),
    ("bail in non-bailable offence",             "CrPC 437 / BNSS 480"),
    ("dowry death stridhan",                     "IPC 304B / BNS 80"),
    ("right of accused to free legal aid counsel", "CrPC 304 / BNSS 341"),
    ("admissibility of confession to police",    "Evidence Act 25 / BSA 23"),
    ("grievous hurt definition voluntarily cause", "IPC 320 / BNS 116-117"),
    ("outraging modesty sexual assault",         "IPC 354 / BNS 74-75"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def embed_query(text: str) -> list[float]:
    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[text],
        config=genai_types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIM,
        ),
    )
    return list(response.embeddings[0].values)


def search(query: str, top_k: int = TOP_K, era_filter: str | None = None) -> list[dict]:
    embedding = embed_query(query)
    params: dict = {
        "query_embedding": embedding,
        "match_threshold": MATCH_THRESHOLD,
        "match_count": top_k,
    }
    if era_filter:
        params["filter_era"] = era_filter

    result = supabase.rpc("match_legal_sections", params).execute()
    return result.data or []


def truncate(text: str, n: int = 120) -> str:
    return text[:n] + "…" if len(text) > n else text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_sample_queries() -> None:
    print("=" * 100)
    print("NYAYA TARAZU — RETRIEVAL TEST (top-5 per query)")
    print("=" * 100)

    passed = 0
    for i, (query, expected) in enumerate(SAMPLE_QUERIES, 1):
        print(f"\nQ{i:02d}: {query!r}")
        print(f"     Expected: {expected}")

        try:
            results = search(query)
        except Exception as exc:
            print(f"     ERROR: {exc}")
            continue

        if not results:
            print("     ⚠️  No results returned (similarity below threshold)")
            continue

        for rank, r in enumerate(results, 1):
            sim = r.get("similarity", 0)
            act = r.get("act_name", "?")
            sec = r.get("section_number", "?")
            title = r.get("section_title", "") or ""
            era = r.get("code_era", "?")
            snippet = truncate(r.get("chunk_text", ""), 100)
            print(
                f"     #{rank} [{era:3s}] {act} § {sec:>6s}  "
                f"sim={sim:.3f}  │ {truncate(title, 50)}"
            )
            if rank == 1:
                print(f"          ↳ {snippet}")

        # Very rough pass criterion: top-1 similarity > 0.65
        top_sim = results[0].get("similarity", 0) if results else 0
        if top_sim >= 0.65:
            print("     ✅ PASS")
            passed += 1
        else:
            print(f"     ❓ LOW CONFIDENCE (top sim={top_sim:.3f})")

    print("\n" + "=" * 100)
    print(f"RESULT: {passed}/{len(SAMPLE_QUERIES)} queries passed (threshold: top-1 similarity ≥ 0.65)")
    print("=" * 100)


def run_custom_query(query: str) -> None:
    print(f"\nQuery: {query!r}")
    results = search(query)
    if not results:
        print("No results (try lowering MATCH_THRESHOLD in test_retrieval.py).")
        return
    for rank, r in enumerate(results, 1):
        sim = r.get("similarity", 0)
        act = r.get("act_name", "?")
        sec = r.get("section_number", "?")
        era = r.get("code_era", "?")
        title = r.get("section_title", "") or ""
        print(f"  #{rank} [{era}] {act} § {sec}  sim={sim:.3f}  {title}")
        print(f"       {truncate(r.get('chunk_text',''), 150)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_custom_query(" ".join(sys.argv[1:]))
    else:
        run_sample_queries()
