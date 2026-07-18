"""
ingest/chunk_sections.py
========================
Step 3: Read the JSON output from convert_pdfs.py and split each act into
section-level chunks with rich metadata.

Chunking strategy
-----------------
1. Load doc["kids"] — a flat list of all elements in reading order.
2. Walk elements; when a heading node is found (type == "heading",
   heading_level <= 2), treat it as a new section boundary.
3. Accumulate all content beneath that heading until the next
   same-or-higher-level heading.
4. Extract section_number via regex on the heading text.
5. Attach act_name, code_era, and cross_references (from NCRB mapping tables)
   inferred from the source filename.
6. Fallback: if a PDF produced <500 chars of total text, emit sliding-window
   chunks of ~1000 chars with 100-char overlap.

JSON element structure (opendataloader-pdf v2.4.7)
---------------------------------------------------
doc = {
  "file name": str,
  "number of pages": int,
  "kids": [                      # flat list, reading order
    {
      "type": "heading"|"paragraph"|"list"|"table"|"caption",
      "content": str,            # text content (heading/paragraph/caption)
      "page number": int,
      "bounding box": [x1, y1, x2, y2],  # PDF points
      "heading level": int,      # 1-6, only on type==heading
      "list items": [...],       # only on type==list
    }, ...
  ]
}

Output
------
ingest/output/chunks.jsonl  -- one JSON object per line

Usage
-----
    python -m ingest.chunk_sections
"""

from __future__ import annotations

import json
import re
import sys
import textwrap
import uuid
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "ingest" / "output"
CHUNKS_FILE = OUTPUT_DIR / "chunks.jsonl"

# ---------------------------------------------------------------------------
# Act metadata lookup keyed by PDF stem
# ---------------------------------------------------------------------------
ACT_META: dict[str, dict] = {
    "BNSS_2023": {
        "act_name": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "short_name": "BNSS",
        "code_era": "new",
    },
    "BNSS_with_CrPC_mapping_NCRB": {
        "act_name": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "short_name": "BNSS",
        "code_era": "new",
        "has_mapping": True,
    },
    "BNS_with_IPC_mapping_NCRB": {
        "act_name": "Bharatiya Nyaya Sanhita, 2023",
        "short_name": "BNS",
        "code_era": "new",
        "has_mapping": True,
    },
    "BSA_2023": {
        "act_name": "Bharatiya Sakshya Adhiniyam, 2023",
        "short_name": "BSA",
        "code_era": "new",
    },
    "CrPC_1973": {
        "act_name": "Code of Criminal Procedure, 1973",
        "short_name": "CrPC",
        "code_era": "old",
    },
    "Evidence_Act_1872": {
        "act_name": "Indian Evidence Act, 1872",
        "short_name": "IEA",
        "code_era": "old",
    },
    # IPC_1860.pdf is corrupt; IPC text is in BNS_with_IPC_mapping_NCRB.pdf
}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
# Matches section numbers: "302.", "Section 302", "Sec. 302", "302A.", "103."
SECTION_RE = re.compile(
    r"(?:Section\s+|Sec\.\s*|S\.\s*)?(\d+[A-Z]?)\s*[.:\-\u2014]",
    re.IGNORECASE,
)

# Cross-reference patterns in NCRB mapping PDFs
XREF_IPC_RE = re.compile(
    r"(?:IPC|I\.P\.C\.)\s*[:\-]?\s*(\d+[A-Z]?(?:\s*,\s*\d+[A-Z]?)*)",
    re.IGNORECASE,
)
XREF_CRPC_RE = re.compile(
    r"(?:CrPC|Cr\.P\.C\.)\s*[:\-]?\s*(\d+[A-Z]?(?:\s*,\s*\d+[A-Z]?)*)",
    re.IGNORECASE,
)
XREF_IEA_RE = re.compile(
    r"(?:IEA|Evidence Act)\s*[:\-]?\s*(\d+[A-Z]?(?:\s*,\s*\d+[A-Z]?)*)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_section_number(text: str) -> str | None:
    m = SECTION_RE.search(text)
    return m.group(1) if m else None


def extract_cross_references(text: str, meta: dict) -> list[str]:
    refs: list[str] = []
    short = meta.get("short_name", "")
    if short == "BNS":
        for m in XREF_IPC_RE.finditer(text):
            for n in m.group(1).split(","):
                refs.append(f"IPC {n.strip()}")
    elif short == "BNSS":
        for m in XREF_CRPC_RE.finditer(text):
            for n in m.group(1).split(","):
                refs.append(f"CrPC {n.strip()}")
    elif short == "BSA":
        for m in XREF_IEA_RE.finditer(text):
            for n in m.group(1).split(","):
                refs.append(f"IEA {n.strip()}")
    return list(dict.fromkeys(r for r in refs if r.split()[-1]))


def bbox_to_dict(bbox: Any) -> dict | None:
    """Convert [x1,y1,x2,y2] list to a dict."""
    if isinstance(bbox, list) and len(bbox) == 4:
        return {"x1": bbox[0], "y1": bbox[1], "x2": bbox[2], "y2": bbox[3]}
    if isinstance(bbox, dict):
        return bbox
    return None


def bbox_union(bboxes: list[Any]) -> dict | None:
    dicts = [bbox_to_dict(b) for b in bboxes]
    valid = [d for d in dicts if d]
    if not valid:
        return None
    return {
        "x1": min(d["x1"] for d in valid),
        "y1": min(d["y1"] for d in valid),
        "x2": max(d["x2"] for d in valid),
        "y2": max(d["y2"] for d in valid),
    }


def elem_text(elem: dict) -> str:
    """Extract all text from an element, including list item children."""
    parts: list[str] = []
    content = elem.get("content", "")
    if content:
        parts.append(content.strip())
    # List items
    for item in elem.get("list items", []):
        item_text = item.get("content", "").strip()
        if item_text:
            parts.append(item_text)
        # nested list items
        for sub in item.get("kids", []):
            s = sub.get("content", "").strip()
            if s:
                parts.append(s)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Primary chunker: heading-boundary split
# ---------------------------------------------------------------------------

def chunk_by_headings(elements: list[dict], meta: dict, source_file: str) -> list[dict]:
    """
    Split element stream into section chunks.

    Two modes detected automatically:
    - Mode A (CrPC/IEA style): section numbers appear IN the heading text
      e.g. heading "397. Calling for records—..."
      -> split whenever a heading whose content starts with a section number is found

    - Mode B (BNS style): section titles are in H2 headings, section numbers
      appear in the first paragraph beneath that heading
      e.g. heading "Definitions." then paragraph "2. In this Sanhita..."
      -> split on every H2 heading; extract section number from first paragraph

    Mode is detected by checking whether any of the first 20 headings contain
    a section number in the heading text.
    """
    # Detect mode
    # Mode A: most headings contain section numbers  (CrPC/IEA style)
    # Mode B: headings are section TITLES, numbers appear in paragraphs (BNS style)
    heading_elems = [e for e in elements if e.get("type") == "heading"]
    # Count headings that contain a section number
    sec_headings = sum(1 for h in heading_elems if extract_section_number(elem_text(h)))
    total_headings = len(heading_elems)
    h2_headings = sum(1 for h in heading_elems if h.get("heading level", 99) <= 2)

    # Mode B indicators:
    # - Many H2 headings (BNS has 131 H2 section titles)
    # - Very few of them contain section numbers (< 10%)
    mode = "B" if (h2_headings > 50 and sec_headings / max(total_headings, 1) < 0.10) else "A"

    chunks: list[dict] = []
    cur_heading: str = ""
    cur_section_num: str | None = None
    cur_page: int | None = None
    cur_bboxes: list[Any] = []
    cur_texts: list[str] = []
    # For mode B: section number extracted from first para of chunk
    mode_b_sec_found: bool = False

    def flush():
        nonlocal cur_heading, cur_section_num, cur_page, cur_bboxes, cur_texts, mode_b_sec_found
        text = "\n".join(t for t in cur_texts if t).strip()
        if not text:
            return
        xrefs = extract_cross_references(text, meta) if meta.get("has_mapping") else []
        chunks.append({
            "chunk_id":         str(uuid.uuid4()),
            "source_file":      source_file,
            "act_name":         meta["act_name"],
            "section_number":   cur_section_num,
            "section_title":    cur_heading,
            "page_number":      cur_page,
            "bounding_box":     bbox_union(cur_bboxes),
            "code_era":         meta["code_era"],
            "cross_references": xrefs,
            "extraction_method": "heading_split",
            "chunk_text":       text,
        })
        cur_heading = ""
        cur_section_num = None
        cur_page = None
        cur_bboxes = []
        cur_texts = []
        mode_b_sec_found = False

    for elem in elements:
        etype = elem.get("type", "")
        page  = elem.get("page number")
        bbox  = elem.get("bounding box")
        hlevel = elem.get("heading level", 99)
        text  = elem_text(elem)

        if not text:
            continue

        if mode == "A":
            # Mode A: heading with section number = new chunk
            if etype == "heading":
                sec_num = extract_section_number(text)
                if sec_num is not None:
                    flush()
                    cur_heading     = text
                    cur_section_num = sec_num
                    cur_page        = page
                    if bbox:
                        cur_bboxes = [bbox]
                    cur_texts = [text]
                else:
                    cur_texts.append(text)
                    if bbox:
                        cur_bboxes.append(bbox)
            else:
                cur_texts.append(text)
                if page and cur_page is None:
                    cur_page = page
                if bbox:
                    cur_bboxes.append(bbox)

        else:
            # Mode B: H2 heading = section boundary; number from first paragraph
            if etype == "heading" and hlevel <= 2 and text.strip() not in ("", "HomePage"):
                flush()
                cur_heading     = text
                cur_section_num = None
                cur_page        = page
                mode_b_sec_found = False
                if bbox:
                    cur_bboxes = [bbox]
                cur_texts = [text]
            else:
                # First paragraph: try to extract section number if not found yet
                if not mode_b_sec_found and etype != "heading":
                    sec_num = extract_section_number(text)
                    if sec_num:
                        cur_section_num = sec_num
                        mode_b_sec_found = True
                cur_texts.append(text)
                if page and cur_page is None:
                    cur_page = page
                if bbox:
                    cur_bboxes.append(bbox)

    flush()
    return chunks



# ---------------------------------------------------------------------------
# Fallback: sliding-window for scanned / text-poor PDFs
# ---------------------------------------------------------------------------

def chunk_sliding_window(
    full_text: str,
    meta: dict,
    source_file: str,
    window: int = 1000,
    overlap: int = 100,
) -> list[dict]:
    chunks = []
    start = 0
    while start < len(full_text):
        end = min(start + window, len(full_text))
        snippet = full_text[start:end].strip()
        if snippet:
            chunks.append({
                "chunk_id":         str(uuid.uuid4()),
                "source_file":      source_file,
                "act_name":         meta["act_name"],
                "section_number":   extract_section_number(snippet),
                "section_title":    None,
                "page_number":      None,
                "bounding_box":     None,
                "code_era":         meta["code_era"],
                "cross_references": [],
                "extraction_method": "fallback_sliding_window",
                "chunk_text":       snippet,
            })
        start += window - overlap
    return chunks


# ---------------------------------------------------------------------------
# Process one JSON file
# ---------------------------------------------------------------------------

def process_pdf_json(json_path: Path, meta: dict) -> list[dict]:
    source_file = json_path.stem + ".pdf"

    with open(json_path, encoding="utf-8") as f:
        doc = json.load(f)

    elements: list[dict] = doc.get("kids", [])

    # Build full text to decide if fallback is needed
    full_text = "\n".join(e.get("content", "") for e in elements if e.get("content"))

    if len(full_text.strip()) < 500:
        print(f"    WARNING: {json_path.name} has only {len(full_text)} chars - using sliding window fallback")
        md_path = json_path.with_suffix(".md")
        if md_path.exists():
            md_text = md_path.read_text(encoding="utf-8")
            if len(md_text.strip()) > len(full_text.strip()):
                full_text = md_text
        return chunk_sliding_window(full_text, meta, source_file)

    return chunk_by_headings(elements, meta, source_file)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    all_chunks: list[dict] = []
    total_by_act: dict[str, int] = {}
    warnings: list[str] = []

    json_files = sorted(OUTPUT_DIR.glob("*.json"))
    if not json_files:
        print("ERROR: No JSON files found in ingest/output/. Run convert_pdfs.py first.", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(json_files)} JSON file(s) from {OUTPUT_DIR}\n")

    for jf in json_files:
        stem = jf.stem
        meta = ACT_META.get(stem)
        if meta is None:
            print(f"  SKIP: Unknown stem '{stem}' - not in ACT_META")
            continue

        print(f"  >> {jf.name} -> {meta['act_name']}")
        try:
            chunks = process_pdf_json(jf, meta)
        except Exception as exc:
            import traceback
            print(f"    ERROR: {exc}")
            traceback.print_exc()
            warnings.append(f"{jf.name}: {exc}")
            continue

        count = len(chunks)
        total_by_act[meta["act_name"]] = total_by_act.get(meta["act_name"], 0) + count
        all_chunks.extend(chunks)
        headings_only = [c for c in chunks if c["extraction_method"] == "heading_split"]
        print(f"    -> {count} chunks ({len(headings_only)} heading-split, {count - len(headings_only)} fallback)")

    # Write chunks.jsonl
    CHUNKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\n=== Chunking summary ===")
    print(f"Total chunks : {len(all_chunks)}")
    print(f"Output file  : {CHUNKS_FILE}")
    print()
    for act, count in sorted(total_by_act.items()):
        print(f"  {count:5d}  {act}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"   * {w}")

    # Print 3 sample chunks
    if all_chunks:
        import random
        print("\n=== Sample chunks (3 random) ===")
        for chunk in random.sample(all_chunks, min(3, len(all_chunks))):
            print(f"\n  [{chunk['act_name']}] Section {chunk['section_number'] or '?'}")
            print(f"  Title  : {chunk['section_title'] or '(no title)'}")
            print(f"  Era    : {chunk['code_era']}")
            print(f"  Page   : {chunk['page_number']}")
            print(f"  XRefs  : {chunk['cross_references']}")
            print(f"  Method : {chunk['extraction_method']}")
            preview = textwrap.shorten(chunk["chunk_text"], 200, placeholder="...")
            print(f"  Text   : {preview}")

    print("\nDone. Next step: review SQL migration, then python -m ingest.embed_and_load")


if __name__ == "__main__":
    main()
