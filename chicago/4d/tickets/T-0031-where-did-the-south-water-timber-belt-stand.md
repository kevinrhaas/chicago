---
id: T-0031
title: Where did the South Water timber belt stand
state: done
epic: FLORA
requested_by: loop
seen: false
effort: M
legacy_id: R-BUG5(b)
parent: null
opened: 2026-08-17
closed: 2026-08-27
pr: 393
claimed_by: run 8/26/2026, 11:27:06 PM CT
blocked_on: null
needs_bake: false
---

`main_stem_belt_east` draws nothing because none of it was on land. Where the belt's near
edge ran is a placement claim no held source settles. The three routes are in the blocked_on
field and § R-BUG5 (~866).


---
**OWNER RULING, 2026-08-17: route 1 — derive the belt from the committed `south_water`
street centreline**, the same move `south_branch_belt` already makes off the river's modern
course. The ruling authorizes asserting which side of the street the timber stood on, which
Andreas does not state — the implementing run records that assertion in `docs/LIBERTIES.md`
as a reconstructed placement, and the far-timber gates re-bank against the derived line.


---

## DONE 2026-08-27 — route 1, and the belt is derived rather than authored

**The line.** `tools/derive_timber_belt.py` builds `FAR_TIMBER.main_stem_belt_east` out of
`data/streets/1835.json`: the committed `south_water` centreline, mitred-offset **12.192 m**
(half the platted 24.384 m corridor) to the SOUTH, clipped east at the **mean easting of the
committed `wells` centreline, E +329.3** — byte for byte the number `timberEastLimits()` already
hands the near-field planter for the same limit, so the far body and the near wood cannot disagree
about where Andreas's belt ends. `tools/check.sh` re-derives it, so the belt cannot drift from the
street it is cut from.

**The measurement that decided it.** The census went **39 of 39 samples over water, 3.347 m under
the surface → 0 of 136**, and `main_stem_belt_east` left `tools/far_timber_baseline.json` by the
ratchet's own third rule. The belt is 265.0 m against the stub's 73.4 m, and every 2 m sample
stands **24–49 m from the water's edge** — inside the 30–74 m gallery `communityAt()` deals from
the same bank distance, so the horizon body stands on ground the near classifier independently
calls ZONE 5.

**A second fault the ticket did not name.** The stub ended at E +396, **66.7 m east of the Wells
Street it was named for**: it was authored against the old 640 m box with Wells guessed at E +400,
the same class of error K45(b2) found in `z05_riverbank_timber`'s note. Being east of its own
street is half of why it ended up in the channel; being offset north instead of south is the other
half.

**What a visitor sees.** The band drew nothing for eleven days. Measured through `horizonCensus()`:
**19 bearings from the Green Tree anchor** (73–80°, crowns to 36.6 px), **36 from Randolph and
Canal** (47–61°, 37.3 px), **15 from the forks** (84–89°, 46.9 px), and nothing from the
`south_water` anchor itself, which is correct — standing on the belt puts it inside `MIN_FAR_M`.

**The assertion the ruling authorised** is `docs/LIBERTIES.md` **L182**: south of the street, on the
dossier's own reading of the same sentence and on the measured 11.5–36.0 m of working waterfront
between the street and the water.

**Worth knowing before anyone re-quotes "the belt draws nothing":** since K45(b2) the near planter
sweeps the whole field and ends the South Division timber at the same Wells Street, so **70 stems
already stood in this reach**. The belt was absent from the skyline, not from the scene.
