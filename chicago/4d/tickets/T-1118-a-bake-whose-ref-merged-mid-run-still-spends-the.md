---
id: T-1118
title: A bake whose ref merged mid-run still spends the whole bake before the PR is withheld
state: open
epic: META
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

`bake_ref.py --check-base` now answers whether the ref a bake was built from still
has anywhere to go, and `open-pr` refuses to open a PR into a base that does not.
That stops the junk PR. It does not stop the bake.

The check runs in the `baseref` step, which is the second step of the `bake` job —
so when it answers `0` the workflow already knows the whole run is pointless, and
then goes on to spend the next three quarters of an hour regenerating 196 binary
assets, pushing a branch nobody will read, and running the published smoke against
it. Every downstream job behaves correctly; all of it is wasted.

Measured 2026-09-14, the seven bakes that produced this rule:

    bake   opened   base                                 parent merged
    #1283  23:15    fix/queue-ratchet                    22:27   before
    #1285  23:49    steward/t-1004-two-men-one-card      23:09   before
    #1286  23:51    steward/t-0995-shared-roll-lines     22:48   before
    #1288  00:05    steward/t-0896-drain-check-capable   23:05   before
    #1292  00:20    steward/t-0266-phone-picket-moire    23:50   before
    #1293  00:31    steward/t-0809-rotting-pr-rule       01:18   after
    #1294  00:40    steward/t-0801-prefire-viewer-wright 02:06   after

FIVE of the seven were dead **before the bake started**, not merely before it
finished — the base had already merged when the run began. Those five are
recoverable in full: the run could have stopped at its second step. The other two
merged while the bake was in flight and are not; a bake cannot know at minute two
what will merge at minute forty.

So this is worth roughly five full bakes in a three-hour window, and it recurs
whenever the loop runs several slices — which is the condition the fleet wants to
return to.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- A bake whose base is already dead at the `baseref` step does not regenerate
  content, does not push a branch, and does not run the published smoke. It ends
  GREEN with a notice saying which ref it declined and why — a skipped bake is not
  a failure and must not read as one in the Actions list.
- The two bakes that die mid-flight keep today's behaviour exactly: the bake runs,
  the branch is pushed, and only the PR is withheld. Nothing here may turn a
  completed bake into a discarded one.
- The nightly is untouched. `dev` is a pipeline tier and always live, and there
  must be a test that says so — a rule that can skip the nightly is worse than the
  waste it saves.
- `bake_ref.py --self-test` covers the new decision, and its drift guards assert
  the workflow still consults it, in the shape the existing T-0454 guards use.
