---
id: T-0536
title: The census_1840 domain declares its 25 read images in its own images[] shape, which the shared research-domain gate does not read
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-05
pr: 858
claimed_by: run 9/5/2026, 2:00:18 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T19:16:11.828Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33985345042
---

The census_1840 domain declares its 25 read images in its own images[] shape, which the shared research-domain gate does not read.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**The finding, measured on 2026-09-03 while landing T-0492.** T-0492 fixed one shape for
six research domains: `coverage.json` carries `declarations[]`, each with a `unit` from the
closed `COVERAGE_UNITS` vocabulary, a `ticket`, and `items[]`; `tools/research_domains.py
--check` builds the declared set from those and fails a **hole** — a declared item nothing
in `records/` or `claims/` reaches.

`data/research/census_1840/coverage.json` predates that shape. It was written by T-0495's
read and is a genuinely richer document — 25 page images, each with its FamilySearch id,
sheet side, printed page, line count, `read_state` and `page_file` — but it carries them
under `images[]`, not `declarations[]`. So the shared gate reads **zero** declarations from
the domain that has actually been read the most, and reports:

```
6 domain(s); 0 record(s), 0 claim(s), 0 declared coverage item(s)
```

This is not a fault under the ratified contract — *"an undeclared item is not read yet and
is not a fault"* — and T-0492 deliberately did not rewrite another ticket's file to make its
own gate look busier. But it means the census_1840 read is outside the hole gate, and every
1840 sweep ticket (T-0494, T-0496, T-0525–T-0530) is about to add more of the same shape.

**The ask.**

1. Decide, and write down, which shape wins. Either `research_domains.py` learns to read an
   `images[]` declaration as a `declarations[{unit: "image", …}]` one, or `census_1840`'s
   coverage is migrated to `declarations[]` **without losing a field** — the per-image
   `read_state`, `page_file` and `lines_with_an_entry` are the evidence that a hole is a
   hole, and none of them may be dropped to fit.
2. Whichever way it goes, the `pages/*.json` files must **reach** their declared images, so
   a declared-but-unread image fails. Today `pages/33S7-9YYJ-NY.json` and
   `pages/33S7-9YYJ-W6.json` are read and the other 23 are `inventoried_only`; an
   inventoried image is *declared as inventoried*, not declared as read, and the gate has
   to be able to tell those apart or the hole assertion means nothing.
3. `--self-test` gains the case: a census_1840 image declared read that no `pages/` file
   reaches.
4. Say in `data/research/census_1840/README.md` which shape it is in and why.

**Do not** take this while a 1840-census sweep ticket is open — it edits the file they are
all appending to. It is cheapest immediately after T-0530 closes.

**Links:** T-0492 (the shape) · T-0495 (the images[] coverage) · T-0494, T-0496,
T-0525–T-0530 (the sweeps that extend it) · T-0513 (the consolidation that reads it).
