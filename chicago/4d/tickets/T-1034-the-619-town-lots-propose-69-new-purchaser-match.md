---
id: T-1034
title: The 619 town lots propose 69 new purchaser matches and nobody has ruled on one: adjudicate them in cohorts as T-0990 did, and bring the land_sales ceiling back down from 869
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-11
pr: 1164
claimed_by: run 9/11/2026, 8:59:44 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T02:34:06.311Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34666288560
---

The 619 town lots propose 69 new purchaser matches and nobody has ruled on one: adjudicate them in cohorts as T-0990 did, and bring the land_sales ceiling back down from 869.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- the cohort is NAMED in the claim commit, and every spelling in it carries a ruling in
  `data/research/land_sales/resident_rulings.json` — `upheld` or `refused`, each with its
  `checked_against` and its reasoning;
- `python3 tools/read_land_sales.py --build` and `python3 tools/spend_land_sales.py` are
  re-run, and what moved is itemised in `data/research/land_sales/README.md`;
- the five derived files a retraction moves are re-run in the same pass —
  `export_resident_audit.py --build`, `consolidate_resident_evidence.py --build`,
  `consolidate_town_cards.py --apply`, `compile_scene.py --all` — because `check.sh`
  reports them one failing step at a time (T-0990 cohort C3's lesson);
- `bash tools/check.sh` green;
- the ceiling comes down as far as the cohort earns, with `measure_research_spend.py
  --tighten land_sales`, and the PR says how far and why not further;
- **the run that closes a cohort names the next one here before it closes.** This ticket
  closes when the crosswalk's `ruled` block reads zero unruled, and says so WITH the count
  — never on "there was nothing left".

---

## COHORT LOG — this ticket stays OPEN until the crosswalk's `ruled` block reads zero unruled

Same shape as T-0990's: a cohort is a run, the run that finishes one names the next here
rather than opening a second ticket for it. The full reasoning per cohort is in
`data/research/land_sales/README.md`; this log is the ledger.

### DONE

**Cohort A — the twenty whose PERSON already carries a ruling under another spelling of
the same name.** Ruled 2026-09-11. **Nineteen upheld, one refused** — `ruled` 89/1/48/72 →
**108/1/49/52**; matched 162 → 161, entries carried 619 → 618, one card retracted
(`wright_truman_g`, lot 7 of block 5, $900). Acres are unchanged because a town lot has
none: the register prints `0000.00` in the acres column for every one of the 619.

| upheld | refused |
|---|---|
| BOTSFORD J K, CARPENTER P, EGAN W B, EGAN WILLIAM, FULLERTON A N, GOODHUE J C, HAMILTON R J, HUBBARD E K, HUBBARD GORDON S, KIMBERLY E S, KINZIE ROBERT, MARSH S, MERRILL G W, MULFORD J H, NEWBERRY W L, PRICE JERE, SHERMAN S W, TAYLOR E D, TEMPLE J T | WRIGHT T |

**What the cohort taught, in one line each** (the argument is in the domain README):

*The precedent is not the ruling.* Nineteen carry a token the fuller spelling also carried;
WRIGHT T carries none, and Fergus 1839 prints both Truman G. and Timothy Wright. Ask what
the token is before reaching for the precedent.

*The register's SEQUENCE is a check, and the June 1836 town sale hands it to you.* These
are lots entered block by block over ten days, so EGAN WILLIAM — no middle initial, and a
rival EGAN WILLIAM G in the same book — is decided by standing in block 45 on 25 June
between WILLIAM B's lots 5 and 7. The section deposits can rarely do this; a ring tract has
no neighbours in the book.

*The town's own paper can be the source of the mis-spelling.* The Democrat prints "Gordon
S. Hubbard" in the notice electing him a trustee, so HUBBARD GORDON S is not a second man.

*Three spellings the crosswalk does not propose are left open on purpose* — GOODHUE G J,
KIMBERLY EDWARD, NEWBERRY WALTER S. Each may be a misreading of a spelling already ruled
on, and a ruling can only be made on a proposal the crosswalk holds. The Newberry one is
noted on T-0396.

*The ceiling is not the measure of this ticket.* `measure_research_spend.py` anchors
rulings through `crosswalk.json` and cannot see `resident_crosswalk.json`, so twenty
judgements moved the meter by one and the ceiling came down 869 → 868. That is T-0962's
blind spot alive in this domain; the crosswalk's own `ruled` block is the number to read.

Filed on the way past: nothing. Every card the cohort touched was clean or already
carrying a ticket, and the one open question found (Walter S. Newberry) was added to
T-0396 rather than filed, per the queue's FILING RULE.

**Cohort B — the twenty-four remaining proposals with an empty `rivals[]`.** Ruled
2026-09-11. **Ten upheld, fourteen refused** — `ruled` 108/1/49/52 → **118/1/63/28**;
matched 161 → 147, **thirteen cards retracted** with twenty-three register rows and $45,319
of stated purchase money. Only **80 acres** move, the one quarter-section that came off
FAY H K: the other twenty-two rows are town or canal lots, and a town lot has no acreage.

| upheld | refused |
|---|---|
| FUNK ABSALOM, GARRETT A, GARRETT AUGUST, HEACOCK RUSSEL E, HEACOCK RUSSELL E, LOYD A, MCKEE DAVID, OGDEN WILLIAM B, SPRING GILES, WELLMAKER JOHN | CHURCH T JR, FAY HARRISON K, FINLEY CLEMENT A, KEYES EDWARD, MACK STEPHEN, MCGREGOR A, PEARSON HIRAM, ROBERTS E, ROBERTS EDMUND, RYAN THOMAS, SHEPHERD A, SHERWOOD S J, WILCOX DELAFAYETTE, WILSON JOHN S |

**What the cohort taught, in one line each** (the argument is in the domain README):

*T-0990's own cohort B had drawn this exact line, and it held without being bent.* Same
field, same question — does the town hold this man in anything more than a bare name? Ten
upholds each have a second document with something IN it; nine of the fourteen refusals have
one name-only reading and nothing else; four are cards the layer marks `letter_list_only`,
two of which T-0990 had already refused in another spelling.

*One line of one civic list is not enough, and it is not a rule against civic lists.* Seven
refusals rest on a single tax or poll line (the STANLEY JOSEPH shape). WELLMAKER JOHN is
UPHELD on civic lists — six readings across five domains, and a surname that appears exactly
once in all 6,849 identities, so there is no rival reading anywhere rather than none in a
thin layer. What each reading says decides it; how many there are does not.

*The sequence argument that carried cohort A cannot work here, by definition.* These
surnames appear once, so no reading of the same name stands on the block beside them.

*The register can be its own rival reading.* PEARSON HIRAM is refused because the same
volume enters PEARSONS HIRAM forty-four times, two of them town lots six days earlier in the
same sale, upheld to Hiram Pearsons — $22,410 off a card a surname fold away from him. Cohort
A's README named this one in advance.

*A middle initial can name the OTHER man.* SHERWOOD S J is the jeweler Smith J. Sherwood,
whom the corpus holds under his own name, and not the Stephen of the letter lists.

*The ceiling moved by one again, 868 → 867*, for cohort A's reason exactly: the meter cannot
see `resident_crosswalk.json`, so twenty-four judgements read as one. T-0962's blind spot,
second cohort running.

Filed on the way past, both from evidence read for this cohort: **T-1038**, the Norris 1844
jeweler line the identity layer has folded onto the letter-list Sherwood card; **T-1039**,
T-0885's row-is-not-a-parcel question asked of the town-lot volume, where four of twenty-four
purchasers turned up a lot entered twice or three times in paired and doubled prices. The
HEACOCK uphold was ADDED to **T-0884** rather than filed, per the queue's FILING RULE — it
settles the identity half of that ticket and leaves it the geometry.

**Cohort C1 — the nine with a namesake, surnames A–K.** Ruled 2026-09-11. **Six upheld,
three refused** — `ruled` 118/1/63/28 → **124/1/66/19**; matched 147 → 144, three cards
retracted with thirty-three register rows and $9,597 of stated purchase money, 25 of those
rows off one card. No acres move: all thirty-three are town lots.

| upheld | refused |
|---|---|
| BAILEY AMOS, GRANT JAMES, HUBBARD H G, HUGUNIN H, HUGUNIN HIRAM, KING TUTHILL | COBB L B, FOSTER AMOS, KINZIE JOHN |

**What the cohort taught, in one line each** (the argument is in the domain README):

*Ask the PRINTED record how many men the forename could be, not the layer.* `rivals[]` is the
layer's census of a surname and the layer is a reconstruction; the directories and the
newspaper run print six Baileys and one Amos, six Hugunins and one beginning H, thirteen Kings
and one Tuthill, eight Hubbards and one H. G. Seven of the nine turn on that count.

*An initial-only spelling is not automatically the BROWN WM shape.* HUGUNIN H survives two
questions: the initial is unique in the printed record of the surname, and the town itself
uses it for that man — 'H. HUGUNIN' chairs the town meeting of 20 May 1835 in the Democrat,
and the same run prints 'Capt. HIRAM HUGUNIN, Agent, Chicago' four weeks later.

*Two initials can be worth less than one.* COBB L B is refused because the rival carries the
same middle initial — S. B. Cobb, the saddler at the corner of Lake, printed over and over —
so only the forename letter separates them, and it is read once on each side and nowhere else.

*A card can look like three domains and be one reading.* FOSTER AMOS's two directory readings
are 'Foster, A. H.' folded on by *the given name of both begins A*. Strip the fold and no Amos
Foster is printed anywhere. Count a card's readings before counting its domains.

*The argument not taken is written down.* KINZIE JOHN would carry on chronology — the elder
died in 1828, the junior's printed age puts him at one year old in 1830 — but that is
elimination, not a token, and T-0501 already refused the identical string.

*The ceiling did not move at all*, third cohort running: `--tighten land_sales` answers
*nothing to reclaim* and 867 stands, because the meter cannot see `resident_crosswalk.json`.
T-0962's blind spot; read the crosswalk's own `ruled` block.

Filed on the way past: nothing new. The A. H. Foster fold was ADDED to **T-1035**, which owns
the one-shared-initial question. The 'J. GRANT, Jr.' caution is recorded in the GRANT JAMES
ruling rather than filed — it is a card-merge question, not a purchaser one.

**Cohort C2 — the nine with a namesake, surnames L–M.** Ruled 2026-09-11. **Three upheld,
six refused** — the first cohort here to refuse most of what it read. `ruled` 124/1/66/19 →
**127/1/72/10**; matched 144 → 138, six cards retracted with twenty-four register rows and
$30,708 of stated purchase money. No acres move: all twenty-four are town lots.

| upheld | refused |
|---|---|
| MONTGOMERY WILLIAM, MORRIS B S, MORRISON J M | LEE GEORGE W, LEE WILLIAM, LOOMIS H G, MILLER GEORGE, MILLER J, MILLER SAMUEL |

**What the cohort taught, in one line each** (the argument is in the domain README):

*Ask the REGISTER for a rival before you ask the town, and it answers four of the nine.*
LOOMIS H G is refused because the same book enters LOOMIS HORATIO G — one man, two
spellings — and MONTGOMERY WILLIAM and MORRISON J M are upheld because the book enters
LOTON WM, LOTON W, EZEKIEL, ORSEMUS, EPHRAIM and THOS M under their own names, so neither
proposal is a clipped reading of a purchaser it already holds.

*The printed record decides which man an initial pair names.* Chicago has exactly two
Loomises: Henry the lumber merchant, who carries no middle initial in any printing, and
Horatio Gates Loomis of Harmon & Loomis, printed 'Horatio G.' in Fergus 1839 and 'H. G.'
in Norris 1844 — the register's two initials exactly.

*A domain count is not evidence; the sentence the name stands in is.* MILLER SAMUEL's two
non-letter-list newspaper readings are one advertisement printed twice, and it closes 'Col.
Samuel Miller, Michigan City, are his Agents'. The Colonel is Carver's Indiana agent.

*A middle initial can DISAGREE rather than be absent.* LEE GEORGE W meets a card whose only
middle initial is the S of a St. Cyr 'G. S. Lee', against the register's W.

*C1's first lesson held under the hardest surname in the queue.* The printed record carries
twenty-five readings of MILLER and not one George; four distinct printed forenames begin
with J.

*The ceiling did not move, fourth cohort running* — `--tighten land_sales` answers *nothing
to reclaim* and 867 stands. T-0962's blind spot; read the crosswalk's own `ruled` block.

Filed on the way past: **T-1040**, carrying both card-level findings — the Michigan City
Colonel on `miller_samuel`, and `person_w_montgomery` holding Loton W.'s `boot and shoe
maker` beside the auctioneer's own trades. A ruling refuses a purchase and does not rewrite
a person, so neither was repaired here.

**Cohort C3 — the last ten, surnames S–Z.** Ruled 2026-09-12. **Eight upheld, two
refused** — `ruled` 127/1/72/10 → **135/1/74/0**, and that zero is what this ticket was
opened to reach. Matched 138 → 136, two cards retracted with four register rows and $7,175
of stated purchase money. No acres move: all four are town lots.

| upheld | refused |
|---|---|
| STEWART ROYAL, TAYLOR A D, TROWBRIDGE S G, WALKER G H, WALKER GEORGE H, WALKER JAMES, WILLIAMS ELI B, WOODWORTH J H | SMITH JAMES A, WRIGHT A |

**What the cohort taught, in one line each** (the argument is in the domain README):

*A crosswalk's recorded REFUSAL is evidence, not a gap.* WRIGHT A is refused because three
separate files already say, each in its own words, that the surname is in their volume and
no entry under it carries an A — Fergus 1843 weighing six Wrights, Norris 1844 two, the
Second Presbyterian roll eleven. Somebody looked, and wrote down that they looked.

*An initial-only reading cannot corroborate an initial-only purchase.* The one 'A. Wright'
in the corpus is a bidder in Fergus 1839's lot sale, folded on by the same letter A. That
is the proposal a second time, not a check on it.

*The printed man who carries the register's middle initial can be one the layer does not
hold apart.* SMITH JAMES A is refused with 'Smith, James Ayer, clerk' / 'Smith, J. A.'
sitting inside the very fold the card's 1843 and 1844 matches are recorded AMBIGUOUS on —
while the card's one unambiguous entry, Fergus 1839's constable, carries M.

*Say the fact that cuts the other way.* The 1840 census does print a head 'James A. Smith',
and the census crosswalk has already ruled it a CANDIDATE and no more. It is written into
the refusal so the next reader can overturn it if a token ever turns up.

*Two spellings of one man can be proved by the page rather than argued.* WALKER G H takes
lot 6 and WALKER GEORGE H lot 1 of block 37 on one day, and the town prints both forms —
'G. H. Walker' in a letter list, 'WALKER, GEORGE H' on Kercheval's Black Hawk muster roll.

*An office is a token.* WALKER JAMES, the oldest purchase in the domain (4 October 1830, the
canal commissioners' first sale), is upheld on the Democrat swearing an estray appraisal
'before James Walker, J. P.' — and the same notice prints Jeremiah Walker beside him, so
the page separates the layer's two Walkers itself. The ruling asserts no residence: Walker's
Grove is not the town.

*A `letter_list_only` card survives only when the list is not what carries it.* WOODWORTH
J H is upheld on Fergus 1839's firm line 'Woodworth, Robert P. & James H., wholesale dry
goods merchants, 103 Lake st', Fergus 1843's 'James Hutchinson, merchant', and the US House
biography — three documents past the list.

*The ceiling did not move, fifth cohort running.* `--tighten land_sales` answers *nothing to
reclaim* and 867 stands. Across all seventy-two judgements of this ticket the meter moved
twice, by one each time: T-0962's blind spot is now measured rather than suspected.

Filed on the way past: nothing. The one finding — Fergus 1839's compound firm entry
'Robert P. & James H. Woodworth' missing from the card's directory appearances, because a
man shares his printed line with his partner — is recorded in the ruling and the domain
README rather than opened, per the queue's FILING RULE.

### CLOSED, WITH THE COUNT

**Seventy-two proposals arrived when T-1033 joined the town lots to the reading, and
seventy-two are ruled: 46 upheld, 26 refused, across five cohorts.** The crosswalk's `ruled`
block reads **135 upheld, 1 named, 74 refused, 0 unruled**. This ticket closes on that
count, and not on 'there was nothing left'.
