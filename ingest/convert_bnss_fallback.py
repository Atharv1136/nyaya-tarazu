"""
ingest/convert_bnss_fallback.py
===============================
Fallback converter for BNSS_2023.pdf and BNSS_with_CrPC_mapping_NCRB.pdf.

These PDFs have PDF 1.5/1.6 compressed object streams (ObjStm) that cause
opendataloader-pdf's Apache PDFBox parser and pypdf to reject them when
opened as standalone files (they worked in the initial opendataloader batch
because the JVM was in a specific initialization state).

This script uses pdfminer.six (which has better XRef/ObjStm recovery) to
extract text page-by-page, then builds a synthetic JSON structure that is
100% compatible with chunk_sections.py.

Usage:
    python -m ingest.convert_bnss_fallback
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LTFigure
except ImportError:
    raise SystemExit("Run: .venv\\Scripts\\pip install pdfminer.six")

ROOT = Path(__file__).parent.parent
SOURCE_DIR = ROOT / "nyaya_tarazu_laws"
OUTPUT_DIR = ROOT / "ingest" / "output"

TARGETS = [
    "BNSS_2023.pdf",
    "BNSS_with_CrPC_mapping_NCRB.pdf",
]

# Section heading: "480." or "480A." at start of line (after stripping)
SECTION_RE = re.compile(r"^(\d+[A-Z]?)\.\s+\S")
CHAPTER_RE = re.compile(r"^(CHAPTER\s+[IVXLCDM\d]+)", re.IGNORECASE)


def pdf_to_synthetic_json(pdf_path: Path) -> dict:
    """Extract text from PDF via pdfminer.six, produce synthetic JSON."""
    kids: list[dict] = []
    elem_id = 0
    page_count = 0

    try:
        for page_num, page_layout in enumerate(extract_pages(str(pdf_path)), 1):
            page_count = page_num
            page_lines: list[str] = []

            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text()
                    for line in text.split("\n"):
                        line = line.strip()
                        if line:
                            page_lines.append(line)

            for line in page_lines:
                elem_id += 1
                if CHAPTER_RE.match(line):
                    etype, hlevel = "heading", 1
                elif SECTION_RE.match(line):
                    etype, hlevel = "heading", 2
                else:
                    etype, hlevel = "paragraph", None

                elem: dict = {
                    "type": etype,
                    "id": elem_id,
                    "page number": page_num,
                    "bounding box": None,
                    "content": line,
                }
                if hlevel is not None:
                    elem["heading level"] = hlevel
                kids.append(elem)

    except Exception as exc:
        print(f"    pdfminer error on {pdf_path.name}: {exc}", file=sys.stderr)

    return {
        "file name":      pdf_path.name,
        "number of pages": page_count,
        "author":         None,
        "title":          None,
        "kids":           kids,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for fname in TARGETS:
        pdf_path = SOURCE_DIR / fname
        if not pdf_path.exists():
            print(f"  SKIP: {fname} not found")
            continue

        stem     = pdf_path.stem
        json_out = OUTPUT_DIR / f"{stem}.json"
        md_out   = OUTPUT_DIR / f"{stem}.md"

        print(f"  Processing {fname} via pdfminer.six fallback ...")
        doc = pdf_to_synthetic_json(pdf_path)

        # Write JSON
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)

        # Write Markdown (simple)
        md_lines = [f"# {doc['file name']}\n"]
        for elem in doc["kids"]:
            content = elem.get("content", "")
            if elem["type"] == "heading":
                lvl = "#" * elem.get("heading level", 2)
                md_lines.append(f"{lvl} {content}\n")
            else:
                md_lines.append(f"{content}\n")
        md_out.write_text("\n".join(md_lines), encoding="utf-8")

        headings = [k for k in doc["kids"] if k["type"] == "heading"]
        sections = [k for k in headings if k.get("heading level", 0) == 2]
        print(f"    -> {doc['number of pages']} pages, {len(doc['kids'])} elements")
        print(f"       Section headings: {len(sections)}")
        print(f"       JSON: {json_out} ({json_out.stat().st_size // 1024} KB)")

        # Sample a few section headings
        for h in sections[:5]:
            print(f"         {h['content'][:80]}")

    print("\nFallback conversion done. Run: python -m ingest.chunk_sections")


if __name__ == "__main__":
    main()
