"""
ingest/convert_pdfs.py
======================
Step 2: Convert every PDF in the nyaya_tarazu_laws/ source folder into
Markdown + JSON using opendataloader-pdf.

Note: IPC_1860.pdf is skipped — it fails the PDF header check (not a valid PDF).
IPC content is covered by BNS_with_IPC_mapping_NCRB.pdf (NCRB Sankalan).

Usage:
    python -m ingest.convert_pdfs

Output:
    ingest/output/<stem>.md   — Markdown for human inspection
    ingest/output/<stem>.json — Structured JSON with bounding boxes, heading
                                levels, and page numbers (used by chunk_sections.py)

Notes:
    • All files are batched into a SINGLE convert() call to avoid spawning
      multiple JVM processes (each call has ~2 s JVM startup overhead).
    • Source PDFs are treated as READ-ONLY; nothing in nyaya_tarazu_laws/ is
      modified.
"""

import os
import sys
import time
from pathlib import Path

import opendataloader_pdf

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
SOURCE_DIR = ROOT / "nyaya_tarazu_laws"
OUTPUT_DIR = ROOT / "ingest" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Collect source PDFs
# ---------------------------------------------------------------------------
# IPC_1860.pdf fails the PDF header check (not a standard PDF file).
# IPC text is fully covered by BNS_with_IPC_mapping_NCRB.pdf (NCRB Sankalan).
SKIP_FILES = {"IPC_1860.pdf"}

pdf_paths = sorted(p for p in SOURCE_DIR.glob("*.pdf") if p.name not in SKIP_FILES)
if not pdf_paths:
    print(f"ERROR: No PDFs found in {SOURCE_DIR}", file=sys.stderr)
    sys.exit(1)

print(f"Found {len(pdf_paths)} PDFs to convert:")
for p in pdf_paths:
    size_kb = p.stat().st_size / 1024
    print(f"  {p.name:50s}  {size_kb:8.1f} KB")

print(f"\nOutput directory: {OUTPUT_DIR}")
print("Starting conversion (single JVM batch) …\n")

# ---------------------------------------------------------------------------
# Batch-convert all PDFs in one call
# ---------------------------------------------------------------------------
t0 = time.perf_counter()

opendataloader_pdf.convert(
    input_path=[str(p) for p in pdf_paths],
    output_dir=str(OUTPUT_DIR),
    format="json,markdown",
    # keep_line_breaks helps preserve section number formatting
    keep_line_breaks=True,
    # threads for parallel page parsing within the JVM
    threads="4",
)

elapsed = time.perf_counter() - t0
print(f"\nConversion finished in {elapsed:.1f}s")

# ---------------------------------------------------------------------------
# Verify outputs
# ---------------------------------------------------------------------------
print("\n=== Output verification ===")
failures: list[str] = []

for pdf in pdf_paths:
    stem = pdf.stem
    md_file = OUTPUT_DIR / f"{stem}.md"
    json_file = OUTPUT_DIR / f"{stem}.json"

    md_ok = md_file.exists() and md_file.stat().st_size > 100
    json_ok = json_file.exists() and json_file.stat().st_size > 100

    status = "✅" if (md_ok and json_ok) else "⚠️ "
    md_sz = f"{md_file.stat().st_size / 1024:.1f} KB" if md_file.exists() else "MISSING"
    json_sz = f"{json_file.stat().st_size / 1024:.1f} KB" if json_file.exists() else "MISSING"

    print(f"  {status} {pdf.name}")
    print(f"       .md   → {md_sz}")
    print(f"       .json → {json_sz}")

    if not md_ok or not json_ok:
        failures.append(pdf.name)

print()
if failures:
    print(f"⚠️  {len(failures)} PDF(s) may need manual review (scanned/image-only?):")
    for f in failures:
        print(f"   • {f}")
    print("   The chunker will fall back to sliding-window mode for these.")
else:
    print("All PDFs converted successfully.")

print("\nDone. Next step: python -m ingest.chunk_sections")
