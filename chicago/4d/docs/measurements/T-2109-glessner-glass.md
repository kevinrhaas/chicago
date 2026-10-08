# T-2109 — 1904's Glessner glass: two cheaper panes, priced and pictured

T-2099's still-frame reading (`docs/measurements/T-2099-still-frame.md`, PR #426) found
that the Glessner house's glass is about half of every frame at the 1904 landing.
The house's GLB marks its one `glass` material with `KHR_materials_transmission`
(transmissionFactor 1, ior 1.52, in both the full model and the `.light` one). Any
visible transmissive material makes three draw every opaque object a second time, into
a target the glass then samples.

`renderers/web/js/glass.js` swaps that material when the page loads. The GLB is not
changed: it still records what the glass is, and only how the browser draws it changes.

| `?glass=` | what is drawn | batches |
|---|---|---|
| `transmission` (the `full` default) | the GLB's own glass, refracting a second render of the scene | — |
| `clear` | plain alpha-blended pane, tint × 0.35, opacity 0.28, no depth write: the room shows through without refraction | one sorted transparent batch |
| `dark` (the `balanced` and `light` default) | opaque plate, tint × 0.12, the GLB's own roughness 0.065: reads like plate glass from the street in daylight | joins the house's opaque batches |

## Frame time at the 1904 landing

`tools/measure_still_frame.mjs` (T-2099's tool, from PR #426) with a `&glass=` added to
its URL; median of 2 frames, clock held. Run on the same runner, one after another,
2026-10-04. The device is SwiftShader: the milliseconds belong to this machine, and the
ratio is what carries over.

| viewport | tier | transmission ms | clear ms | dark ms | triangles (t → c) | calls (t → c / d) |
|---|---|---:|---:|---:|---|---|
| desktop 1280×800 | balanced | 9170 | **4442** (−52 %) | **4417** (−52 %) | 726,695 → 461,411 | 93 → 57 / 54 |
| desktop 1280×800 | light | 9121 | **4430** (−51 %) | **4420** (−52 %) | 718,761 → 457,444 | 91 → 56 / 53 |
| phone 390×780 dpr3, cpu/4 | balanced | 5965 | **2917** (−51 %) | **2898** (−51 %) | 736,239 → 466,183 | 91 → 56 / 53 |
| phone 390×780 dpr3, cpu/4 | light | 5988 | **2909** (−51 %) | **2918** (−51 %) | 736,239 → 466,183 | 91 → 56 / 53 |

Either cheaper pane takes **about half of the frame** at both tiers and both viewports.
On the GPU's side, the two cost the same as each other. They differ only in how the
glass looks.

## How it looks

`t-2109-glass/desktop-transmission-clear-dark.jpg`: the same stand, 8 m in front of
the landing, at `light`. Top to bottom: transmission, clear, dark.

- **clear** is almost the same as today. The upper panes keep their sky-lit sheen and
  are a shade darker.
- **dark** loses the sheen. Every pane reads as dark plate. That is a visible change,
  and no source was read here to say which look is truer to the house.

## What waits on the owner

The ticket asks him to pick which one ships, at least at `balanced` and `light`. Until he
does, nothing changes by default: on the dev preview, `?year=1904&glass=clear` or
`&glass=dark` shows each candidate. The recommendation is **clear at balanced and
light**, with transmission kept at `full`. It halves the frame and changes the least.

## The owner's pick (2026-10-04) and what shipped

**Answer (c): dark at `balanced` and `light`.** Since this PR `glass.js` draws the glass by
Scene detail setting: `GLASS_BY_DETAIL` is `full` → `transmission`, `balanced` and `light` →
`dark`, and `?glass=` still names one glass for every setting. The split falls exactly where the
Glessner asset does (the master GLB at `full`, the shared `.light` GLB below it), so the detail
switch's own rebuild is what changes the glass. `tools/check_glass_modes.mjs` holds the mapping
and the override. The dark plate is Liberty L383.

## Extended owner choice (2026-10-08, T-2183)

Dark glass now defaults at Full, Balanced and Light. The earlier measurements
and recommendation above remain historical; `?glass=transmission|clear|dark`
still overrides every setting. See `../RESEARCH/glessner-courtyard-windows-2183/`.
