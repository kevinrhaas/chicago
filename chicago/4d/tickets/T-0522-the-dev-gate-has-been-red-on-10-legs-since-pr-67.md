---
id: T-0522
title: The dev gate has been red on 10 legs since PR #670 merged the recovered census bridge
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: all five causes verified green on dev and part 13 smoke PASS 2026-09-09; twin of T-0683
needs_bake: false
closed_at: 2026-09-10T04:20:09.342Z
claimed_run: null
---

The dev gate has been red on 10 legs since PR #670 merged the recovered census bridge.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by the T-0460 run on 2026-09-03, which could not bring `tools/check.sh` green
because it was already red. **Measured on a clean checkout of `origin/dev`** (commit
`6e72679b`, "Merge PR #670: integrate recovered 1840 census household evidence"), with no
working-tree changes at all. Ten legs fail:

```
dataset (schema, provenance, date gates, licenses, staleness, publish)
validator self-tests
inferred households, adoptions and their buildings match the programme
every flora and fauna figure is declared read or banked unread
published mirror matches its source
the reconstructed residents' invented names re-derive
the documented residents on reconstructed roofs re-derive from the register
the minted documented residents re-derive from the register
the minted letter-list residents re-derive from the register
the scene-date register re-derives, and every action names its target
```

Three root causes are visible without digging:

1. **The new source record is outside the schema's own vocabulary.**
   `resident_research_v4_1835_census_bridge.json` carries `rights_status:
   'research_notes'` and `type: 'research_synthesis'`, neither of which is in the
   enumerations. Either the record's provenance metadata is wrong or the vocabulary needs
   the terms argued and added — **this is a provenance question and belongs to whoever
   holds the evidence**, which is why this run did not guess at it.
2. **~25 new `later_census.*` figures ship to the browser unread and unbanked.** Every one
   of them fails the layer-reads gate with "wire it up, or bank it with `--update` in this
   commit and say why a figure nobody builds is shipped to a browser". The merge did
   neither.
3. **The mirror was never published.** `site/chicago/4d/` does not match its source, so
   whatever did land is invisible on the live site.

**Why this is worth ranking rather than leaving at the bottom of the queue: it blocks
everything.** No ticket in this queue can satisfy an acceptance clause that asks for
`check.sh` green while this stands, and every improve slice this hour hit the same wall.
The queue's own ordering rule 4 — an invisible ticket outranks a visible one when it
BLOCKS it — is the case here. Agents do not reorder QUEUE.md, so this is left at the
bottom where the tool put it, with the reason stated.

**Acceptance:** `tools/check.sh` green on `dev`, with each of the three causes above
resolved on its own terms — the source record's `rights_status` and `type` settled against
the evidence rather than coerced to pass, the new figures either wired to a renderer or
banked with the reason in the commit message, and the mirror published.
