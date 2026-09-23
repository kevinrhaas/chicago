# 4D Chicago — Walkable Downtown Chicago, First Scene: Summer 1835

## Context

Kevin wants a historically-grounded, walkable 3D reconstruction of downtown Chicago as it stood in **summer 1835** (target date 1835-07-01) — the territory on the 1833 map clip: the river forks (Wolf Point) east to the lake, Kinzie St south to ~Madison, including Fort Dearborn, the sandbar/river mouth, and the government reservation. Per the uploaded BRIEF.md this is **a research dataset with renderers attached**: the durable artifact is georeferenced structure + land data with per-attribute source provenance; renderers are plural and disposable, three.js first.

Kevin directed that it be architected as a **year-parameterized 4D model of Chicago**: the spine is **the land** — elevation, hydrology, shoreline, later fill/grade-raising — versioned per epoch, with structures carrying existence ranges. 1835 is the first rendered scene; earlier states (1830/1833) and later years slot in without restructuring.

Eight research agents swept the repos and the historical record this session; their reports commit into the repo as research dossiers. What they established:

- **Georeferencing masters** (revises the brief): the Leventhal/BPL **Wright 1834 is open-rights and already published as a GeoTIFF** (+ Allmaps annotation); LOC holds a 6536×9318 px **Hathaway 1834** scan, free to reuse (note its "[1820?]" cataloging error — record, don't silently correct). The Newberry Hathaway surrogate is a 1.9 MB JPEG — insufficient. The **J. Wooley-corrected Wabansia plat (approved June 17, 1835 — two weeks from target date)** is the north-side authority.
- **Terrain fully specced** (30 tagged zones): ~15 ft total natural relief; lakeshore sand ridge +9–10 ft above lake along the Michigan Ave line dropping to a **+2–3 ft wet plain west of State St**; Fort Dearborn on a flattened mound (+10–12 ft); the sandbar-deflected old channel decaying behind the spit while the 1833–34 cut + piers (north pier ~800–1,000 ft by July 1835, interpolated) carry traffic; the slough from the public-square pond past Lake & Dearborn to the river at State St; Frog Pond at Lake & LaSalle; soils 1 ft black loam / 3–4 ft quicksand / blue clay (why nothing drained).
- **Structure inventory**: ~45 attested structures with locations, dates, materials, occupants, per-claim confidence — plus a consolidated **EXCLUDE list** (Saloon Building 1836, City Hotel 1836-37, Clarke House 1836, New York House, finished Lake House, Peck brick house 1837…) codifying the brief's date-drift guard. Sauganash: white two-story + bright-blue shutters **documented** (Wau-Bun); dimensions **unattested**; porch/gallery **disputed** across retrospective images — the model carries that honestly.
- **Flora render-ready**: 10 zones, species tables with July densities/heights and **phenology rules** (big bluestem vegetative in July — no turkey-foot heads; ramps leafless; cordgrass is the tall flowering element; the "Dense Forest" NE of the forks is actually a swampy timber thicket mosaic with hazel understory, not closed monumental forest).
- **Fauna** (Kevin's addition — dossier complete): a 7-zone placement table with per-species July-1835 presence, behavior, and visible/audio/prop presentation codes. Documented heroes: **pigs at large** (the 1833 ordinance was a dead letter — Latrobe records wolves eating settlers' pigs), **coyotes ("prairie wolves") visible and howling in daylight within sight of Water Street** (Andreas p. 433), muskrat + ducks at the public-square pond, the **Frog Pond chorus** (documented for early July, one year later, at Lake & LaSalle — the same corner where Hubbard packed 5,000 hogs in 1834), fireflies and prairie/dog-day cicadas as the July dusk/soundscape heroes, "Rat Castle" rats at the Wolf Tavern, cattle drives approaching **from the south** (the Wabash country) to Clybourne's North Branch slaughterhouse. July suppresses spectacle (audio > visible animation): no pigeon sky-darkening (that record is Sept 1836), no prairie-chicken booming, ducks in flightless eclipse moult. Hard anachronism guards: no ring-billed gull flocks (post-1916), no house sparrow/starling, no beaver at the forks, no bison/elk/bear/cougar, no commercial barrel fishery, no winter packing scenes, no wolf-bounty scene (first regional bounties 1838), and the great Potawatomi encampment/war dance is **August** 1835 — weeks after target date. Wolf Point's name is itself flagged: Wau-Bun attributes it to an Indian resident named Moa-way, "the Wolf" — the wolves-gathering story is contested.
- **Fleet conventions**: adopt now — changelog contract, Chromium smoke (390×780 + 1280×800), steward branch discipline, Manager row; defer — promotion pipeline, focus.json lane.

## Decisions locked with Kevin

1. **Home**: `kevinrhaas/custom` → **`chicago/4d/`** (matches the existing 4D schema-spec concept; renameable pre-scaffold), published at `site/chicago/4d/` (walk app at `site/chicago/4d/walk/?year=1835`) via the repo's site/-only Pages pattern.
2. **Temporal model**: `target_date` lives in scene files; terrain versioned per epoch; structures carry phases with ranges.
3. **Generators**: Blender bpy with Kevin's amended split — fast no-Blender `check.sh` per commit; pinned-Blender `bake.sh` on demand + nightly; agents consume committed GLBs; params engine-neutral (contract = glTF + JSON sidecar); authored hero assets allowed, tagged, same provenance rules.
4. **This session after approval**: commit plan + dossiers → scaffold → Milestone 0 start → pre-fire viewer photo/map update.
5. **Brief §10 stands, broadened**: no improvised Native depiction — and **no human figures at all** in v1 (an empty accurate town, uniformly); `review_required` blocks release; Newberry Indigenous Chicago curriculum is the named starting point for any future review path.

## Repository layout (agent-parallel by construction)

```
chicago/4d/
├── AGENTS.md                    1 page: anti-goals, §10 constraint, parcel contract, gate, worktree rule
├── README.md
├── data/
│   ├── datum.json               THE spatial contract: EPSG:26916, Wolf Point origin, verified:false
│   │                            until derived from Wright/Hathaway (generators+bake refuse while false)
│   ├── sources/                 ONE FILE PER SOURCE  — parallel agents never merge-conflict
│   ├── structures/              ONE FILE PER STRUCTURE
│   ├── scenes/1835.json         target_date, terrain_epoch, lighting moment, spawn, anchors, layers
│   ├── terrain/epochs.json      epoch registry (non-overlapping intervals) +
│   │   └── e1834_harbor_cut/    shoreline/river/hydrology GeoJSON + 30-zone heightfield spec
│   ├── flora/{zones/,palettes/} fauna/{species.json,zones/}
│   ├── traces/{allmaps/,gcp/,vectors/}   citable georeferencing artifacts
│   └── exclusions.json          date guards AS DATA with citations (stops re-adding the Saloon Building)
├── generators/
│   ├── blender.pin              version + URL + sha256 (binary tarball pin; bpy wheel = documented fallback)
│   ├── common/                  units, attested→params, confidence_paint (COLOR_0), uv_bake, export
│   ├── archetypes/              *_params.py (pure-Python validation, NO bpy) + *.py (bpy build) pairs:
│   │                            frame_tavern, frame_storefront, frame_dwelling, log_dwelling,
│   │                            institutional, fort_structure, outbuilding, plank_walk,
│   │                            bridge_timber, pier_crib, palisade
│   ├── terrain_gen.py  flora_gen.py  build.py (--all|--only|--stale-only|--dry-run)
├── assets/
│   ├── gltf/                    baked MASTERS (uncompressed glb, committed, regenerable)
│   ├── web/                     meshopt+KTX2 derivatives (what actually publishes)
│   ├── manifest.json            per-asset input-hash + blender version — the staleness contract
│   ├── authored/  textures/  audio/  LICENSES.md
├── renderers/web/               the walkthrough (below)
├── tools/
│   ├── check.sh                 per-commit gate, <10 s, NO Blender
│   ├── validate.py              (ports the shipped validate_structures.py: Report class, attested
│   │                            rules, date gate) + params/licenses/stale/site checks
│   ├── bake.sh  compile_scene.py  publish.sh  smoke.mjs  stamp-changelog.mjs
└── docs/  RESEARCH/ (per-structure dossiers) · research/ (the 8 session reports, verbatim) ·
           PROVENANCE.md · EPOCHS.md · LIBERTIES.md (append-only, joliet pattern) ·
           ROADMAP.md · STATUS.md (honest state)
```

Publish: `site/chicago/4d/` = landing `index.html` + `js/changelog.js` (fleet format, from commit one) + `walk/` (byte-copy of renderers/web) + `data/` (scenes, compiled sidecars, `assets/web` copies, terrain glb + heightfield.bin). `publish.sh` byte-copies; `check.sh` verifies `diff -rq` sync and a **≤25 MB published budget**. Plain binaries, **no LFS** (Pages can't serve LFS objects). Every URL-targeted directory gets an `index.html` (also fixing the existing `site/chicago/pre-fire/` bare-path 404). One new app card on `site/chicago/index.html`.

## Data model (minimal evolution of the shipped schema)

- **Scenes own dates.** `data/scenes/1835.json` carries `target_date`, `terrain_epoch` (validator: epoch interval must cover the date), lighting moment (sun az/el computed from datum lat/lon), spawn + camera anchors (smoke harness reads the same anchors — joliet pattern), and `released: false` while any included structure has `review_required`.
- **Structures = identity + `phases[]`.** Each phase = the old structure body (documented_range, position, footprint, form) + `change_note`. Scene rule shared by validator/compiler/renderer: structure appears iff **exactly one** phase covers the scene date; overlap = hard error; none = excluded (reported). The Sauganash is the test case: `log_1829` (Eagle Exchange, incl. the documented move off the platted street after the 1830 Thompson plat) → `frame_1831` (white 2-story + blue shutters). Legacy single-body records read as an implicit single phase. Per-attribute confidence (`documented` needs sources / `inferred` needs note / `conjectural` surfaced + rendered distinctly) — **unchanged**. `xref` links to `pre_fire_v1` building ids and Conley key numbers.
- **Terrain epochs** are the slow layer (`e1830_natural` planned, `e1834_harbor_cut` active — covering 1833-07→1848); fast-changing works (the growing piers) are **structures** with phases, not terrain.
- **Flora zones**: polygon + community palette ref + per-attribute confidence (extent documented, composition inferred, width conjectural — each stated). **Fauna**: `species.json` (kind wild/domestic, behavior, presence with confidence + source) + zones, seeded directly from the dossier's 7-zone placement table with its presentation codes (A animate / A- occasional / S audio-only / P prop-or-trace); **negative findings stored as `absent` entries with citations** (ring-billed gulls, beaver, bison, periodical cicadas…) so future agents can't innocently re-add them — the fauna twin of `exclusions.json`.
- **Sources** gain `archived_url` (required for web sources — the EOC-503 mitigation) and `rights_status` (`check_required` blocks derived *assets*, e.g. Conley/Stelzer, but not textual citation).
- Internal vertical datum: **Z=0 at the summer-1835 lake surface** (`ASL = Z + 580.0`); horizontal EPSG:26916 → local ENU meters from the verified Wolf Point origin; heightfield quantized ≤0.25 ft, 5–10 ft cells; period feet/chains recorded in notes at ingest.

## check.sh / bake.sh (Kevin's amended §11)

- **`check.sh`** (<10 s, no Blender; every agent sandbox + light CI on PRs): schema → referential → semantic (confidence rules, per-scene phase/date gates, epoch coverage, review_required release block) → archetype **param parse** via the pure-Python `*_params.py` (no bpy import) → license check → **staleness check** (input-hashes vs `assets/manifest.json`; a stale committed GLB is an ERROR) → renderer JS module-parse → publish-sync diff + size budget.
- **`bake.sh`** (on demand + nightly, Actions; also runnable locally): fetch + sha256-verify pinned Blender tarball (cacheable ~350 MB; `bpy` wheel documented as fallback) → refuse if datum unverified → `--factory-startup` headless build: resolved phase → params → archetype `build()` → `confidence_paint` writes COLOR_0 → smart-UV + **bake AO/normals** → GLB export (Y-up meters, node name `<structure>__<phase>`, ids in `node.extras`) → terrain/flora gen → `gltf-transform optimize` (meshopt + KTX2 + palette) into `assets/web/` → compile sidecars → rewrite manifest → publish → check.sh. Ends green or not at all.
- **Determinism** defined on inputs (Cycles AO isn't bit-reproducible across hardware): pinned Blender, fixed seeds, sorted iteration, no timestamps; rebake only what's stale so diffs stay reviewable.
- **Trigger**: `bake.yml` on dispatch + nightly cron + path filter (`data/**`, `generators/**`); non-empty diff → `steward/bake-<run>` branch → PR (never push main); empty nightly runs exit silently. Doc/research/renderer-only agents never wait on Blender.

## Renderer (three.js walkthrough, no build step)

Vendored **pinned three r185** (module + only the addons used) behind an importmap; sha256s in a vendor MANIFEST. Modules: scene-loader (year param → scene json → GLBs + sidecars + registry), world (Sky with prairie-haze turbidity, sun computed from the documented lighting moment, one tight ±60 m shadow, PMREM env, ACES), terrain (mesh + `heightfield.bin` bilinear sampler), buildings (**one BatchedMesh**, shared atlas material, per-building raycast picking), vegetation (InstancedMesh per archetype, distance-fade), controls (**single input-intent object** written by pointer-lock or touch backend — hand-rolled ~150-line thumbstick, tap-to-start doubles as audio unlock), walker (capsule on heightfield + step-up ~0.35 m for plank walks + footprint push-out — no physics engine), popup (per-attribute provenance card with confidence chips + citations), hud (year badge, confidence toggle, themes).

**Confidence view** (non-negotiable, ships in Milestone 0): generator paints per-vertex `COLOR_0` (0=documented, 0.5=inferred, 1=conjectural — the archetype knows which geometry derives from which attested attribute); renderer applies one `onBeforeCompile` uniform — off = normal; on = documented normal, inferred lerped amber, **conjectural as screen-door-dithered translucent massing** (alphaHash-style — no transparency sorting, works inside BatchedMesh). Popup and tint read the **same sidecar**, so the visual claim and the citable claim cannot diverge.

Budgets as gates: ≤50–80 draw calls, ≤600k tris, ≤8 KTX2 ≤1024², ≤20 MB download, pixel-ratio cap 1.5 mobile. `window.__chicago4d` harness handle; **smoke.mjs**: Chromium (fleet `PW_EXECUTABLE`; WebKit CI-only), 390×780 + 1280×800, both themes, zero pageerrors, canvas non-black, confidence toggle changes the render, programmatic pick shows a citation, walk intent moves the camera, draw calls under budget; anchor screenshots as evidence.

## Phases & parallel execution

```
S0 scaffold ─┬─► S1 georeference+datum ──► S2 terrain e1834 ──► S3 M0 integrate (Sauganash walkable)
             ├─► R1 renderer shell (synthetic GLB + flat ground) ─┘
             ├─► P1 research dossiers (read-only) ──► S5 structure records ──► S8 M1
             └─► S4 archetype generators (golden params) ─► S5 bakes
S2 ──► S6 flora/fauna ──► S7 polish/perf/audio ──► release sweep
```

**Critical path: S1 → S2 → S3** (datum first — everything regenerates if it moves; validator hard-fails geometry while unverified). Renderer, archetypes, and research proceed in parallel on synthetic data/golden params/symbolic positions until S1 lands.

| Stage | Parallel parcels (contract: inputs → outputs → gate) | Sessions |
|---|---|---|
| S0 scaffold (this session) | tree, AGENTS.md, schemas, validate port, check green, changelog, landing card | 1 |
| S1 datum (serial, careful) | LOC Hathaway + BPL Wright GeoTIFF + Allmaps annotations → traces/GCPs → datum verified w/ residual memo; warp to PLSS section lines, not buildings | 1–2 |
| S2 terrain | shoreline/river vectors · 30-zone heightfield · slough/hydrology · terrain_gen | 2–3 |
| R1 renderer shell | shell+intent+walker · confidence shader+popup vs test sidecar · smoke.mjs | 2–3 |
| S3 **Milestone 0** | Sauganash end-to-end (DoD below) | 2–3 |
| S4 archetypes | one parcel per archetype (11), golden-param GLB + shot each | 4–6 |
| P1/S5 structures | per-cluster parcels: Wolf Pt west (5) · north bank (6) · South Water blocks A–G · Lake St (7) · civic square (3) · fort interior (10+) · harbor works | 8–15 |
| S6 flora/fauna | per-zone (10) + fauna species + flora_gen | 3–5 |
| S7 polish | perf, ambience audio, popup UX, LIBERTIES, STATUS | 3–4 |
| S8 **Milestone 1** | Wolf Point cluster + South Water block D (LaSalle–Clark) | 2–3 |

**≈30–40 agent sessions, ≈15–20 serial-equivalent.** Orchestration: within a session, subagent fan-outs for parcels whose outputs are disjoint files by construction (per-structure, per-archetype, per-zone); **every writing subagent gets its own worktree** (fleet hard rule); Blender-touching work and milestone integrations run as dedicated sessions. Fleet fold-in: changelog from commit one, steward branch discipline, ROADMAP.md as the future steward playbook, Manager `projects` row (`Chicago 4D`, repo `kevinrhaas/custom`, site URL, status `building`).

## Milestone 0 — the Sauganash, end to end (adapted DoD)

1. Verified `data/sources/` entries incl. `kinzie_waubun_1856` (the load-bearing near-primary), chicagology prefire273, `andreas_1884_v1` **with p.106 actually fetched and page-cited** (best remaining lead on dimensions), the Chicago Landmark record; web sources carry `archived_url`.
2. `structures/sauganash_hotel.json` with two phases (`log_1829` incl. the move; `frame_1831`); honesty baked in: stories/paint/shutters `documented`; footprint `conjectural` pending Hathaway trace; `gallery: conjectural` with the dispute named (the 1867 Blanchard/Shober, CHM drawings, and 1902 Calisphere retrospectives disagree); dispute written up in `docs/RESEARCH/sauganash_hotel.md`.
3. `frame_tavern` builds from the resolved phase alone; balloon-frame logic correct (stud spacing/sheathing — the thing a knowledgeable viewer checks first); confidence channel painted.
4. `bake.sh` emits master + web GLB + sidecar; manifest fresh; committed.
5. Walkable at `walk/?year=1835` on desktop pointer-lock **and** touch.
6. Confidence toggle visibly separates documented massing from the dithered conjectural gallery.
7. `check.sh` + `smoke.mjs` green at both viewports; changelog stamped.

**Milestone 1**: Wolf Point cluster (Wolf Tavern w/ painted wolf sign; Green Tree — best-documented interior, 12×12 ft rooms, 7½ ft ceilings, use the 1859 photograph with alteration caveat; Miller House; Western Hotel; Walker's meeting house with its bank dispute recorded; the two log bridges + raft bridge) + South Water block D (Peck's store, militia ground, Harmon & Loomis with height flagged). `exclusions.json` earns its keep here.

## The 1835 structure ledger (v0 seed — from this session's dossiers)

~30 documented-and-modeled (Sauganash, Wolf Tavern, Green Tree, Western Hotel, Miller House, Walker meeting house, Cobweb Castle at N. State & N. Water (Hamilton residence by 1833 — NOT at the fort), Exchange Coffee House, Tremont House I (3-story flagged), Mansion House (= Graves' boarding house, one structure), Fort Dearborn complex (garrisoned — Maj. John Greene, 5th Inf.; palisade, SW blockhouse, NW bastion, brick magazine + commandant's quarters, log barracks, sutler, hospital, 80×200 parade, gardens toward Madison), 1832 lighthouse (40 ft, conical), Dearborn St drawbridge (~300 ft, 60-ft draw, twin gallows frames, patched per its 1835 repairs), both branch bridges, post office + Brewster Hogan & Co (Franklin & S. Water), Temple Building, Peck store, Chicago Democrat + Chicago American offices (the American four weeks old at target date), Bates auction room, Madore Beaubien log house, Carpenter stores, First Presbyterian (benches across the slough out front), St. Mary's (corner conflict flagged), estray pen + log jail, J.B. Beaubien homestead (corner conflict flagged), Newberry & Dole warehouse + wharf **north bank at Rush**, Dole 1832 warehouse near Lake & Dearborn, Steamboat Hotel); **under construction at date**: Lake House brick shell, first courthouse (month unfixed — frame going up, flagged), pier extensions with active crib works; **inferred/conjectural fill**: attested-but-undimensioned structures + Hathaway built-block massing, all tagged; **documented absent**: Kinzie mansion (gone by 1835 — leave its surviving cottonwood), Ouilmette cabin, and the full EXCLUDE list as data. Population ~3,265; ~250 vessel arrivals in 1835 → busy wharves; Wabansia platted but nearly empty.

## pre_fire_v1 photo/map update (this session's second slice — additive, no schema change)

1. Extract the JPEG from `IMG_5379.jpeg.pdf`; copy the three PNGs under descriptive names into `media/images/buildings/`.
2. `media.csv` rows with the existing caution pattern: `representation_type` retrospective_chromolithograph / retrospective_map_engraving; `accuracy_note` "1880s–90s retrospective, not an eyewitness record"; PD rights; source_url re-pointed at holding-institution scans where locatable.
3. `media_buildings.csv`: the Kurz & Allison 15-vignette sheet links to multiple existing records via its printed key — Sauganash (panel 14), Green Tree (11), Kinzie Mansion (12), Wolf Point (9), Fort Dearborn (1/5/15) — panel numbers in notes.
4. **The 1940 Nelson/Winters "Old Chicago" map does NOT publish** until a Stanford Renewal Database check clears its 1940 copyright; it stays in `reference/`. (Design-review correction.)
5. Regenerate `viewer/data.json` (add a small `tools/build_data_json.py` so the join stops being hand-maintained), bump cache-bust `?v=5`, byte-copy to `site/chicago/pre-fire/`, add the missing bare-path `index.html` stub, smoke it.
6. Cross-link: 4d records carry `xref.pre_fire_v1_building_id`; pre-fire rows whose id appears in the 4d-published `walkable.json` get a "Walk 1835" button → `../../4d/walk/?year=1835`.

## Verification

- `check.sh` green every commit; date-guard test (a deliberately added 1836 structure is excluded from scene 1835); phase-overlap hard error test.
- M0 acceptance = walk + toggle + citation popup + smoke green at 390×780 and 1280×800.
- Bake reproducibility: nightly `--stale-only` on a clean checkout produces an empty diff; manifest asserts Blender version.
- Honest STATUS.md (joliet precedent) — unverified things stay labeled unverified.

## Risks

| Risk | Mitigation |
|---|---|
| Datum is the true critical path | First, serial, careful; validator hard-fails geometry while unverified; derivation memo + residuals make the verification itself citable |
| Conley/Stelzer rights (1933 © stamp vs BPL "no known restrictions") | `rights_status: check_required` blocks derived assets; textual use fine; Stanford renewal check before any derivative texture |
| LOC Hathaway "[1820?]" mislabel | Record discrepancy verbatim; cite Newberry catalog for 1834 alongside |
| EOC 503s (several claims snippet-derived) | `archived_url` required; re-fetch + archive pass before promoting claims to `documented` |
| Bake determinism / GLB churn | Input-hash manifest; sha256-pinned Blender; fixed seeds; rebake only stale |
| Date drift past 1835 | Per-phase scene gates (hard error) + `exclusions.json` as cited data |
| Indigenous history (§10) | Standing AGENTS.md constraint; no human figures at all in v1; `review_required` blocks release |
| Sauganash unattested dims / disputed gallery | Modeled honestly — conjectural footprint, dithered gallery; a feature of M0, not a blocker |
| Mobile retrofit pain | Touch backend + budgets in R1, smoke-gated from first walkable commit |
| Repo/Pages weight | ≤25 MB published budget enforced; masters unpublished; no LFS; revisit past ~80 MB repo growth |
