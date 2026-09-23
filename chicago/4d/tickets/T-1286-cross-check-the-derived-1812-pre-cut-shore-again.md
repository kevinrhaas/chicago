---
id: T-1286
title: Cross-check the derived 1812 pre-cut shore against the Harrison 1830 trace, and record what the two readings disagree about
state: open
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

**The owner ruled on 2026-09-17** that Wright 1834 is accurate enough to carry the pre-cut
shore, so T-1242's derivation (#1399, on `dev`) stands and PR #1398's competing trace off
Harrison 1830 is closed. This ticket keeps the one thing that PR established.

**Why Harrison could not carry the line, which is the part the closed PR had wrong.** It
called the plate "the one plan this project holds that draws the mouth before anybody cut
it", and the date is right — 24 February 1830, three years before the cut. Everything else
about it refuses the job, and this project's own source record already said so:

* it is **tier 2**, because what is readable is Andreas's 1884 re-engraving and not the 1830
  drawing, which "was not consulted";
* its own title admits **"additions and changes suggested by the Memory of Early Settlers"**,
  and `what_it_does_not_supply` names "a separation between the 1830 survey and the
  settler-memory additions the plate admits to";
* `what_it_does_not_supply` also names **"any dimension in feet — there is no scale bar"**;
* `what_it_supplies` is the FORT — plan arrangement, ranges, gates, the named ground — and
  **does not list the shoreline at all**.

A sheet with no scale, re-engraved fifty-four years later with memory mixed in, cannot be
the metric authority for a shoreline. `wright_1834` is tier 1, the MASTER GEOMETRY SOURCE, a
genuine survey at 1:7,200 published as a georeferenced GeoTIFF, and its `what_it_supplies`
names `shoreline` outright. No defect of it is recorded anywhere in this repo; the one
cataloguing error on file belongs to Hathaway.

**What the closed PR did establish, and it is worth keeping.** `tools/trace_shoreline_1830.py`
read the Harrison plate through the transform T-0883 stated and T-0882 checked, asserted the
stockade's ink still falls where that transform says (**8.0 px off its committed centre,
12 px tolerance**), and produced `south_shore_pre_cut` at 688.8 m / 72 vertices and
`north_shore_pre_cut` at 999.1 m / 130 vertices. That is an INDEPENDENT reading of the same
landform, from a pre-cut sheet, by a different method. Nobody has measured it against the
line now on `dev`.

    git fetch origin steward/t-0468-1812-shoreline
    git show 4e90935dc -- chicago/4d/tools/trace_shoreline_1830.py

**Acceptance:** measure the distance between the committed `shore_1812_pre_cut` geometry and
the Harrison trace — greatest separation and a distribution, not one number — and write the
answer into the state's `evidence_limit` and `docs/RESEARCH/shore_1812_pre_cut.md`. **Change
no geometry.** Wright stays the authority per the owner's ruling; this records how far a
second, pre-cut, unscaled reading sits from it, which is the only honest way to say how much
the post-cut base costs. If the two agree closely, that is a real strengthening of a derived
line and it should be said. If they diverge widely, that is a finding and it is filed, not
resolved here.
