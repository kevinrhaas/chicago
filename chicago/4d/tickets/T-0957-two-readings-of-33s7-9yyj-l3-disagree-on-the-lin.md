---
id: T-0957
title: Two readings of 33S7-9YYJ-L3 disagree on the line count and on the printed footing: 27 lines and 115, or 28 lines and 113
state: withdrawn
epic: PAPERS
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1290
needs_bake: false
closed_at: 2026-09-17T19:18:40.430Z
claimed_run: null
---

`#1015` and `#1014` are two independent passes over the same leaf — 33S7-9YYJ-L3, the 1840
census — and they disagree on three figures at once. #1014 merged; #1015 was parked under
`hold` and is closed by T-0930 with this ticket carrying its reading, so the disagreement
survives the branch.

| | on `dev` (#1014, T-0744) | on `#1015`'s branch |
|---|---|---|
| lines ruled with an entry | **27** | **28** |
| records committed to the page file | **27** | **30** |
| printed footing | **115**, `documented` | **113**, `inferred` |
| lines committed to the closure | 21, summing **71** | 19, summing **111** |
| lines left unread | 6 | 7 |
| the matched-pair figure | six lines carry it; the key reads them as 4s | `total_matched_pair: null`, the pairs not named |
| the 33S7-9YYJ-PC pairing | refusal held by TWO keys, population key unchanged at 115 | `pairing_test: null` |

**What separates them, in the branch's own words.** The 113 rests on the last glyph of the
footing being *"a hook and flag over a descender that ends in a bowl at the bottom-left"* —
the same character the COMMERCE column's printed footing carries, and that column's four
entries fix its own footing at 3. So the branch identifies the glyph against a footing the
leaf itself proves, and reads 113. The 115 rests on `pairing_key_26_50.json`, which read the
same cell in T-0656 and describes three glyphs *"a plain slant; a second plain slant; then a
bowl under a long flat top stroke that runs to the cell's right rule"*, at 10x, and is
`documented`.

**Neither closes the column, and the branch says so** — `"THE COLUMN DOES NOT CLOSE, EITHER
WAY, AND NOTHING HERE IS ADJUSTED TO MAKE IT."` 21 committed lines sum to 71 against 115,
leaving a mean of 7.3 for six unread lines where the committed ones average 3.4; 19 lines
sum to 111 against 113, leaving 2 for seven lines that each carry ink. **The second residual
is the harder one to believe**, and that is a fact about the branch's reading, not about the
leaf.

**Why this is not a stalemate.** The two passes disagree on how many lines the leaf rules,
which is prior to the footing: 27 or 28 is settleable off the image alone at the ruling, and
whichever answer wins constrains the sum. `33S7-9YYJ-L3.json` on `dev` is the record in
force; nothing here amends it.

**Acceptance**

1. The line count is settled off the exposure at the ruling — 27 or 28 — with the extra
   line named and shown, or shown not to exist.
2. The footing glyph is read again against the commerce column's own footing, since that is
   the branch's whole argument, and the answer states which of 115 / 113 the character is.
3. Whichever way it falls, `pairing_key_26_50.json`, the page file's `closure` and the
   33S7-9YYJ-PC refusal are brought into line with each other in the same commit — the
   refusal on `dev` is currently held by a key this ticket may move.
4. If the column still does not close, that stays written down. Nothing is adjusted to make
   it close.

## Folded in from T-0941 (2026-09-10) — the same two-stroke glyph and the same footing dispute on 33S7-9YYJ-L3

*T-0941: 33S7-9YYJ-L3's TOTAL column turns on a two-stroke glyph three readings name three ways: 4 on dev, 11 on #1015, unread on #1013*

**Salvaged from PR #1013 by T-0927, 2026-09-07, before that PR was closed as superseded.**
It was filed there as T-0923; that number was taken on `dev` by another run while #1013
sat open, and the ticket file has never existed on `dev`. Refiled here with the finding
widened, because a second reading has since disagreed a second way.

Three passes have read line 1 of 33S7-9YYJ-L3's TOTAL column and no two of them agree:

| reading | line 1 | confidence | what it says the ink is |
|---|---|---|---|
| `dev`, from PR #1014 | **4** | medium | one 43x55 component plus a 7x15 mark below its right — a matched pair with the two strokes touching, closed with a morphological close |
| PR #1013 | **unread** | — | two parallel slants, the right raised 0.7 px and 27 px right of the left; one glyph by the separation test, and not named |
| PR #1015 (`hold`) | **11** | high | two separate parallel slants with clear paper between them — no crossbar and no loop, so 11 and not a two-stroke 4 |

The disagreement is not confined to line 1. The same glyph decides five more of the
column's six matched pairs on the `dev` reading, and it is what carries `dev`'s committed
sum of 71 over 21 lines against #1015's 111 over 19. The two readings also disagree on the
printed footing itself — 115 on `dev` and on #1013, 113 on #1015 — and on how many lines
the leaf rules with an entry: 27 against 28 over a 30-position grid.

**The measurement that would settle it is not on this leaf.** The leaf carries no
alphabet: there is no line where the same hand writes a figure this project has committed
from another source, so nothing calibrates the two-stroke form against a known 4 or a
known 11. What would settle it is a leaf of the SAME hand with committed line values —
find one, read its two-stroke glyphs against values already held, and bring the key back.

**Acceptance:**

1. A leaf of the same enumerator's hand is named, with committed line values from a source
   other than that leaf's own arithmetic, and the reasoning for calling it the same hand
   is written down.
2. The two-stroke form is read on that leaf against those values, and the key says which
   figure it is — or says plainly that the leaf does not settle it and why.
3. 33S7-9YYJ-L3's line 1 and the other five matched pairs carry the key's verdict, with
   their confidence set by the key rather than by the pass that first wrote them.
4. If the key says 11, the footing question (113 against 115) and the line count (27
   against 28) are re-put, because #1015's reading turns on the same stroke.
5. Nothing is adjusted to make the column close. It does not close on either reading and
   that stays stated.

**Links:** T-0744 · PR #1014 (landed) · PR #1013 (closed by T-0927) · PR #1015 (`hold`) ·
T-0942 · T-0943 · T-0930.

## Folded in from T-0925 (2026-09-10) — its two residuals — a second_readings copy of #1015 and the silent claim --force — belong with the dispute they came from

*T-0925: Three runs read 33S7-9YYJ-L3 on the same morning and their line counts disagree: reconcile PRs #1013, #1014 and #1015 into one reading of the leaf*

Three runs read 33S7-9YYJ-L3 on the same morning and their line counts disagree: reconcile PRs #1013, #1014 and #1015 into one reading of the leaf.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by the run that opened PR #1014, 2026-09-07.** Three steward runs claimed T-0744
within about half an hour of each other and each read 33S7-9YYJ-L3 line by line. All three
PRs are open against `dev`, all three create
`data/research/census_1840/pages/33S7-9YYJ-L3.json`, and git will let exactly one of them
land — the other two become a genuine content conflict the PR lap refuses rather than
resolves. Nothing is corrupted by that; what is lost is the disagreement, if nobody writes
it down.

**They do not agree on the ticket's headline number.**

| PR | branch | line count | the 4-vs-11 figure |
|---|---|---|---|
| #1013 | `steward/t-0744-census-l3-total` | not stated in its title | "a figure that is not 11" |
| #1014 | `steward/t-0744-census-1840-l3-read` | **27** | five of six committed 4 on T-0652's axis metric, one left unread |
| #1015 | `steward/t-0744-census-1840-l3` | **30** | not stated in its title |

**Why the count can differ honestly.** The TOTAL column's ink over the cell's own printed
rules (x 1164-1358) is 40 components, which `read_census_continuation.py` groups into 30 at
dy 45 and 55. #1014 reads those 30 groups as 27 ROWS — a two-part 5 is one figure, not two,
and two marks (12 x 14 at y 1607, 9 x 19 at y 1758) are refused as ink that is not an entry
on the 33S7-9YYJ-FJ precedent. A pass that commits the group count commits 30. So the
disagreement is about what a line IS, not about what the ink is, and it is settleable.

**This is the T-0550/T-0534 shape and it has a precedent here**: two independent readings of
one sheet, kept verbatim in `second_readings/` with a reconciliation ticket asking which is
right. Nothing should be deleted before that comparison is made.

**The cause is worth fixing separately.** `ticket.mjs claim` refuses a ticket a rival branch
carries; the run that opened #1014 passed `--force` because the ticket it had looked at first
(T-0723) had two stale branches, and carried the habit across to a ticket where the refusal
would have been right. `--force` should at least name the branch it is overriding and say
whether that branch has an open PR.

**Acceptance:**

- The three readings are compared cell by cell where they overlap, and ONE reading of
  33S7-9YYJ-L3 stands in `pages/`, with the line count stated and argued.
- Where two passes disagree on a committed figure, the disagreement is recorded — in
  `second_readings/` if the losing reading is worth keeping — and never silently dropped.
- `coverage.json` and `pairing_key_26_50.json` end consistent with whichever reading stands.
- The two PRs that do not land are closed with a comment saying which reading superseded them
  and why, not left conflicting.
- Separately: `claim --force` prints the rival branch and its PR state before it overrides.

**Links:** T-0744 (the ask) - T-0657 (its parent) - T-0656 / `pairing_key_26_50.json` (the
strip measurements all three supersede) - T-0652 / `pages/33S7-9YYJ-8D.json` (the 4-vs-11
discriminator #1014 applies) - T-0802 and T-0857 (the same family: nothing is visible between
runs before a PR merges).
