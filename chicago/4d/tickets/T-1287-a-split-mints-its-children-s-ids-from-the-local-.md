---
id: T-1287
title: A split mints its children's ids from the local maximum, so two runs splitting one parent mint the SAME ids for DIFFERENT tickets and the parent's claim lock covers neither
state: open
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
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
