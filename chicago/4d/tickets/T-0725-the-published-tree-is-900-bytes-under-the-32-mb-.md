---
id: T-0725
title: The published tree is 900 bytes under the 32 MB ceiling on dev, so the next PR that adds anything at all fails the gate
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: null
claimed_by: null
blocked_on: Superseded, and the fault is measured gone. All five of T-0722, T-0725, T-0731, T-0774 and T-0803 reported the SAME thing within one day — the published tree sitting a few hundred bytes under SITE_BUDGET_MB on dev at 06a0a9ec/1e9108aa, so the next PR to publish anything failed the gate. T-0722 fixed it in PR #836 by publishing changelog.js once instead of twice. Measured on this tree: 30.412 MB of 32, 1.588 MB of headroom, and ZERO pairs of published files over 64 KB with identical bytes — the condition #836's new validate.py rule now gates, so it cannot return the way it arrived. Withdrawn on the owner's instruction of 2026-09-05, 'do it if those tickets are useless now', after checking each one's own claim rather than the band's summary of them.  CORRECTION, same day: this reason first cited "30.412 MB of 32, 1.588 MB of headroom". The 32 came from tools/site_budget.py, which still hardcoded it while tools/validate.py — the gate that actually refuses a merge — had been raised to 36 by T-0593 (#823). The true figures are 30.5 MB of 36 and 5.5 MB of headroom, so the withdrawal stands and stands wider than stated. site_budget.py now reads SITE_BUDGET_MB out of the gate rather than restating it.
needs_bake: false
closed_at: 2026-09-05T20:03:55.145Z
claimed_run: null
---
**Measured 2026-09-04 while gating PR #827 (T-0692).** `validate.py`'s `run_site_check`
sums every file under `site/chicago/4d/` against a hard 32 MB ceiling, and reports over-budget
as an **error**, so `check.sh` fails and the dev gate stops the PR.

| tree | bytes | of 32 MB |
|---|---|---|
| `origin/dev` | 33,553,488 | **31.9991 MB** — 900 bytes of headroom |
| dev + PR #827 | 33,561,196 | 32.0065 MB — 6,808 bytes over |

**The whole of PR #827's published footprint is 7,708 bytes**: one changelog entry and the
four rows its follow-up tickets add to the mirrored `tickets.json`. There is nothing in it
to trim, and trimming it would not help — **the next PR on this lane hits the same wall**,
whatever it contains. Any PR that ships a changelog entry (which the contract requires of
every user-visible change) adds a few kilobytes to the mirror by construction.

**Why it is not a one-off.** `tickets.json` is mirrored in full and grows with every ticket
filed; the changelog grows with every entry. Both are append-only by design and both are
published. The ceiling exists because GitHub Pages cannot serve Git LFS objects, so it
cannot simply be raised without knowing what Pages will actually take.

**The shape of an answer** (for the owner to rule on, not for a run to pick):
- the 30 MB of assets is where the room is, not the 60 KB of text — one asset re-encode
  buys back more than a year of changelog;
- or the mirror stops carrying what the renderer never loads. `tickets.json` is read by
  Manager, not by the walkthrough, and `smoke_budget.mjs --for-diff` already says so in as
  many words: *"the backlog mirror — the renderer never loads it"*;
- or the ceiling moves, with a measurement of what Pages serves, rather than by guess.

**Acceptance:** the published tree is back under the ceiling with stated headroom, and the
gate says how much; whatever is removed from the mirror is shown not to be loaded by the
renderer (or by Manager, for `tickets.json`); and the check reports the margin on every run
so the next approach to the wall is visible before it is a blocked PR rather than after.
