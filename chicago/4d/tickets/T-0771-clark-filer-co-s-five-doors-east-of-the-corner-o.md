---
id: T-0771
title: Clark, Filer & Co.'s 'five doors east of the corner of Randolph st.' names one street in the anchor and the other in the placement, so the corner-ordinal reader never sees a corner
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 966
claimed_by: run 9/6/2026, 12:01:32 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T05:47:58.073Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34012821945
---

Clark, Filer & Co.'s ordinal names one street in the anchor and the other in the
placement, so the corner-ordinal reader never sees a corner.

Found while landing T-0440, which gave this house a live placement for the first time.
Three printings — 1834-06-11, 1834-06-18, 1834-07-02 — read

> "their ware house on South water St. five [doors east] of the corner [of Randolph st.]"

and `tools/measure_corner_ordinals.py` has reported that phrase as *readable as an ordinal
off a corner* on every run for a week. It still is not read as one. The register now places
the house, but only as `street_only` on South Water Street, noting *"the anchor is a reach
of randolph and names nothing narrower."*

**The reason is where the two streets live.** `docs/CORNER-ORDINAL.md`'s reader wants a
`corner` anchor naming BOTH streets of the crossing. This reading carries `class: relative`
with `anchor: "the corner of Randolph st."` — one street — and the other street, South
Water, in the placement's own `street` field. Nothing joins them, so
`compile_register.resolve_anchor` sees a reach of Randolph and stops. John Holbrook's
*"one door from Dearborn street"* does resolve, because its claim carries the second street
where the reader looks for it.

**The question is whether an anchor naming one street may take the second from the
placement's `street`.** It reads like bookkeeping and it is not: a corner ordinal fixes a
POSITION along a face and gets the house off the whole street and onto five doors of it, so
getting the pairing wrong puts a documented warehouse on the wrong reach of South Water.
There may also be other claims in this shape — count them before ruling, the way T-0440
counted its own population before repairing it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The count of claims whose anchor names one street of a crossing while the placement's
  `street` names the other is measured, not assumed.
- Either the pairing is ruled legitimate and written into `docs/CORNER-ORDINAL.md` with its
  limit, and `tools/measure_corner_ordinals.py`'s sweep stops reporting a readable ordinal
  it cannot spend; or the reason it may not is written down and this closes as refuted.
- `lot_claim`'s limit is untouched either way: an ordinal is a position and never a lot.

**Links:** T-0440 (the placement this house finally has) · T-0384 (the ruling and the
sweep) · `docs/CORNER-ORDINAL.md` · `tools/measure_corner_ordinals.py` ·
`tools/compile_register.py` § resolve_anchor.
