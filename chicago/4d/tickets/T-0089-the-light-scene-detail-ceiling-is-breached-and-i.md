---
id: T-0089
title: The 'light' scene-detail ceiling is breached, and it was breached before this run's geometry
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-27
pr: 407
claimed_by: run 8/27/2026, 2:06:24 PM CT
blocked_on: Withdrawn on measurement: the 600,000 ceiling this breach was measured against was replaced by T-0135's re-basing to 1,050,000. See the body.
needs_bake: false
---

The `light` scene-detail level draws more triangles than its own ceiling allows, and it
did so before this run added a metre of plank walk.

**Measured 2026-08-18**, `tools/smoke_renderer.mjs --published`, desktop 1280 x 800, on the
T-0090 branch: `scene detail 'light' stays inside its own ceiling` FAILS at **604 950 tris of
600 000**, 48 draw calls. `full` and `balanced` both pass, and `turning scene detail down
actually draws less` passes — the levels still mean something, the tightest one is just over.
The mobile half does not fail it: at 390 x 780 the frustum is narrower and the count stays under.

**It is not this branch's.** T-0090's whole addition to the scene is the Sauganash's frontage,
and it was measured in the browser at **3 684 triangles** (the frontage layer draws 7 308 in
total: 3 624 the Green Tree's, 3 684 the Sauganash's, separated by a bounding box — the two inns
are 250 m apart). Take the most generous assumption for this branch, that every one of those
3 684 was inside the frustum at the station the ceiling is measured from, and `dev` still stood
at **601 266 of 600 000**. The branch made a breach worse; it did not open it.

**Why nobody had seen it.** The desktop half of the smoke has never finished inside this runner's
ten-minute per-command ceiling (**T-0060**), and this row sits at assertion 151 of it — far enough
in that the runs which do reach it are the ones that get lucky on timing. T-0052 measured the same
budget at **565 206 / 600 000** and **T-0056** is the open ticket for the layer that eats most of
it; the ~36 000 triangles of headroom that ticket bought have since been spent by the layers
shipped on top (the docks, the goods, the boards, the yard, the wagon shed and two frontages).

**Acceptance:** `scene detail 'light' stays inside its own ceiling` is green at 1280 x 800 on the
published mirror, with the saving stated against the 604 950 measured here, and **without thinning
what any layer claims to be** — T-0056's rule holds: a picket drawn as a rail is a
misrepresentation, not a saving. The likely first move is T-0056 itself (the enclosure layer is
detail-blind), and this ticket is where the number lives until it is.

**Update 2026-08-18 (T-0086, the far sward).** The far band adds a worst case of **2 660
triangles** at `light` — 190 cards of a 7-column archetype — measured in the browser at
**+1 962** at the South Water stand at detail `full`. It makes this breach 0.4 % worse and does
not open it; the saving this ticket asks for is unchanged and still sits in T-0056.

**Update 2026-08-19 (T-0063, the boats).** Measured on the T-0063 branch, desktop 1280 x 800 on
the published mirror: `scene detail 'light' stays inside its own ceiling` **PASSES at 597 894 of
600 000** (51 calls), with the nine-boat layer mounted — `full` 773 198 / 1 000 000 and
`balanced` 689 678 / 800 000 also green. Something between the 2026-08-18 measurement (604 950)
and this run bought the breach back under its ceiling; this ticket's acceptance may already be
met, but the headroom is ~2 100 triangles and the next geometry run will spend it — the durable
saving still sits in T-0056.

**Update 2026-08-20 (T-0049, the siding deal).** Measured on the T-0049 branch, desktop
1280 x 800 on the published mirror: `scene detail 'light' stays inside its own ceiling`
**FAILS at 605 134 of 600 000**, 52 calls. The breach is not the branch's: the siding deal's
whole geometry delta is **+492 triangles** summed over all 24 redealt GLBs (per-building
−48 to +80, counted from the committed web derivatives old-vs-new — a coarser exposure
means fewer courses, so eleven buildings got LIGHTER), an upper bound on its frustum
contribution. The spender is T-0110's ~9 000 street-refinement triangles (#268, whose
desktop half was cut before this row), landing on the ~2 100 of headroom T-0063 measured.
The durable saving still sits in T-0056.

**Update 2026-08-20 (T-0005, the sloughs).** Measured on the T-0005 branch merged with dev
(#273), desktop 1280 x 800 on the published mirror: `scene detail 'light' stays inside its
own ceiling` **FAILS at 614 828 of 600 000**, 52 calls, against clean dev's 605 414 the
same day, same runner. The +9 414 is the carved ground's: the slough swales subdivide the
terrain remesh, and the delta is level-independent (`full` 778 446 → 787 860, `balanced`
701 410 → 710 824 — the same +9 414 everywhere), which is the signature of a base-mesh
cost, not a detail-tier one. The breach it deepens was open before the branch (T-0115
banked 605 414 on T-0060's no-geometry branch). The durable saving still sits in T-0056.

---

## WITHDRAWN 2026-08-27 — the ceiling this ticket reports a breach of no longer exists

Re-measured on **dev at `d9b437dd`**, published mirror, with
`tools/measure_detail_ceilings.mjs` — T-0135's five stands, all three tiers, both
viewports. Every tier is inside its ceiling at every stand.

**desktop 1280 x 800**

| stand | `full` | `balanced` | `light` |
|---|---:|---:|---:|
| the Sauganash at 26 m | 1,009,901 | 857,553 | 641,786 |
| Lake Street at Canal, east | **1,423,855** | **1,239,486** | 839,778 |
| the forks, from Wolf Point | 1,412,635 | 1,223,388 | **858,200** |
| the open aerial | 1,038,508 | 862,941 | 642,448 |
| Lake and Market | 1,170,322 | 995,311 | 754,274 |
| ceiling | 1,425,000 | 1,260,000 | 1,050,000 |
| **verdict** | PASS by 1,145 | PASS by 20,514 | **PASS by 191,800** |

**mobile 390 x 780** — `light` worst **806,468** at the forks, PASS by 243,532;
`full` 1,376,697 (PASS by 48,303); `balanced` 1,195,584 (PASS by 64,416).

### Why this is a withdrawal and not a `done`

**The acceptance cannot be met, and it cannot be met because it was overtaken rather
than because the work was hard.** It asks for the row to be green *"with the saving
stated against the 604 950 measured here"*. There is no saving. The town draws
**858,200** triangles at `light` today — **42 % MORE** than the 604,950 that opened
this ticket. The row is green because the owner re-based the ceiling from **600,000 to
1,050,000** on 2026-08-22 (T-0135's five-stand re-argument, recorded at the definition
site in `main.js` `DETAIL`), and that entry says plainly what it cost: *"`light` now
carries 1,050,000, which is MORE than `full` promised the day before this commit."*

Marking this `done` would be reading a green row off a bar that moved under it, which
is the exact defect T-0135 was opened to end. So it is withdrawn on the measurement,
with the number banked above.

One real saving did land at this tier and it is worth naming, because it is the shape
this ticket asked for and got: **T-0150's furniture reach** distance-culls the derived
furniture at `light` only — the worst stand fell from 998,073 triangles and 177 calls
to 745,933 and 70. That is a distance cull, not a thinning, so it honours this ticket's
*"without thinning what any layer claims to be"*. It was not enough on its own; the town
grew past it.

### Where each half of this ticket now lives — nothing here is dropped

- **The durable saving** — **T-0056**, the enclosure layer's detail-blindness. Still
  open, still the right lever, and no longer bottled up behind this number.
- **Re-lowering the ceilings once trims land** — **T-0147**.
- **The breach that is live today** — **T-0223** (`full` and `balanced`), with
  **T-0229** the receipt for the raise that is meant to expire with it. Note the desktop
  `full` row above: **1,423,855 of 1,425,000, headroom 1,145 triangles — 0.08 %**. The
  raise T-0229 describes as *"the smallest step that clears the breach and leaves an
  ordinary parcel room"* leaves room for about a quarter of one tree. That is context
  for T-0223's urgency, not a new ticket: both tickets already own the state.
- **Nobody sees the row until the nightly bake** — answered by T-0126's
  `tools/measure_detail_ceilings.mjs`, the instrument used above, which reads the whole
  ladder in one command instead of at assertion 151 of a 55-minute crawl. Its own header
  cites this ticket as one of the two cases that justified building it.

**Links:** T-0056 (the layer that pays full cost at every level) · T-0060 (why the row went unseen)
· T-0126 (`tools/measure_detail_ceilings.mjs`) · T-0135 (the re-basing) · T-0150 (the trim that did land)
· T-0223 / T-0229 / T-0147 (today's budget) · `docs/ROADMAP.md` § THE RUN BUDGET · PR for T-0090 (where it was measured).
