---
id: T-0763
title: check.sh self-tests print FAIL lines that are indistinguishable from a failing step, and three tickets misdiagnosed dev's red on them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-11
pr: 1130
claimed_by: run 9/11/2026, 8:51:22 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T14:23:01.300Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34606434036
---

check.sh self-tests print FAIL lines that are indistinguishable from a failing step, and three tickets misdiagnosed dev's red on them.

**Acceptance** (stated before working, 2026-09-11):

1. On a GREEN `./tools/check.sh` (exit 0), **no line containing `FAIL` reads as a failure**:
   every one of them is a self-test's own output and is marked as such at the START of the
   line, where `grep` and a skimmed log both read.
2. **Nothing is silenced.** Each fired assertion's own words survive verbatim, stderr
   included.
3. `check.sh` names **the failing steps once, by label, at the end**, beside
   `CHECK PASS`/`CHECK FAIL` — so "what is red?" is answered where the reader already is.
4. The exit status is unchanged in both directions: a self-test that STOPS firing still
   fails the gate.
5. A gate keeps it true. A self-test that drifts back onto plain `step` — where it would
   print untagged again — is refused by a step of the gate itself.

**Measured 2026-09-05 on a GREEN tree** (`f3dfcc28f`, `./tools/check.sh` exit **0**, zero
`^ <label> failed`): **ten lines of the output still contain `FAIL`.** All ten are
self-tests working — a step that deliberately breaks a derivation and requires its
assertions to fire, where a fired assertion prints the same `FAIL <sentence>` a real one
does, and one of them even prints `2 check(s) FAILED` before its `self-test OK`:

```
FAIL the seven cross streets have 34 platted faces — got 0        (+ 1 more, then "self-test OK")
SOUTHERN GROUND FAIL … FAIL 1 committed platted block(s) stand off the modelled ground   (x2)
FAIL — the far-timber census disagrees with what is banked (ROADMAP R-BUG5)              (x3)
```

**What it has cost, three times in two days.** T-0745 was filed against six of these lines
and wrote three of its four acceptance clauses on them, sending the next run at terrain and
street geometry that are fine; T-0522, T-0612 and T-0683 all report a red dev that was not
one and sit in the queue's "probably already answered" band for it. The failing-step
roll-up exists — `step()` prints it — but only inline, so the only way to read the output
correctly today is to know which steps are self-tests.

**Acceptance:** a reader can tell a fired assertion from a failure without that knowledge.
The cheapest shapes: self-test steps prefix their expected firings (`fires:` is already used
by several), and `check.sh` prints the list of failing step labels ONCE at the end beside
`CHECK PASS`/`CHECK FAIL`. Whatever the shape, `grep -i fail` over a green run's output must
return nothing that looks like a failure. Not to be met by silencing a self-test's output.
