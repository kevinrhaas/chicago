# What a year keeps resident — the memory meter and its ceilings (T-2546)

The owner, 2026-10-16: *"I see often that in a browser on mobile we get memory crashes and
it's getting jittery."* Frame time, triangles, draws and published bytes all had ceilings;
the thing that closes a phone's tab, resident memory, had none. This page is the meter, the
ceiling and the first reading.

## The tools

- `node tools/measure_memory.mjs [--year 1812,1835,1904] [--only desktop|mobile] [--json out]`
  boots each year door as a visitor does (the phone at 390×780, touch, dpr 3, its own boot
  tier; the desktop at 1280×800 `full`), enters the welcome at spawn, draws a few frames so
  every layer has been uploaded, forces two GCs and reads:
  - **JS heap** and **ArrayBuffers** (the backing store behind every live ArrayBuffer) from
    `Runtime.getHeapUsage`;
  - **GPU buffers** and **GPU textures**, measured: an init script wraps the WebGL
    allocation calls before the renderer exists and keeps each object's bytes, less deletes;
  - **per top-level layer** of `scene3d`: the page bytes its attributes still hold, an
    estimate of their GPU bytes, its textures, and the bytes **marked for release but never
    uploaded** (a chunk the tier hides is never drawn, so it keeps its arrays);
  - the **ten largest ArrayBuffer retainer paths** from a heap snapshot (`--no-snapshot`
    skips it).
  `--from reading.json` re-prints a reading with no browser.
- `tools/memory_ceilings.json`: one ceiling per year × viewport on the **total** (heap +
  ArrayBuffers + GPU buffers + GPU textures), at the reading plus 10 %, rounded up to 25 MiB.
  A ticket that lowers memory lowers its ceiling to its own reading by the same rule, in its
  own PR. A change that adds memory argues its new number there, with its reading.
- `--gate` holds the ceilings; `--self-test` boots `/1835/` on the phone with
  `?keep-geometry=1` (every page array kept, as before T-2158) and must read over the ceiling.
  Both run in `.github/workflows/chicago-4d-frame-time.yml`, one job per year × viewport plus
  the self-test, nightly and on any push that touches the tool or its ceilings. Never in
  `check.sh`, never in the smoke.

**What the figures are.** Headless Chromium on SwiftShader, so nothing is a timing; bytes are
bytes, and the same arrays and textures are made on a phone. A driver's own copies and
alignment are not counted, so the total is a **floor** on what a phone pays. On iOS the GPU's
share counts against the tab's own limit, which is why it is one number.

## The first reading — dev @ `8bbb1c670`, 2026-10-16, steward runner (MB)

| door | viewport | tier | JS heap | ArrayBuffers | GPU buffers | GPU textures | **total** | ceiling | boot + snapshot, s |
|---|---|---|---|---|---|---|---|---|---|
| /1812/ | desktop | full | 24 | 247 | 157 | 199 | **627** | 700 | 91 + 13 |
| /1812/ | phone | light | 24 | 95 | 55 | 71 | **246** | 275 | 34 + 6 |
| /1835/ | desktop | full | 111 | 707 | 417 | 343 | **1578** | 1750 | 205 + 39 |
| /1835/ | phone | light | 106 | 333 | 236 | 121 | **796** | 900 | 173–338 + 19 |
| /1904/ | desktop | full | 125 | 912 | 346 | 582 | **1965** | 2175 | 280 + 38 |
| /1904/ | phone | light | 215 | 415 | 213 | 456 | **1300** | 1450 | 91 + 35 |

The `/1835/` phone was read twice on the same build: 795.7 MB both times. The self-test
(`?keep-geometry=1`) read **962 MB** against its 900 MiB ceiling, so the gate goes red. Its
margin is 62 MB, not T-2158's 287, because about 108 MB of the arrays the release would drop
are never uploaded at `light` anyway (below).

The whole reading is `docs/measurements/T-2546-memory.json`;
`node tools/measure_memory.mjs --from docs/measurements/T-2546-memory.json` prints it.

### Whose bytes they are

- **/1835/ phone, per layer** (CPU kept / GPU estimate / textures / never uploaded): frontage
  80 / 65 / 16 / **53**, structures 36 / 71 / 27 / 0, enclosures 41 / 25 / 0 / **21**, yard
  30 / 17 / 15 / **22**, trees 5 / 41 / 16 / 0, terrain 20 / 19 / 0 / **12**, signage
  2 / 2 / 25 / 0. **About 108 MB of page arrays are marked for release and never let go**,
  because the chunks they belong to are hidden at `light` and never drawn, so never uploaded.
  The top retainers say the same thing: `frontage-chunk` and `enclosure-chunk` position,
  normal and colour arrays, then the buildings' batch geometry and its per-structure `geo`
  copies, and a 14.8 MB WebAssembly memory (a decoder).
- **/1904/ phone**: T-2548 has taken `assetBytes` off the phone (it no longer appears among
  its retainers; on the desktop, which banks GLBs for a detail switch, it is still the top
  retainer at 56 MB). The phone's top retainers are now the **`railway` layer** (215 MB of
  page arrays: float32 position, normal and colour on 114 meshes, plus 28 MB of instance
  matrices, none of it released after upload, since `RELEASE_KEEP` does not list the layer),
  then the buildings' float32 batch attributes and their per-structure `geo` copies. Its
  117 distinct textures decode to 456 MB on the GPU.
- The **layer estimate** of GPU geometry is printed beside the measured GL total
  (e.g. 281 vs 236 MB on the 1835 phone). Layers `upload-release.js` does not mark cannot be
  told uploaded from not, so the estimate runs high; only measured figures are gated.

These are the targets of the tickets after this one: T-2547 to T-2550 for page and geometry
bytes, T-2551 to T-2554 for textures. Each lowers its ceiling here.

## What it costs the gate

On the steward runner a year × viewport is one boot (34 s to about 6 min) plus up to 40 s for
the snapshot, which the gate skips: about 17 minutes of boots for all six, run as six parallel
jobs plus the self-test (about 4 minutes), each well inside its 25-minute timeout. `check.sh`
and the smoke are unchanged.
