---
id: T-0826
title: Moses and Kirkland's History of Chicago volume 2 is neither held nor read, and every ABSENT verdict T-0581 recorded is an absence from volume 1 only
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-11
pr: 1106
claimed_by: run 9/10/2026, 11:25:56 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T05:37:27.464Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34561889451
---

Moses and Kirkland's History of Chicago volume 2 is neither held nor read, and every ABSENT verdict T-0581 recorded is an absence from volume 1 only

**Found by T-0581.** That ticket read volume 1 of Moses and Kirkland's *History of Chicago,
Illinois* (1895) and recorded, for each of the forty-nine lead surnames the Newberry index
(T-0570) flagged against the work, what volume 1 says about it — including two ABSENT verdicts
and twenty-one PRESENT BUT LATE ones, at
`data/research/books/moses_kirkland_v1_lead_surnames.json`.

**Those negatives are only half-checked, and the file says so on itself.** The Newberry cards do
not record WHICH volume they cite. A surname absent from volume 1 may be in volume 2, and until
volume 2 is read no absence recorded by T-0581 is a finding about the work — only about half of
it.

Volume 2 is at the pre-existing Internet Archive item `historyofchicagov2mose`. The project owner
uploaded volume 1 to the project's own account in September 2026 as
`historyofchicago01mose_202609` but did not upload volume 2, so the external item is the locator.
Volume 1's text was fetched with `curl -L` from the item's `_djvu.txt` derivative; the same route
should work here, and **the redirect matters** — without `-L` the fetch returns an empty file.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- A source record for volume 2, its own `corpus.json` entry with the committed text's sha256, and
  the text committed byte for byte.
- The same forty-nine lead surnames looked up in volume 2, in the shape T-0581 established, so
  the two files can be read together and every negative becomes a negative about the WORK.
- Anything volume 2 dates and places in Chicago on or before 1835-07-01 written as claims, and
  offered to the residents, households or business layers in those layers' own PRs.
- The folio rule re-derived rather than assumed: volume 1 prints its page numbers into the OCR
  with verso-even / recto-odd parity, and volume 2 may or may not.
