---
id: T-0839
title: One person, several cards: James Allen stands on four, Gurdon Hubbard on six — 39 surname clusters hold 110 cards that may be fewer people. MERGE them — a report is not the deliverable, the merged cards are — losing nothing
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 929
claimed_by: run 9/5/2026, 4:38:26 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T22:51:50.286Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33993456420
---

**The owner, 2026-09-05, reading the households folder on dev:** *"do a review and consolidate of the
residents, like James Allen is almost certainly one record and he is spread across several, don't
lose any data, but consolidation is needed across the residents."*

## Measured on dev at 767020479

Six `hh_allen_*` cards. Four of them are one man — **Lieut. James Allen, U.S. Army, the harbour
engineer** — and the split shows how it happens: each source pass minted the name the way its
source printed it and no pass asked whether the town already had him.

| card | name as minted | grade · rung | sources |
|---|---|---|---|
| `hh_allen_james` | James Allen | attested · G1b | Democrat, IRAD voter lists, Fergus death notices, Fergus 1839 |
| `hh_allen_lieut` | Lieut Allen | attested · G1b | Democrat |
| `hh_allen_lieut_j` | Lieut J Allen | attested · G1b | American 1835 |
| `hh_allen_lieut_james` | Lieut. James Allen · **army_officer** | attested · *(no rung)* | Democrat |

The one card that knows his trade is the one the ladder never reached; the one the ladder graded
best knows nothing about the army. **Merged, he is one attested man with a trade, four sources and
two newspapers behind him. Split, he is four thin men and a town that counts 1,404 people it does
not have.**

He is not alone. A surname-plus-compatible-forename pass over the 1,404 people (a full forename
against the same word, an initial, or a title — nothing looser):

| | |
|---|---|
| surname clusters with two or more compatible cards | **39** |
| cards in them | **110** |

The worst: **Gurdon Saltonstall Hubbard on six** (`hubbard_gurdon`, `_gurdon_s`, `_gordon_s`,
`_g_s`, `_g_t`, `_g`); **Thomas Jefferson Vance Owen on five**; Alexander N. Fullerton on four;
Edmund Stoughton Kimberly on four; Edward H. Haddock on four; Anson Taylor, John S. C. Hogan,
Grenville Temple Sproat, Philip F. W. Peck on three each.

**And some of the 39 are NOT one person**, which is the whole discipline: John H. Kinzie and James
Kinzie are brothers, not a duplicate; Jean Baptiste Beaubien and John S. Beaubien are two men; the
Temple cluster is a household of three. The candidate list is a worklist, never a merge list.

## What exists, and why it did not catch this

`tools/consolidate_resident_evidence.py` clusters *source appearances* into identities and marks
which town cards each identity absorbs (`town_person_ids`, T-0692). T-0723 found the two-card case
and is the narrow sibling of this ticket: *"one identity, two town cards."* But the consolidation's
canonical card is `town[0]` and the merge is never proposed back onto the cards — so a person the
consolidation already knows is one identity stays several cards for ever, and every pass that
spends onto cards (T-0720, the directories, the regrade) spends onto the wrong one or onto all of
them.

## The owner's second instruction, 2026-09-05, which sets the deliverable

*"make the ticket merge those records — research without consolidation is useless."*

So: **the PR that closes this ticket lands merged cards.** The candidates report below is the
ledger the merges are made from and the place refusals are written; it is not an output on its
own. A run that ends at the report has not done this ticket and may not close it.

## The ask — *"don't lose any data"* is the constraint everything else serves

1. **A `--candidates` ledger, then the merges in the same PR.** The ledger: every cluster of town cards the consolidation's
   identity master already joins OR a surname-plus-compatible-forename test joins, with per pair
   the evidence FOR (shared sources, agreeing trade, agreeing dates, a title that fits a documented
   role) and AGAINST (a contradicted forename, two people in one source on one date, a spouse or a
   sibling the sources name). Same standard as the directory forename test T-0515 wrote.
2. **Rule each cluster, in writing, and ACT on the ruling:** MERGE is merged in this PR; DISTINCT is
   written onto both cards so the next pass does not re-ask; UNDECIDED goes to the owner with the
   two readings side by side — and UNDECIDED is the exception that has to earn its place, not the
   default for a cluster nobody looked at hard. Where the evidence is one man with a title, an
   initial and a full name (Allen, Hubbard, Owen, Fullerton, Kimberly, Haddock), it is a MERGE.
3. **A merge loses nothing.** The surviving card takes the UNION of the sources, evidence blocks,
   notes, `directories` blocks, `resident_research`, kinship, old-settler citations and grade
   evidence of every card folded into it; the folded cards are not deleted but become **redirect
   stubs** (`merged_into`, the date, the rule) so every `person_id` any file cites still resolves
   — `data/residents/index.json`, `identity_master.json`, the crosswalks, the smoke cohorts, the
   placed-resident parcels. Run `tools/check.sh`; every consumer must re-derive.
4. **The grade after a merge is the ladder's, re-run** — never the best of the folded grades. Four
   sources on one man may be G1a or G1c where each card alone was G1b; that is the ladder's call
   (`consolidate_resident_evidence.py --build` then `mint_civic_residents.py --build --regrade`).
5. **Then fix the cause**, or this recurs on the next mint: a minting pass must consult the identity
   master before writing a new card, and `--check` must fail when a new card's identity already has
   a canonical card. T-0723's two cases land inside this sweep.
6. James Allen and Gurdon Hubbard are the two demonstrations in the PR body — before and after,
   with what each surviving card gained and the stubs that point at it — and they are two of the
   merges, not the only two. The PR states how many clusters were MERGED, DISTINCT and UNDECIDED,
   and the town's person count before and after.

**Done when** the merges are LANDED — every cluster ruled MERGE is one card, a union with redirect
stubs, and nothing a consumer cites fails to resolve; every other cluster carries a written
DISTINCT or UNDECIDED ruling; the grades are re-derived by the ladder; the minting passes refuse to
re-split an identity; and the town's person count has gone DOWN to the number of people it can
actually name. A report with no merged card behind it does not close this.
