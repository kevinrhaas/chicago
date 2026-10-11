# T-2207 — Glessner stable cupola and north loft fittings (audit GA-08)

## What the sources show

- **HABS photograph 1** (Cervin Robinson, 1963; committed web copy
  `chicago/prairie_1904_v1/research/public/glessner-habs-photo-01.jpg`), read at 5x on
  the cupola (crop 1240-1390 × 290-420 px). The vent band is **two tiers of
  round-headed openings, each on a projecting landing board** — a pigeon cote, not a
  louvre. The pyramid is steep and **kicks out over a deep eave**.
- **HABS photograph 17** (1965, from the north-east): the same flared pyramid, small.
  It is the second matched view for acceptance 1; it agrees on the tier/roof proportion
  and is too small to count holes.
- **HABS photograph 15** (1965): the gable without the cupola. It shows the 1946 loft
  boarding with its vent, as photograph 1 does.
- **HABS data p. 2**: the loft door was "closed up" in 1946. So a door hung there
  before. The 1946 boarding is not carried back to 1904 (acceptance 3).
- The audit's c. 1887 Cornell view (#104) and the Nickel west-roof view (#161) are
  link-only. The blog page served no images to this runner, so neither was read.

## Inventory of the north loft fittings (acceptance 2)

| fitting | 1904 treatment | basis |
|---|---|---|
| loft opening | kept, open, framed | HABS sheet 3 + photo 1 (existing) |
| loft door leaves | **added**: two six-board leaves standing open inward, strap hinges | HABS data p. 2 ("closed up" 1946); reconstructed |
| hoist stone | kept (W 140.5-141.7, 1.75 ft projection) | photo 1 (existing) |
| hoist iron | **added**: eye and hook 0.9 ft under the stone's nose | reconstructed |
| hoist beam / hay hood | **ruled out** | no source shows either; photo 1's long shadow is the stone's own in a grazing sun |
| pigeon holes 1/3/5 + ledge | kept | photo 1 (existing, T-1999) |
| carriage doors | kept | T-1999 |

## Captures

`before-desktop-*.png` were taken on dev's bake before any change. `desktop-*.png`
(1280×800, full) and `mobile-*.png` (390×780, light) were taken after.
`node tools/qa_glessner_t2207.mjs` (or `QA_TAG=before- QA_VIEWPORT=desktop …`) re-runs them.
`cupola-nw` was re-aimed and `cupola-west` added after the before set was taken, so
those two have no exact before. `cupola-east`, `north-gable`, `hoist-close` and
`street-nw` are matched pairs.

## Cost

| tier | before | after | cap |
|---|---|---|---|
| full | 1,234,129 | 1,236,675 | — |
| light | 198,082 | 199,116 | 200,000 |

The light tier draws the pigeon-hole heads with 3 segments (full: 6). K01 measure: 0
coincident faces in all three tiers. A first bake carried its own 0.2 ft fascia on the
cupola eave; it landed on the roof-edge pass's own eave fascia and gave 8 same-winding
duplicates in the quantized light tier, so it was removed and the roof-edge pass dresses
the eave, as it does every other eave in the house.
