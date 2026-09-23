---
id: T-1351
title: ticket.mjs done gives the claim back on the assumption its PR merges in minutes, and when the PR cannot merge the ticket is claimable again while the work is invisible: T-1333 was claimed and built twice, 1h43m apart, both runs correct
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-18
pr: 1485
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T00:53:20.192Z
claimed_run: null
---

ticket.mjs done gives the claim back on the assumption its PR merges in minutes, and when the PR cannot merge the ticket is claimable again while the work is invisible: T-1333 was claimed and built twice, 1h43m apart, both runs correct.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. `ticket.mjs done` KEEPS the claim marker, exactly as `split` has since T-1145. The
   marker is collected by AGE — `claims --sweep` deletes anything older than `RUN_HOURS`,
   and the lap runs it — rather than handed back at a moment the run cannot know is safe.
2. The same for `withdraw` and `block`, which carry the identical assumption.
3. A self-test drives the real window: claim, `done`, and then a SECOND run's `claim`
   against the same id must be REFUSED while the marker is young, and must succeed once
   it is older than `RUN_HOURS`.
4. The litter this reintroduces is measured, not assumed: how many markers stand on the
   remote for tickets in a terminal state, and that `claims --sweep` clears them.

## THE ASSUMPTION, IN THE CODE'S OWN WORDS

`split` keeps its claim today because T-1145 cost two runs on 2026-09-17 — two runs split
one ticket into DIFFERENT children, nineteen minutes apart, with colliding ids. The comment
that fix left behind says exactly why `done` was left alone:

    `done` and `withdraw` end a run: rule 7 has its PR merging minutes later, so the
    window where `dev` disagrees is short. A split is the OPPOSITE — the run carries on
    for another hour working a child.

**The window is not short when the PR cannot merge.** That is what happened on 2026-09-18,
and the numbers are the ticket:

    21:02:57Z  run 35389718070 claims T-1333, works it, runs `done --pr 1477`,
               and the release here deletes claim/t-1333 while #1477 is unmerged
    22:10Z     #1477 opens — and cannot gate, because it is `dirty` and GitHub
               builds no merge commit for a conflicted PR
    22:45:27Z  run 35402702816 reads `dev`, where T-1333 is still `open` because
               #1477 has not landed, finds no lock, and claims the same ticket
    23:15Z     #1480 opens — a second, independent implementation

Both runs were correct by every rule as written. Both claims were legitimate: 1h42m30s
apart, comfortably inside `RUN_HOURS`. The lock that exists to stop exactly this had been
handed back by the first run 100 minutes earlier.

**AND THE WORK WAS INVISIBLE FOR ALL OF IT.** The second run could not have seen #1477:
a ticket's `state`, its `pr:` field and its claim all live on the first run's BRANCH until
that branch merges. The queue in `dev` said `open`, and that is the only thing a starting
run reads.

## WHY AGE IS THE RIGHT COLLECTOR AND A HANDBACK IS NOT

A run cannot know when its PR merges. It ends at `done`; the merge happens later, by a lap,
a gate, or a person — and tonight, for some PRs, not for hours. Any handback at `done` is a
bet on that interval, and the bet is lost exactly when the queue is congested, which is
exactly when a duplicate is most expensive.

`RUN_HOURS` already encodes the honest answer: a claim is good for three hours, and a
marker nobody collected is litter that the sweep removes. `split` was moved onto that
footing and has not duplicated since. This puts the other three terminal states there too.

**WHAT IT COSTS, stated plainly:** a ticket whose PR is abandoned stays claimed for up to
three hours instead of being immediately re-offered. That is the designed staleness
behaviour, and it is the cheaper side of the trade — three hours of a ticket nobody picks
up against two runs building the same thing twice.
