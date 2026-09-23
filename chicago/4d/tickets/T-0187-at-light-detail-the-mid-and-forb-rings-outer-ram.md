---
id: T-0187
title: At light detail the mid and forb rings' outer ramps dither inside the verge
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: 392
claimed_by: run 8/26/2026, 11:27:35 PM CT
blocked_on: null
needs_bake: false
---

At light detail the mid and forb rings' outer ramps dither inside the verge.

Found while shipping **T-0093** (the near/mid handover), and named there as the residue that run
holds rather than closes.

**What it is.** T-0093 converted two boundaries from coverage ramps to density handovers — the near
ring's OUTER edge and the mid ring's INNER edge — so nothing inside the near/mid crossover is
written through the 4×4 Bayer screen door any more. The mid and forb rings' own OUTER edges are
still coverage ramps. At `full` that is fine: they run 18–27 m and 18.9–27 m, where a plant is a
handful of pixels and the far band stands over the same ground (T-0086). **At `light` — the phone —
the rings are 13.0 m and 13.0 m, so the same ramps run from 5.4 m and from 7.4 m**, which is inside
the verge a walker looks at. Measured on the published mirror before T-0093 landed, at the open
prairie stand at 390×780: `flora-mid` 122 partial instances inside 9 m, `flora-forb` 14.

**Why T-0093 did not do it.** Different edge, different ticket: T-0093's acceptance is about the
handover from the near tufts to the mid cards, and its two named stands are in a roadway where the
near ring places nothing at all. And the outer edge is not free the way the inner one was — the mid
and forb rings' outer boundaries carry the world-anchored **fringe** that keeps the sward's edge off
a constant screen row (ROADMAP § S6a item 3), and `tools/smoke_renderer.mjs` holds that with
*"the boundary's variation is the fringe, not a hole in the field"* (`minReach >= nominal − fringe −
1.2`, `meanReach >= nominal − 0.5 × fringe`). A density spread thins the outermost slots, so the
drawn edge moves in by roughly `band / N` for the N slots in a bearing bin's outer metre, and that
interaction has to be measured before it is chosen — not assumed to be small.

**Acceptance:** at 390×780 at `light`, `node tools/measure_near_verge.mjs --gate` reports **0.000 %**
of the frame screen-doored inside 9 m at every stand (it is the `ditheredShare` line, not the
handover line T-0093 already holds at zero) — and both boundary checks in the smoke's part 7 stay
green at their existing bars, with the measured reach printed before and after. Before/after pairs
of the verge at eye height on a phone.

**Links:** T-0093 (which found it, and the instrument) · T-0086 (the far band, and why the outer
edges were left) · ROADMAP § S6a items 3 and 3b · `renderers/web/js/flora.js` (`TUNE.mid.band`,
`TUNE.forb.band`, `fringeOf`, `slotRing`).

---

**Closed 2026-08-27 — the artefact is real and the named fix is not affordable at `light`. Measured
before a parameter was touched.**

**Reproduced.** `tools/measure_near_verge.mjs --viewport mobile --gate` on the published mirror,
390×780, booted `light` (the tool reads `window.__chicago4d.detail` back and prints it, so this is
not T-0162's trap — the detail tier is confirmed from the page, not assumed from the viewport):
15.395 % of the frame screen-doored inside 9 m at open prairie, 2.081 % from the South Water verge,
1.729 % at Wells approaching Lake, 0.000 % in the middle of the South Water travel track. `flora-mid`
partial over 5.19–13.04 m, `flora-forb` over 6.64–13.30 m. Exactly the banked figures, to the digit.

**The cause is narrower than the ticket assumed.** Not the boundary's KIND but the ramp's WIDTH.
`LOW` and `MID` cut the ring radii and scaled `fringe` with them — "about an eighth of the radius at
every setting" — and left `band` at TUNE's full-detail 7.0 m and 5.0 m. `balanced` had it too, and
nobody had noticed: its mid ramp began at 8.2 m, also inside the verge.

**THE FIX THE TICKET NAMES WAS PRICED AND REFUSED.** A density spread of the outer band was
simulated slot by slot against every mid instance's own `aChiRing` and the gate's own sixteen
bearing bins. Mean drawn reach: `full` 26.81 → 25.42 m (bar 24.90 — survives); **`light` 11.89 →
9.64 m against a bar of 11.60 m, of which only 0.29 m was unspent.** A one-metre spread lands at
11.48 m. So the ticket's two acceptance clauses — 0.000 % inside 9 m AND both boundary checks green
at their existing bars — cannot both be met by a density handover on this ring, and that is a fact
about the bar rather than about the fix: the reach admits any plant at `fadeAt > 0.02`, two per cent
coverage, which on a coverage ramp is every placed slot. Filed as **T-0209**. The bars were not
touched.

**Shipped instead:** the outer band is cut to the ring, under a rule written where the numbers live
— an outer band may not BEGIN inside the verge, `radius − step − fringe − 9.0`. `light` 1.6 m on
both rings, `balanced` the proportionate 4.7 m and 3.4 m, `full` unchanged. The grass lattice is
untouched — the ramp never paid for geometry — so the species deal and the drawn census are
identical plant for plant. Two things do move and both are stated in STATUS: fill, because the
ground the ramp used to thin is written solid; and the flower heads, whose ring hangs off the band
(`headRingOf`), so at `light` the forb heads run to 11.8 m where they stopped at 10.0 m.

**Both boundary checks green at their existing bars, and the reach went UP.** Part 7 at 390×780,
45 passed / 0 failed: min drawn reach **10.32 m** (unmoved, bar 9.60), mean **11.89 → 11.96 m**
(bar 11.60), max **12.76 → 13.22 m**, boundary rows **17.4 → 19.8 px** (bar 4). The smoke culls a
plant below `fadeAt <= 0.02`, which costs 0.14 m of reach on a 7 m band and 0.03 m on a 1.6 m one —
the mirror image of why the density handover could not be had, since that one does not draw the
outermost plants at all.
