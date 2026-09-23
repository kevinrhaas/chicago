# The press on the cards — the 147 dated appearances of T-1343

*T-1343, the second piece of T-1338 and the last of T-1329's four corpora. Its siblings
are T-1337 (the 1830 Peoria & Putnam schedule and St Mary's register, 27 bounds on 21
cards) and T-1326 (the town's own poll and tax rolls, 292 bounds on 236 cards).*

## What was unspent, and why it was not an identification problem

The closed research-spend ledger counts a reading as SPENT only where a structured,
source-bearing, `attested`/`inferred` node on a card NAMES the unit. 147 press units of
the Democrat and the American named a person on a dated day and reached no such node, and
they had been handed forward four times — T-1169, T-1318, T-1329, T-1338, T-1343.

The blocker was never the identity. `data/research/newspapers/register_1835.json` is the
committed newspapers-to-residents crosswalk and has been since T-0648: one row per person
the press names, with `action` and `action_target`, where `enrich` means *this layer
already holds that person* and names the card by its person id. `tools/compile_register.py
--build` derives it from the gazetteer and the committed town, and `tools/check.sh`
refuses a committed copy a rebuild would not produce.

The blocker was the NAME OF THE UNIT. A press claim's ledger id was its bare `c004`, which
55 held issues each print, so a bound naming one would have closed 937 other units of this
corpus as `asserted` — and had already closed 142 of them off three resident cards.
**T-1342 repaired that**: a press claim's key is the issue file's stem and the claim id
joined by `#`. This pass is the spend that repair unblocked.

## What was written

`tools/spend_press_bounds.py` writes **225 bounds onto 148 people in 146 households**, off
**111 of the 147 units**, as `persons[].dated_bounds[]` through `tools/dated_bounds_block.py`
— the block T-1326 introduced and T-1332 gave a second owner. The two papers are two
owners of it, one per source id, so each replaces its own group and nobody else's.

| | |
| --- | ---: |
| bounds written | 225 |
| people written | 148 |
| units spent | 111 of 147 |
| rows that put a body in the town | 0 |
| grades moved, identities reopened, persons minted | 0 |

**A name in print is not a body in the town**, so `here_by` is null on every row. The
standing ruling `a_dated_appearance_bounds_a_presence` said so in prose and this pass says
it in a field. One of these very readings is the argument for it:
`chicago_american_1835_06_27#c001` is a list of State Bank of Illinois officers reprinted
from the Sangamon Journal, and the brick building on the square near the court house that
the bank had taken is SPRINGFIELD'S square and SPRINGFIELD'S court house. Chicago in June
1835 had neither a brick bank nor a court house.

No row is `attested`: the issue is documented — deposited, dated and numbered in
`corpus.json` — and the identity is a name agreement the register declared, so the bound is
inferred however documented the page under it is. No row covers the scene date, under the
ladder ratified 2026-09-03.

**A row cites its crosswalk rule and does not transcribe it**, which is T-1337's rule 4 and
was measured again here. The register's `action_note` names the resident card BY ID —
"data/residents/ already holds this person as `mather_thomas`" — and a residents cohort
unit's ledger key is that same bare id. Transcribed onto a card, eleven of those notes
closed eleven resident-research units as `asserted` off a press bound that says nothing
about them. The row now names the register, the gazetteer person and the action, and the
reason stays in the file that authored it.

## What was refused, and what reopens it

The other **36** get a written refusal in `data/research/newspapers/spend_rulings.json`
rather than a fifth deferral. Both grounds are about the CARD and not about the name, and
both reopen themselves the day the layer changes:

| Rule | Units | Why | What reopens it |
| --- | ---: | --- | --- |
| `the_press_name_is_a_person_the_town_does_not_hold` | 30 | the register's action is `new_resident` — a person to be minted, not one to write on | the mint: the register re-derives to `enrich` and the bound is written |
| `the_press_name_replaces_an_invented_card` | 6 | the action is `replace_invented` — a card this project composed rather than read, and the substitution has not been made | the substitution |

A unit whose register row says `enrich` cannot fall under either: `press_appearance_rule`
raises rather than ruling it, because a unit with a card waiting for it is a unit this pass
owes a bound. That is the same discipline `CHURCH_OUTCOME_RULES` uses for an unseen
crosswalk outcome — mapping one onto the nearest rule is how a statement stops being true
of the units under it.

`a_dated_appearance_bounds_a_presence` is therefore gone from `RULES`, answered rather than
moved.

## The one civic claim that travelled with them

T-1342 freed a twelfth claim of another corpus by the same fix: Andreas on how the town got
its water by cart from the lake at the foot of Randolph Street, five to ten cents the
barrel. It had been read as an assertion about George W. Dole's reason for coming, because
its id is `c013` and so is the Democrat claim his card cites. It names no person, so no
card can receive it. What it describes is a TRADE — "private enterprise reaped a
comfortable little financial harvest in the operation of water carts" — that this project
holds no business record for, so `research_spend_ledger.EPIC_PIECES["civic"]` now points at
**T-1182**, whose acceptance is to raise an inferred business for every in-window trade
that has none. The routing is the one `PLACE_AND_ENTERPRISE` already gives an enterprise
claim, reached from the civic corpus instead of the press.

## What this does not decide

Nothing here mints a person, moves a grade, reopens an identity or invents a citation. It
does not decide that a person named in the press was a resident, that a printed name is a
person rather than a firm, or that a card of that name is the individual the paper meant —
the register decided that, in its own file, and this pass reads it.
