---
id: T-1080
title: The Michigan St tract's name and the curved road north through it: who platted it, what the sources call it, and the road traced off Wright's sheet
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-1075
opened: 2026-09-12
closed: 2026-09-13
pr: 1202
claimed_by: run 9/13/2026, 8:30:54 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T14:05:14.188Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34759781726
---

The Michigan St tract's name and the curved road north through it: who platted it, what the sources call it, and the road traced off Wright's sheet.

Piece 2 of 2 of **T-1075 — The Michigan St tract named and seated: who platted it and what the sources call it, and its street, alley, parcels and the curved road north into the town's data**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance**, stated before working and not weakened to pass:

1. The tract's name is settled from a source that gives a BOUNDARY, or the refusal is
   recorded as a refusal. `docs/RESEARCH/michigan_st_tract.md` already carries the one
   candidate the corpus raises — Wolcott's Addition, canal-commissioner land west of State
   Street, which is the right section and the right side of the river — and the arithmetic
   that refuses it: Wolcott's was eighty acres and this tract is 7.78, with nothing platted
   beside it on Wright's sheet to make up the rest. Start there, not from scratch.
2. The curved road that leaves the Kinzie/North Water corner and runs north through the
   tract is traced off the sheet and committed as a TRACK of the same kind as `fort_road`,
   not as a platted corridor — or the trace is refused with the reason on the record.
3. Whatever is found is graded, and a name without a boundary grades no higher than
   conjectural.

---

## FOUND BY T-0795, 2026-09-13 — the road is the slough, and that is why the ribbon is wet *(acted on; see RESOLVED below)*

T-0795 walked the whole 600 dpi NA/HUP sheet for watercourses. It draws exactly one that is
not the river, and **it is this ticket's curved double line.**

**The project has held it as water since before this ticket existed.** `north_side_slough`,
in `data/terrain/epochs/e1834_harbor_cut/hydrology.geojson`, is a 45-vertex centreline
described as *"a narrow winding watercourse running north out of the main stem, across Kinzie
Street, ending at Michigan Street"* — the same two ends, the same reach, `wright_1834` cited
for **existence and course**. Re-measured against the NA sheet, 41 of its 45 stations find the
pair of strokes that bracket them and the centre of the pair departs from it by **1.78 m
median, 8.03 m at worst**. `michigan_st_tract_road` and `north_side_slough` are not neighbours.
They are one feature, read twice, four hundred commits apart.

**This dissolves the blocker exactly.** The WIP note above measures the road's ribbon standing
10–25 cm below the summer-1835 water surface and offers three ways out — move the terrain, move
the road, or break the ribbon. There is a fourth, and it is the one the evidence points at: the
ground under the road is wet **because the project already carves a watercourse along it**. The
swale is not modelled relief that happens to be in the way; it is this line, in the terrain.

**What the sheet says about which reading is right** — stated, not decided, because it is this
ticket's to decide:

1. **It is drawn as a confluence.** At NA px (2033, 2270) the west stroke *becomes* the river's
   north bank running south-west and the east stroke *becomes* the same bank running east: two
   banks continuous with the main stem's, on either side of an opening. A road drawn to a river
   either stops at the bank or crosses it. This does neither.
2. **Thompson's 1830 plat draws this feature as water**, across North Division block 6 — the
   same block the line crosses (T-0452, `docs/RESEARCH/thompson_plat_sloughs.md`). A second
   surveyor, four years earlier, on the same ground.
3. **The road argument cuts both ways.** "It curves, and it cuts diagonally across platted
   blocks and lot lines" is at least as true of a stream: a plat ruled over a watercourse is
   the ordinary case, a road ruled across finished blocks is not.
4. **The corridor widths agree, which is the tell.** This ticket measured 12.22 m between
   stroke centres; T-0795 measured 13.02 m on the same strokes by a different method. Same ink.

**What this ticket now owes**, and none of it is new reading: either withdraw
`michigan_st_tract_road` as a duplicate of `north_side_slough` and say so on L234, or show why
Wright drew a road down the middle of a watercourse he drew joining his own river. Whichever
way it goes, the two records must not both stand.

Audit: `docs/RESEARCH/wright_1834_watercourses.md`,
`data/traces/wright_1834_watercourse_audit.json`.

---

## RESOLVED, 2026-09-13 — the road is withdrawn, and the reading is kept as the slough's cross-check

T-0795 asked this ticket to decide, and it decides for the watercourse. **The road record
`michigan_st_tract_road` is withdrawn and nothing is seated into `data/streets/1835.json`.**
Both acceptance criteria are met as REFUSALS, which was always a permitted outcome:

1. **The name is refused**, twice over. Wolcott's Addition is out on the calendar — Moses &
   Kirkland line 13122 places it after the canal commissioners' June 1836 addition, two years
   past Wright's survey — and out on the arithmetic, eighty acres against this tract's 7.78.
   No source in the corpus gives this tract a boundary or a name.
2. **The road trace is refused**, because the thing it was read from is water.
3. **Nothing was graded up to make it pass.** The slough keeps T-0687's grades exactly:
   course `attested`, width `inferred`, depth `reconstructed`. A second reading corroborates;
   it does not promote. No liberty is taken, so no L234: withdrawing a record invents nothing.

**The measurement that settled it**, and it is re-derived by `--check` rather than transcribed:
this reading's 36 sheet stations fall a **median 1.54 m** from the committed `north_side_slough`
centreline, **17.91 m** at worst — against that record's own stated ±20 m vertex uncertainty and
this sheet's 16.19 m RMS. Two scans (NA/HUP 600 dpi against the BPL master), two registrations,
two tracers, four hundred commits apart. Beside it: T-0795's count of ONE non-river watercourse
on the whole sheet; the confluence at NA px (2033, 2270); Thompson's 1830 plat drawing the same
feature as water across the same block; and stroke separations agreeing to 0.2 m (12.35 m here,
13.02 m there).

**The blocker is dissolved rather than worked around.** The wedge check was reporting the truth:
the ribbon's west edge sampled 10–25 cm below the summer-1835 water surface *because this project
already carves a watercourse along that line*. None of the three ways out in the WIP note was
needed. The terrain does not move, the line does not move, and nothing is rebaked.

**What shipped**

- `tools/read_north_side_slough_na.py` and `data/traces/north_side_slough_na_reread.json`
  (renamed from `read_michigan_st_tract_road.py` / `michigan_st_tract_road.json`) — the reading,
  under the feature's own name, carrying a re-derived `identity` block. It is now the only
  independent cross-check `north_side_slough` has.
- `tools/check.sh` gates its `--check`.
- The open question on the terrain record and its Evidence card is closed in the record's own
  words (`terrain_spec.json`, recompiled into `data/sidecars/1835/terrain.json`); the same in
  `tools/audit_wright_watercourses.py`'s narrative and in
  `docs/RESEARCH/wright_1834_watercourses.md`.
- `docs/RESEARCH/michigan_st_tract.md` carries the adjudication and both refusals.

**Verification.** `tools/check.sh` green — 375 steps, none red. Smoke `--for-diff` named parts
2-3,7-8,10-12; parts 2,7-8,10-11 are attributed only by the `data/traces/` glob and this trace
builds nothing, so the four legs that genuinely cover the diff were run and all passed: desktop
and mobile part 3 (the record's account on the card, and the heightfield) and part 12 (the
release notes). Readings filed with `dev-smoke-state.mjs record`.
