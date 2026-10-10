# K09 on a named target: 1808 Prairie's carved street front (T-2310)

Piece 2 of T-1851 (package K09 of the T-1837 Prairie programme). Piece 1, T-2309, built the
carved-trim kit on specimen boards. This piece puts the kit's own pieces on a house in the 1904
scene.

## Acceptance (stated before work)

1. The target is named: **1808 Prairie** (`keith_house_1808_prairie`, register `pa-1808-6`). It is
   one of the two houses standing in the 1904 scene, and the register reads it as a
   "Romanesque-classical stone front". The other is Glessner, a documented landmark.
2. The entrance and the street windows are trimmed from the kit (`k09_trim.py` builders, sizes
   from `k09_trim.json`). The pieces are the kit's geometry moved onto the wall, not a copy of it.
3. Glessner's documented carving is kept distinct. It is not touched, and no kit motif stands on
   it (the kit's `never_replaces_landmark` restriction).
4. The record carries the choice as one attribute (`street_front_trim`, reconstructed) with a
   liberty, and the generator refuses a value it cannot build. The kit's data and both modules
   are inputs to the asset's hash, so a kit change stales the house.
5. The K01 contract measure stays green on both tiers: scale, origin, 0 coincident or degenerate
   faces, and metric UVs on the house's limestone tile.
6. The house is read in the actual published `/1904/` app at 1280x800 (full) and 390x780 (light)
   from the front, an oblique, the entrance and a principal window close (2-5 m), the rear and the
   roof. Every stand records load, draws, triangles, textures and a timed frame, with zero page
   errors.

## What was built

`generators/archetypes/k09_frontage.py` reads the record's `street_front_trim` and builds each
head with the kit's own `Variant` builders in the kit's frame (x along the wall, y up, z out).
It drops the specimen board and moves every piece onto the K01 street-front wall. `k01_frontage.py`
calls it where it used to lay a flat lintel.

| where | trim | kit source |
|---|---|---|
| door (north bay) | round ring of 13 voussoirs and a label, springing from two engaged foliate colonnettes on the stoop's landing; a plain tympanum over the flat door head | `voussoir`, `label`, `colonnette` + `capital.foliate` (the hero entrance's parts, one order) |
| principal-floor windows | architrave and a cornice hood on scrolled consoles | `k09.surround.rowhouse_restrained` |
| under them | a bounded foliate apron panel, centred between the basement light's lintel and the sill | `k09.trim.foliate_panel` |
| second-floor windows | a cornice hood on consoles | `k09.trim.lintel_cornice_hood` |
| third-floor windows | K01's flat lintel, kept | — |

Three fits were needed to make the kit sit on a real wall:

- **The sill runs past the architrave.** K01's sill stopped 0.08 m past each jamb, and the
  architrave is 0.15 m wide, so its feet would have hung over the wall. Under an architrave the
  sill now runs 0.18 m past each jamb.
- **The ring springs from the abaci.** The ring's intrados springs 10 mm outside the door jamb,
  over the abacus' inner edge. The colonnettes are engaged, with the shaft's back in the wall, so
  the abacus lies under the ring's springer. Like the kit's hero, each capital stops 4 mm short of
  what it carries, so no face lies on a face.
- **The crown clears the belt.** The label's crown sits at 5.26 m, 4 cm under the second-floor
  belt course (5.30 m). The generator raises an error if a change would make them meet.

## Costs

| | before (T-2291) | after |
|---|---|---|
| full GLB | 1,860,744 B | 2,726,168 B |
| web GLB | 782,536 B | 1,027,692 B |
| triangles | 8,264 | 19,128 |
| primitives | 14 | 15 (`carved_trim`, the capital leaves and panel carving) |

The K09 triangles by trim id are 6,336 for the entrance, 3,632 for the two apron panels, 440 for
the two principal-floor surrounds and 516 for the three hoods. The five flat lintels they replace
were 60.

In the app (`browser-validation-desktop.json`, `browser-validation-mobile.json`), every stand
stays within budget:
- **Desktop, full detail:** 64-67 draws, 2.51-2.53 M triangles of a 3.8 M budget, 124-146
  textures, ready in 34.4 s.
- **Mobile, light detail:** 61-63 draws, 0.48 M triangles, ready in 12.3 s.

T-2291's stands read 62-68 draws and 2.49-2.50 M triangles. Frame times here come from software
GL on a shared runner. Treat them as a relative reading only. The QA script times 5 frames per
stand (T-2291 timed 12), so the desktop pass fits a 10-minute foreground run.

## What the views show

- `*-front.jpg`: the trim's hierarchy up the front: the portal and the framed principal floor, the
  hooded second floor, the plain third floor. Glessner's own arched entrance is beside it.
- `*-oblique.jpg`: the hoods and consoles standing proud in a raking view, against the common
  brick return.
- `*-entrance-close.jpg`: the voussoir joints, the label's level returns and the foliate capitals
  under the springers.
- `*-window-close.jpg`: the architrave's feet on the lengthened sill, the consoles and the apron
  panel's leaves inside their field.
- `*-rear.jpg`, `*-roof.jpg`: no trim leaks round the corner, and the roof and eaves are as before.

## Not done

- **The register's entrance loggia** (Ionic columns, balustraded balcony, stair) is not built.
  The entrance kit (K07, T-2304) and the cornice and parapet package (T-1852) own those forms. The
  1888 plate they would be read from is not a source record here. The kit has no Ionic capital,
  so the colonnettes are the kit's generic foliate order (liberty L-k09-1808-trim-2310).
- **A carved tympanum.** The half-round over the door is plain wall. The kit's panel is
  rectangular, and the half-round has no room for one with its frame.

Re-run: `python3 generators/k01_emit.py --only keith_house_1808_prairie`,
`tools/web_derivatives.sh --only keith_house_1808_prairie__as_built_1886.glb`,
`node tools/k01_contract.mjs --measure-asset keith_house_1808_prairie`, `tools/publish.sh`, then
`QA_VIEWPORT=desktop node tools/qa_k09_t2310.mjs` and the same with `mobile`.
