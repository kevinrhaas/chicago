---
id: T-1368
title: A conflicted PR can never be gated, so it can never be merged: no merge ref means no pull_request run, merge-ready only takes clean, and the lap stops at REAL CONFLICT — three PRs hit it in one evening and each needed hands
state: done
epic: META
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-20
pr: 1601
claimed_by: run 9/20/2026, 7:44:36 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T01:06:42.120Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35548071057
---

A conflicted PR can never be gated, so it can never be merged: no merge ref means no pull_request run, merge-ready only takes clean, and the lap stops at REAL CONFLICT — three PRs hit it in one evening and each needed hands.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**The deadlock, stated as a cycle.** A pull request whose conflicts the lap will not clear
cannot be merged by anything in this repo, and cannot become mergeable by waiting:

1. The PR is `dirty`, so GitHub cannot compute its merge ref.
2. `.github/workflows/chicago-4d-check.yml` gates on `pull_request` — and a `pull_request` run
   needs that merge ref, so the gate never starts. The PR carries **ZERO check runs**.
3. `gate` is a REQUIRED check on `dev`, so GitHub never calls the PR `clean`.
4. `.github/steward/merge-ready.sh` merges **only** on `clean` — deliberately, and its own
   comment measured why — so it passes over the PR every time.
5. `.github/steward/pr-lap.sh` prints `REAL CONFLICT — left alone` and stops, which is correct:
   it will not hand-merge a file no tool owns.

Nothing in that loop advances. The PR sits at zero checks for as long as it is left.

**Measured, three times in one evening (2026-09-19):**

| PR | ticket | conflicts | outcome |
|---|---|---|---|
| #1495 | T-1172 | 12, five "NOT the manifest's to clear" | hand-resolved; merge-ready merged it **within two minutes** of the push |
| #1497 | T-1174 | 136, 118 of them resident household cards | hand-resolved; merge-ready merged it at 04:33:48Z |

Both merged themselves almost immediately after the push — #1495 within two minutes. That is
the proof that the rest of the automation is sound: the ONLY thing missing was a gate run, and
the only way to get one was a person resolving conflicts.

**AND THE SHAPE ALONE DOES NOT IDENTIFY IT — corrected at filing, 2026-09-19.** This ticket was
first written citing THREE instances. The third, #1499 (T-1343), was `dirty` with zero check
runs and looked identical to the other two. It was not the deadlock: its steward run was still
going, and it went on to rebase onto `dev` twice, re-derive on each rebase, push, and clear
itself. It reached `blocked` with a gate running, entirely without hands. Counting it was wrong
and the table above is the corrected one.

So `dirty` + zero check runs is the SYMPTOM and not the diagnosis. A PR mid-run looks exactly
like a PR nothing will ever touch again. The distinguishing fact is whether the run that owns
the ticket is still alive: read `claim/t-NNNN` for the branch's ticket, take the `run:` URL out
of the marker body, and ask GitHub whether that run is still `in_progress`. #1499's was — its
`Run steward` step had been going 1h49m and it had opened the PR mid-run. A marker that no
longer exists means no run holds the ticket, which is the same answer as a finished one.

This matters twice over: anything that acts on the symptom will "fix" PRs that were about to fix
themselves, and colliding with a live run costs more than waiting — measured on #1495, where the
owning run's own convergence was better than the mechanical merge that raced it.

**Where it came from, and the part that matters.** The gate's push trigger is filtered:

```yaml
push:
  branches: [dev, main]
```

T-1288 added that filter, for a real and measured reason: a steward branch with an open PR
satisfied BOTH triggers, so every push ran the 439-step suite TWICE on one commit, and because a
PR is not `clean` until every required check passes, the PR waited on the SLOWER of two identical
runs. Four PRs were seen sitting `blocked` with one gate green and its twin still going. That
finding is not in question and this ticket must not undo it.

But an unfiltered push trigger fires on a branch push **regardless of mergeability**, which is
exactly the case `pull_request` cannot serve. T-1288 wrote down what it believed it was giving
up — "a steward branch pushed BEFORE its pull request exists is not gated by that push", closed
by the PR opening in the same run — and that list did not include this one: a PR that EXISTS and
is `dirty`, where `pull_request` structurally cannot run. So the filter removed the only trigger
that could have gated a conflicted branch, and the trade-off as recorded did not know it.

1. A conflicted PR either gets gated, or it is made LOUD. Both are defensible and the unit picks
   one with its reading written down; what must not survive is a PR sitting at zero checks with
   nothing reporting it. Options that exist, none of them prescribed here: dispatch the gate for
   a branch the lap left alone (`workflow_dispatch` is already on the workflow); have the lap
   label the PR and say so on it when it prints `REAL CONFLICT`; or have merge-ready report the
   `dirty` + zero-checks shape rather than passing over it silently.
2. **T-1288's measurement is preserved.** Whatever is done, one commit does not get two identical
   gate runs, and a PR does not wait on the slower of a pair. If the fix touches the push
   trigger, it is measured the same way T-1288 measured — count the check runs on one head sha —
   and the count is in the ticket.
3. The lap's own behaviour is unchanged where it is right. `REAL CONFLICT — left alone` is the
   correct call for a file no tool owns (T-1282); this ticket is about what happens NEXT, not
   about making the lap merge things it should not.
4. Demonstrated on a reconstruction of the deadlock — a branch conflicted against `dev` with an
   open PR — not asserted from the workflow files. Show the zero-check state before and whatever
   the fix produces after.
4b. **Whatever acts does not act on a PR whose run is still alive.** The check is the one above:
   the branch's `claim/t-NNNN` marker names its run, and a run still `in_progress` means the PR
   is being worked, not stuck. A fix that labels, comments on, dispatches a gate for or
   otherwise touches a mid-run PR is a fault of this ticket, because #1499 proves such a PR
   commonly resolves itself.
5. The hand-resolution path stays available and documented. Some conflicts genuinely need a
   person (118 resident cards carrying drawn values did), and the goal is that such a PR is
   VISIBLE and gateable, never that no PR ever needs hands.

**Not T-1362.** That one is the lap skipping its re-derive when a branch is already current with
the base — a branch that merges cleanly and is stale. This is a branch that does not merge at
all. They meet only in that both leave a PR red or stuck with no automation able to move it.

---

## FINDING (2026-09-19, 3:00 PM CT): a SPLIT ticket stops the lap dead, and nothing says so

A second way the queue deadlocks, unrelated to mergeability, measured today.

`tools/ticket.mjs split` leaves the parent at `state: split`. That is not an open
state. `tools/research_spend_ledger.py` holds every `unresolved` hand-off to an OPEN
ticket:

```
if states.get(ticket) not in OPEN_TICKET_STATES:
    faults.append(f"{where}: unresolved ticket {ticket!r} is missing or not open")
```

**T-1179 was split at 8:39 AM CT** into T-1392, T-1393 and T-1394. Five hand-offs
across three registers still named it. That check runs inside `rederive.mjs --run`,
and `.github/steward/pr-lap.sh` runs `--run` on every lap, so from 8:39 AM the lap
failed on every pass:

```
rebuilding the derived layer against the merged inputs
the derived-layer rebuild failed — left alone:
   FAIL: ... unresolved ticket 'T-1179' is missing or not open   (×5)
PR lap: pushed=0  already-current=0  left-alone=2
```

**The lap is the only thing that clears a `dirty` PR** (T-0857: GitHub's merge never
runs this repo's merge drivers, so a branch that merges `dev` cleanly in a clone is
reported conflicting by the platform). So a broken `--run` does not merely delay a
rebuild — it removes the one mechanism that can unstick the queue. #1526, #1529 and
#1533 sat `dirty` for six and a half hours behind it, and no amount of waiting would
have cleared them.

### The three ways this hid

1. **The log shows only the first five failures**, all prefixed `newspapers:`. The
   other four hand-offs — three in `civic/`, one in `land_sales/` — were never
   printed, so a fix aimed at the visible file would have left the lap just as dead.
2. **`validate.py --all` is green** throughout. This check lives in
   `research_spend_ledger.py`, which the lap runs and a spot-check of the dataset
   gate does not.
3. **The PRs look exactly like the mergeability deadlock** above — `dirty`, no check
   runs, owning runs finished — so the watch routine's liveness check clears them as
   reportable and the diagnosis stops at the wrong cause. It did here, twice.

### What actually fixes it

Repointing the five hand-offs is the remedy, not the fix. The fix is that **a split
must not orphan a hand-off**:

- `ticket.mjs split` knows the parent and the children. It could repoint every
  `unresolved` hand-off naming the parent, or refuse the split until they are
  repointed — the same way it already refuses other unsafe states.
- Failing that, the invariant should name the split's children in its own error, so
  the next person reads `T-1179 was split into T-1392, T-1393, T-1394` instead of
  `missing or not open`.
- And the lap should say which check failed on the PR, not only in its own log. A
  lap that gives up silently on every pass for six hours is indistinguishable from a
  lap that has nothing to do.

### Also corrected here

The finding above this one presents the merge-driver cause as new. It is not:
**T-0857** has it, and `pr-lap.sh` states it at the top of the file. What today's
measurement adds is only that GitHub's `mergeable` can stay `null`/`unknown`
indefinitely rather than merely stale — #1518 never resolved and merged fine when
asked directly.

**Still live, and it cost hands on FOUR PRs on 2026-09-20** — #1587, #1585, #1584 and #1590.
Each was `dirty`, each merged `dev` cleanly in a local clone, and each needed a human to
push that merge before any gate would run. #1590 is the cleanest demonstration: its gate had
already passed (two green runs at 21:27) and its steward run finished a minute later, so it
was a GREEN PR that no automation could merge, purely because dev moved four times under it.

**The mechanism is the repo's own merge drivers.** They are local git config, so GitHub's
server-side merge never runs them; a branch that merges `dev` cleanly in a clone still reads
`dirty` to the API. A dirty PR has no merge ref, so the `pull_request` gate never fires, so
it can never become clean. The lap says `REAL CONFLICT — left alone` and stops on a branch
that has no conflict at all.

**A `hold` label looks identical from outside** — dirty plus zero check runs — and was twice
mistaken for this deadlock on 2026-09-20 (#1533, #1576). Whatever clears this must read
labels before declaring a PR stuck.

---

## DEMONSTRATED, 2026-09-21 — on a reconstructed deadlock, not on the workflow files

Acceptance 4 asks for the deadlock to be RECONSTRUCTED and the zero-check state shown
before and after. It was, against the live API.

**The reconstruction.** Branch `steward/pr-stuck-probe`, cut from `dev~12`, rewriting the
exact two lines of `docs/RESEARCH/1835_town_model.md` that `dev` had rewritten under it —
PR **#1599**. Two earlier shapes were tried and REJECTED BY THE MEASUREMENT rather than
by argument, which is worth recording because both look like conflicts and are not:

| probe | GitHub's verdict |
|---|---|
| a line inserted at the top of `QUEUE.md` | `mergeable: true` — a three-way merge reconciled it |
| every non-blank line of `LIBERTIES.md` annotated | `mergeable: true` — `dev`'s own edits were elsewhere in the file |
| the same two lines `dev` rewrote | **`mergeable: false`, `mergeable_state: dirty`** |

Only the third is the deadlock. "Touched a file `dev` touched" is not enough, which is the
same lesson the ticket already records about `dirty` + zero checks not being a diagnosis.

**BEFORE** — head `ec34caec`, read from the API:

```
state=dirty   check-runs=0   commit-statuses=0   labels=[]   comments=0
```

Zero check runs, and nothing anywhere reporting it. The `pull_request` gate never started,
exactly as step 2 of the cycle above says it cannot.

**AFTER** — one run of `.github/steward/pr-stuck.sh`:

```
#1599  STUCK — dirty, 0 check run(s), 0m old, and the branch names no ticket, so no claim can be read
     labelled `stuck`
     said so on the PR

labels=[stuck]   comments=1
```

Run again on the same head: `already said so on this head`, and the comment count stays 1.

**AND THE REFUSALS, on the real queue in the same sweep** — this is the half that matters
more, because every one of these wears the deadlock's shape:

```
#1599  STUCK — dirty, 0 check run(s)
#1598  STUCK — dirty, 1 check run(s), claim/t-1466 names a run that has completed
#1596  held — the owner parked this on purpose; not a deadlock however much it looks like one
#1588  held — …
#1576  held — …
```

Three held pull requests, each `dirty` with few or no checks, each left alone — #1576 is
one of the two the ticket records being mistaken for this deadlock on 2026-09-20. And at
the real 45-minute floor the same sweep reports **nothing at all**, because #1599 and #1598
had both been pushed minutes earlier and the lap had not had its turn:

```
PR stuck: stuck=0 held=3 mid-run=0 too-young=2 moving=0 unlabelled=0
```

**THE READING, as acceptance 1 requires it to be written down: LOUD, not gated.** The other
option was to dispatch the gate for the branch. It was rejected on merit. A dispatched run
gates the BRANCH, not the merge result, and attaches a `gate` check run to the PR's head
sha — so a REQUIRED check would be satisfied by a verdict about a tree that is not the one
that would land. And it still would not merge: `dirty` is not `clean`. A green tick that
means less than the empty space it replaces is worse than a report.

**Acceptance 2 — T-1288 is preserved and not merely left alone.** `chicago-4d-check.yml`'s
triggers are not touched by this ticket, nothing here produces a check run on any head sha,
and `test_pr_stuck.mjs` case 15 is a drift guard that fails if the `branches: [dev, main]`
filter is ever reached for. The count T-1288 measured is unchanged because the trigger it
measured is unchanged.

**Acceptance 3** — the lap's `REAL CONFLICT — left alone` is untouched. **Acceptance 4b** —
the liveness check is the one the ticket specifies: the branch's `claim/t-nnnn` marker names
its run and GitHub is asked whether that run is still going; anything unreadable inside the
three hours `ticket.mjs` already calls a run's life is treated as ALIVE. **Acceptance 5** —
the hand path is in the comment the PR receives and in `docs/PIPELINE.md` § When a pull
request will not move.

Found while being written, and fixed: GNU `date -u -d "" +%s` does not fail, it answers
midnight today at exit 0. An unreadable timestamp therefore read as a few hours old, and
after 00:45 UTC that is old enough for the reporter to declare a pull request stuck on no
evidence at all. `to_epoch` now checks the shape before trusting `date` with it.
