---
id: T-1107
title: The two fort crops in the 2026-08-11 set are almost certainly Kurz & Allison panels 1 and 5: measure the join and fill fort_dearborn_apron's empty sources
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-13
pr: 1265
claimed_by: run 9/13/2026, 1:18:20 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T19:01:12.866Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34774017544
---

T-0055 identified the Kinzie crop (`p6_1.png`, numeral "12.") as **panel 12 of
`kurz_allison_1893`** — Kurz & Allison, *Chicago In Early Days, 1779-1857* (1893) — and proved
it three ways: the printed numeral, the sheet's own key line, and a normalised
cross-correlation of the crop against the committed sheet
(`chicago/reference/photos/IMG_5382.png`), 0.797 on that vignette against 0.341 anywhere in a
control panel. It filled `data/enclosures/town_dooryard_pickets.json`'s empty
`existence.sources` with the source id, and its README table records the method.

**The same debt is still open one directory over, for the fort.**
`data/enclosures/fort_dearborn_apron.json` carries a `sources_note` reading *"EMPTY, AND THAT
IS THE FINDING, exactly as data/enclosures/town_dooryard_pickets.json says of the Kinzie
view"* — and cites `p4_0.png` and `p4_1.png` by committed path. The 2026-08-11 README calls
`p4_0` plate "1" and `p3_1` plate "5"; the Kurz & Allison key reads *"No. 1.  Old Fort
Dearborn.  Erected 1803."* and *"No. 5.  Fort Dearborn, as re[built] … 1835.  Population
3,265."*, and `kurz_allison_1893`'s own locator already names panel 5. So the join is strongly
implied and **was not measured**, which is why T-0055's README table marks those two rows
*unconfirmed* rather than filling them in.

Note the fort plates are read far harder than the Kinzie one: `tools/measure_fort_works_plate.py`,
`measure_fort_trees_plate.py`, `measure_picket_plate.py` and `data/flora/plantings/fort_dearborn_wood.json`
all take measurements off `p4_0`/`p4_1`. If those crops are panels of a sheet held at
`public_domain`, the rights position of everything derived from them improves — and if they are
NOT, that is a finding worth having before more is derived.

**Acceptance:** each of `p4_0.png`, `p4_1.png` and `p3_1.png` either resolves to a named
`kurz_allison_1893` panel — proved the way T-0055 proved panel 12, with the correlation figure
and the control recorded — or its README row states what was measured and why it failed. Where
a join lands, `data/enclosures/fort_dearborn_apron.json`'s `sources` is filled (through its
generator if it has one, never by hand-editing a derived file) and its `sources_note` stops
pointing at a finding that no longer stands. `p4_1` is a wider view than `p4_0` and may be a
different sheet entirely — do not assume the batch is homogeneous. Gates green.

**Links:** T-0055 (the pattern and the method) · `data/sources/kurz_allison_1893.json` ·
`data/sources/assets/prefire_views_kevin_2026_08/README.md` § Identifications ·
`data/enclosures/fort_dearborn_apron.json`
