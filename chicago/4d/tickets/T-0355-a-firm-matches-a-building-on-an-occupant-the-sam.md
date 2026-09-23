---
id: T-0355
title: A firm matches a building on an occupant the same sentence dates to 1831
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 550
claimed_by: run 8/29/2026, 12:20:37 PM CT
blocked_on: null
needs_bake: false
---

`tools/compile_register.py` proposes `enrich_existing` — a committed building already
carries this documented business — by matching the firm's partner surnames against the
record's own prose. `wolf_point_tavern_stable` carries:

    the tavern's keeper of the day — Elijah Wentworth in 1831, William Walters on the
    scene date

so E. Wentworth's public house matches it. The sentence names its scene-date occupant
in the same breath and the match ignores that. Three register rows land on the stable
this way (`business_e_wentworth`, `business_e_wentworth_s_public_house_on_flag_creek`,
`business_e_wentworth_s_tavern_flag_creek`), and the business they belong to is on Flag
Creek, on the road to Ottawa — outside the plat entirely.

Two candidate fixes, and the second is the better one if it is affordable:

1. Read the date qualification. A surname followed by "in <year>" where the year is not
   the scene year is a HISTORICAL occupant and must not match. Narrow, and it fits the
   one record shape that produced the fault.
2. Refuse a match when the business's own placement puts it outside the committed plat.
   That is the real error here — a tavern on Flag Creek cannot be in a Wolf Point stable
   whoever kept it — and it generalises.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The three Wentworth rows no longer take `wolf_point_tavern_stable`, and the register
  says what they take instead.
- A self-test case on the occupants line that caused it, so the guard can fire.
- No currently-correct `enrich_existing` is lost: the 39 are re-derived and the diff is
  stated in the PR.
