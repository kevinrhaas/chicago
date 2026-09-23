---
id: T-0941
title: 33S7-9YYJ-L3's TOTAL column turns on a two-stroke glyph three readings name three ways: 4 on dev, 11 on #1015, unread on #1013
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: folded into T-0957: the same two-stroke glyph and the same footing dispute on 33S7-9YYJ-L3
needs_bake: false
closed_at: 2026-09-10T04:20:05.565Z
claimed_run: null
---

**Salvaged from PR #1013 by T-0927, 2026-09-07, before that PR was closed as superseded.**
It was filed there as T-0923; that number was taken on `dev` by another run while #1013
sat open, and the ticket file has never existed on `dev`. Refiled here with the finding
widened, because a second reading has since disagreed a second way.

Three passes have read line 1 of 33S7-9YYJ-L3's TOTAL column and no two of them agree:

| reading | line 1 | confidence | what it says the ink is |
|---|---|---|---|
| `dev`, from PR #1014 | **4** | medium | one 43x55 component plus a 7x15 mark below its right — a matched pair with the two strokes touching, closed with a morphological close |
| PR #1013 | **unread** | — | two parallel slants, the right raised 0.7 px and 27 px right of the left; one glyph by the separation test, and not named |
| PR #1015 (`hold`) | **11** | high | two separate parallel slants with clear paper between them — no crossbar and no loop, so 11 and not a two-stroke 4 |

The disagreement is not confined to line 1. The same glyph decides five more of the
column's six matched pairs on the `dev` reading, and it is what carries `dev`'s committed
sum of 71 over 21 lines against #1015's 111 over 19. The two readings also disagree on the
printed footing itself — 115 on `dev` and on #1013, 113 on #1015 — and on how many lines
the leaf rules with an entry: 27 against 28 over a 30-position grid.

**The measurement that would settle it is not on this leaf.** The leaf carries no
alphabet: there is no line where the same hand writes a figure this project has committed
from another source, so nothing calibrates the two-stroke form against a known 4 or a
known 11. What would settle it is a leaf of the SAME hand with committed line values —
find one, read its two-stroke glyphs against values already held, and bring the key back.

**Acceptance:**

1. A leaf of the same enumerator's hand is named, with committed line values from a source
   other than that leaf's own arithmetic, and the reasoning for calling it the same hand
   is written down.
2. The two-stroke form is read on that leaf against those values, and the key says which
   figure it is — or says plainly that the leaf does not settle it and why.
3. 33S7-9YYJ-L3's line 1 and the other five matched pairs carry the key's verdict, with
   their confidence set by the key rather than by the pass that first wrote them.
4. If the key says 11, the footing question (113 against 115) and the line count (27
   against 28) are re-put, because #1015's reading turns on the same stroke.
5. Nothing is adjusted to make the column close. It does not close on either reading and
   that stays stated.

**Links:** T-0744 · PR #1014 (landed) · PR #1013 (closed by T-0927) · PR #1015 (`hold`) ·
T-0942 · T-0943 · T-0930.
