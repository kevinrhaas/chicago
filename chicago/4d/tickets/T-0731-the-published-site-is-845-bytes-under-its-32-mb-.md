---
id: T-0731
title: The published site is 845 bytes under its 32 MB budget on dev, so the next changelog entry fails the gate
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
closed_at: 2026-09-05T20:03:55.280Z
claimed_run: null
---

The published site is 845 bytes under its 32 MB budget on dev, so the next changelog entry
fails the gate.

**The measurement.** `site/chicago/4d/` on `origin/dev` at 1e9108aa is 33,553,587 bytes
against `validate.py`'s `SITE_BUDGET_MB = 32` (33,554,432). That is **845 bytes of
headroom**, and `run_site_check` reports it as "32.00 MB of 32 MB budget" — a PASS printed
one rounding away from a FAIL, which is why nobody has seen it coming.

**Why every PR now trips it.** The changelog is a contract: every user-visible change ships
an entry, `publish.sh` mirrors `renderers/web/js/changelog.js` to BOTH
`site/chicago/4d/js/changelog.js` and `site/chicago/4d/walk/js/changelog.js`, and the file
is already 1.37 MB — so a single ordinary entry costs about **8 KB of site tree**, ten
times the remaining headroom. T-0597 measured it: an entry of four items plus two edited
household records put the tree at 33,557,759 bytes and turned the gate red on a change
that touched two people's cards.

**What it is not.** Not a data problem. `site/chicago/4d/data/` is 30.8 MB of the 32 and
has grown honestly. The cheap 2.75 MB sitting in front of anyone who wants it is the
changelog, shipped twice and in full: 543 entries, every one of them, fetched by a browser
that opens the What's-new tab to read the newest three.

**Candidate readings, none of them chosen here:**
- Split the changelog: a small recent literal the tab imports, an archive fetched on
  demand. `js/changelog.js` is a fleet contract path Manager and the launcher parse, so
  whatever moves, that URL must not.
- Stop shipping the second copy. `walk/js/changelog.js` exists because the walkthrough
  cannot import from its own publish mirror; that is a real constraint and may have a
  cheaper answer than a duplicate.
- Raise `SITE_BUDGET_MB`, having first established what GitHub Pages actually costs at that
  size. A budget moved to make a red go away is not a budget.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `origin/dev` has enough headroom that a normal changelog entry plus a normal data change
  passes `run_site_check` — state the number, and state how many entries of headroom it
  buys, so the next person knows when this comes back.
- Whatever is done, `site/chicago/4d/js/changelog.js` still resolves and still parses for
  Manager's ingest, and the What's-new tab still reads the newest entries.
- `tools/check.sh` green on the site check.

**Links:** T-0597 (which measured it) · `tools/validate.py` `run_site_check` ·
`tools/publish.sh` · the fleet changelog contract in `docs/SHELL-API.md`.
