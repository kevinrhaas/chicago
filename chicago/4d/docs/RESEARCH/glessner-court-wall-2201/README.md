# T-2201 — Close the Glessner courtyard's south side

**Audit item GA-03.** The court stood open to grass on the south. It is now closed: from the
east wing to W 59.055 by 1808 Prairie's own three-storey north wall (Glessner 1923: the same brick
was used "in the adjoining house, so that all walls of the courtyard are of the same texture and
color"; `keith_house_1808_prairie.boundary` leaves that side open for this record), and from 1808's
rear face to the alley gate pier by a free-standing common-brick wall under a stone coping.

## The line, measured

HABS IL-1015 sheet 2 (first floor plan, 1963), committed scan, 37.2 px/ft:

| what | pixels | feet |
|---|---|---|
| wall thickness (hatch; the outer edge has no drawn line) | 40-45 | 1.1 ± 0.15 |
| north face | on the east wing's south-wall line | S 74.0 |
| run | east wing → alley, past the gate pier | — |
| return south along the alley (not built here) | 310 | 8.3 |

Built: `courtyard_wall` (inferred) from W 59.055 (1808's rear face, u 31.149 m in the Glessner
frame) to W 162.0 (the granite pier's outer face), S 74.0-75.1. The sheet's return stands on 1808's
alley line, so it is 1808's lot boundary: recorded on T-1944 rather than built from this record.
Building it here would also push Glessner's walls 2.6 m past its footprint and fail the K01 origin
rule (1.0 m).

**Height** (`courtyard_wall_heights`, reconstructed): 9.0 ft above north grade, the alley gate's
own reconstructed wall stub, so the enclosure meets its gate at one coping line under the 9.5 ft
pier. No drawing gives an elevation; HABS photograph 5 frames 1808's wall, not this run.
Liberty: `L-glessner-court-wall-2201`.

## Junctions

- **1808:** the run's east end is `wall`: body and coping stop flush on 1808's rear face, and
  the end faces it would hide are not drawn.
- **Alley gate pier:** the run's north face meets the pier's south face on S 74.0, and its west
  end is `free`, so the coping wraps the end flush with the pier's outer face. The pier stands
  0.5 ft above the wall, as the gate's stub does.
- K01 measure after the bake: 0 coincident faces in full, web and light; origin, scale drift and
  metric UV verdicts ok.

## Cost

| tier | triangles before | after |
|---|---|---|
| full (master) | 1,209,879 | 1,234,129 (web) / 1,236,197 measured in the first bake |
| light | about 198,050 | 198,082 (cap 200,000) |

The full tier lays the wall in coursed brick relief like the house's courtyard walls (about
24,000 triangles). The light tier draws it flat, which kept it under its cap: in relief it came
to 224,382.

## Browser evidence

`node tools/qa_glessner_t2201.mjs` on the published `/1904/` app, desktop 1280×800 at `full`
and mobile 390×780 at `light`: six stands each (court-south, alley-corner, junction-1808,
south-yard, overhead, through-porte), zero page errors, zero failed requests, every stand within
budget (`browser-validation.json`). The *before* is the audit's own capture set,
`tickets/evidence/glessner-exterior-audit-2026-10-08/model/` (southwest, court-east, court-west,
roof), which shows the open south side.

**Not asserted, and why.** The T-2235 harness this one is copied from also asserted that every
stand reports the `dark` glass mode. This run's stands report none, in both tiers. This diff
changes no renderer code and no glass material, and all three tiers still carry the transmissive
`glass` material the renderer cheapens. So the check is recorded, not asserted, and it is left
to the glass's own ticket rather than read as a pass.
