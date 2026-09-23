---
id: T-0962
title: measure_research_spend.py's second hop cannot see a resident_crosswalk: census_1840 read 27 head rulings as fully spent while 15 of the 27 cards had never been told
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-10
pr: 1049
claimed_by: run 9/10/2026, 12:07:19 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T05:20:25.818Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34439477799
---

measure_research_spend.py's second hop cannot see a resident_crosswalk: census_1840 read 27 head rulings as fully spent while 15 of the 27 cards had never been told.

**Acceptance:** the second hop counts every person-reaching ruling in a registered domain's
crosswalks whatever container it is filed in; the report is re-run; and whatever red that
uncovers is recorded as the true figure, with the reason, rather than tuned away.

**WHAT IT FOUND, and the correction the ticket itself needed** (2026-09-10, PR below).

*The diagnosis above is wrong.* The hop reads `resident_crosswalk.json` and always has —
`is_crosswalk()` is a substring test. Running `577c2f6f5`'s own tool over `577c2f6f5`'s own
tree reproduces `27 reached / 27 judgeable / 27 written` **out of that file's `heads`**: 12
`matched` + 15 `candidate` = the 27. They were not a different 27; they were those 27, seen and
passed. What passed them is the FILE-LEVEL SOURCE FALLBACK — heads carrying empty
`discriminators` are judged against the one source id at the top of the file, which the cards
already cited from the earlier bridge pass. That fault is real, covers 817 of the town's 1,364
person-reaching rulings, and is now T-0989.

*The blind spot that WAS there,* found by asking the ticket's question of every container
rather than of one file: `MATCH_CONTAINERS` held `matches` and `merges` and not `matched`.
`church/second_presbyterian_crosswalk.json` files its 82 adjudicated roll members under
`matched`. The hop did not report them unwritten — it did not report **church** at all, and an
absent domain reads as a domain with nothing to answer for. Widened, and the red is true:
**church 82 reached, 82 judgeable, 0 on a card**, confirmed independently — not one resident
record in the town cites `second_presbyterian_chicago_1892`. Recorded as church's write ceiling
with the reason; T-0992 spends it.

*And the price of the widening, paid in the same commit:* a container may no longer overrule a
ruling that states its own verdict, or census_1830's sixteen `earlier_evidence` rows filed
under `matched` would have been counted as matches — coverage bought with a false reading. Both
halves are gated by assertions proved to fire when reverted.

**Measured on `dev` at `577c2f6f5`, 2026-09-07, while landing T-0698.** The meter's second
hop is the instrument that catches a ruling naming a person whose CARD has not learned it —
it is what stopped T-0670. It reported `census_1840` as **27 reached, 27 judgeable, 27 on a
card, 0 unwritten** at the same moment that **15 of those 27 cards carried no mention of the
1840 census at all**, seven of them MATCHES (Philo Carpenter, John Calhoun, Ira Couch,
George W. Dole, William H. Stow, John Davis, Edward A. Rogers).

**Why.** The hop reads the domain's `crosswalk.json` — the spelling-pair rulings — and never
reads `resident_crosswalk.json`, which is where the head-to-person adjudications live. The 27
it counted were a different 27. So the domain's per-person rulings were invisible to the one
gate whose job is to see them, and stayed invisible under a `--check` that was green.

**This is a class, not an instance.** T-0698 spent census_1840's heads by hand
(`tools/spend_census_1840_heads.py`, gated in its own commit), which fixes this domain and
nothing else. Every other domain holding a `resident_crosswalk.json` — land_sales,
directories, civic, church, books, old_settlers — is measured by the same blind hop.

**The ask.** Make the second hop read `resident_crosswalk.json`'s `matched` and `candidate`
rulings alongside `crosswalk.json`'s, for every registered domain; then re-measure and report
what it finds. Expect it to go red somewhere, and expect that red to be true — the ceilings
were set against a count that was missing this whole class of ruling, so raising or spending
is a ruling in itself and belongs to whoever takes it.

**Links:** T-0698 (found it; spent census_1840) · T-0670 (stopped by the hop when it could
still see one ruling) · T-0714 (gated the crosswalk's `--check`) ·
`tools/measure_research_spend.py` · `tools/spend_census_1840_heads.py`.
