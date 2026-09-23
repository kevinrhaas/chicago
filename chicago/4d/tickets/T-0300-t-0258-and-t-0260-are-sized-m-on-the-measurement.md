---
id: T-0300
title: T-0258 is sized M on the measurement that split T-0259 into six
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: 477
claimed_by: null
blocked_on: null
needs_bake: false
---

T-0259 was sized `M` — one run — and a run that claimed it on 2026-08-28 measured the work
before committing to it and found six runs. It was split into T-0289..T-0294, one month
each, and the first of them (July 1834, five issues) filled a whole run: 129 claims, 298
people, five extraction files.

**T-0258 (November 1833 to June 1834, ~30 issues) carries the same `M` and was sized the
same way.** It is the same paper, the same segmenter, the same interleave, and more issues
than T-0259 had. On the July measurement it is seven runs.

T-0260 had the identical problem and was split the same afternoon, independently, by the
run that read the scene-date issue — into T-0295 (done) and T-0296..T-0298. Two runs
reaching the same conclusion about two sibling tickets on the same day is the argument
that T-0258 is not a special case.

Nothing here says what the right seam is — months worked for T-0259 because the standing
advertisements and the letter lists run in monthly cohorts, and the same is likely true
either side of it. What this ticket asks for is that the sizing be **decided before a run
claims one of them and discovers it mid-flight**, because a run that splits a ticket spends
the front of its budget on bookkeeping rather than on reading.

Note that `ticket.mjs claim` refuses an `L` and `ticket.mjs check` refuses one sitting in
the queue, so the two cannot simply be re-graded `L` and left — they have to be split, or
left `M` on a stated argument that they are not.

**Acceptance:** (state it before working — never weakened to pass)

- T-0258 is either split into pieces each sized on the July measurement, or left as it is
  with the argument written into the ticket.
- Whichever it is, the reasoning names a per-issue cost — claims, pages that have to be
  read, whether a letter list stands in the range — rather than a feeling.
- The children, if any, take the parent's exact place in QUEUE.md. The owner orders that
  file; a split may not re-prioritise.

## Resolved, 2026-08-28 — split, on the measurement this ticket asked for

T-0258 is split into **T-0308..T-0315, one calendar month each**, and the children took the
parent's exact place in QUEUE.md (line 50, at the head of the NEWSPAPERS band, where T-0258
stood). Nothing was re-ranked.

The per-issue cost was counted over the deposit rather than felt, and it is in every child:

| piece | issues | characters | lines | column markers | letter lists |
|---|---|---|---|---|---|
| T-0308 November 1833 | 1 | 133,650 | 3,419 | 25 | 0 |
| T-0309 December 1833 | 5 | 653,071 | 16,659 | 120 | 0 |
| T-0310 January 1834 | 4 | 488,263 | 6,006 | 96 | 1 |
| T-0311 February 1834 | 4 | 465,667 | 15,040 | 96 | 1 |
| T-0312 March 1834 | 3 | 354,692 | 11,556 | 72 | 0 |
| T-0313 April 1834 | 5 | 550,304 | 23,597 | 160 | 2 |
| T-0314 May 1834 | 4 | 455,877 | 18,442 | 128 | 0 |
| T-0315 June 1834 | 4 | 454,800 | 16,859 | 96 | 0 |
| **total** | **30** | **3,556,324** | **111,578** | **793** | **4** |

**The seam is the month, and the argument is T-0289's own measurement**: five issues of July
1834 filled one run and produced 129 claims, 298 people and five extraction files. Thirty
issues at that rate is six to seven runs; no month in this range holds more than five issues;
and standing advertisements and letter lists run in monthly cohorts, so a run's second issue
of a month is cheaper than its first. That is why T-0259 was cut this way and why cutting
T-0258 differently would cost more.

**Three things the count found that a feeling would not have.** Only FOUR of the thirty
issues carry a post-office letter list (1834-01-28, 1834-02-04, 1834-04-23, 1834-04-30), so
the epic's most expensive clause bites on four issues and not thirty — and T-0313 carries two
of them, which is why it is flagged as the piece most likely to need splitting again. There
is no 1834-03-11 in the deposit, so March is three issues and T-0312 must say in
`coverage.json` whether that is a skipped week or a hole in the scan set. And a third of the
range is written in a page-and-column dialect the citation resolver had never been shown —
121 markers invisible — which T-0308 fixed on its way past.

**T-0300's own sizing** was `M`, and it was: this is one run's bookkeeping, done alongside
T-0308.
