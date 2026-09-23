---
id: T-0228
title: Two wharf decks oversail the riverside plank walk, and the walk now meets a half-metre riser at their edge
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 451
claimed_by: run 8/28/2026, 4:19:38 AM CT
blocked_on: null
needs_bake: false
---

Two wharf decks oversail the riverside plank walk, and the walk now meets a half-metre riser at their edge.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-0058, which made the wharf decks walk surfaces and so made this visible.

**Measured, in the loaded page.** `carpenter_south_water_store` and `h_jones_store` tie their
deck heels 2.0 m back into the south bank at E 392 and E 353 — ground the riverside plank walk
(`river_walk_frontage` / the town street edge) already runs along. About **2,700 frontage
vertices lie inside those two deck outlines** and a further **270 inside their boarding stairs**;
the walk's boards sit at 0.35-0.40 m on ground at 0.22 m, and the deck top is 0.90 m, so the
dock oversails the sidewalk by roughly **half a metre** with about 0.36 m of clearance under the
slab — less than a visitor is tall.

None of that geometry moved in T-0058. What moved is what the WALKER does with it: the deck is
now a registered floor, so a visitor on the walk meets a 0.50 m riser at the deck's edge against
the 0.35 m step-up rule and is refused, except across the 2.4 m of boarding stair, which at these
two docks rises off the plank walk rather than off bare ground. Stepping back DOWN is free, so
the deck can be left anywhere along its edge and re-entered only at the stair.

Physically truthful and possibly right. But nobody chose it, and there are three answers worth
weighing rather than one: cut the walk where a dock crosses it (a walk does not run under a
dock); cut the dock's heel back to the walk's landward edge (the 2.0 m tie-in is invented, L132);
or leave it and say so. `tools/smoke_renderer.mjs` excludes wharf decks from the frontage layer's
tie-into-the-ground probe for exactly this reason (T-0058), which is correct for that check and
is not an answer to this.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
