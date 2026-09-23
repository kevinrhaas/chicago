# `census_1840` — the 1840 federal census of Chicago, read off the page images

**This is LATER EVIDENCE.** Nothing in this directory mints an 1835 resident. The
project's ratified ladder is explicit: *1839/1840 alone is never a 1835 resident.*
What is read here is a named 1840 household head with a line position; the bridge to
1835 is a separate, adjudicated step (T-0505), and the minting is a separate one again
(T-0514, T-0515).

## What the deposit holds

`chicago/reference/census1840/` holds **74 distinct** FamilySearch page images in 75 files —
`33S7-9YYJ-9WF (1).jpg` is a byte-identical copy of `33S7-9YYJ-9WF.jpg`. (The tickets, the source
record and this file all said 75 distinct in 76 files; `ls *.jpg | wc -l` is 75 and `md5sum *.jpg |
awk '{print $1}' | sort -u | wc -l` is 74, so the count was one too many and the third image group is
51-74, not 51-75.) The deposit is **read only**: no image, crop or render is ever committed. Only
derived text is.

The sheets come in two kinds and both are numbered in the same run of printed pages:

| kind | what it carries |
|---|---|
| **left sheet** | `NAMES OF HEADS OF FAMILIES`, then 13 free-white male and 13 free-white female age bands, then free coloured males and females |
| **right sheet** | the continuation: slaves, the family TOTAL, the six industry columns, pensioners, deaf/dumb/blind, and schools & illiteracy |

A household is one ruled line spanning both, so a name and its own household figures
live on two different images.

## What is in here

| file | what it is |
|---|---|
| `coverage.json` | exactly which images have been looked at, what each one is, and what has and has not been read from it. A hole is meant to FAIL rather than pass quietly. |
| `pages/<familysearch_id>.json` | one file per page read: the printed page number, the sheet side, and one record per ruled line — `line`, `as_read`, `normalized`, `name_confidence`, `reading`. |
| `crosswalk_670.json` | the line-by-line comparison against the 210 rows PR #670 recovered from the owner's lost v4 workbook, page by page, with a row-offset test on each. |
| `claims.json` | what the sheets say ABOUT the enumeration and about the town, as opposed to who they name. Hand-authored, each with its verbatim quote and locator. |
| `composition_1840.json` | **counts and nothing else** — what a Chicago household looked like in 1840: the household-size distribution, the age bands, the industry columns, and the 1830 district and 1835 town placed beside them. Derived by `tools/census_1840_composition.py`, gated by `check.sh`, and refused by its own self-test if a name or a serial ever reaches it. T-0507; read `docs/RESEARCH/household-composition-1840-calibration.md` beside it. |

## The reading rules

- **`as_read` is a POSITION-PRESERVING reading.** An unread letter is `[?]` — a position,
  not an absence (T-0397). `normalized` is the modern spelling this project would use;
  where the surname itself is unread, `normalized` keeps the `[?]` rather than inventing a
  name that scans well.
- **`name_confidence` is `high | medium | low`** and is about the LETTERS, not about who
  the person was. A name can be read with confidence and still belong to nobody this
  project can identify.
- **`reading: scan_verified`** means it was read off the deposited page image. It is the
  senior reading: where a transcription and the sheet disagree, the sheet wins and both
  are kept.
- **Enumeration order is data.** The line sequence is the only spatial signal the 1840
  census carries — households were visited in walking order — so lines are never
  reordered and a blank or illegible line is recorded, never skipped.
- **No IPUMS serial is attached here.** The serial mapping is by age-band fingerprint and
  is T-0504's job, over all three image groups at once.

## The finding this pass exists to record

PR #670 recovered 210 named household heads from the owner's v4 workbook, which he has
since ruled lost — "They are lost; rebuild". Those 210 rows are the calibration set any
new reading must reproduce before it extends. **All seven of the pages they cover have now been read off the sheets, and they do not
reproduce.** Printed 233 and 235, the last two, were read to the name off `33SQ-GYYJ-RJ` and
`33SQ-GYYJ-ZQ` against T-0741's inventory of the group.

| printed page | image | scan lines | #670 rows | agree on both names |
|---|---|---|---|---|
| 229 | `33S7-9YYJ-9M5` | 30 | 31 | 2 |
| 230 | `33S7-9YYJ-NY` | 31 | 31 | see `crosswalk_670.json` |
| 231 | `33S7-9YYJ-38` | 31 | 31 | 0 |
| 232 | `33S7-9YYJ-W6` | 31 | 31 | see `crosswalk_670.json` |
| 233 | `33SQ-GYYJ-RJ` | 31 | 31 | 2 |
| 234 | `33S7-9YYJ-99F` | 31 | 31 | 4 |
| 235 | `33SQ-GYYJ-ZQ` | 24 | 24 | 6 |

Some of the disagreements are large: page 232 line 17 reads *Gurdon S. Hubbard* on the
sheet against *Saml. J. McCord?* in #670, and line 25 reads *John H. Kinzie* against
*John W. Rogers?* — two of the most consequential names in the town.

**Two different faults are present, and they want telling apart.** `crosswalk_670.json`
runs a `row_offset_test` on every page: how many of that page's scan lines find any
name-part agreement with the #670 row one or two places away. Page 234 peaks at offset 0
(16 partial hits against 3 at −1): the rows are aligned and the READINGS differ. Page 231
peaks at offset −1 (11 hits against 5 at 0): #670's rows are DRIFTED one place down that
page, so *Patteson Nickalls* at #670 row 12 is the sheet's line 11, and *John Leonard* at
row 27 is line 26. Page 230's tail shows the same drift shape. Page 229 is a third case
again: the sheet carries **30** ruled entries and #670 carries **31 rows** for it, so at
least one #670 row on that page has no line to sit on.

`crosswalk_670.json` carries every line of it. **Nothing in #670 was overwritten** — both
readings stand, with the reason the scan is treated as senior stated on each line. What
this means for T-0504 and T-0505 is that the 210 rows cannot be used as ground truth for
a serial fingerprint or an identity bridge until they have been re-read against the
images, and that a bridge built on #670's row NUMBERS is unsafe on at least page 231.

## Images 51-74: the first cells read from the third group

T-0741 inventoried all 24 images of the third group and read nothing else from them; T-0746
was then split by printed page into five pieces, because two left sheets to the cell is one
run's demonstration and the group holds seven left sheets, a recapitulation leaf and fifteen
continuations. **T-0963 read printed 212 and 213 in full — names AND all thirty-eight
columns** — the first cells read anywhere in this group.

| printed page | image | lines | footing columns closed | free coloured |
|---|---|---|---|---|
| 212 | `33SQ-GYYJ-RY` | 31 | 19 of 20 | 1 male 55–100, line 13 |
| 213 | `33SQ-GYYJ-RK` | 30 | 18 of 18 | 2 females, line 2 |

Two things this pass leaves open rather than closing. Printed 212's `f_10_15` footing glyph
sits under the closing rule and is **not settled**: the read total of 8 stands without a
check. And its `m_20_30` closes on 33 only because the cells of lines 20 and 27 are read
**from** that footing rather than from their own ink — they carry a glyph this hand does not
use for 3 elsewhere on the leaf, and the column is labelled as closing by construction.

Printed 213's footings are crisp where 212's are faint, and they are what fixes the
enumerator's numeral alphabet for both leaves: `f_10_15` closes at 3 against a bold curl over
an open bowl, `m_u5` at 4 against two parallel diagonals, `f_u5` at 6 against an elongated
slanted loop.

**The free coloured block of this group is not empty.** Printed 212 line 13 is a household
with no free white cell at all — a free coloured head of household — and printed 213 line 2
is a free white household of six with two free coloured females in it. Both close against the
free coloured footing row at the foot of their own leaf. This is still LATER EVIDENCE: nothing
here mints an 1835 resident.

Each leaf now carries a derived **page population key** — 107 for printed 212, 116 for printed
213 — which is what T-0967 will pair the group's fifteen continuation sheets against.

### The first continuation of this group read, and the pairing it refuses

T-0967 was split by leaf, one to a run, and **T-0972 read `33SQ-GYYN-385R`** — 24 lines, every
one of them, against a row grid measured on the leaf's own ink because
`read_census_continuation.py` refuses this sheet outright: its printed rules **lean 17 px** across
the body, and one darkness profile over the whole of it finds too few to name a column. That is
T-0761's finding met in the field, and the way round it is banded profiles.

**The column closes on the nose.** The 24 TOTAL figures sum to 123 against a printed footing of
123, residual zero — the second continuation sheet in the deposit to do that, after
`33S7-9YYJ-B2`. Two of the three other written columns close exactly as well (agriculture 1,
learned professions 3); manufactures and trades commits 1 + 4 = 5 against a printed 6 and **that
residual of 1 is left unspent**.

**The footing is a correction.** The inventory recorded this leaf as *foots 125*. It foots **123**.
The leaf writes a 3 and a 5 and they are not alike — its 5 has a separate horizontal cap over a
bowl that opens right, its 3 is one stroke from a top-right flag into a bowl that sweeps left — and
the footing's third glyph is the 3. What holds that is not opinion: the learned professions and
engineers column carries 1 and 2 and nothing else, and it foots in the same form. 1 + 2 = 3.

| key | `33SQ-GYYN-385R` | printed 235 (`33SQ-GYYJ-ZQ`) |
|---|---|---|
| lines with an entry | 24 | 24 — the **only** left sheet in the deposit with 24 |
| page population | 123, printed footing of the TOTAL column | 106 committed, **2 of 38 footings unread** |

So the pairing coverage.json called *a pairing hint and not a pairing* is **refused**, on T-0642's
rule that a pair must match on both keys. The two unread cells of printed 235's footing row would
have to carry 17 between them against a largest-figure-on-that-row of 14. Printed 235's **footing
row was read this pass** for exactly this test — its cells are still unread and nothing here reads
them. `33SQ-GYYN-385R` is recorded **unpaired**: its partner is one of the group's three unread
left sheets (printed 214, 220, 233, whose line counts are 30, 31 and 31 and so do not match), or a
leaf that is not in this deposit at all. The recapitulation counts thirty city pages; the deposit
holds 74 images of both sides.

## Three pages in this deposit are not household pages

`33S7-9YYJ-95F`, printed page **206**, is a printed left sheet used as the enumeration's
**certificate and recapitulation**: no household lines, and a manuscript note that names
Assistant Marshal **S. W. Sherman** as the man who took Cook County, is certified by a
signature reading *Mary Prittyman*, and records the book's two recapitulations —
population 3850, **4470 — City of Chicago**, 8320. The addition is internally consistent,
and 4,470 is the published 1840 figure for the city. It is transcribed in full in
`pages/33S7-9YYJ-95F.json` and its town findings are claims in `claims.json`. It is still
LATER EVIDENCE: it fixes the size of the town five years after the scene and may not be
extrapolated back to 1835.

`33S7-9YYJ-C8`, printed page **238**, is printed, numbered and wholly unfilled. A
swept-and-empty page is evidence, which is why coverage declares it rather than omitting
it.

`33S7-9YYJ-V2`, printed page **237**, is the other recapitulation — **the sheet the
certificate page was pointing at**. It sat in the inventory as "a continuation sheet whose
TOTAL column carries three-figure numbers", and the three-figure numbers were the evidence:
it enumerates nobody. Thirty ruled lines each carry a **division total** of 70 to 201
persons, gathered into six blocks, each block closed by a ruled footing that adds it, and
the foot of the leaf carries **4,470** — the certificate's own *"4470 — City of Chicago"*.
Four of the six footings close exactly on the lines above them (1164, 1320, 294, 1137), on
figures nobody typed in; the fifth is illegible under two crossing rules and the sixth block
is a lone line with no footing of its own. The six blocks sum to 4,466 against the 4,470
written at the foot, and **that residual of 4 is left open** rather than closed by adjusting
a digit.

The same row gives the city's employment in 1840: agriculture 25, commerce 182,
manufactures and trades 744, navigation of the ocean 1, navigation of canals, lakes and
rivers 44, learned professions and engineers 73, mining none — with 11 primary and common
schools and 397 scholars. It is transcribed in `pages/33S7-9YYJ-V2.json` and claimed in
`claims.json`, and like page 206 it is LATER EVIDENCE that may not be carried back to 1835.

**Why the sheet is not a continuation sheet, measured rather than judged.**
`tools/read_census_continuation.py` records that a household continuation leaf carries
exactly two strong horizontal rules — under the printed heading and above the enumerator's
footer — with the largest excess over local background anywhere between them at 4 grey
levels. The same measurement on this leaf finds **twelve rules inside the body**, at depths
of 23 to 117 grey levels. They are the block footings; and it is why that tool's own body
finder mis-reports this sheet's body as one block of six.

**No serial may be hung on any line of it.** A serial identifies an IPUMS *household*, and
no line here is a household, so there is nothing for `tools/census_1840_fingerprint.py` to
fingerprint and no head to name. The tool now says exactly that in the sheet's own row of
`serial_crosswalk.json`, instead of the generic continuation-sheet reason, which would have
been wrong twice: this is not a continuation sheet, and pairing it to a left sheet would not
help — a recapitulation's left sheet carries aggregates too, not age bands. (T-0529)

## The cells, and what the sheet's own footings say about them

Both calibration pages are now read to the cell. Every one of the 62 lines carries all 38
columns of its left sheet — 13 free white male age bands, 13 free white female, 6 free
coloured male and 6 free coloured female — as integers in the sheet's own order, under
`records[].cells`. A blank cell on the schedule IS a zero and is recorded as one; no line
was skipped and none is `illegible`.

**How the columns were fixed, because it is the whole risk.** These are 38 narrow columns
of single strokes and a mark read one column off is a person of the wrong age. The rules
were located per line from the image's own darkness profile rather than from a fixed grid,
which matters: the ruling on `33S7-9YYJ-NY` leans about 36 px between line 1 and line 31,
so a grid measured in the middle of the sheet puts the top and bottom lines a quarter of a
column out. Every column carrying a mark was then read a second time as a montage of its
own 31 cells; that second pass is what caught four counting slips in the first.

**The check is the enumerator's own arithmetic.** Each sheet foots its columns at the
bottom, and `column_totals` states, per column, what the marks come to and what the footing
says. On these two pages **73 of the 76 columns reconcile exactly**, and the three that do
not are named rather than smoothed:

| page | column | marks | the sheet's footing |
|---|---|---|---|
| 230 | free white females, 5 and under 10 | 15 | 13 |
| 230 | free white females, 15 and under 20 | 3 | 5 |
| 232 | free white males, 20 and under 30 | 33 | 35 |

The two on page 230 **cancel**: 15 + 3 = 13 + 5, and the page's free white female total is
70 whichever reading is taken, so the page's free population is 151 both ways. That is what
a footing written into the wrong column looks like — but nothing on the sheet says so, and
neither reading is preferred here. Page 232 has no such cancellation: its free population is
193 by the marks and 195 by the footings.

Page 230's free coloured section is empty in all 12 columns with no figure in any footing.
Page 232 has four free coloured people, three of them on line 31 under a head this reading
gives as `Emanuel M[o]nd[?]`, and its footings — 1, 2, 1 and 1 — reconcile exactly.

## The continuation sheets, and what closing one costs

A continuation (right) sheet carries no name. It carries the other half of every household
line: the twelve slave columns, the family TOTAL, the seven industry columns, the pensioners,
the ten deaf/dumb/blind/insane columns and the seven schools columns — and, at the foot, the
enumerator's own printed totals for the columns he used. **Those footer totals are the gate.**
A continuation reading is committed only when the per-line values sum, column by column, to
what the man who took the census wrote at the bottom of his own sheet; where a column does not
close, the residual is recorded with it and no line is altered to make the total come out.

Three of group 1's eleven continuation sheets have been read on that rule (T-0540):

| image | lines | closes | page population | what it says |
|---|---|---|---|---|
| `33S7-9YYJ-24` | 31 | **all five columns** | 201 | agriculture 2, commerce 9, manufactures 27, learned professions 2 |
| `33S7-9YYJ-5D` | 31 | 4 of 6 | 125 | manufactures 25, canals 2, learned 1, and 1 school with 26 scholars; totals read 128 against 125 and commerce 2 against 3 |
| `33S7-9YYJ-5S` | 29 | **no — not committed** | 189 | 1 school with 42 scholars; the attempted reading is on the page file as an attempt, `cells` is null on every line |

**`33S7-9YYJ-5S` is the useful failure.** Its attempted reading sums to 183 persons against a
printed 189 AND 12 in agriculture against a printed 10. Two columns out by different amounts is
not two misread glyphs; it is the row indexing itself slipping over part of the sheet, and the
project's rule is that a half-read row is worse than an unread one. So the sheet's footer and
its exact line count — 29, not the 28 the inventory stated to the nearest line — are committed,
and the per-line reading is kept beside them as an ATTEMPT that nothing downstream can consume
as fact. The next run starts from it rather than from nothing.

**The cost is the other finding.** T-0535 asked for all eleven sheets plus the pairing, sized S.
It was split twice as the size was measured — into T-0538/T-0539, then T-0540/T-0541 — because a
sheet that closes takes something like ten passes at magnification, not one: this hand writes
`4` as two strokes that read as `11`, its `7` and `9` differ by a loop, and its two-digit family
totals sit hard against the column rule. Three sheets is a run.

**One continuation sheet here is paired to a left sheet, and ten are not.** A right sheet has
neither a name nor a printed page number on its exposure, so the pairing has to be earned: each
page's population (the TOTAL footer, published on each page file as `pairing.page_population_key`)
has to be matched against the printed age-band totals at the foot of each candidate left sheet.
T-0642 read those footings for all twelve filled left sheets of the group and ran the test on all
eleven continuations — see the section below and
`data/research/census_1840/left_sheet_population_key.json`. Everything it did not pair stays
recorded as `unpaired`, with the candidate it came nearest to and the rule that refused it —
never guessed.

## The cells, and the rule that decides whether a column is committed (T-0532)

The age-band cells were read for the first time on printed pages **221, 222 and 226**.
Reading them at all needed a way to say WHICH column a mark is in that does not depend on
counting narrow rules by eye, so each page carries a `grid_note`: the 39 vertical rules are
fitted as a single pitch off the empty right-hand columns of the same image, and the fit is
**checked against the printed heading** — column 1 must read `Under 5`, column 27 `Under 10`
under FREE COLORED MALES — before a single cell is read. Every cell is then cut at that grid
and read as an image, one at a time. Nothing here is an OCR output.

**A column is committed only when it balances.** The lines this pass read must SUM to the
figure the enumerator wrote at the foot of the sheet; where they do not, the column is left
unreconciled with its residual stated, exactly as the ticket required, because a half-checked
column is worse than an unread one. So each page file carries two things per record:

| field | what it is |
|---|---|
| `cells` | the committed reading — only the columns whose page total balanced |
| `cells_first_pass` | the whole reading, balanced or not. **Not reconciled data.** It exists so the next reader starts from a reading rather than from the sheet. |

and `cells_column_check` states, per column, the read sum, the printed total, how confidently
that printed figure was read, whether it balanced, and the residual.

**Printed page 221 balances on 36 of its 38 columns** and is committed on those. The two that
do not are column 6 (free white males 30 under 40: read 10, printed 11) and column 15 (free
white females 5 under 10: read 11, printed 13) — one and two marks this pass did not find,
not a disagreement about what the sheet says.

**Printed 222 and 226 commit nothing, and the reason is the TOTALS and not the cells.** Both
sheets' footers are written across the foot rule and neither could be read to better than
`low` — so no column on them can be certified, whatever the cells say. What the page files do
record is that the read sums are *consistent with a plausible reading of the footer* on most
columns (`read_sum_matches_an_alternate_reading`), which is a lead for the next reader and is
explicitly not a balance. Re-read those two footers at higher magnification and most of both
pages should commit without the cells being touched.

## The 30-versus-31 question on printed page 229, settled (T-0534)

The most consequential thing in this directory is now settled, and it was settled by arithmetic
rather than by looking harder at the ruling. **Printed page 229 carries 30 household entries.**
PR #670 carries 31 rows for it. The test is the enumerator's own footings: on a page where the
column totals close, a 31st household has to put its people somewhere, and on 33S7-9YYJ-9M5 there
is nowhere left. **Seventeen of the nineteen columns that carry a mark close EXACTLY on the 30
lines read** — free white males 1-5, 7-10 and free white females 15-22 — against the figures
written at the foot of the sheet. So at least one of #670's 31 rows for that page has no line to
sit on, which is what `crosswalk_670.json`'s `row_offset_test` could only suspect. Nothing here
says which row is the intruder; that is a reading of #670, not of the sheet.

**A second finding sits beside it.** Line 26 of page 229 is a named head — the reading gives
`R. D. Coe` — with **no mark in any of the 38 columns**. A ruled, named line with a household of
nobody. It is not an artefact of the two columns that fail to balance: neither of them carries a
mark on line 26 either. It is recorded as it stands, an empty `cells` object on a named line.

## The cells of printed 229 and 231, and where the footings and the marks part company (T-0534)

Both pages are read to the cell on the T-0532 rule — a column is committed only where the lines
read SUM to the figure the enumerator footed — and **36 of 38 columns commit on each**. The four
that do not are named rather than smoothed:

| page | column | marks | the sheet's footing | what it looks like |
|---|---|---|---|---|
| 229 | free white males, 30 under 40 | 8 | 1 | not a reading dispute. A column montage of all 30 cells shows eight separate single strokes, on lines 2, 3, 4, 8, 15, 18, 20 and 28, and the footing is one stroke. Either the footing was never finished or it was written for a different column. |
| 229 | free white females, Under 5 | 19 | 11, or 19 | the footing is two long diagonals on the worst-degraded paper on the sheet. This hand writes `1` as a long diagonal, so `11` is the literal reading — but the second stroke carries a hook that reads as a `9`, and 19 is exactly what the marks come to. Neither reading is preferred here. |
| 231 | free white females, 20 under 30 | 20 | 21, or 20 | the footing is a `2` followed by a character that is either this hand's `1` or its `0`. A montage of all 31 cells of the column, cut and read one at a time, gives 20 and no twenty-first mark to find. |
| 231 | free white females, 40 under 50 | 3 | 5 | a genuine shortfall. The montage shows marks on lines 11, 24 and 29 only, and the footing is an unambiguous `5`. Two people this pass did not find. |

Everything else closes. **Page 231 is the cleanest sheet read in this deposit so far**: 34 of its
36 non-empty-or-footed columns balance on the first pass, including two-digit footings of 14, 30,
14, 16, 12 and 9. Page 229 is the worst-exposed, and it still closes on 36.

**Neither page has a free coloured person.** All 12 free-coloured columns are blank down both
sheets and blank in both footings, and that is recorded as a balance at zero rather than as
silence.

**The reading's populations**, which are the reading's and not the sheet's: page 229 is 71 free
white males and 81 free white females, 152 in all; page 231 is 83 and 74, 157. Taking every
footing exactly as written instead would give 137 and 160. Both are candidate keys for T-0539's
pairing of the eleven continuation sheets, and both should be treated as ±the residuals above
until a right sheet's TOTAL column confirms one.

**How the grid was fitted here, because it differs from T-0532's.** The 39 vertical rules were
fitted as a single pitch over the whole width of the sheet's own body and then checked against the
printed heading — column 1 must read `Under 5`, column 27 `Under 10` under FREE COLORED MALES,
column 38 `100 and upwards`. That check is what caught the thing a fixed grid would have missed:
**the rules of this book lean, and so do the lines.** The same column grid sits about 10 px left
of the printed rules at the head of a sheet and 10 px right of them at its foot; and on
33S7-9YYJ-9M5 the writing lines drop about 45 px between the left edge of the table and its right,
which is more than half a row — so a flat row grid reads the free-coloured end of a line into the
wrong household. Both leans are carried in the grid. Every column carrying a mark was then read a
second time as a montage of its own 30 or 31 cells; that second pass is what separated three
name-tails intruding from the NAMES column into column 1 of page 229 from the tally marks, and it
is what makes the 8-against-1 above a finding rather than a miscount.

## Two line counts the sheets do not agree with the inventory about (T-0532)

The row grid was fitted the same way as the column grid and checked against the names, and on
two of the three pages it finds fewer entries than the inventory declared:

| printed page | image | inventory said | entries read | blank ruled lines at the foot |
|---|---|---|---|---|
| 221 | `33S7-9YYJ-2T` | 31 | **31** | 0 |
| 222 | `33S7-9YYJ-98M` | 31 | **30** | 1 |
| 226 | `33S7-9YYJ-B3` | 31 | **29** | 2 |

The inventory's figure is `lines_with_an_entry`; the difference is blank ruled lines below the
last household, which the page files **record as lines** rather than skip. Coverage now carries
both numbers per image (`lines_with_an_entry` and `lines_ruled`).

## Printed 234 to the cell, and a second reading of 229 and 231 that does not agree with the first (T-0551, PR #698)

`33S7-9YYJ-99F` (printed **234**, 31 lines) is read to the cell: **37 of 38 columns balance the
enumerator's own footings and are committed**. The one that does not is free white females 5 under
10 — ten marks against a footing of 11 — and line 17 is the candidate, its mark carrying a second
stroke at the foot that this pass read as an inked start to a 1 and that could be the base of a 2.
Line 2 (*Geo. Shelley*) is the deposit's largest household so far — 7 males 20-30, 4 males 30-40,
6 females 20-30 and 4 females 30-40 — and every one of those four columns closes on its footing with
that reading in it. A single line that large is a lodging house rather than a family, and it is the
sort of thing T-0507's composition calibration will need to hold separately. All twelve free
coloured columns are empty and footed empty.

**The same run also read printed 229 and 231 to the cell, and so, one batch earlier, did T-0550
(PR #697).** Two independent readings of the same two sheets now exist, and they do not agree.
T-0550's is the committed reading in `pages/`; this run's is preserved verbatim in
`second_readings/` (its page files exactly as PR #698 first carried them), and the disagreement is
stated here rather than one reading being chosen by whichever landed first:

| printed page | lines | names agree | lines whose cells differ | column checks that differ (second reading / committed) |
|---|---|---|---|---|
| 229 (`33S7-9YYJ-9M5`) | 30 | 30 of 30 | **20** | free white males Under 5: 9 read against 14 footed on the second reading, 10 against 10 on the committed one; free white males 30 under 40: 8 read against 7 footed on the second reading, 8 against 1 on the committed one; free white females Under 5: 19 read against 19 footed on the second reading, 19 against 11 on the committed one |
| 231 (`33S7-9YYJ-38`) | 31 | 31 of 31 | **25** | free white females 5 under 10: 9 read against 9 footed on the second reading, 12 against 12 on the committed one; free white females 20 under 30: 20 read against 20 footed on the second reading, 20 against 21 on the committed one; free white females 40 under 50: 3 read against 3 footed on the second reading, 3 against 5 on the committed one |

**SUPERSEDED BY THE RECONCILIATION BELOW.** The table above counts each reading's `cells` block,
and each reading's `cells` block is masked to that reading's OWN committed columns — so the 20 and
the 25 are mostly the two MASKS differing, not the two readings differing. Compared on the raw
`cells_first_pass` blocks, which is what each pass actually read off the sheet, **the two readings
of 229 differ on ONE line and the two readings of 231 differ on ONE line.** The paragraph that
stood here inferred a grid disagreement from those figures — strokes one reading put in column 1
and the other in column 14 — and there is no such disagreement on either sheet. What the two
passes really disagreed about is the FOOTINGS, and that is what made each of them balance a
different set of columns. The finding the section was written for survives the correction intact:
**a column that balances is not, on its own, a column read right** — both passes balanced column 1
of 229, at 10 and at 9.

### RECONCILED against the sheets, T-0559

Both pages were re-read against the images at 4x to 12x, on a grid re-fitted off each sheet's own
vertical rules and checked against the printed heading before a cell was read (column 1 `Under 5`,
column 14 `Under 5` under FEMALES, column 15 `5 under 10`, column 18 `20 under 30`, column 20
`40 under 50`). Every disputed cell and all six disputed footings are decided; the decisions and
the reasoning are stated per column in each page file's `cells_note`, and
`second_readings/` is untouched.

| what was in dispute | decided | prevailing reading |
|---|---|---|
| 229 line 28 (Patrick Sanderken), column 1 | no stroke | second reading — the ink is the terminal flourish of the surname, one continuous tapering movement out of the last letter, where the free-standing tally on line 27 stands clear of the name |
| 229 column 1 footing | **14** (alt. 10, 16) | second reading — the second glyph is an open angular crossing with no closed bowl, this hand's 4 rather than its 0 |
| 229 column 6 footing | **7** (alt. 1) | second reading — one glyph, a long diagonal with a barred head, unambiguous at 9x |
| 229 column 14 footing | **19** (alt. 11) | second reading — two faint slants on the worst paper on the sheet, and 19 is the alternate the committed file itself recorded |
| 231 line 13 (Michael Duffy), column 15 | **4** | committed reading — a written numeral, a filled angular head with a stem crossing it, where every tally on the sheet is a single thin slant |
| 231 column 15 footing | **12** (alt. 9) | committed reading — two glyphs, a clean slant clear of the blot and then the filled bowl, not one blotted 9 |
| 231 column 18 footing | **21** (alt. 20) | committed reading — a 2 and then a straight hooked slant, this hand's 1 and not its 0 |
| 231 column 20 footing | **5** (alt. 3) | committed reading — a stroke entering from the upper right into a full open bowl, the construction of the 5s at columns 15 and 21 of printed page 229 |

**What moved.** On 229, column 1 is DE-COMMITTED — it was committed at 10 read against 10 footed and
is now 9 read against 14 footed, residual 5 — and column 14 is COMMITTED at 19, because both passes
read its thirteen cells at 19 independently and 19 is one of the two readings its footing admits.
Column 6 stays unbalanced at 8 read against 7 footed. The page still commits 36 of 38 columns and
they are not the same 36; its reading population falls from 152 to 151. On 231 nothing moved: all
three footings and the one disputed cell go the committed reading's way, and the 36 committed
columns stand. Where a footing was decided against a reading's cells, the reading is left unbalanced
with its residual stated rather than a stroke being found to close it — the five extra strokes 229's
column 1 footing implies are not on the sheet, and all six candidate lines (16, 19, 22, 28, 29, 30)
were examined at magnification and every one is a name terminal.

Printed 229's line count is settled at 30 by both readings independently, on the same argument
(the footings close on 30 lines and there is no 31st ruled line), so that finding stands whichever
reading of the cells prevails.

## Three more sheets read to the same rule (T-0533)

| image | printed page | entries | blank ruled lines | columns committed | `cells_state` |
|---|---|---|---|---|---|
| `33S7-9YYJ-9HY` | 225 | 23 | 8 | 38 of 38 | `read` |
| `33S7-9YYJ-6J` | 228 | 17 | 14 | 38 of 38 | `read` |
| `33S7-9YYJ-9MX` | unknown | 31 | 0 | 36 of 38 | `read_partly_reconciled` |

**Two of the three balance completely.** On 225 the twenty-three entries sum to the
enumerator's own 10, 5, 5, 9, 14, 12, 4, 2, 0, 1 across the male bands and 13, 6, 4, 2,
17, 6, 4, 0, 1 across the female; on 228 to 6, 2, 3, 2, 8, 8, 1, 1 and 8, 10, 1, 1, 8, 9,
2, 0, 1. Both sheets leave the FREE COLORED PERSONS block wholly unfilled, with no total
written under it, so those twelve columns commit at zero.

On `33S7-9YYJ-9MX` twenty-four of the twenty-six free-white columns close and **two do
not** — free white males Under 5 (sheet 11, thirty-one lines 18) and 5 under 10 (9
against 10). Those two are absent from `cells` and kept in `cells_first_pass`, which is
the same shape T-0532 set: the reading is evidence of what is on the page, and it is not
reconciled data.

Three things the totals rows taught, which the remaining cell tickets will want:

- **This hand's `8` is a reversed S with a closed head** and passes for a `5` until you
  have seen four of them. Four columns on page 228 were first read 5 and are 8.
- **Two-digit totals straddle the printed rule.** The second digit of 14, 17, 29 and 10
  each falls partly into the next cell, so reading a cell in isolation loses it — the
  page-225 female 20-under-30 total read as 13 and is 17.
- **The check catches the reader at least as often as the sheet.** Every apparent failure
  on 225 and 228, and two on `9MX`, was a printed digit misread rather than a mark
  miscounted.

Two more inventory counts are now exact: page 225 stops at line **23** (inventory said
25) and page 228 at line **17** (said 18). The remainder of each sheet is ruled and
blank, and those lines are recorded as lines.

`33S7-9YYJ-9MX` keeps `printed_page: "unknown"`. The corner carrying the number is
outside the exposure; the `(p. 4.)` in the printed heading is the form's plate marker and
is not the book's page; and it is not inferred from the filename order, which is not the
book's order. T-0504's serial fingerprint is the route that can place it.

One household is worth naming before anyone reads these sheets as families: **line 1 of
`33S7-9YYJ-9MX` holds nineteen men** — 11 in their twenties, 8 in their thirties, no
women under forty and no children. That one line is most of why its 30-under-40 column
totals 21.

## What has NOT been read yet, and where it is

The age-band, free-coloured and industry cells are a column-by-column reading that has to
be checked against the **printed column totals at the foot of each sheet** before it can
be committed — 26 narrow columns of single strokes, where a mark one column off is a
person of the wrong age. Committing a half-checked row would be worse than leaving it
unread, so a page's `records[].cells` stays `null` with `cells_state: "not_read"` until that
check is done. Eight pages have had it: printed 230 and 232 (T-0530 — 62 households, every
age band and free coloured column read line by line, 73 of 76 footings reconciled exactly,
the three that do not named on the page files), printed 221, 222 and 226 (T-0532 — the
balance stated per column in the section above, 221 committed on 36 of 38 columns, 222 and
226 committing nothing until their footers are re-read), printed 229 and 231
(T-0550 — 36 of 38 columns committed on each, printed 229's line count settled at 30, and a second
reading of both on PR #698 that does not agree with it, see below) and printed 234 (T-0551 — 37 of 38).
On every other page here the cells
are still `not_read`, and those cells are their own ticket. The other images of both read groups are inventoried in
`coverage.json` — kind, printed page, line count — and transcribed by the sibling tickets
T-0494 and T-0495 were split into.

One printed page number could not be read at all: `33S7-9YYJ-9MX` is a filled left sheet
whose top-right corner falls outside the exposure. It is recorded as `unknown` rather than
inferred from the ids around it, because the sorted filename order is not the book order —
this group alone runs 221, 231, 228, 206, 222, 234, 225, 219, 229, ?, 210, 215, 226, 238.

The **continuation half** of these two households — the family TOTAL, the six industry
columns, pensioners, and the schools and illiteracy columns — is on the paired right sheet,
and which right sheet that is is not settled. It is not in this image group: no continuation
sheet in images 26–50 foots a TOTAL of 193, and the only one footing 151 (`33SQ-GYYJ-9CZ`)
carries a per-line total vector that does not match page 230's. `records[].cells.free_persons`
is the fingerprint that settles it — a household is one ruled line spanning both sheets, so
the right sheet's TOTAL column must equal it line for line. That pairing is T-0528's ticket
and the continuation columns follow it.

The other 23 images of this group are inventoried in `coverage.json` — kind, printed page,
line count — and transcribed by the sibling tickets T-0495 was split into.

## Printed pages 216 and 217, read to the cell (T-0552)

`33S7-9YYJ-DD` (printed **216**) and `33S7-9YYJ-RC` (printed **217**) are the first two left
sheets of image group 26–50 to be read in full: 62 households, every one of the 38 age-band
columns on each line, and the enumerator's own footings transcribed beside them.

**How the columns were fixed.** The leaf bows into the gutter, so a grid taken off the printed
header is about a quarter of a column out in the middle of the page — the first reading of page
216 put two marks a column to the left of where they stand because of it. Both sheets were
therefore gridded from the image's own vertical darkness profile (page 216: free white males
from x=0.1558 of the image width at a pitch of 0.019725, females from 0.4118 at 0.019575,
coloured from 0.6689 at 0.01963; page 217: 0.1529/0.019523, 0.4067/0.0195, 0.6611/0.01955) and
every line re-read from a crop with that grid drawn over it. The row ruling leans about half a
line down page 217, which on a uniform row grid reads as a blank line between Philo Carpenter
and Robert Crawford; it is drift, not a blank line, and the tail was re-read on a grid fitted
to it.

**A line count corrected.** The inventory declared page 217 at 33 lines "to the nearest line".
It carries **31**, counted twice — once down the names column and once on the drawn grid — with
no blank ruled line anywhere between entries. Page 216's declared 31 is restated unchanged.

**What closes and what does not.** Every column of both sheets is checked against the figure the
enumerator wrote at the foot of his own column, and a residual is recorded rather than adjusted
away.

| sheet | block | footings that close | that do not |
|---|---|---|---|
| 216 `33S7-9YYJ-DD` | free white males | 5 of 8 | under 5 (20 read / 21 footed), 10–15 (3/6), 15–20 (6/1) |
| 216 | free white females | 7 of 9 | under 5 (15/14), 5–10 (4/2) |
| 216 | free coloured | 3 of 3 | — |
| 217 `33S7-9YYJ-RC` | free white males | **9 of 9** | — |
| 217 | free white females | 5 of 8 | under 5 (20/16), 20–30 (19/18), 30–40 (15/12) |

Page 217's male block closing exactly on all nine footed columns is what licenses the method:
the same grid, read the same way, reproduces the enumerator's own arithmetic on 86 people. The
residuals that remain are therefore a statement about the sheets, not a confession about the
grid — and two of page 216's are as likely to be a glyph as an error, which the page file says
where it says it (its 10–15 footing is a bottom-looped figure read as 6, and a 3 would close the
column exactly; the reading is flagged, not assumed).

**What this means for pairing.** Neither sheet is paired to its continuation — that is T-0539's
single reading over all eleven. Each publishes its population key: page 216 at 175 by the
footings, 180 by the lines; page 217 at 160 by the footings, 168 by the lines. Try the footing
key first, because the TOTAL column a continuation sheet foots comes out of the same arithmetic.

**Nothing here mints or regrades an 1835 resident.** Philo Carpenter is on page 217 line 29 and
is the one name a modern reader can be sure of; the bridge from a named 1840 head to an 1835
record is T-0505's step, under a ladder that is explicit that 1839/1840 alone is never a 1835
resident.

## Printed 210 and 215, read to the cell (T-0584)

Two more left sheets of image group 1 are now read line by line and column by column,
and both were closed against the figures the enumerator footed on his own sheet.

| printed page | image | lines with an entry | columns balanced | not committed |
|---|---|---|---|---|
| 210 | `33S7-9YYJ-9RG` | 30 (inventory said 31) | 36 of 38 | free white females Under 5 (14) and 5 under 10 (15) |
| 215 | `33S7-9YYJ-9WF` | 31 (inventory's figure stands) | 37 of 38 | free white females 30 under 40 (19) |

**The footings corrected the reading twice, and the reading corrected the footings twice.**
On 210 the columns for free white males 20 under 30 and 30 under 40 were first read off a
1400 px contact view as 25 and 16; the line-by-line sums came to 29 and 19, and zoomed on
the footing itself both figures are plainly 29 and 19. The other way round, on 215 the
first column template — anchored on the strongest 39 rule detections rather than on the
printed heading — started one whole column too far right, which would have aged every
person on the sheet by one band. Rendering the template over the printed heading is what
caught it, and it is why the grid note on every page file states that check.

**What the two sheets are.** They are not alike. Printed 210 is a page of large households:
30 entries carrying 179 free white persons, one of them (line 1) of fourteen. Printed 215
is the opposite — 31 entries, and columns 6 and 7 (free white males 30 under 40 and 40
under 50) carry 49 of its 116 free white persons between them, mostly one man to a
household. Printed 215 also carries the only free coloured persons read from image group 1
so far: six of them in John Johnson's household on line 29, and one on line 5.

**Two residual columns are left standing rather than forced.** On 210, free white females
Under 5 reads 14 against a printed 16 and 5 under 10 reads 18 against a printed 15 — equal
and opposite to within one, which is the shape of marks read into the wrong one of two
adjacent columns; the montage was cut at the leaned rules, re-read, and did not move them.
On 215, free white females 30 under 40 reads 17 against a printed 19. Those columns are
omitted from `cells` and kept in `cells_first_pass`, which is read but unreconciled and is
not data anything downstream may use.

## Printed 219, read to the cell (T-0585)

The last of the three left sheets T-0531 named is read, and image group 1 now has
eight left sheets carrying names and cells.

| printed page | image | lines with an entry | columns balanced | not committed |
|---|---|---|---|---|
| 219 | `33S7-9YYJ-9K3` | 31 (inventory's figure stands) | 37 of 38 | free colored males 24 under 36 (29) |

**The column template was checked against the printed heading before a cell was read**,
because that is the check T-0584 learned the hard way, and the pitch it settled on —
x = 662.5 + 79.35 n — is the same 79.35 px pitch printed 215 carries, which is what a
shared plate should give. Rendered over the heading it reads column 1 `Under 5` under
MALES, column 13 `100 and upwards`, column 14 `Under 5` under FEMALES and column 26
`100 and upwards`.

**A footing settled a blot.** Line 16 carries a thick mark in free white males 20 under
30 that a row-band view reads as a tally. Montaged against its own 31 cells it has no
stroke form at all, and the column's printed footing of 62 balances the other eighteen
lines exactly and refuses it. It is recorded as a blot and not as a person.

**What this sheet is: boarding houses.** Printed 219 is neither 210's large families nor
215's single men. 195 free white persons stand on 31 lines and FOUR lines carry 104 of
them — line 18 (S. M. Osterhoudt) 33, line 29 (G. W. Cook) 27, line 10 (Wm R. Miller) 22,
line 17 (Lyman Butterfield) 22 — each one a stack in the young bands: free white males
20 under 30 alone carries 62 of the page's 126 men, and free white females 20 under 30
carries 30 of its 69 women. Against those four, twelve households hold two persons or
fewer and ten of those hold one or none. Line 25 (Oliver Henson) is the only household on
the page with no free white person in it: as read, a boy under 10, a man 24 under 36 and
a woman 24 under 36.

**One residual column is left standing rather than forced.** Free colored males 24 under
36 reads 4 — a 2 on line 18, a 1 on line 25, a 1 on line 29, and the montage of the whole
column holds nothing else — against a footing of two identical hooked diagonals, which is
the form this hand foots column 1 with (where the body confirms 11). A 4 would balance and
the glyphs do not support one. The column is omitted from `cells` and kept in
`cells_first_pass`, which is read but unreconciled and is not data anything downstream may
use.

**The letters are open and are recorded as open.** No name on this sheet is graded `high`:
9 are `medium` and 22 are `low`, each with its alternates in the record's note. Two lines
may be women heading households (line 15 `Susan McCord`, line 28 `Mad Sara L. Hoare`) and
both forenames are among the `low` readings, so neither is asserted. Nothing here mints or
regrades an 1835 resident: the 1840 census is later evidence and the ratified ladder is
explicit that 1839/1840 alone is never a 1835 resident.

## Every named head has an outcome now (T-0505)

The 498 names read off the 19 left sheets in this repo were in no state at all: three of
them were bridged to an 1835 person and the rest were neither matched nor refused, which
reads exactly like a pile nobody has looked at, so the next sweep would have looked at it
again. `tools/crosswalk_census_1840_heads.py --build` writes
`resident_crosswalk.json`, which gives every one of them an outcome and the rule that
decided it, and it fills this domain's `crosswalk.json` — which held
`passes: [], merges: [], refusals: []` — with 5 merge(s) and 139 refusal(s).

**The counts.** 5 matched, 5 candidate, 488 refused.

| rule | heads |
|---|---|
| `L1 unreadable_name` | 141 |
| `L2 no_surname_in_the_1835_pools` | 230 |
| `L3 given_name_conflict` | 94 |
| `L4 initial_only` | 21 |
| `L5 name_is_not_unique` | 2 |
| `L6 matched` | 5 |
| `L6a low_confidence_caps_at_candidate` | 1 |
| `L7 candidate` | 4 |

**The ladder is deliberately hard to climb.** `matched` needs the full forename and the
surname to agree, the name to be unique BOTH among the 498 heads and among the 1835
persons, the reader's own grade on that name to be `medium` or better, and a discriminator
that is independent of the name — an 1843 Fergus or 1844 Norris directory entry adjudicated
to that person, or an 1840 bridge already adjudicated. An appearance of the SAME NAME on a
poll list or a letter list is NOT a discriminator: it is the same name again, and it cannot
separate two people who share it. Those appearances are recorded on every head as
`same_name_support`, and they never promote a candidate.

**What it found.**

| 1840 head | 1835 person | printed page / line | rule |
|---|---|---|---|
| William H. Stow | William H. Stow | 225 / 20 | L6 |
| William Allen | William Allen | 230 / 26 | L6 |
| Philo Carpenter | Philo Carpenter | 217 / 29 | L6 |
| John Davis | John Davis | 232 / 13 | L6 |
| Gurdon S. Hubbard | Gurdon Saltonstall Hubbard | 232 / 17 | L6 |

and 5 candidate(s):

| 1840 head | 1835 person | printed page / line | rule |
|---|---|---|---|
| John Wilson | John Wilson | 229 / 2 | L7 |
| John H. Kinzie | John Harris Kinzie | 232 / 25 | L7 |
| Byram King | Byram King | 207 / 4 | L7 |
| Samuel C. Jackson | Samuel Jackson | 207 / 5 | L7 |
| Joseph M. Chandler | Joseph Chandler | 207 / 6 | L6a |

**John Murphy is now a refusal, and that is the most useful thing in the pass.** The
adjudicated bridge in `census_1840_identity_bridges.csv` puts him on printed page 233 row
30. This repo has read a `[?]ohn Murphy` on printed page 222 line 27 — a different line, on
a sheet the bridge does not name, and printed 233 has not been read here at all. Two 1840
lines carry the name, so neither identifies the man, and the pair is refused under L5 with
the conflict written down. The bridge is not withdrawn here: this file adjudicates lines
and T-0515 owns the bridge table. Reading printed 233 settles it.

**The 29 heads the 2 September legacy matcher left unmatched are re-adjudicated**, and they
split three ways: 14 sit on printed pages this repo has not read yet and are refused as
unverifiable rather than carried forward (the workbook behind them is lost — the owner's
ruling of 2026-09-03 is "They are lost; rebuild"); 13 sit on pages that HAVE been read here
line by line and no line on them carries the name, so the workbook row is refused in favour
of the page; and 2 are found in this reading and take an ordinary ladder outcome.

**Town finding.** The only spatial signal an 1840 sheet carries is the order the enumerator
walked it in. 2 adjacent pair(s) of matched-or-candidate heads are recorded under
`town_findings` — an 1840 fact about 1840 neighbours, which places nothing on the 1835
ground and may not.

**Nothing here mints or regrades anybody.** Each `matched` head carries a PROPOSED
`later_census` block in the shape PR #670 wrote, with `serial: null` because the
page-to-IPUMS-serial fingerprint is T-0504 and is not landed; T-0515 applies them. The
ratified ladder binds throughout: an 1839 or 1840 appearance alone is never an 1835
resident, and 1840 household composition is never back-projected to the scene.

---

## The line index of a continuation sheet (T-0565, 2026-09-04)

**A right-hand continuation sheet has no rows on it.** `read_census_continuation.py`
measured that on `33S7-9YYJ-5V`: a row-darkness profile through the empty slaves block
finds exactly two horizontal rules on the whole leaf — under the printed heading and above
the enumerator's footer — and nothing between them. The printed form rules the page
vertically only. So which LINE a number stands on cannot be counted off the paper, and
every pass that tried to get it from the TOTAL column's own ink got a different answer:
`coverage.json` inventoried 28 lines, one grouping threshold gave 31, another 34, and the
page file could only record "29 to 31, favouring 31".

**The fix is to stop asking the column that is in dispute.** `tools/fit_census_line_grid.py`
fits a straight grid `y = origin + pitch × n` to the enumerator's OTHER ink — the entries
of the written industry columns, which are read and close against their own printed
footings — and reports the best fit for every line count in turn. On `33S7-9YYJ-5V` the 22
industry entries choose **30 lines at an rms of 6.7 px**, against 19.9 for 28, 21.3 for 29
and 19.0 for 31, and 15.4 or worse for every count out to 38. Dropping each anchor in turn,
20 of the 22 jackknife refits still choose 30; the two that do not are the two endpoints,
which shorten the span by a line when removed.

The TOTAL column is then read AGAINST that grid rather than used to build it, which is what
makes the row index and the numbers independent. It is also what a continuation sheet needs
before it can be paired to its left sheet, so `pairing.line_count_key` is a number on this
sheet now and not a range.

**The tool reads its anchors out of the page file's own `column_closure` block** (`entry_y`),
so it has nothing typed into it and re-runs against whatever that block holds. Only
`33S7-9YYJ-5V` records `entry_y` today; the other continuation sheets record their column
closures without y positions, so the tool cannot yet be turned on them. A pass that adds
`entry_y` to `33S7-9YYJ-24`, `-5D` or `-5S` gets their line indices for the cost of the
measurement alone.

**What it does not do.** It gives an ordinal, not a reading. On `33S7-9YYJ-5V` the grid has
30 lines and the TOTAL column has 31 glyph groups, and the surplus — one stroke at
y2743-2772, sitting dead centre between two numbers that are each where the grid puts them —
is recorded as unassigned rather than folded into either. A row index that cannot be wrong
about the count is still allowed to be silent about one mark.

## Printed pages 218 and 224, read to the cell (T-0553)

`33S7-9YYJ-PC` (printed **218**) and `33S7-9YYJ-JM` (printed **224**) finish T-0526's four
left sheets, after T-0552 read 216 and 217. Sixty households, every one of the 38 age-band
columns on each line, and the enumerator's own footings transcribed beside them.

**Both sheets close.** Every column either sheet's enumerator footed reproduces from the
cells exactly — sixteen of sixteen on page 218 (113 people), fifteen of fifteen on page 224
(175 people). That is thirty-one footed columns closing at a residual of zero, and it is a
check on the grid as much as on the reading.

| sheet | block | footings that close | that do not |
|---|---|---|---|
| 218 `33S7-9YYJ-PC` | free white males | **7 of 7** | — |
| 218 | free white females | **9 of 9** | — |
| 218 | free coloured | unfooted; body empty | — |
| 224 `33S7-9YYJ-JM` | free white males | **7 of 7** | — |
| 224 | free white females | **8 of 8** | — |
| 224 | free coloured | unfooted; body empty | — |

**The column grid has to be measured twice, and the second measurement is the one that
matters.** T-0552 already found that a grid taken off the printed header is a quarter of a
column out in the middle of the page. These two sheets add the other half of the lesson.
Fitting an evenly spaced comb to the whole leaf finds the pitch correctly — 79.8 px on page
218 — but it cannot tell you WHICH rule the block starts at, and on page 218 its strongest
fit for the free-white-female block was one entire column to the right of the truth. Read
that way, every woman on the sheet is one age band too young and nothing announces it. What
settled it was the printed header read at magnification: the box lettered `Under / 5` for
the female block occupies x=1799–1878 on that leaf, and the male `100 / and up- / wards.`
box ends at 1799. Both sheets' block edges are fixed that way and the comb is used only for
the pitch and the drift. The drift is real and it is why the fit is banded: page 218's male
block starts at x=768.5 near the top of the body and at x=798.5 near the foot.

**A line count corrected, twice.** The inventory declared page 218 at 33 lines "to the
nearest line" and page 224 at 33. Each carries **30**, counted twice — once down the names
column at magnification and once on the drawn grid — with no blank ruled line between
entries. With page 217 (33 declared, 31 read) that is three of this group's four counted
left sheets whose inventory figure was high, and the pattern is worth stating for the sheets
still uncounted: the "to the nearest line" figures in `coverage.json` run about 8% long.

**Five marks refused, all of them named.** Four on page 224 and one on page 218 are recorded
as no entry rather than as a person, and each refusal is written on the page file with the
reason and with what the column would have footed had the mark been read. Four of the five
lie on the path of the flourished tail this hand gives the name to their left; the fifth is
a descender from the line above, which a gridded re-read at 2.2x made plain. None of the
five was refused because a total wanted it: the cells were read and fixed before the footer
was looked at.

**One footer glyph is doubtful and says so.** Page 224's male 20–30 footing is two figures,
`3` and a small bowl above a right-turning curl. The same second glyph stands in the 30–40
footing beside it, where the column reads 17 from the cells; so the glyph is a 7 and the
20–30 footing is 37, which is what the cells give. The alternatives (2, 9) and their
residuals are on the page file.

**What this means for pairing.** Neither sheet is paired to its continuation — that is
T-0539's work. Each publishes its page population as the key that pairing will read: 113 for
page 218, 175 for page 224, on 30 lines each.

## The left-sheet population key, and what pairs to what (T-0642, 2026-09-04)

A continuation sheet has no name and no printed page number, so it can only be joined to its
left half by numbers. Two are available. The **line count** — ruled lines carrying an entry —
must be the same on both halves of one opening. The **page population** is given twice: on the
left sheet as the sum of the enumerator's 38 printed age-band footings, and on the right sheet
as the printed footing of the TOTAL column. `left_sheet_population_key.json` publishes both for
every sheet in image group 1 and states the outcome of the test for all eleven continuations.

**The rule: a pair must match on BOTH keys.** A match on one key alone is recorded as a
candidate with the rule that refused it, so a later pass can retry it rather than rediscover it.
The right key is always the enumerator's own TOTAL footing and never a pass's line-by-line sum
of that column — the two differ on four of the seven sheets that have both.

| printed page | image | entries | page population |
|---|---|---|---|
| 210 | `33S7-9YYJ-9RG` | 30 | 187 |
| 215 | `33S7-9YYJ-9WF` | 31 | 103 |
| 219 | `33S7-9YYJ-9K3` | 31 | **208 as footed, 201 by its own lines** |
| 221 | `33S7-9YYJ-2T` | 31 | 146 |
| 222 | `33S7-9YYJ-98M` | 30 | 123 or 124 |
| 225 | `33S7-9YYJ-9HY` | 23 | 115 |
| 226 | `33S7-9YYJ-B3` | 29 | **184** |
| 228 | `33S7-9YYJ-6J` | 17 | 71 |
| 229 | `33S7-9YYJ-9M5` | 30 | 137 |
| 231 | `33S7-9YYJ-38` | 31 | 160 |
| 234 | `33S7-9YYJ-99F` | 31 | 182 |
| unknown | `33S7-9YYJ-9MX` | 31 | 152 |

**Two footings were read off the page this pass**, because two sheets had columns their
cell-reading passes recorded as `not_read`. On `33S7-9YYJ-B3` twenty of the twenty-one are blank
and the twenty-first — column 29, free coloured males 24 under 36 — carries a cursive **2** that
balances the 2 its cells hold; that figure moves the sheet's key from 182 to 184. On
`33S7-9YYJ-98M` all seventeen are blank, which fixes its key rather than leaving it open — and
the same reading disagrees with one figure already committed: column 27 is a single diagonal
stroke where T-0532 read 2. The disagreement is recorded, not spent: the sheet is keyed **123 or
124**, and neither value pairs with anything, so nothing in this pass turns on it.

**One of the eleven pairs.** `33S7-9YYJ-24` — the calibration sheet of the whole continuation
reading, which closes on all five of its own footed columns — carries 31 entries and foots 201
persons. Printed page **219** (`33S7-9YYJ-9K3`) carries 31 entries and its own 31 lines hold
exactly **201**. Nothing else in the group comes within eleven of that number by either measure.

**And that pairing settles a glyph the sheet alone could not.** 9K3's column 29 is footed with
two hooked diagonals, which T-0585 read as **11** against **4** in the column's own 31 cells; it
committed neither and recorded the residual of 7. If the footing were 11 the page would hold 208
persons and the facing continuation foots 201; read as 4, the two sheets agree to the person.
That is a second and independent witness for 4 — and it is the same two-stroke 4/11 form that
T-0627 and T-0645 settled toward 4 on `33S7-9YYJ-6H`. The page file is not rewritten: the
residual stays where T-0585 put it, with this pairing named beside it.

**And the 4/11 form is now decided by a measurement rather than by prose (T-0647).** Every pass
that met the two-stroke figure argued it in words — "tops level", "set below and right", "the
sheet's reference pair" — and `33S7-9YYJ-6H` recorded honestly that the argument does not work:
"the pitch test does not separate them on this sheet". Neither does stroke weight or stroke
height; `33S7-9YYJ-24` line 21 is a **4** on a column that closes at its printed 201 and its two
strokes are twins. What does separate them is the **x overlap of the two strokes' ink boxes**,
because that is a fact about the form and not about the hand: two digits written side by side
occupy two x slots, and one numeral's two strokes share a slot however far their feet drift.
Measured on **nine figures whose value is fixed by a closure and not by anyone's eye** — three 4s
and four two-digit numbers on 24's closing TOTAL column, the 4 in 6H's TOTAL footing that T-0645
settled at 144, and the 11 in 6H's MANUFACTURES footing that T-0627's column closes on — the two
classes are **+10 to +17** for one numeral and **−13 to +4** for two digits, and they do not
touch. `tools/census_pair_geometry.py` is the instrument; it imports the ink mask and component
finder from `read_census_continuation.py` rather than defining a second pair, and it reads no
digits. The calibration table is committed on `33S7-9YYJ-5V`'s page file under
`total_column.stroke_overlap_test`.

**What it did to `33S7-9YYJ-5V`.** That sheet read six two-stroke figures as 11 and called one of
them its reference pair. They are not one figure: lines **6, 9 and 24** measure +10, +19 and +19
and are **4s**; lines **2, 3 and 4** measure +5, +3 and +5 and stay at **11**. The committed sum
falls from 126 to 105, which does not close anything — the sheet's own footing is still one glyph
short of legible — but it does dissolve the strain that reading recorded and could not resolve.
Line 3 is the cross-check the whole result rests on: it carries a **commerce 4 and a
learned-professions 1**, five persons of that family employed, against a TOTAL column that counts
*persons in each family* — so it is at least 5 and cannot be a 4, and both those columns close
exactly against the enumerator's own footings. An instrument that knows nothing of the ink and an
instrument that knows nothing of the arithmetic agree on the one line that can be tested both
ways.

**Whether the key binds `33S7-9YYJ-8D` is still open, and deliberately.** The calibration is
S. W. Sherman's hand — 24, 5V, 6H and 6Q all carry his name in the printed heading — and **8D's
page file records no division at all**, so nothing yet shows he wrote it. Its six two-stroke
figures, and the +15 by which its lines over-run its printed 106, belong to T-0652, which now has
an instrument it did not have.

**One is shown outright to have no partner here.** `33S7-9YYJ-8D` carries **32** entries, read
line by line by T-0643 and anchored on a thirty-second line the inventory had missed. No left
sheet in images 1-25 carries more than 31, so 8D's left half is not in this image group at all.
That is a fact about the deposit, and it is the frame for the rest: the deposit is ordered by
sorted filename, not by the book, so an opening is only whole inside one group by accident.

**Five have a committed key that matches nothing here**, and each is recorded with its nearest
candidate: `33S7-9YYJ-5D` (125) against printed 222 at 123–124, refused on 31 entries against 30;
`33S7-9YYJ-5S` (189, 29 entries) against printed 226, the group's **only** 29-entry left sheet,
refused because B3 keys 184 and its own lines hold 185; `33S7-9YYJ-6H` (144) against printed 221,
which brackets it at 146 footed and 143 read; `33S7-9YYJ-6Q` (198) and `33S7-9YYJ-5V` (165
favoured, uncommitted) against no 30-entry sheet within eleven. **Four have no key at all yet** —
`33S7-9YYJ-9WS`, `-B1`, `-B2` and `-BF` have unread TOTAL footings and belong to T-0644 and
T-0641.

**What the ten unpaired sheets are actually blocked on** is not more reading of this group. It is
the left-sheet footings of image groups 2 and 3: nine of those sheets are read for names and none
of them for cells, so none of them has a population key to be tested against.


## Printed 232 has no facing leaf in this deposit, and the search that says so (T-0543, 2026-09-05)

Printed pages **230** and **232** were both read to the cell with their family totals, industry
columns, pensioners and schools cells still on a leaf nobody had named. Printed 230 was settled
first: T-0656 attached it to `33S7-9YYJ-K2` on both keys with the sequence agreeing position for
position, and `pages/33S7-9YYJ-NY.json` carries that pairing. Printed 232 was not, and the reason
is worth stating, because it is the reason a pairing question can sit open for four tickets — the
search had only ever been run INSIDE one image group at a time. The deposit is ordered by sorted
filename and not by the book, so a left sheet and its own continuation are in the same group only
by accident.

So this pass ran the search across all three groups at once, and it is exhausted.
`continuation_search_page_232.json` names **every right sheet in the deposit — 37 of them, 33 of
which are household continuations — image by image, with its TOTAL footing and the reason it is
not printed 232's pair.** Seventeen of those footings were read here for the first time: the whole
of image group 51-74, which nothing in this project had opened, plus `33S7-9YYJ-5V`, `-B1` and
`-B2`, the three that T-0642 recorded as owed.

**Printed 232 wants a sheet of 31 entries footing 193 (by its marks) or 195 (by its own
footings), and no such sheet exists here.** The nearest unpaired footings in the whole deposit are
`33S7-9YYJ-6Q` at 198 — refused by its 30-entry line count — and `33SQ-GYYJ-Z1` at 181, twelve
short. One sheet and one only matches on the line count: `33SQ-GYYJ-9J5`, measured at 31 entries
at every grouping distance the tool offers. It foots 179, and its TOTAL column read at
magnification opens 5, 6, 25, 11, 8 against printed 232's 5, 7, 5, 9, 6 — agreeing at position one
and nowhere else, with none of the page's distinctive 13, 14, 16 run anywhere on the leaf. Refused
on the population key and refused again on the sequence.

That is a statement about the deposit, not about the schedule. The 1840 book had a facing leaf for
every page it enumerated; these 74 images do not hold all of them, which is the same fact that
leaves ten of image group 1's eleven continuations without a partner. `pages/33S7-9YYJ-W6.json`
now says so in its own `pairing` block: those 31 households' family totals and industry columns
are **absent rather than unread**, and nothing should be filled into them from the left sheet's
own cells. Recovering them needs a leaf from outside this deposit — FamilySearch collection
1786457, recorded as login-walled and inaccessible rather than absent, or a National Archives
microfilm this project does not hold — and that is a new source record, not a re-reading.

## Printed 232's continuation, found on the film (T-0736, 2026-09-06)

The search above was exhausted and it was also right: the leaf is not in this deposit. It is on the
**film**, and it always was.

T-0736 tried both of the routes the search left open. **FamilySearch collection 1786457 is still
shut**: the collection's search page, the image ark of printed 232's own left sheet, and the
collection's search service were all fetched unauthenticated from the runner on 2026-09-06 and all
three answered HTTP 403. That is inaccessibility and not absence, and nothing about what the
collection holds may be read out of a refusal.

**The National Archives microfilm was the open one, and nobody had ever looked up its roll
number.** The 1840 population schedules are NARA microfilm publication **M704**, 580 rolls;
archives.gov names the publication and says the images are on the genealogy sites rather than on
NARA's own. The Allen County Public Library Genealogy Center scanned the Illinois rolls for the
Internet Archive, one item per roll, and each item's description carries the contents of the whole
state. **Roll 57 is "Coles, Cook, Crawford Counties"** — item `populationsc18400057unit`, 330
leaves, public and unauthenticated.

**Leaf n166 of that roll is printed page 232, and leaf n167 is its continuation.** The leaf was
identified by its own names rather than by the page stamp: n166's 31 heads of families are printed
232's 31, in printed 232's order, opening Nicholas W. Smith, Jos. D. Boone, Jacob Miller, Amy Brown
and Wm J. C. Scovill. The stamp agrees, and the film's order agrees again — on this roll a left
sheet is filmed before its own right, so the even leaves carry the names and the odd ones the
continuations.

**It pairs on both of T-0642's keys and on the sequence screen besides.** n167's TOTAL column
carries 31 entries against 31 ruled lines, its printed footing reads 195 — the figure printed 232's
own footings give — with 198 named as the arguable alternate at this exposure, and the column opens
5, 7, 5, 9, 6, 4, which is printed 232's own per-line free-person count. That last strand is the
one that matters most, because it is the same screen that REFUSED `33SQ-GYYJ-9J5`: the deposit's
one 31-entry sheet opens 5, 6, 25, 11, 8. The pairing does not rest on the footing glyph, and the
glyph keeps its alternate rather than being chosen.

`pages/33S7-9YYJ-W6.json` now reads `paired_outside_this_deposit`, and the leaf lands as a source
of its own — `census_1840_chicago_nara_m704_roll57`, with each leaf's URL and sha256. **No cell of
n167 has been read.** The 31 households' industry, pension and schools cells are readable now and
they are still unread; that is a separate demonstration and it has its own ticket. Nothing may be
filled into them from the left sheet's own cells in the meantime.

**What this says about the deposit as a whole.** It is a partial selection of frames, exactly as
the search guessed. The ten continuations of image group 1 that stand without a partner are the
same hole, and roll 57 is where they will be.

**A by-product worth having.** Counting the deposit by side classified all 24 leaves of image
group 51-74 for the first time: 9 left sheets and 15 right, listed in the same file so that T-0496
does not have to open them again to find the names. One of the nine is unlike anything else here —
`33SQ-GYYJ-PW` is the densest leaf in the deposit and writes STREET NAMES down its left margin
beside the households. It is the leaf T-0496 should open first.

## Images 51-74 inventoried, and the sheet that names the wards (T-0741, 2026-09-05)

`coverage.json` carried two image groups while its own `schema_note` promised three, so the
last **24 images of the deposit — 51 to 74 in the sorted filename order — were the only ones
nothing described**. A hole there could not fail. They are now declared, one entry each: what
the sheet is, which side it is, the printed page number where it carries one, and how many
ruled lines carry an entry. Nothing else was read from them — no name, no cell, no serial, no
resident. That is T-0746's, and this inventory is what lets it be parcelled by printed page.

**Nine left sheets, fifteen continuations, one of them blank.** The eight printed page numbers
this group carries are **212, 213, 214, 220, 223, 233, 235 and 240** — a set that does not run
consecutively, so the deposit's filename order is not the printed order and an opening is whole
inside one group only by accident. `33SQ-GYYJ-BH` is printed, ruled and wholly unfilled, which
is declared rather than omitted for the same reason printed 238 is. Two of PR #670's seven
calibration pages fall here exactly as the corrected deposit note predicted: **233** on
`33SQ-GYYJ-RJ` and **235** on `33SQ-GYYJ-ZQ`.

**Where the printed page number lives.** On a left sheet it is printed at the TOP RIGHT, past
the marshal's signature. A continuation sheet carries none of its own; what shows through at
its top left is the number printed on the other side of the leaf, read backwards. That
show-through is legible on some of these sheets and is deliberately NOT recorded as a reading —
it is not this sheet's number, and pairing is a fingerprint job, not a bleed-through job.

**The find is `33SQ-GYYJ-PW`.** It is a left-sheet form used as a recapitulation, and it is the
third non-household sheet in this deposit. Instead of names its first column runs **1 to 30**
under the heading *Page*; each numbered page carries its own totals across the free-white age
bands; and a brace in the left margin gathers the thirty pages into **First, Second, Third,
Fourth, Fifth and Sixth Ward**, each closed by a subtotal rule, with a grand total at the foot.
The margin heading reads *"Recapitulation of [?] (Chicago City) preceding pages"*, one word
struck through before the parenthesis.

That shape is the shape of printed **237** — the recapitulation this README already describes,
whose thirty ruled lines carry division totals gathered into six blocks. 237 gives the division
totals and no more; `33SQ-GYYJ-PW` gives the same thirty rows broken out by age band and **names
the six groups as the city's wards**. So it is a second, independent statement of the same
recapitulation, and it is worth three things this pass does not attempt: it can be added against
237's blocks, it may bear on the residual of **4** that 237 leaves open against the 4,470 at its
foot, and it attributes every one of the thirty enumerating pages to a ward. Thirty pages at the
~31 ruled lines these sheets carry is about 930 households against the **964** the IPUMS extract
holds, which makes it a completeness test for the whole reading programme. None of that is done
here. This pass records that the sheet exists and what it is.

**One sheet is agricultural throughout.** `33SQ-GYYN-38YY` carries a figure in the AGRICULTURE
column on every one of its 31 lines, footing 53. Chicago's own sheets foot agriculture at or
near zero and carry their families under commerce and under manufactures and trades, so this is
evidence about which enumeration district the sheet belongs to. The question is left open rather
than answered.

**What the line counts are worth.** They are read off a rendering of each image at 820 px across
the left half of the sheet — the NAMES column on a left sheet, the TOTAL column on a continuation
— and are stated to the nearest line, exactly as groups 1 and 2 state theirs. Both of those
groups found the estimate reads LONG by one to four lines and never short, so a transcribing pass
should expect to remove lines rather than find them. Two counts here have an independent check:
`33SQ-GYYJ-NV`'s seventeen TOTAL figures sum to **exactly** its printed footing of 70, and
`33SQ-GYYJ-9ZK`'s twenty-three sum to 118 against a footing of 119.

## The thirty columns a continuation sheet's reader never names, swept (T-0629, 2026-09-05)

`read_census_continuation.py` names eight columns of a right-hand sheet — TOTAL and the seven
industry columns — because that printed run is the one stretch of the form whose columns can be
named off pitch alone. The other **thirty** are wide blocks of unequal pitch, and the tool has
always reported their ink as one lump per block with a note saying the lump is dominated by
printed rules and is not evidence either way. On `33S7-9YYJ-6H` that left the twelve SLAVES
columns, both PENSIONERS columns, the ten DEAF AND DUMB, BLIND AND INSANE columns and the whole
SCHOOLS, &c. block unlooked-at, and it left the sheet's own note saying a 1 and a 40 stood at the
head of the schools block, still not read.

`tools/read_census_lower_blocks.py` names them and sweeps them. It reads no digit — it says where
to look and what the ink is like when you get there — and it reports four measurements per
component: the box, the share of pixels standing 120 or more grey levels below local background
(**solid**), the paper the ink shuts in after a 5 px closing (**encloses**), and the distance to
the nearest printed rule.

**The pale-rule problem is per block, and it is stated rather than tuned.** This leaf already
needs `--cover 0.50` where its sibling 5V takes the 0.6 default. The six white
deaf/dumb/blind/insane columns are paler again: at 0.50 only the block's outer rules stand, and
the four interior ones arrive at 0.30. At 0.25 two of them drop out. 0.30 is not a threshold the
reading was tuned to; it is the only one at which that block's run is complete.

**Thirty columns swept, two cells written.** Fifteen components survive in the body and six in the
footing band. Five are the enumerator's ink. Every other one is a printed rule clipped by the
sweep window, a horizontal rule crossing the band, a round blot, or the feathered ghost of writing
on the other side of the leaf — and the discriminator is measured, not judged: the sheet's 55
committed number groups run 10–65 px wide and 15–82 tall, median 34×41, and every rejected
component is at most 19×26 with a solid fraction of 0.01–0.14. So **744 cells** are committed
blank, which on this form is a zero.

**The 1 and the 40.** They stand in **Primary and Common Schools** and in the **No. of Scholars**
immediately right of it — not the academies pair, which is empty on every line — and they stand
on **line 1**. Placing them took a measurement the sheet had not needed before: the leaf *rises to
the right*, its upper body rule falling from y613 at x300 to y580 at x3500, and the committed line
index was fitted to industry ink 2 200 px to the left. Corrected for that slope the index predicts
line 1 at y659.1 where the figures are; their ink centres are y661.5 and y662.5, residuals of
+2.4 and +3.4 px against an index whose own rms is 4.81. Line 2 would be at y734.

**The 40's nought is the only bowl on the sheet outside the industry run.** Flooding each
component's background from its box border, exactly one of the twenty-one encloses paper: the
48×46 figure at x3536–3584, which encloses 25 px. That is what rules out 4, 44 and 11 — and it
hands the leaf an *independent* instance of the two-stroke 4 that T-0645 had to argue into from
the TOTAL footing's arithmetic. Here the same two-stroke figure is read off form, standing beside
a nought it cannot be.

**And the block is footed, which nothing had looked for.** `footer_blank_columns_note` listed the
blocks carrying no figure at the foot of this sheet; the schools block was absent from that list
only because nobody had examined it. Under Primary and Common Schools the footing is a single bold
slash of the body figure's own form — read **1**, and **that column closes**: one entry of 1 in
the body, 1 at the foot. It is the first column on this leaf outside the industry run to close.

Under No. of Scholars the footing is **written and does not read**. Three components spanning
38 px where the body's 40 spans 48; the bowl test returns 0 against the body's 25, the first glyph
carries no crossbar, and the ink is half the body figure's depth — a drier pen at the foot of a
leaf already curling into the binding. It is where a 40 would stand and it is not recorded as one,
because assuming it is exactly how a column is made to close. **T-0754** carries it.

The seventh schools column, *No. of Scholars at public charge*, has no right-hand rule at any
threshold down to 0.30: the gutter takes it at about x3640. It is recorded **unread, not blank** —
a blank here would mint a nought nobody read. **T-0755** carries it.

None of this closes the sheet. The TOTAL column still stands 7 short of its 144 footing.

## Two of image group 2's continuation sheets read line by line (T-0658)

`33S7-9YYN-3CF6` and `33S7-9YYJ-V4` are read to the cell on the rule the continuation
readings have used since T-0540: **a column is committed only when the per-line values sum,
column by column, to what the man who took the census wrote at the foot of his own sheet.**
Neither leaf carries a printed page number and neither is paired, so nothing here attaches a
household figure to a name; both remain LATER EVIDENCE that names nobody.

| image | lines | footed columns | closes | what it says |
|---|---|---|---|---|
| `33S7-9YYN-3CF6` | **27** | TOTAL 116 · agriculture 25 · canals 31 | TOTAL and canals **exactly**; agriculture short one illegible cell | 116 people, 25 in agriculture, 31 on the canal |
| `33S7-9YYJ-V4` | **21** | TOTAL 100 · agriculture 33 | TOTAL **exactly**; agriculture reads 34 against 33 | 100 people, agriculture on nearly every line |

The group's third continuation sheet, `33S7-9YYJ-VJ`, is **not** read here. T-0658 was sized
at three and two is what one run could demonstrate, so the third is split out as T-0762 with
the method above written down for it rather than shipped as a self-invented half.

**`33S7-9YYN-3CF6` is a canal sheet, and that is the reading's finding rather than its
premise.** Twenty-seven households hold 116 people; twenty-five of them are returned in
agriculture and thirty-one in the navigation of canals, lakes and rivers, and *not one*
person on the leaf is in commerce, in manufactures and trades, in the learned professions,
in mining or on the ocean — the other five industry columns are blank down all 27 lines and
carry no figure at the foot. The last seven lines are what the canal looks like in a
schedule: lines 21, 22 and 23 are households of ONE with that one man on the canal, and
lines 24, 25, 26 and 27 are households of 11, 7, 7 and 3 with **every** member of each
returned on the canal. Four shanties and three single men, consecutive in the enumerator's
walking order, on a leaf taken while the Illinois and Michigan Canal was being dug.

**The two-stroke figure is settled on this leaf, by arithmetic.** Line 24 carries the form
this deposit has argued about since T-0627 — two parallel slants that read as `11` or as
this hand's `4` — and it carries it twice, in the TOTAL column and in the canals column.
Read as 11 both columns close on the enumerator's own footings exactly, 116 and 31; read as
4 they come to 109 and 24. The same leaf writes a plain `4` on four other lines as one
cursive glyph and not as two strokes, so on this hand the forms are distinct and the
two-stroke one is 11. **That is a witness about this hand on this leaf and it is not carried
to `33S7-9YYJ-5V`, `-6H` or `-8D`**, whose own tickets are open: a second enumerator's 4 is
a second question.

**One cell on 3CF6 is illegible and the column that holds it is therefore not committed.**
Line 5's agriculture cell sits on a hard vertical crease that has taken the body of the
figure with it. The 26 legible lines sum to 23 against a footing of 25, so the residual of
exactly 2 sits in exactly one unread cell — the column is one legible cell away from closing
and the sheet's own arithmetic asks for a 2 there. That is *not* written into the record. An
arithmetic implication is not a reading, the rule is that a column commits only when the
lines READ sum to the footing, and the cell is null with the residual named and located.

**`33S7-9YYJ-V4` corrects its own line count, and the correction is not a matter of
opinion.** The contact-sheet pass declared 31 lines "to the nearest line"; T-0656 counted 20
off a magnified strip and said why that count was soft. This pass reads the TOTAL column
glyph by glyph and finds **21** entries — and they sum to 100, which is exactly what the
enumerator footed. At 20 lines no subset of the reading reaches 100. The line the strip pass
missed is line 19, a pale `5` written low between a `7` and a `2`. `pairing_key_26_50.json`
carries the corrected key; the pairing verdict does not move, because the sixteen left
sheets read anywhere in this deposit run 29 to 33 lines and none foots 100.

**V4's agriculture column is an ATTEMPT and not data.** Its 21 lines read 34 against a
footing of 33. One person out is one cell, not a spread, and on this exposure there are
three cells that could carry it — line 2 (read 6, alternate 5), line 7 (read 2, alternate 1)
and line 16 (read 4, alternate 1). The reading is kept whole in `cells_first_pass`, where
nothing downstream can consume it as fact, and `cells` carries null for that column on every
line. This is the `33S7-9YYJ-5S` treatment applied to one column instead of a whole sheet.

**The tooling did not survive contact with either leaf, and the reason is the same on both.**
`tools/read_census_continuation.py` refuses 3CF6 outright — *"no industry run bracketed by
TOTAL and PENSIONERS: the form is not as expected"* — at every `--cover` from 0.40 to 0.60,
and it cannot fit a row grid to V4 at all. The cause is measured rather than guessed: **these
rules lean.** On 3CF6 the nine printed rules of the TOTAL-and-industry run stand at 1004,
1194, 1265, 1329, 1396, 1480, 1564, 1647 and 1712 px at the head of the body and 12 to 17 px
further right at its foot; on V4 the lean is 41 px. That tool locates its rules from a single
darkness profile over the whole body, and a rule that walks 41 px across the leaf smears out
of such a profile entirely. Both page files carry the banded measurement that replaced it, so
the next reader does not spend the same passes rediscovering it. The tool is **not** changed
here — the fix it wants is a banded profile, and that is filed as T-0761 rather than
slipped into a reading.

Both leaves also show the other trap a fixed grid sets. A tenth apparent rule on 3CF6 at
x=1250, and one on V4 at x=1333–1365, appear in every band and do **not** lean with the
printed rules. They are creases. V4's runs through the TOTAL column, which is why that
sheet's footed `100` looks at first sight as though its last `0` has crossed into the mining
cell; it has not — the mining rule is 60 px further right.

## Which coverage shape this file is in, and why it stays in it (T-0536)

`coverage.json` here is in the **`images[]` shape**, not the `declarations[]` shape
`tools/research_domains.py` fixed for the other seven domains — and after T-0536 that is a
decision rather than a leftover. **The gate learned this shape.** `research_domains.py` reads
an image object as a declaration of unit `image`, item its FamilySearch id, ticket the one its
group's `declared_by` opens with; the same hole assertion that guards a declared page now
guards a declared image.

Three reasons it went that way and not the other:

1. **The file is being appended to.** T-0496 and the sheet-reading tickets split out of T-0494
   and T-0495 all extend this one document, on branches that cannot see each other. Migrating
   it underneath them loses readings to a merge, and a lost reading is a sheet read twice.
2. **`declarations[{unit, items[], ticket}]` has nowhere to put `read_state`, `page_file` or
   `lines_with_an_entry`** — and those three are the evidence that a hole is a hole. T-0536
   forbade dropping a field to fit the shape, so the shape gave way instead.
3. **`declarations[]` is a projection of `images[]`, not a rival to it.** A projection can be
   derived, so nothing had to be hand-migrated at all.

**`read_state` is what the gate grades on, and the distinction is the whole point.** An image
whose state is `inventoried_only` is declared as INVENTORIED — the sheet has been looked at and
described, and nothing has been read off it — and it is *not* asserted to be reached; its
`page_file` must be `null`, because an inventoried sheet has nothing read off it to point at.
Every other state declares the image READ, and a read image must name a committed `page_file`
and be reached by a `pages/*.json` naming the same `familysearch_id`. Run the two states
together and "declared" would mean "seen", and a hole could never fire.

Measured when this landed, on the dev of 2026-09-05: the shared gate went from **0 declared
coverage items** in this domain to **46 declared read and 28 declared inventoried** — 74
images, the whole deposit, and 357 to 403 declared items across all eight domains — with no
reading touched. The counts moved because the gate can now see what was already committed.

Five new self-test cases hold it: an image declared read that no `pages/`
file reaches, an inventoried image that names a page file, a read image that names none, a
declared page file that is not committed, and an image with no `read_state` at all.

## The Dalton Data Bank index is one surname, not a city (T-0497, 2026-09-05)

`data/sources/dalton_1840_chicago_census_index.json` had been cited for exactly one man since
T-0479, and the ticket that asked for it to be read whole described it as *"a free 1840 Chicago
head-of-household index by ward"* and *"the cheapest second reading of the 1840 heads the project
can get"*. **It is neither.** The Dalton Data Bank is a one-surname genealogical databank: its
Illinois page extracts Dalton, Dolton and Daulton entries out of census indexes, marriages, births,
deaths, directories, land sales and naturalizations, and its whole 1840 census block is **20
Illinois rows**. It cannot cross-check the spelling of any 1840 head who was not called Dalton, and
it is not a second reading of the 964 IPUMS households.

All three of its pages were fetched on 2026-09-05 (HTTP 200 each: the front page, `Illinois.html`,
`Illinois_Page_2.html`); there are no per-ward pages, because the ward is a value inside a row.

| what the 1840 block holds | rows |
|---|---|
| Illinois rows, read whole | 20 |
| in a Chicago ward | 3 — Edward Dalton (1st), Michael Dalton (2nd), "Mr. Dalton" (1st) |
| Cook County outside a Chicago ward | 4 — Thornton Precinct, Bridgeport, and two with no place |
| outside Cook County | 13 — Morgan, Knox, Pike, Adams, Scott, Jo Daviess |

The rows are in `records/dalton_index.json` (names only: the page's rights are `check_required`),
and `dalton_index_crosswalk.json` beside it carries the adjudication — 0 merges, 7 refusals, 1
candidate — in `identity.json`'s shape. It is written as its own file because `crosswalk.json` is
generated by `tools/crosswalk_census_1840_heads.py --build` and a hand edit there would be lost.

**The one thing the reading changes, and it changes no grade.** T-0479 kept the index's *Edward
Dalton, Chicago 1st Ward* as an unasserted candidate for the letter-list Edward Dalton, and read
the First Ward as part of the agreement. The block, read whole, carries a **second** First-Ward
Dalton household — *"Mr. Dalton, Cook Co., 1 Ward Chicago"*, surname-only and so never an identity
here — and a third in the Second Ward. The ward locates the name among at least two Dalton
households and narrows nothing. The candidate stands exactly where T-0479 left it, now qualified;
T-0513 consolidates and T-0514/T-0515 apply.

**Swept and empty, which is evidence rather than a gap.** The surname meets **0** of PR #670's 210
named heads, **0** of the 1833–1835 poll and voter lists, and **0** of the federal tract sales the
`land_sales` domain read through 1836. The first of those is the useful one: the three Chicago-ward
Dalton households the index names are not on any of the seven printed pages read so far, so they
stand on unread images of this deposit — something for T-0496 and T-0657–T-0659 to watch for. The
index's own 1820 and 1830 blocks carry no Cook County row at all.

## The adjudication caught up with the reading, and a gate now says when it has not (T-0714, 2026-09-06)

The owner's complaint, in its purest form: *the pages were read and nothing across.* On `dev`,
`crosswalk_census_1840_heads.py --check` was red and had been for some time — **498** named heads
adjudicated on disk against **788** read off the page images. 290 heads of finished reading had
never been put to the ladder. Nothing said so, because `tools/check.sh` ran that tool under no mode
at all, while every sibling crosswalk — Norris 1844, Fergus 1843, the three Fergus 1839 passes, the
death notices — fails the gate the moment its committed file stops re-deriving.

**Re-derived, and the movement itemised.** `--build`, then `--report --baseline` against the file
that was on disk. Nothing was dropped: the 290 are additions, and they come off ten sheets read
after the crosswalk was last built.

| printed | familysearch | heads added |
|---|---|---|
| 209 | 33SQ-GYYJ-93Y | 31 |
| 211 | 33SQ-GYYJ-97P | 30 |
| 218 | 33S7-9YYJ-PC | 30 |
| 219 | 33S7-9YYJ-9K3 | 31 |
| 224 | 33S7-9YYJ-JM | 30 |
| 227 | 33SQ-GYYJ-6V | 31 |
| 233 | 33SQ-GYYJ-RJ | 31 |
| 235 | 33SQ-GYYJ-ZQ | 24 |
| 239 | 33S7-9YYN-3CDH | 31 |
| 241 | 33S7-9YYJ-Q1 | 21 |

So the answer to *"did reading those pages produce anything?"* is a number and not a shrug: the
sheets carried the town **6 more matched heads and 11 more candidates**, 5 → 11 matched and
5 → 16 candidate, and `--report` will print the same table off the committed file at any time.

**Ten heads already on disk changed outcome, and every one of them is the ladder reading a town
that moved, not a rule that moved.** No rule was edited in this pass. The 1835 pools gained people
between the two builds, so a surname absent in the old build is present in the new one — 21 heads
moved from L2 *no surname in the 1835 pools* to L3 *given-name conflict* on that ground alone.

| the head | printed, line | was | is | why |
|---|---|---|---|---|
| John Knight | 207, 21 | refused | candidate | the surname is in the pools now |
| James A. Smith | 207, 23 | refused | candidate | ditto, and no longer a given-name conflict |
| Henry Fitz Simmons | 207, 28 | refused | candidate | ditto |
| William Brown | 208, 24 | refused | candidate | ditto |
| John C. Rue | 216, 18 | refused | candidate | L6a — the 1844 directory holds the person, the read is graded `low` |
| **Elijah Peacock** | 217, 19 | refused | **matched** | L6 — unique on both sides, and separately adjudicated into BOTH the 1843 and the 1844 directory |
| Seth Johnson | 226, 7 | refused | candidate | L6a — 1844 directory at a stated address, read graded `low` |
| John Wilson | 229, 2 | candidate | **refused** | L5 — a second 1840 line now carries the name, so it identifies nobody |
| John H. Kinzie | 232, 25 | candidate | **refused** | L5 — the town now holds two John H. Kinzies |
| Ed. Kimberley | 234, 3 | refused | candidate | the surname is in the pools now |

The two withdrawals matter as much as the promotions. A candidate is a claim about a person, and
L5 withdrew two of them because the name stopped being unique — which is the ladder working, not
the crosswalk losing something. Peacock is the only promotion to `matched`, and it rests on a
discriminator independent of the name in the sense this file has always meant: attestation in
Chicago *after* the 1840 book was taken.

**Gated, in the same commit as the re-derivation, so the gate never lands red.** `check.sh` now
runs `crosswalk_census_1840_heads.py --check` beside the bridges gate it belongs with.

**And the class of fault, not just this instance.** `tools/audit_check_gates.py` surveys every tool
carrying a `--check` mode and reports which ones `check.sh` never runs one on: **18 of 100** today,
17 of them not invoked by the gate under any mode at all. Gating those 18 is work with rulings in
it — `mint_letter_list_residents.py --check` is red for a reason that is T-0691's, not this
ticket's — so this pass does not do it. What it does is stop the set GROWING:
`data/research/check_gate_baseline.json` records the 18, and `audit_check_gates.py --gate` fails
when a tool appears with a `--check` mode nothing runs and no line saying why. T-0896 drains the
list.

One sheet in the by-sheet report has no printed page: `33S7-9YYJ-9MX` carries
`printed_page: "unknown"` because the number is torn off the image. Its 31 heads are adjudicated
like any other; only the label is missing.

**What moved downstream, and what deliberately did not.** The cross-domain identity master is
derived from this crosswalk among its sources, so it was re-derived in the same commit: declared
merges 379 → **385**, declared refusals 1,680 → **2,084**. Identities, appearances and
identities-on-a-card do not move at all — 6,697 / 10,412 / 1,357, unchanged — because this
crosswalk mints nobody and regrades nobody. It rules on names; the town's population is untouched,
and applying a `matched` head to a household record is still `apply_census_1840_bridges.py`'s job
under T-0515, on the ratified ladder, one bridge at a time.

**One ruling reaches a person and not their card, and it is written down rather than absorbed.**
`measure_research_spend.py --gate`'s second hop — *has the town's card learned what was ruled onto
the person?* — went red on exactly one head: **Ira Couch**, printed 211 line 3, ruled L7 candidate,
whose card cites no 1840 source. Spending it means writing a household record, which this crosswalk
does not do by design. The domain's write-hop ceiling was raised from 0 to 1 with that reason
recorded in the baseline, and **T-0899** spends it and drops the ceiling back to 0. A ceiling raised
by one with a named person on it is a debt anybody can see; a re-derivation that quietly wrote the
card would not be.

## The ruling reached the card, and the meter that said it already had (T-0698, 2026-09-07)

**T-0714 made the adjudication re-derive and gated it. It did not make the ruling arrive.**
`crosswalk_census_1840_heads.py --check` was green on `dev` and said what it always says —
788 named heads, 12 matched, 15 candidate, 761 refused. Those 27 matched and candidate heads
name a person this town holds a card for. **Twelve of the 27 cards carried the source at all,
and fifteen did not** — among them seven of the twelve MATCHES, including Philo Carpenter,
John Calhoun, Ira Couch, George W. Dole and William H. Stow. The town's best-documented men
were matched to a line on an 1840 sheet and their cards had never been told.

**And the instrument that exists to catch exactly this reported the domain fully spent.**
`tools/measure_research_spend.py`'s second hop counts a ruling that names a person whose card
has not learned it, and it read census_1840 as *27 reached, 27 on a card, 0 unwritten*
throughout. It reads `crosswalk.json` — the spelling-pair rulings — and has never looked at
`resident_crosswalk.json`'s heads. A meter that cannot see a hop reports it green. That is why
this stayed invisible under a gate that was already watching, and it is the same shape as the
fault T-0714 fixed one layer up: *a gate cannot notice a reading it never looks at.*

**T-0670 met the same wall from the other side.** It rebuilt the crosswalk, the rebuild carried
one ruling more than the domain had spent, `measure_research_spend.py` reported *ceiling 0 (+1)*,
and that run reverted rather than take a ruling that was not its business.
`tools/spend_census_1840_heads.py` is that ruling taken generally rather than for the one person
it happened to be: **whatever the crosswalk reaches, the card is told.** 27 people — 12 as matches
and 15 as candidates — each gaining the source id in `persons[].sources` and one paragraph in
`persons[].note`. `head_spend_1835.json` is the ledger of those writes. It carries no "crosswalk"
in its name on purpose, so the spend meter does not read a record of writes as a second
adjudication.

**A candidate is written as a candidate.** The paragraph says so in those words — the name agrees
and is unique on both sides, nothing independent of it was found, nothing is asserted from it and
no household of 1840 is carried back to 1835. A match's paragraph names the discriminator that
decided it. Reading a candidate and a match the same way on a card is exactly what the crosswalk's
ladder exists to prevent, and the pass's self-test holds the distinction over every paragraph it
writes.

**Two fields, and no grade moved in either direction.** Not an arrival, not a claim block, not a
placement, and above all not `present_on_scene_date`; `--self-test` holds that by diffing a record
through the applier and asserting the changed key set. The ladder is not applied here — T-0515
applies it against every source at once, and this pass hands it the evidence and not the verdict.
`grades_changed: 0` is in the ledger's own counts.

**Three gate steps in `tools/check.sh`, beside the `--check` T-0714 added.** Every ruling is on the
card it names, once each; no card carries a paragraph for a ruling the crosswalk never made; and —
T-0700's lesson taken rather than relearned — a paragraph that is PRESENT but no longer says what
the crosswalk says is a failure, not a pass. A card still calling somebody a candidate after the
ruling became a match is wrong in the one way that looks exactly like being right.

---

## One page read here is not in the deposit at all: printed 232's continuation

`pages/m704_r57_n167.json` is the only reading in this directory taken off a leaf the
FamilySearch deposit does not hold. That absence is a finding, not an oversight:
`continuation_search_page_232.json` exhausted every right sheet of all 74 images looking for
printed 232's other half and refused all 33 candidates — the nearest unpaired TOTAL footing in
the deposit is 12 short of the 193 printed 232's marks require. T-0736 then found the leaf on the
film instead, as leaf **n167** of the Internet Archive's scan of NARA M704 roll 57
(`census_1840_chicago_nara_m704_roll57`), and T-0912 read it.

**The deposit's read-only rule is untouched.** No image, crop or render from the roll is
committed. What makes the reading re-checkable is the sha256 the source record carries for the
leaf, and the geometry the page file states — the shear that carries the printed rules down a
warped leaf, and the x bounds of the TOTAL column and the seven industry columns at the top of
the body.

**What it settles.** All 31 entries of n167's TOTAL column reproduce printed 232's own per-line
free-person counts, position for position, at offset 0 and nowhere else — the strongest pairing
key any sheet in this directory carries, and the two readings were made independently off two
different digitisations. The footing glyph T-0911 could only read as *195 or 198* is settled at
**198**, against the leaf's own 5s, its own 9 and its own 8.

**What it leaves open, on purpose.** Two of the leaf's four footings do not close on the entries
above them, and both are short by exactly five: the TOTAL column reads **193** against a footing
of **198**, and manufactures and trades reads **10** against **15**. Commerce (4), navigation of
canals, lakes and rivers (18) and learned professions (8) close exactly. Nothing was re-read to
make the other two come out, and no cause is proposed for the repeated 5.

## T-0974 — continuation 33SQ-GYYJ-9J5 (2026-09-07)

All 31 entries on image 51 are recorded in `pages/33SQ-GYYJ-9J5.json`, including
six unresolved family totals. The 25 readable totals sum to 150; that is a partial
sum, not the sheet population. The enumerator writes **179** at the foot. Four
assignments of the recorded alternatives would reach 179, so arithmetic alone
cannot settle which separated-stroke cell is 11 rather than 4. No assignment is
selected. Three occupation columns close independently: commerce **6**,
manufactures and trades **8**, learned professions and engineers **2**. The other
four industry columns have no written entries.

The slave and pensioner blocks are blank. The disability block has one unresolved
short vertical mark in the white-blind column on line 30; its 8 by 28 px box and
reason for withholding a value are recorded. The seven school columns are blank;
the narrow illiteracy column is obscured at the binding and remains unread.

The page stays **unpaired**: no available printed population key for a 31-entry
left sheet equals 179. Sixteen equal-line-count candidates are listed, with
unread population keys distinguished from mismatches. No name, serial, 1835
resident, occupation or grade is derived from the unpaired continuation.

T-0973 was split under the queue's one-leaf-per-run rule. T-0974 owns this reading;
T-0975 preserves the remaining twelve filled continuations and the blank leaf in
the parent's queue position. The continuation coverage count includes inspected
lines with unresolved cells; it is not a claim that every glyph was deciphered.


### T-0976 — open PR reconciliation (PR #1040)

Integrated T-0964 (BP/P5) and T-0966 (PW) without replacing later dev work. The four earlier competing page readings are retained verbatim under `data/research/census_1840/second_readings/`, with original commits, content hashes and name comparisons. The PW page numbers are excluded from both head and identity readers. T-0969 and T-0970 repair courtesy-title parsing and the Loyd identity split. See `docs/RESEARCH/open-pr-reconciliation-2026-09-08.md` for each old PR’s disposition and the unresolved research disagreements.

## T-0977 — continuation 9SQ: thirty entries, four unresolved totals

Image 52 is read in `pages/33SQ-GYYJ-9SQ.json`: 30 occupied TOTAL entries,
all seven industry columns, and the other visible blocks. Four totals remain null
(lines 5, 7, 13, 16), with visual alternatives. The 26 readable totals sum to 149.
Only one combination of those alternatives reaches the written 175, but arithmetic
is not a reading; none is filled. Agriculture 1, commerce 4, inland navigation 1
and professions 6 close independently. Four clear manufacturing entries also sum
to its footing 4, but a fifth short upright mark stays unresolved. A small loop
beside a slave-column rule is unresolved; the obscured school/literacy edge is unread.

Printed 224 (JM) shares 30 households and 175 people, but only 2 of the 26
readable right-hand totals match its independently committed household sequence.
That coincidental two-key match is refused. Printed 216 (DD) has 175 people but
31 households and fails the count. The sheet stays unpaired and assigns no names
or occupations to 1835 residents. Measured column bands, crop boxes and the
instrument's truncated-body limitation are recorded on the page.

Group 3 now has three continuations read line by line and twelve inventoried-only
images. T-0975 was split in place: T-0977 owns this leaf; T-0978 retains eleven
filled leaves and blank BH, one leaf per run. PR #1041 carries this completion.

## T-0979 — continuation 9ZK: twenty-three households, unpaired

Image 53 is recorded in `pages/33SQ-GYYJ-9ZK.json`, with all 23 occupied TOTAL
entries and seven industry columns inspected. Nineteen totals are read and sum
to 95; lines 3, 4, 18 and 21 remain null with alternatives. Their one conditional
completion to the written footing 119 is recorded without filling any cell.
The inventory's old strip sum of 118 is not promoted to a reading.

Agriculture closes at 2 + 1 + 1 = 4. Eleven manufacturing entries close at 21,
including the independently read 7 on line 20. Inland navigation has one body
entry and no written footing. A horizontal professions mark, a crossed mark
beside a disability-column rule, and an upright mark near the school binding
remain unresolved. The literacy column is unread. Geometry records the measured
bands, individual crop boxes and the instrument's spurious component groups.

The sole committed left sheet with 23 households is printed 225 (9HY), whose
115-person footing agrees with its own cells. It fails this sheet's 119-person
key. No household identity or 1835 occupation is assigned. Group 3 now has four
continuations read line by line and eleven images still inventoried only.
T-0978 split in place: T-0979 owns this leaf, T-0980 retains ten filled leaves
and blank BH. PR #1042 carries this completion.

## T-0981 — continuation BS: twenty-nine households, unpaired

Image 56 is recorded in `pages/33SQ-GYYJ-BS.json`, with all 29 occupied TOTAL
entries and every continuation block inspected. Twenty-six family totals are
readable and sum to 102. Lines 4, 10 and 12 remain null with alternatives 4 or
11; the resulting conditional totals are 114, 121, 128 and 135, none equal to
the written footing 131. The discrepancy stays recorded and no glyph is chosen
from the arithmetic.

All seven written occupation and school footings close independently: agriculture
2, commerce 7, manufactures and trades 5, inland navigation 1, learned professions
1, one primary/common school and 115 scholars. Mining and ocean navigation are
blank in the body and footing. The slave, pensioner, and disability blocks are
blank; the literacy column at the bound edge remains unread.

The only available left-sheet key with 29 occupied households is printed 226,
with population 184. The only population key of 131 is printed 208, with 30
households. Neither passes both keys, so the sheet remains unpaired and sequence
evidence is not used. No household identity, resident, occupation, or school fact
is projected into 1835. Group 3 now has five continuations read line by line and
ten images still inventoried only. T-0982 retains the remaining nine filled leaves
and blank BH, one leaf per run. PR #1043 carries this completion.

## T-0983 — continuation FS: twenty-seven households close at 125

Image 58 is recorded in `pages/33SQ-GYYJ-FS.json`. Native-resolution row crops
correct two contact-sheet inventory readings: 27 occupied TOTAL entries, not 28,
and a written footing of 125, not 152. Three ruled positions inside the run are
blank; the apparent twenty-eighth group was the footing below the closing rule.
The footer's middle glyph matches the 2 repeated in the body and its last glyph
matches the barred 5 repeated there.

The 27 totals were read independently and sum to 125. Nine entries in
manufactures and trades sum to its footing 12; inland navigation 1 and learned
professions 1 also close. Mining, agriculture, commerce and ocean navigation are
blank in both body and footing. Slaves, pensioners and disability are blank. A
horizontal mark straddling a school-column rule is preserved unresolved rather
than counted, its school footings are blank, and the bound-edge literacy column
remains unread.

The two pairing keys contain no left sheet with either 27 committed household
lines or population 125. Printed page 240 has 27 names, but four unread age-band
cells leave its population key unset. No candidate passes both keys, no sequence
screen is licensed, and the continuation stays unnamed. No 1840 count is assigned
to an 1835 resident. Six group-3 continuations are now read line by line and nine
images remain inventoried only; T-0984 retains eight filled leaves and blank BH.

## A head reached through a card merge is a candidate, never a match (T-1003, 2026-09-13)

THE RULE IS WRITTEN HERE BEFORE IT IS CODED, because it decides an outcome and not a
convenience, and because it is general: it governs every card merge this project lands,
not the one that exposed it.

**What exposed it.** T-1001 ruled that `kimberley_ed` and `kimberly_edmund_s` are one man —
the Chicago Democrat of 1 July 1835 sets both spellings in one column of one page, `E. S.
Kimberley` and `Dr. Kimberly` four sentences apart inside one article — and folded the
first onto the second. With that card folded the residents layer held no Kimberley at all.
`crosswalk_census_1840_heads.py` gathers its 1835 bearers by surname and folds the surname
EXACTLY, so the 1840 head `Ed. Kimberley` (33S7-9YYJ-99F, printed page 234, line 3) stopped
reaching anybody and fell from an L7 candidate to **L2 no_surname_in_the_1835_pools** —
whose standing text reads "a surname absent from 1835 is evidence of that, not a gap in the
reading". On that row it had become a false statement. The surname was never absent from
1835; it was absent from the layer's LIVE index, and only because the town folded it.

**First question: does the survivor inherit the folded card's printed name for matching?**
YES. A folded card's name is a spelling the town's OWN card carried, joined to this person
by a written ruling read off a page — `data/residents/card_merge_rulings.json` states it and
`index.json`'s `merged` table remembers the name. That is an adjudication this project has
already made, and declining to gather under it would throw the adjudication away and refuse
a head against nobody. So the folded spelling enters the 1835 pools — both the surname pool
and the full-name key pool — standing for the SURVIVOR.

Two limits come with it, both taken from the land register's answer to the same question
(`tools/read_land_sales.py` `merged_card_surnames`, T-1001), which is already on the record:

  * The person is WEIGHED BY HIS LIVE CARD — its name, its grade, its attestations. Only
    which bucket he stands in comes from the folded card. Nothing about the decision is
    special-cased; the row prints the live name as `resident_name`, as every other row does.
  * THIS IS NOT A FOLD AND MUST NEVER BECOME ONE. Nothing here compares two spellings or
    measures a distance between them. It reads a written ruling that a specific card of a
    specific spelling names a specific person. `tools/measure_surname_fold.py` prints what a
    mechanical one-letter fold would cost instead, and it is refused.
  * Uniqueness counts the survivor ONCE however many of his spellings gather him, so L5 is
    not made to refuse a man for being adjudicated twice.

**Second question, and it is the one that matters: may the discriminators the merge handed
him count towards L6?** NO. A head that reaches a person ONLY through a folded card's
spelling is CAPPED at `candidate`.

L6 does not ask merely that a discriminator exist. It asks that the full name AGREE, be
unique on both sides, and be independently discriminated. On this route the name that agrees
is the FOLDED card's, and the discriminator is attested under the SURVIVOR's — the survivor
has one here, `Kimberly, Edmund Stoughten, physician, 101 Lake` in Fergus 1843. Nobody has
read the 1840 line against the live card's spelling; the merge ruling was made about two
1835 cards and says nothing whatever about an 1840 sheet. To let it through would be to have
a card merge PROMOTE AN 1840 IDENTITY AS A SIDE EFFECT OF TIDYING 1835 — an identity minted
by bookkeeping rather than by a reading. T-1001's own ruling says in as many words that
nothing was promoted to make it tidy, and this is the same sentence applied one domain over.

What promotes such a head is a reading: the 1840 line set beside the survivor's live card by
somebody who looked. Until then the row says candidate and says why.

**The ladder gains one rule**, parallel to L6a and capping for the same kind of reason — the
identity may well be right, and the ground under it is not firm enough to assert:

    L6b reached_through_a_card_merge_caps_at_candidate
        the full name agrees, is unique on both sides, a discriminator holds, and the
        agreement is with a spelling the residents layer no longer prints — it reaches
        this person only through a landed card-merge ruling. The merge supplied the
        agreement, so the merge may not also supply the match.

Where a row could fire both L6a and L6b the first that fires names the outcome, as the
ladder has always worked; both cap at `candidate` and the reason states the other.

**A row always says how it was reached**, so no outcome on this route can be read without
seeing the merge behind it. A head that reaches ONE person through a folded spelling carries
**`via_card_merge`** — the folded person id, the land crosswalk's field name, deliberately —
on whatever rung it lands, refusals included, beside a `reached_through_card_merge` block
naming the folded card, the survivor and the merge's own rule and ticket. A head merely
REFUSED against a bucket that an alias stands in reaches nobody, so it carries no
`via_card_merge`; instead `surname_bearers_via_card_merge` names which of the bearers the
refusal lists are held under a spelling the layer no longer prints. Both fields are absent,
not null, where neither applies.

**The tool proves this rule against itself.** `--self-test` asserts that no head is ever
`matched` through a card merge, that every L6b row is a candidate naming the read that would
promote it, that this head lands exactly where this section says, and that a survivor
gathered under two spellings is still one person in a bucket. Deleting the cap turns two of
those assertions red, which is how the cap is stopped from quietly coming off.

**What it moves.** Eleven landed merges fold a name that gives a handle the survivor's live
name does not; three of those differ in the SURNAME (Clybourn/Clybourne, Kimberley/Kimberly,
Vandenbogart/Vanderbogart) and the rest in the forename (Gordon/Gurdon Hubbard, John B/Jean
Baptiste Beaubien, Medard and Medore/Madore Beaubien, Russell/Russel Heacock, Th J V/Thomas
Owen, Ed S Kimberly, James/Lieut. James Allen). The counts this pass moves are in the
crosswalk's own `counts_by_rule`, and the Kimberley head lands where this rule says it does:
a candidate under L6b, not a match.
