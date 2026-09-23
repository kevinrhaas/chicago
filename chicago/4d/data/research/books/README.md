# Books and reminiscences — prose, read the way the newspapers are read

**What lives here.** Fergus' Historical Series Nos. 26-29 (read in its first half
by T-0499 - see the contents table below), Gurdon Hubbard's
autobiography (a 226-page scan the project has never mentioned), H. H. Porter's
*Short Autobiography* (read in full by T-0502 and it carries no Chicago before
September 1853), and the memoirs printed beside them (T-0499,
T-0500, T-0501, T-0502).

**Shape: `claims`.** A book is PROSE, so the unit is a claim and not a row —
exactly the newspapers' shape, for exactly the newspapers' reason. A claim carries
a `kind` from the closed vocabulary, a `reading` grade, a **verbatim `quote`**, the
`normalized` reading, the `locator` that finds it again, `describes_date`, the
`entities` it names, and `town_finding`.

**`town_finding` is the field this domain needs and the papers did not.** A
reminiscence is mostly about its author. The paragraph that says the writer's
mother was kind is worth recording and is not worth placing in the town;
`town_finding: false` says so, and keeps a reading from being mistaken for a
finding by whoever consolidates.

**THE VERBATIM GATE BINDS THIS DOMAIN.** `tools/research_domains.py --check`
reassembles every `quote` out of the committed file at `text/`, line by line, and
fails on a one-character difference. A tidied quote is invisible to every other
check in this repository, and the smoothed reading has a field of its own to live
in: `normalized`. Commit the text you quote from; a quote whose text is not
committed cannot be checked and does not pass.

**`describes_date` is not the printing date.** These books were written decades
after 1835. The date a passage DESCRIBES is the one the reconstruction cares
about, and a memoir's own distance from it is a reason to grade carefully, not a
reason to skip the field.

**Hand-authored:** `claims/`, `records/`, `text/`, `coverage.json`, `crosswalk.json`,
`corpus.json`, `trade_class_rulings.json`'s twin `trade_census_1835_spend_rulings.json`.
**Generated:** `page_index/` (`tools/build_book_page_index.py --build`, gated by its own
`--check` in `tools/check.sh`); `trade_census_1835_crosswalk.json`
(`tools/trade_census_1835.py`); `trade_census_1835_spend.json`
(`tools/trade_census_spend_1835.py`); `data/research/domains.json`.

**The two trade-census files are a measurement and a spend, and they are separate on
purpose.** `trade_census_1835_crosswalk.json` (T-1006) sets the town's 206 businesses against
`bk_mose1_006` class by class and creates nothing. `trade_census_1835_spend.json` (T-1007)
answers the gaps it found from layers this project already holds — chiefly the residents
layer, because the business register is compiled from printed NOTICES and five of the town's
physicians never advertised. Neither may invent a person, a business or a building, and both
`--check` in the gate. The census's lawyer and physician lines count PEOPLE, its store and
brewery lines count PREMISES, and the register counts NOTICES: the spend record states the
unit of every comparison it makes, because nineteen lawyer records are fourteen men.

**`corpus.json` is the register.** One entry per book whose text this project commits: what
the book is, which source record grades it, the deposit copy and its sha256, the derived text
and its sha256, HOW that text was produced, and what has been read out of it. A quote is
checked against a committed file, so the file has to be traceable back to the artifact or the
check is circular.

**Coverage.** Declare the PAGES read. A declared page no claim reaches is a hole —
and in a 226-page scan, a hole is the difference between "read" and "opened".

**This is research, not payload.** Nothing under `data/research/` reaches
`site/chicago/4d/`.

---

## What has been read (T-0961, 2026-09-10) — the one TABLE in a domain of prose

**Moses and Kirkland vol. 1, printed pages 78-79: LIST OF ACTUAL SETTLERS AT CHICAGO,
PRIOR TO 1830** — thirty-six rows at
`records/moses_kirkland_v1_actual_settlers_pre_1830.json`, with the NAME, NATIVITY, YEAR
and REMARKS cells as separate fields and the scan's own printed line beside them.

**Why this domain now has a `records/` file at all.** The shape is decided by the SOURCE
and not by the domain — `tools/research_domains.py` says so at the top of itself — and
these two pages are not prose. They are a four-column table, and the unit is a row read as
it stands. Every other reading in this domain is a paragraph and sits under `claims/` for
the same reason in reverse. **T-0581 found this table and deliberately did not transcribe
it**, recording only its existence and the rule it was built on, as claim `bk_mose1_014`;
that was a scope decision and this is the demonstration it deferred.

**The verbatim gate now reaches a row, when the row asks it to.** A claim's `quote` has
always been rebuilt out of the committed text and failed on a one-character difference. A
record's `as_read` cannot be — it is a *cell*, lifted out of one column, and no line of text
contains it alone. So each of these rows carries a `verbatim` of the whole printed line
beside its cells, and `research_domains.py --check` rebuilds THAT at the row's own locator.
The field is **opt-in and stays opt-in**: the domains whose rows come off a scan — a census
sheet, a parish register — have no committed text to rebuild from and never will, and
requiring the field would either fail them or teach them to fake it. A row that offers it is
asking to be checked.

**What the REMARKS column licenses, which is the reading's first finding.** The cells say
*Paid taxes in 1825*, *voted in 1826*, *voted in 1830*. Those are **civic acts at dates**,
every one of them five to ten years before the scene. Paying a Peoria County tax in 1825
says a man was assessed in 1825; standing on the 1830 poll says he was on that poll.
**Neither is a residence on 1835-07-01**, singly or together. Under the ladder ratified
2026-09-03 a pre-scene civic act corroborates an identity and dates it and never places a
person, so the twelve merges below moved twelve identities and moved **no grade, no arrival
and no dwelling**. The table's own preamble draws the same line from the other side: it
names those "known to have had a residence at the settlement" *before* 1830 and excludes
Gurdon S. Hubbard by name because he "did not take up a permanent residence until 1832" — a
compiler of 1895 refusing to count a man who was merely often here.

**Thirty-six rows, thirty-six verdicts, none left silent** (`crosswalk.json`, pass T-0961):

| verdict | n | |
|---|---|---|
| **merged** onto a card | 12 | Jean Baptiste, Mark and Madore Benjamin Beaubien; Billy Caldwell; John K. Clark; Archibald Clybourne; Russel E. Heacock; John Harris and James Kinzie; Barnardus H. Laughton; David McKee; Alexander Robinson |
| **refused** | 16 | John Kinzie the elder; Dr Alexander Wolcott; Samuel Miller; Michael Welch; three Scotts; four Laframboises; two Clybourns; Joseph Anderson; Archibald Caldwell; Rev. Jesse Walker |
| **absent** — the layer holds no card of the surname | 8 | Ament, Galloway, Jouett, Crafts, Kelly, Ouilmette, Pothier, See |

**The rule was borrowed intact and not reinvented.** A merge is upheld only where the town's
own card carries something the ROW can be checked against **beyond a bare name** — a middle
initial both records print, an arrival year the card states in its own words, a date of
death, a nativity the card's origin agrees with, or a civic act the card holds out of
another document. That is `data/research/land_sales/resident_rulings.json`'s
`the_ruling_rule`. It is why **Samuel Miller and Michael Welch are refused** — a common name
against a thin card, with nothing on either side to check — while **Barney H. Laughton is
upheld and graded the weakest merge in the pass**, the agreement being a forename in two
forms plus a middle initial.

**The three strongest merges are strong for three different reasons**, and they are worth
naming because they are the shapes the next pass should look for. *Mark Beaubien*: the
remarks cell reads "died April 11, 1881" and his card already carries Wentworth's
old-settler roll reading "Mark Beaubien, April 11, 1881" — **two men of one name do not die
on one day**. *Alexander Robinson*: the row and the card agree on **three separate civic acts
at three dates**, stated independently out of Andreas. *Archibald Clybourne* and *Russel E.
Heacock*: the YEAR cell — 1823 and 1827 — is **exactly the year each card quotes Andreas
for**, in a column running from 1804 to 1829.

**The refusal worth reading is Dr Alexander Wolcott's,** and it is refused for a reason that
is not doubt. The row is plainly the Indian agent who came in 1820 and died 25 October 1830.
The layer's card of that name is **already a conflation and says so in its own text**: it
carries that death notice, an 1839 directory entry making him clerk of the Steamer Geo. W.
Dole, an 1843 entry making him a surveyor who died in 1884 aged 69, and an 1882 reception.
A fourth reading of the elder would have **deepened the conflation while looking like
evidence**. The elder Kinzie is refused on the same generational ground the American Fur
Company pass already ratified at `bk_afc_011` — restated here because a second source has
now printed the same trap.

**Two things this pass found and deliberately did not do**, both named on their own rulings.
`hh_clark_john_k.json`'s bound would move from 11 July 1835 (ten days *after* the scene) back
to 1817 — a resident-record edit, on the weakest evidence in the building for making one. And
the layer holds **three pairs of cards this pass found to be one man each**: Madore/Medore
Beaubien, Clybourn/Clybourne Archibald, Russel/Russell E. Heacock. All three differ by **one
letter**, which is precisely what the candidate test behind
`data/residents/card_merge_rulings.json` cannot see — it compares strings. Folding cards is a
card-merge ruling; it is filed as **T-1002** rather than smuggled into a reading pass.

**Hurlbut pages 37-8 were not fetched, and the reason is provenance and not effort.** The
table credits *Hurlbut's Chicago Antiquities, pp. 37-8* three lines above itself, and this
project holds Hurlbut at `text/hurlbut_chicago_antiquities_28_36.txt` — pages 28 to 36,
stopping one page short. Extending it is not a download: `corpus.json` is the register, and
an entry there owes a deposit, a sha256, and a statement of how the derived text was
produced, because a quote is checked against a committed file and a file that cannot be
traced back to an artifact makes the check circular. The existing Hurlbut text is a
Genealogy Trails transcription with no page breaks marked anywhere in it, so pages 37-8
cannot simply be appended to it either — they would need their own deposit and their own
provenance. That is its own demonstration, and this run did not spend a transcription's
budget on half of one.

---

## What has been read (T-0581, 2026-09-05)

**Moses and Kirkland, *History of Chicago, Illinois*, vol. 1 (Chicago and New York: Munsell &
Co., 1895)** — twenty claims at `claims/moses_kirkland_history_of_chicago_v1.json`, read out of
the Internet Archive's own OCR of the whole volume committed at
`text/moses_kirkland_history_of_chicago_v1.txt` (137,410 lines). Source record:
`data/sources/moses_kirkland_history_of_chicago_v1.json`, **tier 3** — compiled secondary, the
same rung as Andreas, which it cites.

**WHY IT WAS FETCHED, AND WHY THE NEGATIVES ARE THE POINT.** T-0570's reading of the Newberry
genealogical index found 299 cards citing this work — 193 of them Chicago or Cook County — and
**forty-nine surnames** on those cards that also stand on a lead in this project. It was the
largest Chicago work the index pointed at that the project did not hold. All forty-nine were
looked up in the volume itself, not a sample, and **the row-by-row result of that search is
committed at `moses_kirkland_v1_lead_surnames.json`**, verdict by verdict:

| verdict | n |
|---|---|
| READ — earned a claim | 13 |
| PRESENT AND EARLY, NOT CLAIMED | 8 |
| NOT A SURNAME HERE (`black`, the adjective) | 1 |
| PRESENT BUT LATE — never reaches 1835 | 21 |
| UNRESOLVED — the volume prints a surname one character away | 4 |
| ABSENT | 2 |

A surname with a verdict and no claim is a **negative result**, and the file exists so the next
run does not pay for the same search twice. Nine of the verdicts are authored by hand against the
mechanical one, which is kept beside them: `allen` looked like four hits and is four given
names; `black` looked like a claim and is Black Hawk and black walnut.

**A ZERO IS NOT AUTOMATICALLY AN ABSENCE, and one nearly got away.** Both sides of the search are
OCR — the index cards and this scan — so a miss can belong to either. A plain word-boundary
search reported `obrien` absent while the volume prints **O'Brien** thirteen times; the match is
apostrophe-tolerant because of it. Every remaining zero is re-tested at edit distance 1 against
the volume's entire vocabulary, and the four whose neighbour is a *surname* (`blodget`/Blodgett,
`caapbell`/Campbell, `gardiner`/Gardner, `mattoson`/Matteson) are **unresolved and refused in
`crosswalk.json`**, not merged — deciding two spellings are one name is a merge, and a merge
needs a rule.

**THE FOLIOS ARE READ, NOT DERIVED — no page index was built.** `build_book_page_index.py` exists
because Hubbard's djvu text carries no page breaks at all. This volume prints its own: the page
number stands alone on a line at the head of every verso above "HISTORY OF CHICAGO", and after
the chapter title at the head of every recto. **Verso heads are even and recto heads are odd**,
and that parity is a check the OCR cannot pass by accident — it is what refuses the "93" printed
above a verso head at line 13147, which the surrounding run 96, 97, 99 fixes as **98**. Where a
numeral did not survive, the page is carried between two read folios and the locator says so.

**What the reading is worth, shortest first.**

1. *A trade census of the whole town* (page 95). The State census taken between 1 September and
   December 1835: 3,297 people, forty-four stores, four druggists, eight taverns, two breweries,
   twenty-two lawyers, fourteen physicians, and eleven more counts. The project has never held a
   **denominator** for its business layer. It does now — for December 1835, **not for July**, and
   the claim says so in its first line. The population figure itself is a *third* printing of a
   number already in `data/research/newspapers/`; the trade counts are new to the repository.
2. *A building with four of the five fields `data/structures/` wants* (page 90). Hogan's
   story-and-a-half **log** storehouse, **45 x 18 feet**, at the angle where Lake and South Water
   meet, with the post office partitioned off inside it from 2 November 1832.
3. *Two residences stated as such* (pages 571, 577) — the field the town is thinnest in at 2.4%.
   Jeremiah Porter lodging and keeping his study in the second storey of Peck's store; John Dean
   Caton renting Dr Temple's back room and attic, sleeping in the attic, practising law in the
   back room, and sub-letting desk-room in it to "his competitor, Spring".
4. *Businesses given by corner, lot or landmark* — and one of them by **tree**: Sylvester Marsh
   killing beef under an old elm on the open prairie at what became Monroe Street, from the winter
   of 1833-4 (page 389). A pre-street locator that must not be rounded to a block corner.
5. *One statement about the ground of the scene* (page 79): the winter of 1834-5 was open, little
   snow, front doors open all winter, **cattle living on grass on the river bank**. The closest in
   time of anything here, and evidence for the preceding winter and not for July.

**THE VOLUME CONTRADICTS ITSELF TWICE AND BOTH ARE RECORDED, NEITHER ADOPTED.** Page 89 dates
Dole's and Peck's first frame business buildings to 1832 while page 570 has Peck's occupied in the
fall of 1831. Page 207 forms the Pioneer Hook and Ladder Company on 7 October 1835 while page 570
has it organised on 20 October 1835. A fortnight is exactly the gap a compiler working from two
sources leaves behind.

**NOTHING WAS PLACED, AND THAT IS THE TICKET'S OWN RULE.** No record under `data/structures/`,
`data/residents/`, `data/households/` or `data/assets/` was edited. T-0581's third acceptance
clause requires that what this work dates and places before 1835-07-01 is offered to those layers
**under the ratified ladder, in that layer's own PR** — never off the reading. The claims are
written so a later run can act on them without re-opening the volume.

**Two things it found and did not do, both filed rather than left silent.** The **LIST OF ACTUAL
SETTLERS AT CHICAGO, PRIOR TO 1830** at pages 78-79 — about thirty rows with nativity, year and
remarks columns — is recorded as claim `bk_mose1_014` and transcribed by **T-0961**, because a
roster is a records-shaped dataset and its own demonstration. And **volume 2 is neither held nor
read** (**T-0826**): the Newberry cards do not say which volume they cite, so every ABSENT verdict
above is an absence from *volume 1 only*.

---

## What has been read (T-0502, 2026-09-05)

**H. H. Porter, *A Short Autobiography* (1915) — all seventy leaves, and it carries no
document of Chicago 1830-1836.** Eight claims at
`claims/porter_hh_short_autobiography_1915.json`, out of the Internet Archive's own hOCR
search text of this project's own deposit, committed at
`text/porter_hh_short_autobiography_1915.txt`. Source record:
`data/sources/porter_hh_short_autobiography_1915.json`, tier 4.

**THE DELIVERABLE IS AN ABSENCE, AND THE POINT IS THAT SOMEBODY LOOKED FOR IT.** The
owner listed this book among the reference materials to read. T-0502 read it end to end
and the answer is: nothing. The volume prints no year between 1829 and 1848 except the
author's own birth year, and its earliest Chicago is **September 1853**, when Porter
stepped off the Michigan Central onto the prairie at about Sixteenth Street. An absence a
pass has looked for is evidence; an absence nobody looked for is a hole, and without this
record the next run that meets a 66 MB scan of a Chicago memoir spends its budget
discovering the same nothing.

**The sentence that rules on the volume** is one line of leaf 11: *"I was born in
Machias, оп the 7th day of December, 1835."* On the scene date the author was unborn, and
he was born five months later 1,300 miles away. The ticket allowed for family memory of
the 1830s reaching him second hand; it does not exist either. His father, Rufus King
Porter, was a Biddeford man who read law at Portland and practised at Machias "until his
death, in 1856"; his mother died at Machias in 1862. **There is no Chicago anywhere in the
family.**

**Two town findings, and both of them describe 1853.** They are recorded because they are
what the sweep yielded and because a later run should not have to re-read seventy leaves
to learn that this is all there is:

1. *The old blockhouse of Fort Dearborn was still standing in September 1853* — a
   terminus ante quem non for its removal, seen by a man who was there. It constrains no
   dimension, no position and no appearance, and no fort record is edited by it.
2. *The grade.* In 1853 the street level from the river south to Monroe stood five to
   twelve feet below the grade of 1904, the raising having begun some years before the
   fire of 1871. This is the statement most likely to be cited loosely, so it is written
   down with its date attached: it is a reading of 1853 against 1904 and it is **not**
   evidence for the natural surface of 1835. `data/datum.json` is derived from committed
   ground control and nothing here touches it.

**Three Porters, two of them ruled apart here.** `crosswalk.json` refuses H. H. Porter
against the poll list's `Porter, H.` on the birth date, and against the Rev. Jeremiah
Porter on given name, trade and dates alike. **The third pair is deliberately not ruled
on**: whether `Porter, H.` is Jeremiah Porter is a question about the poll list and the
chaplain, not about this book, and it stays with T-0493. `poll_1835_059` remains a
candidate matched to nobody — this pass removes a wrong answer and does not supply a
right one.

**The text is the hOCR search text and not the djvu text, and the reason is the page
index.** The deposited PDF's own text layer is garbage, exactly as the ticket said — it
uses subset encodings — and it could not have been used here in any case, because the 66
MB scan is offloaded outside this repository and is not in the checkout. Two Internet
Archive derivations of the same OCR pass were available; the hOCR search text was
committed because the Archive emitted its **page index** beside it, which gives every
leaf's exact character range in that very text. So `page_index/porter_hh_short_autobiography_1915.json`
holds all seventy leaf boundaries **exactly and not by alignment**, and
`tools/build_book_page_index.py --build` refuses to write it unless the ranges tile the
committed text end to end. That is the Fergus arrangement, for the Fergus reason, and the
two deposit artifacts sit beside the pointer at
`chicago/reference/hh-porter-a-short-autobiography/`.

---

## What has been read (T-0650, 2026-09-05)

**Illinois Catholic Historical Review, vol. 4 (1921-22), pages 256-259** — Joseph J.
Thompson's *The Illinois Part of the Diocese of Vincennes*, read for one sentence and the
four pages around it. Eight claims at `claims/ichr_v4_thompson_vincennes.json`, out of the
Internet Archive's own OCR of the whole volume committed at `text/ichr_v4_1921_22.txt`.
Source record: `data/sources/ichr_v4_thompson_illinois_vincennes.json`, tier 4.

**THE TICKET'S PREMISE WAS WRONG TWICE AND THAT IS THE FINDING.** T-0650 was opened on the
belief that the first Catholic church is not in the scene, and that this passage is the only
located statement of the building the project holds. Neither is true.
`data/structures/st_marys_church.json` has stood on the south-west quadrant of Lake and State
since 2026-08-11, and it was placed off `chicagology_prefire216`, whose Andreas transcription
has St. Cyr selecting *a canal lot near the southwest corner of Lake and State streets*. So
this reading is a CORROBORATION of a placement already made, and it is written down as one.
A run reaching for "the ICHR passage that puts the church on the map" is reaching for a second
witness, not a first.

**What the passage fixes.** Four things, and only the last two are new to the project.

1. *The quadrant, said again by a second author.* "near the southwest corner of what is now
   State and Lake Streets", and a second time sixty lines later as "the State-Lake location".
   Same quadrant as the record already carries, same hedge word — **near** — so it does not
   narrow the lot and the unbounded westward error `st_marys_church.json` states is untouched.
2. *Whose ground it was.* "upon ground controlled by the Canal Commissioners". On the scene
   date the congregation stood on a canal lot it did not own. That is a fact about the parcel,
   and the project had the word *canal lot* but not the ownership.
3. *A price.* The commissioners' valuation was "fixed at $10,000", the Catholics could not
   raise it, and "the lot was purchased by a private party". The project held the shape of
   this story from Andreas and not the figure.
4. *A terminus post quem for the removal, which is what this article is worth to a scene dated
   1835-07-01.* "When he came he found the little church … standing" is O'Meara's arrival, and
   the same article dates that to "the early or middle part of June, 1837". **The church had
   not moved 23 months after the scene date.**

**What it does not fix.** The lot — "near" is still *near*. Any dimension, material, plan or
orientation; the article says "the little church" and no more. The date of the removal: it
names the auction as the cause and dates neither. Anything about 1835 in particular — it looks
back from 1837 at a building of 1833 and is silent on the years between. And it is not an
independent voice: the run read here footnotes Garraghan on six of its pages, this project does
not hold Garraghan, and **the sentence about State and Lake carries no footnote at all**, so
which of those words are Thompson's cannot be said.

**One sentence is a NEGATIVE constraint on the scene and is the second most useful thing here.**
The rear addition, the small belfry, the three-pound bell and the cross all come *after* the
removal. The building standing at Lake and State on 1835-07-01 therefore had no belfry, no bell
and no rear addition, and was one length rather than two. `st_marys_church.json` already refuses
a tower and calls the belfry "the tower trap on this record"; this dates the trap. It also says
something about the town — until at least 1837 no church bell had ever rung in Chicago.

**Nothing here is payload, and one reading is deliberately left unspent.** No structure, asset,
resident or household record was changed. The June 1837 terminus sits against a phase end of
1836-12-31 on `st_marys_church.json`, which that record took as the conservative of two
readings; the scene is not wrong either way — the record's own note says so — but the end bound
is, and **T-0717** carries that question rather than this ticket. Jean Baptiste Beaubien's
claim on the whole Fort Dearborn reservation, which the removal passage states in passing, is
recorded in `bk_ichr4_003` and written into no resident record.

**The volume is committed and four pages of it are read.** 290,298 bytes of OCR for four pages
of reading, because a quote is checked against a committed file and cutting the middle out of an
OCR run would break the byte-identity the corpus asserts. There is no deposit PDF and no page
index: the page boundaries were read off the volume's own running heads, which this OCR prints,
so no alignment was needed. `data/sources/st_cyr_register_ichr_v4.json` reads the SAME volume
through a Genealogy Trails transcription of two of its register pages — two source records of
one volume, by two different routes, and neither was re-read against the other.

---

## What has been read (T-0575, 2026-09-03)

**Hurlbut's *Chicago Antiquities* (1881), pages 28-36** — the chapter on the American
Fur Company and Chicago. Nineteen claims at
`claims/american_fur_company_hurlbut.json`, out of this project's own committed copy
of the transcription at `text/hurlbut_chicago_antiquities_28_36.txt`, which is
byte-identical to the genealogytrails cache it was taken from. Source record:
`data/sources/chicago_antiquities_american_fur_co.json`.

**Three voices, and every claim says which it is.** Hurlbut compiles in 1881 and
judges; Gurdon S. Hubbard remembers inside quotation marks at sixty years' distance;
and an outward-invoice book of the Michilimackinac agency, 1821-22, is a period record
printed verbatim with its orthography kept. The source record's `transcribes[]` grades
the three separately — 4, 2 and 1 — and the record's own tier is 2, which is
Hubbard's rung and not Hurlbut's.

**What the chapter is for.** It is a SIZE ARGUMENT about the town, said twice by two
men who did not copy each other: Hurlbut's "Chicago was the port and point of a very
limited district of distribution", and Hubbard's "this place never had been preeminent
as a trading-post, as this was not the Indian hunting-ground". With the two dates
beside them — Hubbard bought the company's whole Illinois interest in 1828, and Astor
sold the company in 1834 — it settles what this town may say about the American Fur
Company in 1835, which is nothing.

**Nothing here is payload.** No structure, asset, resident or household record was
changed by this reading. The readings that argue for such a change — Hubbard's dated
1818 arrival against a resident record that grades the same year "reconstructed", the
Factory House origin of `jb_beaubien_homestead`, the catalogue of trade goods, and the
James / John H. Kinzie half-brotherhood — are written as proposals in T-0575 and carry
their own tickets. **The chapter's latest Chicago event is 1828**, so it dates and
corroborates and places nobody.

**`coverage.json` declares this chapter as one `list` item and not as nine `page`
items**, because the transcription marks no page breaks. The page RANGE is named in
every locator; a page number would be an invention, and the gate would then be checking
a fiction. The day this project reads the book itself, the declaration can become nine
pages honestly.

---

## What has been read (T-0501, 2026-09-03)

**Gurdon S. Hubbard's *Autobiography* (Lakeside Classics, 1911)** — a 226-leaf scan that had
sat in the deposit unmentioned: no text, no source record, and zero hits for "swift walker"
anywhere in `docs/`, `data/sources/` or `tickets/`. Ninety-two claims at
`claims/hubbard_autobiography_1911.json`, out of the Internet Archive's own OCR committed at
`text/hubbard_autobiography_1911.txt`. Source record:
`data/sources/hubbard_autobiography_1911.json`, tier 3.

**THE BOOK IS TWO BOOKS AND EVERY CLAIM SAYS WHICH.** Hubbard's own narrative is a
participant's recollection of 1818–1830 at rung 2, and it **stops dead in November 1830** —
the closing editorial note says so in as many words. Caroline M. McIlvaine's Introduction is
1911 compilation at rung 4, and it is the *only* place in the volume where the town of
1834–1836 appears at all: the brick building at La Salle and South Water, the five or six
hundred inhabitants, the brig *Illinois* of 25 May 1835, the Green Tree Tavern, the fire
engine, the Russell & Mather purchase, the canal commissioners. **A run reaching for "Hubbard
on 1835" is reaching for McIlvaine.** One period document is printed between them — Hubbard's
letter to his sister, headed *Chicago, July 25, 1827* — and it alone reads at rung 1.

**What the book is actually worth here** is 1818, and it is worth a great deal: a full
elevation of Fort Dearborn and its enclosure (fourteen-foot oak pickets, block house
south-west, bastion north-west, whitewashed throughout, officers' quarters *outside* the
pickets with a piazza at second-storey level, a brick magazine, a four-acre garden, one road,
a fence line closed from river to river, a well by the south gate, wash-houses on the beach);
the Factor House and the American Fur Company's round-log storehouse that passed from John
Craft to Jean Baptiste Beaubien; John Kinzie's long log cabin with its rude piazza facing the
fort across the river; and a **complete building count for the whole of Cook County** — the
fort's group, those two, Hardscrabble, Ouilmette's cabin and Kinzie's house, and nothing else.
Seventeen years before the scene.

**Two contradictions are recorded and neither is resolved.** Page 36 puts the officers'
quarters outside the pickets and built of hewn logs; page 167 puts the commanding officers'
former quarters in a *brick* building just within the north stockade. And page 167 dates the
Pottawatomie payment and the fort fire to "September of the year 1828" while the section
heading, the narrative around it and Hubbard's own dated letter all say July 1827. Both are
written down as disagreements. Neither is smoothed.

**The scan is out of order, and finding that out is part of the reading.** Pages xv and xvi
were photographed at the *front* of the Internet Archive item, as leaves 11 and 12, ahead of
the title page — leaf 26 ends "Quoting Mr. Gale's characteristic manner of narration:", leaf
11 opens the Gale quotation, leaf 12 ends "his engine was soon put to", leaf 27 opens "use as
'Fire King Engine No. I,'". Six folios read off the page fix the runs above and below the
displacement, and `tools/build_book_page_index.py` now carries all three runs and **hard-fails
if a folio printed on a page ever contradicts them** — which is the check that would have
caught it without the text.

**`page_index/` exists because the committed text has no pages.** The djvu output carries not
one form feed. The leaf boundaries are transferred onto it, mechanically and reproducibly,
from the deposited PDF's own text layer, which has all 226; 207 of the 208 non-blank leaves
aligned, and the one that did not — the Contents at leaf 19 — is declared, and the leaf that
swallows its lines says so with `runs_into`. No claim cites those lines.

**Nothing here is payload.** No structure, asset, resident or household record was changed by
this reading. Seven identities are merged and fifteen refused in `crosswalk.json`, all inside
the research layer; the sharpest refusal is the "John Kinzie" of the 1834 trustee list, which
*looks* like an easy merge and is not — the elder John Kinzie died in 1828 and this project
holds three separate Kinzies, so a 1911 writer's shortened form is not enough to put a dated
civic office on any one of them.

---

## Fergus' Historical Series, Nos. 26-29 — what the volume actually holds

**The deposit's filename says 26-29 and until T-0499 nothing said what that meant.**
It is four separately printed pamphlets bound as one, each with its own title page and
its own folio run starting at 1 — which is why a page number in this volume is not
unique and why every claim cites its LEAF. The table is read off the four title pages
inside; the front matter names no contents at all.

| No. | Title | Author | Printed | Leaves |
|---|---|---|---|---|
| — | Library plate, digitisation note, half-title "FERGUS' HISTORICAL SERIES No. 26 - 29", Fergus Printing Company advertisements | — | — | 1–14 |
| 26 | *A Discourse on the Aborigines of the Ohio Valley*, with the Fort Wayne Indian speeches of 2 October 1811 appended and footnoted | William Henry Harrison (the discourse, 1838); Hiram W. Beckwith (the footnotes) | 1883 | 15–206 |
| 27 | *The Illinois and Indiana Indians* | Hiram W. Beckwith | 1884 | 207–398 |
| 28 | *Directory of the City of Chicago, Illinois, for 1843* | compiled by Robert Fergus | **1896** | 399–656 |
| 29 | *Biographical Sketch of Joseph Duncan, Fifth Governor of Illinois* | Julia Duncan Kirby | 1888 | 657–858 |

The leaf ranges include each number's own advertisement and cover leaves, which is why
they meet with no gap. Blank and plate leaves are inside them: 624 of the 858 leaves
carry text.

## What has been read (T-0499, 2026-09-03) — the first half by page index

**Leaves 1–429**, declared as four `list` items in `coverage.json` with no hole. That is
the front matter, No. 26 entire, No. 27 entire, and No. 28 down to the port statistics,
stopping where the 1843 business directory begins at leaf 430. **T-0500 takes leaves
430–858.** Forty-one claims at `claims/fergus_26_29_first_half.json`; twenty of them are
town findings. The target was stated before the reading began and is in the ticket: at
least forty claims and at least eighteen town findings.

**THE ASK WAS FOR SETTLERS' REMINISCENCES AND THIS HALF IS NOT THAT.** The Fergus numbers
in general are where the settlers of the 1830s told their own stories thirty and forty
years on. Numbers 26 to 29 are a discourse on the mound-builders, a tribal history, a
directory and a governor's life. **No. 26 is a sweep that came back all but empty, and
that is evidence**: four claims out of 192 leaves, every one of them from the 1811
speeches appended to the discourse rather than from the discourse itself, which never
reaches the Illinois lakeshore.

**The two numbers that do touch Chicago miss the scene year from both sides.** No. 27
reaches it fourteen years early and No. 28 eight years late, and every claim's
`describes_date` says so.

**No. 27 — Beckwith, and it is the better of the two.** Where he compiles he is tier 3;
where he quotes Henry R. Schoolcraft on the Chicago treaty of August 1821 he is
transmitting an eyewitness journal, and that is where the landscape comes from: **a belt
of forest skirting the south branch, and beyond it the extensive level plain stretching
to the lake shore** — the first independent corroboration in this domain of the shape the
project's heightfield and timber belt already assume. With it: **a scattered Potawatomi
village on both branches of the river** (the site was inhabited, and not at a point);
the stream's name read as *a skunk* primarily and *a wild onion* secondarily, in that
order; the Des Plaines named for a maple growing along its banks; **a seated bower on the
green along the north bank, near the old John Kinzie house and directly under the guns of
the fort**, which bounds how built that bank can have been; and between two and three
thousand people assembled there, the largest crowd figure this project holds for this
ground.

**No. 28 — a directory *for 1843* that was compiled in 1896**, by a man who did not reach
Chicago until July 1839, out of a canvass of 1843 of which he himself writes that
"sailors were made tailors, and tailors sailors, names were spelled at and locations
guessed". That sentence is a claim in this file (`bk_fer_043`) and it is the most useful
thing in the pamphlet, because **it bears directly on T-0506**: the "1839 Chicago
directory" this project cites is, on the same compiler's account, an 1876 publication —
the same retrospective act, thirty-seven years after its year. What the pamphlet still
gives the town is **the mail across the scene date** (horseback weekly in 1832 under
Jonathan Nash Bailey; a semi-weekly four-horse stage from 1834; **tri-weekly in 1835**),
**the Chicago Lyceum instituted 2 December 1834**, seven churches placed to the block
face as an upper bound on 1835, a Masonic lodge in a third storey at Clark and South
Water, and the earliest customs figures for the port — 1836, exports $1,000.64 against
imports $325,203.90, with the custom house's own warning that both understate.

**One reading was refused outright.** The 1843 census table's ward columns are woven by
the OCR into lines of loose digits. The totals appear to read 7,580 against 4,853, and
"appear to read" is not a transcription: `bk_fer_057` records the refusal instead of the
number, and says what a run would have to do to get it.

**The identity pass is small on purpose.** `crosswalk.json` rules on the five names that
fall in the 1830–1836 window — two merges (Billy Caldwell into Billy Caldwell
(Sauganash); John Stephen Coates Hogan into John S. C. Hogan, which dates the
postmastership the resident record already half-carried) and three refusals (Jonathan
Nash Bailey against Bennet Bailey; John Kinzie against his son John Harris Kinzie;
"Mrs. Kinzie" against Juliette Augusta Magill Kinzie, on the surname-only rule). Every
other name in 429 leaves is outside the window, and the pass says so by name so the next
sweep does not do the work again.

**Nothing here is payload.** No structure, asset, resident or household record was
changed by this reading.

**The page index needed no alignment, and that is new.** Hubbard's leaf boundaries had to
be transferred from a second file by `difflib`. This volume's deposit carries the hOCR
page index emitted with the same OCR pass that made the text, so the 858 leaf boundaries
are exact arithmetic; `tools/build_book_page_index.py` grew a second derivation mode for
it (`derivation: hocr_page_index`) and hard-fails unless the ranges tile the committed
text with no gap and no overlap. **Its folios are read or they are null** — the volume
binds four pamphlets that each restart at 1, so there is no offset to carry and a carried
folio would be an invention. 194 of the 624 non-blank leaves print one the reader could
take.

## What has been read (T-0500, 2026-09-03) — the second half by page index

**Leaves 430–858**, declared as five `list` items in `coverage.json` with no hole, which
completes the volume: T-0499 stopped where the 1843 business directory begins and this
takes it from there. Fifty-eight claims at `claims/fergus_26_29_second_half.json`;
forty-five of them are town findings. The target was stated before the reading began, in
its own commit: fifty claims and twenty town findings.

The five are **No. 28's Business Directory** (430–457) and **Obituary** (606–644) and the
whole of **No. 29** (658–850), read in full; the **publisher's advertisement leaves**
(645–657, 851–858) read for Chicago titles only; and **No. 28's alphabetical name
directory** (458–605) **swept by machine and not read continuously**. That last is stated
as plainly in its declaration as it is here, because it is the one limit that could be
mistaken for coverage: every line was passed against two patterns — every year from 1820
to 1836, and every personal and firm name this project's own 1835 records hold — and only
the thirty-odd lines that answered were read. An absence from this file is therefore **no
evidence** that a name is absent from the directory.

**The directory is 1843 and the claims say so, forty times over.** Not one of its
addresses is carried into the scene year, and the most useful thing in it is a dated
negative: `bk_fer2_043`, Fergus's own note that Bristol & Porter's was the **first
warehouse on the South Side, erected in the fall of 1839**. `bk_fer2_044` is why every
other annotation of his is graded where it is — his own entry gives his arrival as
**1 July 1839**, which is T-0499's finding reached independently from the other end of the
book. What 1843 does give is the distance travelled: a four-storey brick on South Water
second door from Clark, the Sauganash still at Lake and Market, a *later* Tremont House on
Lake Street, and two shops reading their position as an ordinal off a named building —
the same grammar T-0384 and T-0385 read for 1835.

**The Obituary is where the second half touches the scene year at all**, six times:
Thomas J. V. Owen the Indian agent (15 October 1835), the Rev. Jesse Walker twelve miles
west of Chicago (5 October 1835), Hollis Newton hotel-keeper (25 August 1835), a **Dr
Spring** with no given name (10 November 1835), the Rev. Allen B. Freeman (17 December
1834) and Dr Alexander Wolcott (25 October 1830, his the first will probated in Cook
County). The Spring line is **refused** against this project's Giles Spring and the
refusal is the point: a surname with a doctor's title in front of it is not a lawyer, and
T-0423 would otherwise inherit a death inside the scene year on a surname alone.

**No. 29 names Chicago four times in ninety-five pages and places nothing here.** Its one
thread that reaches the town is the Illinois-and-Michigan Canal, and that thread is worth
the reading: Duncan's Washington diary of March 1829 pressing the War Department to get
the route **located**; the legislature of 1834–35 adjourning without acting on it; and the
special session of **December 1835** — the last month of the scene year — where he
reported every attempt at a loan had failed and asked instead for the faith of the State
to be pledged, which that session granted and which is the money the canal was built
with. One passage naming Chicago canal lots is recorded as a **trap** (`bk_fer2_012`): it
sits in a message headed *July 11, 1837*, so its "20th of June last" is 1837, and a sweep
for Chicago plus a canal context would take it for 1835.

**The identity pass rules on eleven claims** — six merges and seven refusals — and lists
all twenty-five people named inside the 1830–1836 window by name with the outcome of
each, because a crosswalk that reports only its merges cannot be audited. Nothing in
`data/residents/`, `data/structures/` or `data/assets/` was edited.

## The trade-census spend rulings are guarded against a lost judgement (T-1125)

`trade_census_1835_spend_rulings.json` is `hand_authored: true`, and every gate that reads
it re-derives DOWNSTREAM of it — so a shrinking file is a legal file, and no derivation can
say otherwise. Since T-1125 `tools/check_rulings_not_lost.py` (run by `check.sh`) holds it
to the MERGE BASE: every judgement adjudicated there must still be adjudicated at HEAD, by
identity and not only by count, so a swap that never moves the total is caught too.

**Five stores hold a judgement** and are counted together, so moving one between them is a
move and not a loss: `classes_ruled`, `practitioners`, `institutions`,
`documented_absences` and `register_records_not_assigned`. A class ruled, a practitioner
placed under it, an institution present at the scene date, an absence documented and a
register record deliberately left unassigned are five ways of saying that somebody decided.

**Two stores are deliberately left out.** `occupation_classes` maps the residents
vocabulary onto a census word and is a transcription of that vocabulary, not a ruling on
the town. `open_questions` is the opposite of a judgement — it is what this pass declined
to decide — and it *should* be able to shrink, because a question leaves by being answered.

**To remove a ruling**, move it into `withdrawn[]` carrying a `reason` and the `ticket`
that decided it. It is counted with the other five, so the total never falls and the record
of what left says why. A `withdrawn[]` entry with no reason is refused as a deletion
wearing a label. The array does not exist in the file yet and does not need to.
