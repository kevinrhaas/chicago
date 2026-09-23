---
id: T-0199
title: The five South Water stores standing on a lot the roof schedule already dealt
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0127
opened: 2026-08-24
closed: 2026-08-27
pr: 371
claimed_by: run 8/26/2026, 11:58:51 PM CT
blocked_on: null
needs_bake: false
---

The five South Water stores standing on a lot the roof schedule already dealt.

Piece 2 of 2 of **T-0127 — The rest of the town gets the street edge**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

These five documented buildings on South Water Street's south side were placed in August 2026 by
reading the MODERN West Wacker Drive centreline out of OpenStreetMap and stepping 12.2 m south of
it — each record's own `position.note` says so, and several already warn that *"modern Wacker Drive
is not exactly the 1835 South Water Street line"*. Measured against this project's committed South
Water centreline, offset by half the committed 80 ft corridor, each stands out in the platted
roadway, and `tools/generate_frontage_works.py` refuses the plank sidewalk along the stretch it
covers. T-0188 reconciled the other six of the eleven; these five it could not.

| store | out past the frontage line | would move | and would then seat |
|---|---:|---:|---|
| `h_jones_store` | 8.17 m | 9.67 m | `blk_south_water_wells` lot 0 |
| `carpenter_south_water_store` | 6.62 m | 8.12 m | `blk_south_water_wells` lot 2 |
| `chicago_american_office` | 6.91 m | 8.41 m | `blk_south_water_dearborn` lot 0 |
| `frederick_thomas_shop` | 6.25 m | 7.75 m | `blk_south_water_dearborn` lot 2 |
| `pruyne_kimball_drugstore` | 5.55 m | 7.05 m | `blk_south_water_clark` lot 2 |

**WHY EACH IS BLOCKED, MEASURED ONE AT A TIME (T-0188 ran all five separately).** Every one of those
lots is in its block's `frontage.lots` in `data/reconstruction/1835_platted_block_parcels.json` — the
665-roof schedule has already dealt that lot's roof to the anonymous South Water frontage run — and
`tools/generate_block_infill.py` refuses to deal a roof to a lot that already carries one: *"the
schedule's headroom is the block's, not the lot's"*. Nothing overlaps geometrically; the three runs
physically stand at the east end of their faces, well clear of all five stores. The conflict is
entitlement, not ground.

**Two honest routes, and the ticket is for choosing one with numbers rather than by taste.** Either
the three blocks' headroom is re-scored and the frontage runs give up the lots the documented
buildings take — which removes standing anonymous roofs from the street and has to be argued against
the owner's *"there should be more and denser buildings"* — or the runs' entitlement is re-pointed to
the lots they physically occupy, which needs `check_frontage`'s adjoining-strip rule and
`ROW_UNITS_PER_LOT` measured against the result. Either way `tools/reconcile_665.py` re-derives the
programme in the same commit.

**Acceptance:** all five are either reconciled with the committed plat or refused in writing with a
NEW reason (the roof-schedule collision having been resolved or shown unresolvable); South Water
Street's walk then runs unbroken except where its own ground refuses it, asserted by standing the
walker on it end to end; no standing roof leaves the town without that removal being argued and
counted; and all three detail tiers stay inside their ceilings. Never by weakening a gate.

**Links:** T-0127 (parent) · T-0188 (piece 1, which measured all of the above) · T-0115 (the tier
ledger) · `data/frontage/town_street_edge.json` `refused`, where all five are already named.

---
## 2026-08-27 — SETTLED BY THE OWNER, and all five are on the plat

This ticket set out two honest routes and asked for one to be chosen with numbers. **Neither
was needed: the choice was the owner's, because it is the core density standard rather than a
sidewalk detail, and he made it on 2026-08-27.** A platted business-front lot may carry a
documented store at the street AND an anonymous dwelling behind it. So the third route — the
one the ticket did not list — is the one taken: the block programme's headroom is untouched,
the frontage runs keep every lot they were dealt, and the five stores come onto the plat
beside them.

**No standing roof left the town** (338 before, 338 after), no household moved, and no gate
was weakened. What moved is the RULE, deliberately: `tools/plat_occupancy.py` now answers two
different questions with two different maps — `occupied_lots`, "what stands on this lot",
unchanged and still truthful; and `exclusive_lots`, "what BARS another roof", which is the
first less the owner's clause. `tools/generate_block_infill.py` and `tools/reconcile_665.py`
both ask the second, so the generator and the schedule cannot drift apart on it (T-A6/T-A7).

**What the clause admits, and what it still refuses** — all three tests must hold:

1. the lot is named in that block's own `frontage` run in the committed parcel recipes, so an
   interior lot, a side lot, and any lot of a block with no frontage run are untouched;
2. the standing building is RESEARCHED — a record one of this project's reconstruction
   programmes wrote is not a documented store, and two anonymous roofs on one lot is still one
   too many;
3. it stands AT the street — its street wall no further back than the run's own units plus one
   lot margin (`setback_m + LOT_MARGIN_M`, both read from the block's own recipe). A documented
   building standing back in the depth of its lot still takes the lot.

…and a fourth that falls out of the third: the store has to be the lot's only occupant. A lot
the anonymous run already stands on has been used, which is what keeps the schedule from
offering a block room it is already building on.

**Nothing physical was relaxed, and only ONE rule moved.** No overlap, the lot margin, the
platted corridor and the three-metre separation all still bind, untouched. One pair did fail
the separation gate on the way — `recon_1835_blk_south_water_wells_d1_05` at **2.40 m** from
`carpenter_south_water_store`, side by side along the face with their fronts level — and the
honest fix turned out to be in the recipe, not in the gate. That break is AUTHORED: that slot
stands `clear_west_of` the store by a stated `clear_m`, and `place_frontage`'s own note says
where the figure comes from — *"the three-metre separation rule — not this recipe — is what
fixes the size of the break"*. **2.4 m was authored while the store stood 6.62 m out in the
roadway**, when the along-face break and the real gap were different things. On the plat they
are the same thing, so the authored break moved to the gate: **2.4 → 3.0 m**, one anonymous
roof 0.6 m further west, `clear_why` recorded beside it. The measured gap is now exactly 3.0 m.

**The five, and the metres:** `h_jones_store` 9.67 · `chicago_american_office` 8.41 ·
`carpenter_south_water_store` 8.12 · `frederick_thomas_shop` 7.75 ·
`pruyne_kimball_drugstore` 7.05, each along its block face's inward normal, each leaving its
street wall 1.50 m back from the committed frontage line — T-0198's method, so the eleven are
repaired by one rule. **South Water's street edge: 1,214.5 m of walk in 20 runs becomes
1,297.3 m in 18, with 9 corner crossings becoming 11 and 89 walking decks becoming 96**; the
Wells and Dearborn block faces each go from two stumps to one whole run. The march refuses
zero steps for a wall anywhere on South Water; the eleven wall-refused steps left in the town
are all on Lake Street, which is T-0196.

Closed with T-0220, which carries the fork as it was put to the owner and his answer.
