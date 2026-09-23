---
id: T-0611
title: Fergus 1839, the appendices: the city register, the 1837 charter election and its list of voters for mayor, the Fort Dearborn Addition lot sales and the population table
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: null
claimed_by: run 9/4/2026, 8:05:55 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T13:08:36.571Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33875897472
---

Fergus 1839, the appendices: the city register, the 1837 charter election and its list of
voters for mayor, the Fort Dearborn Addition lot sales and the population table.

**Where this comes from.** T-0506 read the alphabetical directory of *Fergus' Directory of
the City of Chicago, 1839* (Internet Archive `fergusdirectoryo00ferg`) — printed pages 5-36,
1,655 entries — and printed page 37, the churches, hotels and public places. It stopped
there, and declared where it stopped in
`data/research/directories/coverage.json`. What it did not read is leaves 50-64, printed
pages 38-52, and that is a richer sixteen pages than the reading that has been done:

- **printed 37-38, the CITY REGISTER and the MAYORS** — the officers of the city, by year.
- **printed 40-41, the CHARTER ELECTION of 2 May 1837 and the FIRST ELECTION** — the poll
  as printed, two years after the scene date and the closest thing to a complete adult male
  roll the volume holds.
- **printed 43-46, the LIST OF VOTERS FOR MAYOR** — several hundred names. This is the one
  the resident sweep wants: it sits between the 1833-1835 poll lists T-0493 read and the
  1840 census, and a name in all three is a man who stayed.
- **printed 47-49, LOTS SOLD IN FT. DEARBORN ADDITION** — purchasers and lots, which is
  land evidence of the kind T-0557 read out of the federal tract books.
- **printed 50, POPULATION OF CHICAGO** — the volume's own year-by-year table, which gives
  1835 as 3,265 and 1839 as 4,200. It is set in two columns and archive.org's OCR
  interleaves them, so the pairing of year to figure has to be reconstructed and SAID to be
  reconstructed; do not read it off the flat text.

**The pattern is T-0506's**, and its three tools are the model: `tools/read_fergus_1839.py`
already knows how to turn this scan's `_djvu.xml` into committed page text with the turned
lines marked, and `tools/crosswalk_fergus_1839.py` already holds the surname-fold plus
first-initial rule and the four pools. Extend the coverage declaration rather than opening a
new domain.

**The two warnings that bind everything in this volume** are on printed page 3 and are
already recorded in `data/sources/fergus_chicago_directory_1839.json`: the book is Fergus's
1876 completion, from Old Settlers' recollections, of a list he set up from memory in 1839;
and no street but Lake carried numbers in 1839, so every address number printed is 1876's.

**Split it if it does not fit.** The voter list alone is plausibly one run; the lot sales
another. `ticket.mjs split` rather than shipping a self-invented half.

**Not in scope:** Fergus's historical sketch, leaves 65-80. It has no ticket yet.
