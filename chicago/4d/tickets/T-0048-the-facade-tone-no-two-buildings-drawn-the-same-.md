---
id: T-0048
title: The facade tone: no two buildings drawn the same colour
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: K4
parent: T-0002
opened: 2026-08-17
closed: 2026-08-17
pr: 233
claimed_by: null
blocked_on: null
needs_bake: false
---

Piece 1 of 2 of **T-0002 — Weathered facades: unpainted boards, no two buildings alike**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** no two neighbouring buildings are drawn the same colour, measured off the batch
the renderer draws rather than off the rule that wrote it, and **no documented-paint record
changes by a bit**. Half of the parent's clause — *"the lake_market and south_water critic frames
show visibly distinct neighbouring facades"* — is quoted with its caveat below rather than
claimed: `lake_market` stands in front of the Sauganash, which is one of the two records this
rule may not touch.

---

**DONE 2026-08-17, PR #233 — 10 of 321 adjacent pairs were drawn identically to the bit, and now
none are.** `renderers/web/js/facades.js` gives every structure a tone: silvering that grows with
the record's own age (at most 0.35 toward the surface's own luminance and 0.10 of darkening at 12
years; half-rate on whitewash, none on masonry) plus a ±16 % value / ±7 % warmth jitter dealt from
a hash of its id. It folds into the per-vertex colour the batch already carries (**R-W5a**), so
the untextured town is still **one batch** and the sun's reach is unchanged.

**It is reconstructed, and the dataset is the argument for it:** `paint` is `reconstructed` on 236
of 335 records, `inferred` on 15, **`attested` on exactly two** — the Sauganash's documented white
and St Mary's attested unpainted, both handed the identity tone and asserted bit-exact by the
smoke. Bounds and reasoning: `docs/LIBERTIES.md` **L126**. Measured by
`tools/measure_facade_variety.mjs` on the published mirror: 331 distinct tones across 331
structures, median neighbour difference **10.4 %** of applied value, winding the tone off moves
the worst 48² frame cell by **10** and restores to a residual of 0.

**Two findings worth carrying forward.** (1) The age input is a construction date for the
well-attested buildings and a SCENE-PROGRAMME date for the 262 anonymous infill records, so those
draw unsilvered — the absence of a claim, not a claim that they are new. (2) **The first
magnitude shipped was too small to SEE while every instrument read green**: at ±10 % the
before/after frames were hard to tell apart with 331 tones and no two neighbours alike. A gate
that counts distinct values cannot answer a clause written about what a visitor sees.
**T-0047** owns the measured tail — the deal is blind to position, so a tenth of neighbour pairs
still differ by only ~2.4 % of value.
