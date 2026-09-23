---
id: T-0265
title: The sward census fails its own gate at a phone: z10_settled_town owes xanthium_strumarium a whole slot and draws it nowhere
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 523
claimed_by: run 8/29/2026, 4:05:27 AM CT
blocked_on: null
needs_bake: false
---

The sward census fails its own gate at a phone: z10_settled_town owes xanthium_strumarium a whole slot and draws it nowhere.

`SWARD_VIEWPORT=mobile node tools/measure_sward_draw.mjs --gate` is RED on an unmodified
`dev` and has been since the phone stand was first measurable: *1 of 96 (list, species)
pair(s) drawn NOWHERE in the whole scene — z10_settled_town.forb.xanthium_strumarium owed
1.49*. The desktop stand is green. Every branch cut from `dev` inherits the red one, which
is why this sits in the STANDING REDS band.

**Acceptance:** (stated before working — the definition of done, never weakened to pass)

- `SWARD_VIEWPORT=mobile node tools/measure_sward_draw.mjs --gate` reports **0** (list,
  species) pairs drawn nowhere, against the PUBLISHED mirror, and the desktop run stays at 0.
- The repair is a statement about the DEAL, not about this species: it says why a band of
  the CDF went unhit in a phone's window and what now hits it, and the reasoning is in
  `flora.js` beside the code rather than in this ticket.
- Whatever it costs on the census's other columns is measured and written down, both
  viewports, rather than left for the next reader to discover.
- The screenshot veto K49(b) records is honoured: the construction may not put a direction
  into the field that a visitor can read as rows.

## What was measured

The deal itself, at the settled-town station the census stands at, mobile stand:

- the forb ring reaches **12.4 m** at the `light` tune and the Cranley–Patterson rotation
  block is **54.4 m** square, so the whole frame lies inside ONE block and one rotation;
- the 46 slots that frame deals, sorted, leave a gap of **0.0399** between 0.8247 and
  0.8646 — nearly twice their mean spacing of 1/46;
- cocklebur's band is **0.0324** wide, seventh of seven in that list's CDF, and lies wholly
  inside that gap. It is not rare in the frame; it is absent from it.

The rank-1 lattice's claim in `flora.js` — *"It is equidistributed over any window"* — is
therefore false of a phone's window, and that sentence is now struck in the file.

## What was refuted, so nobody spends a run on it again

| repair | mobile gate | forb deviation /100 |
|---|---|---|
| unmodified `dev` | RED (cocklebur) | 16.23 |
| the sub-cell term made exact, `k/perCell` for `k·γ` | RED (two mesic-prairie forbs) | 19.53 |
| the forb and shrub passes moved onto `stratum` (K49(d)) | RED | 28.70 |
| the rotation block cut to four cells, phases swept | RED (a wet-prairie forb) | 18.80 |
| **the cell-resolution sweep that shipped** | **GREEN** | 17.46 |

**Links:** K49(b) (the lattice), K49(c2) (`blockPhase`, whose argument this reuses one scale
down) · T-0371 (the block rotation the sparse draw no longer reads) ·
`tools/measure_sward_draw.mjs` (the gate)
