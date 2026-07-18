import json, re

SECTION_RE = re.compile(r'(?:Section\s+|Sec\.\s*|S\.\s*)?(\d+[A-Z]?)\s*[.:\-\u2014]', re.IGNORECASE)

for fname in ['BNS_with_IPC_mapping_NCRB.json', 'CrPC_1973.json', 'Evidence_Act_1872.json']:
    with open(f'ingest/output/{fname}', encoding='utf-8') as f:
        doc = json.load(f)
    kids = doc['kids']
    heading_elems = [e for e in kids if e.get('type') == 'heading']
    mode_a_count = sum(1 for h in heading_elems[:20] if SECTION_RE.search(h.get('content','')))
    mode = 'A' if mode_a_count >= 2 else 'B'
    print(f'{fname}: {len(heading_elems)} total headings, mode_a_count={mode_a_count} -> mode={mode}')
    
    # For BNS: count H2 headings
    h2 = [h for h in heading_elems if h.get('heading level', 99) <= 2]
    print(f'  H2 headings: {len(h2)}')
    for h in h2[:5]:
        print(f'    {repr(h.get("content","")[:70])}')
    print()
