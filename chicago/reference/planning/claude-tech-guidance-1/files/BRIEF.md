# Chicago 1835 — Development Brief

**Handoff document for Claude Code.** Read this in full before writing any code.

---

## 1. What this project is

A historically-grounded, walkable reconstruction of Chicago as it stood in **summer 1835**.

It is **not** primarily a game project. It is a **research dataset with renderers attached**.
That distinction drives every architectural decision below. The expensive, durable,
irreplaceable artifact is the georeferenced structure data with source provenance. Renderers
are disposable and plural.

**Target date:** `1835-07-01` (configurable, but enforced — see §5).

**Scope at full build:** roughly a half-square-mile — Chicago River forks east to the lake,
Kinzie St. south to Madison, State St. west to Des Plaines. Approximately 150 structures,
population ~3,300.

**First milestone:** one building (Sauganash Hotel) end to end. See §8.

---

## 2. Anti-goals

Read these before you start. They are the failure modes that kill this kind of project.

- **Do not hand-model geometry directly into a renderer.** All meshes are generated from
  data via scripts in `generators/`. If a mesh cannot be regenerated from `data/` by running
  a command, it does not belong in the repo.
- **Do not invent sources.** Every `source_id` referenced in structure data must resolve to a
  real entry in `data/sources.json` with a real citation. If evidence does not exist, mark the
  attribute `conjectural` — never fabricate a citation to make a validator pass.
- **Do not silently fill gaps.** Missing evidence is recorded as missing. The confidence model
  in §4 exists precisely so that guesses stay visibly labeled as guesses.
- **Do not drift past the target date.** Much of the vivid published description of early
  Chicago is from 1837–1845 and describes a substantially different, larger town. See §5.
- **Do not ingest assets without license provenance.** Every file in `assets/` needs a
  `LICENSE` entry. CC0 / CC-BY only unless explicitly cleared.
- **Do not couple renderer code to data structures.** Renderers consume glTF + JSON. They do
  not reach into `generators/` or reimplement the data model.

---

## 3. Repository layout

```
data/
  sources.json          Bibliography. Every citable source, with an id.
  structures.json       The core dataset. One record per building. Schema-validated.
  traces/               Georeferenced raster + vector traces of historical maps.
  terrain/              Shoreline, river channel, sandbar, elevation.
generators/
  common/               Shared bpy helpers: units, materials, export.
  archetypes/           One module per building archetype (see §7).
  build.py              CLI: data/structures.json -> assets/gltf/*.glb
assets/
  gltf/                 Generated meshes. Regenerable — treat as build output.
  textures/             PBR sets. Sourced or authored. License-tracked.
  audio/                Foley and ambience. License-tracked.
  LICENSES.md           Provenance for every third-party asset.
renderers/
  web/                  three.js viewer. Ships first. Maintained permanently.
  (godot/)              Later. Consumes the same glTF + JSON.
tools/
  validate_structures.py   Schema + semantic validation.
  check.sh                 Local CI gate. Must pass before any commit.
docs/
  RESEARCH.md           Working research notes, per-structure.
  PROVENANCE.md         The confidence policy, expanded.
AGENTS.md               The agent contract. Short. Read every session.
```

---

## 4. The provenance model

This is the part that makes the project worth doing. Get it right before there are thirty
buildings in the dataset.

Every structure carries per-attribute confidence, not one confidence score for the whole
building. You will routinely know a building's footprint and location precisely while knowing
nothing about its roof pitch.

**Confidence levels:**

| Level | Meaning |
|---|---|
| `documented` | A primary source directly attests this attribute at the target date. |
| `inferred` | Derived from typology, adjacent evidence, or construction practice of the period and region. Reasoning must be stated in `note`. |
| `conjectural` | No evidence. Filled for visual completeness only. |

**Rules the validator enforces:**

- `documented` requires at least one `source_id` resolving in `sources.json`.
- `inferred` requires a non-empty `note` explaining the inference.
- `conjectural` requires nothing but is surfaced in the build report and rendered distinctly.

**Renderer requirement:** every renderer must implement a **confidence view** — a toggle that
recolors the scene by evidence quality. Documented geometry renders normally; inferred renders
tinted; conjectural renders as translucent massing. This is not a debug feature. For a museum,
a classroom, or a civic audience it is the single most valuable thing the project offers, and
it is what separates this from a themed environment.

---

## 5. Date enforcement

Chicago between 1833 and 1837 changed faster than almost any settlement in American history.
A building that is correct for 1837 is wrong for 1835.

Every structure carries `documented_range: { from, to }` — the interval over which the
structure is attested to have existed in the described form.

`tools/validate_structures.py` **fails the build** if `TARGET_DATE` falls outside a
structure's `documented_range`. This is the most important check in the suite. It is cheap and
it catches the failure mode that quietly ruins historical reconstructions.

When a source describes something without a date, do not guess a range wide enough to pass.
Narrow the range to what is attested and mark the structure `conjectural` if that is what it is.

---

## 6. Coordinates and units

- **Geodetic working CRS:** EPSG:26916 (UTM Zone 16N, NAD83, meters). All map georeferencing
  and footprint data lands here first.
- **Scene frame:** local East-North-Up, **meters**, with a fixed datum origin. Structure
  records store both the UTM position and the derived local position; local is computed, not
  hand-entered.
- **Datum origin:** the Chicago River forks at Wolf Point. Approximately
  `41.8885 N, -87.6385 W` — **this is a placeholder and must be verified** against the
  georeferenced Hathaway (1834) and Wright (1834) surveys before any geometry is generated.
  Fixing this after the fact means regenerating everything.
- **Axis convention:** author to glTF — **Y-up, right-handed, meters**. three.js and Godot
  consume this natively; Unity's importer handles the handedness flip. Do not author in
  Blender's Z-up and export without conversion.
- **Historical units:** period surveys are in feet, chains, and links. Convert at ingest and
  record the original figure in `note`. Do not carry mixed units into the dataset.

---

## 7. Archetypes

Buildings are generated from a small set of parameterized archetypes, not modeled individually.
Target for the first two milestones:

1. `frame_tavern` — two-story balloon-frame with gallery. Sauganash.
2. `frame_storefront` — one/two-story balloon-frame commercial, gable to street. South Water.
3. `log_dwelling` — hewn log, still common in 1835.
4. `plank_walk` — raised board sidewalk over mud.
5. `ground_prairie` — the unimproved ground condition; wet prairie, mud, ruts.

Balloon-frame construction was invented in Chicago in 1832–33 and is the defining local
building technology of this exact moment. Get the framing logic right in the generator —
stud spacing, sheathing, proportions — because it is the thing a knowledgeable viewer will
check first.

Each archetype module exposes a single `build(params: dict) -> bpy.types.Object`. Parameters
come from the structure record. No archetype reads `structures.json` directly.

---

## 8. Milestone 0 — the Sauganash, end to end

Do this before anything else. One building through the entire pipeline surfaces every
integration problem in the project, and it is a week of work, not a year.

**Subject:** the Sauganash Hotel, Mark Beaubien's tavern at Wolf Point at the forks — the
social center of the settlement in the target window.

**Definition of done:**

1. `data/sources.json` contains real, verified entries for the Sauganash sources.
2. `data/structures.json` contains one schema-valid record for the Sauganash with per-attribute
   confidence and a defensible `documented_range`.
3. `generators/archetypes/frame_tavern.py` produces a mesh from that record alone.
4. `generators/build.py` runs headless and emits `assets/gltf/sauganash.glb`.
5. `renderers/web/` loads the glb and lets a person walk around it in a browser.
6. The confidence view toggle works and visibly distinguishes documented from conjectural
   geometry on this single building.
7. `tools/check.sh` passes clean.

**Expect this specific problem:** the surviving images of the Sauganash are later
reconstructions and illustrations, not photographs, and they disagree with each other. This is
the correct time to hit that — it forces the provenance model to prove itself on building one.
Record the disagreement in `docs/RESEARCH.md` and pick the best-attested reading with reasoning.

**Milestone 1** is one South Water Street block. It was the commercial street, so it yields
repeatable storefront archetypes — where the generator approach starts paying for itself.
Watch date drift here especially: South Water built up rapidly and most of the colorful
descriptions people cite are late-1830s.

---

## 9. Research sources

**Primary cartography**
- Joshua Hathaway, *Chicago with the School Section, Wabansia, and Kinzie's Addition* (1834).
  Commissioned by John H. Kinzie to facilitate lot sales; small rectangles denote individual
  buildings. Newberry Library digital collections. **This is the master geometry source.**
- *Chicago, drawn by J.S. Wright according to survey* (1834). Newberry. Best source for
  shoreline, river mouth, and the sandbar. Note the river's outward flow direction.
- Conley/Stelzer reconstructed plan of Chicago in 1833, via chicagology.com/prefire — compiled
  from library research plus data gathered directly from surviving pioneers.

**Textual**
- A.T. Andreas, *History of Chicago* (1884), 3 vols. Public domain. Includes the 1830
  landownership map and extensive pioneer recollection. Dense with building-level detail.
- *Chicago Democrat* (John Calhoun / J.S. Wright, from 1833). Period advertisements naming
  businesses and their locations block by block. This is the best street-level source that
  exists and it is well suited to bulk processing once digitized to text.
- Newberry Library Chicago manuscript collections — pioneer reminiscences.
- *Encyclopedia of Chicago* (Newberry/CHM) for orientation and cross-checking.

**Methodological precedent**
- `CamilleMorlighem/histo3d` — automatic reconstruction of historical 3D city models from
  historical maps. GRASS GIS digitization → BlenderGIS → BCGA procedural modeling → CityJSON
  via Up3date → val3dity geometry validation. Closest existing pipeline to what this project
  needs; read the accompanying paper before designing the trace-to-footprint step.
- chicago00.org — Chicago History Museum / Geoffrey Alan Rhodes. Not code, but the strongest
  precedent for archive-driven Chicago reconstruction, and locally reachable.

**Agent tooling reference**
- `Unity-Technologies/skills` — official agent skills for Unity CLI/headless workflows.
- `duolahypercho/GT-caliber` — read `AGENTS.md`, `LOOP_AGENT.md`, `tools/check.sh`,
  `docs/ASSETS.md` for the agent-contract and headless-CI-gate pattern. Ignore the game code.

---

## 10. Handling the 1835 context

The final removal of the Potawatomi from Chicago occurred in **August 1835** — within the
target window. It is the most historically significant event of the project's chosen year.

Requirements:

- Do not let an agent improvise Native presence, representation, dialogue, or depiction. This
  is not a research gap to be filled by inference; it is a subject requiring consultation.
- The Newberry's Indigenous Chicago curriculum is the starting point, and the project should
  seek review from Native scholars or community organizations before shipping any depiction.
- Until then, the correct behavior is to build the built environment accurately and leave
  human depiction out of scope entirely. An empty, accurate town is honest. A populated,
  invented one is not.

Record this as a standing constraint in `AGENTS.md`, not just here.

---

## 11. The CI gate

`tools/check.sh` must pass before any commit. It runs, in order:

1. `validate_structures.py` — JSON Schema, then semantic checks (§4, §5), then referential
   integrity against `sources.json`.
2. Asset license check — every file under `assets/` has an entry in `assets/LICENSES.md`.
3. Headless generator run — `generators/build.py --dry-run` for every structure. Catches
   archetype parameter drift.
4. Renderer build — `renderers/web` compiles.

Keep it fast. A gate that takes four minutes gets skipped.

---

## 12. First actions for Claude Code

1. Read this brief and `data/structures.schema.json`.
2. Scaffold the repo layout in §3. Empty modules with docstrings are fine.
3. Write `AGENTS.md` — one page, derived from §2 and §10.
4. Verify the datum origin against the Hathaway and Wright georeferences before anything else.
5. Begin Milestone 0 at step 1: build `sources.json` entries for the Sauganash. Research first,
   geometry second.

Do not skip ahead to geometry. The dataset is the project.
