---
id: T-0766
title: The Illinois abbreviation still matches on the wreck of a word — 'Eng.', an author's initials, a France card — and those are the bad keeps the four precision samples have left
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-06
pr: 1001
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T20:06:39.143Z
claimed_run: null
---

The Illinois abbreviation still matches on the wreck of a word — `Eng.`, an author's
initials, a France card — and those are the bad keeps the four precision samples have left.

**Where it was measured.** T-0600 struck 443 stanzas that name a locality and no work, and
re-adjudicated the ten sample rows that went with them. Four bad keeps are left in the 159
adjudicated cards, and all four are the same failure at four different sources: three
strokes and a stop that came out of a word, at a position the surviving rules must not
touch.

- `nbi_v01_2418` — 'Ferne family. — Eng. (Misc. geneal. gleanings. (Waters, H. F.) 1901: 2',
  read as `i ii. gleanings.`. `Eng.` broke into three strokes at the head of the line, and a
  start-of-line stroke followed by a citation is exactly what a WRAPPED locality looks like.
- `nbi_v04_0233` — 'Williams family. — Dorland fam. (Cremer, J. D.) 1898: 121', read as
  `(Grower, LII.)`. The strokes are the author's initials inside the parenthesis.
- `nbi_v04_0065` — a France card under 'Spangen, de, family.', whose body reads
  `,I,,,,II1,,. ,w,1I,_` and names nothing.
- `nbi_v04_0197` — a Watson run divided by state banners that carries MISSOURI, NEW
  HAMPSHIRE, NEW JERSEY and NEW YORK and no Illinois section at all.

Volume 4 supplies three of the four, which is the same thing its 0.513 says: its text layer
is the poor one, and T-0613's tesseract re-read is the ticket that changes the input rather
than the filter.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Whether any rule can separate these from a wrapped locality is answered with a
  measurement over all four volumes, not asserted — and if the answer is no, the ticket
  says so and closes on that, because a filter that costs real Illinois cards to catch four
  is the wrong trade and the sample already names the cost.
- If a rule lands, all four volumes re-extracted and re-parsed in the same commit and the
  precision samples maintained the way T-0600 maintained them.

**Links:** T-0600 (the rules that landed and the four rows that survived them) · T-0613
(volume 4's re-read) · T-0765 (the page-list class) · `precision_sample.json`.
