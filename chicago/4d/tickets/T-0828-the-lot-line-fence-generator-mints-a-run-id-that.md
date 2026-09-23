---
id: T-0828
title: The lot-line fence generator mints a run id that names a lot, not a side, so two sides of one lot share an id
state: done
epic: TOWN
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-06
pr: 989
claimed_by: run 9/6/2026, 10:08:07 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T15:35:45.654Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34041163701
---

The lot-line fence generator mints a run id that names a lot, not a side, so two sides of one lot share an id.

## What was found, and how

T-0820 asserts that no committed list carries the same `id` twice. Surveying the
tree for the shape that rule applies to — a dict value that is a list of two or
more objects, every one carrying an `id` — turned up **67 kinds of keyed list,
and 66 of them were already clean.** The single exception is `runs[]` in the
three lot-line fence files:

| file | runs | ids carried twice |
|---|---|---|
| `data/enclosures/town_lot_line_pickets.json` | 59 | 4 |
| `data/enclosures/town_lot_line_rails.json` | 147 | 8 |
| `data/enclosures/town_lot_line_boards.json` | 83 | 5 |

**This is not a duplicate. Both entries are real fence.** Two runs sharing
`side_blk_lake_dearborn_lot1` in the rails file carry different geometry —

```
path_local_enu_m  [[709.82, -201.81], [709.90, -189.59]]
path_local_enu_m  [[735.73, -201.97], [735.81, -189.81]]
```

— about 26 m apart in easting, which is one lot's width. They are the east and
the west side line of the same lot. The generator mints `side_<lot>`, and a lot
has two sides, so the name **under-specifies**: it identifies the lot the run
belongs to and then stops. Every colliding pair inspected has this shape.

## Why it matters even though the geometry is right

An id that names two different things is not an id. Anything downstream that
indexes these runs by id — a scene compile keying a mesh, an audit joining a run
to its lot, a diff asking "did this run move" — silently keeps whichever entry it
read last and loses the other side of the lot. Nothing observed has done that
yet, which is exactly why this is S and not a fire.

It is also the one place `tools/check_unique_ids.py` has to look away. That
check is otherwise a rule with no exceptions, and a rule with no exceptions is
the kind that stays true; the file names these three entries and points at this
ticket precisely so the gap does not become permanent by going unrecorded.

## Acceptance

- The generator mints a run id that names the SIDE, not just the lot — the two
  runs above end up with distinct ids, and the id says which side it is.
- The three files rebuild from the generator with no id carried twice.
- The `EXCEPTIONS` table in `tools/check_unique_ids.py` loses all three entries,
  in the same commit — the check then covers `runs[]` like every other list.
- Whatever else reads these runs still resolves them (rebuild the enclosures and
  run the gate; if a downstream file embeds the old ids, it re-derives too).
