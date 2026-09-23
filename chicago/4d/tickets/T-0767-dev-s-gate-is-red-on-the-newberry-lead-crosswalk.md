---
id: T-0767
title: dev's gate is red on the Newberry lead crosswalk: 56 leads anchor to cards T-0600 struck, and acquisition_list.json no longer re-derives
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 878
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T12:27:15.528Z
claimed_run: null
---

dev's gate is red on the Newberry lead crosswalk: 56 leads anchor to cards T-0600 struck, and acquisition_list.json no longer re-derives.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured, 2026-09-05, by T-0517's run.** `tools/check.sh` was run on a clean worktree of
`origin/dev` (at the tip after #873 merged) and on this run's branch. Both exit 1, both fail
exactly one step and it is the same step on the same line — the branch introduces none of it:

```
^ every Newberry lead is ruled on, anchored, and re-derives from the cards failed
57 problem(s)
```

Two classes, from `python3 tools/rule_newberry_leads.py --check`:

- **56 leads anchored to a card that is not in the records** — 8 under `refusals`
  (`nbi_v04_0252`, `…0261`, `…0266`, `…0268`, `…0270`, `…0276`, `…0292`, `…0298`) and 48 under
  `ambiguous` across volumes 2 and 3 (`nbi_v02_1887`-`1981`, `nbi_v03_2015`-`2118`).
- **`acquisition_list.json` does not re-derive from the committed cards.**

**The cause is #873 (T-0600), merged 11:12 UTC.** That PR's rules struck 443 stanzas that
named a place and no book, which is right — but `lead_crosswalk.json` and
`acquisition_list.json` still point at card ids that no longer exist. The rulings themselves
are not lost: a refusal or an ambiguity about a card that has been struck is a ruling about
nothing, and the repair is to decide, per lead, whether it goes with its card or re-anchors to
a surviving one. That is a judgement per lead, not a sweep.

**Acceptance:** `python3 tools/rule_newberry_leads.py --check` exits 0 on `dev`, every one of
the 56 leads either withdrawn with its struck card or re-anchored with the reasoning written
down, `acquisition_list.json` re-derived rather than hand-edited, and `./tools/check.sh` back
to exit 0. Not silenced: a lead pointing at a card that is not there must keep failing.

**Why this is filed rather than fixed here.** T-0517 is one unit of work about summarising the
residents and households. This is the Newberry index's crosswalk, it needs a ruling on each of
56 leads, and bundling it into that PR would make one un-revertible commit out of two unrelated
things.
