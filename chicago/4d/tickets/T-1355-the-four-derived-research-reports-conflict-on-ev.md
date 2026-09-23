---
id: T-1355
title: The four derived research reports conflict on every merge: decide whether they come off the PR surface the way T-0937 and T-0938 took the board and the mirror, with the reading written down
state: open
epic: META
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The four derived research reports conflict on every merge: decide whether they come off the PR surface the way T-0937 and T-0938 took the board and the mirror, with the reading written down.

**The measurement (2026-09-19).** On `dev`, 342 commits in the week from 2026-09-12.
These four files changed in a large fraction of them:

| file | commits touching it, 09-12 → 09-19 |
|---|---|
| `docs/RESEARCH/research-spend-ledger-2026-09-15.md` | 38 |
| `data/research/research_spend_ledger.json.gz` | 33 |
| `docs/RESEARCH/research-signoff-2026-09.md` | 30 |
| `docs/RESEARCH/research-closing-audit-2026-09.md` | 28 |

Every one of them is DERIVED: each is owned by `tools/derived_manifest.json` and
rebuilt by `tools/rederive.mjs`, and `check.sh` refuses the whole layer stale via
`node tools/rederive.mjs --check`. So a branch open for more than a few hours
collides on them, the collision is never about the branch's actual work, and the
resolution is always the same: take a side, then re-derive, because taking a side on
a derived file is only half a resolution.

**Measured on this run, 2026-09-19.** Four PRs (#1480, #1483, #1487, #1488) were
carried to green. #1483 alone paid the lap FOUR times in about ninety minutes — once
against dev, once against the steward lap's own `Lap onto dev: generated files
regenerated, not merged` push onto its branch, once after #1480 merged, once after
#1488 merged — on the same three files each time, with no substantive disagreement in
any of them. #1487 paid it twice.

**What has already been tried, and must not be tried again.** `merge=generated`
(T-0831) was built for exactly this set and kept OURS while printing the rebuild
command. It was RETIRED, and the reason is in `/.gitattributes`: a custom driver only
ever protects a LOCAL `git merge`. GitHub's server-side merge runs no custom driver,
so the platform still calls the branch conflicting and auto-merge can never fire —
measured on PR #940, zero conflicts in a clone with the drivers registered and
"merge conflict" on the identical merge in the UI. A driver is not the answer here
and re-proposing one is re-paying #940.

**What DID work, twice.** Taking the artifacts off the PR surface: `tickets/BOARD.md`
and `tickets/tickets.json` (T-0937), then the whole published mirror
`site/chicago/4d/**` (T-0938). Untracked and .gitignored — a file that is not tracked
cannot conflict, in a clone or on the server — and still written, because every
consumer regenerates before it reads.

**The open question this ticket must answer, not assume.** The precedent set is build
products. These four are NOT build products in the same sense: three of them are
human-readable research reports under `docs/RESEARCH/`, and being readable on GitHub
without a checkout is a real part of their job. Untracking them would buy a clean
merge surface and lose that. So the unit is to DECIDE, with the reading written down,
between at least:

1. **Untrack all four** (the T-0938 move), and if the reports must stay readable,
   publish them into the mirror the way `changelog.js` already ships.
2. **Untrack only `research_spend_ledger.json.gz`** — the one that is genuinely a
   build product and not a document — and leave the three Markdown reports tracked,
   accepting a thinner treadmill.
3. **Keep all four tracked** and accept the lap as the cost of the reports being
   reviewable, having written down that the cost was measured and chosen.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. The decision is made and WRITTEN WHERE THE RULE LIVES — `/.gitignore` beside
   T-0937's and T-0938's reasoning if anything is untracked, `/.gitattributes` if the
   answer is to keep them. A choice with no written reading is not this ticket's
   deliverable; the reasoning is.
2. If anything is untracked: every consumer is shown to regenerate it before reading
   it, the way T-0938 showed `publish.sh` does for the mirror. Naming a consumer that
   does not is a finding of this ticket, not a footnote.
3. The reports do not silently stop being readable. If option 1 is taken, the
   publish path that replaces GitHub-rendered `docs/RESEARCH/` is named and works.
4. The #940 result is restated in the ticket's own words, so the next run does not
   reach for a merge driver a third time.
5. `node tools/rederive.mjs --check` still refuses the layer stale afterwards — the
   gate that made the conflict unnecessary in the first place is not weakened by
   whatever this unit does.
