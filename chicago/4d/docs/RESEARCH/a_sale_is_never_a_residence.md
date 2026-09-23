# A sale is never a residence — the written ruling on all 1,572 land-sale units

**T-1296**, the first piece of **T-1236**. Register:
`data/research/land_sales/spend_rulings.json`, derived by
`tools/spend_land_sales_rulings.py` and re-derived by its `--check` in the gate.

## What was open

The Illinois State Archives' Public Domain Land Tract Sales database, read for the
townships around Chicago through 1836 (T-0636), is 1,572 rows in three files. Every one
of them sat `unresolved` in the closed research-spend ledger — the largest single
unanswered body in it — because a land-sale row says nothing *about itself* that the
ledger's derivations can read. It has no `superseded_by`, no `outside_chicago` flag, no
`describes_date`; its date is printed inside `sale.date_purchased`, which is none of the
four fields the ledger's year test looks at. So all 1,572 fell to the one outcome left,
and the epic that owned them owned them by default rather than by argument.

## The rule every row is ruled under

**A purchase is a TRANSACTION and not a RESIDENCE.** That is the rule this whole domain
was read under, and it is the register's own position: its Residence column — the only
thing on the page that speaks to residence at all — reads COOK, ILLINOIS, some other
county, or UNKNOWN. A county, a state, or nothing, and never a town. A row can *bound* a
presence. It can never *assert* one.

## The eight rulings

| units | rule | reaches | what it says |
| ---: | --- | --- | --- |
| 570 | `the_purchase_is_later_than_the_scene_date` | later_only | Entered after 1 July 1835. Under T-0513's ladder it may corroborate and may date; it may not assert an 1835 fact. |
| 566 | `a_sale_is_never_a_residence` | refused | Entered on or before the scene date, Residence UNKNOWN (or only ILLINOIS), no upheld identity. The row evidences that this name entered this tract on this day, and nothing further. |
| 313 | `the_purchase_bounds_a_held_residents_presence` | → **T-1169** | Entered on or before the scene date, and the crosswalk's adjudication (T-0700 / T-0850) upholds the join to a person this town holds. A dated appearance is a bound on arrival, which is T-1169's field. |
| 46 | `the_register_places_the_purchaser_outside_cook` | outside_chicago | The Residence column names a county or state that is not Cook. The source answers the question instead of leaving it open. |
| 40 | `the_cook_residence_names_a_withheld_person` | → **T-1159** | Residence COOK, before the scene date, and no upheld join: either the identity was weighed and refused, or the layer has never seen the name. A named person in Cook County inside the window, read and withheld — the borderline roster's case exactly. |
| 27 | `the_purchaser_is_a_corporate_body` | refused | The county commission, the school fund, a public account. A body has no residence and no place in a population; the row names no person. |
| 8 | `the_registers_date_is_unreadable` | refused | The transcription carries a stub or an impossible year (`1000`, `1483`, `6/22`). A purchase that cannot be dated bounds nothing, and the stub is recorded rather than repaired. |
| 2 | `the_purchaser_is_a_firm_style` | refused | An `AND CO` entry. Which partner stood behind it is not on the page, and a surname-only join is always a refusal here. |

Two orderings are decided in that table and are held by the tool's self-test. The ladder
outranks the identity: an upheld resident who bought in 1836 is `later_only`, not a
presence bound. And the register outranks the silence: a Residence of MACON is an
outside-Chicago reading even where the identity is open.

## What the residue does to the 1835 town

**Nothing, directly, and that is the honest answer.** Not one of these rows adds a person
to 1 July 1835, changes a grade, or moves a household — the standing rule forbids it, and
no ruling here reopens an identity the crosswalk already adjudicated. What the corpus
leaves behind is two hand-offs, both dated and both narrower than the bodies they came
from:

* **313 rows to T-1169.** For 135 people this town already holds, the register prints a
  day on which they were at the land office. That is a ceiling on their arrival date and
  nothing else; T-1169 owns arrival and will read it there.
* **40 rows to T-1159.** Names the register places in Cook County before the scene date
  that the town does not carry — refused joins like CHIPMAN ANSEL, and names the layer has
  never seen. They are not residents and this file does not make them any; they are
  candidates for the borderline roster, each with a source and a re-admission class.

The other 1,219 rows are closed decisions, not missing work.

## What is derived, and why

Every note in the register is built from the row's own fields — its purchase number,
volume and page, its tract, its date as printed and as stored, its Residence column — so a
reader can set the note beside the row and see that it says what the row says. Nothing is
typed, because 1,572 typed notes would be a *worse* register: they would drift, and no one
could prove a note still matched its row. `tools/spend_land_sales_rulings.py --check` is
that proof, and it runs in `tools/check.sh`.
