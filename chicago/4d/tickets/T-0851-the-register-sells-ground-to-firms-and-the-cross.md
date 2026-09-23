---
id: T-0851
title: The register sells ground to FIRMS and the crosswalk can only propose people: A. Garrett & Co. entered eighty acres and no record carries it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-10
pr: 1055
claimed_by: run 9/10/2026, 1:56:27 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T07:29:11.677Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34446953304
---

The register sells ground to FIRMS and the crosswalk can only propose people: A. Garrett & Co. entered eighty acres and no record carries it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. A partnership is recognised from the REGISTER'S OWN WORDS, not from a list of names:
   the conjunction it prints before its abbreviation for company. Capacity words — `AS`,
   `AGENT`, `TRUSTEE`, `HEIRS`, `OF` — are explicitly NOT a partnership style, because a
   man buying as an agent or an heir is still a man and the page names him.
2. No firm reaches `matches[]`. Every one is refused against every person, by rule and
   not by hand, and the refusal names what carries the sale instead.
3. The reading is not lost with the proposal: a `firm_purchasers[]` block carries what
   the house bought — records, tract, acres, price, dates, the Residence column — and
   the ONE partner the register names, put to the same forename rule and carried at the
   grade that rule gives it, stated as a proposal about the PARTNER'S NAME and not about
   a purchase by him. Silent partners are recorded as silent, never proposed.
4. A firm reads back as a firm. `normalize_name` stops producing `A Et Co Garrett`.
5. Any card that had a firm's entry written onto it as a person's is re-derived, and
   what moved is itemised.
6. A firm the reading finds that nobody has declared FAILS the build, so a new deposit
   carrying one stops for a human instead of going onto no card at all.
7. `bash tools/check.sh` green; the hand ruling this rule absorbs is retired in writing
   rather than deleted.

**What it found and what moved.**

* Two firms on 953 rows: `GARRETT A ET CO` (ls0693 — 80 acres, W2SW of sec 33 in
  T38N R14E, $100, 1 December 1835) and `PRUYNE P AND CO` (ls0322 — block 97 of the
  school section, 3.27 acres, $310, 22 October 1833).
* **The second one was never refused at all.** Peter Pruyne's card said the register
  enters *this person* six times, one of them as the firm, and counted the firm's acres
  and dollars among his own: 6 entries, 171.10 acres, $713.79. It now reads 5 entries,
  167.83 acres, $403.79. That is the defect this ticket names, found on a spelling the
  ticket did not mention — `GARRETT A ET CO` had been caught by hand in T-0700 and
  `PRUYNE P AND CO` had not, which is precisely what a hand ruling on one spelling
  cannot do.
* A. Garrett & Co.'s eighty acres are now carried by a reading. Nothing places the firm
  in the town, on the tract, or in the business layer; the identification of the house
  with the town's A. Garrett the auctioneer is probably right and is **not** what was
  refused — what is refused is spending a partnership's entry as a person's.
* `data/research/land_sales/README.md` § *The register sells ground to FIRMS* is the
  written form of all of this. The T-0700 hand ruling moves to `retired[]` in
  `resident_rulings.json` with the date, the ticket and the reason, because the argument
  is what the rule was written from.

