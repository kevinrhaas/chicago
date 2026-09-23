---
id: T-0785
title: north_water's committed line stopped matching its own derivation when T-0686 moved the South Branch bank
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: null
claimed_by: null
blocked_on: Fixed on dev by T-0780 (#889), which re-derived north_water off the bank T-0686 moved.
needs_bake: false
closed_at: 2026-09-05T14:57:58.458Z
claimed_run: null
---

north_water's committed line stopped matching its own derivation when T-0686 moved the South Branch bank.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Inherited red on `dev`, found by T-0451, which does not touch it.**
`tools/check.sh` step *"north water street is still the line its own derivation produces,
and still dry"* fails on `origin/dev` as of f046ef78e:

```
committed  … [155.0, 121.8] [183.0, 157.5] [189.0, 157.5] [195.0, 157.5] [200.0, 156.9] [255.0, 128.3] [375.0, 121.6] [410.0, 118.1] …
derived    … [155.0, 121.8] [183.0, 157.5] [189.0, 157.5] [195.0, 157.5] [200.0, 156.9] [240.0, 134.3] [250.0, 134.3] [410.0, 118.1] …
```

`north_water` is DERIVED — `tools/derive_north_water.py` lays its corridor's south line on
the committed north bank and fits the centreline to the bank's 12.192 m offset curve. **T-0686
(#882) moved that bank**, putting the South Branch's east bank back on the ink Wright drew, and
the committed street was not re-derived in the same commit. Two vertices at local east 255 and
375 are now a pair at 240 and 250, so the reach between them is the disagreement.

The gate is doing its job and the fix is one command plus its consequences: re-derive, and
account for what moves with the street — the frontage works and yard stands that measure off
it, and T-0451's `market_north`, whose south end lands on `north_water`'s committed centreline
at exactly this reach. **T-0447 is open on the same west end** and should be read first: it
asks whether North Water Street runs across Wolf Point at all.
