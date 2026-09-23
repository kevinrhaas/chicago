---
id: T-0245
title: South Water Street can have its first control point, at Franklin, and nothing has claimed it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-27
pr: 429
claimed_by: run 8/27/2026, 9:15:24 PM CT
blocked_on: null
needs_bake: false
---

South Water Street can have its first control point, at Franklin, and nothing has claimed it.

Found by **T-0183**, which went looking for a control point at Market × South Water, could not
derive one (a bend, not a crossing — see that ticket and `refused_control` in
`data/traces/street_control.json`), and read this one on the way past.

## What is there

`data/traces/street_control.json` holds four control points — `lake_canal`, `lake_market`,
`randolph_canal`, `kinzie_canal` — and **none of them is anywhere on South Water Street**, the
town's principal riverfront street. Under the file's own `node_rule`, one is available:

| | |
|---|---|
| named surface roadways | `West Upper Wacker Drive` × `North Franklin Street` |
| shared nodes | `28358941` (E 447281.12, N 4637399.57), `28358883` (E 447281.20, N 4637414.85) |
| mean | E 447281.16, N 4637407.21 — local **(208.46, +11.41)** |
| spread | 15.28 m — an ordinary two-carriageway crossing, the same shape as `lake_market` |

Read 2026-08-27 off a 260 m map extract from the OpenStreetMap API. No bikeway or footway is in
the set; both ways are surface roadways under the rule's own list.

**And it is a corner this project already has a document about.** The first post office stood at
the southwest corner of Franklin and South Water from 2 Nov 1832 to 3 Mar 1837
(`docs/research/03-structures-north.md`), which puts it there on the scene date.

## Why it was not adopted on the spot

Committing a control point is not a bookkeeping edit here. `tools/validate.py`
(`check_position_derivations`) recomputes every placement from the control it names, so adding
one invites — and may require — re-deriving the placements along South Water that currently
stand on something else, and `data/streets/1835.json` records that stretch as following the
modern Wacker control *"shifted into the dry half of the platted riverfront corridor"*, which is
a relationship this point would let somebody check for the first time. That is a unit of work
with a measurement in it, not a footnote on somebody else's refusal.

It also does **not** unlock `blk_south_water_market`: that block's gap is at its WEST corner, and
South Water already reaches Franklin.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`south_water_franklin` is committed in `data/traces/street_control.json` with its two node ids,
its `osm_ways` and its lat/lon, `tools/refetch_control.py --discover south_water_franklin`
reproduces it and the default verify pass reports it inside tolerance, and **the dataset says what
changed because of it**: either South Water's committed centreline east of Franklin is re-derived
against it and the drift is reported, or it is stated — with the number — that the line already
agrees and nothing moved. `tools/check.sh` green either way.

**Links:** T-0183 (the refusal that found it, and the bend at Market) · `node_rule` and
`refused_control` in `data/traces/street_control.json` · `docs/RESEARCH/thompson_plat_grid.md` § 6.1.
