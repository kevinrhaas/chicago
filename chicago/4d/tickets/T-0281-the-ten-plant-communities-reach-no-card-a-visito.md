---
id: T-0281
title: The ten plant communities reach no card a visitor can open
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: 470
claimed_by: run 8/28/2026, 11:01:29 AM CT
blocked_on: null
needs_bake: false
---

The ten plant communities reach no card a visitor can open.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The Evidence panel carries the liberties, the ground, the households, the animals, what is not here
and what is still open. It does not carry the PLANTS. `data/flora/zones/*.json` — ten communities,
their graminoid, forb, shrub and tree lists, each species with its recorded density, cover, height
and sources — is read by `flora.js` and by nothing a visitor can open. It is the same gap K51 found
in the animal records and K52 found in the households, and it is the last of the three.

It has a second reason now. T-0019 measured what the forb lattice's ceiling costs and found nine of
ten communities drawing between 0.5 % and 85 % of the flowering plants their own records ask for.
That figure lives in `tools/forb_clamp_baseline.json` and in `docs/STATUS.md`, which is to say it
lives where a reviewer reads and not where a visitor does. **A visitor standing in the dense forest
is looking at half a per cent of the flowers the research put there and has no way to find that
out.** This project's whole bar is "never misrepresent what you built"; an undrawable density that
is only declared to reviewers is the weaker half of it.

**Acceptance:** a "What grows here" section in the Evidence panel, straight from
`data/flora/zones/*.json` the way the fauna section is straight from `data/fauna/`, listing each
community, the species in it with their recorded figures and sources, and — for the nine layers the
lattice clamps — the share of the record the scene is able to draw, read from the declaration rather
than typed. Publish-mirrored, both themes, phone and desktop.
