---
id: T-0649
title: Settle whether the Eliza Chappel shore drawing is a fifth view of the Sauganash's log annex, by reading its lighthouse
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 777
claimed_by: run 9/4/2026, 6:19:06 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T11:57:49.646Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33867088988
---

Settle whether the Eliza Chappel shore drawing is a fifth view of the Sauganash's log annex, by reading its lighthouse.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Settle whether the Eliza Chappel shore drawing is a fifth view of the Sauganash's log annex, by reading its lighthouse.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Settle whether the Eliza Chappel shore drawing is a fifth view of the Sauganash's log annex, by reading its lighthouse.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Where this comes from.** T-0617 read the four attested Sauganash views and deliberately
did NOT spend the fifth image the owner deposited on 2026-09-03,
`chicago/reference/images/chicago/eliza-chappel-school/21617595_10203558686525015_5452300313452439832_n.jpg`,
because it is not settled what it depicts. Its provenance record is filed at
`data/sources/eliza_chappel_school_shore_view.json` — unattributed, undated, tier 5,
`asset_use: cross_check`, nothing resting on it. `docs/RESEARCH/sauganash_image_accuracy.md`
§ 4 states the fork.

**The fork.** (a) It is Eliza Chappell's FIRST school of September 1833 — the *"small log
house formerly used as a store"* that the Beaubien material identifies as Mark Beaubien's own
original cabin beside the Sauganash at Lake and Market — in which case it is a **fifth view of
the Sauganash's log annex**, nearly square-on, and the most informative one the project holds:
log course count, door and window placement in the face, roof pitch and eaves, all scaled
against a schoolmistress and two dozen children. (b) It is some other log schoolhouse, in which
case it leaves the Sauganash and goes to whichever record it does depict.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The **lighthouse is the control**, and it is read rather than eyeballed: the tower's drawn
  position and proportions against `chicago_harbor_lighthouse_1838.jpg`, the bank's bearing,
  and the log building's orientation, taken together, say which corner of the town this view
  can be standing on — or say, with the number that shows it, that they cannot.
- The finding is a committed detector under `tools/measure_*.py` with a banked baseline, per
  T-0197's rule, not a paragraph. `tools/measure_sauganash_plate.py` is the worked example.
- The source record's `describes_date` and `note` are updated with whatever the lighthouse
  establishes, and `verified` moves only if the subject is actually settled.
- If (a) holds, the successor that SPENDS the view on the annex is filed, and this ticket does
  not spend it. If (b) holds, the image is pointed at the record it does depict and the
  Sauganash research note is corrected to say so.
- Either way, nothing about an attributed plate (Braunhold, Petford, Trowbridge) moves on this
  image's authority. Where it agrees it corroborates; where it is alone it is a single weak view.

**Links:** T-0617 (the reading that filed this) · T-0616 · T-0626 (where the Sauganash plan is
decided) · T-0197 (measure, do not look) · T-0092 (how a single weak view is graded) ·
`data/sources/eliza_chappel_school_shore_view.json`.
