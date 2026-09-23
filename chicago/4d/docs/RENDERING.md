# RENDERING — the phased program toward AAA-class graphics

**Status: ACTIVE — owner reviewed and merged 2026-08-14 (PR #106).** The program is
sanctioned and its phases are buildable. Claim a phase the way ROADMAP parcels are claimed
(§7) before starting it.

Two things bound that sanction and are not negotiable by an agent. **Phases land on `dev`,
never on `main`** — `docs/PIPELINE.md`; production moves only when the owner dispatches
`chicago-4d-promote-to-prod.yml`. And the **H and N tracks, plus every item still boxed
`OWNER DECISION`, remain gated exactly as written**: activation covers the W track and the
G0 harness, not the tracks whose cost the owner has not yet ruled on.

Prerequisite reading, in order: `AGENTS.md` (the contract), `docs/GLB-CONTRACT.md` (the
portability promise every renderer inherits), the one phase you intend to execute (§4), and
`docs/STATUS.md` § "Known weaknesses, stated plainly" item 00 (the measured baseline this
program exists to retire).

---

## 0. What "AAA" means here — and what it cannot mean

The goal, in the owner's words: much higher resolution, more realistic, Call-of-Duty-class
graphics, on a base that was deliberately designed so that renderers can be swapped and
added. This document is the plan for getting there. Two lessons from this repo's own history
shape everything below.

**First: a blind side-by-side against a commercial game cannot be the bar.** The Joliet
project in this same repo was originally briefed exactly that way, and dropped it with
reasoning that stands (`joliet/docs/QUALITY-LOG.md` § "What the critic compares against"):
the comparison frames cannot be legitimately obtained, so a critic claiming to have run the
test would be fabricating its evidence — and an unsatisfiable exit condition reliably
produces either an infinite loop or a rubber stamp. The bar that can actually be held is the
one Joliet holds: **an independent critic scores fixed camera anchors 1–10 on eight axes
(lighting & shadow, material realism, texture detail & tiling, geometric detail & silhouette,
atmosphere, post-processing, composition, historical accuracy) against reference photographs,
with written justification and a specific fix for every axis below 8. Pass = mean ≥ 8.0 with
no axis below 7, under a regression gate on frame rate, draw calls and triangles.** This
project already owns a reference set: the twelve pre-fire pictorial plates in
`data/sources/assets/prefire_views_kevin_2026_08/` (one of which K2 designates a *negative*
reference) and the verified tallgrass photograph set from the 2026-08-10 prairie sweep, with
its two methodology corrections (§1) inherited by every future loop.

**The calibration photograph is in the repository as of 2026-08-15** (R-REF1):
`data/sources/assets/saari_2018_dupage_tallgrass/dupage_tallgrass_2018-07-24.jpg`, source
record `saari_2018_dupage_tallgrass`, CC BY-SA 4.0 and cleared for verbatim redistribution
and measurement but **not** for asset derivation. It is the file `world.js` calls
`bar/dupage_tallgrass_2018-07-24.jpg`, and until R-REF1 it existed in no checkout — so every
sky number in the renderer was a quotation nobody could check. `python3
tools/measure_reference.py` re-measures it, and **all four quoted sky readings reproduce to
within a few units**. Its frame is solved as well as committed: 57.0 px/deg vertical, the
horizon at row 820, so `elevation(row) = (820 − row) / 57.0` degrees above the horizon.
**State the elevation of any reading taken from it** — the readings this project has
disagreed about were taken at different heights in the frame, not from different photographs.

**Second: the gap to AAA is mostly not the renderer.** Joliet's own status, after building
the full PBR + IBL + CSM + SSAO + TAA chain: "the gap is content density — foliage, clutter,
decals, wear passes, set dressing, and the sheer number of authored props per square metre —
plus audio." 4D Chicago's measured critic losses (§1) say the same thing from the other
direction: the failures are structural — vegetation that ends before the haze begins, a town
with no textures, no baked occlusion, no furniture, no sound. A renderer swap alone would
render the same emptiness at higher cost. This program is therefore roughly one-third
rendering features, one-third calibration against references, and one-third content — and the
phases are cut accordingly.

**The strategic thesis: the data contract is the renderer abstraction.** This was the
design intent from the original brief and it is already real. `AGENTS.md`: renderers are
plural and disposable; they consume glTF + JSON sidecars and never reach into the data model.
`docs/GLB-CONTRACT.md` calls itself the interface between the generators and *every*
renderer, present and future. The uncompressed GLB masters in `assets/gltf/` are committed
and deliberately unpublished precisely so a future engine can consume them without the web
renderer's compression choices. So quality scales by **adding renderers in tracks** — the
dataset does not change, and no track is allowed to break another's gates. §3 defines three
tracks; §4 phases them.

---

## 1. Where quality actually is — the measured baseline

Everything in this table is measured, most of it in `docs/STATUS.md` § "Known weaknesses"
item 00 (the 2026-08-10 prairie sweep: three critics, blind A/B against verified Illinois
tallgrass photographs, all three lost). Owning phases refer to §4.

| # | Failure | Measurement | Owning phase |
|---|---|---|---|
| 1 | Mid-field vegetation ends before the haze begins | Canopy rings discarded beyond ~455 m (rings drop to `y = 0.05`, `aMask = 0`); the 93 % haze designed for 1290 m never lands on a vegetated pixel | W4 |
| 2 | No aerial recession on flat ground — structurally | At a 1.68 m eye, 55° vertical field, 800 rows: the whole 10 %→93 % fog ramp occupies ~6 pixel rows (402–406). Distance fog cannot buy recession here; only vertical structure carried into the distance can | W4 |
| 3 | Ring seam | `TUNE.mid.radius = 27 m` maps to a constant screen row on flat ground — predicted 448.8, measured 450, razor-straight across all 1280 columns | W4 |
| 4 | Grain collapses with depth | 5×5 high-pass RMS by depth band: ours 13.8 / 14.6 / 21.2 vs references 18.8 / 31.4 / 39.3 and 39.3 / 41.7 / 41.3 | W2, W4 |
| 5 | Horizon timber nearly absent | Detected in 31 % of horizon columns (3.6 % central two-thirds) vs 100 % in every band of the reference | W4 |
| 6 | Crowns read as boulders | Fine-detail ratio 0.23–0.34 vs the photograph's 0.61–0.64 | W4 |
| 7 | Shadows clip to black | Literal `(0,0,0)` where the photograph's darkest decile is L 14–27 | W1 |
| 8 | Sunlit crowns are blue | G−B −19 to −26 where the reference is warm green, +13 to +24 | W1 |
| 9 | Zero textures anywhere | Flat PBR colours on all 244 assets; the only textures in the scene are runtime canvases (prairie tile, street wear, water normal) | W2 |
| 10 | AO baked but switched off | `baked_ao: false` on all 244 assets. The bake works end to end; clapboard courses and window reveals a centimetre off the wall occlude each other (measured mean 0.265, 69 % of texels below half). It needs a low-poly AO cage, not tuning | W3 |
| 11 | No environment lighting | The sky PMREM is built at boot and deliberately not installed — at any useful intensity it swamped albedo (brown log wall at R/B 1.08 vs the 1.75 its colour specifies). `renderers/web/js/world.js` says the fix in place: "Revisit with a properly exposed HDRI rather than a PMREM of an analytic sky" | W1 |
| 12 | One shadow map, no cascades | ~~±60 m follow ortho~~ — **±120 m at 2048²/1024² (R-W3b(a), 2026-08-17), then ±240 m at 4096²/2048² (R-W5a2, same day), at an unchanged 11.7 / 23.4 cm per texel.** Still one map: past ±240 m the reach has to be bought by spending texels, which is R-W3b(b), true cascades | W3 |
| 13 | No reflections | Water is a flat plane with a drifting normal map | W5 |
| 14 | No town furniture | No fences, signboards, wagons, woodpiles, barrels, stovepipes, docks (ROADMAP K5, open, called "the biggest structural gap") | W6 |
| 15 | No audio | `assets/audio/` does not exist (ROADMAP S7) | W6 |

Two methodology corrections from the sweep bind every future critic loop: ~~**the honest
flower-load target is 4–6 %, not 13.89 %**~~ — **WITHDRAWN 2026-08-15 by R-W4c(b1): there is no
4–6 % target.** Its never-plowed-remnant half cites no photograph this repository holds, its
restoration-planting half does not reproduce (the committed recipe reads **5.54 %** on that frame
and 12.91 % is not on it under either ordering of the recipe's tests), and the recipe that read
both has recall **0.055**. Do not quote 4–6 %, 13.89 % or 12.91 % — read ROADMAP § R-W4c(b1)
first, and run `node tools/measure_bloom_target.mjs`. The correction that stands is **the shot
harness must be pitch-matched** (two rounds were judged at the wrong look-angle; the harness now
prints its pitch). A third stands as a warning: hue/saturation cannot separate July from October
here and must not be quoted.

Also on the books: current full-scene budgets are 49 / 53 draw calls and 378,647 / 499,343
triangles at 390×780 / 1280×800 *(the draw-call halves are 16-batch figures and are superseded —
R-W5a2 merged the town to one batch on 2026-08-17 and the worst desktop anchor reads 50 of 80)*,
against gates of **≤ 120 draw calls** and per-tier triangle
ceilings (1,000,000 full / 800,000 balanced / 600,000 light). There is headroom, and the
program spends it deliberately.

**The draw-call gate was 80 until 2026-08-21 and is 120 now** — a conscious re-budget on
the owner's ruling (*"or just raise the budget?"*), argued at the definition site in
`renderers/web/js/main.js` `BUDGET`. The 80 was set when every derived layer was ONE
town-spanning mesh; T-0067, T-0119 and T-0069 have since chunked those layers so the
frustum can cull them, which trades triangles for draw calls deliberately, and the sun's
own pass draws every chunk inside its ±240 m box a second time. Measured at the release
gate's stand (`frame('sauganash_hotel', 26)`), desktop: 65 calls before T-0069's street
edge and 78 after it. The TRIANGLE ceilings are unchanged and `light` remains the floor a
weak machine has to hold.

**Every figure in the two paragraphs above is a REFERENCE-STAND figure, and since
2026-08-22 the gate is not.** T-0135 replaced the one camera with a named set of five and
holds each tier to its ceiling at the WORST of them, which found the town 32 % over at
`full`, 27 % at `balanced` and 65 % at `light` — at viewpoints the Go-to menu already
offers. The ceilings were raised on the owner's ruling to 1,400,000 / 1,210,000 /
1,050,000 (`balanced` to 1,225,000 on 2026-08-24, below) and the call budget to 215, which made a dishonest number honest and left the
bottom rung heavier than the old top rung. T-0149 is the programme that wins the floor
back by trimming the axial view instead of carrying it; its first piece landed on
2026-08-23 (T-0150) and distance-culls the derived furniture beyond 350 m at `light`
only, taking the worst stand from 998,073 triangles and 177 calls to 745,933 and 70.
The ceilings above have NOT yet followed it down — that is T-0147, kept separate so the
trim has to be measured before the ceiling moves.

**`balanced` was re-budgeted once more on 2026-08-24 (T-0098), 1,210,000 → 1,225,000, and
the measurement is the point of the entry.** The parcel that found the bar measured it at
the worst stand twice, with and without itself: `dev` alone read **1,209,926 of 1,210,000 —
inside by SEVENTY-FOUR triangles**, and the same tree with a twelve-stem planting record
read 1,213,446. Seventy-four triangles is a quarter of one tree on a 1.2-million-triangle
frame: the middle rung was not overspent by that parcel, it was simply full, and the next
visible parcel of any size was going to fail it whatever it was. `full` carried 1.2 % of
headroom in the same runs, so the squeeze was on `balanced` alone. The new figure gives
`balanced` the same PROPORTIONAL headroom `full` has (about 1 %) over the measured worst
stand — the ladder keeps its shape, and the raise buys no room for the parcel after this
one. **`light` is untouched at 1,050,000 and reads 815,777, 22 % under.** T-0149 and
T-0147 still own the trim that would win the middle rung back properly.

Read `renderers/web/js/main.js`
`DETAIL`, `BUDGET` and `FURNITURE_REACH_LIGHT_M` for the arguments and the tables;
`tools/smoke_renderer.mjs` `STANDS` for the set.

---

## 2. Doctrine that binds every track

These are not suggestions; most of them carry data-integrity force established elsewhere.

1. **The conformance trio, in every renderer** (`docs/GLB-CONTRACT.md` § what the renderer
   must implement): the confidence view driven by the `_CONFIDENCE` vertex attribute, pick →
   provenance from the sidecar, placement computed from the sidecar (`local_e` / `local_n` /
   `rotation_deg` / `vertical_anchor`). The confidence view is not a debug feature; a
   renderer without it does not ship. K17's additions (roof dithering, a HIDE mode, per-level
   toggles) become part of the trio once landed. **Name the levels by function, not by the
   current strings** — K16 is renaming the vocabulary mid-flight; the three levels are
   *source-attested*, *reasoned-from-specific-evidence*, and *invented-to-fill-a-need*, and
   `docs/PROVENANCE.md` at your arrival date is the authority on their names.
2. **The lighting moment is data, not a control.** Sun position comes from NOAA's algorithm
   against the datum and the scene's `lighting.local_time` (local mean solar time — standard
   time zones did not exist in 1835). No invented weather in documentary rendering: there is
   no weather record for 1835-07-01, so clouds stay off. A sanctioned exception exists —
   the labeled cinematic mode, §8 decision 2 — and it is an *exception*, clearly labeled,
   off by default, never the canonical view.
3. **The LIBERTIES ledger binds the atmosphere.** L17 lets the ground run past the modelled
   box only because fog is total by 1500 m. L35 caps the horizon timber's haze at
   `HAZE_MAX = 0.82` as a recorded exception to L17's extinction. L80 replaced the far
   vegetation sheet with terrain colour because the sheet read as a second ground plane.
   A technique that changes what any liberty claims gets an appended **Revised** line in
   `docs/LIBERTIES.md` in the same PR — the ledger is append-only and supersession is
   recorded, never silent (L80 superseding L33 shows the form).
4. **No human figures, v1, uniformly** (`AGENTS.md` standing constraint). This binds native
   engines exactly as it binds the web renderer: no crowd systems, no distant silhouettes,
   no "just one blacksmith." An empty, accurate town is honest.
5. **Fidelity tiers may never degrade the reconstruction.** Detail levels scale flora and
   tree caps only — never buildings, terrain, or the river. A machine being slow does not
   make the town less true. Higher tiers may *add* (cascades, reflections, post); lower
   tiers fall back to today's rendering, which remains correct.
6. **The published-site budget is a gate, and raising it is a decision.** `tools/validate.py`
   enforces `SITE_BUDGET_MB = 25`; the site is at ~14 MB. The owner has sanctioned raising
   it to on the order of 100 MB *when the HD renderer ships* (§8 decision 3) — as a
   deliberate one-line change in the PR that needs it, never as a drive-by.
7. **Mobile is a release gate.** `tools/smoke_renderer.mjs` runs ~360 assertions at 390×780
   AND 1280×800 with zero page errors, and the `--published` run is the one that matters.
   Never weaken an assertion to pass. New capability means new assertions.
8. **`renderers/web/` stays no-build.** Plain ES modules, an import map, vendored three.js
   pinned by sha256 in `vendor/MANIFEST` — new addons are vendored from the *same* pinned
   tarball with manifest updates, or the whole vendor bumps at once. A build step is allowed
   only in a *separate* app directory whose built output is committed, which is exactly how
   `joliet/` ships (`site/joliet/app/`).
9. **No model identifiers in repo artifacts**, this document included.
10. **OWNER DECISION convention.** Items boxed as `OWNER DECISION` in this document are not
    executable by any agent until the owner records a ruling in §8. Three are already
    resolved there; the open ones stay open in writing.

---

## 3. The three tracks

Renderers are plural. The tracks are additive — none replaces another, and `walk/` remains
the permanently maintained, runs-anywhere baseline (it is also the fallback every tier
degrades to).

### Track 1 — maximize `renderers/web/` in place (phases W1–W6)

The current renderer, made as good as a no-build WebGL2 forward renderer honestly gets.
Everything here ships through the existing gates and stays inside the 25 MB envelope.
New three.js addons (RGBELoader, CSM, EffectComposer, SMAA, GTAO, Reflector) are vendored
from the pinned r0.185.1 tarball with `vendor/MANIFEST` + `MANIFEST.sha256` updates.

The ceiling, stated honestly: single forward pass plus a modest composer, SMAA-class
antialiasing (three's WebGL TAA is accumulation-based and unusable with a free camera),
single-digit-megabyte shared texture atlases, no real GI — analytic environment plus
hemisphere bounce. That ceiling is still far above today's floor: **most of §1 —
items 1–13 — is retirable inside Track 1.**

### Track 2 — a second, high-fidelity web renderer: `renderers/web-hd/` → `walk-hd/` (phases H0–H3)

A separate app with a build step (Vite + TypeScript, built bundle committed under
`site/chicago/4d/walk-hd/`, the Joliet precedent). **Recommended engine: three.js
WebGPURenderer with TSL node materials**, for these reasons:

- The genuinely portable modules — scene/sidecar loading, ENU↔world math, the NOAA solar
  position, the heightfield sampler, the walker, the input-intent layer — are plain ES
  modules that port nearly verbatim. The engine-specific 80 % (materials, batching,
  vegetation shaders, sky) is what gets rewritten, and it is exactly the part WebGPU + TSL
  improves.
- The confidence dither becomes a **TSL node composed onto every material** instead of
  `onBeforeCompile` string patches against three's GLSL chunk names — the single largest
  fragility in the current renderer becomes a first-class, testable function. The
  conformance trio gets *easier* to honor, not harder.
- three's WebGPU post-processing ships real temporal AA (TRAA), GTAO, bloom, depth of field
  and motion blur as maintained nodes, and the renderer falls back to WebGL2 automatically —
  which is how the 390×780 mobile gate stays alive on devices without WebGPU.
- One library family across both web renderers is one maintenance story, one vendoring
  policy, one set of glTF/meshopt/KTX2 loaders.

**The named fallback is Babylon.js**, and it is a real option, not a strawman: the Joliet
renderer in this repo already runs the full chain (PBR + IBL, cascaded shadows with contact
hardening, SSAO2, ACES, TAA, grain, motion blur, four quality tiers) with its pitfalls
written down. Phase H0 is a time-boxed bake-off with kill criteria decided *before* the
spike; if three-WebGPU fails them, port the Joliet chain and inherit its logs.

Code sharing policy: **copy, don't couple.** `walk-hd` bundles its own copies of the
portable modules. Duplication of ~1,500 stable lines is accepted; the data contract — not
shared code — is the interface, and `walk/`'s no-build gate must never depend on another
app's refactor.

### Track 3 — a native-engine renderer (phases N0–N2)

The only track that genuinely reaches the named bar. **Recommended engine: Unreal Engine 5**
— Lumen global illumination, virtual shadow maps, Nanite geometry and volumetric fog are the
technologies the "Call of Duty look" is actually made of, and UE imports glTF through
Interchange. **Godot 4 is the documented open-source alternative** (best-in-class native
glTF import; lower ceiling) — this document specifies the track engine-neutrally enough
that a Godot agent can execute the same phases, which honors the original brief's
"`(godot/)` later" note.

The dataset needs nothing: the uncompressed masters in `assets/gltf/` plus
`data/sidecars/<scene>/` plus `data/terrain/epochs/<epoch>/heightfield.bin` are the input.
(The Draco-vs-meshopt question from `docs/research/05-maps-and-precedents.md` is moot for
native tracks — masters are uncompressed by design.)

Coordinate conversion (glTF is Y-up right-handed metres; the ENU convention is
`world.x = +local_e`, `world.y = elevation`, `world.z = -local_n`):

| quantity | glTF / walk | Unreal (Z-up, left-handed, cm) | Godot (Y-up, RH, m) |
|---|---|---|---|
| east (`local_e`) | +X | +X × 100 | +X |
| elevation | +Y | +Z × 100 | +Y |
| north (`local_n`) | −Z | +Y × 100 | −Z |
| `rotation_deg` (bearing, CW from north) | yaw = −bearing | yaw = +bearing (handedness flip) | yaw = −bearing |

Structure identity must survive import: `node.extras` carries `structure_id`, and the node
NAME is `<structure_id>__<phase_id>` by contract — so even an importer that drops extras
still yields identity by name. N0 verifies both.

Distribution: **downloadable builds first** (Win/Mac/Linux on GitHub Releases — zero hosting
cost, honest). Pixel streaming — the browser-URL experience backed by a GPU server — is an
OWNER DECISION because it is a continuous cost, not a build artifact (§8).

### How a visitor selects a renderer

Each renderer is its own URL directory: `walk/` (baseline, permanent), `walk-hd/` (Track 2),
native builds linked for download. Deep links keep working forever; the two web apps are
separately budget-accounted.

The chooser is `site/chicago/4d/index.html`. Today `tools/publish.sh` writes it only if
absent (a redirect stub straight to `walk/`); at phase H1 that heredoc becomes an
unconditional write — a real generated mirror artifact like everything else in `site/` —
rendering one card per renderer with a one-line honesty note each ("runs anywhere" /
"high fidelity, WebGPU, larger download"), remembering the visitor's choice in
`localStorage` and redirecting instantly on return (`?choose` reopens the cards). Each
app's Settings tab cross-links the other.

**Explicitly rejected: a `?renderer=` parameter on one app.** The renderers are different
code payloads with different budgets; a switch inside `walk/` would drag Track 2's weight
into the no-build baseline and put both behind one gate. The plural-directories design is
the abstraction the project already chose — use it.

---

## 4. The phase plan

```
G0 critic harness ──► W1 light ──► W2 textures ──► W3 AO+cascades ──► W4 atmosphere ──► W5 water/post ──► W6 content+audio
   [S]                 [M]          [L]             [M]                [L]               [M]               [L]
G0 ──► H0 bake-off ──► H1 walk-hd slice ──► H2 HD content pack ──► H3 scored critic pass
        [M]             [L]                  [L]                     [M]
        N0 UE5 import+conformance ──► N1 look-dev ──► N2 content, audio, distribution
        [M-L]                          [L]             [XL]
```

Effort legend: S ≈ one steward run; M ≈ two to four; L ≈ five to ten plus bake cycles;
XL ≈ an ongoing program. Runner legend: **improve-runner** (no Blender, hourly loop),
**nightly bake** (`chicago-4d-bake.yml`, pinned Blender, PRs its own output),
**interactive** (owner-approved session; anything outside `chicago/4d/` scope or needing a
native workstation). W1+W4 alone retire most of §1 — if only two phases ever run, run those.
Every phase updates `docs/ROADMAP.md` and `docs/STATUS.md` in the same PR as its work.

---

### G0 — the critic harness *(S · improve-runner · no dependencies)* — **G0.1 DONE 2026-08-14**

**Goal:** one reproducible measurement loop for this scene, so every later phase proves its
delta with numbers instead of adjectives.

**Workstreams**
- `tools/critic_shots.mjs`: Playwright capture at a FIXED anchor set — the eight scene
  anchors in `data/scenes/1835.json` (sauganash, sauganash_wing, lake_market,
  first_post_office, forks, green_tree, south_water, from_above), the prairie-sweep
  stations (prairie_south, prairie_west, river_bank), and the K2 plate viewpoints as they
  land. Uses the existing `window.__chicago4d` API (`goTo`, `setAnimationHold(true)`,
  `capture`), prints its pitch (the sweep's pitch-matching correction is inherited), runs
  both viewports.
- Port the measurement recipes (Appendix B) into small scripts the harness can run: depth-band
  high-pass RMS, horizon-column timber detection, crown fine-detail ratio, shadow-decile L,
  crown G−B, flower-load fraction.
- Adopt the Joliet protocol verbatim for scored passes: independent critic (an agent that did
  not write the code under review), eight axes, written justification, specific fix per axis
  below 8, pass = mean ≥ 8.0 / no axis < 7, **hard cap four iterations per scene** — anything
  unresolved goes to a backlog and ships as-is. The critic compares against the §0 reference
  set, never against commercial game frames.

**Milestones**
- G0.1 — **DONE 2026-08-14.** Harness merged (`tools/critic_shots.mjs` +
  `tools/critic_metrics.mjs`), eleven stations, both viewports, smoke and check green.
- G0.2 — **numeric half DONE 2026-08-14** (`docs/STATUS.md` § "The critic baseline", every §1
  metric at both viewports). The baseline **8-axis score is still open** and is now its own
  parcel, ROADMAP **R-G1**: the protocol requires a critic that did not write the code under
  review, so the run that built the harness could not also be it.

**Amendment 2026-08-14 — "byte-stable" is now a stability contract, and here is the
measurement behind the change.** Within one browser process the captures are exactly
reproducible: leaving a station and returning reproduces the file bit for bit, so neither the
renderer, the scene nor the harness carries hidden state or hidden time. Across processes, on
this software rasteriser, they are near-identical rather than identical — both baseline runs
came out 11/11 byte-identical at both viewports, but an earlier pair of rounds had four
desktop stations alternating between two variants differing in 1, 2, 11 and 43 pixels of
1,024,000, on the horizon row and on alpha-blended surfaces. A hash gate would therefore have
failed intermittently while telling a later phase nothing about whether its change was real.
So `--stability` asserts what the program actually depends on — **≤ 0.05 % of pixels may
differ AND every reported metric must repeat within 1 %** — and reports the byte-identical
count beside it, because a fall in that count is worth reading even when it is not a failure.
Nothing was weakened to make a frame pass: the assertion is stricter than the phase needs on
the metrics and looser only on the last bit of the rasteriser.

---

### W1 — calibrated light and environment *(M · improve-runner · after G0)*

**Goal:** retire §1 items 7, 8 and 11 — an environment that lights the town without
overriding albedo, shadows that are dark rather than black, sunlit foliage that is warm.

**Workstreams**
- `tools/gen_sky_env.py`: generate a clear-sky equirectangular `.hdr` (~1024×512, ≤ 1.5 MB)
  from an analytic sky model evaluated at the scene's exact NOAA solar position — sun disc
  EXCLUDED from the map (the direct sun stays on the directional light; `world.js` already
  documents why a five-figure-radiance disc destroys the PMREM). Committed with its
  generation command and provenance in `assets/LICENSES.md`. This is not weather — it is the
  same documented clear sky, exposed correctly.
- The exposure discipline that was missing when the PMREM failed: a **white-card harness**
  (place a known-albedo Lambertian card in-scene, capture, assert the rendered value in
  band). The acceptance is the sentence the project already uses: *a documented white wall
  reads as white, and a brown log wall keeps the R/B ratio its base colour specifies
  (1.75, measured 1.08 at the failure).* Environment intensity is tuned until materials keep
  their hue, then the hemisphere fill and ground bounce are rebalanced down so total
  illuminance stays calibrated rather than doubled.
- Vendor `RGBELoader` (manifest update). Install the HDRI via PMREM as `scene.environment`;
  keep the Preetham sky as the visible backdrop (they must agree in hue at the horizon —
  assert it in capture).
- Lift the shadow floor: ambient/environment contribution inside shadowed regions so the
  darkest decile lands at L ≥ 14 (reference L 14–27), and re-tune the foliage
  leaf-transmittance tint so sunlit crowns measure G−B ≥ +10.

**Milestones**
- W1.1 — white-card and R/B assertions pass; env installed; no draw-call increase.
- W1.2 — shadow decile L ≥ 14 and crown G−B ≥ +10 at the G0 anchors; new smoke assertions
  added for both; §1 rows 7/8/11 measured-closed in STATUS.

---

### W2 — texture the town *(L · improve-runner + nightly bake + one interactive workflow PR · after W1)*

**Goal:** retire §1 item 9. Real material response — albedo/normal/roughness — on every
structure, within the 25 MB envelope, without breaking the one-BatchedMesh-per-material
draw-call economy.

**Workstreams**
- **Shared tiling material sheets, not per-building unique textures**: weatherboard,
  hewn log, round log, shingle, whitewash, canvas — one small library (1024², KTX2) mapped
  in world scale, with the per-building variation that already landed in K4 (board-tone
  jitter via `COLOR_0`) carrying the individuality. Texel density target 128–256 px/m —
  inspection distance is arm's length in first person.
- Generators grow real UVs per archetype (`generators/common/mesh.py` + archetype builders;
  **nightly-bake territory** — improve-runner ships the parameter/data half and says so,
  per AGENTS).
- Enable the anticipated-but-never-run pipeline stages: `gltf-transform palette` (merges the
  flat-colour materials it can), KTX2 compression — `tools/bake.sh` already auto-enables
  KTX2 when a `ktx` binary exists, so the change is installing KTX-Software in
  `chicago-4d-bake.yml`. **That workflow file is at the repo root, outside improve-runner
  scope — it ships via an interactive, owner-approved PR.** ETC1S for albedo, UASTC for
  normals.
- Confidence-view parity: the dither must render correctly over textured materials —
  `confidence.js` patches `map`-carrying materials the same as flat ones; add a capture
  assertion.

**Milestones**
- W2.1 — material sheet library committed with license provenance; palette + KTX2 stages
  live in the bake; first archetype family textured end to end.
- W2.2 — all nine families textured; texture payload ≤ 6 MB; site ≤ 25 MB
  (`validate.py --site` green); draw calls ≤ today's 49/53 (palette should *reduce*
  materials); confidence dither verified over textures; near-band high-pass RMS moves
  toward the reference (§5); K2's image-accuracy loops re-run on the landmark buildings.

---

### W3 — ambient occlusion and cascaded shadows *(M · nightly bake + improve-runner · after W2)*

**Goal:** retire §1 items 10 and 12 — contact darkening that makes geometry read as solid,
and shadows that hold resolution beyond 60 m.

**Workstreams**
- **AO cages**: per archetype family, a low-poly occluder proxy (the fix STATUS names for
  the measured 0.265-mean bake — clapboard courses and window reveals must not self-occlude
  at bake time). Bake AO into the atlas/UV2, flip `baked_ao: true` family by family in
  `assets/manifest.json`. Nightly-bake territory.
- **Cascaded shadow maps**: vendor three's CSM addon; two cascades on coarse pointers, three
  on desktop, replacing the single ±60 m follow-ortho. CSM composes with
  `confidence.js patch()` and the custom depth material (dithered walls must cast dithered
  shadows through every cascade) — verify on every material family, and tune bias per
  cascade.

**Milestones**
- W3.1 — AO live on all families, no course/reveal artifacts in capture diff, buildings
  gain measured contact darkening (before/after decile stats recorded).
- W3.2 — cascades live both tiers; shadow texel density at 100 m ≥ today's at 30 m;
  no acne/peter-panning at the G0 anchors; budgets hold; mobile smoke green.

---

### W4 — atmosphere and the mid-field *(L · improve-runner · after G0, best after W1)*

**Goal:** retire §1 items 1–6 — the sweep's structural failures. This is the highest-leverage
visual phase in the whole program.

**Workstreams**
- **Vegetated pixels out to the haze**: extend the instanced mid-field clump rings outward
  from ~455 m to where fog reaches ~90 %, with density thinning by distance — instanced
  cards, NOT a solid plant-height sheet, so L80's decision stands as written. If any
  implementation step reintroduces a continuous surface, L80 gets an appended Revised line
  argued from §1's measurements — never a silent supersession.
- **Kill the ring seam**: jitter/feather the ring radii so no constant radius maps to a
  constant screen row (acceptance: no straight-line boundary detectable across columns).
- **Aerial perspective with vertical structure**: the fog law itself stays L17-honest (total
  by 1500 m — keep the existing smoke assertion). What changes is what the fog has to work
  on: the extended mid-field, plus a height-aware fog term so vertical elements (timber,
  buildings, the fort group) carry visible recession the 6-pixel ground ramp cannot.
- **Horizon timber to reference density**: ≥ 90 % of horizon columns (reference: 100 % in
  every band, cap L35's `HAZE_MAX = 0.82` respected). The previous round's regression
  (21.1 % → 0.9 % while reporting a re-tone) is why G0's detector runs in CI, not in a
  one-off.
- **Crowns that read as trees**: near-crown silhouette and internal detail to fine-detail
  ratio ≥ 0.6 (canopy edge break-up, leaf-cluster frequency — geometry/shader work in
  `trees.js`, not textures alone).
- **`river_bank` conformance**: Zone 1 cordgrass at spec (1.2–2.0 m, 40–55 % cover,
  no bare soil) — the flora data already says this; the renderer is what fails it.

**Milestones**
- W4.1 — mid-field extension live: vegetated pixels present to the fog-90 % distance, ring
  seam undetectable, L17 assertion still green, triangle budget held via the existing
  flora-cap tiers (never via building/terrain cuts).
- W4.2 — horizon ≥ 90 % columns; crown fine-detail ≥ 0.6; depth-band RMS non-collapsing
  (far band ≥ 0.75× reference); flower load 4–6 % from `flower.bloom`, not `flower.load`
  (R-W4c(a)); blind A/B re-run against the sweep's
  references at the same stations — the loss margins recorded in STATUS either close or
  get honest new numbers.

---

### W5 — water, post-lite, dynamic resolution *(M · improve-runner · after W1)*

**Goal:** retire §1 item 13 and spend the remaining Track-1 headroom carefully.

**Workstreams**
- Vendor `EffectComposer`, `SMAAPass`, `GTAOPass`, `Reflector` (manifest updates).
- A small pipeline seam in `main.js` — today's single `renderer.render()` call becomes the
  no-post path of a two-path render (`composer.render()` when the tier enables it). This is
  deliberately NOT a renderer abstraction layer; it is one seam, and `__chicago4d` keeps
  its full API surface either way (the ~360-assertion smoke drives it).
- **Planar river reflection**: the water is a flat y=0 plane — the textbook Reflector case.
  Reduced-resolution reflection of buildings + terrain + timber only (no flora), desktop
  full tier only; the reflection pass's draw calls are accounted and asserted separately
  from the ≤ 80 main-pass budget.
- SMAA on desktop (the current MSAA stays for the no-post path); GTAO full tier only;
  **film grain only if the reference photographs justify it** — §1 row 4 is missing
  *surface texture frequency*, not missing camera noise, and W2/W4 are the honest fix.
  Anything further (bloom, DoF) waits for the cinematic-mode decision's implementation.
- **Auto image-sharpness**: a frame-time governor that walks the existing pixel-ratio
  setting (1 / 1.5 / 2) to hold ~30 fps mobile / ~60 desktop, honoring a manual override.

**Milestones**
- W5.1 — seam merged with zero behavior change at default tiers (capture-identical), smoke
  green both viewports.
- W5.2 — reflection + SMAA + GTAO live on desktop full tier; budgets hold (main pass ≤ 80
  calls; reflection pass documented + asserted); mobile path byte-identical to pre-W5
  rendering; auto-sharpness holds target frame rates on a throttled run.

---

### W6 — content density and ambience *(L · improve-runner for records + nightly bake for geometry · anytime, best after W2)*

**Goal:** retire §1 items 14–15. The Joliet lesson executed: props per square metre, and
sound. This phase is mostly the existing ROADMAP items done under this program's acceptance
numbers — it does not fork them.

**Workstreams**
- **K5 as written**: the `enclosure` archetype (fences, gates), signboards (subject named in
  the record, imagery not invented — L25's rule), woodpiles, barrels, wagons, stovepipes,
  porches, docks. Records and parameters from the improve-runner; geometry lands via the
  nightly bake's own PRs; every invention gets its liberty entry.
- **Wear and grime decals**: base-of-wall mud splash, threshold wear, chimney soot —
  extending the street-wear CanvasTexture approach to structures, confidence-graded like
  everything else.
- **The S7 ambience bed**: wind-in-grass, insects, river water, gulls — synthesized or
  license-verified only (an entry in `assets/LICENSES.md` per file; a `check_required`
  source ships nothing). Off by default, a Settings toggle, no autoplay before the
  gate's user gesture (the AudioContext hook already exists).

**Milestones**
- W6.1 — K5 families a–e landed with liberties; props-per-100 m² counted at the town
  anchors and recorded in STATUS.
- W6.2 — ambience live behind its toggle; axis-4 (geometric detail) and axis-5 (atmosphere)
  rubric scores at the town anchors ≥ 7; zero new pageerrors.

---

### H0 — Track 2 bake-off spike *(M · improve-runner · after G0; W2 assets help but are not required)*

**Goal:** decide three-WebGPU vs Babylon on evidence, in a week-scale spike, with the kill
criteria written before the code.

**Workstreams**
- `renderers/web-hd-spike/` (throwaway by declared intent): load three buildings + one
  terrain tile + the water plane from the *published* derivatives; implement the confidence
  dither as a TSL node; pick → provenance; TRAA + GTAO nodes; run on WebGPU Chrome/Edge and
  on the WebGL2 fallback at 390×780.
- Kill criteria (all must pass or the recommendation flips to Babylon): boots on WebGPU and
  on WebGL2-fallback mobile with zero pageerrors; meshopt + KTX2 assets load; the dither is
  visually correct in BOTH backends; TRAA stable under free-camera motion; frame time at the
  spike scene ≤ 1.5× the current renderer's on the same hardware.

**Milestones**
- H0.1 — spike runs; criteria measured; a decision memo appended to THIS document (§8 log);
  the spike directory deleted in the same PR (renderers are disposable — the memo is the
  artifact, not the code).

---

### H1 — `walk-hd` vertical slice *(L · improve-runner · after H0)*

**Goal:** a second conformant renderer, selectable by visitors, correct before it is pretty.

**Workstreams**
- `renderers/web-hd/`: Vite + TypeScript, vendored-in-lockfile deps, **built bundle
  committed to `site/chicago/4d/walk-hd/`** (the deploy workflow stays build-free, the
  Joliet way). Copies of the portable modules (loader, ENU, solar, heightfield, walker,
  intent) — copy, don't couple.
- **Conformance trio first**, before any glamour: confidence view (with K17's modes),
  pick → provenance, sidecar placement — verified against `walk/` with a placement-parity
  capture (same anchors, geometry within a pixel tolerance).
- Then the stack, in order: HDRI environment (from W1's generator, higher resolution),
  CSM with contact hardening, TRAA, GTAO, planar/SSR water, height fog honoring L17,
  the W4 atmosphere structure re-expressed in TSL.
- `tools/smoke_hd.mjs`: cloned assertion discipline (both viewports, zero pageerrors,
  budget assertions of its own), added to CI alongside — never replacing — the `walk/`
  smoke. The chooser page (§3) goes live in this phase via the `publish.sh` heredoc change.

**Milestones**
- H1.1 — conformance trio + placement parity green; smoke_hd green (WebGL2 fallback path
  included).
- H1.2 — full stack live; chooser deployed; `walk/` untouched (its smoke run proves it);
  side-by-side captures at the G0 anchors published in STATUS.

---

### H2 — the HD content pack *(L · nightly bake + improve-runner · after H1, needs W2)*

**Goal:** the resolution jump — the same masters, richer derivatives, served only to
`walk-hd`.

**Workstreams**
- A second derivative tier in the bake: 2K material sheets, higher-poly archetype meshes
  (real trim/reveal geometry where the web tier uses normal maps), a 4K HDRI, denser flora
  cards — all derived from the same masters and records; nothing forked.
- Execute the sanctioned budget raise: `SITE_BUDGET_MB` to the agreed number (order of
  100 MB — exact figure set here, in this PR, with the owner's sign-off recorded in §8),
  with per-app accounting so `walk/`'s share stays lean.
- Loading UX for the bigger payload: progress by stage, and the pack fetched only by
  `walk-hd` (the chooser's honesty note tells visitors the size before they click).

**Milestones**
- H2.1 — HD derivatives in the bake, budget raise merged with per-app numbers in the PR.
- H2.2 — `walk-hd` consumes the pack; `walk/` payload unchanged (asserted); capture deltas
  at the anchors recorded.

---

### H3 — the scored critic pass *(M · improve-runner · after H1, best after H2)*

**Goal:** hold the bar, in writing.

Run the G0/Joliet protocol on `walk-hd` at five anchors: independent critic, eight axes,
four-iteration hard cap, honest backlog for what does not close. **Pass = mean ≥ 8.0, no
axis below 7**, regression gate on frame time / draws / tris. Results and backlog land in
`docs/STATUS.md`.

---

### N0 — native import and conformance *(M-L · interactive, native workstation · anytime — the masters exist today)*

**Goal:** the portability promise proven in a native engine, correct before pretty.

**Workstreams**
- `renderers/unreal/` (or `renderers/godot/` — same shape): import scripts (editor Python /
  EditorScript), the coordinate conversion from §3's table, and docs. Engine binaries,
  derived data and marketplace content are never committed; if project size demands it,
  the engine project lives in its own repo and this directory holds the scripts + docs +
  a pointer — decide in this phase with the owner.
- Batch-import the uncompressed masters via Interchange; place every structure from its
  sidecar; verify `structure_id` survives (extras if the importer keeps them, node-name
  parsing as the contract-guaranteed fallback).
- The conformance trio natively: a confidence material function reading `_CONFIDENCE`
  (dither + hide modes), a provenance panel (UMG / Control) fed from the sidecar JSON,
  documentary lighting from the same NOAA solar math at the scene's moment.

**Milestones**
- N0.1 — full-town import scripted and repeatable; placement parity screenshot set vs
  `walk/` at the G0 anchors within tolerance.
- N0.2 — conformance trio demonstrated in-engine; import guide written well enough that a
  second agent reproduces it from the docs alone.

---

### N1 — native look-dev *(L · interactive, native workstation · after N0)*

**Goal:** the image this program is named for.

**Workstreams**
- Lumen GI + virtual shadow maps + volumetric height fog **calibrated to the same claims**:
  extinction total by 1500 m (L17), timber haze cap (L35), the documented clear sky at the
  documented solar moment. Documentary mode ships first and stays the default; clouds,
  weather and alternate hours exist only inside the labeled cinematic mode (§8 decision 2)
  and each cinematic preset gets a liberty entry when it lands.
- Nanite on terrain and structures; foliage re-scattered natively from the flora zone
  records (renderer-side scatter is legitimate — the current `flora.js` lattice is exactly
  that; the records, cover fractions and phenology stay the single source of truth).
- Materials from the same sheet library at native resolution; AO from W3's cages or
  Lumen-native; the W4 recession structure re-expressed with real volumetrics.

**Milestones**
- N1.1 — documentary mode at the G0 anchors through the 8-axis rubric ≥ 8.0 mean.
- N1.2 — cinematic mode (if exercised) clearly labeled in-app, liberties recorded, and the
  documentary default untouched.

---

### N2 — native content, audio, distribution *(XL · interactive · after N1)*

**Goal:** something a visitor can actually run.

K5-parity props natively (license provenance per `AGENTS.md` rule 6 — any third-party asset
library's license is OWNER-reviewed before first use, §8); the ambience bed spatialized; a
photo mode (the research plates' viewpoints as bookmarks); packaged Win/Mac/Linux builds on
GitHub Releases, linked from the chooser with size and system requirements stated plainly.
Pixel streaming only if the owner sanctions the standing cost (§8).

---

## 5. The numeric targets ledger

One sheet, so builders and critics read the same numbers. "Ref" = the §0 reference set;
recipes in Appendix B.

| metric | target | source of target |
|---|---|---|
| Horizon timber column coverage | ≥ 90 % (ref: 100 % in every band) — quote `timberOnly`, never `coverageAll` (R-W4a) | STATUS §00 |
| Crown fine-detail ratio | ≥ 0.6 (ref 0.61–0.64) | STATUS §00 |
| Sunlit crown warmth (G−B) | ≥ +10 (ref +13..+24) | STATUS §00 |
| Shadowed darkest decile | L ≥ 14, no literal (0,0,0) (ref L 14–27) | STATUS §00 |
| Depth-band high-pass RMS | non-collapsing; far band ≥ 0.75× ref | STATUS §00 |
| Flower load | 4–6 % of vegetated pixels — **quoted from `flower.bloom`, never from `flower.load`, which counts a yellow coneflower as grass (R-W4c(a)); and the target itself needs re-deriving before it is compared against `bloom`** | STATUS §00 correction |
| Vegetated-pixel extent | present to the fog-90 % distance | §1 item 1 |
| White-card / albedo integrity | white wall in band; log-wall R/B ≈ 1.75 | world.js measurement |
| 8-axis rubric | mean ≥ 8.0, no axis < 7, ≤ 4 iterations | Joliet QUALITY-LOG protocol |
| Draw calls (`walk/`) | ≤ 120 (raised from 80, 2026-08-21 — see §above and `main.js` BUDGET); shadow pass included in the count | existing BUDGET + W5 |
| Triangles (`walk/`) | ≤ 1,000,000 / 800,000 / 600,000 by tier | existing DETAIL |
| Published site | ≤ 32 MB (raised from 25 on 2026-08-29, T-0317, and from 28 on 2026-08-30, T-0379 — the owner's ruling that the town holds every letter-list name added 712 household records; the cohort was first cut by a third by de-duplicating prose identical on all 727, which was not enough. Both raises reasoned at `validate.py` § SITE_BUDGET_MB) until H2's sanctioned raise (~100 MB) | validate.py + §8 |
| Drawn ground vs the heightfield | within the 22 mm road lift at **every** field sample, after conforming (16-bit: 12.9 mm worst; 14-bit was 46.3 mm at 87 samples) | R-W6, `tools/measure_terrain_horizontal.mjs` |
| Page errors | zero, at 390×780 AND 1280×800, every renderer | AGENTS.md |
| Fog extinction | total by 1500 m, every renderer, every mode | LIBERTIES L17 |

**Note 1 — the ref-derived rows can now be re-derived, and should be.** Every row sourced to
"STATUS §00" is a number measured off the July tallgrass reference, and until 2026-08-15 the
photograph was in no checkout: the targets were quotations, and a builder who disagreed with
one had nothing to open. **R-REF1 committed it** —
`data/sources/assets/saari_2018_dupage_tallgrass/dupage_tallgrass_2018-07-24.jpg`, source
record `saari_2018_dupage_tallgrass` — and `python3 tools/measure_reference.py` reproduces
all four sky readings `world.js` quotes to within a few units. Two consequences for anyone
touching this table:

- **Re-anchor by measuring, not by re-quoting.** `tools/critic_metrics.mjs` was built so the
  same recipes can measure a reference and a frame; the reference now exists to point them
  at. A target that a re-measurement moves should move, with the measurement quoted.
- **Every reading carries its elevation.** The frame is 57.0 px/deg vertical with the horizon
  at row 820, so `elevation(row) = (820 − row) / 57.0` degrees, the frame reaches 14.4° above
  the horizon, and the camera was pitched −12.1°. Two of this project's own reference
  disagreements have turned out to be two people measuring different heights in the same
  photograph — one of them cost a whole tuning round (§1's look-angle correction).
- **It may be measured; it may not be derived from.** CC BY-SA 4.0: verbatim redistribution
  and measurement are cleared, any crop or resample is an adaptation carrying ShareAlike.
  `assets/LICENSES.md` holds the clearance. And it is still not evidence for flower load —
  it is a restoration planting, and §1's correction to 4–6 % stands.

---

## 6. What we will not do

- No invented weather, clouds, or times of day in documentary rendering — and the cinematic
  mode never becomes the default or the screenshot-of-record for a documentary claim.
- No human figures, in any renderer, until the consultation constraint lifts.
- No invented imagery on documented signs (L25's rule: the record names the subject; the
  mesh says only that something hung there).
- No weakening, skipping, or deleting a smoke assertion to make a phase land.
- No degrading buildings, terrain, or the river by quality tier.
- No CDN scripts, no runtime-fetched code, no build step in `renderers/web/`.
- No claimed comparisons against commercial game frames — the rubric is the bar.
- No silent budget raises, no drive-by edits to `SITE_BUDGET_MB`.
- No renderer reaching into `generators/` or reimplementing the data model.
- No baking the confidence presentation into geometry — it is a renderer effect driven by
  `_CONFIDENCE`, per the contract.
- No third-party asset library in any track before its license is recorded and
  owner-reviewed (`assets/LICENSES.md`).
- No model identifiers in any artifact this program produces.

---

## 7. How an external agent starts

You are picking up ONE phase. The generic entry checklist:

1. **Read**: `AGENTS.md` (every rule applies), `docs/GLB-CONTRACT.md`, this document's §2
   and your phase, STATUS § "Known weaknesses" item 00. If your phase touches vegetation or
   atmosphere, read the liberties it names (L17, L35, L80) in full before writing code.
2. **Claim**: mark your phase heading here (§4) `CLAIMED <date>, expires <date+3d>` in a
   small first commit, the way ROADMAP K-items are claimed — parallel runners must not
   collide. Check `git log` and open PRs first; a phase someone claimed and shipped half of
   is theirs to finish unless the claim expired.
3. **Baseline**: on a fresh `steward/<topic>` branch off `main`, run both gates BEFORE
   changing anything — `./tools/check.sh` (needs `pip install jsonschema pyproj openpyxl pypdf numpy scipy
   Pillow` — T-1083; without the last three, thirteen steps stand on banked readings) and
   `node tools/smoke_renderer.mjs` — so you know green means your green.
4. **Work inside the phase's file list.** A unit that needs new geometry ships the
   data/archetype half and says so — the nightly `chicago-4d-bake.yml` bakes and PRs the
   rest. Never install Blender on the improve runner. Anything outside `chicago/4d/` +
   `site/chicago/4d/` (workflow files included) goes through an interactive, owner-visible
   PR.
5. **Definition of done**, every phase: its milestone criteria measured and quoted in the PR;
   both gates green in the foreground; `tools/publish.sh` run in the same commit as any
   renderer/data/scene change (docs-only changes excepted — `docs/` is not mirrored); a
   changelog entry (`v: null, ts: '', date: ''`, then the stamper) for anything a visitor
   can see; `docs/ROADMAP.md` + `docs/STATUS.md` updated in the same PR; liberties appended
   for anything invented.
6. **Honesty**: report the numbers you measured, including the ones that got worse. A phase
   that closes three metrics and regresses one, stated plainly, is a good phase. The sweep's
   history shows what a round that "reported re-toning" while regressing 21 % → 0.9 % costs.

**Track 2 delta**: `walk-hd` has its own smoke (`tools/smoke_hd.mjs`) and its own budget
accounting; its built bundle is committed under `site/chicago/4d/walk-hd/`; `walk/` must
pass its own unchanged smoke in the same PR — the baseline renderer is never collateral.

**Track 3 delta**: work happens on a native workstation in an interactive session, consumes
`assets/gltf/` masters + `data/sidecars/` + the terrain epoch, commits scripts and docs
(never binaries), and its definition of done includes the in-engine conformance screenshot
set at the G0 anchors.

---

## 8. Decisions

**RESOLVED — owner, 2026-08-14** (recorded from direct review):

1. **Scope of the program**: all three tracks are in scope, phased as this document lays
   out, with UE5 as the primary native engine and Godot 4 documented as the open
   alternative. Downloadable builds are the native distribution channel first.
2. **Cinematic mode**: sanctioned — an optional, clearly-labeled, off-by-default
   non-documentary presentation (clouds, weather, alternate hours) may exist in Track 2/3.
   Documentary rendering stays the canonical default in every renderer, and each cinematic
   preset gets a liberty entry when implemented.
3. **HD budget**: raising `SITE_BUDGET_MB` deliberately (order of 100 MB) when `walk-hd`
   ships is approved in principle; `walk/` stays lean regardless.

**RESOLVED — owner, 2026-08-14** (second set, recorded from direct instruction):

4. **The program is ACTIVE.** Reviewed and merged as PR #106. The W track and G0 are
   buildable now; H and N stay gated behind the open decisions below.
5. **KTX-Software on the bake runner is APPROVED.** `.github/workflows/chicago-4d-bake.yml`
   installs the `ktx` binary so `gltf-transform` can run `--texture-compress ktx2` (W2).
   Until W2 lands there is nothing textured in the scene, so this changes no bytes today —
   it removes the blocker from the phase that needs it. Note the failure mode it fixes:
   `tools/bake.sh` asks for KTX only when the binary is present, because gltf-transform
   aborts the WHOLE optimize when it is absent — meshopt included — which silently meant no
   compression at all on the derivatives for months.
6. **Overnight integration targets `dev`.** Neither the hourly steward lane nor the nightly
   bake may write to `main`. The bake branches off `dev` and PRs into `dev`; promotion to
   production is owner-dispatch only. Recorded because it changes where every phase in this
   document lands, not merely how it is reviewed.

**RESOLVED BY MEASUREMENT — R-W6, 2026-08-16** (no owner ruling was needed once the number
existed, which is the point of taking the measurement first):

7. **The terrain keeps shipping quantised, at 16 bits on the epoch meshes.** The payload question
   ("688 KB on a lattice against 6.45 MB exact") turned out to be answerable without trading
   anything: 16 bits costs **1,116 bytes** and takes the drawn ground's worst departure from the
   heightfield from **46.3 mm to 12.9 mm**, inside the 22 mm road lift at all 259,689 field
   samples, while the uncompressed file would buy 12.9 → 7.7 mm for 5.8 MB — and 7.7 mm is the
   master's own decimation error, which no compressor setting touches. Raising every asset to 16
   bits was measured and rejected: +105.7 KB for nothing visible, because quantisation precision
   is set per-mesh by its own bounding box and only the terrain and water meshes are km-scale.
   Full table and the two corrections it carries: ROADMAP § R-W6, STATUS 2026-08-16.

**OPEN** (no agent acts on these without a ruling recorded here):

- `OWNER DECISION` — **Pixel streaming** for the native build (a standing GPU-server cost
  vs. download-only distribution). Default until ruled: download-only.
- `OWNER DECISION` — **The exact H2 budget number**, set in the H2 PR with per-app
  accounting attached.
- `OWNER DECISION` — **Third-party asset libraries** (native props/materials, e.g. engine
  marketplaces): license terms reviewed and recorded before first use; until then, N2 uses
  only project-generated and license-verified content.

Decision log additions (H0's bake-off memo, budget sign-offs) append here.

---

## Appendix A — the current renderer, inventoried

`renderers/web/` — vanilla ES modules, import map, vendored three.js r0.185.1
(sha256-pinned), no build step. ~11,600 lines of app JS.

| file | LOC | role |
|---|---|---|
| `js/main.js` | 761 | boot, render loop, detail tiers, budgets, the `window.__chicago4d` harness |
| `js/scene-loader.js` | 181 | scene/datum/sidecar-index fetch, GLB parse, the registry (pure data; portable) |
| `js/world.js` | 501 | Preetham sky + patches, NOAA solar position, sun/hemisphere lights, shadow follow, fog |
| `js/terrain.js` | 894 | ENU↔world convention, heightfield sampler, ground tiling, water, prairie shader |
| `js/buildings.js` | 409 | per-material BatchedMesh batching, sidecar placement, raycast picking |
| `js/confidence.js` | 236 | THE confidence view — the one material hook every mesh passes through |
| `js/flora.js` | 2525 | instanced prairie: lattice placement, wind, leaf transmittance, ring fades |
| `js/trees.js` | 1876 | near timber (merged) + horizon silhouette band with hand-computed haze |
| `js/streets.js` | 287 | 17 dated travelways draped on the heightfield, canvas wear |
| `js/walker.js` | 399 | first-person capsule + free-fly; the only author of the camera transform |
| `js/navigation.js` | 304 | compass + overview map sampled from the heightfield |
| `js/hud.js` / `js/popup.js` | 496 / 556 | settings/tabs; the provenance card |
| `js/controls/` | 557 | intent contract + pointer-lock and touch backends |
| `js/changelog.js` | 638 | the fleet-parsed release feed (contract path — see AGENTS) |
| evidence UI (`liberties/ground/exclusions/citations`) | ~800 | the Evidence panel, all data-driven |

Portable nearly verbatim to any web track: `scene-loader`, the ENU/heightfield layer of
`terrain.js`, the solar math in `world.js`, `walker.js`, `controls/`, `units.js`. Engine-
coupled (the rewrite surface): materials/batching, the vegetation shaders, sky, and every
`onBeforeCompile` patch.

## Appendix B — measurement recipes

All captures: `window.__chicago4d` → `goTo(anchor)`, `setAnimationHold(true)`, `capture()`,
at 1280×800 and 390×780, pitch printed and matched to the reference (the sweep's
correction). Every number quotes its anchor and viewport.

- **Depth-band high-pass RMS**: locate the land/sky boundary per column; take three bands
  downward from it; 5×5 high-pass; RMS per band. Collapse toward the far band is the tell.
- **Horizon timber coverage**: per column, detect a break in the sky's own extrapolated
  gradient within the band above the land/sky boundary; report % of columns overall and
  across the central two-thirds. **Measured on a second capture of the same pose with the
  town's `structures` group hidden** — a gable end breaks a skyline exactly as an oak does,
  and no property of one frame separates them (R-W4a measured the proposed G−B
  discriminator: gables +22.4, hazed timber +0.1..+17.5, complete overlap; and L17's total
  extinction by 1500 m converges both on the fog colour by design). The visitor's frame is
  still reported, as **skyline-break** coverage, which is not a timber figure and is never
  what this row is quoting.
- **Crown fine-detail ratio**: ratio of fine-scale (high-frequency) to coarse-scale energy
  over crown-masked pixels at 20–60 m; reference 0.61–0.64.
- **Color checks**: sunlit-crown G−B; shadowed-region darkest-decile L in Lab.
- **Flower load**: fraction of vegetated pixels the flower heads actually paint, measured on a
  third capture of the same pose with the nine `flora-head-*` sets hidden — `flower.bloom`,
  and **never `flower.load`**, whose hue cut at 50° classifies a yellow coneflower as the grass
  it is being compared against and missed 94.5 % of the bloom at `prairie_west` (R-W4c(a); the
  argument and the per-station numbers are in `critic_metrics.mjs` and ROADMAP). Target 4–6 %,
  **carried forward but not yet on the same scale as `bloom`**: it was derived by running the
  blind recipe on the reference photographs, and a photograph has no second frame to subtract.
  Re-deriving it is R-W4c(b)'s first job.
- **White-card exposure**: a known-albedo card placed at a fixed anchor; assert the rendered
  sRGB value in band; assert the log-wall R/B ratio ≈ its base-colour ratio (1.75).
- **Placement parity** (multi-renderer): same anchors, both renderers, structure-silhouette
  IoU within tolerance; any drift is a contract bug, not a style difference.
- **Rubric passes**: the §0/G0 protocol — independent critic, eight axes, five anchors,
  written justification, fix per axis below 8, four-iteration cap, regression gate.
