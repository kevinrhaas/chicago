---
id: T-0069
title: Fences line the streets, and plank sidewalks run beside them
state: done
epic: TOWN
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-21
pr: 293
claimed_by: run 8/21/2026, 7:24:08 AM CT
blocked_on: null
needs_bake: false
---

Fences line the streets, and plank sidewalks run beside them.

**The owner, 2026-08-18, of the first Cook County jail engraving, verbatim: "note the
fences lining the street and what appears to be plank sidewalks. all of the streets
should be updated like this... at least south of the river or near the river."**

Four images in the brief agree (`data/sources/assets/owner_brief_2026_08_18/README.md`):
the jail engraving (image 1 — board fences at the frontage line, plank walk at their
foot), both Sauganash views (images 8, 9 — **plank sidewalks on both frontages with board
crossings over the road**, posts at the corner), and the Green Tree engraving (image 6 —
plank walks and crossings).

Build the streetscape edge as a generated layer from the street network, so one change
covers the scope: along the core streets **south of the river and near it**, run plank
sidewalks at the lot line, board crossings at the corners, and street-lining fences where
lots are improved but not built to the line. Hitching posts at the commercial fronts
(the Sauganash's posts) can ride along. Reconstructed tier, one LIBERTIES entry; the
walkable surface must actually be walkable (the walker steps up onto the planks —
coordinate with the T-0045 deck-walking machinery, done).

**Acceptance:** walking one core street south of the river end to end, plank sidewalks
run at the fence line with board crossings at the corners, and the treatment demonstrably
comes from the street network (not hand-placed on one block); carded reconstructed.
Gates green.

**Links:** owner_brief_2026_08_18 README (images 1, 6, 8, 9) · T-0068 · T-0070 ·
T-0045 (done) · docs/LIBERTIES.md.

---

## Done 2026-08-21 on the two river streets; the rest is T-0127

The street edge is built as a GENERATED layer from the street network —
`data/frontage/town_street_edge.json`, written by `tools/generate_frontage_works.py` from
the committed plat grid (whose every block face IS a committed street centreline offset by
half the committed 80 ft corridor) and re-derived byte for byte by `tools/check.sh`.

**Laid: SOUTH WATER STREET and LAKE STREET (both frontages), Market Street to State
Street** — 1,147.7 m of plank sidewalk in 21 runs at the lot line, 9 board crossings
(212.5 m: at the corners over the cross streets, and over Lake Street itself between facing
walks), 12 street-lining board fences (504.9 m) on the frontage line with the walk at their
foot, and 86 walking decks registered with the walker so a visitor steps UP onto the boards
and stays on them. Reconstructed on every vertex; docs/LIBERTIES.md **L160**.

**Where it breaks, and both breaks are written into the record's `refused`.** The La Salle
and State Street sloughs cross these frontages and no crossing is committed over either, so
the walk stops at the water. And the South Water frontages come out in pieces because ten
documented buildings on that side were placed against the modern kerb rather than against
this project's platted line and stand up to 6.9 m out past it — the march names the
building in each refusal. Reconciling those placements, plus Randolph, Washington, the
cross streets' own frontages, the West Division across the South Branch and the hitching
posts at the commercial fronts, is **T-0127**.

**Cost at the release gate's own stand (`frame('sauganash_hotel', 26)`), desktop,
published mirror:** full 794,916 → 855,832 of 1,000,000; balanced 718,994 → 752,164 of
800,000; light 557,311 → 576,335 of 600,000. Draw calls 65 → 78, against a ceiling raised
the same day from 80 to 120 on the owner's ruling (*"or just raise the budget?"*) and
argued at `renderers/web/js/main.js` BUDGET. Recorded in T-0115's ledger.
