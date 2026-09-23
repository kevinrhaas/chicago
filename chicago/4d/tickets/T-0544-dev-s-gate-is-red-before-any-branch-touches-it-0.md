---
id: T-0544
title: dev's gate is red before any branch touches it: 0 platted cross-street faces, a block off the ground, the far-timber census, and six resident-name assertions in the smoke
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

dev's gate is red before any branch touches it: 0 platted cross-street faces, a block off the ground, the far-timber census, and six resident-name assertions in the smoke.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`origin/dev` at 34eb6a34 fails its own gate with NOTHING applied. Proved by stashing a
working tree clean and re-running: the failure set is byte-identical before and after,
so every branch cut from dev inherits a red gate and no ticket can merge on one.

`./tools/check.sh` — CHECK FAIL, four groups:

- `the seven cross streets have 34 platted faces — got 0`, and `both sides of every
  covered cross street are found`.
- `1 committed platted block(s) stand off the modelled ground: blk_washington_clark` —
  a block the plat emits that `tools/generate_block_infill.py` cannot deal roofs to.
- `SOUTHERN GROUND FAIL — the programme's stated southern coverage is not what the
  ground measures.`
- `the far-timber census disagrees with what is banked (ROADMAP R-BUG5)`, three times.

`node tools/smoke_renderer.mjs` — six assertions fail in the residents/households layer, and **that half is already T-0524's** (`The renderer smoke still asserts a reconstructed resident, 956 person entries and 150 research reviews, and the layer has none of the three`, in flight on `steward/t-0524-to-the-top`). Listed here only so the two halves of a red gate are visible in one place; this ticket owns the `check.sh` half
at 390x780, all of the same shape (a value arriving `undefined` or empty where the card
expects a graded one):

- `a reconstructed resident has an invented period name — name "undefined"`
- `the invented name is graded as invented and says so — name_basis undefined`
- `the household is named for its head and still says which layer it is`
- `the card shows that title and keeps the reference below it`
- `search still finds it by its part number and by its household`
- `a building raised for an inferred household says so — basis ""`

**Acceptance:** `./tools/check.sh` passes on `origin/dev` with nothing applied (the smoke half is T-0524's), and the fix says which merge broke each group. The window is PRs #682-#686, merged 2026-09-03, which are the only things between T-0491's
"dev's gate is green again" and this reading.

**Note for whoever takes it:** the smoke needs more than ten minutes of wall clock for
both viewports on this runner, which is longer than a single foreground command may
run. `SMOKE_VIEWPORT=mobile` and `SMOKE_VIEWPORT=desktop` split it, and that is how this
reading was taken.

**Found by:** T-0533, which could not merge a fully verified transcription because of it.

Still red at 5c0d015f (after #689, #690, #692 merged), with the identical check.sh failure set — so none of the census or voter-list work is the cause, and none of it is the fix.

**Withdrawn 2026-09-03 (afternoon), on the merge of PR #693 into a green dev.** The condition this ticket named no longer holds: `bash tools/check.sh` passes on dev at 050e934c, af271bd0 and on every branch merged from it today (CHECK PASS, three times), and the smoke half was closed by T-0524 in PR #696 (parts 3 and 13 green in both viewports). Nothing here was worked; the repairs landed under other tickets.
