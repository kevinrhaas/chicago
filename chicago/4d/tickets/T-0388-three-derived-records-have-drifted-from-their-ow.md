---
id: T-0388
title: Three derived records have drifted from their own generators on an unmodified dev, so every branch's gate is red
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: the three layers were regenerated in #541 (T-0350) and verify on dev; twin of T-0377
needs_bake: false
closed_at: 2026-09-10T04:20:09.168Z
claimed_run: null
---

Three derived records have drifted from their own generators on an unmodified dev, so every branch's gate is red.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-0336's run on 2026-08-29, on `origin/dev` at 4e213898 with nothing but a
ticket claim on top of it. `tools/check.sh` is RED on three steps and on nothing else:

    the dooryard plantings re-derive from the rule that dealt their stems   FAILED
    the planted poplar rows re-derive from the rule that chose their greens FAILED
    the yard goods re-derive from the rule that chose their frontages       FAILED

Each is the same shape — the committed record no longer matches what its own generator
produces — and each is the gate T-0082 exists to keep: a rule that is not re-run is a
rule nobody is keeping. The three records are
`data/flora/plantings/town_dooryard_plantings.json`,
`data/flora/plantings/town_planted_rows.json` and `data/yard/town_trade_goods.json`.

**Why it matters more than three files.** `chicago-4d-check.yml` IS the dev gate, so
while this stands EVERY branch opened off `dev` is red before it changes a line, and
every run has to prove its own red is inherited before it can merge. That is the cost
T-0215 measured on the smoke, at the gate that is supposed to be the cheap one.

**Not repaired here, deliberately.** Re-running the three generators is one command
each and the diff is small (23 insertions, 76 deletions), but it is not small in the
scene: `town_planted_rows.json` loses 57 lines, which is a poplar row leaving the town.
A row of trees disappearing is a visible change and belongs in a PR that says which row
and why the rule now refuses it — not carried in the margin of an unrelated ticket.

**What the run that takes this has to get right:** say which merge moved the inputs
(the three all read the committed buildings, and `T-0376` put sixteen documented
tradespeople into the town in the commit before this was found), name the row that
goes and the greens that refuse it, and state whether the drift is the rule working or
the rule breaking. Regenerating to green without reading the diff is how a row is lost
silently.

**Acceptance:** the three records re-derive, `check.sh` is green on an unmodified
`dev`, and the PR names every stem and every trade good that moved and why.

---

## THE RED IS GONE — measured 2026-08-29, verify and withdraw

`tools/check.sh` was run on an unmodified `origin/dev` at `9b6e3276`, clean worktree.
All three steps this ticket names now PASS:

```
the dooryard plantings re-derive …    verified 128 dooryard stems across 62 of 144 dwellings
the planted poplar rows re-derive …   verified 2 planted row(s), 8 stems, across 144 dwellings
the yard goods re-derive …            verified 148 object(s) on 26 trading frontage(s)
```

A later merge re-ran the three generators and committed their outputs. **Which merge did
it, and whether the visible consequence this ticket predicted actually happened — a poplar
row leaving the town — is NOT established here**, and that is what the withdrawing run
owes: name the commit, say whether a row left, and confirm a changelog entry was made if
one did. Withdraw with that evidence; do not withdraw on the green alone.

**AND THIS TICKET HAS A TWIN.** T-0377 and T-0388 describe the SAME three failures from
the same cause, filed hours apart by two different runs (T-0376's and T-0336's) that could
not see each other — the collision T-0238 records, this time in `new`, not `claim`. One
withdrawal should close both, and the pair is a second data point for T-0238's rate.
