---
id: T-1336
title: The parallel gate from T-1289 races: a self-test that breaks a live file to prove a check fires runs concurrently with the step that reads it, so any PR in the queue can go red on a tree that is green
state: done
epic: META
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-18
pr: 1474
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T20:53:52.311Z
claimed_run: null
---

The parallel gate from T-1289 races: a self-test that breaks a live file to prove a check fires runs concurrently with the step that reads it, so any PR in the queue can go red on a tree that is green.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. **The gate's verdict does not depend on scheduling.** A step that is green on a
   quiet tree is never reported red because of what ran beside it. Demonstrated by
   the two PRs this was found on, both of which went red on a step that was green
   standalone on the identical tree.
2. **A real failure still fails.** The mechanism that removes the false red must not
   remove a true one: a step red on a quiet tree is red, first run and retry alike,
   and its output is printed once rather than twice.
3. **No self-test writes the live working tree.** Measured, not reasoned: an audit
   hook over every `self_test` in `tools/`, recording every file opened for writing
   inside the repo. Every offender fixed by breaking a COPY, with its assertions
   still firing and the live tree byte-identical afterwards.
4. **A race that survives is named, not swallowed.** A silent retry turns a race into
   folklore about a flaky gate. Any step that fails in the pool and passes alone is
   printed inline with its own label and listed again in the summary, on a PASS as
   loudly as on a failure.
5. `CHECK_JOBS=1` remains the escape hatch and reproduces without the race.


## WHAT IT IS, AND HOW IT WAS FOUND

T-1289 made check.sh run its ~497 steps in a work-stealing pool (775s → 251s). The
comment it shipped with named this hazard — "that is the escape hatch for any step
that turns out to share state with another" — and shipped without proving no step
did. It does.

Some self-tests prove a gate by BREAKING A LIVE FILE and restoring it in a `finally`.
Serially that is invisible. In a pool it is not: the step that reads the same file is
usually declared right beside it, so the pool runs the two together and the check
reads the break.

**Observed twice in one afternoon, on unrelated branches:**

  the T-1144 split   red on "the 1830 schedule's reading and its crosswalk re-derive"
                     — `read_census_1830.py --self-test` drifts the live
                     `resident_crosswalk.json`; green on the next run of the same tree
  T-1302 batch 2     red on "the business layer re-derives" naming
                     `biz_a_chicago_stove_and_hollow_ware_dealer_august_1835.json` —
                     which is `sorted(BUSINESSES.glob("biz_*.json"))[0]`,
                     `compile_businesses.py`'s own victim. `--check` green standalone.

The second names the file, which is what turns a plausible story into a diagnosis.

**AND MY T-1289 VERIFICATION COULD NOT HAVE CAUGHT IT.** It compared a parallel
transcript against a serial one and found them byte-identical. A race that fires on
some fraction of runs passes that test whenever it does not fire, so the check was
not weak — it was the wrong shape for the fault.

## THE MEASUREMENT

An audit hook (`sys.addaudithook`) over every `self_test` in `tools/`, recording each
file opened for writing that resolves inside the working tree. Tools whose `self_test`
takes arguments were run through their own `--self-test` CLI with the same hook.

**Six offenders out of 177.** Five wrote committed files; the sixth left its own
scratch PNG in `tools/`, which could not redden a neighbour but is still a self-test
leaving something in the tree:

    read_census_1830.py        data/research/census_1830/resident_crosswalk.json
    compile_businesses.py      data/businesses/biz_a_chicago_stove_…_1835.json
    build_book_page_index.py   data/research/books/page_index/*.json
    rule_newberry_leads.py     data/research/newberry_index/lead_crosswalk.json
    read_wabansia_streets.py   data/traces/wabansia_streets.json
    measure_plate_join.py      tools/.selftest_p6_1.png  (its own scratch)

`read_wabansia_streets.py` was the worst of them and had NO `try`/`finally` at all:
an assertion raising anything but SystemExit, or a killed process, left the committed
trace broken on disk. It also "restored" by re-serialising rather than writing the
bytes back.

Two of the six had comments claiming they already did the safe thing.
`compile_businesses.py` said "Broken in a temporary copy of the tree so the working
tree is never touched" — the temporary copy was the BACKUP, and the edit went into the
live record. A comment is not a measurement.

## THE FIX, IN TWO PARTS

**The offenders.** Each now copies to a scratch tree and rebinds the module-level path
(`DOMAIN`, `BUSINESSES`, `BOOKS`, `OUT`). A self-test runs in its own process, so the
rebind is enough: this process checks the copy while every other process still sees
the committed files. The `finally` restores the BINDING, not the bytes — no byte of
the live tree is written. Where a fixture used to depend on its `finally` running, it
now ASSERTS the live tree is unchanged at the end, so the property is checked rather
than hoped for.

**The harness, for the offenders nobody has found yet.** A step that fails in the pool
is re-run once the pool has drained — which is the only moment the tree is provably
quiet — and the retry's result decides. A step that then passes is recorded as a RACE:
printed inline with its label and listed in the summary under its own heading. That is
the difference between fixing this and hiding it.

## VERIFIED ON THE FIXED TREE

The same sweep, re-run after the six fixes:

    177 self-tests measured — 162 through an in-process audit hook, 15 through
    their own --self-test CLI with the same hook (their self_test() takes the
    arguments main() supplies, so they cannot be called directly)

    0 write the live working tree

Both halves of the population are measured, so this is a complete reading rather
than a sample. Each fixed fixture was also run on its own and its assertions
counted — 11 for compile_businesses, 5 for build_book_page_index, 5 for
rule_newberry_leads, 8 for read_wabansia_streets, and the plate-join's whole set —
because a fixture that stops firing is a worse outcome than the race it was
holding.


## CORRECTION: THE SWEEP ABOVE WAS PYTHON ONLY, AND IT DOES NOT SAY SO (2026-09-18)

This ticket says, twice, "an audit hook over **every** `self_test` in `tools/`", and reports
"177 self-tests measured". That reads as the whole population and it is not. The hook was
`sys.addaudithook`, which reaches python and nothing else. **check.sh runs 17 self-tests
that are not python — 15 node and 2 bash — and the sweep measured none of them.**

The number 177 was the python population. The claim built on it was broader than the
evidence, and the owner asking "is the race still a problem?" is what surfaced it rather
than anything in the gate.

**MEASURED SINCE, and the conclusion survives.** The 9 distinct node self-test commands were
re-run under an fs-write probe (node has no audit-hook API, so the `fs` write entry points
are wrapped instead), and the bash one was run with the tree watched:

    9 node self-test commands   all clean
    1 bash self-test            clean, tree unchanged

One apparent hit was a FAULT IN THE PROBE, not in the tool. `resolve_id_collisions.mjs`
appeared to write `tools/ticket.mjs`; it copies that tool and itself OUT of the repo into a
tmpdir where it builds a throwaway git repo, and the first probe recorded argument 0 of
`copyFileSync` — the SOURCE. A probe that cannot tell a read from a write manufactures
findings, and that lesson is written into tools/isolation_probe/node_probe.js where the
next reader will meet it.

So: no live-writing self-test remains, in any of the three interpreters. What was wrong was
the claim, not the fix.

**AND THE GAP THAT CORRECTION EXPOSES IS T-1339.** A point-in-time sweep proves today and
nothing else; the seventh offender is written tomorrow, and two of the six found here
carried comments claiming they already worked on a copy, so a convention does not hold this.
The retry net keeps the VERDICT correct when that happens and names the step — it does not
stop it. T-1339 turns the sweep into a measurement the gate reads
(tools/step_isolation.json + tools/audit_step_isolation.mjs), which also closes the second
gap this ticket left open: only self-tests were ever measured, and an ordinary `step` that
mutates races identically.
