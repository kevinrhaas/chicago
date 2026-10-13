# T-2213 (GA-12) — Glessner's dark glazing: depth and variation

The audit's finding: *windows appear as nearly identical dark blue-gray panels with repeating
diagonal shading.* `before-desktop-prairie-close.png` shows it: every light catches the same
gradient of sky, because every pane was one plate — one albedo, one roughness, one plane.

## What changed (renderer only — no GLB, no bake)

`renderers/web/js/glass.js` — when `cheapenGlass` builds the dark pane (the default at every
detail setting since T-2183), it now patches it:

- **`paneLayout()`** finds the panes in the GLB's glass mesh — each is its own 12-triangle slab
  — and the windows they stack into: same facing, same plane, overlapping across, gap no deeper
  than a meeting rail. Full model: 195 panes in 111 windows (mostly double-hung pairs). Light
  model: 99 panes in 98 windows. Each pane gets a seed from its position to the millimetre, so it
  draws the same on every load and at every detail setting.
- **Per pane:** a tilt of up to 0.03 rad out of plane plus a faint low wave, and a roughness of
  0.6–1.8× the GLB's. No two panes reflect the same sky.
- **Shallow backing:** the backing's head and sill sit 10 cm behind the glass and its jambs fall
  into shadow, with a parallax that moves with the eye.
- **Blinds:** each window has a pale holland shade hanging 6 cm behind the glass at its own drop:
  up (3 in 10), 16 / 27 / 40 / 68 % of the window's height, or to the meeting rail (3 in 10). A
  darker hem marks its edge. Narrow lights (a door's grid, under 0.3 m) and cellar lights (under
  0.6 m) get none. Because the shade sits behind the glass it moves with the viewpoint and does
  not read as painted on. Its albedo is set as a multiple of the pane's own, before
  `<color_fragment>`, so the building's tone and the confidence view still apply over it.
- `buildings.js` gives the patched glass its own batch key (`glassPanes`) and writes the
  `_pane` / `_paneWin` attributes in `normalizeGeometry`.

Evidence and liberties: `docs/LIBERTIES.md` § `L-glessner-glazing-blinds-2213`. The front
photograph with the Keith house (`a18-gh-glessner-front-with-keith`) shows pale shades at the
meeting rail and part-way; which window has which drop is reconstructed.

## Cost

| stand | draw calls before → after | programs | triangles |
|---|---|---|---|
| desktop, every stand | +2 | 37 → 39 | unchanged |
| mobile, every stand | +2 | 23 → 24 | unchanged |

The desktop `eighteenth` / `courtyard` / `court-close` stands and the mobile `eighteenth` stand
were already over the **triangle** budget before this change, with the same triangle counts (see
`before-browser-validation-*.json`). That is not this ticket's, and nothing here adds geometry.

## Reproduce

```sh
./tools/publish.sh
QA_TAG=after- node tools/qa_glessner_t2213.mjs        # desktop (full) + mobile (light)
node tools/check_glass_modes.mjs                      # the layout and patch, in check.sh
```

Captures: `before-*` is dev at d350deb62, `after-*` is this branch, both from the actual published
`/1904/` app with zero page errors and zero shader or console errors.
