# The trades the residents vocabulary had no word for (T-0418)

`data/residents/` speaks a CLOSED occupation vocabulary, declared in the
`vocabulary` block of `data/residents/index.json`, and
`tools/compile_register.py`'s `TRADE_TO_OCCUPATION` is the whole of the translation
from the prose a newspaper prints into it. The table is deliberately a table rather
than a matcher: a fuzzy trade match would silently retire an invented household on a
word that happened to collide, which is how every milliner in this corpus was once
compiled as a grain MILLER (T-0376).

The cost of a closed vocabulary is that a trade with no word in it reads back as
`occupation: null` — indistinguishable from a person the papers never gave a trade at
all. T-0373's pass refused 36 people on exactly that account: the papers DO print
their trade, and the vocabulary could not say it. This note is the adjudication of
every one of those printed phrases. Sixteen of them gained a word, three of them
already had one and only wanted a needle to reach it, and ten are refused with the
reason set out below.

## The rule that shapes both halves

**A word may fill a null; it may never displace a reading the register already
makes.** The T-0418 needles are a SECOND table (`TRADE_TO_OCCUPATION_T0418`), asked
only after the established one has failed across every trade the corpus prints for a
person and the trade of his firm. Without that ordering the additions would have cost
more than they bought: John Watkins, who kept the town's first school and also sold
books, would have stopped being a `schoolteacher`; E. K. Hubbard, printed both as a
merchant and as agent for the Howard Fire Insurance Company, would have stopped
retiring the merchant household the town invented for want of him. Neither is a
near-miss — both trades are printed for both men — but a ticket about people the
register reads NOTHING for has no business rewriting people it already reads.

Re-derived under that rule the change is purely additive: 52 people and 14 businesses
went from `null` to a word, no reading changed, and every action count in
`register_1835.json` (`enrich` / `new_resident` / `replace_invented`) is untouched.

## The sixteen words gained

| printed | word | who, in the 36 |
|---|---|---|
| bookseller | `bookseller` | Aaron Russell |
| stationer | `stationer` | (Russell's second trade; reached where it stands alone) |
| tinsmith, sheet iron worker | `tinsmith` | J. K. Botsford, W. Keeney |
| founder | `founder` | M. Jones, Wm. Jones |
| stove dealer, stove and hollow ware | `stove_dealer` | the Joneses' second trade |
| provision dealer | `provision_dealer` | Edward Simons, Silvester Marsh |
| keeper of the Exchange Coffee House | `coffee_house_keeper` | George Smith |
| refectory keeper, restorator keeper | `refectory_keeper` | J. A. Collett |
| insurance agent | `insurance_agent` | Hiram Hugunin |
| master mariner | `master_mariner` | (Hugunin's second trade) |
| harbour agent | `harbour_agent` | J. Allen, whose record places him at the Piers of the Chicago Harbor |
| house and land agent, house and lot agent | `land_agent` | W. G. Blanchard |
| Register of the (United States) Land Office | `land_office_register` | James Whitlock |
| sheriff, Sheriff of Cook County | `sheriff` | Stephen Forbes, Silas W. Sherman |
| militia officer | `militia_officer` | Josiah Stillman |

Two of these are offices rather than trades, and the ticket asked first whether
`data/residents/` should carry an office at all. **It already does, and has since the
vocabulary was written**: `justice_of_the_peace`, `postmaster`, `county_clerk`,
`indian_agent`, `sub_agent` and `lighthouse_keeper` are all offices, held by men whose
livelihood at Chicago they were. The precedent settles the question for the town's own
offices — a sheriff of Cook County held that office at the county seat, which was this
town — so it did not need to go to the owner. It does NOT settle it for an office held
somewhere else, which is the first refusal below.

## The three words that already existed and had no needle

`justice_of_the_peace`, `postmaster` and `army_officer` were in the vocabulary from
the beginning; nothing in `TRADE_TO_OCCUPATION` ever reached them. (`postmaster` had
one needle, `post office`, which the phrase "postmaster" does not contain.) Adding the
three needles is what gives Cornelius C. Van Horn, Stephen M. Salisbury and James
Walker their bench; L. F. Arnold his post office; and E. Kirby Smith, J. Green,
L. T. Jamison and Lieut. Allen their commissions.

## The ten refusals, and why each one stands

They are recorded in code as `TRADE_NOT_IN_VOCABULARY` in
`tools/compile_register.py`, matched on the WHOLE printed phrase rather than as a
substring — a refusal is a ruling about one phrase, and a substring refusal of "agent"
would quietly retire the insurance agent, the harbour agent and the land agent three
rows above it. The set is checked BEFORE both tables, which is what keeps the
Postmaster General of the United States out of the `postmaster` needle.

**An office of another government seat.** This is the vocabulary of the town's
RESIDENTS. A word here is an invitation to the mint pass to raise a Chicago household
for a man the same record places elsewhere, and the mint's placement refusal cannot be
relied on to catch him — it fires on a place the gazetteer records, and two of these
three carry no place at all.

- `postmaster general` — W. T. Barry, Postmaster General of the United States, whose
  name reaches the Democrat of 17 September 1834 from Washington.
- `governor of illinois` — Joseph Duncan, whose own gazetteer record places him at
  Vandalia.
- `judge of the fifth judicial circuit` — Richard M. Young, a circuit bench and not a
  Chicago livelihood.

**A single act, not a living.**

- `appraiser` — Timothy J. Clark, Richard M. Sweet and Jeremiah Walker are the three
  men named in ONE notice, of 26 November 1833, to appraise ONE estate. Nobody was an
  appraiser for a living.
- `administratrix` — Harriet Bradford's role in one probate, in one notice.
- `judge of election` — E. Peacock's one day's duty at one poll.

**Named, but not named as anything.**

- `agent` — Col. Samuel Miller is "Agent" and the notice says of what: nothing. (His
  record also places him at Michigan City, so the mint refuses him twice over.)
- `mechanic` — Wm. Payne. "Mechanic" is the papers' word for any skilled hand, and
  choosing which hand would be invention of exactly the kind this project exists not
  to make.

**A property relation, not a trade.**

- `steamboat owner` — J. F. Wight. The notice gives the vessel he owned, not the work
  he did. If this reconstruction is to carry vessel ownership it belongs on the boat's
  own record in `data/boats/`, joined to the man, rather than inside his trade.

**An itinerant.**

- `ventriloquist` — R. Kenworthy has one notice, of 11 June 1834, one night's
  entertainment, and no second issue that puts him in the town at all.

## What this note does not settle

The 36 are the people the register reads a trade for and cannot say. Sweeping the
whole gazetteer the same way finds **131** people in that position, so about 95 printed
trades are still unread — ship, schooner and sloop masters (a large and coherent
group), clergymen and Baptist pastors, livery stable keepers, hatters, brewers,
carriage and sleigh makers, confectioners, pedlars, land office receivers, town
clerks and trustees, and the state and federal offices that belong with the refusals
above. They are the same shape of question and not this ticket's list; they are filed
as their own ticket.

---

# The other 128 printed trades (T-0661)

T-0661 finishes what the section above leaves open. T-0418 adjudicated the 36 phrases
the newspaper register itself refused; sweeping the WHOLE gazetteer the same way —
2,630 persons and 206 businesses, and the trade of each — finds **343 distinct printed
phrases**, of which 128 were read by no table. This is the adjudication of all 128.
Every printed phrase in the gazetteer now either gains a word or is refused with a
reason: **311 are read, 32 are refused, 0 are unruled.** `tools/compile_register.py`
carries the ruling as `TRADE_TO_OCCUPATION_T0661` (86 needles) and
`T0661_NOT_IN_VOCABULARY` (23 new refusals, joining T-0418's ten and one carried
forward).

## The ordering rule holds, and it is measured

`TRADE_TO_OCCUPATION_T0661` is a THIRD table, asked after both of the others, for
T-0418's reason exactly: a word added here may fill a null and may never displace a
reading the corpus already resolves. Re-derived under that rule:

| | before | after |
|---|---|---|
| persons with an occupation the register could not say | 52 filled | 0 displaced |
| businesses likewise | 32 filled | 0 displaced |
| business action ledger | `enrich_existing` 30 / `new_building` 25 / `street_only` 58 / `unplaceable` 93 | **identical** |
| person action ledger | `enrich` 1386 / `new_resident` 1207 / `replace_invented` 37 | `enrich` 1386 / `new_resident` **1206** / `replace_invented` **38** |

**The one row that moves is an addition, not a displacement,** and it is stated here
because the acceptance clause asked for the ledger. Trowbridge is named in one notice,
for the "EAGLE COFFEE HOUSE (TROWBRIDGE'S)" of 24 June 1835, and the reading pass
printed his trade as `innkeeper`. An inn is a tavern and `tavern_keeper` is this
vocabulary's word for the man who keeps one, so he stops being a person with no trade
and becomes a documented tavern keeper — which is to say a candidate to retire one of
the four tavern-keeper households the town invented for want of a documented one. His
occupation was `null` before the needle and a word after it; nothing he already read
changed. `retirable_total` is unchanged at 10, because the four invented tavern-keeper
households were already fully covered by candidates.

## The twenty-one words gained

| printed | word | who |
|---|---|---|
| president of the board of trustees; president of the town trustees | `town_president` | John H. Kinzie, T. J. V. Owen, S. Hugunin |
| town clerk; clerk of the board of trustees; secretary to the town trustees | `town_clerk` | Isaac Harmon, G. W. Snow, Alex. N. Fullerton |
| assessor | `town_assessor` | George W. Snow |
| fire warden | `fire_warden` | Edward F. H[u]nter, appointed for the second ward, 1 October 1834 |
| Public Administrator of Cook county | `public_administrator` | G. W. Snow, J. B. Beaubien |
| receiver, United States Land Office; Receiver of Public Moneys | `land_office_receiver` | Edmund D. Taylor, appointed by the President with the Senate's advice, 25 March 1835 — the officer whose Register half T-0418 gave a word to |
| hatter; hat manufacturing and dealing | `hatter` | William Clay, who "has taken up his residence in the town" and put up a factory at Lake and Franklin |
| brewer; brewing | `brewer` | Crawford, of the Chicago Brewery, wanting 4,000 bushels of barley |
| confectioner; confectionary | `confectioner` | Stuart, John Wellmaker |
| livery stable keeper; liveryman; livery stable | `livery_stable_keeper` | Everson, Lathrop Johnson, J. N. Story, Thos. Emerson & Co. |
| carriage maker; sleigh maker; carriage and sleigh making | `carriage_maker` | Briggs & Humphrey, Riggs & Humphrey, William W. Morin |
| pedlar | `pedlar` | Bernard Jeste or [Ya]ple, whose lost package of bills was advertised |
| trunk maker | `trunk_maker` | Goss & Cobb |
| jeweller; jewelry | `jeweller` | J. H. Mulford |
| silversmith | `silversmith` | J. H. Mulford's second trade |
| liquor | `liquor_dealer` | Cromelien, Brothers & Co.; the wholesale wine and liquor store in Dearborn Street |
| engineer; superintendent of public works | `engineer` | Lieut. James Allen, on the harbour works |
| mail contractor | `mail_contractor` | John T. Temple |
| music teacher; piano forte tuner | `music_teacher` | Samuel Lewis |
| dancing master | `dancing_master` | J. A. Marshall |
| ship chandler | `ship_chandler` | four in Fergus 1839; see the note on it below |

## The words that already existed and had no needle

There are more of these than there are new words, and they carry more people. `master_mariner`,
which T-0418 minted and never reached, takes the sweep's largest single group: ten
schooner masters, three ship masters and one sloop master, out of the port arrivals
and clearances. `minister` — in the vocabulary from the beginning, with nothing that
reached it — takes nine, the four printed `clergyman`, the three Baptist pastors and
the two printed `minister` outright; the vocabulary keeps `priest` for the Catholic
cure and `chaplain` for the garrison's. `soldier`, `farmer`, `indian_agent`,
`county_clerk` (which Richard J. Hamilton holds under five spellings — county clerk,
clerk of court, clerk of the circuit court, clerk of the Cook Circuit Court, clerk of
the county commissioners' court), `justice_of_the_peace`, `attorney` (ten men printed
"solicitor in chancery" and one conveyancer), `physician`, `druggist`, `packer` and
`speculator` are the rest.

`army_officer` gains the ranks and staff appointments the papers print — a lieutenant
of the U.S. Army, the major of the 5th Infantry commanding the post, a post adjutant,
an acting and an assistant commissary of subsistence.

**The Cook county regiment takes `militia_officer`, not a refusal.** The ticket filed
its colonel (John B. Beaubien) and its regimental adjutant (J. Grant, Jr.) with the
offices of another government seat. They are not: the Cook county regiment is THIS
county's militia, mustered at this town, and `militia_officer` has been the word for
Josiah Stillman's commission since T-0418. The refusal ground is a livelihood held
ELSEWHERE, and neither of these men holds one.

## The twenty-three refusals, on T-0418's four grounds

**An office of another government seat.** `Secretary of War` (Lewis Cass, at
Washington), `Secretary of State of Illinois` (a state office held at Vandalia),
`circuit judge` (Sidney Breese — a circuit bench, and the same ruling T-0418 made for
the judge of the fifth judicial circuit).

**A single act, or a temporary duty, not a living.** `clerk pro tem` and `clerk pro
tem. of the Board of Trustees` — one meeting's duty at one board, and the office
itself already has `town_clerk`. `price reporter for the Chicago Democrat` — a duty
the paper's price current names, beside P. F. Peck's own printed trade. `map
publisher` — one map, published once, by a firm whose living is the Indian trade.
`railroad commissioner` — a commission to organise the Chicago and Vincennes Rail
Road, which never ran; the four Chicago men who held it (Kinzie, Dole, Hubbard,
Pruyne) are read by their own printed trades, and the fifth, William B. Archer,
promoted it from Clark county. The ticket filed this one under the town's offices; it
is not one, and refusing it is what keeps a Clark county promoter out of the town.

**Named as an agent, and the notice does not make the agency a living.** T-0418
refused a bare `agent` on this ground. `newspaper agent` and `newspaper subscription
agent` are the same shape and the notices say so plainly: W. Montgomery receives
subscriptions for the Saturday Evening Post at his own auction room, and R. Stewart
receives them for six New-York papers *at Col. Hamilton's office* — an accommodation
beside a trade, not a trade. `steamboat agent`: taking freight and passage for a boat
IS the forwarding trade, and the two so printed are read by it already (John H. Kinzie)
or are a St. Joseph house (J. Griffiths & Co., whose notice gives St. Joseph).
`manufacturers' agent` — an agency for manufacturers John Holbrook's notice does not
name, held beside his own printed trades. `hat manufacturers and wholesale dealers,
Detroit` — M'Cormick & Moon advertise in Chicago from No. 109 Jefferson Avenue,
Detroit; the FIRM's phrase is refused on their own notice's word.

**A property relation, not a trade.** `land owner`, `property owner` and `landlord`,
all three of John T. Temple, on T-0418's `steamboat owner` ground: what he held, not
what he did.

**A vessel's run.** `lake packet` and `packet service for freight and passengers
between Chicago and the mouth of the St. Joseph`. T-0418 put vessel ownership on the
boat's own record in `data/boats/` rather than inside a man's trade, and a packet run
between two ports is the same shape.

**The notice states no trade.** `[not stated in the notice]`, `unstated — the notice
announces only its closing`, `unstated — the notice announces only its dissolution`,
and `corn, sold from a barn` — one lot of corn from a barn on the Dupage, which the
gazetteer's own note already places outside the plat.

## What this ruling reaches beyond the register

`tools/fergus_1839_street_faces.py` measures the same vocabulary against Fergus's 1839
directory, where 1,655 entries print a trade. The trades it could not say fall from
**525 to 468 distinct phrases, and from 815 entries to 736** — 57 phrases and 79
entries the town's word list can now speak, including every farmer in the ring
townships, the tinners, the livery stables, the mail contractors and the civil
engineers on the canal.

**And the exposure that comes with it, recorded rather than hidden.** `occupation_of`
matches a needle as a SUBSTRING of the printed trade, which is what makes the table
cheap and what T-0376 already showed can go wrong (`mill` inside `milliner`). Fergus
1839 sometimes prints an employer or an address inside its occupation field, so four
of its 1,655 rows now reach a needle through an address rather than through a trade:
"milkman, Wm. Dili's brewery" and "real estate dealer, 6th ward, near Lill's brewery"
reach `brewer`; "carriage-driver, Graves' livery stable" and "horse-dealer, Graves'
livery stable" reach `livery_stable_keeper`; and two "law student" rows reach
`attorney`. None of them is evidence — that file is explicitly a measure and its own
note forbids placing a shop from it — and none of them is in the gazetteer the
register compiles. It is the same exposure the FIRST table already carries with
`store`, `boot` and `school`, widened, and it is written down here so the next pass to
touch this matcher knows what it costs.

`ship chandler` sits ABOVE `chandler` in the table for the same reason: a ship chandler
victuals and rigs vessels and is not a maker of candles. Daniel Elston, the one
"chandler" the gazetteer prints, is a soap and candle maker by his own notice; Fergus
prints four ship chandlers, and reading them as candle makers would have been exactly
T-0376's milliner-as-miller again.

## The city on the trade line belongs to the men who keep the house (T-0694)

**Settled 2026-09-06.** M'Cormick & Moon read `hatter` as PERSONS. Their FIRM's phrase
was refused on its own Detroit address — `hat manufacturers and wholesale dealers,
Detroit` is in `T0661_NOT_IN_VOCABULARY` — but the gazetteer also held them as a person
whose occupation is printed plainly as "hatter", and the person carried no place at
all. So the firm knew where it stood and the man did not, and the mints refuse on the
PERSON's `associated_places`.

Nothing had gone wrong yet, and re-derivation says so: their register action is
`new_resident` and was `new_resident` before, because ruling 1 turns on the town not
holding the name; `mint_documented_residents` refuses them one step earlier still, as
"a firm, not a person". What was missing was the *second* refusal behind the first —
if a later reading ever split the sign into two men, nothing would have said Detroit.

**Two corrections, both read off the printing that was already committed.**

| claim | entity | place now carried | read from |
|---|---|---|---|
| `chicago_democrat_1834_07_02#c018` | M'Cormick & Moon, proprietor | Detroit | the address line "No, 109 Jefferson Avenue" and the dateline "Detroit, March 15, 1[8]34" of their own notice |
| `chicago_democrat_1834_07_23#c006` | [uncertain: Wm. McCaleb], proprietor | St. Joseph | his partner's entity on the same claim, and c005's dissolution notice in the same issue |

**And the gate, so the shape cannot recur silently.** `compile_gazetteer.py`'s
`house_place_problems` requires that where a printed trade line ENDS in a place, every
entity on that claim in a HOUSE role — `proprietor` or `partner`, never an assignee, an
agent or a passenger — carries that place. It is DERIVED rather than a list of cities:
a trade tail counts as a place only where the corpus itself already names it as one on
some entity, which is what holds Newberry & Dole's `agents, Merchants Line` out of it
without anybody typing which words are towns. Its blind spot is stated rather than
papered over — a city this corpus names ONCE, on the very claim that omits it, is
invisible here. Four `--self-test` cases assert the rule and its three controls, and
`tools/check.sh` has run this pass's `--check` all along.

Swept across all 1,168 claims, the rule found exactly the two rows above and nothing
else.

## What this note still does not settle

- **Twenty-one new words is a large addition to a closed vocabulary**, and the closure
  is the point of it. Every one of them is a phrase the papers print for a named person
  at Chicago; none is a category invented to tidy the list.
