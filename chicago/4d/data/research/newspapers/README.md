# The newspaper corpus — what is here, and how to cite out of it

`corpus.json` is the register. Eighty-six issues: **seventy-three** of the *Chicago
Democrat*, 1833-11-26 to 1835-08-26, and **thirteen** of the *Chicago American*,
1835-06-08 to 1835-08-29. The scene date sits inside both runs, and a Democrat was
printed on 1835-07-01.

Two source records carry the judgements — the traps, the owner's three rulings, the
uneven transcription quality, and what each publication may and may not be used for:

- `data/sources/chicago_democrat_1833_1835.json`
- `data/sources/chicago_american_1835.json`

`data/sources/chicago_democrat_1833_11_26.json` is the per-issue record for the first
issue and **stays senior to both** for that issue: it was verified against the page
images, and a scan read outranks a transcription read.

## Citing

A claim that cannot name its column cannot be made. Resolve the issue through
`corpus.json`, quote the transcription's uncertainty brackets as they stand, and cite:

> *Chicago Democrat*, 1835-07-01, Vol. II, No. 11, issue page 3, column 4 —
> `chicago/reference/newspapers/Transcriptions/Chicago_Democrat_1833-11_to_1835-08/Chicago_Democrat_1835-07-01_Vol2_No11_Transcription.txt`, lines 812-819.

Page and column come from the transcription's own column markers — and this file has now
been wrong about how many dialects there are **three times**. There are SEVEN, the last
two found by T-0325, and the count is now measured against every artifact in the corpus
rather than asserted. The sixty-six issues the deposit
delivered as committed `.txt` carry a RULED marker in one of three shapes:

    ===== ISSUE PAGE 4 / PDF PAGE 36 / COLUMN 5 OF 6 =====
    ===== ISSUE PAGE 4 / SOURCE PDF PAGE 36 / COLUMN 5 OF 6 =====
    ===== ISSUE PAGE 4 / ORIGINAL PDF PAGE 36 / COLUMN 5 OF 6 =====

and the twenty-three extracted here from `.docx` carry the same two facts as prose
headings, the page once and each column under it:

    Newspaper Page 1 — Source PDF Page 13
    Column 1

**AND THE WHOLE OF 1833 SPEAKS A FIFTH SHAPE, which is a third of T-0258's range.** The five
issues 1833-11-26 to 1833-12-24 separate the page from the column instead of ruling them onto
one line — a page banner, then a rule before each column:

    ===== SOURCE PDF PAGE 9 / ISSUE PAGE 1 =====      1833-12-10 .. 1833-12-24
    SOURCE PDF PAGE 1                                  1833-11-26, 1833-12-03
    --- Column 1 ---

Counted on 2026-08-28 over the thirty issues of Vol. I Nos. 1-30: **five** are dash-column,
**five** (1833-12-31 to 1834-01-28) are the prose pair, and the remaining **twenty** are
ruled. 121 column markers were invisible to the resolver, and — the same blind spot T-0289
recorded — `dev` could not tell, because the page/column assertion is skipped outright when
the text cannot be opened. The bare banner names the SCAN page and not the issue's (the
Democrat of 1833-12-03 opens at PDF page 5, because No. 1 occupies 1-4), so it is resolved
**by ordinal**: the first page banner of a transcription is issue page 1. That is the only
rule here not lifted verbatim off the line, it is a reading of the transcription's own stated
method — "assembled in printed page and column order" — and it is not used when the banner
states the issue page itself. The self-test carries a case per dialect plus three negatives.

**AND A SIXTH AND A SEVENTH SHAPE, WHICH ARE THE FIRST HALF OF 1835 — the last two, and
this is now measured rather than asserted (T-0325).** Six of the eight Democrats between
1835-01-21 and 1835-06-24 resolved to ZERO columns, so every claim citing them would have
failed the gate with *"the transcription carries no ISSUE PAGE / COLUMN marker"* and the
read of that range could not have landed at all. T-0298 had recorded three of them as
*"bare `=====` rules carrying no page or column at all"* and left open whether that was a
transcription defect. **It was not.** The rules are decoration around a page banner, and
every column carries its own rule naming the scan page:

    [Source PDF page 9; newspaper page 1; column 1]      1835-01-21, the 03-25 Extra, 05-20
    PRINTED PAGE 1 — SOURCE PDF PAGE 13                  1835-05-27, 06-04, 06-10
    --- SOURCE PDF PAGE 13, COLUMN 1 ---

46 bracket markers and 72 dash rules under 12 banners: **118 column markers invisible to a
resolver already corrected twice for exactly this.** The seventh dialect's column rule
states its own scan page, so it is resolved through the banner naming that page rather than
through the banner last passed — no ordinal, nothing counted. One bracket marker carries no
column number, `[Source PDF page 8; Extra page 4; single-column subscription prospectus]`,
and is read as that page's column 1 on the warrant of its own word and its file's header
line ("Extra pages 1–3 have 3 columns; page 4 is a single-column subscription prospectus").
That page is Calhoun's subscription list and it names people.

**Where the census now stands.** Every artifact in `corpus.json` was resolved before and
after the change on 2026-08-29: the six move, the other 83 do not. **One artifact of the
89 still resolves no column and it is not a resolver gap** — the `alternate` of 1833-11-26,
a prose reading transcription made from the page images, which segments nothing and names
its pages "SUPPLIED SCAN PAGE 1". There is no column marker in it to find, so it is not
citable at column level and a claim needing it must cite the `primary`, which is what
T-0308 read. That is a fact about the artifact, recorded here rather than left silent.

**The middle ruled shape is the majority and it was the one nobody had.** Counted across
the deposit on 2026-08-28 while reading July 1834 (T-0289): 1,176 of the 1,266 ruled column
markers say `SOURCE PDF PAGE`, 90 say the bare `PDF PAGE`, and four say `ORIGINAL PDF
PAGE`. T-0257's resolver matched only the bare form, so it could find a column marker in
NONE of the twenty-six issues of the second half of 1834. Nothing caught it because the
gate skips the page/column assertion outright when it cannot read the text, and on `dev`
it never can — a resolver that speaks no dialect and one that speaks all three are
indistinguishable on this branch. `tools/compile_gazetteer.py` now reads all four shapes
and its self-test carries a case per ruled dialect plus a negative.

**Where the deposit is not readable, run the gate against a copy of it.** `--deposit
<path>` re-roots deposit-held citations exactly as `newspaper_corpus.py` does, so a reading
pass working on `dev` can machine-check every quote it makes against the real text from
`main` before it opens its PR. `check.sh` on `dev` then counts those claims unresolved and
reports them, which is green.

## Where the text is, and why it is in two places

| | issues | text |
|---|---|---|
| the deposit carries a committed `.txt` | 66 | cited at its `chicago/reference/...` path, never copied |
| delivered as `.docx` only | 20 primaries + 3 alternates | extracted here to `text/`, and **committed** |

The deposit is the owner's archival deposit and this project reads it only. It was
committed to `main` on 2026-08-28, and for a week after that it was NOT on `dev`, where
this subtree is developed — so ten reading passes materialised a read-only copy from
`main` and machine-checked their quotes with `--check --deposit <path>`, which is why so
many `coverage.json` notes say so.

**IT IS ON `dev` NOW, and a reading pass no longer needs `--deposit` (found 2026-08-29,
T-0325).** The promotion back-merge carried `chicago/reference/` across, and every one of
the 178 recorded paths and sha256s in `corpus.json` resolves and matches on this branch —
checked file by file, not assumed. `tools/newspaper_corpus.py --check` says `deposit
present`, and the gate reassembles all 713 committed quotes here rather than counting them
unresolved. `--deposit` stays for the case it was built for: a branch or a checkout that
does not carry it. T-0275, which asks for exactly this back-merge, has not been closed and
should be looked at by whoever next reads its queue row rather than being done again.

The three states `tools/newspaper_corpus.py --check` reports are unchanged: deposit
**present** (every path resolved file by file), **absent** (reported, and green),
**partial** (always red — that state means damage).

## Quality is not uniform

The 1833, 1834 and January–July 1835 Democrat batches were reconciled against enlarged
page images with a second-reviewer pass. The August 1835 Democrat tail, the three `-2`
rebuilds and **the entire American run** are single-pass OCR. Where two runs cover one
issue the `-2` text is visibly worse; 1835-07-15 survives only as a `-2`, and
`corpus.json` says so on that entry. Weight a reading by the batch it came from —
`status`, `completeness` and `sole_witness_note` carry it.

## This is research, not payload

`tools/publish.sh` copies named subdirectories of `data/` and this is not one of them.
The gate asserts that nothing under `data/research/` has reached `site/chicago/4d/`,
so the corpus can grow without spending the published tree's size budget.

## Rebuilding

    tools/newspaper_corpus.py --build --deposit <path to Transcriptions>

Deterministic: the same deposit produces byte-identical `corpus.json` and `text/`.
`--deposit` exists because the deposit is on another branch; paths are always
*recorded* at their canonical `chicago/reference/...` home whatever `--deposit` says.

## Reading out of it — claims, and the gazetteer they compile into

`corpus.json` says where a passage IS. These say what was read out of it (T-0257).

| | |
|---|---|
| `extracted/<issue_id>.json` | one file per issue, holding `claims[]` — hand-authored |
| `identity.json` | the only place two differently-spelled names may become one person, two firm styles one house, or two of a house's proprietors one partner — the only place a name is declared a PLACE rather than a person, and the only place an AGENCY is declared a relation rather than a house |
| `coverage.json` | the ranges a reading pass has DECLARED it read, and the gate holds it to them |
| `gazetteer.json` | **generated** by `tools/compile_gazetteer.py --build` — never hand-edited |

    tools/compile_gazetteer.py --build       recompile the gazetteer
    tools/compile_gazetteer.py --check       the gate (in check.sh)
    tools/compile_gazetteer.py --self-test   its assertions still fire

**A declared range may not have a hole in it.** The failure a reading pass is prone to is
not a bad claim — the quote gate catches those — but a MISSING ISSUE: fourteen of fifteen
read, and nothing anywhere saying which one was skipped. Counting extraction files cannot
answer it, because the count that should have been is exactly the thing in question. So a
pass names the range it read in `coverage.json` and `--check` resolves that range against
`corpus.json` and refuses any issue inside it with no extraction file. Declaring is what
makes the assertion: an issue nobody has declared is simply not read yet and is not a
fault, and a range is only widened by the pass that widens the reading (T-0295).

**A claim quotes verbatim and normalizes beside it, never instead.** `quote` is the
transcription's own text including its uncertainty brackets; `normalized` is the reading
after OCR judgment — interleaved columns unshuffled, `rn/m`-class confusions corrected.
The gate reassembles `quote` out of the transcription line by line and refuses any claim
whose text differs by a character, so a smoothed quote fails rather than passing quietly.

**WHEN TWO PRINTINGS DISAGREE, COUNT THE PRINTINGS BEFORE YOU SEND FOR THE IMAGES
(T-0328).** A weekly's advertising is STANDING type: the same notice runs week after week,
and every week is a separate impression, separately scanned. So a disagreement between two
settings of one advertisement is rarely a two-witness problem — it is an n-witness problem
in which n has not been counted. D. Weaver's building on North Water street was read as
Lot 9 in one issue and Lot 2 in the next, and the reading pass filed a ticket for the page
images because "one of the two transcriptions is simply wrong". It ran FIVE times, from
1834-11-26 to 1834-12-24. Four of the five read Lot 2; the outlier's own line drops the t
out of `Norh`. No image was needed.

The method, and it is three greps: search the whole run for the advertiser's name, resolve
each hit's page and column, and read the settings side by side. It has now answered three
questions the ticket queue had assigned to the page images — the blacksmith's "opposite the
Tremont House" (T-0330), the axes that belonged to the ironmongers and not the booksellers,
and this lot number. **Nothing is amended to agree with anything**: every printing keeps its
own verbatim quote, the losing reading stays visible in `normalized`, and the winner is
declared in the notes with the tally that decided it.

Two cautions, both learned here. **The tally is over impressions, not over readings** — two
transcriptions of the SAME impression are one witness, and `corpus.json`'s `-2` rebuilds are
exactly that. And **a run of concordant settings does not make a scan trustworthy in
general**: the same printings that agree on the lot number set the advertisement's copy date
four different ways, so the digit that was decidable and the digit that was not stood two
lines apart in one column.

**A BRACKETED SUPPLY MAY NOT OUTRANK A LETTER THE IMPRESSION SETS WHOLE (T-0407).** A
supply in `normalized` is a reading of a letter the page does not deliver; it is not a
licence to replace one the page delivers plainly. The blacksmith is the case. One printing
of Matthias Mason & Co.'s standing notice, 1834-02-18 c010, was read as `MATTHIAS [N]ASON &
CO.` and minted a business called `Matthias Nason & Co.` — and line 2823 of that
transcription sets `MATTHIAS MASON & CO.` whole, on its own line, with no uncertainty
marker on it and with the claim's interleaving beginning two lines below. So there was no
unread letter for the bracket to stand in. The tally is one-sided: nineteen impressions of
the notice carry the surname's first letter and every one is an M — fifteen set `MASON`
whole, two wreck the S and keep the M (`MAJON`, `MADON`), two break off at `MATTHIAS MA` —
and the post office prints the man `Mason, Matthias` in two letter lists, independently of
his own advertisement. Withdrawing the supply is not amending a printing to agree with
another printing; the quote was never touched and always read `MASON`.

**The route matters as much as the answer.** The defect was a CLAIM's, so it was repaired
in the claim, and `firm_merges`' partner-surname guard — *the two styles must carry the same
set of partner surnames* — was left exactly as it stood. `Nason` against `Mason` is an
ordinary surname difference and the guard is right to refuse it; the escape would have had
to be "unless the surname resembles the other one", which is the one thing a partnership
rule may never say. `compile_gazetteer.py --self-test` already asserts the refusal on a
clean fixture (*a merge that would change who the partners are*, and five more under the
sign-name cases), and none of those assertions moved.

**AND THERE IS NO MECHANICAL GATE FOR THIS, WHICH IS WORTH KNOWING BEFORE SOMEBODY WRITES
ONE.** Two candidate checks were measured against all 86 extractions before this was
repaired by hand. *A supply that contradicts a letter the quote carries* fires on several
hundred claims and every one is legitimate — correcting `ITREET` to `[S]TREET` is precisely
what `normalized` is for, so the shape of the fault is not local to the claim. *A
single-letter supply inside a business name that no other printing corroborates* is
narrower: it flags twelve names in the corpus, and the twelve include `MA[T]HIAS` — the
supply `firm_merges` cites as the GOOD one, because there the transcription brackets the
very letter at issue. Nine of the twelve are the only printing their notice ever got, so
there is no tally to run against them at all. The instrument is the tally above and a
reader willing to run it; the twelve are the candidate list if anyone wants to.

**AND COUNT THE PRINTINGS BY THE NOTICE'S BODY TEXT, NOT BY ITS ADVERTISER (T-0350).** The
sentence above used to say "the same FIVE printings", and five was wrong: D. Weaver's notice
ran SEVEN times, from Vol. I No. 50 of 1834-11-12 to Vol. II No. 4. Two reading passes and
then T-0328's tally all missed the two earliest, for one reason — a search for the advertiser
cannot find a column that sets his name `D. WEAVE.R`, or one that loses the name to the
alternating column entirely. Search a standing notice's own words instead; a notice already
claimed somewhere gives you them for nothing.

**THE DATELINE'S TRAILING FIGURE IS AN INSERTION KEY, AND IT DATES THE COPY WHEN THE DAY IS
ILLEGIBLE (T-0350).** `Nov. 5, 1834.—49`, `Nov. 26, 1834-52`, `Dec. 16, 1834.-3` — the number
after the year is not part of the date, it is the number of the issue the copy is keyed to,
the first number published on or after the dateline. Vol. I No. 49 was printed 5 November,
No. 52 on 26 November, Vol. II No. 3 on 17 December. So a key **bounds the dateline to one
week**, which is a second instrument on any damaged date and a stronger one than a tally:
D. Weaver's seven settings all key 50, No. 50 was printed 12 November, and that excludes the
`Nov. 13` and `Nov. 19` two of them read without needing to count anything. Read it as a fact
about the DATELINE and not about first appearance — J. Bates's `Nov. 5, 1834.—49` notice does
not stand in No. 49 at all, and first appears in No. 50.

**Interleaving is the normal case.** The segmenter frequently alternates two physical
columns line by line, so one advertisement occupies a SUBSET of a line range with another
woven through it. `locator.lines` is the range cited; `locator.lines_of_claim` names the
lines the quote is built from, and the gate checks the subset lies inside the range.

**And it happens INSIDE a line too, which is what `locator.spans` is for (T-0261).** The
Democrat's transcriptions carry one line per printed line, so naming lines names an
advertisement. The American's do not: its densest advertising columns arrive as ONE line
of up to 11,361 characters carrying four separate advertisements and the segmenter's own
coordinate telemetry, so naming that line quotes seven other things. `spans` is the
character-level sibling of `lines_of_claim` — a list of `{line, from, to}` half-open
ranges — and when it is present the quote is those ranges joined by a newline instead of
those whole lines. Every range is still verbatim and still rebuilt from the file by the
gate; only the grain is finer. It is optional and additive: a claim without `spans`
behaves exactly as before, which is why the T-0257 fixture and the Democrat read needed no
edit. All 130 of the American's claims use it.

**Nor does the Democrat's own first issue, and SIX of T-0258's thirty do.** This count
has been corrected twice by reading — the two paragraphs below are the corrections, and
each names the sweep it refuted — and it stands at six issues carrying Chicago's own list:
**1834-01-14** and **1834-01-28** (the 1 January list, printed cut and then nearly whole,
T-0310), **1834-02-04**, **1834-03-04** (T-0312), and **1834-04-01** with its
**1834-04-08** reprint (the 1 April list, T-0313). The other twenty-four carry none of
Chicago's — the April Hennepin printings are another town's and mint nobody — so a reading
pass over 1833 and the first half of 1834 meets the epic's letter-list clause mostly by
demonstrating absence. Where a list IS there it is the census proxy and ruling 1 applies
in full.

**The fifth was found by READING and not by searching, and that is the lesson (T-0312).**
This file said four until March 1834 was read through, because a text sweep cannot match a
heading the segmenter has cut in half. The list of 1834-03-04 sits on page 4, and the crop
boundary runs down the middle of its printed column: `List of L` stands at the head of
column 2 and `etters` / `ost-Offiee at Chica-` / `34.` at the head of column 3. No search
for *list of letters*, *letters remaining* or *remaining in the post office* can hit a
heading that exists whole in neither column. **So sweep for the FRAGMENTS too** — `ist of L`,
`etters`, `ost-Off`, `advertis` — and expect a list to be split across two claims, one per
crop, the way `chicago_democrat_1834_03_04.json` c024 and c025 carry it. Its date line
survives only as `34.`, so WHICH return it is cannot be read and is not asserted; its
seventy-eight extracted names are a floor, cut on their left edge where January's were cut
on their right.

**THAT SWEEP WAS WRONG, AND READING APRIL 1834 IS HOW IT WAS FOUND OUT (T-0313).** It is
six of the thirty, not four, and the two it names for April are the wrong two. **1834-04-23
and 1834-04-30 carry the HENNEPIN list**, not Chicago's — as does 1834-04-16, which the sweep
missed as well — and out-of-county lists mint nobody here (T-0290, T-0292). Chicago's own
list of letters remaining on **1 April 1834**, over J. S. C. Hogan's signature, is printed
twice, in **1834-04-01** and **1834-04-08**, in the two issues the sweep passed over. The
reason a keyword sweep cannot find it is the reason a keyword sweep cannot be trusted on this
deposit: on 1834-04-01 the heading reads `SQA AINIG init` — that is `REMAINING` — and the
words *List of Letters* stand in the NEXT segmenter column, over the list's second half. So
every form of the heading this file lists was searched for, and every one of them returned
Hennepin. **Sweep for a list by reading the columns of the issues in the range, not by
searching them**; the eight issues of 1835 that only the deposit can open (T-0298) have never
been swept any other way.

**The Chicago American carries no post-office letter list.** Searched across all thirteen
issues for every form the Democrat uses — *list of letters*, *letters remaining*,
*remaining in the post office*, *uncalled for*, a signature ending *P. M.* — for exactly
one hit, and it is a list of State Bank of Illinois officers reprinted from the *Sangamon
Journal* (1835-06-27). The American's post-office notices are its hours and rules, signed
by the postmaster J. S. C. Hogan, and are extracted as `infrastructure`. The epic's
letter-list ruling has nothing to bite on in this paper; the census proxy is the
Democrat's.

**Nor does the Democrat carry one every month.** July 1834 (T-0289) and September 1834 (T-0291) were both swept for every form of the heading — *list of letters*, *letters remaining*, *remaining in the post office*, *uncalled for*, a signature ending *P. M.*, and the bare words *letter*, *postmaster* and *list* — and September's four issues carry none. The month's post-office matter is a reprinted Senate report, a Cumberland postmaster's letter about mail robbers, the Postmaster General's own Chicago-to-Green-Bay proposals (extracted as `infrastructure`) and a want-advertisement routing replies through the office. So the letter-list ruling has nothing to bite on there either, and `coverage.json` records the sweep rather than the silence — an absence a pass has looked for is evidence, an absence nobody looked for is a hole.

**A LETTER LIST IS STANDING TYPE, SO COUNT ITS PRINTINGS BEFORE YOU DATE IT (T-0331).**
The rule two sections above — count the printings before you send for the images — was
written about advertising and it holds harder for a quarterly return, because a return
runs unchanged until its letters go to the dead-letter office. The Chicago post office's
**1 January 1834** return stands in **every Democrat from Vol. I No. 7 of 1834-01-07 to
No. 15 of 1834-03-04, nine weeks unbroken**. The sweep this file used to record found
FOUR lists in T-0258's thirty issues; there are nine Chicago printings of this one return
alone, and the reason the sweep missed five of them is that it searched for the HEADING:
four of the nine headings are cut in half by the segmenter, illegible, or in a different
crop from the names they head. `tools/letter_list_printings.py` holds the nine, each with
the line its fingerprint stands on, and re-derives them.

Three things follow, and each has cost a run already.

- **DATE A LIST BY ITS CONCORDANT PRINTINGS, NOT BY THE ISSUE IT SITS IN.** The
  1834-03-04 crop keeps `34.` of its date line and nothing else, and T-0312 reasonably
  floated a 1 March quarterly return. It is January's. Four printings set the line whole
  or nearly — `go, Ill. January [1,] 1834.` at No. 7 line 645 is the plainest.
- **A LATER PRINTING IS NOT A SECOND COHORT.** T-0299's rule that one list mints once is
  a rule about the RETURN, not about the issue: nine printings of the 1 January 1834
  return are one list, and minting the ninth as a fresh 1834 cohort would have put the
  same men in the town twice.
- **THE CONCORDANCE REPAIRS THE DAMAGE THE IMAGES WERE ASKED FOR.** Every printing is
  cut in a different place, so the forename one crop loses another sets. Match on the
  SURNAME — the part the damaged crop states plainly — and complete a forename only where
  two or more PRINTINGS agree; twenty-five of fifty-seven cut readings on 1834-03-04 were
  repaired that way and none of them needed a scan. Two guards make it safe, and both were
  put in after the loose version proposed `Thomas Bonnet` for `[…]as Bennett`: the fold
  closes only the confusions the scans actually make, and **a surname standing TWICE in
  one list is never completed** — two Bennetts, two Miners, two Temples and two Tullers
  stand in this return, and a crop that lost both forenames cannot say which line is which.

**AND THEN THE IMAGE WAS READ, AND IT PRICED BOTH ROUTES (T-0424).** The page images
the concordance was built to avoid were finally fetched for this one list — the scan
behind the deposit is the public Internet Archive item
`chicago1835-newspaper-chicago-democrat-1834`, and the IIIF regions read are recorded in
`data/research/newspapers/letter_list_1834_01_01_printed.json` beside all 170 printed
lines. Four things came off it, and three of them could not have come off anything else.

- **THE PRINTED LENGTH IS 170**, in two sub-columns of eighty-five: Eliphalet Atkins to
  J. P. Harkness, Isaac Hays to Samuel Wright, over John S. C. Hogan's signature. The
  crops mint 78. **The hand count was a floor at 46 per cent of the list**, and the 92
  missing lines are the segmenter's loss, not the paper's — which also means the 97 names
  minted from the 1834-01-28 printing are a floor of the same return, not a census of it.
- **THIRTY-ONE OF THE THIRTY-TWO READINGS THE CONCORDANCE COULD NOT CLOSE ARE CLOSED**,
  including all four the doubled-surname guard blocked. Read the SAME impression the crop
  was cut from and the guard is unnecessary: the crop lines are in printed order, so
  `as Bennett` is line 13 and `Bennettra` line 19 by position alone. The list holds THREE
  Bennetts, not the two the concordance could see.
- **TWELVE READINGS WERE WRONG, and three of them were concordance completions.**
  `[Ori]nda Miner` is Miranda Miner — Orinda is a different person on the same page,
  Orinda Garyl; `[Ne]stor Marshall` is Chester Marshall; `John Monroe` is John Monreou.
  That is the price of completing a name from another impression, and it is worth paying
  for twenty-five repairs — but a completion is a hypothesis until a scan is read, and
  `completed_from` is what lets a later pass find every one of them.
- **ONE FRAGMENT THE IMAGE CANNOT PLACE STAYS UNPLACED.** No line of the printed list
  reads `Leena` or `Cenige`; each of those crop lines is one of three or five printed
  lines the crop lost around it, and both are recorded with their candidates and keep
  `reading: transcription_mediated` while every other entity takes `scan_verified`.

`tools/read_letter_list_1834_image.py` holds the tie from every crop entity to its printed
line and `check.sh` gates it, because the tie is by ORDER: a line added to or dropped from
the roster re-points every entity below it at its neighbour, silently.

**A SECOND OFFICE'S RETURN RUNS IN THE SAME WEEKS.** Hennepin's 1 January 1834 list is
printed alongside Chicago's at No. 9 line 937 and No. 10 line 957, and a sweep that
matches on `REMAINING in the Post-Office` alone will fold the two towns together. Resolve
the office off the heading's own tail before minting a name.

**`[…]` marks absence, `[word]` marks a supply.** Text the column edge cut away is a gap,
not an invitation. The worked fixture leaves *'a few doors below'* unsupplied for exactly
that reason and says where a fuller witness might be found.

**The owner's three rulings live in fields, not in prose.** `letter_list_only` on a person
(a listed name mints a resident candidate, and the weaker evidence stays distinguishable);
`reading` required on every claim (`transcription_mediated`, or `scan_verified` where a
scan was read and outranks it); and `built_at_scene_date` / `survival_liberty_required`
computed on a business — documented businesses stand in the 1835 town unless a claim
contradicts them, and one last seen before 1835 stands on a stated liberty.

**Identity never coalesces by accident.** The gazetteer is keyed on the whole normalized
name, so `Cohen, P.` and `Cohen, J.` are two people. A merge is declared in
`identity.json` with a `merge_rule` naming both spellings; same surname with different
initials never merges, rule or no rule.

**The first bulk merge pass is T-0299**: the list of letters remaining in the Post Office at
Chicago on 1 July 1834, which the Democrat printed three times — 1834-07-02, 1834-07-09 and
1834-07-16 — and which the segmenter cut differently each time, so 298 names had been
minting up to three people apiece. The three readings are aligned BY POSITION, because the
list is one ordered sequence that every printing carries in the same order; a pair is a
candidate only where the alignment puts the two readings at the same entry, never on
resemblance alone. **175 merges declared and 29 REFUSED**, the refusals recorded in
`refused_merges` beside them with the surname the two share and the initials that separate
them — the refusals are the evidence that the pass was a judgement and not a
de-duplication. The gazetteer went from 2,108 persons to 1,933. The file's `passes` block
states the method, the canonical-reading rule, and the two returns printed in the same
issues that are deliberately NOT part of this list (Plainfield and Juliet). Seventeen of
the twenty-nine refusals are an initial one printing could not read against the same
initial another prints whole. **Whether such a pair may merge is NOT settled here**: it is a
change to the identity policy and it is the owner's, and T-0392 carries the question with
both answers and their costs — no keeps eighteen duplicate persons the project's own best
witness resolves, yes needs a bound (same list, same entry, no competing letter).

`surname()` and `initials()` take the transcription's markup off before they parse (T-0299).
They did not, so `A[n]drew W. Borland` read as four forenames and `Benjamın Swena` as two,
and whether the policy protected a pair came down to which side of a name a bracket fell on.
The policy is unchanged; ten self-test cases hold both halves of that.

**AN UNREAD `[?]` IS A POSITION, NOT AN ABSENCE (T-0397).** Taking the markup off is right
for a surname and was wrong for a forename, because DELETING the `[?]` hands the initial to
whatever letter stood behind it. All seventeen `[?]` refusals above had been stated on such
a reading: seven named a letter invented from the rest of the forename (`[?]rah Fowler` as
`R.`, `[?]nn M. Gooding` as `N. M.`, `[?]saac Scarrett` as `S.`), six collapsed a middle
initial into first position (`[?]. M. Fish` as `M.` against `E. M. Fish`'s `E. M.`), and
four read no initial at all — which is the shape all seventeen were assumed to have. So a
committed record was asserting letters no printing carried. `initials()` now records the
marker as UNREAD, in the slot it was printed in, welded to the word it opens, and UNREAD is
equal to no letter; every `refused_because` states the reading the page carries and each
refusal carries its parsed `initials_read`. **Nothing merged or unmerged** — 177 declared
person merges and 29 refusals before and after, 2,634 persons either way, and `gazetteer.json`
and `register_1835.json` are byte-identical across the change. Nine self-test cases assert
the VALUE and not merely that a pair differs, which is what let `[?]nn M. Gooding` pass while
reading `N. M.`

**AND THE RULE HAS NO SIBLING FOR FIRMS, WHICH IS WHY ONE BOOKSHOP STANDS IN THREE PLACES.**
The Chicago Democrat's bookseller is `RUISAL & CLUPR,` in the December 1834 advertisement's
only legible heading, and T-0327 read the name off the firm's OTHER advertisement rather
than off that line: the copartnership notice dated `Chicago, Aug. 26, 1834` — Aaron
Russell of Boston and [—] Clift of Philadelphia, opening a store adjoining P. Carpenter's
drug establishment in Water-street — runs from 1834-08-27 to 1834-11-12 and is signed
legibly four times, `RUSSELL & CLIFT`. So the December claim's business name is now a
supply, `[RUSSELL & CLIFT]`, and the compiler folds it into `business_russell_clift` by
key, which is a corrected READING and not a merge. What the key cannot fold is the rest:
`business_chicago_wholesale_and_retail_book_stationary_store` is the 1834-08-27 printing of
that same notice, whose signature went with the woven half of the column, and
`business_russell_clift_chicago_book_and_stationary_store` is the firm's own 1835 card in
the *American*. Three keys, one house, and the evidence for it is a shared copy date and a
shared body of type — but joining them means DECLARING two names one firm, and that is
exactly what `identity.json` supplies for people and, as of T-0304, for firms as well:
`firm_merges`, below. The three keys stand apart until somebody declares them, because a
declaration cites its printings and nobody has yet written that one down (T-0340) — but the
place to write it now exists, and the alternative it replaces was a hand-merge, which makes
a gazetteer nobody can recompile.

**Firms have the same policy and a different discriminator** (T-0304). A business is keyed
on its whole name too, so five printings of one house are five businesses until something
says otherwise, and `firm_merges` is where that is said — same two rules, a `merge_rule`
naming both spellings verbatim. What changes is the guard. For a person a differing
forename initial is fatal, because the letter lists are full of families; a `& Co.` style
routinely elides or misprints the forename it trades under, so applying that rule to firms
would refuse every merge a firm needs. What survives is the SURNAME: the two styles must
carry the same set of partner surnames, with or without a rule, because a partnership is
its partners and a changed one is a different house — which is what keeps `Clark, Filer &
Co.` and `A. Filer & Co.` apart. The second guard is about the ground rather than the
name: two styles the papers put in different STREETS never merge, because a firm that
moved is documented by a removal notice, and a removal notice is a claim. A merge takes
the union of mentions, proprietors, goods and copy dates, the wider issue window, the
more specific placement, and every trade either side printed in `trade_variants` — it can
widen a record and it cannot narrow one.

**A VENDOR'S FOR-SALE NOTICE PLACES NOTHING** (T-0412). A `building` claim carries an
address because the notice gives one, and the extractor attaches the business the
signature names to it — which is right where the signer KEEPS the house and wrong where he
is only selling it. P. Pruyne signs "[W]E offer for sale the House on [the corner] of
Lasalle and Lake streets. [It] is 16 by 30 feet" (`chicago_democrat_1834_05_21` c001) as
VENDOR; the record it minted was merged into `P. Pruyne & Co.`, whose store the papers put
between Clark and Dearborn streets across four printings, and the corner then stood among
that firm's `placement_readings` as though it were a second frontage of the store. It did
no harm there, and that was luck: the minting printing's own placement was `none`, so
`placement_rank` never promoted the corner. **A vendor notice that happened to be the only
reading on its record would have moved a firm to a house it was selling.**

So a `building` claim whose own entities sign it as the **vendor** of that building
contributes no placing reading to the business the signature names. What the printing said
about the firm's own ground is nothing, and it records `{"class": "none"}` — the same value
every other silent printing records, so the claim key still stands in the record's readings
and no printing is dropped out of the history. The notice is kept on the business as
`vendor_placements`: the placement as printed, the address text, the role as authored and
the claim, so the judgement can be read back off the record it was made about. **The
building is not lost** — the claim in `extracted/` is untouched, a documented Chicago house
with a named corner and a 16-by-30-foot footprint, and it is a candidate for the buildings
programme rather than a frontage of somebody's store (T-0783).

The match on `role` is **exact** — `vendor`, or `vendor` followed by a qualifier ("vendor at
auction") — because `role` is free prose in this corpus, some three hundred distinct
strings, and a looser rule would silence an auctioneer selling at his own store house.
`chicago_democrat_1834_04_16` c008 is precisely that: "auctioneer, selling at his own store
house", and the business is David Carver's own commission house. Anything other than
`vendor` is a role somebody has to write a rule for, deliberately, having read it. **The
sweep found exactly one record in the position** — the corpus carries three `vendor` roles
in all, and the other two are on claims that place nothing (`1834_05_14` c006 is
`street_only`, `1835_08_05` c023 mints no business).

**A pair judged NOT one house is a record too** (T-0399). `firm_surnames()` groups the
register on the partner surname alone, so it puts together houses that are not one house
— the two Montgomerys, a namesake, an anchor mistaken for a partner. Until this ticket the
only record of having judged such a group was the ABSENCE of a merge rule, which reads
exactly like a group nobody has looked at yet: the next sweep finds the group again, does
the work again, and the argument for keeping the pair apart — the thing that stops a wrong
merge on the second pass — is the part that was never written down.
`refused_firm_merges` is that argument, declared as explicitly as a merge and held to the
same disciplines. `refused_because` names BOTH styles verbatim; `witnesses` names the
printings the refusal rests on, because a refusal rests on printings exactly as a merge
does; `kind` is one of three, because *not shown to be one* is a different finding from
*shown to be two* — `two_houses` (the papers show two houses under one surname),
`not_joined` (one name, and no printing puts the two styles under one roof), and
`different_ground` (one house, and the papers put the two styles in different places: a
removal or a succession, which is a claim and not a merge). And a refusal **cannot outlive
its pair**: if a later merge collapses the two styles it names, the refusal is a judgement
nobody can check, and the compile fails rather than leaving it to rot. Each refusal is
written onto both of the businesses it holds apart, so a reader meeting one of them meets
the reason the other is not it.

`premises_relations` is the **third answer**, and T-0411 is the ticket that found the
first two are not enough. A merge says two styles are one house; a refusal says they are
not one house; the corpus keeps producing pairs for which BOTH sentences are false. The
Chicago Democrat against the Chicago Democrat printing office is the case: T-0402 was
asked to judge it and could write down no true thing. `firm_surnames()` reads the last
word of each style as the partner surname and so compares `{democrat}` against `{office}`,
and the partner-surname guard has no escape by design — but neither style names a partner
at all, so there is nothing here for the guard to be about. And all three refusal kinds
are untrue of it: they are not `two_houses` (one man, John Calhoun, stands over both), not
`not_joined` (the colophon IS the paper naming the shop it is printed at), and not on
`different_ground` (in 1834 both stand on the corner of South Water and Clark). A refusal
here would have been a false judgement filed to make a group look closed, which is why
T-0402 declined to file one.

So the relation states the one thing that IS true — **two businesses, and one of them is
the other's premises** — in one direction, and it is not a merge: both records stay whole,
keep their own printings, their own placement readings and their own trade, and the
partner guard is untouched. It is held to the merge's disciplines: `relation_rule` names
both spellings verbatim, `witnesses` names the printings it rests on, it cannot outlive
either end, it may not be declared alongside a merge or a refusal of the same pair, it may
not run both ways, and a business may stand on **one ground only**. `kind` is one of two:
`premises` (the part is the ground the whole is carried on — one roof, and the model must
not mint a second for the whole) and `department` (the part is a branch of the whole's own
business under a style of its own). The edge is written onto both records — `part_of` on
the premises, `parts` on the house carried there.

**The roof is DECIDED and not left to fall out of the data**, which is the half of T-0411
that is visible in the town. One roof: `chicago_democrat_office`, which already stands at
that corner and carries "John Calhoun's printing office" among its aka. The shop enriched
it; the paper did not, because `match_occupant` requires ALL the partners' surnames and
the paper's proprietors read `['John Calhoun', 'Calhoun, J.']`, a required set of
`{calhoun, j}` no occupant line can carry — so `compile_register` took `new_building` at
`clark+south_water` for it, a second roof at the same corner for a business with no ground
of its own. `compile_register` now makes the whole follow its premises where the premises
is placed and the whole was about to raise or name ground of its own, and the register's
actions move from 30 `enrich_existing` / 29 `new_building` to **31 / 28**. The businesses
table does not move: 206 before and after, because a relation is not a merge.

**T-0403 stays open**, and on purpose. It records that the printing office keeps its 1834
corner through T-0399's internal merge, because `placement_rank` prefers a corner to a
relative offset regardless of date — so on the scene date the shop may stand at the wrong
end of South Water Street, and the paper now stands with it. That is a question about
placement RANKING rather than about identity: joining the pair moves neither reading, and
answering it would mean changing how every house in the register chooses its live address.

**The first firm pass is T-0399**, the restyled duplicates of T-0338's surname groups —
where one style is the other with a trade description, a signboard or an extractor's
parenthesis after it. **25 merge rules over 20 houses, and 3 refusals**; the businesses
table went from 242 to 221 and `survival_liberty_required` from 126 to 111, because
records that were each claiming a liberty for a shop last seen before 1835 turned out to
belong to a house still advertising in 1835 under its other heading. The three refusals
are A. Garrett (`different_ground` — the auctioneer advertises from South Water street in
December 1834 and signs from Dearborn street twenty months later, with no removal notice
between them), B. Jones (`not_joined` — a grocery and a forwarding house set as two
advertisements in one issue; a business record here is a trade with a place, not a
proprietor) and W. Montgomery (`two_houses` — the auctioneer at David Carver's old stand
against L. W. Montgomery the bootmaker next door to P. Cohen's). T-0400, T-0401 and T-0402
carry the bands the pass did not reach.

**The second firm pass is T-0401**, the surname groups that are NOT one house — and it
merges nothing at all. **16 refusals, and the businesses table does not move**, which is the
shape of the ticket: the whole output is the written argument. Five hold the Kinzies apart
(J. H., John S. and R. A. — the Democrat of 1833-12-10 prints two of the family on one
page, and 'JOHN 8. KINZIE' in that same issue is a damaged glyph the file refuses to repair
into an H, so that pair is `not_joined` rather than `two_houses`); one each for J. H.
Mulford the jeweller against the carriage and sleigh maker who shares his surname and an
issue, W. H. Brown the grocer against 'Brown, painter' who has no forename to compare, and
Wm. H. Taylor the boot store against Charles Taylor the tailor; three for the Curtisses,
where an attorney read once as J and once as L stands against L. G. Curtiss the deputy
surveyor of Cook County, and the Democrat of 1835-08-05 prints the attorney and the
surveyor in one issue.

The last five are the ones worth the section existing. `firm_surnames()` takes the LAST
word of a partnership segment as the surname, so a style ending in a trade word is grouped
on the word: 'store' alone holds thirteen businesses, and the New York Clothing Store,
Peter Cohen's store and W. Kimball's New Store are refused against each other with that
said in each, so the failure stays legible if the function changes. 'Eagle Hotel' against
'the new blacksmith shop opposite the Chicago Hotel' is the same failure one step worse —
the word belongs to the ANCHOR inside the second style, so a house is grouped with the
building it stands opposite. And the two Chicago & St. Joseph packets are a group made
entirely of words: the split on '&' and 'and' turns the route's own name into the partners
'Chicago' and 'packet', and the schooners Llewellyn and Phillips are two hulls on one run.

**Six of T-0401's candidates turned out to be one house** and are recorded in T-0413 rather
than refused, with the printings that show it: P. F. Peck and P. F. W. Peck on one La Salle
corner in abutting windows, F. G. and G. Blanshard opposite Dr. Temple's, G. W. and W.
Keeney a few doors below Newberry & Dole's, Dr. J. B. and Dr. J. H. Barnard at the New-York
House nine days apart, M. H. and Wm. H. Kennicott on one copy date, and J. and L. Curtiss
on one copy date at one anchor. A refusal asserted against the evidence is worth less than
no refusal at all, so none was written for them; a merge would have moved the business
count this ticket holds fixed, so none was written either, and the reading is in the ticket
so it is not done a third time.

**The second firm pass is T-0400**, and it is the band where the two styles carry the SAME
partner surnames and differ only in the FORM of a forename — whole against abbreviated
against bare initial. T-0304 had already ruled that a forename initial is not decisive for a
firm the way it is for a person, so this band is judgeable; what it needed was, in each case,
the printing that ties the two forms to one house. **Eight merges and two refusals over ten
groups**, taking the businesses table from 217 to 209 and `survival_liberty_required` from
109 to 103. Not one of the eight rests on the forename. `Collins & Caton` and `J. H. Collins
& J. D. Caton` share the card copy-dated Jan. 20, 1834 and the anchor next door east of
Brewster, Hogan & Co.; `G. Spring` and `Giles Spring` share the card of Dec. 3, 1834 and then
print the same removal to the Tremont House; `J. Bates, Jr.` and `John Bates, Jr.` run the
same advertisement for the same sixteen steel-pointed crowbars, both times signed with the
INITIAL, the kegs of blasting powder down from twelve to seven; `J. Wellmaker & Co.`'s own
dissolution notice sets the firm's name as `John Wellmaker & Co.` inside the record filed
under the short style; and the timber notice of Ap'l. 22 runs over `P. PRUYNE & CO.` in one
printing and `P PRUYNE` in the next, with a plural subscriber above a singular signature both
times. The two refusals are as much the point of the band as the merges: `J. D. Caton,
attorney and counsellor at law` against `John Dean Caton` is `different_ground` — the same
man, South Water Street in December 1833 and Dearborn Street in July 1835, with the
partnership between them and no removal notice anywhere — and `John Wright` against `J.
Wright, merchant` is `not_joined`, a Democrat dry-goods house of 1833-34 against an American
seller of leather, salt and oak scantling in July 1835, with nothing printed to join the two
forms.

**And the proprietors are a third place a name lives** (T-0337). `business.proprietors` is
neither a gazetteer person nor a firm style — it is a string put on a business record by
whichever claim read that printing — so neither policy above could reach it, and one man
read two ways stood as two proprietors of his own house. `business_russell_clift` carried
'Benj. Clift' from the 1834-09-03 impression of the copartnership notice and '[H. H.] Clift'
from the 1834-11-12 impression of the SAME notice; four impressions of it survive in the
deposit and three set the name whole, so the man is Benj. H. Clift and the second initial
was the line's debris. The rule that now stops the next one is the firm-side sibling of the
person rule, pointing the other way on purpose: two person-styled proprietors of one house
sharing a surname and carrying different READ initials are refused until `identity.json`
declares which they are — `proprietor_merges` to join two readings, `proprietor_distinctions`
to hold two men apart, each with its reasoning. Neither merge nor silence can be the default,
because a house really does hold brothers (William and Franklin Brewster sign one dissolution
notice) and really does hold one man read twice. A bare surname beside a full name is not a
pair — that is the papers printing less — and a declaration whose pair has gone is refused
too, so the file cannot rot.

**And a proprietor is not always a person either** (T-0398). The other half of that list is
the house's OWN trading style, put there by a notice that signed nothing else: the Democrat
of 1835-08-19 prints "for sale only by Russell & Cl[if]t (Agents for the State of
I[ll]inois) at the Chicago Book Store", so `Russell & Clift` stands among
`business_russell_clift`'s proprietors beside Aaron Russell and Benj. H. Clift. That is what
the paper printed and it is not a misreading — 28 of the 199 houses carry their style this
way — but read as a list of people it says the partnership is its own third partner. Each
business record therefore carries `partners` and `firm_styles` beside `proprietors`, both
DERIVED by the same `firm_styled()` the proprietor policy above steps over styles with, both
in the order the proprietors print, and neither editing a claim: `proprietors` is still the
union of what was read. `partners` is EMPTY for the twelve houses the papers only ever
signed with the firm — `H. Doty & Co.` is the whole of that record's list — because no man
is named, and an empty list is the honest answer rather than a surname guessed out of the
style. Nothing is declared: `firm_styled()` sees every style the corpus prints, and
`identity.json` would only be needed for one it cannot. The register carries both fields
through, and `mint_placed_residents.py` reads `partners` where it asks whether a printed
name is a house or a man — a house that signs its own notice can no longer vouch for itself
against a test written to catch exactly that. What still reads `proprietors` whole is the
surname passes, deliberately: a style carries real surnames (`Clark, Filer & Co.`) and
reading them all out of it is T-1042.

**And a name is not always a person** (T-0359). A claim's entities are keyed on a name and
carry no notion of what KIND of thing a name is, so a building the papers name by its
signboard arrives in the persons table and is then held to a policy written for people.
The compiler read `Tavern` as the surname and `Haddock's` against `Maddock's` as forename
initials, and the families rule refused a reconciliation the evidence closes: one For-Sale
notice of G. Spring's stands over five settings, four read Haddock's and one reads
Maddock's. The rule is right and the subject was wrong. `identity.json` therefore has a
third section — `places`, where a name is declared NOT to be a person with the argument
written out, and `place_merges`, which joins two spellings of one building afterwards. A
place has no forename initial to be a family by and no partners to be a house by, so the
discriminator is the declaration itself: **a place merge may only join two names `places`
has already argued are not people**, which is what keeps this from becoming a hole in the
families rule. Two more guards protect the same thing from the other side — a name whose
every mention is a post-office letter list may not be declared a place at all (a letter
list is a list of people somebody wrote to, and `Chester House` and `Rodney House` are
exactly that shape, both recorded in `refused_places`), and neither may a name a claim
gives an occupation to. Five names are declared: Haddock's and Maddock's Tavern, the Eagle
Hotel, the Eagle Hotel (Steele's) and the Baptist meeting house; the two taverns merge and
the two Eagle readings deliberately do not, because nothing in the corpus prints both and
a shared word is the resemblance argument this file exists to refuse (T-0397). The table
lands in `gazetteer.json` as `places`, beside `persons` and `businesses`, and the register
compiled from it no longer carries signboards as inhabitants of the town.

**And some things the papers name are neither a person nor a house** (T-0410). The Howard
Fire Insurance Company of the city of New-York sold fire insurance in Chicago through a
LOCAL AGENT, and an agency is not a trade, a shop or a signboard: it is a RELATION between
a principal that never stood in this town and the house or the man who held it for a
season. With only `persons` and `businesses` to mint into, the corpus expressed it the one
way it could — as its own business — which then collided under `firm_surnames()` with the
house holding it and had to be refused by hand. T-0402 wrote that refusal and it said the
wrong thing: *these are two houses*, when the finding is that they are JOINED, by an agency
that passed from one to the other.

`identity.json`'s fourth section, `agencies`, is that relation. A declaration names the
principal with a `why` that names it verbatim, lists the `holdings` — who held it, whether
a `business` or a `person`, and the printings each holding rests on — and may name a
minted record it `retires`. Two things it does NOT do are the point. **The window is
computed from the witnesses' own issue dates and may not be asserted**, the same discipline
as ruling 3. And **a holding says that a house held the agency and nothing else**: no
proprietor, no trade, no street, no roof, because a man who signs for a principal is not
thereby a partner in the house he signs for — which is precisely why E. K. Hubbard could
never be merged into Hubbard & Co. `refused_holdings` is the same record kept the other way
up, for a candidate the printings refute. A retirement is guarded four ways, because it is
the only declaration in this file that takes a business OUT of the register: the record
must be one the register carries, it must be unplaced (a placed record would take an
address out of the town with it), every printing it was compiled from must be a witness of
some holding, and no refusal may still name it.

The Howard is the first and the whole of the section so far. **Two holdings, one refusal,
and the businesses table goes from 206 to 205.** Hubbard & Co. held it first and advertised
in the PLURAL over the firm's signature — 'The subscribers having been appointed Agents for
the Howard Fire Insurance Company of the city of New-York … HUBBARD & CO.', 1834-07-02 c048
through 1834-10-15 c005 to 1835-05-20 c023. From 1835-06-20 c015 the identical copy runs in
the SINGULAR over one man, 'THE subscriber having been appointed agent … E. K. HUBBARD.',
reprinted by the Democrat at 1835-07-01 c017, 1835-07-08 c005 and 1835-07-29 c011. So on
the scene date the agency sits with the man, the forwarding house goes on trading under its
own name to 1835-08-29, and nothing here makes E. K. a partner in it.

**The third holder the ticket was filed for does not exist, and the printing that seemed to
show it is what refutes it.** T-0410 read Jones, King & Co. as a third holder off
1835-08-05 c008, and the register agreed: that business record announced itself 'appointed
Agent for the Howard Fire Insurance Company' over a dateline of 1 July 1835. The fragment
carries TWO notices, as its own claim note had said since T-0335 — its reading runs 'July
1, [1835]. [E]. K. [H]UBBARD. — Hardware, Stoves, &c. Th[e] u[n]dersigned have [formed a]
connect[ion] … under the [f]irm o[f] Jones, [King] & [C]o.', and the hardware notice is
signed WILLIAM JONES, BYRAM KING, W. B. CLARKE while the insurance card above it is signed
by the man. The claim's own entity list already read `UCBRARB,` as 'Hubbard, E. K.' with
the role *insurance agent*. So c008 is the FIFTH printing of E. K. Hubbard's holding, Jones,
King & Co. is recorded as a `refused_holding` on the printing that refutes it, and the
claim's `announces_opening` — the agency's sentence read onto the hardware firm's record —
is dropped. Nothing of the quote, the normalized reading or the entities moves. The firm's
own opening is still announced by its formation notice at 1835-07-08 c009 and 1835-07-22
c009. With the minted record gone the T-0402 refusal has no pair, so it comes out in the
same pass; the OTHER refusal that ticket wrote, 'Jones & King' against 'Jones, King & Co.',
is a copartnership succession and not an agency, so this relation leaves it standing.

The scene-date Democrat, `extracted/chicago_democrat_1835_07_01.json`, is both the worked
fixture (claims c001-c003, T-0257 — Peter Cohen and J. S. C. Hogan on South Water Street,
and one letter-list name) and the first issue read through (c004-c021, T-0295).

**And `extracted/chicago_democrat_1833_11_26.json` is the one issue where the scan outranks
the transcription in practice rather than in principle** (T-0308, the first piece of T-0258).
Vol. I No. 1 is the only issue in the corpus with a per-issue source record read off the page
images, `data/sources/chicago_democrat_1833_11_26.json`, and six of its thirty-three claims
carry `reading: scan_verified` because the record supplies type the transcription lost — the
schooner's master, the tavern keeper, Philo Carpenter's name, Kimball's address, Goss & Cobb's
address, the imprint. One claim runs the other way and is worth as much: the record warns that
*a* transcription of this issue read "C. & L. Harmon" for "C. & I. HARMON", and the deposit
transcription read here has the I, so the warning now attaches to a named artefact instead of
to transcriptions generally. Two advertisers the record does not enumerate — C. H. Chapman and
S. Foot — are added by the transcription pass, and three traps the record quarantines are
claimed by neither: the stock engraving over "Two Buildings to Let", the pencilled "S. W." in
the margin beside the imprint, and the estray notices, which are county filings from Du Page
and Walker's Grove and not Chicago.

**It is read from the deposit `primary`, not from the `-2` rebuild `dev` can open**, and
the reason is the letter list: the primary sets it legibly at name level and the alternate
does not. So its quotes are verified with

    tools/compile_gazetteer.py --check --deposit <a materialised deposit>

and the committed gate on `dev` reports them unresolved-but-green until T-0275 lands. The
segmenter cut each printed column in half and alternates the halves line by line, so nearly
every claim there is `interleaved`, and most bracketed supplies are read off the OTHER half
of the same printed lines — each claim's note names the lines they came from.

## `register_1835.json` — the work list (T-0262)

`gazetteer.json` is an index of what was PRINTED. It says nothing about what the model
should build. `tools/compile_register.py --build` turns it into the register the seeding
tickets read: for every business, whether it stood on 1 July 1835 and what the town has to
do about it; for every person, whether the town already holds them.

    tools/compile_register.py --build       recompile register_1835.json
    tools/compile_register.py --check       the gate (check.sh runs it)
    tools/compile_register.py --self-test   the gate's assertions still fire

**It is DERIVED, and the gate refuses a hand-edit** — the same contract `gazetteer.json` is
under, for the same reason: a hand-edited register is a place to promote a business into the
town without an argument, and T-0263 and T-0264 read it as if it were derived. Its inputs are
the gazetteer, `data/structures/`, `data/streets/1835.json` and `data/residents/`; change
those, not this.

**Four business actions.** `enrich_existing` — a committed building already carries this
house, and the row names the field it matched on and the exact text. `new_building` — nothing
committed carries it and the paper's own placement resolves: a corner of two platted streets,
a landmark that is a committed structure, or ONE hop through another documented business that
is. `street_only` — a platted street face and nothing narrower. `unplaceable` — no street the
model holds.

**Two guards on a match into the committed town, both T-0355.** A structure's `occupants`
line is read CLAUSE BY CLAUSE, and a clause that dates itself to a year the scene date does
not fall in is a former tenant, not evidence of who is there now:
`wolf_point_tavern_stable` records "the tavern's keeper of the day — Elijah Wentworth in
1831, William Walters on the scene date", and read whole it matched E. Wentworth's tavern.
And a business whose OWN record puts it out of town takes no action at all — `outside_plat`
names the marker and quotes it. Three markers, each a positive statement: a distance in
miles (the plat is under a mile across), a road LEADING TO somewhere (the town's own ways
are streets), and a named creek (the committed town holds the river and its branches and no
creek — `read_town` checks that rather than asserting it). Five of the 242 businesses are
excluded this way and all five are genuinely out of town: four readings of Wentworth's
tavern on Flag Creek, eighteen miles out on the Ottawa road, and Richard M. Sweet's barn on
the Dupage.

**Three person actions.** `enrich` (already in `data/residents/`, matched under the
gazetteer's own identity policy, imported so the two tools cannot drift), `replace_invented`
(a documented person of a trade the town invented a household for) and `new_resident`
(everybody else — owner ruling 1, a letter-list name is enough).

**Two exclusions, and the second one reads the paper (T-0356).** A contradiction dated ON OR
BEFORE the scene date excludes; a LATER one is recorded (`dissolved_after_scene_date`) and
disobeyed, because a firm dissolved in August 1835 was demonstrably open in July. The second
used to be the proxy `first_evidence_after_scene_date` — T-0262 asked to exclude on an
`announces_opening` field the claim vocabulary did not have, so the register excluded every
business whose first surviving issue postdated 1 July. It is now
`opening_announced_after_scene_date`, and it reads the field itself.

**`announces_opening` is a reading, and its `dating` is the whole of it.** A claim of kind
`business` or `building` may carry `{verbatim, dating, iso, note}`. `verbatim` must appear
character for character in the claim's `normalized` reading; `note` says how the date was
read; and `dating` is one of:

| dating | what the printing says | what the register does |
|---|---|---|
| `stated` | names a date the house WILL open | excludes if that date is after the scene date |
| `effected` | announces an opening already made; `iso` is the advertisement's own dateline and the gate refuses any other number | never excludes — the dateline bounds the opening from ABOVE. On or before the scene date it is positive evidence |
| `undated` | announces an opening and dates it nowhere; `iso` must be absent | decides nothing |

It had been a bare `true` on twenty claims that nothing read. The gate now refuses the
boolean, so those twenty were re-read into dated readings, which is where Wm. H. Taylor's
8 July 1834 dateline came from.

**What the proxy cost, measured on the re-read.** Thirty-eight businesses carried it; four
of them genuinely announce an opening after the scene date and stay out (Cromelien's wine
branch, 14 Aug; Everts' high school, 10 Aug; Hunt's, 17 Aug; Lyon's wholesale grocery,
1 Sep). The other thirty-four are back in the July town — among them five printed standing
in it: Taylor's boot store over an 8 July 1834 dateline, Kennicott saying he had practised
dentistry here "for the past year", Samuel Lewis's copy dated 22 June, S. Abell's 24 June
and John Holbrook's 10 June.

**And standing on August evidence alone is a liberty, which the register names.**
`backdating_liberty_required` is the forward twin of `survival_liberty_required`: documented
only after the scene date, present on it by assumption, and no opening notice dated on or
before it to carry the assumption. Thirty-three businesses. `docs/LIBERTIES.md` carries
neither class yet — T-0357 is the survival half and T-0404 the backdating half.

## The trade-class and place rulings are guarded against a lost judgement (T-1125)

Two hand-authored adjudications live in this directory, and both are read by gates that
re-derive downstream of them — which means a shrinking file passes every one of them. Since
T-1125 `tools/check_rulings_not_lost.py` (run by `check.sh`) holds both to the MERGE BASE
by identity as well as by count.

**`trade_class_rulings.json`** — `trade_rulings` (145) and `business_overrides` (4) are the
judgement. `scope` is part of a trade ruling's identity because the same trade is ruled
twice, once inside the town and once outside it. LEFT OUT: `vocabulary` transcribes the
eighteen printed count-lines of the census and its `compared` flag is recomputed by
`trade_census_1835.py --check`; `register_cautions` is prose about the register rather than
a ruling on it; `boundaries` is the rule text B1–B6 the rulings cite, and a rule is not one
of the things it rules on.

**`place_vocabulary.json`** — `places` (128) is the judgement: a place the newspapers name,
resolved inside or outside the committed town. LEFT OUT: `counts`, which
`resolve_place_vocabulary.py --check` recomputes field by field from the gazetteer and
these rulings, and which the file itself says is measured rather than asserted. The
identity is the `place` and nothing under it, because the `derived` block inside each entry
is rewritten by that same tool.

**To remove a ruling from either**, move it into `withdrawn[]` with a `reason` and the
`ticket` that decided it; it is counted alongside the rest, so the total never falls.
