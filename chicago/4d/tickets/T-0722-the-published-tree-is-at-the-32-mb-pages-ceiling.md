---
id: T-0722
title: The published tree is at the 32 MB Pages ceiling on dev alone, so any PR that adds a byte cannot go green
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 836
claimed_by: run 9/4/2026, 10:30:40 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T20:03:55.015Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33941748580
---

The published tree is at the 32 MB Pages ceiling on dev alone, so any PR that adds a byte cannot go green.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0693 (PR #834), 2026-09-05, which cannot merge because of it.**

`tools/validate.py` fails the dataset step with:

```
FAIL  site: published tree is 32.1 MB, over the 32 MB budget — GitHub Pages
      cannot serve Git LFS objects, so this has to stay lean
```

## The measurement, and why it is not one PR's fault

Blob bytes under `site/chicago/4d/`, measured with `git ls-tree -r -l`:

| tree | size |
|---|---|
| `origin/dev` alone | **31.99 MB** |
| dev + T-0693 (97 person notes, ~60 KB) | 32.05 MB |

**dev has consumed the entire budget by itself.** T-0693 adds 0.06 MB of prose to
person records and is merely the straw. Any PR that adds a byte to the mirror — a
changelog entry alone is a few KB — now fails the gate, so this is not a T-0693
problem, it is a queue-wide stop.

## Why it must not be closed by shrinking whatever PR hits it

The tempting fix is for each blocked PR to trim its own contribution. That is how a
budget gets paid for by the honesty of the record: T-0693's notes are provenance —
the trade, the year and the source an absence is dated against — and shortening them
to buy 60 KB would be exactly the wrong trade. The ceiling needs a real answer, once.

## The ask

1. **Say where the 32 MB actually is.** A report over `site/chicago/4d/` by directory
   and by file type — GLBs against JSON against textures — so the decision is made on
   numbers. It has never been printed.
2. **Decide what the mirror owes a visitor.** The likely candidates are the baked GLBs
   and any published research JSON the walkthrough does not read at runtime; the second
   category, if it exists, is free to drop.
3. **Give the gate some headroom rather than landing exactly on 32.** A budget with no
   slack fails the next PR either way.
4. **Check whether the ceiling is real at 32.** The note cites Pages' inability to serve
   LFS objects, not a documented 32 MB site limit — worth confirming what the number is
   defending before anything is deleted for it.

**Done when** the published tree is back under the budget with room to grow, the report
that says where the bytes are is committed, and `./tools/check.sh` passes on dev.

---

## CLOSED 2026-09-05 by T-0807 — answered by PR #836, which the ticket record never recorded

#836, "the mirror was shipping the changelog twice — publish it once, and say where the
32 MB is", merged at 16:07:50Z and answers this ticket's first two asks directly:

- **Ask 1, the report that has never been printed:** `docs/SITE-BUDGET.md` is committed —
  the published tree by directory and by kind, GLBs against JSON against textures.
- **Ask 2, what the mirror owes a visitor:** the changelog was being published twice.
  `site/chicago/4d/walk/js/changelog.js` is now an 898-byte re-export of the single copy
  at `site/chicago/4d/js/changelog.js`, which is the contract path Manager and the
  launcher parse and which did not move.
- **Ask 3, headroom:** answered by the 32 -> 36 re-budget in #823 (T-0593). The tree
  measures 31,889,319 bytes = 30.41 MiB of 36, so 5.59 MiB of slack.
- **Ask 4, whether the ceiling is real at 32:** answered in the note above
  `SITE_BUDGET_MB` in `tools/validate.py` — Pages allows 1 GB a site with a 100 MB
  per-file cap, the LFS clause is about FORMAT not size, and 32 was this project's own
  discipline rather than a platform edge.

This ticket and **T-0803** are the same stop filed twice, four hours apart; both close
here. The refusal both of them wrote down — that the budget must never be met by shrinking
a note, because the notes are the product — was honoured: nothing was trimmed to fit, a
duplicate was removed and the number was re-set on purpose.
