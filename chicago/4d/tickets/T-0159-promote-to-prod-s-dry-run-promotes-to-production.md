---
id: T-0159
title: promote-to-prod's dry_run promotes to production and says it did not
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-23
pr: 328
claimed_by: null
blocked_on: null
needs_bake: false
---

`chicago-4d-promote-to-prod.yml`'s `dry_run` input did the opposite of what it
says, and said so in the log while doing it.

```yaml
- name: Stop here on a dry run
  if: inputs.dry_run
  run: |
    echo "dry_run — nothing promoted."
    exit 0
```

`exit 0` in a `run:` block ends **that step**, not the job. Every step below it
ran anyway. Dispatched with `dry_run: true` on 2026-08-23 at 14:31Z, run #9
printed

```
dry_run — nothing promoted.
```

and then:

```
3509196f..731764b7  main -> main
Promoted 27 commit(s) to main.
Tagged release-v248
```

— a full production release, plus a deploy dispatch. The log asserted one thing
and the repository recorded another, which is the worst shape a safety flag can
take: the operator reads "nothing promoted" and believes it.

Found by using it. This run dispatched the dry run first *specifically* to check
a 27-commit release before shipping it, which is what the input exists for, and
the check shipped the release.

**Fixed here.** The guard is on the DESTRUCTIVE steps rather than in a step of
its own — `if: ${{ !inputs.dry_run && … }}` on both "Back-merge…" and
"Publish…" — so a dry run is expressed the only way that cannot lie: those steps
read as *skipped* in the run's own step list.

Note for whoever reviews: the first attempt at this fix ADDED a second `if:` key
to a step that already had one. YAML silently keeps the last, so the guard was
inert and the step list still showed the old condition. Both conditions are now
combined into one expression, and a duplicate-`if:` scan over the file reports
none.

**Acceptance:** a `dry_run: true` dispatch leaves `main` unmoved and no new
`release-v*` tag, with "Back-merge…" and "Publish…" showing as skipped;
a normal dispatch still promotes. Demonstrated both ways before this is trusted.

---

## DEMONSTRATED 2026-08-23, both directions

The fix could not be tested until it reached `main`, because `workflow_dispatch`
reads the workflow from the default branch. It got there in `release-v249`.

**A dry run leaves production alone.** Run #11, `dry_run: true`:

```
main before: 04c28297      latest tag before: release-v249
main after:  04c28297      latest tag after:  release-v249
```

and the step list is the part that cannot lie:

```
 6  What is on dev                                          success
 7  Say what a dry run would have done                      success
 8  Back-merge main into dev, then merge dev into main      SKIPPED
 9  Publish (GITHUB_TOKEN pushes don't trigger deploy…)     SKIPPED
```

**A normal dispatch still promotes.** Run #10 moved main 731764b7 → 04c28297,
"Promote chicago/4d dev→prod: 4 commit(s)", and tagged `release-v249`.

### The cost of the bug, recorded honestly

It fired **twice** before it was fixed, both times on a dry run dispatched as a
safety check:

- Run #9 — the original defect. Printed "dry_run — nothing promoted." and
  promoted 27 commits, tagging `release-v248`.
- Run #10 — the fix existed by then, but only on `dev`. Dispatching against
  `main` read the OLD workflow, so a dry run promoted 4 commits and tagged
  `release-v249`. This was avoidable and was not avoided: the run that
  dispatched it had written, minutes earlier, that the guard was inert on main
  until it landed there, and then used a dry run as a safety check anyway.

Both promotions were wanted — the owner had asked for them — so no work was lost
and nothing had to be rolled back. The lesson is not about the outcome: a guard
that lives on a branch protects nothing, and knowing that in prose is not the
same as acting on it.
