# Church registers — baptisms, marriages and burials

**What lives here.** Sacramental registers naming people in and around Chicago in
the scene window. St Mary's baptismal register 1833-1835 comes first, because
eleven images of it are already in the deposit and unread (T-0503).

**What is here now — THE BAPTISMS (T-0503).** All eleven deposited page images of
St Mary's baptismal register have been read off the scans, entry by entry:
`records/st_marys_baptisms_1833_1835.json` holds 57 entries and 267 named readings,
`claims/st_marys_baptisms_town_findings.json` holds the eight things the book says
about the PLACE rather than about a family, `st_marys_baptisms_crosswalk.json` is
the pass against `data/residents/`, and `search_log.json` records the second-reading
search that came back empty. `tools/read_st_marys_baptisms.py` builds and gates all
four: the reading lives in that file as a table and `--check` proves the JSON is
still exactly what the table says, so a hand-edit of the artifacts is a gate failure.

**Three things that reading cost, and a later run should not pay again.**
First, THE BOOK CHECKS ITSELF. A pencil hand wrote a tally under each year's last
entry — 1833: 19, 1834: 24, 1835: 14 — and the reading meets all three exactly. A
fourth number, 'total 20' in the margin of page 6, is not a contradiction: 1833
entry 9 baptised two children in one entry. Second, THE ELEVEN IMAGES ARE
CONTIGUOUS and the deposit's filenames say nothing about their order; the order is
the title page, then pages 1-19 of the book, then one stray later leaf, and it was
established by reading the entry numbers across the openings. Third, IT IS NOT ALL
CHICAGO — see below.

**What is here from the marriages and deaths (T-0573).** Father St. Cyr's MARRIAGE register and his death
and burial page, both read out of the *Illinois Catholic Historical Review* vol. 4
by way of the Genealogy Trails transcription: `records/st_cyr_marriages_1834_1839.json`
(128 entries, 513 named readings) and `records/st_cyr_deaths_1834_1837.json`
(11 entries, 13 named readings), with `claims/st_cyr_register_prose.json` for what
the article says around the entries and `st_cyr_crosswalk.json` for the scene-year
pass against `data/residents/`. `tools/read_st_cyr_register.py` builds and gates
all of it. The BAPTISMS are still unread — the same article tallies 282 of them —
and that is T-0503.

**Two things a later run should not have to rediscover.** First, the page titled
"First Chicago Marriage Records" is not all Chicago: footnote 5 puts three of its
first four entries at Bear Creek, Sangamon County. Those rows carry `at_chicago:
false` themselves. Second, the article prints its own tally — 22 St. Cyr marriages,
18 Schaeffer, 87 O'Meara, 1 Plunkett — and 22+18+87+1 = 128 is the only independent
check a reading of this page can have without the book. T-0573 was written against
"87 marriages", which is O'Meara's subtotal.

**What is here from the Second Presbyterian roll (T-0583).** The register fifty-four
Chicago cards of the Newberry genealogical index cite — `Chicago, Ill. Second Presb.
Ch., 1842-92. (Grant)` — located, and read. It is the congregation's semi-centennial
volume, *The Second Presbyterian Church of Chicago, June 1st, 1842, to June 1st, 1892*
(Knight, Leonard & Co., 1892), John C. Grant editor, and its printed pages 154-206 are A
LIST OF MEMBERS OF THE CHURCH, 1842-1892 in three rolls: absent members, present members,
and members dismissed, deceased or ordained. All 2,255 lines are read.
`records/second_presbyterian_members_1842_1892.json` holds the 938 of them whose surname
this project already holds from the 1835 town, `second_presbyterian_crosswalk.json` is
the pass against `data/residents/`, `text/second_presbyterian_roll_1892.txt` is the
committed reading and `second_presbyterian_rowmap.json` the map that puts its four
columns back in printed order. `tools/read_second_presbyterian.py` builds and gates all
of it, and `search_log_second_presbyterian.json` is the search that found the book.

**Three things that reading cost, and a later run should not pay again.** First, THE FLAT
OCR IS UNUSABLE HERE. archive.org reads a four-column table in the order the scanner met
the ink: on printed page 192 it runs `King, Edward / Letter. / October 31, 1855. /
Dismissed. / W. / Profession. / Dismissed. / King, Henry / September i, 1858.`, which is
two printed rows inside one another, and only 672 of 1,361 `Profession.`/`Letter.` lines
stand in printed order. The rows are rebuilt from the word coordinates instead. Second,
THE COLUMN BANDS MOVE WITH THE LEAF — recto and verso differ by about seventy pixels — so
each leaf's bands are taken from its own ink, and from the MEDIAN left edge of the anchor
words rather than the leftmost: a single stray `May` out in the names column of printed
page 171 was enough, read as a minimum, to put every `Letter.` on that page into the date
cell. Third, THE ROLL NAMES A WIFE UNDER HER HUSBAND'S NAME — `Fullerton, Mrs. A. N.` —
so a line that meets a man in the 1835 layer has met his name and not him. Every matched
line carries `a_married_womans_entry` for that reason.

**And what it can never do.** The roll opens on 1 June 1842, seven years after the scene
date. Every record carries `beyond_ticket_window: true`, the crosswalk mints nobody and
regrades nobody, and the gate asserts that nothing dated on or before 1835-07-01 has
reached a record. What a match IS: the same surname and first initial, in Chicago, within
seven years — a lead for a pass that is allowed to write people, which this is not.

**Shape: `records`.** A register is a LIST: one entry is one record. `as_read`
keeps the clerk's Latin, his abbreviations and his spelling exactly as they stand;
`normalized` is this project's spelling of the same person. The two are never
merged — a register's Latin forms are the evidence a later crosswalk reasons from.

**Sponsors and parents are names, and names are people.** An entry that names a
child, two parents and two sponsors carries five readings, not one. Record each,
with its role in `notes`.

**A baptism is not a residence.** It documents that a person was present at a font
on a date. Where the register places them in the town, that is a separate claim
with its own reasoning, and it belongs in `crosswalk.json` or in the resident
record's own note — not in this row.

**Hand-authored:** `records/st_cyr_*`, `coverage.json`, `crosswalk.json`, `search_log.json`.
**Generated:** `records/st_marys_baptisms_1833_1835.json`, `claims/st_marys_baptisms_town_findings.json` and `st_marys_baptisms_crosswalk.json`, all three by `tools/read_st_marys_baptisms.py` out of the reading table inside it; `data/research/domains.json`, which is gated too.

**AND IT IS NOT ALL CHICAGO — the same trap the marriage page set.** Entries 1 to
11 of 1834 were written at Bear Creek, at the South Fork of the Sangamon and at
Springfield, in Sangamon County, on Father St. Cyr's journey back from St. Louis:
the Durbins, Logdsons, Alveys and Potts are Sangamon households and not Chicago
ones. Those rows carry `at_chicago: false` themselves. A reader who takes this book
as a Chicago roll plants eleven households in the wrong county.

**What the baptisms reach that nothing else does.** Kinship — a child, two parents
and two godparents on one dated line, 44 times over — and the town the poll books
cannot see, because a poll book recorded men who voted. Of the 107 distinct adults
the register names in its Chicago entries, 85 reach no surname in the residents
layer at all. Eight of them SIGN, in their own hands, under the priest's.

**Coverage.** Declare the IMAGES read, by image id. Eleven is the deposit's size
for St Mary's; a twelfth image found later is an undeclared item, which is not a
fault. A declared image nothing reaches IS.

**Reading grade.** A reading made off the page image is `scan_verified` and
outranks a `transcription_mediated` one. Register hands are hard; say which you
did.

**This is research, not payload.** Nothing under `data/research/` reaches
`site/chicago/4d/`.
