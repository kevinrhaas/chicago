---
id: T-0554
title: The Old Settlers of Chicago: the Calumet Club receptions (1879 on) for residents prior to 1 January 1840, the Tribune's 1882 roll of settlers who died that year, and the Fergus reception lists — research the people and the meetings, add residents with citations
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 706
claimed_by: run 9/3/2026, 10:44:21 AM CT
blocked_on: null
needs_bake: false
---

The Old Settlers of Chicago: the Calumet Club receptions (1879 on) for residents prior to 1 January 1840, the Tribune's 1882 roll of settlers who died that year, and the Fergus reception lists — research the people and the meetings, add residents with citations.

**The owner's ask, verbatim (2026-09-03):** "there was a group called the old settlers club and they have some
names can you research them and their meetings and add residents accordingly make sure you include citations,
add this ticket to the queue with all of the other resident data improvements
https://chicagology.com/goldenage/goldenage063/".

**What the page is.** chicagology's "Golden Age" page 063 compiles Chicago Tribune reporting on the **Calumet
Club's annual Old Settlers' receptions** — the club (Michigan Avenue at Twentieth) invited, from 1879, every
resident of Chicago "prior to 1 January 1840" who was of age, and the Tribune printed the rosters, the speeches
and the deaths since the last meeting. The page carries, among other things, the 1882 reception report with
**John Wentworth's roll of old settlers who died in 1881–82** — Bennett Bailey, Joseph A. Barnes, Mark Beaubien,
Levi D. Boone, Henry Brookes, Peter Button, John Casey, Dennis S. Dewey, Simon Doyle, James Fish, Thomas Q. Gage,
Edward H. Haddock, William A. Hail, Samuel Hoard, William Hickling, Alonzo Huntington, Lathrop Johnson, Benjamin
Jones, Harlow Kimball, Robert M. Mitten, David McKee, Jacob De Witt Merrill, Orrin C. Moody, Luther Nichols, James
Wellington Norris, Seth T. Otis, Levi M. Ousterhoudt, Ebenezer Peck, John P. Reis Jr., George Frederick Rumsey,
Adam Schock, Ezra L. Sherman, James W. Steele, Clemens Rose, William H. Stow, Spencer Warner, Benjamin Waters,
Sextus N. Wilcox, Eli B. Williams, Homer Willmarth — and an interview with **Capt. Thomas S. Eells**, who came in
1832 with Gurdon S. Hubbard. Several of these are already in the residents layer; several are not; none of the
roll's arrival years are on their records yet. chicagology is a pointer (the tier the repo already gives it in
`data/sources/chicagology_*.json`); the evidence is the originals it quotes.

**The meetings are a source series, and that is the first thing to lay out.** The Calumet Club's first
reception (27 May 1879) was printed as a pamphlet — *Reception to the Settlers of Chicago prior to 1840, by the
Calumet Club of Chicago* — with the guest list and each guest's year of arrival, and the Fergus Historical Series
reprinted it; the receptions of 1880 and after were reported in the Tribune with rosters and the year's deaths.
Record every reception you can find as an event with date, venue, host, where its roster is printed, and how
many names it carries (`data/research/old_settlers/receptions.json`); then read the rosters.

**What to do with the names.** For every person on a roster or a death roll: the arrival year the roster gives,
the trade or office it gives, and any statement placing the person in Chicago on or about 1 July 1835. Cross-check
each against the residents layer, the voter lists (T-0493), the 1840 census heads (T-0494/T-0495/T-0496) and the
newspaper extracts before writing anything. Then add or enrich residents **under the ratified ladder**: a
reception roster's "came 1834" is later recollection, corroborating and dating, and it grades exactly as the
ladder says for that class of evidence — never above. Every person written carries the citation to the original
(Tribune issue by date, page and column; or the printed proceedings by page), not to chicagology alone.

**Citations, since the owner asked for them by name.** One source record for the chicagology page (pointer,
`url`, accessed date), one per original it quotes, each with `describes_date`, locator and verbatim quote; every
resident, household, business and claim written here names the source record id it rests on.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `data/research/old_settlers/receptions.json` — every reception found, dated, with where its roster is printed.
- `data/research/old_settlers/people.json` — every name from the rosters and death rolls read, with arrival
  year, trade, the statement that places them (or does not) in 1835, the source id and locator, and the
  ladder grade proposed with its reason.
- Residents added or enriched from it, each with the citation on the record; a count in the PR of added /
  enriched / left out and why.
- Source records for chicagology 063 and each original read; town findings in `claims.json`.
- The 1840 census is later evidence and stays so; nothing here reads it backwards.

**Effort.** This is more than one run if the rosters are long: read chicagology 063 and lay out the receptions
first; if the Fergus reprint and two or more Tribune rosters are in reach, split by reception (`ticket.mjs split`)
so the pieces keep this place in the queue.

**Links:** `data/sources/chicago_old_settlers_hugunin_1883.json` and `old_settlers_bridges_1883.json` (the
repo's existing old-settler sources — same genre, use their shape) · T-0493 (voter lists) · T-0499/T-0500 (the
Fergus volumes, where the reprinted reception proceedings may already be in the OCR) · T-0513 (consolidation —
waits on this) · T-0514/T-0515 (the residents/households write).

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
