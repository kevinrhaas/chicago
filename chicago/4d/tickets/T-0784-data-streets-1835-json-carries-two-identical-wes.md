---
id: T-0784
title: data/streets/1835.json carries two identical west_water records under one id
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: null
claimed_by: null
blocked_on: Fixed on dev by T-0780 (#889) before this could be worked: the duplicate west_water record is gone and the sidecars regenerate.
needs_bake: false
closed_at: 2026-09-05T14:57:58.335Z
claimed_run: null
---

data/streets/1835.json carries two identical west_water records under one id.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0451.** `data/streets/1835.json` `streets[]` holds **two records with
`id: "west_water"`**, byte-identical in every field. Reading the file into a dict keyed
on `id` silently drops one; reading it as a list counts 23 streets where the town has 22.
Nothing downstream is known to be wrong today — the two records agree — but the file's
`id` is used as a key by `compile_scene.py`, `generate_plat_lots.py` and
`measure_west_division_streets.py`, and a duplicate id is a trap set for the day the two
copies stop agreeing.

It arrived with T-0445 (PR #875), which seated `west_water`; `.gitattributes` carries a
union merge driver for this repository's changelog and QUEUE and the duplication has the
shape of one. **The fix is not just to delete a line**: the gate should refuse a
duplicate `id` in this file, so the next union merge cannot reintroduce it.
