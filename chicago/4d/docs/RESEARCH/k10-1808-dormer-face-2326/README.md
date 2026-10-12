# T-2326 — the K10 dormer face on 1808 Prairie

The street dormer on 1808 Prairie's K05 hip, dressed as the K10 kit's pedimented dormer
(`k10.dormer.pedimented_on_bracketed_eave`, T-2316). T-2317 left this out because there was no
room for it (`../k10-1808-wall-head-2317/README.md` § Not built). This ticket makes the room, then
lays the kit's pieces.

**Acceptance (set before the work):** the kit's 0.20 m dormer cornice runs across the face and
is returned on both cheeks, with the sash's head clear of it by at least the kit's
`window_top_gap_m` (0.10 m). The kit's raking cornice stands on the tympanum. Every open edge lies
on a surface, no faces are coincident, and the published `/1904/` app shows it at 1280×800 (full)
and 390×780 (light) with no page errors, within the frame budget, and with its costs recorded.

## The re-proportion

| | before | after |
|---|---|---|
| dormer face height (record) | 2.15 m | **2.35 m** |
| face foot | 12.70 m | 12.70 m |
| sash sill / head | 12.95 / 14.45 m | 12.95 / 14.45 m (unchanged) |
| cheeks' soffit | 14.58 m | 14.78 m |
| sash head under the soffit | 0.13 m | 0.33 m = 0.20 cornice + 0.13 gap |
| dormer ridge | 15.60 m | 15.80 m |

The sash is already the contract's smallest opening (0.85 × 1.5 m), and its sill sits as low as the
K04 apron's upstand allows. That leaves the face's height as the only thing that can move. The
sash's flat K01 lintel (0.30 m) is dropped: as on the kit's own dormer, the cornice is the head.
`k10_frontage.dormer_fit` refuses a record whose sash head stands closer than the cornice's depth
plus the window gap under the cheeks' soffit.

## What is built (`generators/archetypes/k10_frontage.py`, `_dormer`)

- **The horizontal cornice.** The kit's `dormer_cornice` section is swept across the face at the
  foot of the pediment, mitred at both corners, run 0.13 m (`return_m`) back along each cheek and
  capped there. Under the cheeks' soffit its top is open, because it lies on the soffit. In front
  of the face, where only K05's raking soffit is above it, a top closes it.
- **The raking cornice.** The kit's two stepped bands (0.08 m crown 0.11 m proud, 0.10 m fascia
  0.05 m proud) stand on the tympanum. The crown's top runs under K05's verge (0.15 m deep, so it
  covers the crown) and its feet stand on the cornice's top. Where the verge's line meets the
  soffit 0.02 m past the cornice's end, the crown is stopped square over that end.
- Built in the face's own frame exactly as the kit builds its specimen (`Variant._dormer`), then
  turned onto the house. Painted timber, the verge's fascia material.

## Verification

- `node tools/k01_contract.mjs --measure-asset keith_house_1808_prairie`: 0 coincident faces,
  degenerate 0, back-to-back 0, at both tiers. Scale, origin and metric UVs are OK.
- `node tools/qa_k10_t2326.mjs` (desktop and mobile) in the actual published `/1904/` app: front,
  oblique, the face, the south cheek and the pediment close, and the roof. 0 page errors, 0 bad
  responses, every stand within budget (`browser-validation-*.json`, screenshots here).

## Costs

| | before (dev) | after |
|---|---|---|
| full GLB | 7,142,380 B | 7,147,776 B |
| web GLB | 2,133,112 B | 2,133,848 B |
| triangles | 60,872 | 60,944 (+72: cornice, top, bands, less the lintel) |

## Not built, and why

- **A parapet.** This is unchanged from T-2317. The register's pierced parapet would replace this
  dormer outright, and it waits on the 1888 plate being read as a source (T-1882).

Liberty: `L-k10-1808-dormer-face-2326` (docs/LIBERTIES.md).
