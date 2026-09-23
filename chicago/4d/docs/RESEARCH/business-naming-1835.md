# How a Chicago house of trade signed itself in 1835

**T-1184.** The style guide every reconstructed business in this project is named by,
written from the **196 firm styles the newspaper register prints** — the whole of what the
*Chicago American* and the *Chicago Democrat* put in front of readers between 1833 and
August 1835. It is a reading of that corpus and nothing else: no form appears below that the
register does not carry, and the attested house that carries it is named beside it so the
form can be checked against a printing.

`tools/reconstruct_businesses_1835.py` is the executable half. Its `STYLES` table holds the
forms and goods lines this page argues for, each with the printing it comes from, and the
build refuses a style the register already prints (§ *What an invention may not do*).

## The six forms the register prints

**1 · The sole trader, initials and surname.** The commonest signature in the corpus, and
the one a reconstructed sole trader takes: an initial or two, a surname, a comma, and the
trade or the goods.

> *B. Jones, grocery and provision store* · *J. C. Goodhue, land agent* ·
> *L. W. Montgomery, boot and shoe maker* · *S. B. Cobb, saddle, harness and trunk
> manufactory* · *R. Stewart, attorney* · *J. Bates jr., Auction Store*

The initials are the point. Of the eighty-odd single-keeper houses the register holds, far
more print `J. Curtiss` than `John Curtiss`, and a great many print nothing but the
initials and the surname — *A. Garrett*, *S. Foot*, *S. Dewey*, *W. Reed*, *P. F. Peck*,
*A. O. T. Breed*. The forename in full is the minority form and is also attested:
*Frederick Thomas, drugs and paints*, *William F. Lyon, Wholesale Grocery Store*,
*Philo Carpenter*, *Russell E. Heacock*, *Hiram Pearsons*.

**2 · The partnership, two surnames and an ampersand.** Two names, `&` between them, and
nothing else. Twenty-two of the thirty-six distinct firm styles the register carries are of
this shape.

> *Newberry & Dole* · *Jones & King* · *Pierce & French* · *Kinzie & Forsyth* ·
> *Goss & Cobb* · *Russell & Clift* · *Briggs & Humphrey* · *Magie & Wilkinson* ·
> *Dally & Youngs* · *Kercheval & Hamilton* · *Taylor & Handy* · *Tuttle & Brown*

Two brothers or a father and son sign with shared surname and split initials —
*C. & I. Harmon*, *G. W. & W. Laird*. A house that spells out **and** rather than `&` is
attested once — *Cooley and Halsman* — and is the rarer form.

**3 · The house with a silent partner: `& Co.`** A named principal, or two, with the rest
of the firm behind an abbreviation.

> *P. Pruyne & Co.* · *Hubbard & Co.* · *H. Doty & Co.* · *J. L. Wilson & Co.* ·
> *Wm. Hogue & Co.* · *Thos. Emerson & Co.* · *Matthias Mason & Co.* ·
> *Clark, Filer & Co.* · *Harmon, Loomis & Co.* · *Jones, King & Co.* ·
> *Cromelien, Brothers & Co.*

Three names take commas and the ampersand falls before the last: *Clark, Filer & Co.*
This is also where the register's abbreviated forenames live — *Wm.*, *Thos.*, *Jno.*,
*Geo.* — and `Jno. L. Wilson & Co.` and `J. L. Wilson & Co.` are the same house in two
printings.

**4 · The named house.** A sign rather than a surname: a bird, a city, a virtue, or the
town itself.

> *Eagle Tavern* · *Eagle Hotel* · *New York Clothing Store* · *The Boston Market* ·
> *Chicago Bakery* · *The Chicago Brewery* · *the Chicago Academy* · *the Traveller's
> Home* · *the Man Trap* · *W. Kimball's New Store* · *the Livery Stable at the Point*

**5 · The keeper's possessive.** The house named by whoever keeps it, with the trade after.

> *A. Clybourn's market on the market square* · *E. Wentworth's tavern on Flag Creek* ·
> *Stuart's confectionary and perfumery* · *Ingersoll's tavern stand* ·
> *Miss Bayne's Boarding and Day School* · *Peter Cohen's store*

**6 · The professional's full title.** The learned trades print the office rather than the
goods, at length, and capitalised.

> *Henry Moore, Attorney & Counsellor at Law* · *J. D. Caton, attorney and counsellor at
> law* · *Wm. H. Kennicott, Surgeon Dentist* · *L. G. Curtiss, Deputy Surveyor of Cook
> County* · *Charles Hunt, High School for Young Ladies* · *Dr. J. H. Barnard*

## The goods line

A trade line in this corpus is the advertiser's own idiom and it is a LIST, in the order
the house wanted them read:

> *drugs, paints, chemicals, perfumery and dye stuffs* (Frederick Thomas) ·
> *drugs and medicines* (Philo Carpenter) · *wholesale and retail store — groceries,
> hardware, crockery and drugs* (P. Pruyne & Co.) · *Boot, Shoe & Leather Store*
> (Wm. H. Taylor) · *Tin, Sheet Iron and Copper Factory* (J. K. Botsford) ·
> *storage, forwarding and commission merchant* (Wm. Sabine)

Capitalisation is inconsistent in the papers themselves and is not regularised here. Where
a reconstruction needs a goods line it takes one the register prints for that class,
never one composed for it.

## What an invention may not do

- **It may not reuse an attested style.** A reconstructed house may not trade under a name
  or a firm style the register already prints, and may not carry the name of a real
  proprietor. `reconstruct_businesses_1835.py --check` refuses each, over the whole
  register, and `--self-test` fires both.
- **It may not use an anachronism.** No *Inc.*, no *Ltd.*, no *Company* spelled out, no
  brand word, no trademark, no ampersand-free corporate style. The register has none, and
  the general incorporation acts that would license them are decades away.
- **It may not invent a surname.** Surnames come from
  `data/reconstruction/1835_invented_name_pools.json` by the proprietor's community, and in
  practice a reconstructed house does not draw one at all: it **adopts** a reconstructed
  trade head the resident band already drew, so the surname on the sign is the surname on a
  card that was checked against every real name in the town when it was written.
- **It may not be more specific than its evidence.** The house's name is a reconstruction
  and the record says so on every field; nothing about a style is ever graded above
  `reconstructed`, and no reconstructed house cites a source.

## Worked: the two druggists of 1835

The December 1835 State census prints **four druggists**; the register holds **two** at the
scene date — Philo Carpenter and Frederick Thomas. The order book therefore orders two, and
the resident band had already drawn exactly two reconstructed heads at the trade. They sign
by form 1, on goods lines both attested druggists advertise:

| | reconstructed house | adopted keeper | face |
|---|---|---|---|
| south | *B. Crandall, drugs, medicines and dye stuffs* | `rc_crandall_benjamin` | Dearborn Street |
| north | *Nathaniel Metcalf, drugs, medicines and dye stuffs* | `rc_metcalf_nathaniel` | Kinzie Street |

Both forms of the sole trader's signature are in the table, and the seed decides which each
house takes — which is why one prints an initial and one a forename. The face is a
`street_only` limit, not a premises: no lot, no roof, no coordinate. See
**docs/LIBERTIES.md § L254**.

## Worked: the four boarding houses of 1835, and the honorific that is not dealt

A boarding house signs by **form 5, the keeper's possessive**, and by nothing else. It is
the form this town's own lodging houses take — *Miss Bayne's Boarding and Day School* in
the register, *Rufus Brown's Boarding House* on the one boarding house the structure layer
names — and the seed deals between the possessive in full and the possessive with the
forename cut, exactly as *Ingersoll's tavern stand* and *Stuart's confectionary and
perfumery* print it.

| | reconstructed house | adopted keeper | seat |
|---|---|---|---|
| north | *Bardwell's boarding house* | `rc_bardwell_esther` | `recon_1835_north_h1_007` |
| north | *Newell's boarding house* | `rc_newell_lydia` | `recon_1835_north_h2_030` |
| north | *Ellen Cavanagh's boarding house* | `rc_cavanagh_ellen` | `recon_1835_north_h2_045` |
| west | *Martin Fitzgerald's boarding house* | `rc_fitzgerald_martin` | `recon_1835_west_006` |

Two things are different here from the druggists above, and both follow from the same fact:
**the building came first**. The seat is a `premises` and not a street face, because the
roof is what bought the house — the census enumerates taverns and never boarding houses, so
no shortfall of this class can be counted and there is no order-book row to spend. And the
keeper is adopted from the **lodgers** stage rather than from the trade heads: T-1371 drew
these four as the keepers of roofs it was putting people into, and their cards already read
`boarding_house_keeper`.

**No honorific is dealt, ever.** Three of the four keepers are women, and the register
prints both *Mrs. H. Sherman* and *Miss Bayne's* — so the form is available and attested.
It is refused anyway, because both forms assert a marital status and these cards carry
none: the stage minted them as solitary keepers and nothing in the layer says whether they
were married, widowed or single. A sign reading *Mrs. Bardwell's* would be inventing a
husband to make a shopfront read well. The possessive stands on the name alone, which
asserts only what the card holds. See **docs/LIBERTIES.md § L257**.

## Worked: the two law offices and the physician's room of 1835

A learned trade signs by **form 6**, and the professions group takes it unchanged. The two
law offices take the attorney's own two printings — the initial and surname of *J. Curtiss,
Attorney and Counsellor at Law*, or the forename in full of *Ebenezer S. More, attorney at
law* — with one of the three trade lines the register actually prints after it: *attorney at
law*, *attorney and counsellor at law*, or the fullest and commonest of the three, *attorney
and counsellor at law, and solicitor in chancery*. The physician's room takes the doctor's
title, which in this corpus IS the firm style: *Dr. J. H. Barnard* prints the title, the
initials and the surname and no trade at all, and *Dr. W. G. Austin, botanic physician*
prints the same with a line after it.

| | reconstructed house | adopted keeper | face |
|---|---|---|---|
| north | *B. Robillard, attorney and counsellor at law, and solicitor in chancery* | `rc_robillard_baptiste` | North Water Street |
| south | *R. Parmelee, attorney and counsellor at law, and solicitor in chancery* | `rc_parmelee_reuben` | South Water Street |
| south | *Dr. J. McGuire, physician* | `rc_mcguire_john` | South Water Street |

**One attested line is deliberately withheld.** Austin's own *botanic physician* names a
medical school. The register knows Austin's because Austin advertised it; nothing whatever
knows it of a man nobody wrote down, and dealing it on a seed would invent a training. The
physician's goods table therefore carries the single line *physician* — the one the register
prints under Dr. J. H. Barnard — and the form, not the line, is what the seed varies.

**Why there are three and not fifteen.** The census lines behind this group count MEN and not
premises, and the count was returned months after the scene. Both corrections are in the
order book rather than here: see **docs/LIBERTIES.md § L259**.

## Worked: the brewery and the jeweller's of 1835

T-1185's group, the mechanics' shops, writes two. Both sign by form 1, on goods lines the
register prints for their own class and nowhere else:

| | reconstructed house | adopted keeper | face |
|---|---|---|---|
| north | *M. Quinn, brewery* | `rc_quinn_martin` | North Water Street |
| west | *L. Chevalier, watches, jewelry, engravings and fancy goods* | `rc_chevalier_louis` | Canal Street |

Two things about the goods lines. The brewery's is a single word because that is all the corpus
gives: the register carries one brewery, *the Chicago Brewery*, with no trade line under it, and
a list composed for the reconstruction would be exactly the invention this page exists to
refuse. The jeweller's is J. H. Mulford's own line, verbatim — he is the one attested house of
the class — which is the rule of § *The goods line* applied at its strictest.

And the faces differ in kind from the druggists'. A brewery is not a shop front: it wants water,
fuel and a yard, and it takes the working banks rather than a retail street, which is why
*M. Quinn* lands on North Water and not on Kinzie. The jeweller's is a retail front and takes
the retail faces, as Mulford does from South Water Street.

**The brewery also carries the count that argues against it.** The *Chicago American* of
15 August 1835 counts one brewery where the December census counts two. The record's own
`reconstruction.basis.note` prints that sentence, so a reader holding the card holds the
objection to the card. See **docs/LIBERTIES.md § L257** and
**docs/RESEARCH/business-layer.md** § *the mechanics' shops of 1835*.

---

Related: the order book **docs/RESEARCH/1835_reconstruction_order_book.md**, the trade heads
**docs/RESEARCH/1835_trade_households.md**, the lodging model
**data/reconstruction/1835_lodging_model.json**, the business layer
**docs/RESEARCH/business-layer.md**, tickets **T-1184**, **T-1418** (of **T-1186**), **T-1408**, **T-1173**, **T-1166**.
**docs/RESEARCH/business-layer.md**, tickets **T-1184**, **T-1408**, **T-1173**, **T-1166**.
**docs/RESEARCH/1835_trade_households.md**, the business layer
**docs/RESEARCH/business-layer.md**, tickets **T-1184**, **T-1185**, **T-1173**, **T-1166**.

## Worked: the two livery stables and the two lumber yards of 1835

T-1424's four houses are the first the programme draws with **no count behind them at all**.
The apothecaries stand on a census line that prints four against a register that holds two;
the boarding houses stand on buildings this project already raised. A livery stable stands on
neither — the census's eighteen lines never reach the trade, and nothing in `data/structures/`
is one — so what buys the house is the KEEPER, drawn months earlier by the resident band at a
trade whose own word names the establishment. The naming problem that follows is unusual: the
register prints only **three** houses between the two trades, so the forms are few and every
line offered is one of those three printings.

**The liveries.** *Lathrop Johnson & Co., livery* is the register's one printed firm style of
the trade: form 1, cut here to the sole keeper each drawn head is, since `& Co.` would assert
partners nobody drew. *the Livery Stable at the Point* is form 4 and cannot be reused — it
names a PLACE, and a reconstructed house that borrowed it would be claiming the Point. What
it does yield is a second trade line, since *livery stable* is the register's own phrase for
the trade beside Lathrop Johnson's bare *livery*. The two heads are both south-division and
draw as **J. Dufresne, livery stable** and **W. Leland, livery stable**.

**The yards.** The register's one printed yard is a descriptor rather than a signature — *the
lumber yard and warehouse announced for the opening of navigation, 1834* — and its trade line
is *lumber yard and store house, on sale and commission*. Two goods lines come off it: the
bare *lumber yard*, and *lumber yard and store house* with the commission cut, because a
commission business is a claim about how the house traded and not merely what it sold. The
forms are 1 and 5, and form 5 is licensed for a yard by *A. Clybourn's market on the market
square* — this town's own possessive over an open working ground rather than a shop front.
The two heads draw as **A. Hubbard, lumber yard and store house** in the south division and
**Woodruff's lumber yard** in the west.

**And the honorific question does not arise here,** as it does for the boarding houses: all
four heads are men, and the possessive stands on the name alone in any case.

## Worked: the fifteen service houses of 1835

T-1419's fifteen houses take T-1424's form — the **trade head** — into four trades the
December 1835 State census enumerates nowhere: nine **millineries**, four **land offices**,
one **dress making shop** and one **barber's shop**. The naming problem here is the opposite
of the liveries': three of the four trades are printed in this register several times over,
so nothing has to be reasoned from a neighbouring class.

**The millineries and the dress making shop.** The register prints three millineries at the
scene date and one dress maker, and all four carry the same idiom: *Elmira Fowler* on
Dearborn, *Mrs. H. Sherman* and *[Mrs.] Herman* at the Mansion House, all at *millinery and
dress making*, and *Sarah D. Howe* at *dress, cloak and habit making* on Lake. Two goods
lines come off that: the trade word alone and the printed line whole. The forms are 1 with
the forename in full — the form Fowler and Howe both print — and 1 with the initial, the
corpus's commonest signature. **No honorific is dealt**, exactly as for the boarding houses
and for the same reason (**L257**): *Mrs. H. Sherman* is available and attested, and it is
refused anyway, because these cards assert no marital status and a sign reading *Mrs.
Chapin's* would invent a husband to make a shopfront read well.

**The land offices.** Three printings, two of them signatures: *J. C. Goodhue, land agent*
and *W. G. Blanchard, house and land agent*, with one unnamed house and land agent carrying
Blanchard's line again. Form 1 in both its readings, and the two trade lines as printed.
Blanchard is the one land agent the register places, on **Lake Street**, so Lake leads the
south-division face rule and the two business streets either side follow it.

**The barber's shop, which has no printing at all.** The corpus prints no barber — the
December census does not count the trade and no advertisement survives — so there is no
style to take and, by the rule above, none is composed. The forms are the naming guide's own
sole-trader readings, and the goods line is the single word *barber*: the one this project
already stands a barber's shop under, in `rcb_fb_barbers_shop` (**L255**, T-1377). One head,
one shop, and the second shop is bought by the head rather than by a count — which is the
restatement T-1186 asked for before a second barber could be raised.

**docs/RESEARCH/business-layer.md**, tickets **T-1419** (of **T-1186**), **T-1424**,
**T-1404**, **T-1173**, **T-1377**.
