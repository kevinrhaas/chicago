---
id: T-0364
title: Two byte-identical copies of changelog.js are 7.2 per cent of the published payload, and they grow on every release
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---
Two byte-identical copies of changelog.js are 7.2 per cent of the published payload, and they grow on every release.

Found by **T-0317** on 2026-08-29, which is the run that exhausted the 25 MB payload budget and
raised it (`tools/validate.py` § SITE_BUDGET_MB, 25 -> 28, with the reasoning written there). This
ticket is the question that raise deliberately did NOT answer.

**Measured on the published tree, 2026-08-29:**

    dev      26,110,827 bytes   24.901 MB   changelog copies 1,895,776 (7.3 %)
    branch   26,249,226 bytes   25.033 MB   changelog copies 1,899,254 (7.2 %)

`site/chicago/4d/js/changelog.js` and `site/chicago/4d/walk/js/changelog.js` are the same
949,627 bytes twice. Both paths are contracts and neither may simply move: the first is the URL
Manager and the polecat.live launcher parse live, the second is what the walkthrough's What's-new
tab imports out of the copied renderer tree (AGENTS.md § changelog).

**Why it matters more than its size.** It is the only item in the payload that grows on every
RELEASE rather than on every building. A 375-entry file at roughly 2.5 kB an entry adds about
5 kB to the payload per release across the two copies, so the tree grows whether or not the town
does — and a budget raise buys a number of releases rather than a number of buildings.

**What has NOT been established, and should be before anything moves:** whether the walkthrough
can import the `js/` copy across the `walk/` boundary at all (a relative import out of the copied
tree is what the current arrangement exists to avoid), whether a fetch rather than an import is
acceptable to the What's-new tab, and whether the entries older than the What's-new tab shows
need to be in the payload at all. Three routes at least: one copy plus a fetch, a split file with
the recent entries inline and the archive fetched on demand, or leaving it alone with the growth
written down. The third is a legitimate answer.

**Acceptance:** either the payload carries one copy of the changelog rather than two, with both
contract URLs still resolving and `tools/check_published.mjs` green, or the duplication is
recorded as deliberate with the per-release growth rate stated where the budget is defined so the
next raise is not a surprise. Never by moving a contract URL.

**Links:** T-0317 (found it, and the re-budget) - T-0154, T-0155 (the publish/stamp order the two
mirrors come from) - `tools/publish.sh` - `tools/validate.py` § SITE_BUDGET_MB - AGENTS.md §
changelog.
