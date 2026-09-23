---
id: T-1126
title: A building that fails to load leaves its signboard hanging in the air and its goods in the grass: the scene draws furniture whose host is missing, and nothing reports the error
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-14
pr: 1338
claimed_by: run 9/14/2026, 12:57:25 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T18:43:32.425Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34877560228
---

**The owner, 2026-09-14**, on Dearborn Street in the `/dev/` walk at `?year=1835`: *"we have a
sign hovering and goods no building, what happened to the building"* — with a screenshot showing
the board **J. BATES, JR. / AUCTIONEER** floating at head height over a lot-line fence, two crates
lettered `SUNDRIES` and `JOHN BATES JR. CHICAGO` standing in the grass beside it, and no building
between them.

**On a reload it was there** — *"ok its there now must have been a load anomaly"* — the auction
room standing, the board on its wall, the crates against its front.

**So the building is not missing and this ticket is not about Bates.** It is about what the scene
did while the building was not there, which is the part that is reproducible and wrong.

## The record is sound — checked before the reload, so the ruling-out stands

Every place the building could have dropped out was checked on dev at `575aec5b0`, and it is
present in all of them: the structure record with one `frame_1834` phase and archetype
`frame_storefront`; its position, its 12.192 × 7.62 m footprint and its 3.6 m wall height; the
baked master (`assets/gltf/…glb`, 34,640 B) and the web derivative (`assets/web/…glb`, 12,576 B),
both inside the ordinary range (`hogan_store` 32,368 / 12,688 B, `green_tree_tavern` 43,124 /
12,284 B); the entry in `assets/manifest.json`; the entry in the renderer's own
`data/sidecars/1835/index.json` → `structures[383]`; absence from `data/exclusions.json`, from the
sidecar exclusions and from `excluded_by_date`; and `roof_count: 1, inventory_eligible: true` in
the roof reconciliation. **Nothing in the data explains the empty lot, which is why the answer was
a transient load failure.**

## What the scene did about it: nothing

The board is not near where the building goes. It is on the building's east wall, to the
centimetre. The sidecar puts the footprint origin at local ENU **E 679.7, N −43.7**, 7.62 m of
depth running east and 12.192 m of frontage running south; the signboard anchors at
**E 687.32, N −54.83**:

```
east wall face  E 679.70 + 7.62 = 687.32   ← the sign's easting, exactly
frontage spans  N −43.70 .. −55.89         ← −54.83 falls inside it
```

Its `height_datum` says in terms *"the base of this building's walls — the lowest of a 5×5 terrain
grid over the footprint, as buildings.js sets it"*, its `wall_height_m` 3.6 is *"from the record"*,
and `opening_fit` records that the pass **moved it 5.03 m along the front, off door and window,
onto blank face**. The board is a function of a wall. The trade goods are placed the same way.

**When the wall failed to arrive, the board drew anyway, 2.55 m up, on nothing.** That is the
defect: a failed asset load does not degrade into an absence, it degrades into a *false scene* —
furniture presented as if its host were standing. A visitor cannot tell that from a claim, and
this project's whole contract is that what is drawn is what is argued for.

And **nothing said a word.** No console error reached the owner, no badge, no counter; the walk
looked finished. A load failure that is silent is one that cannot be measured, so there is no way
to know whether this is one building once or many buildings often.

## The ask

1. **Make furniture follow its host.** A signboard, a set of trade goods, a hitching post — anything
   placed off a structure record — must not draw when that structure's geometry is not in the
   scene. The board here is honest about its datum, so the test is available: if the host emitted
   no geometry, the dependent does not draw.
2. **Make the failure visible instead of silent.** A structure that is in `index.json`, manifested
   and unexcluded, and whose asset fails to load, should report it — a console error naming the id
   at minimum, and counted somewhere the DEV overlay can show. Right now the only detector is a
   person standing in front of the hole.
3. **Then find out why the fetch failed**, with the counter from (2) rather than by guessing: one
   GLB out of ~383, transient, recovered on reload. Look for the ordinary causes — a concurrent
   fetch cap, an aborted request on a fast camera move, a cache miss racing the tile cull, a
   `publish.sh` window where the mirror was mid-write. Do not change the record; it is sound.
4. **Count it before and after.** Drawn structures against indexed structures, reported once per
   load. If the number is ever short, the walk is lying about the town, and that is the figure
   that says whether this was one anomaly or a rate.

**Done when** a structure whose asset fails to load takes its signboard and its goods down with
it, the failure is reported and counted rather than silent, and the drawn-against-indexed count is
available to say how often it happens.
