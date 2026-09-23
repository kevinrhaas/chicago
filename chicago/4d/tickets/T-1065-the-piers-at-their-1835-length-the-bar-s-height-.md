---
id: T-1065
title: The piers at their 1835 length, the bar's height argued where the admission is, and the reservation's blue edge and the lighthouse checked against Wright's sheet
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0800
opened: 2026-09-12
closed: 2026-09-12
pr: 1189
claimed_by: run 9/12/2026, 5:44:16 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-12T11:45:08.387Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34689035657
---

Piece 2 of 2 of **T-0800 — The mouth as built**. T-1066 took its fourth ask (the re-bake, and
the staleness hash that had been hiding the need for one). These three are what is left, in
the parent's own words:

1. **The piers as structures**, on Wright's alignment from the bend, at the 1835 length the
   dossier gives — north pier between 700 ft (1834) and 1,850 ft (Oct 1837),
   *"interpolate ~1,000–1,300 ft, flagged inferred"*
   (`docs/research/01-terrain-hydrology.md` § 3.2). **READ `data/structures/north_pier.json`
   AND `south_pier.json` FIRST — they already exist**, measured off Wright's two red lines
   through the committed affine, with a bearing check against the documented 200 ft entrance.
   What is open is the LENGTH: both records carry 900 ft, interpolated and argued on
   `form.length_m`, against the dossier's own 1,000–1,300 ft. Settle that, and say which of
   the two arguments the ticket is overturning. A length change moves geometry: re-bake the
   two structures with `tools/bake.sh --only`.
2. **The bar's height, argued.** The parent quotes the spec's admission *"THE HEIGHT OF THE
   BAR IS CHOSEN, NOT FOUND."* **The four-reason argument the parent asks for is already
   written in that same note** (the soldiers' ditches and the 1834 breach, CPL's reading of
   the 1839 Fort Dearborn Addition plat, the high-water phase, and the direction of the
   error). Either this ask is already discharged — say so and close it — or it wants the
   dossier's beach-ridge figures brought in beside them, which is a paragraph and a citation,
   not a re-argument.
3. **The reservation's blue edge** as T-0792's polygon closing on the traced old channel, and
   the lighthouse (`chicago_lighthouse_1832`) checked against Wright's *L. House* beside the
   fort. The committed position is adjacency turned into a coordinate and says so; Wright's
   glyph would be the first independent witness to it. This is a plate reading plus a
   baseline, in the idiom of `tools/measure_*.py` — and it is the piece with the most yield.

**Acceptance:** a stated pier length with the argument that chose it and the two structures
re-baked to it; the bar's height either shown already argued or argued from the dossier's
figures where the admission is; the lighthouse position measured against Wright's sheet and
either confirmed with the residual or moved with it.

## Closed 2026-09-12 — all three asks, and only one of them wanted a change

**Ask 3 first, because it had the yield and it moved something.** Wright drew the lighthouse.
On his 1834 sheet, west of the fort at the inside of the bend, there is an inked ring with
*L. House* lettered round it. The ring's centre was picked twice — at 15x in IIIF region
`2913,1573,60,60` and again at 20x in `2925,1585,40,40`, a different frame so the eye could not
repeat itself — reading (2942.0, 1603.8) and (2940.5, 1603.9). The committed pixel is their mean,
**(2941, 1604)**, and through the one fitted affine this project keeps that is **local E +1055.59,
N +172.54** (UTM 16N 448128.29, 4637568.34).

| | before | after |
|---|---|---|
| position | local E +1105.2, N +229.2 | **E +1055.6, N +172.5** |
| grade | `reconstructed`, no source | **`inferred`, on `wright_1834` + `andreas_1884_v1`** |
| relation to the fort centre | 47.5 m, bearing 280° (WNW) | **107.9 m, bearing 243° (WSW)** |
| ground under it | +3.57 m | **+2.48 m**, dry, inside the modelled field |
| inside the derived reservation by | 20.8 m | **40.9 m** |
| liberties covering it | L44 | **none** |

Residual between the two: **75.31 m**. The reading's own uncertainty is **22.4 m** in quadrature
— 1.4 m picking, 10 m for the half-width of a ring drawn 19.9 m across for a forty-foot tower,
20 m for the affine here (whole-sheet RMS 17.5 m; the two nearest controls, G8 at 240 m and G6 at
320 m, residual 12.6 and 23.0 m). **3.4σ**, so it is a disagreement and not noise, and the point
it replaced was declared invention in its own note. The tower moved.

The reservation margin and the dry ground are **corroborations, not inputs**: neither was used to
choose the point, and both improved. `docs/LIBERTIES.md` L44 loses `position` from its covers list
— the gate caught that itself, which is the gate working. **Wentworth now disagrees** (his 1839
lots are north of the river) and is left disagreeing in writing; Andreas agrees better than
before. The reading is committed at `data/traces/wright_1834_lighthouse_glyph.json` and
`tools/measure_wright_lighthouse.py` recomputes the coordinate from that pixel on every
`check.sh`, so record and evidence cannot drift apart silently.

**Ask 1 — the pier length. Settled, and the conflict turns out never to have been one.** The
ticket asks which of two arguments is overturned: dossier 01's *"~1,000–1,300 ft, summer 1835"*
or `north_pier.form.length_m`'s 900 ft. **Neither, once 01's own arithmetic is done to the day.**
700 ft on 31 Dec 1834 to 1,850 ft in Oct 1837 is 1,019 days and 1,150 ft — 1.13 ft/day — and
1 July 1835 is 182 days along: **905 ft**, five feet from what is committed, on a straight
calendar interpolation with no season-weighting at all. 01's band is what the same line reaches
at the END of 1835 (1,112 ft), and dossier 04's documented 1,260 ft for the close of that season
sits in it too. So 01 printed a year-end figure under a "summer 1835" heading, and reading it at
the scene date is what made it look like a rival. Three lines of reasoning now converge on ~900 ft
where there were two that disagreed. `docs/research/01-terrain-hydrology.md` § 3.3 and its zone-24
row are corrected to date the band rather than dropped; `north_pier` records the settlement.
**No length change, so no bake** — and the record's own claim that 04 "supersedes" 01 is corrected
to the truth, which is that they agree.

**Ask 2 — the bar's height. Already argued, and one figure added.** The four-reason argument the
parent asks for is written where the admission is, in `terrain_spec.json`'s `islands[0].note`, and
has been since it was set. What the ticket offers as the alternative — the dossier's beach-ridge
figures brought in beside them — is worth having and is added as a **fifth** reason: dossier zone 3,
the mature lakeshore ridge belt, is given at **+9.0 to +10.0 ft and graded documented**, the only
elevation in that table that is. The bar is the young tip of the same littoral system, still being
trenched and breached, so a +4 ft crest sits 5–6 ft below it — the relation the evidence describes
— where +8 ft would put the youngest sand within a foot of the oldest. The height is still CHOSEN
and the surface still ships conjectural; the choice is now bounded above by a documented number.

**Gates.** `check.sh` 321 steps green (two of them new). Smoke, four legs, all `--published`, all
in the foreground and all filed to `dev-smoke-state.json`: desktop 2-3 (157 checks — the card and
the Evidence pane, where the sidecar, the liberties and the terrain note land), desktop 11-12
(80 — flora and What's-new), mobile 1-4 (250), desktop 1 (81 — the scaffold, for the publish
stamp). **568 checks, 0 failed, zero page errors.** Prose and gate tooling map to no part.

**The reservation's blue edge is NOT closed here, and is not in this ticket's acceptance.**
Ask 3's body pairs the lighthouse with "T-0792's polygon closing on the traced old channel", but
the acceptance names three things and that is not one of them — and it should not be, because the
blue edge is a **tract**, and T-0792 (open, band 6, owner) is the ticket that owns the tract layer:
*"the legend's nine coloured tracts are the town's survey history … and the project has no tract
layer."* Closing a swatch here would author the first tract outside the layer that is meant to hold
them all, which is the shape T-0792 exists to prevent. What this run leaves T-0792 is a filed
finding: the reservation's ground now carries a second reading on it, and the lighthouse glyph is a
control the blue edge's south-east corner can be checked against when the layer is built.
