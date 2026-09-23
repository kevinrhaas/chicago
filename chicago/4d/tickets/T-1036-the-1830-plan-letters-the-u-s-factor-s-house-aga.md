---
id: T-1036
title: The 1830 plan letters the U.S. Factor's House against three blocks 152 m south of the stockade, T-0894 measured them, and the fort reservation's one documented dwelling outside the pickets is still not built
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-11
pr: 1144
claimed_by: run 9/11/2026, 1:15:03 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T19:18:45.174Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34632001897
---

The 1830 plan letters the U.S. Factor's House against three blocks 152 m south of the stockade, T-0894 measured them, and the fort reservation's one documented dwelling outside the pickets is still not built.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Opened by T-0894, 2026-09-11**, out of the reading that closed it.

T-0894 asked where the Factory House stood and answered it off F. Harrison Jr.'s 1830 plan of the
river mouth — the plate this project's fort, garrison garden, Out Buildings and Mrs Jouett's grave
are all placed from. It letters **`U.S. Factor's House`** against **three** solid blocks on the
reservation, and `data/traces/harrison_1830_us_factors_house.json` carries them:

| block | local ENU | approx size | long axis |
|---|---|---|---|
| A, the one the label touches | (1152.2, 36.4) | 20.4 × 7.9 m | 40° ccw from east |
| B, north-west bar | (1140.3, 46.3) | 16.6 × 5.1 m | 128° |
| C, south block | (1141.2, 25.6) | 6.7 × 5.0 m | 42° |

Ink-weighted centre **(1145.6, 38.7)** — 152 m south of the palisade's nearest corner, east of the
road, off the garrison garden's southern corner. Three checks in that file land the same transform
on records already committed from the plate.

**Why it was refused on T-0894 rather than built.** The plate gives arrangement and a ±20 % size and
nothing else: no material, no roof, no opening, and no way to say which of the three blocks carries
`bk_hub_063`'s *"two-story, squared-log structure, inclosed by a neat split-picket fence"*. One
measured footprint under four invented attributes is the shape `docs/RESEARCH/fort_dearborn.md`
already refuses for the Well and the Cultivated Field.

**Why it is still worth a ticket.** This is the reservation's one dwelling outside the pickets that
two independent texts describe and a period plan draws, it is where Jouett and then Dean lived as
United States factors, and Andreas p. 205 and `bk_afc_009` agree Beaubien made it his dwelling house
from 1822. `jb_beaubien_homestead` is NOT it (T-0894), so the town currently shows nothing at all on
ground three sources furnish.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- A decision, in writing, on whether ONE block is built or all three, and on which block — if any —
  `bk_hub_063`'s two storeys and picket fence attach to. "Not determinable, so the storey count is
  inferred from the type" is an acceptable answer and is better than a quiet pick.
- Every invented attribute in `docs/LIBERTIES.md`, footprint graded from the plate at `inferred` and
  everything above it `reconstructed` at the L228 shape.
- The split-picket fence is an enclosure if it is built at all, not a wall on the structure — the
  Jouett grave's record is the precedent next door.
- It is a bake and a publish. Size it before claiming: one structure plus `bake.sh --only` fits a
  run; three do not.

**Links:** T-0894 · T-0883 · T-0882 · T-0881 · `harrison_1830_river_mouth` · `bk_hub_063` ·
`bk_afc_009` · `data/traces/harrison_1830_us_factors_house.json` ·
`docs/RESEARCH/fort_dearborn.md` § 7 · `docs/RESEARCH/jb_beaubien_homestead.md` § 6a
