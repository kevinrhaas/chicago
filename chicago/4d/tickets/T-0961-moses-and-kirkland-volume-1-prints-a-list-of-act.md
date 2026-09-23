---
id: T-0961
title: Moses and Kirkland volume 1 prints a LIST OF ACTUAL SETTLERS AT CHICAGO PRIOR TO 1830 with nativity, year and remarks columns, and T-0581 found it without transcribing it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-10
pr: 1078
claimed_by: run 9/10/2026, 11:55:30 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T17:46:25.420Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34504662950
---

Moses and Kirkland volume 1 prints a LIST OF ACTUAL SETTLERS AT CHICAGO PRIOR TO 1830 with nativity, year and remarks columns, and T-0581 found it without transcribing it

Moses and Kirkland, *History of Chicago, Illinois*, vol. 1 (1895), printed pages 78-79,
carries a table headed **LIST OF ACTUAL SETTLERS AT CHICAGO, PRIOR TO 1830** with the columns
NAME / NATIVITY / YEAR / REMARKS. It runs about thirty rows, from "Ament, Edward G." across the
page break, and the remarks column records taxes paid in 1825 and votes cast in 1826, 1828 and
1830 person by person.

**Found by T-0581**, which recorded the list's existence and the RULE it was built on — that it
"contains the names of all those who are known to have had a residence at the settlement,
nearly all of whom paid taxes in 1825 and voted in 1826", and that Gurdon S. Hubbard is
deliberately excluded because he "did not take up a permanent residence until 1832" — as claim
`bk_mose1_014`, and did NOT transcribe the table. That was a scope decision, not an oversight: a
roster with nativity and arrival year per person is a records-shaped dataset, and reading it is
its own demonstration.

The text is already committed at
`data/research/books/text/moses_kirkland_history_of_chicago_v1.txt`, lines 10783 onwards, so no
fetch is needed. The list credits Hurlbut's *Chicago Antiquities* pages 37-8 three lines above
it; this project holds Hurlbut at `text/hurlbut_chicago_antiquities_28_36.txt`, pages 28 to 36,
which stops one page short of the cited run — so the SOURCE of the list is very nearly in hand
and worth fetching alongside.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Every row transcribed into the `books` domain in its committed shape, with nativity, year and
  remarks as separate fields and the verbatim text the gate rebuilds from the committed file.
- The rows crosswalked against `data/residents/` under this domain's rules — merges with a rule
  naming both spellings, refusals stated as explicitly as merges.
- What the remarks column does and does not license said plainly: paying tax in 1825 and voting
  in 1826 are civic acts and are not, on their own, a residence on 1835-07-01.
- Hurlbut pages 37-8 fetched and compared, or the reason it was not, stated in the PR.
