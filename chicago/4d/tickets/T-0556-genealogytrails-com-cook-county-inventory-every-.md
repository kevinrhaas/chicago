---
id: T-0556
title: genealogytrails.com Cook County: inventory every section of the site, grade what it holds for 1835 Chicago, and split the extraction of residents, households, businesses, structures and occupations into tickets
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 705
claimed_by: run 9/3/2026, 11:15:05 AM CT
blocked_on: null
needs_bake: false
---

genealogytrails.com Cook County: inventory every section of the site, grade what it holds for 1835 Chicago, and split the extraction of residents, households, businesses, structures and occupations into tickets.

**The owner's ask, verbatim (2026-09-03):** "And this entire site has useful information so include a ticket to
assess and add information from here too https://genealogytrails.com/ill/cook/index.htm".

**What the site is.** Genealogy Trails' Cook County, Illinois pages: volunteer transcriptions of county records
and printed histories, section by section — the kind of site that holds early settlers' lists, biographies,
marriages from 1831, births and deaths, cemetery readings, census indexes, church records, Black Hawk War rolls,
newspaper extracts, tax and land lists, wills. Which of those it actually holds for Cook County, and how much of
each is 1830s, is exactly what this ticket finds out: the session that filed it could not fetch the site (its
proxy answers an empty page), so the inventory is yours to make from the index page down.

**Phase 1 — ASSESS (this ticket).** Walk the index and every section it links. For each section write one row
in `data/research/genealogytrails/inventory.json`: URL, what it transcribes, the ORIGINAL it derives from (the
site usually names it — a county history, a newspaper, a record book), the era it covers, a count of 1830s
items, and a grade for 1835 Chicago (a transcription is a pointer to its original: cite the original where it is
named, the page where it is not). A README says what the site is good for and what it is not. Cache every page
you read under `text/`.

**Phase 2 — EXTRACT, as split tickets.** Every section worth reading becomes a piece via
`node tools/ticket.mjs split T-0556 "…" "…"` so the pieces keep this place in the queue — residents and
households from the settlers' lists and biographies, businesses and occupations from the same, structures and
streets from the histories, marriages and deaths as dating evidence for people already attested. Each piece
carries the T-0492 shape, source records for the originals, `describes_date` on everything, and the ladder for
any grade.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `inventory.json` covers every section the index links, none skipped silently; the README states the grades.
- The split filed with one piece per section worth reading, each with a stated acceptance; the pieces hold this
  ticket's place in the queue.
- Anything read in passing that is a town finding is in `claims.json` with quote and locator, now, not later.

**Links:** T-0492 (shape) · T-0513 (consolidation — waits on this and its pieces) · the repo's existing
Genealogy Trails-genre sources in `data/sources/` (Kane, Racine and Will county old-settler pieces) for the
citation shape.

**This is overall expansion, not a residents-only pass.** The owner's words, 2026-09-03: "this is overall
expansion because while you are parsing for residents and household people you might as well improve the
business and structure and occupation and other surrounding data and attributes that will help us render the
most complete reconstruction possible of chicago 1835." So every person this source yields is read WITH the
trade, the business, the street or lot, the building and the year it carries — and each of those goes to the
layer it belongs to (residents, households, `businesses`, structures, `claims.json` town findings with
`town_finding: true`, verbatim quote and locator), under the research-domain shape T-0492 fixed. Later
evidence stays date-flagged (`describes_date`), and under the ratified ladder (quoted in T-0513) a later
source alone never makes an 1835 resident — it corroborates, enriches and dates. No IPUMS serial is minted
here; nothing here regrades a person without the ladder's test being stated on the record.

**PHASE 1 DONE, 2026-09-03 — what the assessment found.** The runner CAN fetch the site (the
session that filed this ticket could not; its proxy answered an empty page), so the inventory was
made from the index down. Delivered in the splitting PR:

- `data/research/genealogytrails/inventory.json` — all **22** sections the county index links,
  none skipped, with 12 leaf-page rows under them; `text/` holds the **40** pages read, `html/`
  holds the index raw so the coverage can be gated rather than trusted.
- `tools/read_genealogytrails.py --check | --self-test`, wired into `tools/check.sh`. Ten
  assertions, all proven to fire; the load-bearing one re-extracts the county index's links and
  refuses an inventory that has no row for one of them.
- `claims/town_findings_genealogytrails.json` — the five findings read in passing, each with a
  verbatim quote the gate rebuilds, and in two cases the reason a tempting merge was refused.
- `README.md` — what the site is good for and what it is not.

**The grades, in one line.** Four sections A, four B, eight C, six D. The site's own narrative
history of Chicago begins at INCORPORATION IN 1837, which is the most useful negative finding here:
the town of 1835 is reachable through this site only through its lists, never through its prose.

**The site holds three COMPLETE Chicago directories free, in text** — 1839, 1843 and Norris's 1844
— with trade and street for nearly every name. When this walk began `data/research/directories/`
was empty; while it was running, **T-0566 (PR #704) read Norris's 1844 in full** off the Internet
Archive, so the 1844 here became a SECOND READING rather than a first, and is filed as one. The
1839 already has an owner in **T-0506**, which calls it "cited from a web transcription and never
extracted" — this is that web transcription, and it is cached. The 1843 had no owner and now does.

**The four 1830s lists this site holds** are the poll and tax lists of 1833-1835 (345 names,
ALREADY READ under T-0493 — do not re-read), 134 Black Hawk War veterans enrolled at Chicago in
1832, 87 St. Cyr marriages of 1834-1839 with their witnesses named, and nine St. Cyr deaths of
1834-1836. The last three became pieces, with Fergus's 1843 directory, his 743 old-settler death
notices, Hurlbut on the fur company, and the 1844 second reading.
