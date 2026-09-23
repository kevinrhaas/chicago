---
id: T-1287
title: A split mints its children's ids from the local maximum, so two runs splitting one parent mint the SAME ids for DIFFERENT tickets and the parent's claim lock covers neither
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-18
pr: 1459
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T17:23:00.917Z
claimed_run: null
---

**This is the mechanism behind four of the five duplicate pull requests closed on
2026-09-17**, and the claim lock cannot see it.

`ticket.mjs claim` is a compare-and-swap on a `claim/t-nnnn` marker branch, which is a real
lock and it works. But a SPLIT does not work on the parent — it MINTS CHILDREN, and
`nextIdNum()` reads the local maximum. Two runs that both claim-and-split the same parent are
each reading a `dev` where the other's split has not landed, so both compute the same maximum
and both mint the same ids for entirely different tickets. The parent's lock is held, and
correctly; it protects an id nobody is going to work.

**Measured on `dev` and the closed branches:**

| parent | split by two runs into | collision |
|---|---|---|
| T-0468 | `dev`: T-1242, T-1243 · #1398: its own T-1243 | **same id, two different tickets** |
| T-0473 | `dev`: T-1249–T-1252 · #1401: T-1249–T-1252 | **same four ids** |
| T-1145 | `dev`: T-1229 · #1386: T-1223 | disjoint ids, same work |
| T-1147 | `dev`: T-1237–T-1241 · #1389: T-1230 | disjoint ids, same clauses ¶1/¶8/¶9 |

`dev`'s T-1243 is "Author the e1830_natural terrain spec and generate the 1812 heightfield";
#1398's T-1243 is "The 1812 shoreline: shore_1812_pre_cut gets its own dated trace". One id,
two tickets, two runs, no collision anywhere a lock could catch it.

`resolve_id_collisions.mjs` and `restamp` clean this up AFTERWARDS, at the merge, which is
the expensive end: by then both runs have spent an hour each on the same work and one of them
is thrown away. Four PRs' worth on 2026-09-17 alone.

**THE FIX IS TO LAND THE SPLIT BEFORE ANY CHILD IS WORKED, and it is cheap because a split is
cheap.** A split writes ticket files and queue lines and nothing else — it gates in minutes
and carries no derived layer. So:

1. `split` commits, pushes and opens its own pull request carrying ONLY the split;
2. the parent's claim lock is held until that pull request MERGES, not released at split time
   (T-1145 already made the lock survive a split, 2026-09-17 — this is the other half);
3. only then does the run claim a child and start work.

A second run reading `dev` after that sees the children and their ids, and `claim` refuses
the one that is taken. The cost is one extra merge per split; the saving is an hour of
duplicated work per collision.

**The cheaper interim, if the above is too large for one run:** have `split` take a claim
marker for each child id at mint time. The compare-and-swap already exists and is already
remote, so a second run minting T-1243 is refused by the push before it writes a file. That
does not stop two runs doing the same WORK under different ids (T-1145 and T-1147's shape),
but it does stop two different tickets wearing one id, which is the half that corrupts the
queue.

**Acceptance:** demonstrate the collision in a test before fixing it — two sandboxes, the
same parent, no shared `dev`, both splitting, and assert that today they mint the same id.
Then implement one of the two fixes above and assert the second run is refused. State in the
ticket which fix was taken and why. The existing `test_ticket_claim_split.mjs` sandbox with
its real bare remote is the right harness.


---

## Done — the id is reserved on the remote, not scanned for

**The ticket's own proposal was to land a split before any child is worked.** That is
sound for splits and does nothing for `new`, and by 2026-09-18 `new` was the bigger
source: of five collisions that day, **two came from `split` and three from `new` or
`restamp`**. So the fix is at the mint rather than at the merge.

### What was actually wrong, measured

`nextIdNum` reads the highest id on every origin ref and adds one. **That scan works** —
1,066 refs in 8 s, and it does see ids sitting on other runs' branches. I assumed it was
blind and was wrong; it is not the fault.

The fault is one line further back:

> **A minted id is invisible to every other run until the branch is pushed.**

This session renumbered a ticket to T-1324 and pushed twenty minutes later; #1455 minted
**and merged** its own T-1324 inside that window. No scan could have seen the first — it
existed on one disk. And the fifth collision of the day was *created* by a careful attempt
to dodge the fourth by choosing an id above everything visible. "Above everything visible"
is read-then-write, and any run minting in between wins.

### The change

Minting takes a lock, the same compare-and-swap `claim` has used since T-1145: push an
empty commit to `refs/heads/idlock/t-NNNN` with a lease saying **the ref must not exist**.
Git rejects the loser atomically and the loser steps to the next number. `new`, `split`
and `restamp` all go through it.

**Offline still mints.** An unreachable remote falls back to the scan and says exactly what
was given up; a *rejection* is never mistaken for an unreachable remote. The test suite
runs both paths.

**The markers are swept by possession, not by age** — a claim is a lease that expires with
its run, but a reservation must hold from the mint until the ticket reaches `dev`, which
can be hours and several merges. `claims --sweep` deletes an id lock once the tree carries
that ticket.

### Proof

`test_ticket_claim_split.mjs` cases 21–23: two clones of one bare remote mint at the same
moment and get **T-1146 and T-1147**, both reserved on the remote **before either branch is
pushed** — the exact window that defeated the scan. Under the old code both took T-1146.

### The day this was measured

Five collisions on 2026-09-18, across #1449, #1452, #1454 and #1455. One of them —
`handed_to_the_arrival_pass`, 21 book units from Hubbard, Andreas, Moses and Kirkland —
did not dangle when its id moved: it **silently retargeted** onto a real, open, unrelated
ticket, with every gate green. That is the cost this was always about. A renumber that
misses one hand-authored file does not fail loudly; it points 21 research units at the
wrong owner and says nothing.
