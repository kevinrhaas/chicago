# 4D Chicago

A historically-grounded, walkable reconstruction of downtown Chicago — architected across
time. The first rendered scene is **summer 1835** (`1835-07-01`).

**This is a research dataset with renderers attached.** The durable artifact is the
georeferenced land and structure data with per-attribute source provenance. The three.js
walkthrough is the first renderer; the data is designed to outlive it.

## Why "4D"

The spine of the project is **the land**, versioned through time: elevation, hydrology,
shoreline, the sandbar and the harbor cut, and later the fill and grade-raising that buried
the original ground. Structures carry existence ranges and dated phases on top of it. A
*scene* — `data/scenes/1835.json` — picks a date, and everything else resolves to it.

That means 1830, 1833, or 1848 are new scene files plus a terrain epoch, not a rewrite.

## The confidence model

Every attribute carries its own evidence level, because you routinely know a building's
location precisely while knowing nothing about its roof pitch.

| level | meaning |
|---|---|
| `documented` | a source directly attests this attribute at the scene date (requires a resolving `source_id`) |
| `inferred` | derived from typology, adjacent evidence, or period practice (requires a stated reasoning `note`) |
| `conjectural` | no evidence; filled for visual completeness only |

**Every renderer must implement the confidence view** — a toggle that recolors the scene by
evidence quality: documented renders normally, inferred renders tinted, conjectural renders as
translucent massing. This is not a debug feature. It is what separates this from a themed
environment.

## Layout

```
data/         the project — sources, structures, scenes, terrain epochs, flora, fauna, traces
generators/   Blender (bpy) archetypes; every mesh regenerates from data by command
assets/       baked output (masters + web derivatives), authored hero assets, licenses
renderers/web the three.js walkthrough (no build step, vendored + pinned)
tools/        check.sh (fast gate) · bake.sh (content build) · validate.py · smoke.mjs
docs/         PLAN, PROVENANCE, EPOCHS, LIBERTIES, STATUS, RESEARCH/, research/ dossiers
```

## Working here

```bash
tools/check.sh          # the gate. seconds. no Blender. run before every commit.
tools/bake.sh --help    # the content build. pinned Blender. on demand + nightly.
```

Read **`AGENTS.md`** before doing anything — it is one page and it carries a standing
constraint about Indigenous history that applies to every session.

Published at `site/chicago/4d/` (walk app at `walk/?year=1835`).
