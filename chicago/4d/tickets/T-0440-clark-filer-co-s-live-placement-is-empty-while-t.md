---
id: T-0440
title: Clark, Filer & Co.'s live placement is empty while three printings put its warehouse five doors east of Randolph
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-30
closed: 2026-09-04
pr: 824
claimed_by: run 9/4/2026, 5:43:52 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T23:42:45.824Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33926203781
---

Clark, Filer & Co.'s live placement is empty while three printings put its warehouse five
doors east of Randolph.

Found by T-0384's corpus sweep (`tools/measure_corner_ordinals.py`, which reports it every
time it runs). The gazetteer holds three placement readings for `business_clark_filer_co`,
and the middle one — printed 1834-06-11, 1834-06-18 and 1834-07-02 — reads

> "their ware house on South water St. five [doors east] of the corner [of Randolph st.]"

with `class: relative`, an anchor of *the corner of Randolph st.* and `street: South Water
Street`. That is an ordinal off a corner in the exact shape `docs/CORNER-ORDINAL.md` was
written for, and under the owner's ruling of 2026-08-30 it places.

**It never reaches the register.** `business_clark_filer_co`'s LIVE placement is
`{"class": "none"}` with `street: null`, so `compile_register.resolve_anchor` is handed no
anchor at all and the row reads `action: unplaceable`, *"The paper gives no anchor."* The
house is present at the scene date and is not excluded — it is unplaceable only because the
live placement is empty while three of its own printings are not.

So the fault is in how the gazetteer chooses a business's live placement, not in the
register's reading and not in this corpus. `tools/compile_gazetteer.py` ranks placement
classes `none < street_only < relative < corner` and a `relative` reading should beat a
`none` one; something else is choosing here, and whatever it is may be choosing for other
houses too — the first thing this ticket owes is a count of how many.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Why the live placement is `none` when a `relative` reading exists is stated, with the
  code path named, and the count of OTHER businesses in the same position is measured
  rather than assumed.
- Either the live placement resolves to the printings' own anchor and Clark, Filer & Co.
  stops reading `unplaceable`, or the reason it may not is written down and the ticket is
  blocked on it — never a silent narrowing.
- Whatever changes, `tools/measure_corner_ordinals.py`'s sweep and the register both
  re-derive green, and the gazetteer's own self-test carries the case.

**Related:** T-0384 (the ruling and the sweep that found this) · `docs/CORNER-ORDINAL.md` ·
T-0306 (the storefronts programme).

---

## What was found, 2026-09-04

**The code path.** `tools/compile_gazetteer.py`, the business mint (`businesses.setdefault`
inside the claim loop). A house's dict takes `placement` and `street` from WHICHEVER CLAIM
MINTS THE KEY — the earliest printing the corpus carries, in filename order — and nothing
downstream ever revised the live one. `record_reading` keeps every later printing as a
dated READING (T-0345) and a firm MERGE may raise the live placement
(`placement_rank(src) > placement_rank(dst)`), but within a single key the first printing
won outright.

So `placement_rank` was never consulted for this house at all. The ticket supposed
something was choosing badly; nothing was choosing. Clark, Filer & Co. announced itself on
1834-05-28 with a furniture list and no address, and the three printings that carry
*"their ware house on South water St. five [doors east] of the corner [of Randolph st.]"*
arrived a fortnight later, by which time the house was already `{"class": "none"}` for
good.

**A second, structural half.** `identity.json`'s `anchor_changes` is the ONE mechanism that
may order a house's anchors, and it could not be written for this house either: guard 3
refuses an anchor name no printing carries, guard 4 refuses a reading no group claims, and
a silent printing's anchor is `null` — nameable by neither. Every house whose advertisement
ever ran without an address was therefore outside the only mechanism that could have
repaired it.

**The count, measured.** `tools/measure_placement_silence.py`, committed with this work and
run by `tools/check.sh`. Of 206 houses, **19** held a live placement outranked by one of
their own readings, in two populations that are not the same problem:

- **14 placed by nothing while a printing placed them.** Silence, not disagreement. 13 are
  repaired here; the 14th (`business_jones_king_co`) is placed only by a printing of
  1835-08-05 and stays silent, which is the scene-date bound working.
- **7 holding a printed address that a later printed address outranks.** That is a house
  that may have MOVED, and choosing between two printed addresses is `anchor_changes`'
  judgement to make. Left alone, listed, and filed as **T-0702**.

## What changed

`compile_gazetteer.py` gains one pass, run before the `anchor_changes` rules so an authored
rule still overrides it: where a house's live placement places NOTHING, it takes the
earliest placing reading first printed on or before the scene date, and the reading's own
`street` where the mint had none. A `placement_from` block records which printing it came
from. A printed address is never overridden by another printed address; the pass fires only
on silence. Three self-test cases carry it, and each was confirmed to fail with the repair
removed.

Clark, Filer & Co. reads `street_only` on South Water Street instead of `unplaceable`, and
takes a street face. Register actions: `unplaceable` 93 → 90, `street_only` 58 → 60,
`new_building` 25 → 26. Street-face adoptions 35 → 37.

**What it did NOT reach, and it is worth saying plainly:** the ordinal itself. *"Five doors
east of the corner of Randolph st."* is still not spent as a corner ordinal, because the
anchor names one street of the crossing and the placement's `street` names the other, and
nothing joins them. That is **T-0703**.
