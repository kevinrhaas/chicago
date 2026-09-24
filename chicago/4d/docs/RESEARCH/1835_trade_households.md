# The trade households of 1 July 1835

**T-1347, of T-1173.** Written by `tools/reconstruct_trade_households.py --build`; re-derived
by `--check` on every gate run. **Nobody in this page is named by any source.**

The reconstruction order book (T-1166) carries twenty-four buckets whose axis reads
`family/trade` — an adult in a family household who works at something — and every one of
them was empty. **308 people**: 197 men and 111 women, across the three civil divisions,
by age band. This stage draws them as heads of their own households and writes them to
`data/residents/reconstructed_trades/`, outside the mints' directory for the reason
T-1172's re-admissions are outside it.

## What decides a head's trade

The only per-trade share this corpus yields is **T-1346's Fergus 1839 trade table** — 1,377
mapped entries over 88 printed trades, of which the 1835 controlled vocabulary carries 75.
The table's own `how_to_use_it` says what to do with it, and this stage does exactly that:
deal each sex's heads across the trades by largest remainder on those shares, renormalised
over the set being drawn for. **The 1839 volume is four years after the scene** and
describes a town three times the size; that is stated on every card rather than hidden.

Three bounds sit on top of the shares.

**A census ceiling.** Where the December 1835 State census counts a class one person keeps,
the town model's `against_the_state_census` table sets the bound. The town already holds as
many taverns, schools, printing offices, book stores and foundries as the census counted, so
those trades draw nobody more; it is short eleven physicians and four lawyers, so those draw
up to that. 64 draws were refused by a ceiling — 50 of the women's and 14 of the men's.

**A categorical refusal.** Fourteen trades never enter the deal at all. The garrison's four
— soldier, army officer, army surgeon, chaplain — because the order book's own method says
the fort "is read, not apportioned"; T-1176 reads the post return and T-1349 musters the
companies. And the town's singular offices — sheriff, postmaster, Indian agent, lighthouse
keeper, county clerk, public administrator, the land office's receiver and register — because
the civic mint already names the man in each, and a second is not a gap in the evidence.

**A residual.** Day labour for the men, domestic service for the women. Neither is an
establishment, so a census that counts stores and shops cannot enumerate either; neither
advertises, subscribes or signs. The residual takes the rounding remainder and everything a
ceiling refuses, and the ledger prints the arithmetic rather than absorbing it: **26 labourers
and 57 domestics**.

## What was drawn

| axis | result |
| --- | --- |
| heads ordered | 308 — every bucket filled to its order and no further |
| trades written | 54 distinct, all inside the controlled vocabulary |
| division | south 171 · north 72 · west 65 |
| age band | 20-29: 171 · 30-39: 91 · 40-49: 29 · 50+: 17 |
| naming pool | yankee 177 · irish 92 · french colonial 39 |
| kin seated | **0** — 1,241 owed and handed on |

## Three things this stage deliberately does not do

**No seniority rule.** T-1173's rules sketched "labourers young, master tradesmen older".
The 1839 table carries no ages and the 1840 schedule carries no trades, so nothing in this
corpus prices the association — a seniority curve drawn here would be a liberty invented to
make a table look like a town. Each trade is spread across the age bands in proportion to
what the book ordered, and the master/journeyman split is T-1183's, the ticket that models
how a business was staffed.

**No kin.** Each head is owed the family the 1840 size histogram drew for them; the size and
its seed are written onto the card as `household_owed` and **1,241 people are owed in total**.
They are not seated here because the kin of a family household are `family/none` in the order
book, and that quota is T-1174's and T-1171's — seating them here would order the same women
and children twice, which is the one arithmetic the book exists to prevent.

**No arrival.** The arrival model's `arrival_year_of_the_known_layer` table is computed
over the compiled scene, and the scene carries these cards — so an arrival drawn here would
move the table it was drawn from, and the research layer's own arrival fills re-derive from
that table. Writing one would silently redraw 1,440 research cards. T-1169 owns the block.

**No roles, and no place.** `roles[]` is the canonical record of a trade and its generator
reads the mints' directory, which this one is deliberately outside of; `lives_at` and
`works_at` are null, because T-1199 seats these households on the lot grid and T-1189 staffs
the businesses. The business band (T-1184 … T-1188) **adopts** these heads as its proprietors
rather than minting its own, so the two bands fill one quota. T-1179 converges the trees.

## Where it is recorded

- ledger — `data/reconstruction/1835_trade_households.json` (the plan, the refusals, the fills)
- cards — `data/residents/reconstructed_trades/hh_rc_*.json`, 308 of them
- the liberty — **L248** in `docs/LIBERTIES.md`
- the quota — `data/reconstruction/1835_reconstruction_order_book.json`, `fills` for T-1347
- the scene — `data/sidecars/1835/people.json`, `counts.reconstructed_trade_heads`
