---
id: T-1373
title: Dev is red at desktop part 12: T-1347's 308 trade households are written outside data/residents/households/, so the People directory counts them and the manifest cannot, and the smoke's count assertion only knows to add the re-admitted
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-20
pr: null
claimed_by: null
blocked_on: Superseded by T-1466, the same failing assertion measured a day later and in full. Both are the People directory's count identity in smoke_renderer.mjs (stated == manifest + readmitted + trades + transients). T-1373 named one unaccounted layer, T-1347's 308 trade households; T-1466 measures the whole gap on dev — 3,228 against 2,269 + 182 + 308 + 307 = 3,066, short by 162 — and covers every layer that mints a person outside data/residents/households/, which is T-1373's own stated acceptance.
needs_bake: false
closed_at: 2026-09-20T23:17:06.088Z
claimed_run: null
---

Dev is red at desktop part 12: T-1347's 308 trade households are written outside data/residents/households/, so the People directory counts them and the manifest cannot, and the smoke's count assertion only knows to add the re-admitted.

**Acceptance:** `SMOKE_VIEWPORT=desktop SMOKE_STAGE=12` is green on dev, with the count
assertion holding the directory to a sum it can actually name — every layer that mints a
person outside `data/residents/households/`, not just the re-admitted.

**Found by** T-1370's run, 2026-09-19, on the first desktop part-12 leg run after
T-1347 (#1503) merged. Both failures are DEV's: that branch mints no person and changes
no byte under `data/residents/`, `renderers/web/js/people.js` or `data/town_census.json`.

```
FAIL desktop 1280x800: the People directory lists the town, and its count is the file's and the manifest's
     — {"rows":80,"api":2626,"file":2626,"stated":2626,"manifest":2144,"readmitted":174}
FAIL desktop 1280x800: the tavern-keeper pill narrows the list to tavern keepers
     — {"all":2626,"matched":8,"pressed":"","offTrade":[],"rows":8,"cleared":2626}
```

**The first, and the arithmetic is exact.** The assertion holds
`stated === manifest + readmitted`: 2,626 against 2,144 + 174 = 2,318. The shortfall is
**308** — precisely the trade households T-1347 minted into
`data/residents/reconstructed_trades/`, a directory that did not exist one commit earlier
(309 files on `origin/dev`, 0 on `origin/dev~1`). The manifest is derived from
`data/residents/households/` and cannot see that layer, which is deliberate and is the same
shape as T-1172's re-admissions — but the assertion was taught about the re-admitted only,
so a THIRD off-manifest layer reads to it as a card that reached the town by an unknown path.
The stage's own `--check` is green; this is the count assertion not knowing about a layer,
not a reproduction failure.

**The second** fails on one clause only: `pressed` is empty, so the pill's `aria-pressed`
never took. Everything else in that check passes — `matched` 8, `rows` 8, no off-trade rows,
`cleared` back to 2,626. Not investigated here.

**Confirming it is dev's, not the branch that found it:** `git diff origin/dev...HEAD` is
empty for `data/residents/`, `people.js` and `town_census.json`, and part 12 was **73 passed,
0 failed** on the same branch before `origin/dev` was merged into it. The only thing that
changed between the green reading and the red one was the merge.

## The second one, investigated (T-1375, 2026-09-19)

`pressed` is empty because **the pill the assertion reaches for no longer exists**.
`renderers/web/js/people.js` offers the TOP TEN trades by count as pills and everything else
through the `More` select; the smoke looks for
`.pill[data-filter="occupation"][aria-pressed="true"]`. T-1347's reconstructed trades and
T-1344's women and children have rewritten that top ten —

    domestic 76 · boarding-house keeper 40 · laundress 34 · carpenter 26 · clerk 26
    labourer 26 · dressmaker 25 · milliner 21 · attorney 15 · merchant 14

— and tavern keeper, with 8, has dropped out of it. `dir.filter('occupation','tavern_keeper')`
still works, which is why the other four clauses of that check pass; only the DOM lookup for a
pill fails, and it fails correctly.

So the fix is not to swap in a trade that happens to be in today's top ten — that is the same
trap one reconstruction stage later. Either drive the row through the `More` select when the
trade is not a pill, or have the smoke pick its trade off `people.json`'s own top ten and
assert against that.

Re-measured on this branch at `sha256:f8037d0f341c23d0`, desktop part 12: the same two
failures and no others, with parts 13 at both viewports green (115 passed, 0 failed each).

## And a FOURTH term is now missing (T-1325's run, 2026-09-19)

The assertion has since been taught about the trade heads and the transients, and it is
red again for the same reason one layer later. Measured on a clean `origin/dev`
(3c1a0dfe) worktree, published, `SMOKE_VIEWPORT=mobile SMOKE_STAGE=12` — and identically
at desktop on a branch over it, so it is not a viewport:

```
FAIL 390x780: the People directory lists the town, and its count is the file's and the manifest's
     — {"stated":3028,"manifest":2144,"readmitted":182,"trades":308,"transients":307}
```

2,144 + 182 + 308 + 307 = **2,941** against 3,028. The shortfall is **87** — exactly the
men T-1376 (#1511, merged 11:28 UTC) carded from the company the 1832 Chicago roll heads
INDIAN, written to `data/reconstruction/1835_native_and_metis.json` and so outside
`data/residents/households/` like the three layers before it.

This is the third time the same identity has gone stale on the same mechanism, which is
the finding: the check enumerates off-manifest layers by hand, so every new cohort is a
silent red until someone adds a term. The fix that ends it is a term DERIVED from what
the directory actually holds — the compiled people rows already carry `resident_subtype`
and `how_known` — rather than a fourth constant beside the other three.

`tools/dev-smoke-state.mjs ask --viewport mobile --stage 12` has part 12 last passing at
2026-09-19T02:04Z, with eleven commits landed on dev since.
