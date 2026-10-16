import json, pathlib, re, sys
ev = json.loads(pathlib.Path('docs/RESEARCH/ktx2-v4/glessner-v4-ktx2.json').read_text())
p = pathlib.Path('docs/SITE-BUDGET.md')
doc = p.read_text(encoding='utf-8')
if 'has now handed it back' in doc:
    print('SITE-BUDGET.md already carries the measured sentence')
    sys.exit(0)
full = ev['files']['assets/web/glessner_house__as_built_1887.glb']
light = ev['files']['assets/web/glessner_house__as_built_1887.light.glb']
psnrs = [r['psnr_db'] for r in ev['renders'].values() if r['psnr_db'] is not None]
psnr_txt = ('identical renders' if not psnrs else
            f"{min(psnrs):.2f}–{max(psnrs):.2f} dB PSNR")
new = (f"T-2596 (the Glessner v4 set in KTX2) has now handed it back, measured on the "
       f"ticket's own runner run: the full derivative is "
       f"{full['old']['bytes']:,} → {full['new']['bytes']:,} B and the light "
       f"{light['old']['bytes']:,} → {light['new']['bytes']:,} B with its "
       f"{ev['textures']['light']['images']} textures capped at 1024; the three-file "
       f"recovery package is {ev['package']['old']['bytes']:,} → {ev['package']['new']['bytes']:,} "
       f"B, so the headroom above is now conservative. Rendered from the five reference "
       f"cameras, old files against new, the re-encode reads {psnr_txt} "
       f"(docs/RESEARCH/ktx2-v4/glessner-v4-ktx2.json).")
pat = re.compile(r"T-2596 \(the Glessner v4 set in KTX2\) is expected to\s+hand some of "
                 r"this back, since its 28 PNG maps are larger than their UASTC equivalents\s+—\s+"
                 r"expected, not measured\.")
doc, n = pat.subn(new, doc)
if n != 1:
    sys.exit(f'SITE-BUDGET.md: the T-2596 sentence matched {n} times (need exactly 1)')
p.write_text(doc, encoding='utf-8')
print('SITE-BUDGET.md §9 now carries the measured numbers')
