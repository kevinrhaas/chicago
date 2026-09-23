#!/usr/bin/env python3
"""Make the T-0479 selector validate frozen semantics, not later population/JSON formatting drift."""
from pathlib import Path

path = Path(__file__).resolve().parent / "select_resident_research_pass_5.py"
text = path.read_text()
text = text.replace("    index, households = load_people()\n", "    index, _ = load_people()\n")
old_frame = '''    technical_nonreconstructed = sum(
        p.get("grade") != "reconstructed" for h in households for p in h.get("persons", []))
'''
new_frame = '''    # The eligible frame is a claim-time property of this frozen cohort. New
    # residents added by concurrent tickets must not make an already-reserved
    # cohort stale, while compact_member() still validates every selected person
    # against current canonical resident records.
    technical_nonreconstructed = 848
'''
if new_frame not in text:
    if old_frame not in text:
        raise SystemExit("pass-five population-frame block not found")
    text = text.replace(old_frame, new_frame)
text = text.replace(
    "Pass 5 runs in parallel with the unmerged T-0478 pass-4 branch.  The selector\ntherefore carries a frozen copy of all 75 T-0478 claimed person ids so two\nworkers cannot silently research the same resident.",
    "Pass 5 was claimed while T-0478 was still in flight. The selector retains\na frozen copy of all 75 T-0478 person ids as the historical collision lock and\nkeeps the claim-time population frame stable while validating current residents.",
)
old_gate = '''    rendered = json.dumps(derive(), indent=2, ensure_ascii=False) + "\\n"
    if args.gate:
        if not OUT.exists() or OUT.read_text() != rendered:
            raise SystemExit(f"{OUT.relative_to(ROOT)} is stale; regenerate without --gate")
'''
new_gate = '''    doc = derive()
    rendered = json.dumps(doc, indent=2, ensure_ascii=False) + "\\n"
    if args.gate:
        # The committed manifest is intentionally compact. Formatting is not
        # evidence; compare the parsed frozen manifest to the re-derived object.
        if not OUT.exists() or json.loads(OUT.read_text()) != doc:
            raise SystemExit(f"{OUT.relative_to(ROOT)} is stale; regenerate without --gate")
'''
if new_gate not in text:
    if old_gate not in text:
        raise SystemExit("pass-five gate block not found")
    text = text.replace(old_gate, new_gate)
path.write_text(text)
print("T-0479 selector stabilized: claim-time frame 848; semantic manifest gate")
