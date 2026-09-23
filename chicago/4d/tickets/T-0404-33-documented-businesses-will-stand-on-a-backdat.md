---
id: T-0404
title: 33 documented businesses will stand on a backdating liberty and LIBERTIES.md carries none of them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-12
pr: 1174
claimed_by: run 9/12/2026, 12:33:35 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T06:00:46.517Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34675646811
---

T-0356 retired the `first_evidence_after_scene_date` proxy: a business whose first
SURVIVING issue postdates 1835-07-01 is no longer excluded on that fact alone, because the
absence of an earlier printing is not evidence of absence. Thirty-four businesses came back
into the July town, and thirty-three of them stand there on an assumption nothing states:
documented only after the scene date, present on it because ruling 3 says a documented
business is built at the scene date unless contradicted.

`tools/compile_register.py` computes and names that assumption —
`backdating_liberty_required`, the forward twin of `survival_liberty_required` — and clears
it wherever an opening notice is dated on or before the scene date (Wm. H. Taylor's boot
store, 8 July 1834; John Holbrook's, 10 June 1835). `docs/LIBERTIES.md` carries neither
class. This is T-0357's twin and the two should probably be written together: 126 businesses
on a survival liberty, 33 on a backdating one, and a visitor cannot today tell you which of
the town's documented trades rest on either.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `docs/LIBERTIES.md` carries the backdating class, saying what bounds it and what would
  retire it, with the count as measured rather than as quoted here.
- The liberty is reachable from the records it covers, under whatever rule T-0357 settles
  for the survival class — the two must not disagree about how a class-level liberty is
  attached.
- Nothing is upgraded to make the entry shorter: a business restored on this liberty still
  reads as restored on an assumption.

## 2026-09-10 — THE OWNER RULES THE LIBERTY, and this ticket now has its answer

He was asked nothing; he ruled it while reading the December 1835 State census (T-0988):

> "I think we are ok to populate some of those and create them even though the scene date is
> not perfect. or at least head in that direction based on your reasonable inferences. We are
> making a reconstruction and it won't be perfect but we have good inferences like this."

**So the backdating class is permitted, and this ticket stops being a question about whether
and becomes the work of writing it down.** A business documented only after 1835-07-01 may
stand in the July town on the assumption ruling 3 already makes, and `LIBERTIES.md` records
that as a class with its bound and its retirement condition.

**WHAT THE RULING DOES NOT DO, and the entry must say so.** It does not license a business the
sources do not name, and it does not overturn a positive refusal. Both limits were found the
same day in the corpus, testing the ruling against the first three cases it touches:

- **A bank.** The census counts one. `chicago_american_1835_06_27` c001 — **five days before the
  scene date** — has the State Bank of Illinois *determining* to establish a Chicago branch,
  with "the officers of those institutions have not been made known", and Hubbard's branch
  occupied a corner of his warehouse in **1836**. A liberty about DATES cannot outrank a notice
  that says the thing did not yet exist.
- **A lyceum and a reading room.** The census counts them among trades; both are **institutions
  without premises**. The Chicago Lyceum was instituted 2 December 1834 and was meeting in the
  town (`n1844_tf_054`, `bk_fer_050`) with no venue recorded. The Chicago Reading Room's
  directors met at the **Tremont House on 6 July 1835** to work out how to obtain a building
  at $2,500-3,000 by joint stock (`chicago_american_1835_07_11` c001), and seven weeks later
  its books were still "for the present deposited at [?] House" (`..._08_22` c005). **The
  sequence is documented and negative.** Neither adds a roof; both add links.

**Add to this ticket's acceptance:** the entry states that the liberty covers a DATE and never
an ABSENCE, and cites the bank as the worked example of a refusal it does not touch.

