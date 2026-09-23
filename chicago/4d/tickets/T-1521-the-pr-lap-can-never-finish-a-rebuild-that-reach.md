---
id: T-1521
title: The PR lap can never finish a rebuild that reaches manifest step 156: it runs rederive without publishing, so rebuild_closing_set refuses and the PR is left alone on every lap for ever
state: open
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-21
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The PR lap can never finish a rebuild that reaches manifest step 156: it runs
`rederive.mjs` without publishing, so `rebuild_closing_set.py --build` refuses and
the PR is `left alone` on every lap, for ever.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

MEASURED 2026-09-21, lap run 35624254338 (16:13Z), on PR #1630:

    === PR #1630  (steward/t-1516-policy-only-rung-deal)
      rebuilding the derived layer against the merged inputs
      the derived-layer rebuild failed — left alone:
          [154/156] python3 tools/report_census_1840_residue.py --write
          [155/156] python3 tools/report_letter_list_collisions.py --write
          [156/156] python3 tools/rebuild_closing_set.py --build
          FAILED: python3 tools/rebuild_closing_set.py --build
            REFUSED to write docs/RESEARCH/closing-convergence-2026-09.md: the
            mirror is not published, so the published-resident count was not taken.

    PR lap: pushed=0 already-current=0 left-alone=2

AND THE FIX, DEMONSTRATED THE SAME HOUR on the same branch in a clone:

    bash tools/publish.sh                          -> published
    python3 tools/rebuild_closing_set.py --build   -> wrote docs/RESEARCH/closing-convergence-2026-09.md

`site/chicago/4d/` is GENERATED and untracked since T-0938, so a fresh checkout has no
mirror at all. `rebuild_closing_set.py` reads the published resident count and refuses
rather than write a number it did not take — which is right. `rederive.mjs --run` does
not publish, and neither does the lap. `tools/check.sh` publishes FIRST, before anything
reads the mirror, for exactly this reason; the lap never learned it.

WHY THIS IS NOT A TRANSIENT AND WHY IT MATTERS. Every lap on such a PR fails at the same
step, so the PR is left alone permanently. It is not waiting for the lap's next pass —
the lap has already reached it and cannot finish. That is indistinguishable from the
outside from a queue the lap has not got to, which is how three PRs with GREEN gates came
to sit unmergeable on 2026-09-21 (#1629, #1630, #1631) while the lap reported success.

**Acceptance:**

- The lap publishes the mirror before the derived-layer rebuild, the way `check.sh` does
  — and the reason is stated where it is done, not merely in this ticket.
- A rebuild that fails STILL SAYS WHICH STEP AND WHY in the run summary, as it already
  does. That half is working and is how this was found; do not lose it while fixing the
  cause.
- A regression test: a lap over a branch whose rebuild reaches step 156 pushes, rather
  than reporting `left-alone`. If that cannot be tested in the harness, say so in the PR
  and state what was checked by hand instead.
- SEPARATELY, #1629 failed the same lap with `checkout failed` and no further detail.
  That is a second fault in the same run and is NOT covered here: either it gets its own
  ticket or the lap's checkout is made to say what went wrong. Do not fold it in.
