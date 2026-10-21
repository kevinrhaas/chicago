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
`site/4d/walk-hd/`, the Joliet precedent). **Recommended engine: three.js
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

The chooser is `site/4d/index.html`. Today `tools/publish.sh` writes it only if
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
  *Landed differently as T-2555 (2026-10-16): `js/frame-governor.js` scales the ratio
  continuously between 0.67× and 1× of the visitor's Sharpness (the setting is the
  ceiling, never walked past), only while the camera moves, paces to a steady 30 where
  60 cannot hold at the floor, and halves the shadow refresh on `light` while moving.
  At rest it is neutral, so still frames and captures are unchanged; Settings → Frame
  pacing → Fixed turns it off. `tools/test_frame_governor.mjs` (in check.sh) and
  `measure_walk_frames.mjs --live --stills` are its gates. The measured fall in moving
  frame-time sd and p95 is T-2722, waiting on where it is read: this runner's frames come
  about a second apart on SwiftShader AND on Mesa's llvmpipe (`--gl llvmpipe`, weighed as
  a stand-in by T-2721 and rejected), far outside the range the governor acts in. T-2721
  also found that most of a live frame here is the gaze target's synchronous one-pixel
  pick (`readPixels`, 63 of 72 s of moves). T-2723 took it off the frame: on a computer the
  look now reads its pixel back behind a fence (`gpuPickAsync`), and a phone has drawn no
  look at all since T-2827 (`docs/measurements/t-2723-live-*.json`).*
  *Read on the owner's phone, 2026-10-19 (T-2733): **T-2592 is read, NOT MET.** With
  T-2732's Settings → Performance → Read frame pacing, on an iPhone at `/4d/dev/1835/`,
  Light, one 5 s sample a mode (~160 draws): Adaptive lowered both sd and p95 for the
  **walk** only (sd 6.0 → 5.0 ms, p95 43 → 41, frames over 50 ms 3 → 0); the **turn** rose
  (sd 4.7 → 6.5, p95 37 → 41, max 44 → 73 ms) and so did the **flight** (sd 3.9 → 5.0, p95
  38 → 41). The phone does not hold 60 at Light even on Fixed (medians 27–31 ms), so
  Adaptive is pacing to 30 there, and on turns the pacing made frames less even, not more.
  Adaptive stays the default for now; why it worsens turns, and whether Fixed should be
  the default until it does not, is T-2829 (a decision for the owner if the default is to
  change). The reading, verbatim, is `docs/measurements/t-2733-owner-phone-1835.txt`, its
  rows as JSON beside it. The readout now prints the scene, the Sharpness stop and the
  ratio each drive drew at, defaults to 15 s a mode, and walks each scene's own poses
  (in 1904, south along Prairie Avenue's east walk — the first 1904 attempt walked due
  west into the Glessner front, T-2828); `tools/test_pacing_read.mjs` holds every pose
  clear of its scene's footprints. The 1904 reading is T-2719.*
  *Why the turn rose (T-2829, 2026-10-19): the phone draws on a 120 Hz grid. Its Fixed turn
  fits a 25 ms third-vsync rung, and no 60 Hz fit comes close. At that build, Adaptive
  stepped the scale three times (three drawing-buffer resizes that bought nothing, because
  the frame is not fill-bound at Low) and then paced the turn to 30, holding 25 ms frames
  back to 33 ms (median 27 → 32). The governor no longer paces a window whose median lies
  between 21 ms and the paced interval: a rate of the device's own, which a 60 Hz display
  cannot have, so T-2555's 60/30 case is unchanged. A pace now takes three windows in a row,
  and the ladder stops at the first step that does not lower the p80. In a model fed his Fixed rows
  (`tools/model_governor_phone.mjs`, a model and not a reading), the Adaptive turn now reads
  no worse than Fixed in sd and p95. Read frame pacing also prints each row's ratio switches,
  the >50 ms draws that came on one, and the paced share. Adaptive stays the default; his
  15 s repeat on this build is the acceptance. `docs/measurements/T-2829-pacing-model.md`.*
  *Read on the owner's phone in 1904, 2026-10-20 (T-2719, T-2598's last reading): Prairie
  Avenue's moving p95 at Light is **50 ms Fixed / 48 ms Adaptive** (median 43 / 40 ms, about
  23-25 fps; 345 of 346 Fixed walk draws over 33 ms), so the phone does not hold 30 walking
  1904. The tab did not die (T-2828's fix holds). By T-2592's rule no move
  fell: Adaptive lowered every median (walk 43 → 40, turn 32 → 26, flight 80 → 73) and drew
  more frames in each move, but raised sd in all three and flight's p95 (85 → 90). It
  stepped the ratio one to three times a move, and two of the >50 ms draws came on a switch
  in walk and in flight, so a resize can be a hitch on this phone (the question T-2829 left
  open). **Flight is the cost**: median 73-80 ms, every draw over 50 ms, which is T-2927.
  T-2829's acceptance is still its 1835 repeat. `docs/measurements/t-2719-owner-phone-1904.txt`
  and `.json`.*
  *T-2970, 2026-10-20: **the draw budgets count the driver's draws.** `stats().drawCalls`
  was three's `renderer.info.render.calls`, which takes a BatchedMesh's multi-draw as one
  call where the driver receives one draw per kept instance — 360 against 3,288 at the
  1904 flight after T-2927's coalescing. It is now that count plus each multi-draw's
  entries past the first (`renderers/web/js/driver-draws.js`), audited draw for draw by
  `tools/measure_pose_draws.mjs`; `rendererCalls` keeps three's figure. Re-based on it at
  the six stands: `BUDGET` 330 → 7,800 (worst 7,358, full, the aerial, 1280x800), light's
  floor 90 → 5,900 (worst 5,541, West prairie), Glessner's Full-inspection 360 retired
  (worst 4,609 under the town's ceiling). A change of unit, not a raise: these are what the
  town draws today, the ratchet the batching work is read against. Read frame pacing and
  `measure_walk_frames.mjs` print the driver's draws a frame. `docs/measurements/T-2970-driver-draws.json`.
  The counter never enables `WEBGL_multi_draw` itself: it wraps the extension when three
  first asks the context for it (at its first BatchedMesh). Asking for it at boot, with
  nothing wrapped, put one 52-57 ms flora pass on the first walk after a tier change and
  turned the moving-frames gate red at balanced and light; left to three, both read under
  9 ms again and the page meter still agrees with the GL (3,387 = 3,387, 1904 flight).*

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
  committed to `site/4d/walk-hd/`** (the deploy workflow stays build-free, the
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
   `site/4d/` (workflow files included) goes through an interactive, owner-visible
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
accounting; its built bundle is committed under `site/4d/walk-hd/`; `walk/` must
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

### H0 — kill criteria, written before the spike (T-2558, 2026-10-16)

The owner opened H0 on 2026-10-16 (T-2558, answer (a): once T-2546's memory meter had
landed, which it had). These criteria were committed to this section before any spike
code was written, and the memo below answers them one by one without moving them.

**The scene.** "The Glessner block" is every 1904 structure whose placement lies within
60 m of `glessner_house`'s: 12 structures, Glessner House at its `light` level as a phone
boots it. All 12 are meshopt + `KHR_mesh_quantization`; three (Keith, Wheeler, Glessner's
maps) carry `KHR_texture_basisu`. *(Corrected after the reading, the definition unchanged:
the 60 m radius holds **11** structures, not 12, a miscount in this description; and the
KTX2 maps are Keith's and Wheeler's only, 27 of them, while Glessner's light level ships
46 image maps. No bar below depended on either number.)* They stand on the 1904 heightfield (`e1871_postfire`)
under the NOAA sun at the scene's own 10:30 local mean time on 1904-07-01, read from the
SAME published GLBs and sidecars walk/ reads.

**Three pages draw that identical block** (`renderers/web-hd/`):

- **HD-GPU** — three's `WebGPURenderer` on a WebGPU adapter, the confidence view as a TSL
  node composed onto every material;
- **HD-GL** — the same page and the same code on `WebGPURenderer`'s automatic WebGL2
  fallback, on a browser that offers no WebGPU adapter (no flag forces it);
- **CLASSIC** — three's `WebGLRenderer` with walk/'s own `confidence.js` patch: walk/'s
  engine on the same block. walk/ itself has no block-only mode, and a whole-1904 reading
  would flatter the spike by everything else the town holds.

Viewports: the phone profile (390×780, ratio 1) and desktop (1280×800).

| # | criterion | bar |
|---|---|---|
| K1 | boots | HD-GPU and HD-GL reach ready at both viewports, zero page errors, zero console errors |
| K2 | assets | every block GLB loads in both HD backends: meshopt, quantized positions and KTX2 (transcoded, not dropped) |
| K3 | confidence node | captures with the view ON, from the same camera: HD vs CLASSIC mean abs. difference ≤ 6/255 and ≤ 4 % of pixels with a channel off by more than 40/255 |
| K4 | capture parity | the same test with the view OFF |
| K5 | memory | phone-profile resident estimate (JS heap after GC + ArrayBuffer backing + GPU buffer bytes + GPU texture bytes, each counted at the API the backend calls) of HD-GPU ≤ CLASSIC's |
| K6 | moving frame time | p95 of the frame interval over a scripted dolly at the phone profile: ≤ 1.0× CLASSIC is a go, 1.0-1.5× a go with conditions, > 1.5× a no-go |
| K7 | fallback | HD-GL is K1 on a browser with no WebGPU at all — boots with no code path of its own |

**Decision rule.** GO for H1 if K1-K5 and K7 pass and K6 is under 1.5×. A failure of K1,
K2 or K3 means the engine cannot carry the data contract, and the recommendation flips to
Babylon (§3's named fallback). Any other failure is named in the memo with what it costs.

**What H0 does not gate, and why.** §4's H0 also named "TRAA stable under free-camera
motion". This spike does not vendor three's TSL display addons, and a post chain is a
second demonstration; TRAA is therefore moved to H1's entry: H1 does not start until a
TRAA reading under motion is taken. **Frame time on the steward runner is software**
(SwiftShader rasterises all three pages, measured in T-2592's finding), so K6 is answered
on that stand-in and re-read on hardware before anything ships. And §4's "delete the spike
in the same PR" is not followed: the ticket placed the spike in `renderers/web-hd/`, and it
stays as the instrument that reproduces the memo. It is not published.

### H0 — the bake-off memo (T-2558, 2026-10-16)

**Verdict: NO-GO for H1 as measured, on K5 alone — and not a flip to Babylon.** K1, K2, K3,
K4, K6 and K7 pass; WebGPURenderer + TSL carried the data contract (every GLB, the
confidence view, the fallback). K5 fails by 46 MiB at the phone profile. Two allocations
WebGPU makes and walk/ does not (33 MiB, named below) and a 40 MiB shortfall in the WebGL
meter's reading of the baseline account for all of it. The next step is to re-read K5 with
both settled, not H1 and not the fallback engine.

Reading: `node tools/measure_hd_spike.mjs --dir <d>` (six runs, one per page × viewport,
each under the 600 s ceiling), then `--evaluate <d>`; the record is
`docs/measurements/t-2558-h0-bakeoff.json`. Steward runner, headless Chromium,
**SwiftShader on every page**: milliseconds are software, read as ratios only.

| # | answer | the numbers |
|---|---|---|
| K1 | **PASS** | all six runs ready, zero page errors, zero console errors. Boot to ready: phone HD-GPU 3.4 s, HD-GL 2.6 s, CLASSIC 3.2 s; desktop 5.1 / 3.4 / 3.9 s |
| K2 | **PASS** | 11 of 11 structures in every run: meshopt, quantized positions, 27 KTX2 maps transcoded (ETC2/ASTC on WebGPU, BPTC on WebGL; none dropped to RGBA) |
| K3 | **PASS** | view ON, against CLASSIC: mean 3.7-5.7/255, at most 0.85 % of pixels over 40/255 (bar 6/255 and 4 %), both HD backends, both stands, both viewports |
| K4 | **PASS** | view OFF: mean 2.1-5.0/255, at most 0.21 % over 40/255 |
| K5 | **FAIL** | phone, every block texture resident: HD-GPU **494.0 MiB**, HD-GL 490.8, CLASSIC **447.7** (+46.3 MiB, +10.3 %). Desktop 543.9 / 540.6 / 490.7 |
| K6 | **PASS, go** | phone dolly at 4× CPU throttle, frame-interval p95: HD-GPU 1,467 ms, CLASSIC 4,683 ms (**0.31×**); HD-GL 3,150 ms (0.67×). Each frame waited to completion, p95: 1,481 / 1,740 / 2,463 ms (0.60× / 0.71×) |
| K7 | **PASS** | HD-GL ran on a browser offering no adapter; `WebGPURenderer` chose WebGL2 by itself on both viewports, no code of the page's own |

**Where K5's 46 MiB is.** Textures are +65.7 MiB on HD-GPU (424.8 against 359.1); the JS
heap, ArrayBuffers and vertex buffers are 3.6 MiB *lighter* there. Of the texture gap:

- **16.0 MiB — a 2048² RGBA8 colour attachment beside the shadow map.** WebGPU's shadow
  pass holds it; walk/'s WebGL shadow holds a depth map only. Price or drop it in H1.
- **17.0 MiB — the output pipeline at 390×780:** a 4× MSAA RGBA16F target (9.3), its MSAA
  depth (4.6) and a mipped half-float resolve (3.1). three's WebGPU pipeline draws into a
  half-float target before tone mapping. WebGL draws into the canvas's own buffer, which no
  meter sees, so part of this is an ACCOUNTING asymmetry and part is real: the half-float
  target is twice an RGBA8 one.
- **39.5 MiB — unexplained, and on the baseline's side.** All 46 image maps are mip-filtered
  on both pages, at the same sizes (max 2048, nothing resized: both renderers report an
  8192 limit). The WebGPU meter reads them at exactly what three's arithmetic gives (354.7
  MiB against 354.6). The GL meter (measure_memory.mjs's own, read out of that file so the
  tools cannot drift) reads CLASSIC's whole texture total at 359.1 MiB, 39.5 MiB less than
  those images plus the 28.0 MiB of BPTC and the 16 MiB shadow depth that three's arithmetic
  says WebGL was asked for. So either WebGL
  holds less than three asked for, or the GL meter misses an upload path. That is a
  question about the instrument walk/'s ceilings stand on as well, and it is filed as one.
  **Answered by T-2720, below: WebGL holds less, and the meter is right.**

**T-2720 (2026-10-17): the 39.5 MiB is not the meter's, and two lines above are wrong.**
`node tools/audit_gl_meter.mjs` boots CLASSIC with the meter and a second wrapper that logs
every allocating WebGL call, and reads three's own `properties` for the GL texture each block
`Texture` got. Re-read on the H0 build itself (a worktree of `ee49582f6`, published), phone and
desktop, and on today's `dev`: **the meter equals the calls' own sum to the byte** on all four,
once an 8-byte overcount was fixed (three passes `log2(1254) + 1 = 11.29` levels to
`texStorage2D`, WebGL truncates a GLsizei to 11, the meter counted 12). Record:
`docs/measurements/t-2720-gl-meter.json`. What the arithmetic got wrong:

- **It counted Texture objects; WebGL holds image Sources.** three's WebGLRenderer keys a GL
  texture on (Source, sampling state). 11 of the block's 46 image maps share 2 Sources —
  `granite_photographic_basecolor` 1254² ×5 and `granite_stone_occlusion_light` 1024² ×6 — so
  WebGL uploads 37: **58.66 MiB** three's arithmetic counted and WebGL never holds.
- **The shadow colour attachment is on BOTH pages.** r185's WebGLShadowMap gives the shadow
  render target a 2048² RGBA8 colour texture beside its depth texture (16 + 16 MiB, both
  bound to the shadow framebuffer). The 16.0 MiB bullet above calls it WebGPU's alone; it is
  not, and it is not part of K5's gap.
- **WebGL does not draw into the canvas's own buffer here.** CLASSIC renders through a 4× MSAA
  RGBA16F renderbuffer (9.28 MiB), its MSAA depth and a depth (5.80) and a mipped half-float
  resolve texture (3.09): 18.18 MiB the meter reads, in the renderbuffer column, which the
  texture-only comparison above left out.

So CLASSIC's 359.09 MiB of textures is 295.99 (37 image maps) + 28.00 (BPTC) + 16 (shadow
colour) + 16 (shadow depth) + 3.09 (resolve) + under 0.01 (1×1 and 16×16 defaults). Re-read
with `measure_hd_spike.mjs` on the same build (HD-GPU 493.64, CLASSIC 447.30), **K5's +46.34
MiB is +58.65 (the 9 shared maps, which WebGPURenderer uploads once per Texture: 46 RGBA8
textures against WebGL's 37) − 10.33 (KTX2 to ETC2/ASTC against BPTC) + 2.32 (the output
pipeline and canvas depth, 20.50 against 18.18) − 4.29 (JS heap, ArrayBuffers, vertex
buffers)**. By that arithmetic alone, and not measured: if HD-GPU shared Sources as
WebGLRenderer does, K5 would read about 12.3 MiB in its favour. The verdict above stands as
measured; re-reading it is the H track's, which waits on the owner.
`tools/memory_ceilings.json` does not move: walk/'s ceilings stand on a meter that reads
what WebGL was asked for.
- **−10.4 MiB in HD-GPU's favour:** the KTX2 maps transcode to ETC2 RGB / ASTC there
  (17.6 MiB measured), against BPTC at a byte a texel on WebGL (28.0 MiB by arithmetic).
  The remaining +3.5 MiB is small targets and the canvas depth.

**What else the spike found, for H1.**

1. **The TSL node is the improvement §3 promised.** About sixty lines of nodes, no string
   patch against chunk names, and the same pixels as walk/'s patch (K3). It also dithers
   the SHADOWS by itself: the shadow pass runs the material's `colorNode`, so a dithered
   wall casts a dithered shadow with no second material, where walk/ carries a separately
   patched `MeshDepthMaterial` (and the baseline had to be given one to match it).
2. **A flat `scene.background` is tone-mapped by WebGPURenderer** and not by WebGLRenderer.
   walk/ already draws its sky as an untone-mapped dome (`world.js`); walk-hd must too. The
   spike does.
3. **On this runner a WebGPU canvas presents only with `--use-angle=swiftshader`**, and
   `--enable-features` must name `CDPScreenshotNewSurface` again because it replaces
   Playwright's list. Without both, the device is up but nothing presents, and seconds later
   it is lost ("Instance dropped in popErrorScope"). The meter's header records the flags.
4. **The main-thread render call is not cheaper here**: p50 40.0 ms HD-GPU against 31.7 ms
   CLASSIC at the throttled phone, 12.5 against 14.0 ms on desktop. §3's "lower CPU cost per
   draw" is not shown on 134 meshes; it is a claim for batching and render bundles, which
   H0 did not build.

**Not answered here, and why.** TRAA under motion (moved to H1's entry, see the criteria
above). Any frame time on a real GPU: K6's ratio is SwiftShader's, and the moving reading on
hardware stays with T-2722 (T-2592's reading, split).

**What would change the verdict.** K5 re-read with the shadow attachment and the half-float
output target priced or dropped, and the GL meter's 39.5 MiB shortfall explained (T-2720
explained it, above, and moved the first two onto texture sharing). The meter
question is written onto T-2602, which re-reads the 1904 ceilings on that same meter; the
WebGPU half is the H track's next step and waits on the owner, as every H phase does (the
queue was over its ceiling, so no new line was filed for it). If HD-GPU then reads at or
under CLASSIC, H0 is a GO. If it still reads over, the excess is H1's to justify against the
phone ceilings in `tools/memory_ceilings.json`.

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
- **Flora walk parity, shader against CPU** (T-2697, the first piece of T-2557's GPU near
  grass): `node tools/check_flora_gpu_lattice.mjs --gpu [--write]` compiles
  `renderers/web/js/flora-gpu-lattice.js` — flora.js's lattice walk as GLSL, one slot per
  instance id — into a transform-feedback program in Chromium and reads every slot back
  against `jobs/lattice-kernel.js` (held bit-equal to `scatter` by
  `check_lattice_kernel.mjs`): the slots kept and their order, cell seed and stream to the
  bit, position within 1 mm, deal rank within 2^-20. First reading, SwiftShader on the
  runner: 308 walks (every layer's lattice at all 18 of the 1835 anchors, and 200 random),
  373,710 slots, no disagreement; position within 0.042 mm, rank within 1.6e-7
  (`docs/measurements/t-2697-flora-gpu-lattice.json`). The bare command, in `check.sh`,
  holds the shader's walk constants to flora.js's without a browser. Not applied in the
  shader: the view cone, which is a CPU economy; the GPU's own frustum clip replaces it.
- **Near deal parity, shader against flora.js** (T-2706, the first piece of T-2699 under
  T-2557's GPU near grass): `node tools/measure_flora_gpu_deal.mjs [--viewport mobile|desktop]
  [--write] [--self-test]` draws `renderers/web/js/flora-gpu-deal.js` — the near slot's rule
  as GLSL (community, turf, the matrix share and the weight walk, floors, the trodden verge,
  water substrates, the woody band, the walker's clearance, and placeGraminoid's seven
  draws) — on top of T-2697's walk and T-2698's tile, one point per instance id, and reads
  every slot back against flora.js's own `dealNearSlot` (the function the draw calls, via
  `nearField.deal`) at all 22 critic stations. A differing slot is binned `field` (the tile
  answers differently from the CPU there), `float32` (a threshold within an ulp) or `rule`,
  and any `rule` fails the run. First reading, SwiftShader on the runner: 10,648 phone
  slots (`light`) and 29,190 desktop slots (`full`), **0 rule and 0 float32
  disagreements**; the tile's 0.77 % and 0.55 % are the whole difference. Plants per m²
  1.2233 against 1.2253 (phone) and 1.2314 against 1.2309 (desktop), every species' share
  within 1 sigma of the CPU's; instance attributes within 0.03 mm and colour within 3e-5.
  **Exclusion hits are not zero**: 31 and 46 GPU tufts stand where the CPU says BLOCKED, all
  at the wharf, the river bank and the market's edge, which is the tile's BLOCKED miss
  (T-2698: `working-bank.js`'s per-point hash) — T-2708 has to close it before it draws
  (`docs/measurements/t-2706-flora-gpu-deal.json`). `--self-test` swaps the tint's two draws
  and must be refused (265 rule disagreements at sixteenth_prairie).
- **The tile's BLOCKED, slot for slot** (T-2715, the first piece of T-2708): T-2706's
  31 phone and 46 desktop exclusion hits are **0 / 0** at all 22 critic stations
  (`node tools/measure_flora_gpu_deal.mjs --write`, `remeasured: ["T-2715"]` in
  `docs/measurements/t-2706-flora-gpu-deal.json`). Two misses made them. (1) The worked
  bank's bare patches were a per-point sin-hash (`working-bank.js` `blocksGrowth`) no
  raster can hold, and the wharf's 23-33 hits were all it. It now answers once per
  `BANK_PATCH_M` square, the field tile's own 0.125 m world-aligned texel: wet test, wear,
  apron and grass patch at the square's centre, the draw an integer hash of its index. The
  bare share is the same draw against the same weight. (2) A street track edge through a
  texel whose centre it misses (river_bank's last tuft). `nearField.atTexel` and the
  keeper's strips ask the page's `growthEdges` (the track, which is always wider than a
  texel's diagonal) at the texel's four corners, so the tile errs only toward exclusion,
  and `growthPatch` (the yards, the ground strip and the bank) at the centre. Corners
  alone are not enough for everything: Fort Dearborn's fences are thinner than a texel,
  and moving them to corners left 6 kept texels unlike the built tile. Tile-against-CPU
  disagreement at the slots fell from 0.77 % / 0.55 % to 0.27 % / 0.26 %. Plants per m² are
  1.2212 against the CPU's 1.2260 (phone) and 1.2307 against 1.2337 (desktop), both 0.17
  sigma under, which is the edge texels the tile now clears; every species' share is within
  0.65 sigma. The cost, from a same-session before and after with `measure_near_field.mjs
  --walk`: the pool-kept tile's main thread holds at 0.59 -> 0.63 ms a metre on the phone
  (worst step 29.5 -> 31.1 ms; 0.98 desktop). Asking the track at both the centre and the
  corners had cost 1.07 ms a metre and a 54.5 ms step, so the centre no longer asks it.
  The whole tile built on the page (`nearField.build`, used by the tools and nothing in the
  frame) asks the corners unshared: 10.0 -> 15.8 ms a metre. 0 kept texels differ from the
  built tile on either viewport (`docs/measurements/t-2707-near-field-keeper.json`).
- **The near ring drawn from the shader** (T-2716, the second piece of T-2708): the page
  draws the near tufts from `renderers/web/js/flora-gpu-near.js`. At every near placement
  (the same 0.6 m step and centre the CPU walk lands on) one MRT point pass runs the
  lattice walk, the kept field tile and the deal in GLSL for every slot, and writes each
  placed slot's instance — root, height, spread, arch, yaw, colour, confidence and its OWN
  ring (`slotRing`'s handover, in GLSL) — into four RGBA32F targets; the tuft mesh
  (`flora-near-gpu`, one instance per slot) fetches them by `gl_InstanceID` and a slot the
  deal did not place collapses to a point. Each slot's world point is computed from its
  absolute cell and jitter (`flSlotWorld`, `scatter`'s `(c + fe) * cell`), not the
  camera plus an offset, so a tuft is the same float32 point after every pass — the
  camera-relative sum rounded differently as the walker moved, and the smoke's desktop
  pop-in walk read the re-rounded tufts as plants arriving at full coverage inside their
  ring. The CPU walk is kept for the heads alone: it deals
  into a sink that only counts (the census and `stats.sets` read it), and hangs a head only
  where the tile gives the GPU's deal the same answer (`drawsAt`), so the 0.27 % of slots
  where the tile and the CPU differ carry no head over bare ground. A slot the kept tile
  does not cover is left empty rather than clamped to its edge texel, and the pass re-runs
  when a strip lands; a jump of more than a re-centre step, or `step()`, builds the tile
  whole in the frame (234-275 ms on the runner's phone profile). The GPU draws the whole
  ring, not the view cone. `flora-near` is still in the group for its readers: an
  InstancedMesh never drawn, whose instances are READ BACK from the targets the first time
  its `count` is asked for after a pass, so the smoke's root, ring, cover and head-support
  gates read what the GPU drew. Read at prairie_west on the phone profile: 283 GPU tufts
  against the CPU deal's 283 placed slots at the same centre, all 283 at the same slot;
  roots within 1e-7 m of the tile's ground and 6.2e-5 m of the terrain's; the frame against
  dev's CPU-drawn one differs by more than 8 levels in 0.23 % of pixels. The smoke's root
  gate holds the GPU tufts to the tile's ground at its 1e-5 m and the tile's ground to the
  terrain at 5 mm (T-2698's worst at the 22 stations is 4.8 mm). The near re-deal's
  main-thread ms and the moving p95 are T-2717's reading, below.
- **The GPU near ring's cost while moving** (T-2717, the third piece of T-2708):
  `node tools/measure_walk_frames.mjs --source --only mobile --tiers light` now prints a
  `near re-deal` line under each move: the near passes, each one's main-thread ms (a spread
  pass's from its landing record, a one-frame pass's as its frame's flora ms), and where the
  GPU draws the ring, its deal passes, tile builds and uploads with their ms. Read on the
  phone profile (390x780, 4x CPU throttle) with SwiftShader, the commit before T-2716 against
  T-2716 itself, two interleaved runs each, and dev's tip once
  (`docs/measurements/t-2717-near-redeal-mobile.json`):

  | move | near pass, median ms (before / after) | moving p95, scripted ms (before / after) | flora's worst frame, ms (before / after) |
  |---|---|---|---|
  | walk | 2.9, 2.6 / 2.7, 3.4 | 2.5, 2.3 / 1.9, 2.4 | 6.2, 5.5 / 5.4, 6.3 |
  | turn | 4.0, 4.0 / 4.1, 3.4 | 6.5, 5.8 / 5.5, 6.0 | 6.4, 6.9 / 6.0, 6.4 |
  | flight | no near pass | 5.7, 5.4 / 5.1, 6.2 | 5.6, 5.6 / 5.7, 6.1 |

  **The near re-deal is NOT at zero, and the moving p95 did not move outside the runs'
  noise.** The CPU walk still deals every near slot (`dealNearSlot`, then `placeGraminoid`
  into `nearSink`) because the heads hang off the height it returns: in a CPU profile over
  the three moves those two read 61 + 79 ms before and 84 + 103 ms after. On top of them the
  GPU's deal pass costs the main thread 0.4-0.6 ms a pass (42-65 ms over a walk's ~100
  passes; 77 ms on dev's tip), and the kept tile's strip landings (`near-field.js`, which the
  CPU-drawn ring never ran) about 200 ms over the moves. The flight deals the ring 9 times
  and uploads the tile 8 times with no near pass. What the GPU ring took off the main thread
  is the near tufts' instance writes and their buffer upload, and that is about what it added
  back. Zero needs the CPU near walk retired, with the heads hung from the GPU's deal:
  T-2774, the follow-up that also carries the mid, forb and far-shrub sets. SwiftShader
  draws the pass on the CPU, so on a phone's GPU the deal pass's main-thread share is its
  command encoding and should be smaller; the CPU walk's share is the same code anywhere.
- **The near heads hung from the GPU's deal; the CPU near walk retired** (T-2774, the first
  slice of the follow-up T-2717 named): wherever the GPU draws the near ring, `rebuildGround`
  no longer walks the near lattice at all — no `dealNearSlot`, no `placeGraminoid`. The deal
  pass now writes every slot it deals a WORD in its first target's fourth channel
  (`flora-gpu-near.js` `nearWord`: the `NEAR_DEAL` code, the WET bit and the deal-table row),
  and the page reads three targets back after each placement and REAPS them in slot order
  (`flora.js` `reap`): inside the placement's view cone — the cone the CPU walk was given,
  because the GPU deals the whole ring — it counts the matrix census as `dealNearSlot` did,
  counts the placed tufts into the sink `tally` reads, and offers each placed tuft of a
  flowering species its head through `maybeHead`, off the GPU's height and ring, on the
  slot's own xorshift stream rebuilt from its cell and index and moved past the nine draws
  its jitter and tuft took (`NEAR_STREAM_DRAWS`). The heads are recorded, then appended to
  the head sets after the pass's own forb, shrub and far-band heads (`hangNearHeads`); they
  used to be pushed first, so a set that fills now turns away a near head before a forb's —
  no head set fills at the 18 critic anchors at the phone's `light`.
  On the frame loop the read is NOT waited for: three pixel-pack buffers and a fence, polled
  between frames, and until it lands the sets keep the last placement's near heads, which
  stand where they stood (every slot is world-anchored) and differ only at the lattice's
  edge, past the heads' ring. three's own `readRenderTargetPixelsAsync` was tried first and
  is not used: for a float target it asks `getParameter(IMPLEMENTATION_COLOR_READ_TYPE)`,
  a round trip that waits for the GPU — 1282 ms over 169 reads on the phone profile's walk,
  7.6 ms a read in the frame. A caller that reads the buffers straight after (`step()`, the
  boot, `settle()`, `nearDraw.flush()`) reads in the frame. A strip landing re-deals the
  placement only when the tile it was dealt on did not wholly cover its lattice; T-2717 read
  the flight re-dealing 9 times with no near pass.
  **Equivalence**, every head instance at the 18 anchors x 4 bearings on the phone at `light`
  (dev's tip against this, both through the in-frame read and through the frame loop's
  non-blocking one): 2964 heads against 2964, every one matched to the same kind and the
  same size and spin draws, the worst 0.27 mm apart across and 0.12 mm in height (float32
  against double, and the tile's ground against the terrain's); every other flora set's
  instance buffers, `flora-near`'s read-back included, bit-identical; 3 of 792 matrix census
  rows differ, by at most 2 slots, at `from_above` (the aerial frustum test on float32
  points). **Readings** (`docs/measurements/t-2774-near-heads-mobile.json`): the phone
  profile, `light`, SwiftShader, `--source`, dev's tip against this, interleaved
  (before, after, before, after, after with `--profile 400`, before with it, after once
  more as committed), on a shared four-core machine about three times slower than T-2717's
  runner:

  | | near walk in a CPU profile over the three moves | the near ring's other main-thread ms over the moves | GPU re-deals in the flight |
  |---|---|---|---|
  | before | `rebuildGround` 2275 ms inclusive, of which `dealNearSlot` 708 | deal pass 488 | 9 |
  | after | `rebuildGround` 1053 ms (the mid walk alone); `dealNearSlot` and `drawsAt` gone | deal pass 412, asking the reads 171, collecting and reaping them between frames 153 (less the tally since dropped) | 1 |

  `placeGraminoid` still reads about 300 ms in both: the near CARRY set's (`rebuildCarry`,
  on the far pass), which is not the near ring. The `near re-deal` line, walk / turn median
  main-thread ms of a near pass: 9.9, 9.2, 10.2 before against 9.5, 10.5, 9.1 after (walk),
  and 18.5, 17.5, 16.9 against 8.4, 9.4, 9.1 (turn); the moving p95 of scripted ms did not
  move outside the runs' noise (walk 13.8, 10.7, 13.9 against 10.2, 11.3, 12.6). Asking a
  read costs 0.6 ms of the frame; collecting it, 0.3 ms, and reaping it, 0.1 ms, between
  frames. The pass counts that line takes differ between the trees (turn: 5-7 counted
  before against 35-39 after, with 59 near rebuilds in every run), so its medians are not
  like for like and the CPU profile is the reading this rests on. **The near re-deal is
  still not at zero**: a near pass still walks the mid ring, the forbs and shrubs and the
  far band on the CPU, and those — not the near ring — are now nearly all of it. They are
  the rest of T-2774. SwiftShader runs the deal pass on the CPU, in the GPU process,
  unthrottled, so the ms a phone's GPU spends on it are not read here at all; what is read
  is the main thread's share, which is the same code anywhere, and the read-back's
  collection, which on a real GPU is a copy out of a buffer the GPU has finished with.
- **The near pass's mid cards on the GPU's deal** (T-2894, T-2774's second slice). "Mid"
  here is the near pass's own mid ring, `rebuildGround`'s clump cards (`flora-mid`, 3-13 m
  on the phone, 4.5-27 m at `full`), not T-2783's far-prairie mid band, which is the third
  of `rebuildFar`'s bands and still the CPU's. Wherever the GPU draws the near ring and the
  job pool runs, a near pass no longer walks the mid lattice. A second point pass
  (`flora-gpu-mid.js`) deals every mid slot in GLSL — community, short turf, the matrix
  share and the weight walk off the slot's one draw, `station` — against the MID FIELD, a
  second kept tile on the near tile's 0.125 m texel grid sized to the mid lattice's reach
  (`midFieldSpec`: 368 texels on the phone, 464 balanced, 632 at `full`), and writes each
  slot `(e, tone, -n, word)` with T-2774's word layout. The read-back that hangs the near
  heads takes this target too (a fourth pixel-pack buffer behind the same fence), and
  `reapMid` does in slot order what the walk did per slot: the slot's point recomputed in
  doubles from its cell and index, the lattice ring and the view cone, the FRINGE
  (`fringeOf`), the matrix census, `station`'s first question (the page's
  `growthBlocked`, asked at the slot), the INNER HANDOVER (`slotRing`) and the card
  (`placeCard` on the slot's own stream, rooted by `terrain.surfaceHeight`, with the
  GPU's tone). The fringe stays on the page because its dither hashes `round(e * 64)`,
  which a float32 `e` lands across a rounding half about one slot in two hundred.
  The mid field is kept by the pool alone and holds only the worker's answers
  (`keeper({ page: false })`): the near keeper's main-thread share — the streets' track at
  every texel corner, the yards, ground strip and bank at every centre — read 555 ms of
  the dev profile over the three moves, about what the whole mid walk cost, and a tile
  1.4-2.5 times as wide asked the same way would have cost more than the walk it retires.
  It is never built whole on the main thread: a pass whose lattice the kept mid tile does
  not wholly cover (after a boot, a tier change or a jump, until the pool's tile is home)
  deals the mid ring on the CPU exactly as before, counted as `midCpu`.
  **For T-2895 and T-2896**: the forb ring's lattice is never wider than the mid ring's
  (14.6 against 14.6 m on the phone, 19.7 against 20.2 balanced, 29 against 31 at `full`),
  so the forb, rosette and shrub deal can read this same tile with a deal function and a
  reap of its own beside `reapMid`, on the same word; the forbs' re-seated slots
  (`forbSeat`) and their heads are the page's half there as the fringe is here. The far
  band reaches 40-150 m and needs a coarser field.
  **The instrument first** (its own commit): the `near re-deal` line counted a pass only
  when one landed inside a frame `measure_walk_frames.mjs` drove, but the page's own
  animation loop keeps ticking while the tool holds the clock, in the gaps it yields for the
  workers, and lands the rest — T-2774's 5-7 against 35-39 of 59. flora now logs every pass
  (`stats.spread.log`: number, main-thread ms wherever it was dealt, how it ended) and the
  near passes dropped after their ground was dealt (`droppedDealt`); the line reads its
  passes and medians off the log and holds passes + dropped to the rebuild count (it fails
  the run if they disagree). It also prints the held loop's own `flora.update` calls and ms
  between the driven frames: on the phone profile that is 1.7-3.7 s a move, main-thread
  time no driven frame's row carries, and every earlier reading of this tool's scripted
  columns left it out.
  **Equivalence**, every `flora-mid` card at the 18 anchors x 4 bearings on the phone at
  `light`, a fresh pass at each pose once the mid tile is home, dev against this, read in
  the frame and through the frame loop's collected read-back (the two identical): 4293
  cards against 4295; 4291 at the same slot with the same species and every attribute but
  colour bit-identical (position, root, height, width, arch, ring, confidence; colour within
  6.6e-5, the float32 tone); one slot with another species, one card only on dev, three only
  here — all four where the 0.125 m texel centre's community or turf/water answer differs
  from the slot's own (T-2698's tile class; none from float32 or the rule). Every other flora
  set's instance buffers bit-identical; 8 of 2232 census rows differ, by 1 slot.
  **Readings** (`docs/measurements/t-2894-mid-on-gpu-mobile.json`): the phone profile,
  `light`, SwiftShader, `--source`, the instrument commit against this, interleaved:

  | | near pass, median main-thread ms, walk / turn | moving p95, scripted ms, walk / turn |
  |---|---|---|
  | before | 5.4 / 5.6, 6.0 / 6.5, 6.5 / 6.7 (profiled), 6.0 / 6.2 | 4.9 / 8.2, 5.5 / 9.6, 5.9 / 9.3, 5.2 / 9.0 |
  | after | 5.1 / 4.8, 5.3 / 4.6, 6.6 / 5.4 (profiled), 5.1 / 4.2 | 5.5 / 8.4, 5.5 / 9.1, 5.8 / 10.0, 4.9 / 8.7 |

  The turn's near pass falls by about 1.5 ms; the walk's does not move outside the runs'
  noise, because the walk crosses the town's short turf, where the mid walk returned early
  anyway, and the mid deal pass costs the main thread 0.8-1.2 ms a pass on SwiftShader
  (34-198 ms over a move, its tile uploads included). The moving p95 did not move. In a CPU
  profile over the three moves `rebuildGround` goes from 585 ms to nothing in the top 400
  and `rebuildAll` from 1804 to 1615; added are the mid deal pass (248), `reapMid` (108,
  between frames) and the bigger read-back (collect 90 -> 226 with the reap); the mid
  field's strips add no measurable `land`/`finish` (554/495 -> 578/506, one profile each).
  No pass walked the mid ring on the CPU in any after run (`midCpu` 0; the tile was home
  before every move). **The near re-deal is still not at zero**: what a near pass spends
  now is the forbs, rosettes and shrubs (`rebuildForbs`) and the far band (`rebuildFar`),
  T-2895's and T-2896's, and the two deal passes' command encoding. SwiftShader draws both
  passes on the CPU in the GPU process, so what a phone's GPU spends on them is not read
  here; the main thread's share is.
- **The near pass's forbs, rosettes and shrubs on the GPU's deal** (T-2895, T-2774's third
  slice). `rebuildForbs` walked the forb ring twice per near pass — the forb lattice (salt
  0x2545f9, the sparse `'lattice'` draw: `flora-forb` and the basal rosettes,
  `flora-rosette`) and the shrub stratum's own lattice over the same ring (salt 0x7b5c1d,
  the `'wild'` draw, K54's independent draw: `flora-shrub`), each putting up its plants'
  heads. Wherever the mid ring is the GPU's (T-2894), both walks are now dealt in GLSL
  (`flora-gpu-forb.js`) against the SAME kept mid tile — the forb lattice is never wider
  than the mid lattice — as two more point draws in the mid deal pass's own render: the same
  target (rows after the mid slots, `uSlot0`), the same field textures and uniforms, so no
  tile, upload, render-target bind or read-back of their own. The deal is the community,
  the forb (or shrub) share and the weight walk off the slot's one draw, and the ground's
  half of `station` (a floor, the trodden verge against the species' height, the water
  substrates); `dealTable` carries a forb section for it after the graminoid rows. The
  word is T-2774's. `reapForbs` does the rest in slot order, as the walks did: the point
  recomputed in doubles from cell and index (the shrubs' full-cell jitter included), ring
  and cone, the fringe, the forb and shrub census, and the page's half — **`forbSeat`**
  (T-2086: a kept yard turns the slot out, or re-seats it in the strip beside the lot line,
  where the page asks `station` whole at the new foot, as the walk did; on short turf only
  a re-seated forb stands, T-2122), `growthBlocked`, **the woody band** (T-1056, now
  `woodyRefuses`, asked at `terrain.surfaceHeight` because the texel's float32 height is a
  slope's worth off the slot's and the band is most of what refuses a shrub), the walker's
  clearance, and `placeForb` / `placeShrub` and the heads (`maybeHead`, a forb's several
  inflorescences) on the slot's own stream past the jitter's two draws, with `patchOf` in
  doubles — so a plant the GPU places where the walk did is the same instance to the bit,
  colour included. The forb ring's heads go into recorders hung after the pass's own heads
  with the near ring's (`hangNearHeads`); a pass whose forbs the CPU still walks (the tile
  not home: counted as `midCpu`, which now covers the forbs too) records its heads there
  as well and hands them over when it lands, so the heads always belong to the forbs on
  screen.
  The deal passes' programs are compiled as the rig is built (`renderer.compile`, not
  waited for): the first readings of this slice found the walk's worst near pass at 85-99
  ms against 31-43, the first GPU mid pass after the tier change linking the mid and forb
  programs inside the walk (`getProgramInfoLog` 61 ms self against 10); compiled up front
  it reads 8.
  **Equivalence**, every forb, rosette, shrub and head instance at the 18 anchors x 4
  bearings on the phone at `light`, a fresh one-frame pass at each pose once the mid tile is
  home, `ea35e9f76` (T-2894) against this, read in the frame and through the frame loop's
  collected read-back (the two identical on both trees): 1016 plants against 1015; 1013 at
  the same slot with the same species and **every attribute bit-identical**, colour
  included; three slots
  differ, all at `from_above` (the aerial pose sees furthest) and all T-2698's tile class,
  shown at the slot — the 0.125 m texel centre's community is not the slot's own: (66.60,
  -335.36) stands in the settled town's short turf, where an un-seated forb is refused, and
  its texel in the sedge meadow (a forb only here); (69.50, -328.27) in the riverbank
  timber, texel in the town (a rosette only on T-2894); (49.95, -336.36) in the sedge
  meadow, texel in the town (a forb only on T-2894). The heads differ by those plants'
  (2934 against 2926) and nothing else; 6 of 2232 census rows differ, every one by those
  three slots; every other flora set bit-identical, zero page errors.
  **Readings** (`docs/measurements/t-2895-forbs-on-gpu-mobile.json`): the phone profile,
  `light`, SwiftShader, `--source`, T-2894's head against this, interleaved:

  | | near pass, median main-thread ms, walk / turn | near rebuilds, walk / turn | near ms in all, walk | forb reap, ms a pass | moving p95, scripted ms, walk / turn |
  |---|---|---|---|---|---|
  | before | 5.2 / 5.0, 5.4 / 5.2, 6.1 / 5.3 (profiled), 5.3 / 5.7 | 137-143 / 42-50 | 816, 856, 976, 828 | — | 5.5 / 8.9, 5.4 / 9.4, 6.1 / 9.6, 5.7 / 9.8 |
  | after | 4.5 / 4.1, 4.5 / 4.1, 4.9 / 4.5 (profiled) | 115-122 / 40-44 | 600, 576, 700 | 1.0 | 5.3 / 8.7, 4.8 / 8.9, 5.7 / 9.6 |

  A near pass's own main thread falls by 0.7-1.2 ms on the walk and 0.8-1.6 on the turn, and a
  spread pass lands sooner: 5.2-5.5 frames a pass against 6.7-6.9 on the walk, with half
  the frames waiting on a worker (302-382 against 651-730), because the forb ring's two
  walks no longer go to the pool and back. **But the forb reap costs the main thread about
  what the walk did** — 1.0 ms a pass, between frames (`forbReapMs`, inside the read-back's
  `reapMs`) — because what the GPU now answers (the community, the water, the floors and
  the verge band) the workers already brought home with the walk's slots, while the page
  keeps the costly half: `growthBlocked` (the streets' track, `blocksGrowth`, is the
  largest flora entry in either profile), the fringe, the yards' re-seating and the
  placing itself. Per pass the main thread is a wash: in the CPU profile over the three
  moves `rebuildForbs` (639 ms) is gone and `rebuildAll` falls 1559 -> 1139, against the
  forb reap's 195 and the bigger read-back (`collect` 221 -> 387 with its reaps); the mid
  deal pass, which now draws the forb walks too, 239 -> 276; `rebuildFar` reads 375 -> 588,
  most likely because more passes are dealt in one frame, and a one-frame pass takes the far
  band's walk on the main thread rather than waiting for the pool. What the walk gains is FEWER
  passes: a pass that fits the slice is dealt in one frame and not started early (T-2106's
  pacing), so the walk takes 115-122 near rebuilds against 137-143, and its near ms in all
  falls by a quarter to a third (816-976 -> 576-700). The moving p95 does not move outside
  the runs' noise. No pass walked the forb ring on
  the CPU in any after run (`midCpu` 0). SwiftShader draws the deal passes on the CPU in
  the GPU process, so what a phone's GPU spends on the two extra point draws (about 1150
  points on the phone) is not read here; the main thread's share is. **For T-2896** (the
  far shrubs, the carries and the far band): the same lesson binds harder there. The far
  pass (`rebuildFarShrubs`, 4.7 s inclusive over the three moves, 3.9 s of it the carries,
  `rebuildCarry`) is now where flora's main thread goes, and the far band is the near pass's
  largest remaining walk (`rebuildFar`, 588 ms); moving a deal to the GPU gains only what
  the page then stops asking per slot, and a reap that asks `growthBlocked` and the fringe
  for every dealt slot costs what the walk did.
- **The far pass's carries on the GPU's deal** (T-2896, T-2774's fourth slice, the part of
  it that landed). The far pass (`rebuildFarShrubs`, every 4 m walked or a turn) walked
  three lattices: the far shrubs and T-2035's two carries, `flora-near-carry` and
  `flora-mid-carry` (the near and mid rings' own slots, drawn cheaper past the detailed
  ring's handover, out to 18.6 and 45.6 m on the phone, 35 and 69 m at `full`). The
  T-2895 profile put 3.9 s of the far pass's 4.7 in the carries, and this run's own
  before profile showed where: not the walk but the page answering it — a third to more
  than half of a spread pass's pool slots reached the deal before the workers' zone and
  ground answers for them came home (`63 %` of the walk's, `43-44 %` of the turn's and flight's were
  dealt off the workers' ground), so the page asked its own zone finder (`find`, 1.3 s)
  and `station` (0.9 s, the streets' track most of it) for the rest.
  - **The deal on the GPU** (`flora-gpu-carry.js`). Both carry walks are dealt in GLSL
    at the far pass's start, one point per slot, the near carry's rows then the mid
    carry's, in one render, against the CARRY FIELD: a third kept tile on the mid
    field's 0.125 m texel grid over the mid carry's reach (`midFieldSpec`: 864 texels on
    the phone, 1072 balanced, 1240 at `full`), kept by the pool a strip at a time and
    holding only the workers' answers (`keeper({ page: false })`), like the mid field.
    The deal is the mid deal's matrix questions (community, short turf, the matrix
    share and the weight walk off the slot's one draw) and the ground's half of
    `station` (floor, trodden verge, water substrates), without the woody band and the
    tone. The read-back goes into a pixel-pack buffer behind a fence while the far
    shrubs walk, and the pass's generator waits for it as it waits for a walk on the
    pool (a caller with no budget — the boot, `settle`, a tool's `step()` — reads it in
    the frame; a pass that must land before it is home leaves it to the carries' tail,
    T-2966 below). `reapCarry` then does what the walk did, in slot order, a slice at
    a time: the point in doubles from cell and index, ring and cone, the slot's own
    handover (the detailed ring's `slotRing`, fringe included) and edge (the carry
    fringe), the page's half of `station` — `growthBlocked`, and the woody band at
    `terrain.surfaceHeight` — and `placeGraminoid` / `placeCard` on the slot's own
    stream past the jitter's two draws, the card's tone computed there in doubles. A
    far pass the kept tile does not wholly cover (after a boot, a tier change or a
    jump, until the pool's tile is home) walks the carries on the CPU exactly as
    before, counted (`carryCpu`). The carry program is compiled with the others as the
    rig is built.
  - **The streets' track asked per bin, and by the workers.** `streets.blocksGrowth`
    walked every opened street's box for every slot of every pass; it now asks only the
    streets whose padded box reaches the slot's 16 m bin (a street whose box does not
    hold the point never answered true), by street-verge.js `trackAt`, the same test as
    `nearestOn` without its allocations. The job pool's ground answers carry the same
    test (`GROUND_TRACK`, over the same records with `track_width_m` added), so a slot
    whose worker answer is home asks the page only `growthPatch` (the yards, the ground
    strip, the worked bank); `checkHeldZones` holds the bit to the page's answer
    (`--verify`: 5210 of 39478 points on a track, 0 answered differently). The answer
    is the old one at every point, so no plant moves; it helps every caller — the
    reaps, the one-frame passes, the near keeper's corner lattice, the trees.
  - **Equivalence**, every flora instance set at the 18 anchors x 4 bearings on the
    phone at `light`, a fresh one-frame pass at each pose with the kept tiles home,
    `10751c7e9` (T-2895) against this: 137,791 carry instances
    against 137,783 (70,787 mid-carry cards and 67,004 near-carry tufts on `10751c7e9`);
    137,562 at the same slot with every attribute bit-identical, colour included, and 333
    instance-poses over 136 distinct slots that differ, every one shown at the slot to be
    the tile's own class (T-2698's, at the near and mid tiles' same 0.125 m texel): 104
    where the texel centre's community is not the slot's (93 present on one side only, 11
    another species or the other community's mean colour), 29 where the texel centre's
    water test is not the slot's (the clump rooted at the waterline on one side and on the
    ground on the other), 2 where a floor's edge crosses the texel, and 1 slot standing
    0.2 mm south of its texel's edge, whose float32 position lands in the texel north of
    it, in the lakeshore (`battle_reach_1812`, the same mid-carry card at two bearings).
    Every other flora set — the near, mid, forb, rosette and shrub rings, the far band, the
    far shrubs and the nine head sets — is bit-identical at all 72 poses, colour included,
    and no census row differs (the carries were never counted). Zero page errors. One
    `full`-tier stand (`sixteenth_prairie`, 1280x800, four bearings, where the mid carry
    reaches 69 m): the mid carry's 21,515 cards bit-identical; the near carry 31,438
    against 31,434 tufts, 8 slots differing, 6 at a texel centre in the other community
    and 2 near-carry slots standing on a texel's edge (`e` 1410.75 and 1426.25), whose
    float32 position lands in the neighbouring texel. The far shrubs, the far band and the
    near pass are untouched by this slice and match to the bit there too.
  - **Readings** (`docs/measurements/t-2896-carries-on-gpu-mobile.json`): the phone
    profile, `light`, SwiftShader, `--source`, `10751c7e9` against this, interleaved.
    `measure_walk_frames.mjs` now prints a `far pass` line (its passes off the same log
    as the near line, and the GPU carries' deals, CPU walks, read-backs and reaps):

  | | far pass, median main-thread ms, walk / turn / flight | far passes' ms in all, walk / turn / flight | held loop's `flora.update` ms, walk / turn / flight | near pass median ms, walk / turn | moving p95, scripted ms, walk / turn |
  |---|---|---|---|---|---|
  | before | 31.8 / 40.8 / 35.5, 36.7 / 42.9 / 38.6, 28.4 / 44.5 / 38.4, 39.7 / 51.4 / 42.1 (profiled) | 512 / 2457 / 1196, 557 / 2691 / 1227, 521 / 2849 / 1225, 613 / 3425 / 1452 | 1773 / 2868 / 1854, 2073 / 3007 / 1810, 2184 / 3390 / 2058, 2176 / 3781 / 2336 | 4.8 / 3.9, 5.2 / 3.8, 4.6 / 4.0, 5.4 / 4.5 | 5.5 / 8.3, 5.6 / 9.2, 5.7 / 11.3, 5.9 / 10.3 |
  | after | 13.0 / 25.5 / 15.8, 16.7 / 24.6 / 12.3, 17.6 / 27.2 / 13.8 (profiled) | 253 / 1863 / 847, 266 / 1576 / 524, 288 / 1665 / 468 | 1413 / 2091 / 1666, 1481 / 1840 / 1221, 1550 / 2024 / 1319 | 4.4 / 3.8, 4.5 / 3.2, 5.2 / 4.3 | 4.8 / 9.4, 5.0 / 8.4, 5.4 / 9.6 |

  (Three earlier after runs, before three exact refinements of the reap and the keeper,
  read the same: far pass medians 17.9 / 24.8 / 14.2, 15.4 / 24.3 / 12.6, 15.4 / 28.8 /
  13.5.) A far pass's main thread falls by about half on the walk and the turn and by
  two thirds in the flight, and the far passes of a move by 45-60 % in all; the turn,
  whose far pass re-deals every 0.2 rad, drains far fewer of them in a frame (2-20 of 59
  against 12-27). The page's own loop between the driven frames spends a quarter to a
  third less in `flora.update`. In the CPU profile over the three moves `flora.update`
  goes 7302 -> 4390 ms, `rebuildFarShrubs` 4938 -> 2358 and `rebuildCarry` 4135 -> 1535,
  of which the reap is 1443; the deal passes add 234 (the carry tile's uploads inside
  them, 7-9 a move); the page's zone finder 1491 -> 247, `station` 908 -> 52,
  `blocksGrowth` 880 -> 337 and `scatterOnPool` 5155 -> 846. The moving p95 does not move
  outside the runs' noise; the worst flora frames DID (these readings held medians only),
  which CI's moving-frames gate caught and T-2966 below repairs. No far pass walked the carries on the
  CPU on the walk; the turn and the flight, each starting on a fresh tier rig, walked 0-9
  before the 864-texel tile was home (`carryCpu`).
  **What it costs.** The carry tile's keeper lands its strips on the main thread between
  frames, outside every driven frame and outside `flora.update`: 5-11 ms a re-centre on
  the phone profile, 138-172 ms over a walk with the first landing (the keeper now writes
  a strip a row at a time with typed-array copies, an exact change every keeper takes;
  texel by texel the same walk read 203), and the whole tile once after a tier change or
  a jump, 85-101 ms — one long task, for a tile five times the mid tile's. The reap is now what the far pass
  spends (about 17 ms a turn's pass): the fringe, the handover, `growthBlocked`, the
  woody band and the placing, per placed slot, as the walk spent them.
  **The near re-deal is not at the GPU pass's own cost.** This slice moved the far
  pass, and the near pass's line moves only by what the streets' bins took off it (walk
  4.6-5.4 -> 4.4-5.2 ms median, turn 3.8-4.5 -> 3.2-4.3): its largest remaining walk is
  still the far band (`rebuildFar`, 445-553 ms over the moves, three lattices out to 120
  m on the phone and 175 m at `full`), and the far shrubs (70-140 m) are still the
  far pass's CPU walk. Neither fits a 0.125 m tile — the carry tile is already 1240
  texels a side at `full` — and a coarser texel trades the tile's class of difference
  (one slot in 400 here) for many more; they are T-2896's remainder, with the carry
  tile's whole landing after a jump.
  - **The worst frames: the carries' tail** (T-2966, the slice's own repair after CI's
    moving-frames gate failed it on #1161: flora's worst moving frame 73.3 ms at `full`'s
    turn against a 60 ms ceiling, 48.1 at `balanced`'s turn against 32, 43.6 on `light`'s
    ride against 21, while the medians fell). Read on this machine first, every spike
    was one of two things. (1) A far pass finished in one frame — a spread pass out of
    margin (`advance`, late; a turn drains most of its far passes, `dev`'s too) or a cheap
    pass the animation loop deals whole — took the carries' read-back in that frame and
    reaped every slot of it there: on SwiftShader a read-back taken in the frame waits
    for the deal itself (15-85 ms at `full`), and the reap is 8-25 ms more. (2) The first
    mid deal after a tier change, 48-57 ms at `light` in 3 of 3 walks (9-10 ms at
    `balanced`), because three's first use of a program (`onFirstUse`: link status,
    uniforms) is a question the driver answers only after everything queued ahead of it,
    and with this slice a carry deal was queued ahead of it. So:
    - **A pass that must land never takes the read-back and never reaps.** It is resumed
      with `DRAIN` (`advance` when late; `runPass`'s one-frame pass under a budget); every
      walk takes that as "may not wait", as before, and the carries as "land without
      me": `carryPass` hands the job — its fence still pending, or its reap part-way —
      to the CARRIES' TAIL, which `carryTailStep` runs at the start of each later
      frame, a slice of the frame's budget at a time, polling the same fence and then
      reaping in slot order exactly as the pass would have. The far shrubs land on time;
      the carry sets keep the last whole carries until the tail commits (on this runner
      4-11 frames a tail on average: the read-back's latency, then the reap at the frame's 4 ms slice). A
      tail is never dropped for a newer GPU deal (one target, one pack buffer, one
      `carryBuf`): a pass that starts while a tail holds them waits its turn as for a
      walk on the pool, and one that must land meanwhile leaves its pose as NEXT, dealt
      the moment the tail lands; only a CPU walk, which writes the carry sets itself,
      replaces a tail. A caller with no budget (the boot, `settle`, a tool's `step()`,
      `--verify`'s one-frame pass) still deals, reads and reaps in the frame
      (`farSync`), and `inFlight()` counts a tail. The tail's ms are booked on its own
      far pass's log entry, so the `far pass` line's medians include them.
    - **The deal programs are used once before the first carry deal.** At rig build
      `compileAsync` waits, without blocking, for the near, mid and carry programs to
      link, then takes each one's first use there, between frames, with nothing of ours
      queued; until then the carries are the CPU's (`carryWarm`). The first mid deal
      after a tier change no longer reaches 8 ms in a walking frame (3 of 3 walks).
    - **What it holds.** `measure_walk_frames.mjs --only desktop --verify --gate`, this
      machine, flora's worst moving frame (ms) walk / turn / flight / ride: before the
      repair full 48.1 / 184.9 / 15.5 / 23.5, balanced 11.7 / 58.6 / 11.5 / 11.1, light
      47.3 / 50.4 / 46.6 / 36.0 (7 over the ceilings); after full 12.1 / 45.3 / 4.9 / 13.9,
      balanced 4.1 / 17.6 / 13.5 / 13.8, light 4.1 / 5.9 / 5.8 / 6.6 (PASS); `dev` read
      11.8 / 27.3 / 13.2 / 19.2, 5.5 / 15.4 / 13.0 / 6.2 and 4.7 / 9.0 / 4.4 / 7.3 in one
      run and 7.3 / 37.4 / 19.6 / 34.0, 4.7 / 8.9 / 20.2 / 5.0, 4.1 / 8.6 / 4.7 / 8.5 in
      another (this machine is noisier and slower than the CI runner, which read `dev`'s
      full turn at 19.0). What remains at `full`'s turn is the CPU's own carry walk,
      drained, in the turn's first seconds before the 1240-texel carry tile is home —
      `dev`'s code path. The far pass's median (ms, the tail's included) against `dev`:
      full 11.1 / 23.5 / 6.9 / 22.7 against 24.8 / 27.5 / 8.1 / 24.4, balanced 5.5 / 13.8
      / 4.4 / 14.0 against 13.2 / 14.6 / 4.6 / 14.3, light 3.0 / 7.8 / 3.5 / 3.4 against
      8.5 / 9.5 / 3.6 / 7.8 (the flight and the ride move the carry tile faster than the
      pool keeps it, so they are mostly the CPU's, as before). The phone profile, `light`,
      walk / turn / flight, `--source`: the far pass's median 12.5 / 23.4 / 10.7 against
      `dev`'s 26.8 / 40.0 / 34.3, the worst flora frame 13.0 / 18.8 / 10.2 against 25.5 / 13.8 /
      8.0 (the phone reading is not gated). `--verify`: every far pass the
      moves left landed IS the one-frame pass. Equivalence (the T-2896 dump, 6 anchors x
      4 bearings on the phone at `light`, a fresh one-frame pass at each pose): every
      flora set bit-identical to the slice before this repair (33,666 carry instances,
      every other set, colour included, 0 census rows differ), and against `dev` the
      slice's own class of difference unchanged (33,519 carry instances bit-identical,
      312 instance rows differing, every other set identical).
      `docs/measurements/t-2966-carries-tail.json` holds the readings. The carry
      keeper's whole landing (T-2969) lands between frames, outside `flora.update`, and
      is not what the gate read; it stays T-2969's.
    - **`--verify` deals a pass again on the side the pass took.** CI's moving-frames
      gate read `verify far: the spread pass IS NOT the one-frame pass` once, on the
      first move after `full`'s rig was built, with every frame ceiling met. Read with
      every carry set digested apart and each far pass's side recorded: the move's last
      far pass had walked its carries on the CPU (the 1240-texel carry tile, 4.4 m of
      slack past its 8 m re-centre line, had not landed the re-centre the walker had
      crossed), the re-centre landed before `--verify` ran, and the re-deal dealt them
      on the GPU. The far shrubs matched; the spread pass's carry sets were the CPU walk
      of the same pose dealt in one frame, to the bit (and CI's one-frame digest,
      `51aaca4b`, is this machine's GPU-dealt spread pass at that pose). At the walk's
      last pose the GPU's deal and the CPU's walk differ at 17 of 3,870 carry slots,
      every one a texel centre in another community than its slot — the tile's own
      class above, not the spreading. So each pass books which
      side dealt its GPU rings (`onGpu` on its log entry: the near pass's mid ring, the
      far pass's carries), the re-deal walks them on the CPU
      when the pass did (`flora.dealOnCpu`, which the page never sets), and the line
      names both sides. Nothing the page places changed by that half.
    - **A landed pass's carries are owed until a newer pass lands.** With the re-deal on
      its own side, one full run here read the full turn's last far pass `IS NOT` its
      one-frame pass with both on the GPU, and with `1 replaced by a CPU walk`. That one
      was the page's: the pass had waited on the previous pass's tail, the tail landed in
      the frame's own `carryTailStep`, and the pass, resumed with DRAIN, left its pose as
      NEXT with no tail ahead of it. A NEXT was dealt only as a tail landed, so it never
      was — not by `settle` either — and the turn ended on the far shrubs of one pass and
      the carries of the pass before it (the `replaced` was `--verify`'s own CPU walk
      finding that NEXT still waiting). Reproduced on demand by making the carry tile
      read as not covering at a quarter of the turn's asks (a debug patch to the
      mirror, not shipped): `IS NOT` in a few turns, with the event log showing the
      NEXT left behind a tail already landed. Now a pass that finds the target free on
      DRAIN deals as the tail itself; a NEXT with no tail is dealt by the next frame's
      tail step, and `settle` deals it too; a NEXT the kept tile no longer covers is
      walked on the CPU as the tail (`walkCarry`, counted as `walked by the CPU after
      their pass`, its pass's `onGpu` set false) instead of being dropped; a starting
      pass no longer throws an older NEXT away, since it may yet be dropped — a pass in
      its own carries only defers the NEXT (`carryBusy`), its landing supersedes it
      (`carryOwned`) and dropping it deals it (`carryDropped`); and a CPU walk that has
      to stop a tail keeps that tail's pose as NEXT the same way.
- **A kept tile's whole landing, a band at a time** (T-2969, T-2896's fourth slice). The
  kept field tiles (near-field.js `fieldKeeper`: the near tile, the mid tile, and the carry
  tile T-2966 keeps the same way) land a strip at a time, but the FIRST tile after a boot, a
  tier change or a jump of a tile or more is every texel at once, and its finish (the
  pool's answers copied, and the page's own share asked) and its wrapped write were one
  main-thread task: the carry tile's read 85-101 ms on the phone profile. A whole landing
  now finishes and writes `LAND_BAND_ROWS` (16) rows at a time into a second pair of
  arrays, hands the thread back (`setTimeout`) once a slice has run `LAND.sliceMs` (6 ms;
  a slice ends at the first band past it), and moves the tile to the new arrays only when
  the last band is in — until then `tile` is the old one, untouched, as a strip in flight
  leaves it. Each band reaches `finish` as a rect of its own with its rows of the pool's
  reply. A tile `adopt`ed while a whole one is still landing drops the landing, as a strip
  already did. Strips still land in one task, in place (a quarter of the tile or less).
  **Equivalence**: `tools/check_near_field_keeper.mjs` walks its route three ways — one
  slice a landing (the before), a band a slice, and the page's budget — with the heights
  carried in the pool's reply, so a band read from the wrong rows differs; the kept tile is
  the built one, byte for byte, after every landing in all three, a whole landing takes
  exactly size / 16 slices at a band a slice and one at Infinity, and a tile adopted
  mid-landing is the adopted tile. **Reading** (`tools/measure_tile_landing.mjs`,
  `docs/measurements/t-2969-tile-landing-mobile.json`): the phone profile (390x780, 4x
  throttle), `--source`, the walker set down 600 m away eight times, west and east, the
  before (`LAND.sliceMs = Infinity`, set in the page) and the after interleaved with the
  order flipped each rep so each lands at both places. The mid tile (368 texels a side,
  the one dev keeps from the pool alone; the carry tile is not on dev yet):

  | | slices a whole landing | longest slice, ms |
  |---|---|---|
  | before | 1, 1, 1, 1 | 25.8, 25.2, 10.6, 20.2 |
  | after | 3, 3, 2, 3 | 6.4, 7.0, 8.4, 6.6 |

  At the same budget the carry tile's 85-101 ms becomes about fifteen slices of 6-8 ms. What
  the reading also shows, and this does not touch: the near tile on a jump is not landed
  but BUILT in the frame (`keeper.adopt(nf.build(..))`), 450-520 ms west of Lake at Canal
  and 640-690 east of it, in either mode; and the jump's own longest task is 3.2-4.1 s.
  **The mid pass's first draw, warmed at the build.** Landing the mid tile across frames
  moved it home later after a tier change, and with it the first near pass whose mid ring
  is the GPU's: on `chicago-4d-moving-frames.yml` that pass now fell inside the light walk
  (the first move after balanced) and read 27-46 ms against light's 21 ms ceiling, three
  runs of three. Split on the page (`--tiers balanced,light --moves walk`, which reproduces
  it every time; light alone does not, there is no tier change before it): the pass's
  `setRenderTarget` 0.1 ms, its one draw 36-38 ms, no program built (T-2895's
  `renderer.compile` had built it). The first draw of the pass still pays the rest of its
  first use: the target, the field textures, and the driver's draw state for this tier's
  target and slot buffers. Balanced's reads 4 ms. Light's target is 14 rows to balanced's
  23, and its slot buffers 1,936 to 3,600, so it does not get the cached state. The one-task
  landing had only hidden this by bringing the tile home inside the tool's 300 ms settle.
  So `warmMid` (flora.js) draws the mid deal pass once as the rig is built: one point per
  walk into its own target, off an empty tile at the mid field's size. That cost is now
  paid in the tier change's own build. A real pass draws its slots over that point before
  the target is read back, and `place` sets every draw range. Read on that sequence, the
  light walk's worst frame went from 34.4 and 44.4 ms to 6.6, 9.9 and 6.8 ms. The mid
  ring's deal passes went from 61 ms to 15-17 ms in all (the one-task control's 17). The
  workflow's own command (`--only desktop --verify --gate`) passes, with light walk at 6.6 ms.
