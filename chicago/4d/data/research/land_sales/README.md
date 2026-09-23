# Federal land tract sales — the register of who bought the ground

**What lives here.** The Illinois State Archives' *Illinois Public Domain Land Tract
Sales* database, read for the two townships the town of Chicago and its north side
stand on — **T39N R14E** and **T40N R14E**, third principal meridian — and for the five
that ring them, for every sale dated on or before **31 December 1836**. **953 sales, 431
distinct purchasers as the register spelled them, 57,171.59 acres and $125,223.35 of
ground**, over 252 section queries. **Every one of those sections is read whole**: the
three T-0557 had to leave truncated at the search's 150-row page were walked to their
end through the results page's own More button, which is a cursor and not a dead end.
That is the second section below, and it is the correction that matters most here.

| the reading | townships | sales | purchasers | ticket |
|---|---|---|---|---|
| the town and its north side | T39N R14E, T40N R14E | 566 | 260 | T-0557, T-0675 |
| the ring | T39N R13E, T40N R13E, T38N R14E, T41N R14E, T38N R15E | 387 | 209 | T-0676 |

Each reading has its own deposit and its own records file, named after the townships it
holds, and the record ids run on across them — `ls0001` upward — because
`data/structures/*.json` cite them. **A new reading appends and never renumbers.**

**This is not a list of people, and that is the whole discipline of the domain.** The
register records a TRANSACTION. A man who entered eighty acres in T40N R14E in 1835
may have been standing on South Water Street, or in Vandalia, or in Connecticut; the
purchase says only that he bought. The one column that speaks to where he lived is
`Residence`, and it names a **county**, never a town:

| Residence as the register wrote it | sales |
|---|---|
| UNKNOWN | 485 |
| COOK | 36 |
| MACON | 16 |
| VERMILION | 11 |
| ILLINOIS | 9 |
| MCLEAN | 4 |
| LASALLE | 2 |
| IROQUOIS | 1 |
| VIRGINIA | 1 |
| ST. LOUIS | 1 |

The last two are the register's own words and are carried as it wrote them: neither
is an Illinois county, and this project does not correct a clerk.

So a row whose Residence reads COOK is graded `documented` — for residence in **Cook
County on the date of sale**, which in 1835 reaches far beyond the town — and every
other row is graded `inferred`, with the reasoning written on the record. Nothing here
mints a resident or regrades one. `resident_crosswalk.json` proposes correspondences
and states the rule that made each; T-0514 and T-0515 are what spend them.

**What the reading found.** Sales by year: 1830 · 17, 1831 · 8, 1832 · 3, 1833 · 337,
1834 · 95, 1835 · 101, 1836 · 4, and one row the register dates 1810, carried verbatim
because it is what the page says. By type: 205 federal cash entries (`FD`), 337 school
section sales (`SC`), 24 canal sales (`CN`). By what the tract resolves to: 217 town
lots, 167 half quarter-sections, 50 quarter-sections, 2 quarter-quarters and 130 the
parser leaves `unparsed` rather than guess at. The shape of that list is the school
section arriving: 1833 more than doubles, and the town lot passes the half
quarter-section as the commonest thing the register sells.

**The ring, and why it is worth having (T-0676).** T-0610 asked for the country around
the town and T-0675 read only the middle of it. The five ring townships are now read the
same way, section by section, cursor to the end: **387 sales, every one of them a federal
cash entry** — no school section, no canal land, because neither exists out there. They
are late and they are sudden: 1 sale in 1833, 38 in 1834, **318 in 1835** and 30 in the
first half of 1836. That is the land rush arriving, one year behind the town's own lots,
and 64 of the 180 sections carry it while 116 were walked and held nothing through 1836.
The register states a residence on 32 of the 387 — 22 COOK, and 10 spread over McLean,
Macon, Vermilion and Champaign — so the same grading rule applies out here as in town,
and 355 rows are `inferred`. Where the ground is: T38N R14E 152 sales, T39N R13E 145,
T40N R13E 57, T38N R15E 18, T41N R14E 15. **None of it is inside the town**, and none of
it resolves onto a footprint: the constructed section grid reaches only the four sections
that meet at State & Madison (L219), so every ring row says in `ground.json` why it does
not land.

**Nine more purchaser spellings meet a person the town already holds** — William Spencer,
Walter L. Newberry, James Whitlock, James B. Campbell, A. Garrett, John L. Wilson,
H. Pearsons, David P. Frame and Frank Dill. Two of them are the interesting ones: **Hiram
Pearsons enters seventeen ring tracts** and **Walter Newberry six**, both while the town's
own lots were being traded. **All nine have now been RULED ON** — six upheld, three refused
— which is the section below. T-0697 has since re-run the mechanical rule that made the
domain's counts, so the totals those nine sit inside are 136 matched spellings against 295
refused, not the 35 against 396 they were read under.

## The ruling layer (T-0700)

`build_resident_crosswalk()` PROPOSES; it does not decide. `tools/spend_land_sales.py`'s
own rule 1 — *"ONLY WHAT THE CROSSWALK ALREADY DECLARED. This pass re-adjudicates
nothing"* — means that between the mechanical rule and the card there was **nobody**, and
the ring's nine spellings reached thirty-one town cards that way. `resident_rulings.json`
is where a judgement is written instead. It is **hand-authored** — the one file under this
domain that is not derived from the deposit, because a judgement is not a derivation —
and `--build` folds it onto the crosswalk while `--check` validates it: a ruling must name
a spelling the register holds, rule on a proposal the mechanical rule actually made, agree
with that proposal about who is being ruled on, and state its ticket, its date, what it was
checked against, and its reasoning.

**The ruling rule.** A proposal is upheld only where the town's own record of the person
carries something the register's row can be checked against BEYOND a bare name — a middle
initial the register repeats, a trade the purchase is consistent with, a second document,
or the register's own Residence column. Where the town holds nothing but a name read once
off a post-office letter list, the proposal rests on the residents layer being THIN rather
than on the two records agreeing, and it is refused.

| spelling | ruling | what carried it |
|---|---|---|
| PEARSONS H | upheld | the same register spells him HIRAM on 28 other rows; 16 of the 17 H rows fall on one day in one township |
| NEWBERRY WALTER L | upheld | the middle initial agrees with Walter **Loomis** Newberry, attested in the American and both Fergus directories |
| WHITLOCK JAMES | upheld | the town's James Whitlock is **register of the land office** — the purchase is what his trade would predict |
| CAMPBELL JAMES B | upheld | the middle initial agrees, and nine sources hold him |
| FRAME DAVID P | upheld | the letter list printed "David P.Frame"; all three tokens agree |
| DILL FRANK | upheld | ls0912 states **COOK**, and the 1835 poll list has a Frank Dill at Chicago |
| SPENCER WILLIAM G | refused | one letter-list line, and a middle initial the town has never seen |
| WILSON JOHN L | refused | the same, on the commonest name in the corpus, and the entries are 1836 |
| GARRETT A ET CO | *retired* | refused by hand as a **firm**, and the refusal is now a derivation — see below |

Refusing the firm spelling left `GARRETT AUGUSTUS` standing alone on A. Garrett's card, where
the two spellings had both been written onto it. That second spelling is a reading in its own
name and is NOT ruled on here — it is one of T-0850's twenty-six, which the next section rules on (refused: the town has never read the forename).

## The register sells ground to FIRMS (T-0851)

A purchaser is not always a man. Twice on these 953 rows the register sets a partnership
style after the name — `GARRETT A ET CO`, eighty acres of section 33 in T38N R14E entered on
1 December 1835, and `PRUYNE P AND CO`, block 97 of the school section on 22 October 1833 —
and both of them were being read as people:

* `tools/namesake.py` drops the firm words so it can ask which man of a surname a reading
  points at. That is the right thing for that question and the wrong answer to a different
  one: `GARRETT A ET CO` folded to `A`, `A` named the town's A. Garrett, and a **house's**
  purchase was proposed as a **man's**.
* `PRUYNE P AND CO` was never refused at all. Peter Pruyne's card said the register enters
  *this person* six times, one of them as the firm, and counted the firm's 3.27 acres and
  $310 among his own. It now says five, 167.83 acres and $403.79.
* `normalize_name` read the firm words as forenames and title-cased them, so the deposit's
  own `normalized` field said **`A Et Co Garrett`** — a name of nothing.

**The rule, and it reads the page rather than a list.** `namesake.firm_style()` recognises a
partnership by the conjunction the register prints before its abbreviation for company —
`ET CO`, `AND CO`, `& CO`. The capacity words deliberately are NOT styles: `AS`, `AGENT`,
`TRUSTEE`, `HEIRS`, `OF`. A man buying as an agent or an heir is still a man and the register
names him; `BLANCHARD F G AS`, `VANDERBOGERT JOHN AS` and `WILLIAMS GILES AS` are people.

**Where the ground goes.** Every firm is refused against every person in `refusals[]` — the
count of adjudicated spellings stays whole — and the reading of it is carried in a new
`firm_purchasers[]` block of `resident_crosswalk.json`: what the house bought, when, where,
for how much, the register's Residence column, and the **one partner the page names**, put to
the same forename rule and carried at the same grade it would have earned. That proposal is
about the PARTNER'S NAME and not about a purchase by him. Who else stood in the house is not
on the page and nothing here proposes them.

The identification of `A. Garrett & Co.` with the town's A. Garrett — an auctioneer in four
numbers of the *American* and the *Democrat* — is probably right and is not what is refused.
What is refused is spending a partnership's entry as a person's.

`KNOWN_FIRMS` in `tools/read_land_sales.py` declares the two spellings, and `--check` **fails
on a firm the reading finds that is not declared**: a new deposit carrying one is meant to
stop the build, so somebody reads the rows before a purchaser goes onto no card at all.

A refusal is not free: it moves the proposal into `refusals[]`, and
`spend_land_sales.py --build` **retracts** the paragraph the earlier pass had written onto
the card. That retraction is the write made reversible, and it is held by a round-trip
assertion in `--self-test`.

**What ruling on them found.** The crosswalk read each purchaser's residence off the FIRST
row of that spelling. Frank Dill enters the same quarter-section twice on 10 April 1835 and
only the second row states COOK, so he was graded `inferred` against a source that places
him in Cook County; Hiram Pearsons was the same. The reading now takes every row of a
spelling, both grade `documented` — for Cook County on the date of sale and nothing more —
and a card whose paragraph no longer says what the crosswalk says is a gate failure, where
`gaps()` had only ever asked whether a paragraph was PRESENT.

## The first deposit's twenty-six, ruled (T-0850)

**Sixteen upheld, ten refused.** These are the purchaser spellings the town-and-north-side
reading (T-0557, T-0675) matched, ruled on the same rule and by the same file as the ring's
nine. What upholds one is a token the two records SHARE — a middle initial both print, a
trade the purchase is what you would predict from, the register's own Residence column, or
the town holding the man in two documents that bracket the entry date. What refuses one is
a bare name on each side, however unlikely the coincidence looks.

| spelling | ruling | what carried it, or did not |
|---|---|---|
| PEARSONS HIRAM | upheld | 28 rows, 1,157 acres, one stating COOK; the card's own trade is `speculator` |
| PRICE JEREMIAH | upheld | four documents beyond the register bracket the eleven entries of 1835 |
| ELSTON DANIEL | upheld | the Democrat of 1833 and Fergus 1839 hold him on both sides of the 1836 entry |
| WOLCOTT ALEXANDER | upheld | a canal entry of 29 Sept 1830, inside the town's own bound for the man, beside James Kinzie's of the day before |
| BRONSON ARTHUR | upheld | the town's 1833 tax list, the same year as the auction; FREDERIC(K) Bronson stands beside him, so the forename is doing the work |
| CARVER DAVID | upheld | the poll of 10 Aug 1833 and the tax list of 1833, two months before he buys |
| CASEY EDWARD W | upheld | the middle initial, printed by the register AND by the town's own rolls |
| CLYBOURNE ARCHIBALD | upheld | one Clybourne on either side; Andreas's trade and the town's rolls |
| COLE PARKER M | upheld | all three tokens agree — the letter list prints 'Parker M. Cole' |
| INGERSOLL CHESTER | upheld | the tavern at Wolf Point, in the paper weeks either side of the parcel |
| LLOYD ALEXANDER | upheld | two documents around the entry, and one Lloyd on either side |
| PRUYNE PETER | upheld | the forename in full, the trade attested, one Pruyne in the layer |
| PRUYNE P | upheld | the same register writes him PETER on four other rows — the PEARSONS H argument |
| STEELE ASHBEL | upheld | the polls of 1834 and 1835 print the same unusual forename |
| LUDBY JOHN | upheld | **the Residence column reads COOK** on three of four rows — the DILL FRANK carrier |
| WEST HENRY C | upheld | the letter list prints 'Henry c. West' — the middle initial is on both sides |
| HARTZELL THOMAS | refused | one tax line in 1833 against a canal entry of 1830; ILLINOIS is a state |
| VANDERBOGERT HENRY | refused | one tax line; the register holds a second Vanderbogert, and **T-0842** is asking whether the town's own two spellings are one man |
| WESSENCRAFT CHARLES | refused | one tax line; a unique surname makes coincidence unlikely, and unlikely is not checked |
| HALE JOHN | refused | **T-0885**: Ebenezer Hale enters every one of the same 26 parcels, and upholding would decide that open question by default |
| SPENCE JAMES | refused | the middle initial is on the town's side only, which tests nothing — the SPENCER WILLIAM G shape |
| CHANDLER JOSEPH | refused | one garbled letter-list return, six months after the entry |
| KINGSTON PAUL | refused | one letter-list return; the register also holds KINGSTON J T and JOHN T |
| MINARD IRA | refused | the closest call: a letter on 20 May 1835 and 161 acres on 27 June 1835, and a coincidence of date says when somebody bought, not who |
| PRUYNE P AND CO | refused | a FIRM, as GARRETT A ET CO was (T-0851) |
| GARRETT AUGUSTUS | refused | the town has never read this man's forename — the corpus prints 'A. Garrett', and an initial is less than the bare name the clause was written for. An auctioneer's trade is consistent with any land transaction, which is what makes it useless as a discriminator |

**What ruling on them moved.** The crosswalk goes from 136 matched spellings to **126**, and
from 295 refusals to **305**. Nine cards had a paragraph RETRACTED — Chandler, Garrett,
Hale, Hartzell, Kingston, Minard, Spence, Vanderbogert and Wessencraft — and Peter Pruyne's
now names two readings instead of three. The spend falls from 122 people to **113**, from
415 register entries carried to **362**, from 20,613.61 acres to **19,192.93**, and from
202 school-section parcels to **160**. No grade moved, here or anywhere: a ruling never
raises one and a refusal never lowers one.

**A. Garrett's card now carries no land purchase at all.** T-0700 refused the firm spelling
expecting `GARRETT AUGUSTUS` to stand alone on it; ruling on that spelling in turn finds
nothing to check it against, so both are refused and the honest state of the card is empty.
One printing of the forename in full would overturn it.

**The retraction learned to cut from the middle of a note (T-0850).** T-0700 built it to cut
the paragraph off the TAIL, which is where this pass appends. Joseph Chandler's card had the
1840 census written under his purchase, so the tail was somebody else's and the tool refused
the cut and said so. It now excises the span between the two literals that bound the
paragraph — the marker that opens it and the ladder sentence that closes it — and still
refuses where the closing literal is gone, because then where the paragraph ends is genuinely
unknown. `--self-test` holds both.

## T-0697's proposals, cohort A: the fourteen an initial decided among namesakes (T-0990)

Neither T-0700 nor T-0850 was written against the hundred-odd proposals **T-0697** added when
the mechanical rule stopped requiring exactly one person of the surname — both were written
against a crosswalk of 35 matches. **T-0990** rules them one cohort per run, and this is the
first: the fourteen whose match is `initial_agrees` AND whose `rivals[]` is not empty, which
is where the rule is at its weakest. The layer holds a namesake of the surname, and a
forename INITIAL alone chose between them.

**Eleven upheld, three refused.** What moved: matched spellings 126 → **123**, ruled 35 →
**49**, unruled 104 → **90**; three cards retracted, and with them six register rows — 230.78 acres and
$762.89 of ground taken back off them. Nothing was written on — the upheld eleven were already carried, and
upholding a proposal only confirms what the spend pass had put there.

**The discriminator was in `data/residents/directories.json` nearly every time, and it is
where the next cohort should look first.** Where the card holds an initial the later
directories very often print the forename whole, and that printing — not the initial — is
what decides:

| the register | the town's own printing | ruling |
|---|---|---|
| MONTGOMERY LOTON WM · MONTGOMERY LOTON W | Fergus 1843: *Montgomery, Loton W., shoemaker* | upheld |
| BLANCHARD F G · F G AS · FRANCIS G | Fergus 1843: *Blanchard, Francis Gurtrey, capitalist* | upheld |
| FOOT STAN | Fergus 1839/1843: *Foot, Star / Starr, teamster* | upheld |
| WRIGHT T G | Fergus 1839: *Wright, Truman G., speculator* | upheld |
| HADDOCK E H | Fergus 1839: *Haddock, Edward H., commission merchant* | upheld |
| BEAUBIEN J B | Andreas's 1833 roster: *J. B. Beaubien, merchant* | upheld |
| REED JAMES W | the Democrat, 31 Dec 1833: *J. W. REED.*, cabinet maker | upheld |
| HUNTER E E | the register's own duplicate ls0920, *HUNTER EDWARD E*, Residence COOK | upheld |
| GOODRICH CHAUNCEY | *nothing* — one line of the 1833 tax list | **refused** |
| SMITH LIMAN | *nothing* — one line of the poll of 1834 | **refused** |
| MORRISON THOS M | *nothing* — one uncalled-for letter, the Democrat of 20 May 1835 | **refused** |

Three of the fourteen have no directory line at all, and all three are the refusals. The
directories are read here **for the name and nothing else**: *teamster* is a trade of 1839
and *speculator* of 1839, and neither is written onto an 1835 card — T-0633 is the rule for
back-projecting a trade, and identifying a man is not back-projecting one.

**The register's second habit is worth as much.** It prints the same purchaser twice, once
abbreviated and once in full, and the fuller reading is sometimes a whole second row:
HADDOCK E H / HADDOCK EDWARD H, WRIGHT T G / WRIGHT TRUMAN G, and — decisively — HUNTER E E
(ls0919) and HUNTER EDWARD E (ls0920), the same 80 acres of section 13 T40N R13E on the same
day at the same price, with **COOK** in the Residence column of the fuller one and UNKNOWN in
the abbreviated one. SMITH LIMAN and SMITH SIMAN (ls0572, ls0573) are the same duplication
working against the proposal: the deposit itself cannot decide whether the man was a Lyman or
a Simon, so the token the rule matched on is not stable in the source that supplies it.

**A duplicate card found on the way past — and ruled (T-0993).** Fergus 1843's *Francis
Gurtrey* is one man, and the layer held both `blanchard_f_gantry` and `blanchard_gantry`.
T-0993 folded them, under a card-merge rule written for the shape, and named the six
`BLANCHARD GURTREY` rows onto the survivor. The section below is that ruling.

## The ruling the layer could not make: `named` (T-0993)

`upheld` and `refused` can only ADJUDICATE a proposal the mechanical rule made — confirm it,
or take it away. So a reading the rule structurally cannot reach had no way to be ruled on at
all, and `check_rulings` called a ruling on it *"a ruling on nothing"*.

**BLANCHARD GURTREY is that reading.** `namesake.choose` weighs the FIRST forename token, and
the register printed Francis Gurtrey Blanchard's MIDDLE name in the forename's place. Six
school-section rows — ls0076-ls0081, $547.00 of town lots on blocks 2, 3, 21, 82 and 141 —
were refused against every Blanchard the town holds, and no reading of any page could have
changed that.

**What names him.** Fergus 1843 prints *"Blanchard, Francis Gurtrey, capitalist, res 45
Wells"*, so GURTREY is his middle name and the card carries it as *Gantry* from the poll of
1834. And the register proves its own habit at ONE sale: the same school section — sec 16
T39N R14E, type SC, 22 and 24 October 1833 — is entered *BLANCHARD F G* in volume 818 page
010 (0376893-0376895) and *BLANCHARD GURTREY* in volume 817 page 027 (0367525-0367530). That
is the HUNTER E E / HUNTER EDWARD E habit above, one column further along the name.

**The kind, and its guards.** `ruling: "named"` GIVES a match instead of taking one away, and
`read_land_sales.py` holds it to the mirror of the same rules: only where the surname gathered
rivals and the forename failed to choose among them; only onto one of those rivals; never onto
a surname-only purchaser, which this domain refuses however well the tract agrees; and the
same reasoning, ticket and `checked_against` every other ruling owes. A `named_by_ruling`
match carries the refusal it overturned in `was_refused_as`, and it is the one match kept out
of the `namesake.collide` group — that rule asks whether several readings the MECHANICAL rule
named onto one person are one man, with the same forename test a `named` ruling exists because
it failed, and letting it run would have taken the three upheld F G rows down with the sixth.
Four assertions in `--self-test` hold all of it.

**What moved:** matched spellings 123 → **124**, ruled 49 → **50** (33 upheld, 1 named, 16
refused), and $547.00 of town ground reached the card it belongs on — $373.00 → **$920.00**
across ten rows.

**Still unruled: 90.** Cohort B is the twenty-four with no namesake at all (`rivals[]` empty),
cohort C the sixty-six remaining `forename_agrees` proposals that have one; the log on T-0990
carries them. The live count is on the crosswalk's `ruled` block and not repeated here.

## Cohort B: the twenty-four with no namesake at all (T-0990)

The mechanical rule fired on a surname the residents layer holds EXACTLY ONCE, which is
T-0700's and T-0850's original shape — `rivals[]` empty, no namesake for a forename to choose
among. That makes the proposals look safer than they are: holding one bearer of a surname is a
fact about how thin the layer is, and the register itself sells to a second Hurd and to three
Robertses while the town holds one of each.

**Twelve upheld, twelve refused** — the cohort splits exactly in half, and it splits along one
line. What moved: matched spellings 123 → **111**, ruled 49 → **71**, unruled 90 → **66**;
twelve cards retracted, and with them sixteen register rows — **1,549.24 acres and $2,084.04**
of ground taken back off them. Nothing was written on: upholding a proposal confirms what the
spend pass had already put there.

**THE LINE IS WHETHER THE TOWN HOLDS THE MAN MORE THAN ONCE.** Every one of the twelve upholds
has a second document on the town's side, and eleven of the twelve refusals have exactly one
name-only reading and nothing else. Cohort A's discriminator held again — nine of the twelve
upholds are decided by a directory printing the forename whole where the card carries an
initial:

| the register | the town's own printing | ruling |
|---|---|---|
| BOTSFORD JABEZ K | Fergus 1839: *Botsford, Jabez K., Botsford & Beers* | upheld |
| BOYER JOHN K | Fergus 1839: *Boyer, John K., coroner* | upheld |
| GOODHUE JOSIAH C | Fergus 1839: *Goodhue, Dr. Josiah C.* | upheld |
| KIMBALL WALTER | Fergus 1839: *Kimball, Walter, probate judge* | upheld |
| KNICKERBACKER ABRM V | Norris 1844: *Knickerbacker, A. V., grocery and provisions* | upheld |
| PECK P F W | Fergus 1843: *Peck, Philip Ferdinand Wheeler* | upheld |
| SHRIGLEY JOHN | Fergus 1839: *Shrigley, John, tavern keeper* | upheld |
| MARSH SYLVESTER | Fergus 1843: *Marsh, Sylvester, packing-house* | upheld |
| DOLE GEORGE W | Fergus 1843: *Dole, George Washington* | upheld |
| STANLEY JOSEPH | *nothing* — one line of the 1833 tax list | **refused** |
| BLAISDELL BENJAMIN | *nothing* — one line of the poll of 1835 | **refused** |
| SHEPHERD ALBERT · SACKETT JOSHUA · CHIPMAN ANSEL · ALLISON THOMAS · OSTRANDER CATHRINE · ROWLEY HEMAN A | *nothing* — one uncalled-for letter apiece | **refused** |

Six of the twelve refusals are cards the residents layer itself marks `letter_list_only`, which
turns out to be the SPENCER WILLIAM G test written as a field: the household around such a
person was minted to claim nothing, and an uncalled-for letter plus a tract entry is two
name-only readings.

**A MIDDLE INITIAL DISCRIMINATES; IT DOES NOT CORROBORATE — and this cohort is where that had
to be said.** Three proposals agree on a middle initial the register repeats, which the ruling
rule names as its first limb, and they do not all go the same way. **JAMISON LOUIS T** is
upheld: the town prints *L. T. Jamison* twice and independently, in the Democrat of 4 June 1834
and on the poll of 1835, so the initial pair decides among readings the town already holds.
**ROWLEY HEMAN A** and **HURD NIRAM F** are refused: there the initial pair IS the town's whole
record — one uncalled-for letter, one press line — and a fuller reading of one name beside a
shorter reading of the same name is still one name on each side. That is the NEWBERRY WALTER L
check of T-0700 read carefully: the L decided there because the American of 1835 and both Fergus
directories had already put the man in the town.

**The Residence column was weighed twice and carried neither.** CHIPMAN ANSEL and ALLISON
THOMAS both have **COOK** on the register's side, the strongest thing this source ever offers
and what upheld DILL FRANK and LUDBY JOHN. In those two the town's side was a poll list and a
newspaper naming the man in the town between his entries; here it is a letter nobody called
for. A COOK row and an uncalled-for letter agree about a county, not about a man.

**Two refusals turn on a token the register adds and the town cannot answer.** WILCOX DE LA
FAYETTE reduces as distinctive a forename as the cohort contains to the initial D — the town's
whole record is *Capt. D. Wilcox*, one press line, and the register's social-status column is
blank, so the captaincy checks against nothing. And **CHURCH THOS JR**: the JR is the page
saying there was another Thomas Church of the same county. The town holds one, its card is
written — in its own words — almost entirely to keep a building from being anonymous, and its
`present_on_scene_date` says nothing places him in the town on any particular date. That the
identification is probably right is not what is refused.

**A duplicate card found on the way past, and the reason the crosswalk could not see it.**
KIMBERLEY EDMUND S is upheld against `kimberley_ed` — the card's own press reading is *E. S.
Kimberley*, the Democrat of 1 July 1835, and the 1840 census reads *Ed. Kimberley*, so the S is
on the town's side and two documents bracket the scene date. But the layer ALSO holds
`kimberly_edmund_s`, **Dr Edmund Stoughton Kimberly**, printed *Kimberly, Dr. Edmund S.* in
Fergus 1839 — the same forename and the same middle initial, spelled with one letter fewer.
`tools/namesake.py` folds surnames exactly, so it never gathered him: **`rivals[] empty` means
no namesake OF THAT SPELLING, and this cohort is defined by that field.** Filed as **T-1001**.

**Still unruled after cohort B: 66** — cohort C, the `forename_agrees` proposals that have a
namesake, taken in three runs by surname block. The log on T-0990 carries them.

## Cohort C1: the seventeen with a namesake, surnames A-C (T-0990)

Cohort C is the other half of what T-0697 added: the mechanical rule fired on a surname the
layer holds SEVERAL of, and a forename agreeing in full chose among them. C1 is its first
block, surnames A to C, ruled by eye as well as by `namesake.py`.

**Eleven upheld, six refused.** What moved: matched spellings 112 → **106**, ruled 71 → **88**,
unruled 66 → **49**; five cards retracted, and with them nine register rows — **1,040.00 acres
and $1,608.00** of ground taken back off them. What stands: 23 rows, 1,125.71 acres and
$2,943.00. Nothing was written on; upholding a proposal confirms what the spend pass had
already put there.

| the register | the town's own record | ruling |
|---|---|---|
| ARCHER WILLIAM B | Chicago American, 4 July 1835, *William B. Archer*, + a Fergus death notice | upheld |
| BEAUBIEN MARK | the election of 1833 held at his house; Fergus 1839 *hotel-keeper, Lake st* | upheld |
| BROWN WILLIAM H | Democrat, 28 May 1834, *W. H. Brown*; Fergus 1839 *cashier, Branch State Bank*; the register's own **ILLINOIS** | upheld |
| CARPENTER PHILO | Fergus 1839 *druggist and apothecary*; by 1843 he has **Carpenter's Addition** | upheld |
| CHAPMAN CHARLES H | three ordinary press printings, 1833-34; Fergus 1839 *real estate dealer* | upheld |
| CLARK JOHN K | Chicago American, 11 July 1835, *John K. Clark*; the register's own **COOK** | upheld |
| COOK JOSIAH P | Norris 1844: *Cook, Josiah P. baker, res Michigan avenue* | upheld |
| COOK THOMAS | *teamster, Desplaines st* in 1839, 1843 AND 1844, + the tax list of 1833 | upheld |
| ANDREWS WILLIAM | Democrat, 25 June 1834, *Wm. Andrews*; Fergus 1839 *tailor, north side* | upheld |
| BOWEN ERASTUS | tax 1833, poll 1834, Calumet Club, Fergus 1839 *city collector* | upheld |
| BENNETT WILLIAM | the poll of 1834, + the register's own **COOK** | upheld |
| BROWN WM | *nothing the fuller spelling does not already carry* — and Fergus 1843 prints three William Browns | **refused** |
| ANDREWS DAVID · ALLEN WILLIAM · BLAKE LEVI · BURDICK PAUL | *nothing* — one uncalled-for letter apiece | **refused** |
| BALLARD THOMAS | *nothing* — one line of the poll of 1835 | **refused** |

**THE HABIT COHORT A FOUND HAS A LIMIT, AND C1 IS WHERE IT SHOWS.** The register does print one
purchaser twice, abbreviated and in full — HADDOCK E H / HADDOCK EDWARD H was cohort A's. But
**BROWN WILLIAM H is upheld and BROWN WM is refused**, on the same day and against the same
card. The fuller spelling carries a middle initial, a bank, two press readings and an ILLINOIS
in the Residence column; the barer one carries a forename so common that Fergus 1843 prints
*Brown, William, grocer*, *Brown, Wm., bds Sauganash* and *Brown, William Hubbard, cashier* as
three men. The layer holding one William Brown is thinness, not a town. **A spelling with no
middle initial is its own proposal and gets its own ruling.**

**THE SIBLING TEST IS THE CHEAPEST ONE IN THE COHORT.** ANDREWS WILLIAM upheld, ANDREWS DAVID
refused, same surname and same afternoon: one has a newspaper printing and a directory trade,
the other has a letter waiting at the post office and a research row whose `evidence_for` is
EMPTY. A `corroborated_enrichment` outcome with nothing written into it corroborates nothing.

**AND `letter_list_only` LIED ONCE.** Four of the six refusals are cards carrying that flag and
they went the way cohort B's six went. CHAPMAN CHARLES H carries it too and is UPHELD, because
three of its four `press_evidence` rows are ordinary printings with their own locators — the
Democrat of 26 November 1833, the American of 24 December 1833, the Democrat of 13 August 1834 —
and only one is a letter list. Read `press_evidence[].list`, not the flag. Seven cards are
flagged that way; filed as **T-1005**.

**A second card found on the way past.** Fergus 1843 prints two Erastus Bowens — the city
collector of *B. & Cole*, and *Erastus Selden Bowen [veterinary surgeon] [died Oct. 19, 1888,
a. 69]*, who was born about 1819 and was sixteen on the scene date. The layer's single card is
keyed `bowen_erastus_selden` and appears to hold the elder man's documents under the younger
man's name. The ruling is against the elder and says so; the conflation is **T-1004**.

**Still unruled after C1: 49** — cohort C2 (surnames D-J, 21 spellings) and C3 (K-Z, 28). C2
is ruled in the section below; C3 holds KIMBERLY EDMUND S, which is T-1001's man.

## Cohort C2: the twenty-one with a namesake, surnames D-J (T-0990)

C1's block was A to C; this is D to J, the same question — the mechanical rule fired on a
surname the layer holds several of, and a forename agreeing in full chose among them — and
the paired spellings the ticket flagged in advance were ruled together, as it asked.

**Sixteen upheld, five refused.** What moved: matched spellings 106 → **101**, ruled 89 →
**110**, unruled 49 → **28**; four cards retracted and one rewritten, and with them fourteen
register rows — **476.52 acres and $1,525.75** of ground taken back off them. What stands: 57
rows, 4,086.77 acres and $7,855.29, of which 2,428.28 acres are Elijah Kent Hubbard's alone.
Nothing was written on; upholding a proposal confirms what the spend pass had already put
there. The spend pass reports `people_written` 92 → 88 and `entries_carried` 337 → 323.

| the register | the town's own record | ruling |
|---|---|---|
| EGAN WILLIAM B | tax 1833 + poll 1834 print *William Bradshaw* whole; Fergus 1839 **real estate dealer**; Andreas has him building Egan's Row | upheld |
| HUBBARD ELIJAH K | Fergus 1839 *Elijah K., **banker**, 47-51 Dearborn st*; poll 1835; a death notice printing *Elijah Kent* | upheld |
| HUBBARD GURDON S | eight printings, 1834-44, incl. the trustee election of Aug 1834 and the 1840 census | upheld |
| HAMILTON RICHARD J | poll 1833, tax 1833, poll 1834; Fergus 1843 *Richard Jones*; clerk and recorder of Cook County | upheld |
| HADDOCK EDWARD H | the full spelling of cohort A's HADDOCK E H; Fergus 1839 *commission merchant, South Water st* | upheld |
| HUNTER EDWARD E | cohort A's HUNTER E E read with the Residence column; poll 1834 + the register's own **COOK** | upheld |
| HARMON ELIJAH D | Fergus 1839 *Dr. Elijah D.*, 1843 *Elijah Dewey, physician*; the register's own **COOK** | upheld |
| HARMON CHARLES L · HARMON CHAS L | poll 1834 *C. L.*; the 1837 return *Chas. L.*; Fergus 1843 both the card and the roll entry | upheld |
| HARMON ISAAC D | the card's own readings are all bare — Fergus 1839's *Isaac D., dry goods merchant, 8 Clark street* supplies the D | upheld |
| JONES BENJAMIN | street commissioner 7 Nov 1833, a fortnight after the sale; advertising 26 Nov 1833; Fergus 1839 *grocer, South Water* | upheld |
| JONES WILLARD | tax 1833, poll 1834, poll 1835 — and an uncommon forename where both records hold plain Williams | upheld |
| GOODRICH EBENEZER | Democrat, 13 Aug 1834: elected a **town trustee** beside Kinzie and Hubbard; poll 1834 | upheld |
| DAVIS GEORGE | *county clerk, 107-109 Lake st* in 1839, 1843 AND 1844, + poll 1834 and the 1840 census | upheld |
| FOOT JOHN | tax 1833 + poll 1835 bracket the sale; Fergus 1839 *blacksmith, Randolph street, near State* | upheld |
| HANDY HENRY S | his own signed notice, Democrat 18 Mar 1834: *H. S. HANDY*; a death notice, *Maj. Henry S.* | upheld |
| JONES WILLIAM | *nothing the surname does not give away* — Fergus 1843 prints three William Joneses, and the 1839 line is `contested` with Willard | **refused** |
| DAVIS JOHN | the card asserts a **hotel keeper**; all three directories print *Davis, John, tailor* | **refused** |
| HARMON ISAAC | *nothing the fuller spelling does not already carry* — and Fergus 1843 prints a second Isaac Harmon | **refused** |
| JACKSON SAMUEL | `letter_list_only`, one return — and Fergus 1843 prints *Samuel Thomas* AND *Samuel Ezra* | **refused** |
| HALL GEORGE | *nothing* — one repudiated fifty-dollar note, and the advertiser's own name is cut off at the crop | **refused** |

**C1's BROWN WM RULE DID THE MOST WORK OF ANY LESSON CARRIED FORWARD, AND IT FIRED TWICE.**
HARMON ISAAC D is upheld and HARMON ISAAC refused, two days apart on the same card; JONES
WILLARD is upheld and JONES WILLIAM refused, on the same two afternoons of October 1833. Both
times the barer spelling failed for the same reason Brown's did: the town's own PRINTED record
holds a second man of that name — *Harmon, Isaac Newton, with C. L. Harmon* in Fergus 1843,
three William Joneses in the same volume — and the layer holds one only because the layer is
thin. **HARMON CHAS L is the control**: it is a contraction, not a barer spelling, it carries
the middle initial, and it is upheld beside HARMON CHARLES L without argument.

**THE STRONGEST UPHOLD IN THE COHORT IS THE ONE WHERE THE TRADE PREDICTS THE PURCHASE.** Fergus
1839 calls William B. Egan a *real estate dealer* and Elijah K. Hubbard a *banker*; the register
enters the first for 720 acres over four months and the second for 2,428 acres in two afternoons
of the June 1835 ring. That is the PEARSONS reasoning — a speculator buying half of what he can
reach in an afternoon is the man the town already holds, not a stranger who shares the county
and the week — and it is the arm the rule names second.

**A REFUSAL CAN COME OFF THE CARD'S OWN NOTE.** DAVIS JOHN needed no outside argument: the card
already says it, *"a 'Mr. Davis' also took over the Sauganash Hotel in 1835, and whether that is
this man is unknown … if it is not, there is a second Davis in the town."* A card that refuses
to resolve its own identity cannot be the town-side half of a bare-name match.

**AND `letter_list_only` TOLD THE TRUTH ONCE MORE.** JACKSON SAMUEL is the cohort's only card
carrying the flag, C1's test was applied to it — read `press_evidence[].list`, not the flag —
and the flag was right: one return of uncalled-for letters, the Democrat of 22 October 1834, and
nothing else in the corpus. The county history's harbour foreman arriving from Buffalo in June
1833 is an enrichment with real content, which is more than C1's ANDREWS DAVID had, and it still
does not check a row: it predicts no purchase, and the directories print two Samuel Jacksons
with middle names the register does not have.

**Still unruled: 28** — cohort C3, surnames K-Z. The log on T-0990 carries it, and it holds
KIMBERLY EDMUND S, which is T-1001's man.

## Cohort C3: the twenty-eight remaining, surnames K-Z (T-0990) — and the last of them

The block T-0697 opened closes here. **Seventeen upheld, eleven refused.** What moved:
matched spellings 101 → **90**, ruled 110 → **138**, unruled 28 → **0**. Ten cards were
retracted and with them twenty-one register rows — **1,214.64 acres and $3,631.08** of
ground taken back off them — against 45 rows, 2,031.01 acres and $7,069.69 that stand. The
spend pass reports `people_written` 88 → **78**, `households_touched` 85 → **76**,
`entries_carried` 323 → **302** and `acres_carried` 15,896.39 → **14,681.75**.

| the register | the town's own record | ruling |
|---|---|---|
| KINZIE ROBERT A | **the tract IS the story**: ls0059 is the north fractional half of section 10, the ground Butler's letter says Kinzie offered Bronson | upheld |
| TEMPLE JOHN T | poll 1833, tax 1833, poll 1834 bracket eight blocks bought eleven weeks after he arrived; Fergus 1843 *John Taylor, physician* | upheld |
| OWEN THOMAS J V | two middle initials, four Democrat printings, the town's **first president** buying at the town's own sale | upheld |
| SNOW GEORGE W | the town's **Assessor and Surveyor** from 4 Dec 1833, buying at the school-section sale six weeks before; Fergus 1843 *George Washington* | upheld |
| SHERMAN SILAS W | Democrat *Silas W.* on both sides of the row; Fergus 1843 *Silas Wooster*, **sheriff of Cook County** 1834 | upheld |
| SWEET ALANSON | Andreas *Alanson Sweet, 1832*, builder of the first Tremont; tax 1833 + polls 1834 and 1835 | upheld |
| WRIGHT TRUMAN G | Fergus 1839 *Truman G., **speculator**, bds Tremont House* — the EGAN reasoning; cohort A's WRIGHT T G is its twin | upheld |
| NOBLE JOHN | Fergus 1839 *John Noble, **real estate**, res. Dutchman's Point* and 320 acres in the townships between | upheld |
| TAYLOR EDMUND D | the Democrat brackets the ring day, 25 Mar and 8 Jul 1835; Fergus 1839 *Col. Edmund D., Taylor, Breese Co.* | upheld |
| KIMBERLY EDMUND S | Fergus 1843 *Edmund Stoughten, physician*; clerk of the incorporation meeting; T-1001 already merged its sister spelling here | upheld |
| MULFORD JAMES H | Fergus 1839 *James H. & Edward H. jr., jewelers* — the line names the card's only namesake | upheld |
| KINZIE JAMES | the register's own **ILLINOIS**, with Andreas's residents list and the 1833 election as its partner | upheld |
| SMITH JEREMIAH | the register's own **COOK** twice, with the 1832 muster and the Democrat printing *Jeremiah* in full | upheld |
| MERRILL GEO W · MERRILL GEORGE W | the **W** is what separates him from the *Merrill, George, clerk* printed four lines away in 1839 | upheld |
| TAYLOR ANSON H | Fergus 1839's only Anson, *Anson H., general supply store, near the Garrison*; Andreas's bridge-builder | upheld |
| REED THOMAS | Fergus 1839 *Thomas Reed, **teamster**, 115 Lake street* — a trade AND a street; poll 1835 | upheld |
| TAYLOR CHARLES | the card is *Charles **H.***, the register is bare, and 1839, 1843 and 1844 each print **two** Charles Taylors | **refused** |
| MURPHY JOHN | *nothing the surname does not give away* — Fergus 1843 and Norris 1844 each print a John Murphy hotel keeper AND a John Murphy labourer | **refused** |
| SMITH GEORGE | a coffee-house keeper against **three printed George Smiths**, one of them the LaSalle Street banking house | **refused** |
| WENTWORTH ELIJAH · WENTWORTH ELIJAH W | the **register itself** sells to ELIJAH, ELIJAH SEN, ELIJAH W and ELIJAM SEN; the layer holds one | **refused** |
| KING NEHEMIAH | one printing of the forename in full; every other reading is *N. King*, and Fergus 1839 prints *King, **Nathaniel**, clerk, Tuthill King* | **refused** |
| THOMPSON JOHN L | the register's **L** belongs to `thompson_lieut_j_l`, not to the bare *John Thompson* it was matched to; `letter_list_only` and true | **refused** |
| TUCKER ALEXANDER H | one return of letters, read as *'fucker, Alexr. H. ot* — the initial pair IS the town's whole record | **refused** |
| RUSSELL SAMUEL | three whole blocks for $1,205 against a **G3 projected resident** documented once, on the tax list | **refused** |
| SKINNER JOSEPH | the tax list of 1833 and one uncalled-for letter, neither saying anything but the name | **refused** |
| KERCHEVAL BENJAMIN | a canal row of **1830**, five years before the tax list that is the card's whole record | **refused** |

**THE REGISTER CAN PROVE THE SECOND MAN ITSELF, AND THAT IS WHAT C3 ADDS TO THE BROWN RULE.**
C1 and C2 refused BROWN WM, JONES WILLIAM, HARMON ISAAC and TAYLOR CHARLES because the town's
own PRINTED record held a second man of the name. WENTWORTH needed no directory at all: the
tract register sells to **WENTWORTH ELIJAH, WENTWORTH ELIJAH SEN, WENTWORTH ELIJAH W and
WENTWORTH ELIJAM SEN**, and a source that writes *Sen* has told you there are two. A card that
can meet none of the register's own distinctions cannot be handed a row the register took the
trouble to distinguish. The honest reading of a surname like that is that the LAYER IS MISSING
MEN, not that one card owns them all.

**A SECOND DOCUMENT MUST SAY SOMETHING, NOT MERELY REPEAT THE NAME.** Cohort B's operative
line was whether the town holds the man more than once, and C3 is where counting to two stops
being enough. SKINNER JOSEPH is held twice — the tax list of 1833 and an uncalled-for letter of
April 1834 — and neither reading prints a trade, a street, an office or a middle initial, and no
directory of 1839, 1843 or 1844 prints a Joseph Skinner at all. REED THOMAS is held three times
and one of them is *Reed, Thomas, teamster, 115 Lake street*. That difference, and not the
count, is the line: the rule asks what the register's row can be CHECKED against, and two bare
names cannot check a third. It is the cohort's closest call and it is marked so on the ruling.

**THE COMMONEST SURNAME IN THE TOWN SPLIT, WHICH IS THE RULE WORKING RATHER THAN FAILING.**
SMITH GEORGE is refused and SMITH JEREMIAH upheld, both entered on 27 June 1835. Three George
Smiths are printed in this corpus and no volume prints a Jeremiah; the register, which sells to
eleven spellings of the surname, sells to one JEREMIAH and states **COOK** on two of his four
rows. A common surname is not what refuses a proposal — a second printed claimant is.

**AND THE MECHANICAL RULE CAN MATCH A MIDDLE INITIAL ONTO A CARD THAT HAS NONE WHILE A RIVAL
CARRIES IT.** THOMPSON JOHN L was proposed onto `thompson_john`, which holds no middle initial
at all, while the layer holds `thompson_lieut_j_l`. The forename rule looked at the forename and
could not see that the discriminating token already had an owner. Filed as **T-1016**.

Filed on the way past: **T-1014**, the N. King readings on `king_nehemiah` that the directory
gives to Nathaniel; **T-1015**, the *Anson W. Taylor* reading on `taylor_anson_h`; **T-1016**,
the Thompson initial above; **T-1017**, whether buying at the town's OWN school-section sale is
itself a check on a town-side name — the question SKINNER JOSEPH and RUSSELL SAMUEL both turn
on, filed rather than decided because answering it would reopen rulings already made.

**A FIFTH DERIVED FILE MOVES BEHIND A REFUSAL.** C2 named `export_resident_audit.py --build`,
`compile_scene.py --all` and `consolidate_resident_evidence.py --build`; a retraction also moves
`data/research/residents/town_card_candidates.json`, so `tools/consolidate_town_cards.py --apply`
belongs in the same pass. The gate reports them one failing step at a time.

**Nothing is left unruled.** `resident_crosswalk.json` → `ruled` reads
`upheld 89, named 1, refused 48, unruled 0`. Every proposal T-0697 added when the surname rule
widened has been adjudicated by hand, and T-0990 closes on that number rather than on an
absence.

## Forty rulings were reverted, and restored (#1073, T-1000)

**For part of 10 September 2026 this file's rulings block held eight entries and its own
prose described forty-eight.** The merge lap pushed onto #1055 — T-0851, the firm rule —
and `resident_rulings.json` conflicted there. It is hand-authored, and the lap's regex
resolution took the branch's whole block for the second conflict; that branch had been
cut before T-0850 and T-0990 cohort A ruled, so all twenty-six of T-0850's rulings and
all fourteen of cohort A's left the file on one line. #1055's own prose survived, and
went on describing the cohort A rulings the same commit had removed. **A file that
describes forty judgements it does not contain** is what the next run noticed, reading
T-0990's cohort log for the remaining count and finding the crosswalk disagreed with it.

| | before | reverted | restored |
|---|---|---|---|
| entries in `resident_rulings.json` | 49 | 8 + 1 retired | **47** + 2 retired |
| crosswalk `ruled.upheld` | 33 | 6 | **33** |
| crosswalk `ruled.refused` | 16 | 2 | **14** |
| crosswalk `ruled.unruled` | 90 | 129 | **90** |
| matched spellings | 123 | 135 | **123** |

**The loss was not inert, which is the thing to take from this.** A refusal RETRACTS the
paragraph `spend_land_sales.py` wrote, so refusals going missing put the purchases back
onto the cards that had adjudicated them away — Thomas Hartzell, Henry Vanderbogert,
Charles Wessencraft, John Hale, James Spence, Joseph Chandler, Paul Kingston, Ira Minard,
Augustus Garrett, Chauncey Goodrich, Liman Smith and Thos M. Morrison — twelve cards,
each carrying a federal land entry and an `isa_public_domain_land_tract_sales` source
line it had been ruled it could not have. Restoring the rulings and re-running the spend
takes them back off: **twelve records retracted, nothing written on**, and matched
spellings back down 135 → 123, a refusal being what removes a match.

**Every entry is restored as its own ticket wrote it** — the same `ruled_on`, `ticket`,
`checked_against` and reasoning — because a judgement re-argued is a different judgement.
**One is retired rather than kept.** `PRUYNE P AND CO` was T-0850's, refused for being a
partnership; T-0851 then made that a DERIVATION — `namesake.py`'s `firm_style()` refuses
every firm against every person before a surname is gathered — so the crosswalk proposes
nothing for the spelling and `--check` rightly calls a hand ruling on it a ruling on
nothing. #1055 retired its twin `GARRETT A ET CO` in exactly this way, and that
retirement note **names this spelling** as the second firm the rule caught; it could not
retire the entry because its base did not hold it. So the retirement is finished under
T-0851's date and ticket, with the argument kept rather than deleted: it is half of what
the rule was written from.

**Nothing in the gate could see it, and that is still true.** `read_land_sales.py
--check` asserts a ruling is WELL FORMED — that it names a spelling the register holds
and a person the proposal named. It has no opinion about a ruling that is simply GONE,
because a smaller rulings file is a legal rulings file, and the eight-ruling file
re-derived perfectly into a crosswalk perfectly consistent with it. `check.sh` was green
on #1055 and on every commit after it. The count is the only thing that can be watched
here and nothing watches it; T-0999 is that gate.

**Something watches it now (T-1124, the first half of T-0999).** `check.sh` runs
`tools/check_rulings_not_lost.py`, which asks the one question every step above is
structurally unable to ask — *is a judgement simply GONE?* — and it asks it of the MERGE
BASE rather than of anything this tree carries, because a branch that dropped forty
entries and edited a total downwards in the same commit would satisfy any self-consistent
check. Two readings of "still here", both required: by IDENTITY, every
`(purchaser_as_read, resident_id)` adjudicated at the base is adjudicated at HEAD — the
strong one, which catches a swap that never moves the total — and by COUNT, which is the
number a person reads and the one this incident is remembered by, 49 → 9.

`ruled[]` and `retired[]` are counted TOGETHER, so retiring a ruling the way `PRUYNE P AND
CO` was retired above is a MOVE and not a loss.

**How to remove a ruling, since removing one is still possible.** A judgement that should
never have been made does not get deleted. It moves into a third array, `withdrawn[]`,
which is counted alongside the other two and whose entries must carry a `reason` and the
`ticket` that decided it — the same trade `retired[]` already makes, and the same one the
liberty ledger makes. The total therefore never falls, and the record of what left says
why. A `withdrawn[]` entry with no reason written is refused by the gate as a deletion
wearing a label. The array does not exist in the file yet and does not need to: nothing
has been withdrawn.

The second half of T-0999 — the same guard over the rest of the hand-authored evidence in
`data/research/`, which needs a reading of what a judgement is in each file before a count
over it means anything — is T-1125, and it landed. The registry now holds **six** files and
**708** judgements: this one, the trade-census spend rulings, the newspapers' trade-class
and place rulings, Fergus 1839's lot corrections, and `data/residents/card_merge_rulings.json`.
Five more files were REFUSED entry with the reason recorded in the tool's `REFUSED` table —
four of them because they are DERIVED, and a floor under a derivation's count is a gate that
fires the moment the generator legitimately derives less.

## Two things about the source, both learned the hard way

**The search shows at most 150 rows at a time — and it pages.** A whole-township query
stops at 150 and looks complete: the first attempt at this read came back with exactly
150 rows for each township and would have recorded a ceiling as a town. So the reading
is BY SECTION, thirty-six queries per township. That much T-0557 got right. What it got
wrong is the ceiling itself. **The results page carries a `More` button**, and that
button is a keyset cursor — `hiddenPurchaseNo` + `hiddenPurchaser` + `hiddenSectionNo`,
replayed against the same search, return the rows after the last one shown. Results are
ordered by purchaser, so replaying the cursor walks a section to its end.
`harvest_land_sales.py --sweep` follows it and prints how many pages each section took.

T-0557 read the three sections that filled their first page — T39N R14E 16, 21 and 29,
the school section and two of the West Division sections — as truncated, and declared
them unread. T-0675 walked them: **section 16 is 3 pages and 337 sales, all of them the
October 1833 school-section auction; section 21 is 6 pages and 781 rows, 4 of them
through 1836; section 29 is 2 pages and 217 rows, again 4 through 1836.** So the hole
was 191 sales wide and it is closed, and every section of both townships is now declared
read. The lesson is worth keeping over the numbers: **a page that fills is a page, not a
limit** — look for the cursor before recording a refusal.

The `name` field still cannot be used to break a section up: it belongs to the
database's other search form and does not narrow a legal-description query, it replaces
it, returning that name from every township in Illinois. It DOES combine with the county
select, which is a different way through the same ceiling and was not needed once the
cursor was found.

**The site refuses datacentre addresses.** Every user agent tried from this project's
runner gets a bare 403 from the WAF — the session that filed T-0557 hit the same wall
through its proxy. The pages were therefore fetched through the public `r.jina.ai`
reader, which returns the origin's own HTML unchanged; `harvest_land_sales.py --direct`
asks the origin instead, for anyone running it from a machine the site will talk to.
The route is recorded in the source record. It changes nothing about what the page says,
and the reading cross-checks itself: for all 375 sales the summary row and the detail
page agree, field for field, on purchaser, tract, section, township, range, meridian,
county and date.

## What is NOT read, and is not a fault

- **Nothing of what T-0610 asked for.** The two townships the town stands on and the
  five that ring them are all read whole, section by section, cursor to the end.
- **Sales to purchasers whose stated residence is Chicago or Cook County outside these
  townships.** The database's name search cannot be filtered by residence, so this
  needs a different shape of query.
- **The canal sections.** ~~They were sold by the canal commissioners, not the land
  office, and are not in this database at all — their absence is not a hole.~~
  **That was wrong, and T-0830 is what caught it.** The database carries canal sales
  under its own type code `CN`, twenty-four of them are already in this deposit, and
  the town-lot sales the next section counts are `CN` too. What is true is narrower:
  the canal land the sweep reached is the alternate SECTIONS, because those are the
  only canal rows a section query can see.
**Done, 2026-09-04 (T-0609):** the join from a tract to a standing structure.
`tools/resolve_land_tracts.py` puts every sale on the ground or says why it cannot,
writes the result to `ground.json`, and puts a `land_owner` block on the 63 structures
the resolved tracts reach. See the next section.

## The sweep is complete for every section it declares, and blind to a row with no section (T-0830)

The lead was one line of the Dalton Data Bank, read by T-0497: *George Dalton, price
$1055, 6/25/1836*, under COOK COUNTY, sourced to the Illinois Archives. The date falls
inside the window this domain declares it read, and no Dalton was in it. The reading
above said that was a purchase outside the seven townships and not a hole. **It is not
outside them, and it is a hole — of a shape the by-section reading could not have
found.**

**The five purchases, at the register's own detail pages.** Every field below is the
database's own, and the prices match the Dalton Data Bank's line exactly.

| purchase no | tract as written | date | total price | type | vol/page | residence |
|---|---|---|---|---|---|---|
| 0363249 | `L2BL46CHIOT` | 25/06/1836 | $1,055.00 | CN | L5A 017 | UNKNOWN |
| 0363250 | `E2E2L1B46CHI` | 25/06/1836 | $343.75 | CN | L5A 016 | UNKNOWN |
| 0515062 | `W2L1BL46CHIV` | 25/06/1836 | $687.50 | CN | L5A 016 | UNKNOWN |
| 0515063 | `L1B46CHIOTV` | 25/06/1836 | $343.75 | CN | L5A 016 | UNKNOWN |
| 0379985 | `L5BL50CHIOT` | 27/06/1836 | $875.00 | CN | L5A 019 | UNKNOWN |

**They cannot be placed in a section, because the register gives them none.** Section,
Township, Range and Meridian are all EMPTY on every one of the five, on the list page
and on the detail page alike. The tract is a lot and a block in a platted town and the
register writes a town code — `CHIOT`, `CHI`, `CHIV` — where a legal description would
go. **This project does not expand those codes**; they are the Archives' abbreviations
and the Archives' own key for them is not reachable from this runner, so they are
carried exactly as printed. What follows does not depend on expanding them.

**Why no amount of sweeping would have found them.** `harvest_land_sales.py --sweep`
asks the search for a section. A row with no section answers no section query, ever. So
the sweep's completeness could not be measured from inside the sweep.

**The query that could measure it (`--county-list`).** County alone, no township and no
section, walked to its end through the same More cursor — 83 pages, 12,444 rows, of
which **2,785 are dated on or before 31 December 1836**. That walk is committed as
`text/isa_land_tract_sales_cook_county_list_through_1836.tsv` (the results page's nine
columns, nothing added) and `coverage.json § completeness_probe` derives the measurement
from it. The 2,785 fall into three groups and the answer differs for each:

| | rows | in the deposit | what it means |
|---|---|---|---|
| inside the seven declared townships | 953 | **953** | the by-section sweep is read whole — **nothing is missing** |
| sectioned, outside the seven | 1,213 | 0 | outside what the deposits declare; not a hole in them |
| **no section at all** | **619** | **0** | no section query can return these |

So **both halves of the answer are worth having**. The declaration this domain has been
making is exactly true: an independent whole-county walk finds all 953 of its rows and
not one more. And the domain is not the whole of 1836 Cook County: 619 sales are missing
and 466 of them are dated 1836 — the town's own lots, changing hands in the year the
land rush reached the plat. 618 carry a town code and one is a bare `L6BL17`.

**Nothing here mints, grades or moves a resident.** George Dalton's residence reads
UNKNOWN on all five rows; a purchase is a transaction and never a home, which is this
domain's first discipline. **T-1028 split into T-1032, which harvested the 619 (the next
section), and T-1033, which will read them into records.**

## The 619 read: the town's own lots, harvested and not yet joined (T-1032)

T-0830 above COUNTED the 619 and could say nothing else about them, because a list page
prints nine columns and a sale has sixteen. **All 619 are now read at their detail
pages** — one fetch per row, `harvest_land_sales.py --town-lots COOK`, committed as
`text/isa_land_tract_sales_cook_town_lots_through_1836.tsv` in the sweep's own sixteen
columns so that reading them later needs no second shape.

**They are one thing, and the register says so on every row.** All 619 are canal sales
(`CN`), all 619 are in volume `L5A` across thirty of its pages, all 619 give Residence as
UNKNOWN, and **none carries any acreage at all** — 0000.00 acres at 000.00 an acre, with
only the total price filled in. That is what selling a platted lot looks like in a
register built for quarter-sections: there is no aliquot to state and no acreage to
price, so the columns that would carry them stand empty and the tract field carries a lot
and a block instead.

| | rows | total price |
|---|---|---|
| 1836 | 466 | $1,390,763.33 |
| 1830 | 133 | $4,553.00 |
| 1831 | 16 | $0.00 |
| the register's own mis-prints — 1000 ×3, 1483 ×1 | 4 | $3,750.00 |
| **all** | **619** | **$1,399,066.33** |

**That last figure is the reason the ticket was worth its half hour.** The whole
by-section deposit above — 953 sales, 57,171 acres, seven townships — is $125,223.35 of
ground. These 619 town lots are **eleven times that**, and the 466 rows of 1836 are all
but $8,303 of them.
The 1836 rows are also a fortnight: **447 of the 466 fall between 20 and 30 June**, with
64 sold on the 28th, 62 on the 25th and 60 on the 24th. Only 19 of the year's rows are
dated after June at all. **The canal land sale of June 1836 is in this file, day by
day** — including four rows the clerk dated `6/22/1836` without the leading zero, carried
exactly as printed.

**Who bought.** 255 distinct purchaser spellings, and the register's own spelling of
each. The ten busiest are EGAN WILLIAM B (35 lots), FOSTER AMOS (25), COOK CNTY COM (24),
PECK P F W (15), JONES WILLIAM (14), KINZIE JAMES (12), GRANT JAMES (11), HUBBARD H G
(10), BEAUBIEN J B (9) and GOODHUE J C (9). **None of them is a resident yet and none is
graded here** — a purchase is a transaction, which is this domain's first discipline, and
133 of these rows are 1830 sales to men who may never have stood on the lot.

**The shape of the tract field, because T-1033 has to parse it.** 616 of the 619 are a
lot and a block; 57 distinct blocks, numbered 1 to 58.

| form | rows | example |
|---|---|---|
| `L<lot>BL<block><town>` | 517 | `L4BL36CHIOT` |
| `L<lot>B<block><town>` — the same thing, one letter shorter | 53 | `L2B17CHIOT` |
| a half or quarter OF a lot, either spelling | 46 | `W2L3B34CHIOT`, `E2E2L1B46CHI` |
| the parser will have to refuse | 3 | `L5BLCHIV`, `L1013CHIOT`, `SEL1B28CHIOT` |

The town codes are `CHIOT` 334, `CHIOTV` 107, `CHIV` 92, `CHI` 62, `CHIOTVO` 20 and one
row with none. **This project still does not expand them** (T-0830's rule, unchanged) —
and note the trap in the last: `CHIOTVO` ends in `VO`, which is the register's mark for a
VOID sale elsewhere in this domain, and `tract()` currently reads a trailing `VO` as void.
Whether those twenty are void sales or a fifth town code is a question for T-1033 and is
NOT answered here.

**Nothing downstream had moved when this was written, and T-1033 moved it — the
next section is the join.** The file was deliberately not in `DEPOSITS`: a deposit
mints record ids, proposes a resident crosswalk and puts firms in front of the ruling
layer, and none of that can be done honestly while `tract()` has no way to say what
ground `L2BL46CHIOT` is. So `entries.json`, `ground.json`, `crosswalk.json` and every
card are untouched by this reading, and `coverage.json § completeness_probe` still reads
`complete_for_1836_cook_county: false`. **T-1033 is the reading.**

**What the gate does hold it to.** `read_land_sales.py --check` re-checks the harvest
against the probe it was drawn from, every run: the same 619 purchase numbers the county
list called sectionless, no more and no fewer; the purchaser, date and legal description
the list page printed, unchanged by the detail page; and Section, Township, Range and
Meridian still empty on every row. All three agreed on all 619 on the day it was
harvested. Five self-test assertions prove that check still fires when broken.

## The 619 joined: a tract that is a lot and a block, and the plat it refuses to name (T-1033)

The section above harvested the 619 and stopped at the join, for one reason stated plainly:
`tract()` had no way to say what ground `L2BL46CHIOT` is. It has one now, and the file is
the **third deposit**. The reading is 1,572 sales: the 953 read by section and the 619 the
register gives no section, **ids APPENDED** — `ls0954` upward — so nothing `data/structures/
*.json` already cites has renumbered.

**The grammar, and it is the register's and not this project's.** A sectionless tract is
`(half)* L<lot> (BL|B) <block> <towncode>`: 616 of the 619 parse, and the three that do not
are REFUSED by name rather than left to a downstream guess.

| | rows | what `tract()` says |
|---|---|---|
| a lot and a block in a coded town | 615 | `town_plat_lot`, lot and block resolved, code carried |
| a lot and a block naming **no** town | 1 | `town_plat_lot`, and a refusal: the plat is not on the page |
| `L5BLCHIV`, `L1013CHIOT`, `SEL1B28CHIOT` | 3 | `refused`, each with its reason |

57 distinct blocks, 1 to 58. 46 rows are a part OF a lot and the fraction is carried as the
clerk wrote it — `N2` 15, `S2` 11, `W2` 7, `E2` 4, and eight rows of a half of a half
(`E2W2`, `E2E2`, `N2S2`, `W2W2`, `W2E2`). **A half of a half is not reduced to a quarter**:
an eighth would be this project's arithmetic and the doubled half is the register's prose.

**The plat is never named.** `town_code` carries `CHIOT` (334), `CHIOTV` (107), `CHIV` (92),
`CHI` (62) and `CHIOTVO` (20) exactly as printed and `plat` stays null, under T-0830's
unchanged rule: the Archives' key for these abbreviations is not reachable from this runner,
and guessing which addition `CHIV` names would put a house in the wrong half of the town.

**The `VO` trap, ruled — by refusing it.** T-1032 left the question open: `CHIOTVO` ends in
the two letters this register uses elsewhere to strike a sale out, and `tract()` read a
trailing `VO` as void. That test is defined on an ALIQUOT — `E2SEVO`, a half quarter-section
cancelled — where the letters before it are the survey's own; here the trailing letters are a
town code, so asking it is a category error and the answer is noise. **What the evidence
does and does not settle:**

- It does not settle it by price. Nineteen of the twenty carry $1,500 to $9,600 — but a
  void sale in this same register carries a price too (`E2NEVOID`, 80 acres, $100), so a
  filled price column proves nothing either way.
- It does not settle it by re-sale. If these were voided Original Town lots one would expect
  the lot to come back as `CHIOT`; **not one of the twenty has a `CHIOT` peer** on the same
  lot and block. Eight have a peer under `CHI` or `CHIV`, every one of them on a LATER day
  (20-24 June against 28-29 June) and at 12% to 95% of the `CHIOTVO` row's price — a spread
  too wide to read anything into. That leans against the void reading and is not proof: a
  re-sale after 1836 is outside this deposit entirely.

So **`void` is null on every town-plat lot**, neither claimed nor denied, and the twenty
carry a refusal that states the question in full. Nothing downstream may read them as valid
sales by default and nothing may quietly drop them.

**Three buyers that are not people, and the firm test could not see one of them** (T-1033).
`namesake.firm_style` looks for the conjunction the register sets before `CO` — `GARRETT A
ET CO` — and a body corporate has no partner in front of it to conjoin. So `UNION HOTEL CO`
would have gone to the forename rule as a man named Union, and **`COOK CNTY COM` — the
county commissioners, 24 lots, the third busiest buyer of the 619** — was refused
only because no Cook of the residents layer is called Cnty. *Being refused for the wrong
reason is not the same as being read.* `KNOWN_BODIES` now declares the three (`COOK CNTY
COM`, `CHICAGO CITY SCHOOLS`, `UNION HOTEL CO`), they are refused against every person FOR
BEING BODIES, their ground is carried in `resident_crosswalk.json § body_purchasers`, and an
undeclared body stops the build exactly as an undeclared firm does. No new PARTNERSHIP is in
the 619: `KNOWN_FIRMS` is unchanged at two.

**No resident is minted and none is regraded.** The crosswalk goes from 431 purchaser
spellings to 647 and from 93 proposals to 162; every new one is a PROPOSAL and carries
`ruling: null` until somebody rules it. What reached the cards is the same sentence the
by-section rows reach them with — *a purchase and nothing more* — and the town lots get
their own warning beside it, because they are not acres: the register states 0000.00 against
every one, so they add nothing to a card's acreage and only to its money.

**One hand ruling was overtaken by the rule.** T-0700 refused `WILSON JOHN L` against the
town's one John Wilson. The 619 bring a second reading of that surname — the register also
sells to `WILSON JOHN S` — so `namesake.collide` now refuses the spelling on its own, before
any ruling is consulted, and there is no proposal left for the ruling to move. Rule and
ruling AGREE and the reasoning still stands in `refusals[]`, so the gate allows a REFUSED
ruling in that position and still fails an `upheld` one, which would name a person the rule
no longer reaches.

**What the completeness probe says now.** Two of its three groups are closed: the 953 inside
the seven declared townships (held), and the 619 with no section (held). `complete_for_1836_
cook_county` is still **false**, and it now says precisely what is outside it — **1,213 rows
the county list gives a section that is not one of the seven townships the deposits
declare**, counted by township in `what_is_still_outside_it`. That is the whole of the
difference between this domain and Cook County, and no deposit ever promised it.

**A bug the join found.** `build()`'s undeclared-firm guard appended to a name that does not
exist in its scope, so a new firm would have crashed the build with a `NameError` instead of
naming itself. It is meant to stop the build, and now it stops it by saying which spelling
stopped it.

## The town lots' own proposals, cohort A: the twenty the register had already been ruled on (T-1034)

**T-1032 read the 619 town lots and T-1033 joined them to the crosswalk, and 72 new
purchaser spellings arrived proposed and unruled** — the same arrival the widened surname
rule made in T-0697, and adjudicated the same way, one bounded cohort per run, under
T-1034. The `ruled` block read `upheld 89, named 1, refused 48, unruled 72` the morning
this cohort started.

**Cohort A is the twenty whose PERSON already carries a ruling under another spelling of
the same name.** It is the natural first one for the reason cohort A of T-0990 was: it is
where the register's abbreviate-and-expand habit is densest, so a judgement already made
can be applied rather than re-argued — and, just as importantly, it is where applying one
blindly would be wrong, because C1's BROWN WM rule says a spelling with no discriminating
token is its own proposal however well the fuller spelling did. **Nineteen upheld, one
refused.** Ruled 2026-09-11. `ruled` now reads `upheld 108, named 1, refused 49, unruled
52`; matched 162 → 161, entries carried 619 → 618, one card retracted.

| upheld | refused |
|---|---|
| BOTSFORD J K, CARPENTER P, EGAN W B, EGAN WILLIAM, FULLERTON A N, GOODHUE J C, HAMILTON R J, HUBBARD E K, HUBBARD GORDON S, KIMBERLY E S, KINZIE ROBERT, MARSH S, MERRILL G W, MULFORD J H, NEWBERRY W L, PRICE JERE, SHERMAN S W, TAYLOR E D, TEMPLE J T | WRIGHT T |

**What the cohort taught, and cohort B should use it.**

*The precedent is not the ruling.* Nineteen of the twenty carry a token the fuller spelling
also carried — a middle initial (W B, A N, J C, R J, E K, GORDON **S**, E S, G W, W L, S W,
E D, J T), a forename that is unique among everyone the corpus prints of that surname
(CARPENTER **P**, MARSH **S**, PRICE **JERE**, MULFORD **J** H), or the register's own
expansion of it. The twentieth, WRIGHT T, carries none, and Fergus 1839 prints TWO Wrights
whose forename begins with T — Truman G. the speculator and Timothy of Michigan avenue.
**Ask what the token is before reaching for the precedent**, because the precedent was
bought with a token this reading may not have.

*The register's SEQUENCE is a check, and this cohort is where it works.* These are town
lots sold over ten days of one auction and entered block by block, so a bare spelling can
be placed by where it sits rather than by how it is spelt. EGAN WILLIAM has no middle
initial and would fail the BROWN WM test on paper; it is lot 4 of block 45 on 25 June 1836,
entered among EGAN WILLIAM B's lots 5 and 7 of that block on that day, while the rival
EGAN WILLIAM G stands on another block, another day and another leaf. EGAN W B is lot 2 of
block 25 immediately before WILLIAM B takes lots 3 through 8 of it. **That is the PEARSONS
argument, and the June 1836 sale hands it to you page by page** — the section deposits
almost never do, because a ring tract has no neighbours in the book.

*The town's own paper can be the source of the mis-spelling.* HUBBARD GORDON S looks like a
different man until you read the Democrat of 13 August 1834, which prints "Gordon S.
Hubbard" in the notice electing him a town trustee. A register spelling that the man's own
newspaper also used is not evidence of a second man.

*Three spellings the crosswalk does NOT propose turned up beside these and are left open,
deliberately:* GOODHUE G J (two rows of block 49, 27 June 1836, beside J C's nine),
KIMBERLY EDWARD (one row, where every printing of the physician reads Edmund), and
NEWBERRY WALTER S (six rows of the 1833 school-section sale and an $11,950 lot on the same
20 June 1836 as W L, and no volume of this corpus prints a Walter S. Newberry). Each may be
a misreading of a spelling already ruled on, and none of them is ruled on here — a ruling
this domain can only make on a proposal the crosswalk holds. The Newberry question is
noted on T-0396, which already owns which Newberry the corpus is holding.

**And the spend meter moved by ONE, not by twenty.** `measure_research_spend.py` anchors
rulings through a domain's `crosswalk.json`; this domain adjudicates in
`resident_rulings.json`, folded onto `resident_crosswalk.json`, which the second hop cannot
see. So `land_sales` reads 1,572 read against 704 spent whatever a cohort does, and the
ceiling came down 869 → 868. **That is the blind spot T-0962 named for census_1840, alive
in this domain**, and it means the ceiling is not the measure of this ticket's progress —
the crosswalk's own `ruled` block is.

### Cohort B: the twenty-four with no namesake, of the town lots (T-1034)

**Ten upheld, fourteen refused.** Ruled 2026-09-11. The crosswalk's `ruled` block moves
`upheld 108, named 1, refused 49, unruled 52` → **`upheld 118, named 1, refused 63,
unruled 28`**; matched spellings 161 → 147, **thirteen cards retracted** and with them
twenty-three register rows and **$45,319** of stated purchase money. Twenty-two of those
rows are town or canal lots, which have no acreage at all, so **only 80 acres move** — the
single quarter-section of section 11, 40N 13E, that came off FAY H K. Nothing was written
on: upholding a proposal only confirms what the spend pass had already put there.

| upheld | refused |
|---|---|
| FUNK ABSALOM, GARRETT A, GARRETT AUGUST, HEACOCK RUSSEL E, HEACOCK RUSSELL E, LOYD A, MCKEE DAVID, OGDEN WILLIAM B, SPRING GILES, WELLMAKER JOHN | CHURCH T JR, FAY HARRISON K, FINLEY CLEMENT A, KEYES EDWARD, MACK STEPHEN, MCGREGOR A, PEARSON HIRAM, ROBERTS E, ROBERTS EDMUND, RYAN THOMAS, SHEPHERD A, SHERWOOD S J, WILCOX DELAFAYETTE, WILSON JOHN S |

**THE LINE IS THE ONE T-0990's OWN COHORT B DREW, AND IT HELD WITHOUT BEING BENT.** The
same field defines both cohorts — `rivals[]` empty, the residents layer holding the surname
exactly once — and the same question decides them: does the town hold this man in anything
more than a bare name? Every one of the ten upholds has a second document with something in
it, and nine of the fourteen refusals have one name-only reading and nothing else. Four of
those fourteen are cards the layer itself marks **`letter_list_only`** — FAY H K, MACK
STEPHEN, SHEPHERD A, SHERWOOD S — which is the SPENCER WILLIAM G test written as a field,
and two of the four were already refused under T-0990 in their other spelling.

*The discriminator is a directory printing the forename whole where the card carries an
initial*, and it decided five of the ten:

| the register | the town's own printing | ruling |
|---|---|---|
| GARRETT A · GARRETT AUGUST | Fergus 1843: *Garrett, Augustus (G. & Seaman)*; Norris 1844 the same | upheld |
| LOYD A | Fergus 1843: *Loyd, Alexander, carpenter and builder*; 1840 census *Alex[r]. Loyd* | upheld |
| OGDEN WILLIAM B | Fergus 1843: *Ogden, William Butler (O. & Jones)* | upheld |
| FUNK ABSALOM | Norris 1844: *Funk, Absalom, butcher, Fulton and Boston markets* | upheld |
| SPRING GILES | Fergus 1843: *Spring, Giles (S. & Goodrich), res 62 Adams near State* | upheld |

**THE CIVIC LISTS ARE WHERE THIS COHORT'S WEIGHT SAT, AND ONE LINE OF ONE IS STILL NOT
ENOUGH.** Seven of the fourteen refusals rest on exactly one line of the 1833 tax list or
the poll of 1834 — FINLEY CLEMENT A, KEYES EDWARD, RYAN THOMAS, ROBERTS E, ROBERTS EDMUND,
MCGREGOR A, and MACK STEPHEN with a letter beside it. That is T-0990's STANLEY JOSEPH and
BLAISDELL BENJAMIN refusals, and it is not a rule against civic lists: **WELLMAKER JOHN is
upheld on them**, because the town holds him SIX times across five domains — the 1832 Black
Hawk muster, the 1833 tax list, the poll of 1834, a Democrat notice of December 1833 in the
paper's prose rather than its letter column, a witness signature in the St Cyr register of
April 1836, and an old-settler death notice — and because **the surname appears exactly once
in the whole corpus of 6,849 identities**, so there is no rival reading anywhere rather than
none in a thin layer. A count of readings is not the test; what each reading says is.

**MCKEE DAVID IS THE COHORT'S ONE UPHOLD ON A TRADE.** The card carries `arrival` 1823 and
`works_at` the government blacksmith shop at the foot of State Street, both attested to
Andreas, so the town records a resident tradesman and not a name — and a blacksmith of seven
years' standing taking the two cheapest lots of the town's first sale, $31 and $30 on 27
September 1830, is a purchase consistent with what is recorded of him. That is the ruling
rule's second limb, used once in this cohort and available nowhere else in it.

**THE REGISTER CAN BE ITS OWN RIVAL READING, AND PEARSON HIRAM IS WHERE IT IS.** This is
the one refusal made for a positive reason rather than for want of evidence: the same volume
enters **PEARSONS HIRAM** and **PEARSONS H** forty-four times, two of them town lots in this
very June 1836 sale six days earlier, and that spelling is upheld to Hiram Pearsons — while
the town's record of a Hiram PEARSON is two bare civic lines a surname fold away from him.
Four lots of block 1 and **$22,410, the largest retraction in the cohort**, come off a card
that should probably never have carried them. The README's own warning of cohort A named this
one in advance.

**AND THE MIDDLE INITIAL CAN NAME THE OTHER MAN.** SHERWOOD S J is refused against the
letter-list Stephen Sherwood because the J belongs to somebody the corpus holds under his own
name — Norris 1844's *Sherwood, Smith J. jeweler, 144 Lake st*, the business card signed
*S. J. SHERWOOD*, Fergus's *Sherwood, Smith Jones, jeweler and watchmaker*. Found on the way
past and filed as **T-1038**: the identity layer has ALREADY folded that Norris 1844 jeweler
line onto the letter-list card, so a jeweler's trade and address sit on a person minted to
claim nothing.

**WHAT THE SEQUENCE ARGUMENT COULD NOT DO HERE.** Cohort A's strongest tool was the June 1836
sale's block-by-block order, which decided EGAN WILLIAM by standing him between EGAN WILLIAM
B's lots. It decides nothing in cohort B: by definition these surnames appear once in the
layer, and on the register's side not one of the twenty-four stands on a block beside another
reading of its own surname. What the neighbours DID show is a second thing, and it is filed:
lot 8 of block 53 is entered three times for GARRETT A at $940, $940 and $1,880; lot 8 of
block 32 twice, at $3,000 each, for LOYD A and LOYD J; lot 5 of block 54 three times at
$1,110 for MERRILL G W, SHERWOOD S J and WHITLOCK T; lot 4 of block 29 twice at $50 for
ROBERTS E and MENARD PETER JR. **T-0885 asked this of the school section and answered it
there; the town-lot volume was never asked, and the paired and doubled prices suggest halves
of a parcel rather than duplicate rows.** Filed as **T-1039**.

**The ceiling came down 868 → 867, by one again, and for the reason cohort A gave.**
`measure_research_spend.py` anchors rulings through a domain's `crosswalk.json` and cannot
see `resident_crosswalk.json`, so twenty-four judgements move the meter by one. That is
T-0962's blind spot, alive in this domain for the second cohort running; the crosswalk's own
`ruled` block is the number to read.

### Cohort C1: the nine with a namesake, surnames A–K, of the town lots (T-1034)

Cohort C is the last shape the town-lot harvest left: every remaining proposal has a
namesake, so the mechanical rule fired on a surname the layer holds several of and the
forename alone chose among them. Twenty-eight is more than one run can argue, so C1 takes
the first surname block — **A to K, nine spellings. Six upheld, three refused.** `ruled`
118/1/63/28 → **124/1/66/19**; matched 147 → 144, **three cards retracted** carrying
thirty-three register rows and $9,597 of stated purchase money, 25 of those rows off one
card. No acres move: all thirty-three are town lots and the register prints `0000.00` in
the acres column for every one of the 619.

| upheld | refused |
|---|---|
| BAILEY AMOS, GRANT JAMES, HUBBARD H G, HUGUNIN H, HUGUNIN HIRAM, KING TUTHILL | COBB L B, FOSTER AMOS, KINZIE JOHN |

**ASK THE PRINTED RECORD HOW MANY MEN THE FORENAME COULD BE, NOT THE LAYER.** This is the
one lesson C1 carries and it decides seven of the nine. A `rivals[]` list is the LAYER's
census of the surname, and the layer is a reconstruction; the BROWN WM rule was written
because a thin layer holding one William Brown said nothing about a town that printed three.
The mirror of it is true and this block is where it shows: Fergus 1839, Fergus 1843, Norris
1844 and the newspaper run print **six** Baileys and one Amos, **six** Hugunins and one whose
name begins H, **thirteen** Kings and one Tuthill, **eight** Hubbards and one H. G. Where
the fullest record the town has holds the forename once, the namesake is a namesake and not
a rival, and the proposal stands on a token rather than on a gap.

**AN INITIAL-ONLY SPELLING IS NOT AUTOMATICALLY THE BROWN WM SHAPE — HUGUNIN H IS WHERE THE
LINE FALLS.** A bare H looks like a spelling with no discriminating token until two questions
are asked of the page. Is the initial unique in the printed record of the surname? Six
Hugunins are printed — Capt. Robert, Daniel, Hiram, James R., John C., Leonard C. — and one
begins with H. Does the TOWN use that abbreviation for that man? The Democrat of 20 May 1835
sets 'H. HUGUNIN' as chairman of the town meeting, and the same run prints him in full as
'Capt. HIRAM HUGUNIN, Agent, Chicago' for the North Western Fire and Marine of Oswego four
weeks later. An initial the town itself uses for one man is a token, not the absence of one.

**AND COBB L B IS THE SAME QUESTION ANSWERED THE OTHER WAY, WHICH IS WHY THE TWO BELONG IN
ONE COHORT.** Two initials look like twice the discriminator and are not, because the rival
carries the same middle one: the town's documented Cobb is S. B. Cobb — the saddle, harness
and trunk manufactory at the corner of Lake, out of the dissolution of Goss & Cobb, in the
American of 8 and 13 June 1835, 'Silas Cobb' in the Democrat's letter list of 1 April 1834,
'Cobb, Silas B.' at 171 Lake in Fergus 1839 — and only the FORENAME initial separates him
from the proposal. That letter is read once on the poll list and once in the register and
printed nowhere else in the corpus. A $9,000 lot is a large thing to hang on it.

**A CARD CAN LOOK LIKE THREE DOMAINS AND BE ONE READING.** FOSTER AMOS is the cohort's
largest retraction — 25 rows of the first town sale, 27 and 28 September 1830 — and its card
appeared to carry directories as well as the 1833 poll list. Those directory readings are
'Foster, A. H. (Jennings & F.)' and 'Foster, A. H. of Jennings & F.', folded on by the
crosswalk's own forename rule, *the given name of both begins A*: agreement on one letter and
disagreement on the H after it, on a man who boards the American Temperance House in both
years. Strip the fold and no Amos Foster is printed anywhere — not in Fergus 1839, 1843 or
Norris 1844, which give John Herbert, Edward, George Franklin and A. H.; not in the letter
lists, which give Caleb four times, Alburn, Jacob P. and a J. H. **Count a card's readings
before counting its domains.** The fold itself is the shape T-1035 is open on and the finding
is added there.

**THE ARGUMENT NOT TAKEN, AND WHY IT IS WRITTEN DOWN.** KINZIE JOHN is refused although
chronology would carry it: the register prints JOHN bare on seven rows of 27 September 1830,
and of the three John Kinzies the printed record holds, the elder died in 1828 and cannot buy,
while Fergus 1843's 'John Harris, jr., killed … a. 33' in 1862 puts the junior at about one
year old that month. That leaves John Harris by elimination — which is not a token on the
page, and **this project has already refused the identical string**: T-0501 met 'John Kinzie'
in McIlvaine's list of the 1834 trustees and refused it, saying in terms that the
identification is probable and was not that pass's to make. HARMON ISAAC declined the same
shape of argument for the same reason. Two domains reading one name the same way is worth
more than seven lots and $129. The evidence is recorded here so a later run can weigh the
overturn rather than rediscover it.

**THE CEILING DID NOT MOVE AT ALL THIS TIME, AND THE TOOL SAYS SO ITSELF.** Cohorts A and B
each moved it by one, 869 → 868 → 867; `measure_research_spend.py --tighten land_sales` now
answers *every ceiling already sits at what its domain reads — nothing to reclaim*, and 867
stands. The reason is unchanged and is T-0962's blind spot: the meter anchors rulings through
a domain's `crosswalk.json` and cannot see `resident_crosswalk.json`, so nine judgements are
invisible to it. **The crosswalk's own `ruled` block is the number to read**, third cohort
running.

Filed on the way past: nothing new. The A. H. Foster fold was ADDED to **T-1035**, which
already owns the question of a continuity route joining on one shared initial. One caution is
recorded in the GRANT JAMES ruling rather than filed — the card carries 'J. GRANT, Jr.',
regimental adjutant, from the Democrat of 3 September 1834, and a *Jr.* is the one suffix that
says a town held two men of a name. It is a card-merge question and it does not touch the
purchaser, who is printed JAMES in full.

### Cohort C2: the nine with a namesake, surnames L–M, of the town lots (T-1034)

C1 left the middle block. **L to M, nine spellings. Three upheld, six refused** — the first
cohort of this ticket to refuse most of what it read. `ruled` 124/1/66/19 → **127/1/72/10**;
matched 144 → 138, **six cards retracted** carrying twenty-four register rows and $30,708 of
stated purchase money. No acres move: all twenty-four are town lots, and the register prints
`0000.00` in the acres column for every one of the 619.

| upheld | refused |
|---|---|
| MONTGOMERY WILLIAM, MORRIS B S, MORRISON J M | LEE GEORGE W, LEE WILLIAM, LOOMIS H G, MILLER GEORGE, MILLER J, MILLER SAMUEL |

**THE REGISTER SORTS ITS OWN NAMES BEFORE THE TOWN IS ASKED, AND IT DECIDES FOUR OF THE
NINE.** Cohort B found this once, in PEARSON HIRAM against the PEARSONS HIRAM the same
volume enters forty-four times, and named it as the thing to look for next. It is here
twice over, and both times it is the FIRST question to ask rather than the last:

- **LOOMIS H G is refused because the register also enters LOOMIS HORATIO G** — ls0595, a
  federal 80-acre half-quarter section on 27 June 1835, a year before the five town lots.
  One man, two spellings, one book. The printed record then says which man: Chicago has
  exactly two Loomises, and the directories separate them cleanly — 'Loomis, Henry, lumber
  merchant, cor West Water and Randolph', who carries no middle initial in any printing,
  and Horatio Gates Loomis of Harmon & Loomis, printed 'Horatio G.' by Fergus 1839 and
  'H. G.' by Norris 1844, the register's two initials exactly. The residents layer holds no
  card for Horatio Gates, which is why the mechanical rule could only offer Henry.
- **MONTGOMERY WILLIAM is UPHELD for the same reason inverted.** The book holds four
  Montgomerys: LOTON WM and LOTON W, both upheld to the shoemaker under T-0990; JOHN, whose
  Residence column reads MCLEAN; and WILLIAM. The man who signs 'L. W. MONTGOMERY' in the
  Democrat is therefore in the register under his own forename and is not this purchaser.
- **MORRISON J M likewise**: the register enters EZEKIEL, ORSEMUS three times, EPHRAIM and
  THOS M under their own names, so J M is not a clipped reading of a Morrison the book
  already holds otherwise.

**C1'S LESSON HELD, AND ITS SHARPEST TEST WAS THE SURNAME MILLER.** The layer holds four
Millers; the printed record holds twenty-five readings of the surname and not one George.
Fergus 1839, Fergus 1843 and Norris 1844 print Bernhart, Capt. Harry, Charles/Chas., Daniel,
David, H., Henry, Jacob, John, John Newhouse, Peter, Porter, Robert, S. T. and William; the
Democrat and the American of 1833–35 add Col. Samuel, F. W., Henry F., Jacob V., Jesse,
Jesse F., Lorin, Marshall, Matthias B. and an uncertain L. P.; the first city election of
2 May 1837 polls a Daniel and a John B. MILLER GEORGE rests on one line of the 1833 tax
list against all of that, and is refused. MILLER J is the BROWN WM shape at its plainest —
four distinct printed forenames begin with J, and the card the initial was made to choose
is itself name-only in all five of its readings.

**READ THE ADVERTISEMENT, NOT THE OCCUPATION FIELD.** MILLER SAMUEL looked like the
cohort's best-attested refusal candidate and nearly survived on it: five readings, three
domains, and two of them newspaper readings that are *not* letter lists, one carrying the
occupation `agent`. At the page they are one advertisement printed twice — David Carver's
storage, commission and lumber notice of 25 February and 4 March 1834 — and its closing
sentence reads *'Calvin Britain esq. at St. Joseph, and Col. Samuel Miller, Michigan City,
are his Agents, who will immediately forward any article directed to him.'* The Colonel is
Carver's agent in INDIANA, named in a Chicago paper because Chicago readers shipped through
him. Strip the fold and the Chicago Samuel Miller is two bare names, a tax line and an 1832
Black Hawk enrollment. **A domain count is not evidence; the sentence the name stands in
is.**

**AND A MIDDLE INITIAL CAN DISAGREE RATHER THAN AGREE.** LEE GEORGE W is refused not for
silence but for contradiction: the only middle initial the town holds for a George Lee is
the S of 'G. S. Lee', a St. Cyr marriage of 1 October 1835 folded onto the card by the
forename initial alone, against the register's W. The rest of the card is one uncalled-for
letter of 20 May 1835, flagged `letter_list_only` by the newspapers layer itself, and the
three directories print seven Lees with no George among them. LEE WILLIAM is the STANLEY
JOSEPH shape unaltered — one line of the 1833 tax list, against three lots of the ORIGINAL
sale of 28 September 1830, three years earlier.

**THE UPHOLDS ARE WHAT A TOKEN LOOKS LIKE WHEN IT IS REALLY THERE.** MORRIS B S is the
least doubtful ruling of the ticket so far: both initials, the Democrat's 'B. S. Morris' of
17 June 1835 and the firm 'Casey & Morris, attorneys at law' in the same run, Fergus 1843's
'Morris, Buckner Smith, attorney, 59 Clark' and his own advertising card, and no rival Morris
in the layer who could take a B. MONTGOMERY WILLIAM has a trade that IS the purchase — ten
printings of 'W. MONTGOMERY' between 28 January 1834 and 12 August 1835 signing as
auctioneer, agent and commission merchant on South Water Street — and Fergus 1839 prints
'Wm. Montgomery' voting in the First Ward at the first city election, the only Montgomery
polled in the book. MORRISON J M agrees letter for letter with the poll of 1834's
'Morrison, J. M.', and exactly one of the ten printed Morrisons carries M as a middle
initial. **The price is never the argument**: $9,820 of town lots on a carpenter says
nothing about which man the letters name, and the ruling says so in terms.

**The ceiling did not move, fourth cohort running.** `--tighten land_sales` answers *every
ceiling already sits at what its domain reads* and 867 stands, because
`measure_research_spend.py` anchors rulings through `crosswalk.json` and
`resident_crosswalk.json` is invisible to it. **The crosswalk's own `ruled` block is the
number to read** — T-0962's blind spot, and this cohort does not pretend otherwise.

Filed on the way past: **T-1040**, carrying both card-level findings this cohort turned up
and repaired neither, because a ruling refuses a purchase and does not rewrite a person —
the Michigan City Colonel on `miller_samuel`, and `person_w_montgomery` carrying Loton W.'s
`boot and shoe maker` beside the auctioneer's own trades. The 'G. S. Lee' fold is recorded
in the LEE GEORGE W ruling rather than filed: the refusal does not turn on it — an initial
that disagrees and an initial that is absent refuse the same proposal — and a card-merge
question filed off a purchase ruling is the kind of ticket the queue's FILING RULE asks the
loop to stop opening.

### Cohort C3: the last ten, surnames S–Z, of the town lots (T-1034) — and the last of them

**Ten spellings. Eight upheld, two refused**, the most one-sided cohort of the ticket and
the one that ends it. `ruled` 127/1/72/10 → **135/1/74/0** — the crosswalk's own `ruled`
block reads **ZERO unruled**, which is what this ticket was opened to reach. Matched 138 →
136; two cards retracted, carrying four register rows and $7,175 of stated purchase money.
No acres move: all four are town lots, and the register prints `0000.00` in the acres
column for every one of the 619.

| upheld | refused |
|---|---|
| STEWART ROYAL, TAYLOR A D, TROWBRIDGE S G, WALKER G H, WALKER GEORGE H, WALKER JAMES, WILLIAMS ELI B, WOODWORTH J H | SMITH JAMES A, WRIGHT A |

**WHY SO MANY SURVIVED, AND IT IS NOT THE STANDARD SLIPPING.** The S–Z block is where the
town's best-printed men happen to fall: the town's Recorder, its second-best-attested
attorney, the carpenter who framed St. Mary's, the mail contractor, the future tenth mayor.
Six of the eight uphold on **both** of the register's letters being printed by the town
itself — E. B. and Eli B. Williams on two poll lists and in the chair of the Democratic
meeting of 29 June 1835; S. G. Trowbridge on the committee of that same meeting and
'Samuel G., mail contractor' in Fergus 1839; A. D. Taylor in Norris 1844 at the address
Fergus 1843 gives Augustine Deodat; George H Walker on Gholson Kercheval's Black Hawk
muster roll of 1832. C1's and C2's rule did the work in both directions: **ask the printed
record how many men the forename could be**, and in this block it keeps answering *one*.

**THE PRINTED RECORD REFUSES BY SILENCE, AND THAT IS A FINDING AND NOT AN ABSENCE.** WRIGHT
A is the cleanest refusal this ticket has made. The card is one line of the 1833 tax list
and nothing else in the identity master — no trade, no address, no second document — and
three separate crosswalks have already written down, each in its own file, that the surname
is in their volume and no entry under it carries an A: Fergus 1843 weighing six Wrights,
Norris 1844 weighing two, the Second Presbyterian roll weighing eleven. The printed Wrights
are Edward, John, John S., Timothy, Truman G., Walter, Winthrop, P. R. and Mrs. Hulda.
**A refusal recorded by a crosswalk is evidence, not a gap** — somebody looked.

**AN INITIAL-ONLY READING CANNOT CORROBORATE AN INITIAL-ONLY PURCHASE.** The one 'A.
Wright' anywhere in the corpus is a bidder at Fergus 1839's Fort Dearborn Addition sale,
two lots of block 13 at $1,040, and it reaches the card by *the given name of both begins
A* — the proposal over again in another domain, not a check on it. The old-settler match is
worse: 'Wright, Abner Mills', died 1890 aged 62-8-26, folds on by the same letter and was
seven years old in 1835. Counting domains would have upheld this one. **Count the readings,
and then count what is IN them.**

**A MIDDLE INITIAL CAN NAME A MAN THE LAYER DOES NOT HOLD APART.** SMITH JAMES A is refused
under the commonest surname in the corpus, and the register's A is what refuses it. The
card's only scene-window reading is the passengers' CARD of the steamboat Thomas Jefferson
in the American of 20 June 1835 — sixty-three signatures, *each with the place its signer
gives as his own*, the line transcribed 'Janes Stmth'. Its 1843 and 1844 directory matches
are recorded AMBIGUOUS: four printed entries meet the card on *the given name of both begins
J*. The one unambiguous entry it carries is Fergus 1839's 'Smith, James M., constable' — M
against the register's A, C2's LEE GEORGE W shape. And the printed James A. Smith is one of
the four in that ambiguous fold: 'Smith, James Ayer, clerk, L. P. Sanger & Co.' in Fergus
1843, 'Smith, J. A.' in Norris 1844, a man the layer holds no card for. The register is no
steadier — the same book enters SMITH J twice beside SMITH JAMES A's three rows.

**AND THE FACT THAT CUTS THE OTHER WAY IS WRITTEN INTO THE RULING RATHER THAN LEFT OUT.**
The 1840 census of Chicago does carry a head printed 'James A. Smith' (page 207, line 23),
and this card holds it — as a CANDIDATE under rule L7, the census crosswalk having declined
to make an identity of a name that agrees and nothing more. A candidate on one side and a
register row on the other are two name-only readings, five years apart. If that head is
ever tied to a person by something other than his name, SMITH JAMES A is the first ruling
in this file to revisit.

**TWO SPELLINGS OF ONE MAN, RULED TOGETHER — AND THE PAGE PROVES THEM.** WALKER G H and
WALKER GEORGE H are the two forms the town itself prints: 'G. H. Walker' in the Democrat's
letter list of 1 April 1834, 'WALKER, GEORGE H' on Kercheval's muster roll. The register
lays them side by side — lot 6 and lot 1 of **block 37**, both on 22 June 1836, one page —
which is cohort A's sequence argument arriving without being sought. George E. Walker is
refused under rule 2 on the middle initial, and his card is `letter_list_only` besides.
Eleven Walkers are printed across the three directories and not one George of any initial,
so neither register spelling is clipped from a Walker the town holds under a fuller name.

**AN OFFICE IS A TOKEN.** WALKER JAMES is the oldest purchase ruled anywhere in this
domain — lot 4 of block 19 at $36 and lot 4 of block 10 at $20, both 4 October 1830, in the
canal commissioners' first sale of the town, on the pages that carry Wolcott, both
Beaubiens, the Kinzies, Hubbard and Lafromboise. The town's record of him is the Democrat's
'Taken Up' notice of 26 November 1833: a brown horse taken up at Walker's Grove, appraised
by Jeremiah Walker and Timothy J. Clark, sworn **'before James Walker, J. P.'** and attested
by the clerk of the Commissioners' Court. That is the WELLMAKER JOHN shape — a civic reading
with something IN it — and the same notice prints Jeremiah beside him, so the page keeps the
layer's two Walkers apart on its own. **What the ruling does not say is that he lived in the
town**: Walker's Grove is thirty-odd miles down the Du Page, the card is `unplaced`, and a
ruling names a person and never asserts a residence.

**THE `letter_list_only` CARD THAT SURVIVED, AND WHY IT IS NOT THE RULE BENDING.** WOODWORTH
J H is the one card in this cohort the layer flags `letter_list_only`, and cohort B refused
four of those. It is upheld because the letter list is not what carries it. Fergus 1839
prints the FIRM — 'Woodworth, Robert P. & James H., wholesale dry goods merchants, 103 Lake
st' — a trade, a partner and a street number at the register's exact initials; Fergus 1843
carries 'Woodworth, James Hutchinson, merchant' as a single uncontested entry, expanding the
H; and the US House biography behind the card's birth year of 1804 is a third document. Four
Woodworths are printed and one begins J. **A FINDING ABOUT ANOTHER LAYER, NOT ABOUT THIS
PURCHASE:** that 1839 firm line is NOT on the card's directory appearances — the 1839
crosswalk does not carry the compound 'Robert P. & James H.' entry at all, so a man is
missing an 1839 reading because his name shares a line with his partner's.

**THE LOT THAT SOLD TWICE, SIX YEARS APART.** Lot 4 of block 19 is WALKER JAMES's $36 of
October 1830 and WOODWORTH J H's $14,000 of June 1836 — the same lot, the same book, the
town's six years in two rows. C2's hand-off named this pair in advance and sent it to
**T-1039**, which owns the row-is-not-a-parcel question for this volume; it is a resale
rather than a duplicate entry, and it is recorded here and not re-filed.

**The ceiling did not move, FIFTH cohort running.** `--tighten land_sales` answers *every
ceiling already sits at what its domain reads* and 867 stands, because
`measure_research_spend.py` anchors rulings through `crosswalk.json` and cannot see
`resident_crosswalk.json`. Across all five cohorts of this ticket — seventy-two judgements
— the meter moved twice, by one each time. **T-0962's blind spot is now measured rather than
suspected, and the crosswalk's own `ruled` block is the number to read.**

Filed on the way past: nothing. The one card-level finding this cohort turned up — the
Fergus 1839 compound firm entry missing from `woodworth_james_h` — is recorded in its
ruling and in the paragraph above rather than opened as a ticket, per the queue's FILING
RULE: it is a directories-layer question, and T-1035 and T-1040 already carry the fold
questions this ticket has been shedding.

### THE TICKET CLOSES HERE, WITH THE COUNT

**Seventy-two proposals arrived when T-1033 joined the town lots to the reading, and
seventy-two have been ruled: 46 upheld, 26 refused, across five cohorts.** The crosswalk's
`ruled` block reads **135 upheld, 1 named, 74 refused, 0 unruled** for the domain entire.
T-1034 closes on that count and not on 'there was nothing left'.

## The two Newberrys the register writes (T-0396)

**The question.** T-1034 upheld `NEWBERRY W L` and `NEWBERRY WALTER L` onto
`newberry_walter_loomis` on the middle initial, and deliberately did not rule on the S
side of the same surname — the register also writes **WALTER S** and **W S**, and no
volume of this corpus prints a Walter S. Newberry. Fergus 1839, Fergus 1843 and Norris
1844 print `Newberry, Walter L.` and `Newberry, Walter Loomis` and no other forename of
that surname at all. So either the register holds a purchaser the town never printed, or
the S is a misreading of the L. **$11,950 of the town's own ground turns on it** — lot 1
of block 3 of the original town, the second largest of the 619.

**What the S rows actually are, counted as entry events and not as rows.** The twelve
rows are not twelve witnesses:

| the reading | rows | where | when | money |
|---|---|---|---|---|
| `NEWBERRY WALTER S` | ls0288–ls0293, purchase nos **0371964–0371969, consecutive** | one page — vol 818 p 010, sec 16 T39N R14E | the school-section auction, 22–24 Oct 1833 | $809.00 |
| `NEWBERRY W S` | ls1392, purchase no 0365409 | vol L5A p 001, lot 1 of block 3, code `CHIOT` | 20 June 1836, canal sale | $11,950.00 |
| `NEWBERRY WALTER L` | ls0596, ls0823, ls0850, ls0851, ls0871, ls0872 | vol 687 pp 188–189, 260, the ring townships | 26–27 June 1835, federal cash entries | $644.00 |
| `NEWBERRY W L` | ls1391, purchase no 0365410 | vol L5A p 002, lot 8 of block 3, code `CHIOTVO` | 20 June 1836, canal sale | $8,290.00 |

The six 1833 rows are **six consecutive purchase numbers on one page of one volume**, and
`ls0287` — purchase no 0371963, the bare surname `NEWBERRY`, $163.50 for block 106 — sits
immediately above them in the same run, on the same page, in the same auction. That is
**one act of entry**, whoever made it, and seven consecutive rows of it give the forename
six times and omit it once. The 1836 row is a second act, on another volume and another
kind of sale. So the register's S is attested **twice independently**, not twelve times —
and twice is enough to refuse a transcription accident and nowhere near enough to mint a
man.

**What the deposit can and cannot settle.** `NEWBERRY WALTER S` appears in
`isa_land_tract_sales_t39n_t40n_r14e_through_1836.tsv` and again in
`isa_land_tract_sales_cook_county_list_through_1836.tsv`; `NEWBERRY W S` in the town-lot
deposit and the county list. Those are two separately-run queries, so **the S is the
Illinois State Archives' own field value and not this project's misreading of a page** —
this domain reads a database, not a manuscript, and there is no page image here for a
run to go back to. What two queries of one database cannot do is corroborate the
ARCHIVES' reading of the ledger. The letters this register's own transcribers confuse are
recorded nowhere in the deposit, so a preference for L over S would be a palaeographic
claim made without the palaeography.

**The 1836 pair is the sharpest form of the question and it does not answer it.** Lots 1
and 8 of block 3 were entered on one morning at **adjacent purchase numbers** (0365409,
0365410) on consecutive pages of vol L5A. Either the register wrote one man's middle
initial two ways in two consecutive entries, or two Newberrys bought lots in one block on
one day. Both are ordinary. The town codes differ too — `CHIOT` against `CHIOTVO`, whose
trailing letters T-1033 could not tell from a void marker — which is a second respect in
which two adjacent rows disagree, and it argues the same way: this is a page that would
repay being looked at.

**The ruling: the mechanical refusal stands, and it is a refusal and not a finding of
absence.** `resident_crosswalk.json` already refuses `NEWBERRY WALTER S` and `NEWBERRY
W S` against Walter Loomis Newberry `refused_on_the_middle_initial`, and nothing found
here overturns it: the S is the source's own, the project does not correct a clerk, and
upholding it would take the middle initial — the very token that carried the L rows in
T-0700 and T-1034 — and discard it the moment it became inconvenient. That is the
WENTWORTH test, and it has to fail as readily as it passes. **So the school section's
$809 and lot 1 of block 3's $11,950 attach to nobody this town holds**, and they are
carried that way rather than quietly folded onto the one Newberry the layer has.

**What would resolve it, and it is not in this corpus.** The register volumes themselves
— vol 818 p 010 and vol L5A p 001 — at the Illinois State Archives. No printed Chicago
directory or newspaper of 1835–1844 can, because the whole difficulty is that none of
them prints the name.

## A row is not a parcel, asked of the town lots — and answered the other way (T-1039)

T-0885 asked this of the October 1833 school-section auction and found duplication it could
not resolve: 38 parcels entered twice, 26 of them one pair of names. **Volume L5A was never
asked.** T-1034's cohort B, reading the register's neighbours to test a sequence argument,
turned up four lots entered two and three times over in paired and doubled prices, and filed
the question. The answer is not the school section's.

**THE COUNT FIRST, because the ticket asked for the shape counted and not asserted.** 616 of
the 619 parse to a lot and a block. Taking a parcel as the town code, the block, the lot and
the fraction exactly as the clerk wrote them, **those 616 rows name 559 parcels**. Forty-seven
parcels carry more than one row, 104 rows between them. Forty of the 47 are one day and one
page; **seven are the same ground entered again weeks or years later**, which is two
transactions rather than two writings of one — lot 4 of block 19 goes to James Walker for $36
on 4 October 1830 and to J. H. Woodworth for $14,000 on 21 June 1836, across the boom.

**ONE COUNT SETTLES THE DUPLICATION QUESTION: not one of the 40 same-day groups repeats a
purchaser's NAME.** Forty of forty are two, three or four different men. A clerk's duplicate
writes the same name twice; in 616 rows this register never does it once. Whatever these
repeats are, they are not the school section's shape.

**WHAT THEY ARE IS A CO-PURCHASE ENTERED ONE ROW PER BUYER, EACH ROW CARRYING THAT BUYER'S
SHARE OF THE PRICE** — not the parcel's price repeated. Three groups prove it, because in
three the price does not divide evenly and the register had to put the remainder somewhere:

| the parcel | the day | the shares as read | they sum to |
|---|---|---|---|
| lot 1 of block 51, `CHIOTV`, page 019 | 27 June 1836 | $1,916.66 · $1,916.67 · $1,916.67 | **$5,750.00** |
| lot 3 of block 51, `CHIOTV`, page 019 | 27 June 1836 | $686.66 · $686.67 · $686.67 | **$2,060.00** |
| lot 8 of block 38, `CHIOT`, page 014 | 22 June 1836 | $1,166.00 · $1,166.00 · $1,168.00 | **$3,500.00** |

A remainder spread across the rows is a division; one price written twice is not. The third
is the same act rounded to whole dollars instead of cents, which is why a test written for
cents alone would have missed it. **The other 37 groups divide evenly and cannot be settled
that way on their own**, so two things lean and neither is proof:

- **The same three men.** D. B. Brown, N. J. Brown and A. Garnett carry the proven thirds on
  lots 1 and 3 of block 51 — and $1,000 apiece on **lot 5 of the same block**, the same day,
  the same page, between the two. Whatever the proven pair are, lot 5 is. The shape recurs
  elsewhere: four parcels for Goodhue and Thompson, two for Richards and Stone, two for Smith
  and Taylor.
- **The roundness falls where a fraction would put it.** 87.5% of the 40 group SUMS land on a
  round ten, against 78.1% of the 512 rows that stand alone — while the 89 repeated rows' own
  prices land there only **56.2%** of the time. A share of a round price is less round than a
  price. That is a tendency over 40 groups, not a proof over any one.

**SO THE MONEY IS UNTOUCHED AND THE GROUND IS NOT.** $1,387,606.33 stands over the 616 placed
rows and $1,399,066.33 over all 619, exactly as T-1032 printed them and exactly as the cards
carry them, **because no row here repeats another's money** — each is a share, and the shares
add to the parcel's price. Nothing a card says about a man's spend moves. What shrinks is the
ground under the rows: **616 rows, 559 parcels**, and the report prints the two numbers beside
each other so neither can be read as the other by accident.

### And eight lots say the town code is not the plat

Eleven families of rows — one block, one lot, one day, one page — carry fractions that are
**disjoint and exhaustive of a whole lot** and agree, to the cent, on a single price per lot.
**Eight of the eleven spell the town code differently on different fractions of that one
lot.**

| the lot | the day | the rows | one lot at |
|---|---|---|---|
| block 54 lot 4 | 23 June 1836 | `N2L4B54CHIV` $1,755 · `S2L4B54CHIOT` $1,755 | $3,510.00 |
| block 9 lot 5 | 29 June 1836 | `N2L5BL9CHI` $1,310 · `S2L5BL9CHIV` $1,310 | $2,620.00 |
| block 5 lot 9 | 28 June 1836 | `N2L9BL5CHI` $1,350 · `S2L9BL5CHIV` $1,350 | $2,700.00 |
| block 50 lot 1 | 27 June 1836 | `N2L1B50CHIV` $1,325 · `S2L1B50CHIOT` $1,325 | $2,650.00 |
| block 48 lot 3 | 27 June 1836 | `N2L3B48CHIOT` $500 · `S2L3B48CHIV` $500 | $1,000.00 |

Complementary halves, at one rate, on one page, on one day, eight times over, are not two
additions that happened to match. **This does not decode the codes and it does not merge
them.** It says a row's town code cannot be read as naming which plat the lot sits on — which
is the refusal T-0830 and T-1033 already make, for the different reason that the Archives'
key to the abbreviations is not reachable from here. `plat` stays null. The refusal now has
arithmetic behind it as well as an absence.

### Three of the eleven need a bare row read as a fraction, and get it only as arithmetic

Lot 8 of block 53 is A. Garrett's, all three rows, 23 June 1836, page 020: **$940 on a bare
`L8B53CHIOTV`, $940 on `N2S2L8B53CHI`, $1,880 on `N2L8B53CHIOT`.** Read the bare row as the
whole lot and a quarter of it costs what the whole does. Read it as the quarter the other two
leave — the south half of the south half — and all three stand at **$3,760 the lot**. Lot 1 of
block 46 and lot 2 of block 53 do the same, at $2,750 and $2,980. Those, and not halves of a
parcel, are the doubled prices T-1034 saw.

**THE PARSER IS NOT CHANGED AND NO FRACTION IS WRITTEN ONTO A ROW.** `lot_fraction` stays null
on all three, because the clerk wrote none and inferring ground from a price would be this
project inventing the thing it most refuses to invent. The arithmetic is recorded in
`ground.json` under `counts.town_lots`, where a later reading of the plat can test it.

**Nothing here merges a name, drops a row, or writes a fraction.** T-0885's rule holds
unchanged: whether the men on one parcel are partners, a trustee and his principal, or
strangers is an IDENTITY ruling, and `resident_crosswalk.json` is where this domain makes
those. `tools/resolve_land_tracts.py --report` prints the counts and `--self-test` holds the
arithmetic — the disjointness on a 4×4 grid rather than an area sum, so that `E2W2` and
`W2E2` cannot quietly be the same quarter, and `N2S2` is a quarter rather than a half.

## The join to the ground, and the four tracts the town stands on

`tools/resolve_land_tracts.py --build` derives `ground.json`: one row per sale, carrying
either the polygon it lands on or the reason it does not. **346 of the 953 rows land on
the ground; the other 607 each say why they do not.** Ten of them are country tracts and
reach 63 of the 375 structures; the other 336 are school-section rows seated on the block
polygons of T-0797, and they reach no structure at all, for the reason the next section
gives. The
section grid is CONSTRUCTED from the one PLSS corner this project holds — State &
Madison, `G1` — on the plat's own bearing, in nominal one-mile squares, and is carried
only across the four sections that meet at it. That is liberty **L219**, and the module
docstring is the long form.

| the ground | who entered it | when | roofs |
|---|---|---|---|
| north fraction of section 10 — Kinzie's Addition | Robert A Kenzie / Kinzie, printed both ways | 7 May 1831 | 27 |
| E2NE of section 9 | Alexander Wolcott | 29 Sept 1830 | 18 |
| SW fractional quarter of section 10 — the United States Reservation | John Baptist Baubian | 28 May 1835 | 17 |
| E2NW of section 9 | James Kinzie | 28 Sept 1830 | 1 |

The reservation row is the one to read twice. `data/liberties.json` **L108** already
quotes Andreas for Beaubien's pre-emption of 28 May 1835 over the fort's ground; this
register carries the same entry independently, and the polygon under it is the ring L108
derives rather than a second construction of the same tract. **Whether the entry held is
not read here** — it was litigated for years, and this domain records the transaction the
register prints and nothing about its outcome.

## The school section, spent (T-0798)

**337 rows of this register — every one of them in section 16, the school section — were
read at the October 1833 auction and, until T-0797 traced the plat, not put on the
ground.** 336 of them now are: each is seated on the block polygon its own number names
in `data/traces/vectors/school_section_blocks_1834.json`, the 142 blocks measured off
J. S. Wright's 1834 survey. The one that is not is the row whose lot the register prints
as `06126`, refused because the parser will not guess at it.

**The block, and not the lot.** The sheet's ruled LOT lines are not traced, so a row that
buys lot 6 of block 48 is placed on block 48 with its lot carried as read and unplaced. A
block is about a hectare and the auction sold most of them to several men apiece, so
**no school-section row reaches a roof**, by rule rather than by geometry — a purchaser of
some lot in a block did not thereby buy the ground under a particular house. The one
committed structure standing in section 16, `heacock_house_monroe`, therefore still
carries no `land_owner`, and that is the honest answer rather than a missing one.

**What the 336 rows say about who owned the south.** The sale ran 22–25 October 1833 and
**105 purchasers as the register spelled them took ground in 136 of the 142 blocks**. 218
rows name a lot inside their block and 118 name the block alone. The busiest blocks are
95 (12 rows), 26 (11), and 48, 81, 82 and 120 (10 apiece) — the northern tiers, nearest
the town. The keenest buyers are Ebenezer and John Hale on fourteen blocks each, Arthur
Bronson on thirteen (with eight more under the register's spelling `Broson`), and Hiram
Pearsons on twelve, who is also the man who enters seventeen ring tracts above.

**And the rows are not parcels (T-0885).** Every count above is a count of REGISTER
ROWS, which is what the source offers. The ground is smaller: 335 live rows name only
**297 distinct block-and-lot parcels**, because **38 parcels are entered twice**, under
two names, on the same day and the same page of volume 818, each row with its own
purchase number. Six of the 38 carry the register's `AS` suffix on one of the two rows —
an assignment, the one shape of duplicate this source explains itself. **Twenty-six are a
single pair of names: every parcel Ebenezer Hale enters, John Hale enters as well**,
which is why the keenest-purchaser table reads two Hales at its head. One of the 38 is a
price disagreement rather than a name pair — block 72 lot 2, entered at **$8.00** and at
**$80.00**, same day, same page — and both figures are carried as read. Nothing here
merges a name or drops a row: whether a pair is one transaction or two is an identity
ruling, `resident_crosswalk.json` is where this domain makes those, and T-0885 leaves the
Hales an open question with the evidence beside it.

**Six blocks changed no hands at all: 1, 41, 87, 88, 126 and 142.** Four of those are
exactly the four Wright writes `Reserved` across and draws no numeral on. **Neither
reading was made from the other** — one is a plat traced off a sheet in 2026, the other an
auction list kept in 1833 — and they agree, which is the strongest corroboration the
block numbering has. `--self-test` holds it. The ticket that asked for this spend expected
the sheet and the sale to disagree somewhere near the tear at 87/88; they do not, because
neither block was ever offered.

**A block number the sheet does not carry is refused by name and never nudged onto a
neighbour.** No row needs that refusal today; the reason is written into `ground.json` and
the counter is printed at zero, so it is a standing check rather than a dead branch.

**The other silence is the source's rather than the tool's.** 254 of the structures stand
in the SOUTH-EAST QUARTER OF SECTION 9 — the original town — and get nothing, because the
canal commissioners sold those lots and this database does not hold them.

## Buying at the town's own sale is not a check on a town-side name (T-1017)

**T-0990 refused RUSSELL SAMUEL and SKINNER JOSEPH and wrote the same reservation into both:
the rows are at the town's OWN school-section sale, a man on the town's 1833 tax list is the
kind of man who bought there, and that argument is none of the rule's four arms.** It filed the
question rather than deciding it mid-cohort, because fifty rulings across four tickets name this
sale and deciding it by momentum would have moved all fifty. T-1017 decides it by counting.
`tools/school_section_sale.py` is the arithmetic, `school_section_sale_1833.json` the
measurement, `docs/RESEARCH/school_section_sale_1833.md` the reasoning, and the ruling itself is
in `resident_rulings.json` → `questions_ruled` → `T-1017`, where the rulings live.

**THE ANSWER IS NO, AND NOTHING RETRACTS** — which is the outcome T-0990 feared and the one it
got. All ten refusals that name the sale stand; all 39 upholds that name it stand, because in an
uphold it is corroboration beside an office, a middle initial or a trade and never the ground.

**WHAT ARGUES THE OTHER WAY IS REAL AND IS MEASURED FIRST.** Set the sale's 105 buyers against
the 542 purchaser spellings found only elsewhere in the register: **47.6%** of the sale's carry
an upheld match to a town card against **15.7%** elsewhere, and only **12.4%** carry a surname
this layer holds nobody of against **38.7%** elsewhere. The second comparison uses no
adjudication at all — only whether the layer holds the surname — so it cannot be an echo of
rulings already made. The town's own men did buy at the town's own sale.

**IT IS NOT EXCLUSIVE.** Thirteen buyers carry a surname the layer holds nobody of, BROSON
ARTHUR and HUQUEUIN HIRAM among them. And the ground went at auction prices: the 85 rows that
state an acreage fetched **$51.49 an acre** against **$1.45** for the 592 federal rows in the
same register. A sale at thirty-six times the government minimum is one capital could reach from
anywhere.

**IT CANNOT CARRY A NAME ON ITS OWN.** Fifty of the 105 buyer spellings hold an upheld match and
fifty-five do not. A criterion wrong more often than it is right is not what a row is checked
against; 47.6 per cent is a prior over a population, and the rule is applied one proposal at a
time.

**AND THE ARM THAT DECIDES IT: IT CANNOT SEPARATE TWO BEARERS OF A NAME.** Attendance is a
property of the ROW and is identical for every buyer at the sale; a middle initial, a trade, a
street or the Residence column are properties of the NAME, which is exactly why they can tell one
claimant from another. **Twenty surnames are printed at this sale under more than one spelling** —
the two Hales on the same twenty-six parcels, HARMON three ways, JONES three ways, PRUYNE as P, P
AND CO and PETER, WRIGHT JOHN beside WRIGHT T G. That is the WENTWORTH reasoning of cohort C3
turned on the sale instead of on the register as a whole: a source that sells to two men of a
surname has told you there are two. Admitting the sale would lift SKINNER JOSEPH and RUSSELL
SAMUEL and, by exactly the same amount, the 41 buyers refused against a rival and the 13 the town
has never held a surname for.

**THE RULING IS GATED, SO IT CAN BE WRONG OUT LOUD.** The residents layer grows every week and
the crosswalk re-derives from it, so all three of those figures can move. `check.sh` asserts them
rather than printing them: some buyer's surname absent from the layer, upheld matches in the
minority, some surname printed twice. If one flips, the build goes red naming the arm that failed
and T-1017 reopens — instead of a ruling standing on a measurement that has moved underneath it.
`--self-test` breaks each of the three on purpose and requires the failure.

**The enrichment is recorded as a measured prior and expressly NOT admitted as a fifth arm.** It
may be quoted in a ruling as context — it already is — and it may never decide one.
