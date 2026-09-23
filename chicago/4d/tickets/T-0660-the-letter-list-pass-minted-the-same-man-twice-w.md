---
id: T-0660
title: The letter-list pass minted the same man twice when the paper printed his name in both orders, and the corrected reading now shows it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-18
pr: 1442
claimed_by: run 9/18/2026, 12:27:09 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T06:26:28.685Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35310580474
---

The letter-list pass minted the same man twice when the paper printed his name in both orders, and the corrected reading now shows it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The papers print a name in either order, and until T-0638 this pass read the LAST token
as the family name in both. So `Palmer N. H.` was minted under the surname `h` and
`N. H. Palmer` under `palmer`, and refusal 8 — one household per surname per pass —
never saw them as the same man. Both are in the town.

FOUND WHILE LANDING T-0638, by running the pass's own derivation with the corrected
reading and the old one side by side. With the fix in, 11 candidates the pass used to
accept are refused and 16 it used to refuse are accepted; the refusals are the
collisions the fault had been hiding. Named in that diff, among others:

| the pair | how the paper set it |
|---|---|
| `person_n_h_palmer` / `person_palmer_n_h` | given-first and surname-first, same initials |
| `person_wm_osborn` / `person_osborn_b` | ditto |
| `person_philo_c_mills` / `Mills Joel C.` | different men, but only one may hold `mills` |

**This is not a bug T-0638 introduced — it is one it revealed**, and the reason it was
left alone there is that closing it RETIRES RECORDS. A duplicate household removed is a
person removed from the town: the population counts move, the manifest moves, the
published mirror moves, and every ledger that ever ruled on the retired id has to be
told where the ruling went. That is a different unit of work from a rename, and it
needs the owner's ruling on one question first (below).

## What has to be settled before any of it

Which of a pair survives? The two records are not equal — one may carry a research row,
a crosswalk match or an 1840 bridge that the other does not — so `ticket.mjs` cannot
answer it and neither can a rule that just prefers the earlier id.

**Acceptance:** (state it before working)

1. The full list of pairs, derived (not hand-assembled) by running the letter-list
   pass's `mint()` against the committed tree and reporting every candidate refusal 8
   now catches that it did not before, with the two printings side by side.
2. A stated survivorship rule, applied by a tool, with the losing record RETIRED rather
   than deleted — the id kept resolvable, pointing at the survivor, because ledgers,
   crosswalks and the published mirror cite it.
3. The town's population counts move by exactly the number of pairs closed, and
   `index.json`'s counts, the manifest and the published mirror all move with them.
4. `bash tools/check.sh` green, and no record's grade moves in either direction.

## WHAT THE DERIVATION FOUND (2026-09-04, this run)

`tools/report_letter_list_collisions.py` runs the pass's own `mint()` twice over the
committed tree — the pre-T-0638 reading of a printed name and the corrected one — and
`docs/RESEARCH/letter-list-surname-collisions.md` is its committed output. Three things
came out of it that the ticket could not have known when it was filed.

**1. The collisions are 9, and every one of them carries evidence a retirement would
strand.** Nine candidates the old reading accepted, the corrected reading refuses. All
nine hold a research row, a directory match, or both:

| printed | refused because | holds the surname instead | carries |
|---|---|---|---|
| `Es,Jones, High` | the town already names a Jones | Benjamin Jones, D E Jones, M Jones | T-0481, fergus 1839 |
| `Esther Preston` | surname already minted | Stephen II. Preston | T-0479 |
| `Frederick W. Page` | surname already minted | Elisha S. Page | fergus 1843 |
| `Mason Sabrina A.` | the town already names a Mason | Matthias Mason | T-0482 |
| `Mills Joel C.` | the town already names a Mills | John A Mills, Samuel Mills | T-0482, fergus 1839, fergus 1843 |
| `Norton N. R.` | the town already names a Norton | Nelson R. Norton | T-0483, fergus 1839 |
| `Norton Wm. H.` | the town already names a Norton | Nelson R. Norton | T-0483 |
| `Perry A. 8.` | the town already names a Perry | Calvin Perry | T-0483, fergus 1839, fergus 1843, norris 1844 |
| `Wm. Osborn` | surname already minted | B. Osborn | T-0485, fergus 1839, fergus 1843 |

**2. The pass's own ranking would not keep the better record.** `rank()` orders
single-return names by the NEWEST return, so `Wm. Osborn` — a written given name with a
research row and two directory matches — is retired in favour of `B. Osborn`, a bare
initial that is not in the committed tree at all. And `Joel C. Mills` and `Philo C.
Mills` are two different men; refusal 8 does not say they are one, it says one pass may
assert only one household per family name. Retiring here REMOVES A PERSON rather than
merging a duplicate.

**3. The ticket's own sizing is wrong, and by a lot.** The tree holds 727 letter-list
households; the pass run today derives 658. Only 9 of the 87 retirements are this fault.
Seventy-six are records whose surname the town acquired from a LATER pass — the civic
mint of T-0514 — long after this cohort was minted. That is a different rule and a
different ruling; it is filed separately as T-0691.

## THE RULING THIS NEEDS — the options, so it is one word

**The question: when a standing, researched letter-list record collides with a family
name another record holds, what happens to it?**

* **(a) RETIRE IT, as the ticket's acceptance says.** The nine leave the town, the id
  stays resolvable pointing at the record that holds the surname, and the evidence they
  carry — nine research rows and eleven directory matches — is stranded on a retirement
  record nothing draws. Population −9, and T-0691 then asks the same of 76 more.
* **(b) RETIRE THE WEAKER RECORD, not the later-ranked one.** Same mechanism, but the
  survivor is chosen by evidence — returns, then printings, then the fuller printing,
  then downstream attachment — instead of by which letter was printed last. Keeps `Wm.
  Osborn` over `B. Osborn`. Costs a change to `rank()`, which re-derives the whole
  cohort, so it is more than one run.
* **(c) RETIRE NOTHING; make the pass SAY the collision.** Rule that refusals 7 and 8
  are mint-time rules and do not un-mint a record that already stands. The nine records
  keep their evidence and each gains a block naming the other holder of the surname, so
  a reader sees the collision and why both records are there. Population unchanged, no
  evidence stranded, and T-0691 dissolves.

The loop cannot pick between these: (a) and (b) remove people from the town, and (c)
changes what a refusal means. All three are implementable in one run once the ruling is
made. `ticket.mjs unblock T-0660` appends this at the QUEUE bottom — it belongs back in
the research band where it was.


## THE OWNER RULED: (c), 2026-09-18

> "go with c"

**Refusals 7 and 8 are MINT-TIME rules. They do not un-mint a record that already
stands.** Nothing is retired. The nine records keep their evidence, and each gains a block
naming the other holder of the surname so a reader sees the collision and why both records
are there.

**What this settles, in the ruling's own terms:**

* population is **unchanged** — no person leaves the town;
* the nine research rows and eleven directory matches are **not stranded**;
* **T-0691 dissolves.** Its whole subject was what to do about 76 letter-list households
  out of step with their own pass — 727 in the tree against 658 derived. Under this ruling
  they are not out of step: a standing record is not un-minted by a mint-time refusal. What
  survives of T-0691 is its acceptance 1, wiring `--check` into `check.sh`, and that can now
  ship because the check is no longer red by construction.
* `rank()` is **not** changed, so the cohort is not re-derived. That was (b)'s cost and this
  ruling does not pay it.

**What the implementing run must do, and must NOT do.** It writes the collision block on
each of the nine, changes the pass so a collision is SAID rather than acted on, and wires
T-0691's check. **It retires nobody and it re-ranks nothing** — if the work starts to look
like either, that is the wrong branch and it should stop and say so.

This unblocks T-0660, T-0691 and T-1144, which is the queue's second row and had been
correctly skipped by every run since the header told them to wait for this.
