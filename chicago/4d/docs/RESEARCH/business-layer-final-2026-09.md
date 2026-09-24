# The business layer, printed — September 2026

**T-1442**, the last of the three pieces **T-1190** split into. T-1440 settled the identities,
T-1441 tooled the substitution rule, and this report is the count: what the town's business
layer holds on 1 July 1835, set against the two contemporary counts that can be set against
it, and the order book's business buckets read out at the end of the band that filled them.

Nothing here is a new reading. Every figure is lifted from a derived file that `tools/check.sh`
re-derives —
`data/businesses/index.json` (`tools/compile_businesses.py`),
`data/research/books/trade_census_1835_crosswalk.json` (`tools/trade_census_1835.py`) and
`data/reconstruction/1835_reconstruction_order_book.json` (`tools/build_order_book_1835.py`) —
so a layer that moves moves this page through the generators and the gate, and a table that has
fallen behind its inputs is red rather than quietly wrong. **The tables are transcriptions, not
measurements.**

---

## 1 · What the layer holds

| | records |
|---|---:|
| business records in the layer | **271** |
| — compiled from the printed register | 196 |
| — authored (inferred shops, reconstructed firms, the civic rooms) | 75 |
| standing at the scene date, 1 July 1835 | **254** |
| — attested | 148 |
| — inferred | 74 |
| — reconstructed | 32 |
| people the records name | 277 |
| — linked to a card in the resident layer | 224 |

The 254 carry 269 census-class rows between them, because **18 records carry more than one
class** — a store-and-forwarding house is counted on both lines. That is why the per-class
grade columns in § 3 sum past 254 and must not be read as a partition of it.

## 2 · The December 1835 State census, and what the town holds against it

Moses and Kirkland print, at page 95 of volume 1 (`bk_mose1_006`), the State count taken
between 1 September and December 1835. **The date is the whole of the caution**, and it is
written into the crosswalk rather than left to a reader's memory: the count is two to five
months *after* the scene date, in the fastest-growing months the town had. A shortfall against
it is never evidence that a business stood in July.

| | |
|---|---:|
| businesses ruled by the crosswalk | 236 |
| — printed in the register | 196 |
| — authored, attested or inferred | 40 |
| in town | 233 |
| printed as standing outside it | 3 |
| standing at the scene date | 216 |
| carrying no enumerated class | 89 |
| the census's enumerated total | **118** |
| the town's enumerated total at the scene date | **134** |

A **reconstructed** house is not counted on the town's side of that comparison, and the reason
is the order book: its business buckets are cut as *census count minus what the town knows*,
and the reconstructions those buckets order are carried in `filled`, a separate counter. Count
a reconstructed firm as known and the same house is subtracted twice.

## 3 · The crosswalk and the order book, class by class

*census* is the December line; *town 1 Jul* is the crosswalk's count of attested and inferred
houses standing on 1 July; *att / inf / rec* are the Businesses view's own grades over the
scene-date records carrying that class (a record with two classes is in both rows); *book
target / to do / filled* are the order book's.

| class | census line | census | town 1 Jul | att | inf | rec | delta | book target | to do | filled |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `store` | forty-four stores (dry goods, hardware and groceries) | 44 | 65 | 41 | 26 | 0 | +21 | 44 | 0 | 0 |
| `book_store` | two book stores | 2 | 2 | 2 | 0 | 0 | 0 | 2 | 0 | 0 |
| `druggist` | four druggists | 4 | 2 | 2 | 0 | 2 | −2 | 4 | 2 | **2** |
| `silversmith_jeweller` | two silversmiths and jewellers | 2 | 1 | 1 | 0 | 1 | −1 | 2 | 1 | **1** |
| `tin_and_copper_manufactory` | two tin and copper manufactories | 2 | 4 | 3 | 1 | 0 | +2 | 2 | 0 | 0 |
| `printing_office` | two printing offices | 2 | 2 | 2 | 1 | 0 | 0 | 2 | 0 | 0 |
| `brewery` | two breweries | 2 | 1 | 1 | 0 | 1 | −1 | 2 | 1 | **1** |
| `steam_saw_mill` | one steam saw-mill | 1 | 2 | 1 | 2 | 0 | +1 | 1 | 0 | 0 |
| `iron_foundry` | one iron foundry | 1 | 2 | 0 | 2 | 0 | +1 | 1 | 0 | 0 |
| `storage_and_forwarding` | four storage and forwarding houses | 4 | 7 | 7 | 0 | 0 | +3 | 4 | 0 | 0 |
| `tavern` | eight taverns | 8 | 15 | 7 | 8 | 0 | +7 | 8 | 0 | 0 |
| `lottery_office` | one lottery office | 1 | 0 | 0 | 0 | 0 | −1 | 0 | 0 | 0 |
| `bank` | one bank | 1 | 0 | 0 | 0 | 0 | −1 | 0 | 0 | 0 |
| `church` | five churches | 5 | 4 | 3 | 1 | 0 | *not compared* | 5 | 0 | 0 |
| `school` | seven schools | 7 | 5 | 5 | 0 | 0 | −2 | 7 | 0 | 0 |
| `lawyer` | twenty-two lawyers | 22 | 18 | 18 | 0 | 2 | −4 | 15 | 2 | **2** |
| `physician` | fourteen physicians | 14 | 8 | 2 | 6 | 1 | −6 | 9 | 1 | **1** |
| `lyceum_and_reading_room` | a lyceum and reading room | 1 | 0 | 0 | 0 | 0 | −1 | 0 | 0 | 0 |
| `other` | *(not an enumerated class)* | — | 88 | 59 | 30 | 25 | — | — | — | — |
| `not_stated` | *(not an enumerated class)* | — | 3 | 3 | 0 | 0 | — | — | — | — |
| | | **118** | | | | | | **108** | **7** | **7** |

**The seven rows the book ordered are the seven it filled.** Six classes carried a quota and
every one of them is closed: two druggists, one silversmith, one brewery, two lawyers, one
physician.

Six rows need their own sentence, because in each of them a number that looks like a hole is
not one:

- **`lottery_office`, `bank`, `lyceum_and_reading_room` — documented zeros.** The town held
  none at the scene date and none is reconstructed. The census counts them in the autumn; the
  register names nothing for them at all, and a bank the sources are silent about is not built
  to close an arithmetic.
- **`school` — a shortfall two dated notices have already explained.** The register holds seven
  school-keepers and **two of them announce an opening after 1 July** (`business_charles_hunt_…`
  and `business_hiram_everts_…`, both named and dated in the crosswalk). Five stand at the
  scene date; the difference from the census's seven is those two houses, not a hole, so the
  book orders nought and says which is which rather than arriving at nought by luck. (T-1428.)
- **`lawyer` and `physician` — lines that count MEN, not premises.** Ordered in the counted
  unit, against the scene date's population bracket rather than the December return: the
  census counts 22 lawyers in a town of 3,297, the town model brackets 1 July between 2,353
  and 3,265 people, so the scene date holds between 15 and 21 of them and the book orders to
  the low end. Same for the 14 physicians → 9. (T-1418.)
- **`church` — not compared, and therefore not ordered.** § 4.

## 4 · The church row, and the quota that should never have been cut

**T-0988 rules that a church is a structure and not a trade**, so the crosswalk carries the
class `compared: false` — its census figure and the register's four congregations are not two
sides of one subtraction. `docs/RESEARCH/business-layer.md` had already settled the substance
of it in writing: *"The census counts five and the town holds four, and the fifth is not
invented … A fifth congregation on 1 July 1835 would need a source naming it. None reached
does."*

**The order book was cutting the quota anyway.** `business_buckets()` read `census_count` and
`town_records_at_scene_date` off the row and subtracted them without ever reading `compared`,
so the church bucket stood at `to_reconstruct: 1, filled: 0` — an order for a fifth church that
no ticket owed, that the roof programme does not carry (`structures/institutional_public/*` is
`to_build: 0` in all three divisions) and that the project had ruled against. It is why the
Businesses family's bar read **7 of 8** and could never have read full.

This report's own commit fixes it, in the book rather than in the row: a class the crosswalk
declines to compare is **carried**, with both figures and its owning ticket on it, and orders
nought. Two guards hold it — `an_uncompared_class_orders_nothing` among the book's invariants,
and a self-test that fires if a bracketed class is ever also ruled uncompared, since a bracket
*is* a comparison. A companion assertion checks that a compared class still orders its
shortfall (`druggist`, 2), so the guard cannot be read as an amnesty for every business row.
The businesses total moves from 8 to **7**, and the family reads **7 of 7**.

## 5 · The *Chicago American*, 15 August 1835

The nearer of the two counts, six weeks after the scene, and the one this band does **not**
order against:

> "There are now upward of fifty business houses, four large forwarding-houses, eight taverns,
> two printing offices, two book-stores, one steam saw-mill, **one brewery**, one furnace (just
> going up), and twenty-five mechanics' shops of all kinds."

| the American | the December census | the town at the scene date |
|---|---|---|
| four large forwarding-houses | four storage and forwarding houses | 7 |
| eight taverns | eight taverns | 15 |
| two printing offices | two printing offices | 2 |
| two book-stores | two book stores | 2 |
| one steam saw-mill | one steam saw-mill | 2 |
| **one brewery** | **two breweries** | 1 + 1 reconstructed |
| one furnace (just going up) | one iron foundry | 2 |
| upward of fifty business houses | *(aggregate)* | *(aggregate)* |
| twenty-five mechanics' shops of all kinds | *(aggregate)* | *(aggregate)* |

Two of those lines matter and the rest corroborate. **The twenty-five** is an aggregate with no
trades named, so it can bound a total and can never bound a row. **The one brewery** is a row,
and it is the tighter and nearer bound: it disagrees with the December count of two, against
which the book ordered *M. Quinn, brewery*. This band does not apply it — re-cutting an
order-book bucket on a run's own reading of a newspaper is a ruling made in the wrong place,
and the Sept–Dec crosswalk is the right one. So the record stands with the American printed in
its own `reconstruction.basis.note`, under **L258**, and a crosswalk that ever rules the
American in re-cuts the bucket and `--build` withdraws the record. That is the substitution
rule working exactly as T-1441 tooled it.

## 6 · The reconstructed firms, and what would retire them

**32 reconstructed business records stand at the scene date.** Seven of them fill the
enumerated-class buckets above; the other **25 carry `other`** — trades the December
enumeration does not count at all (T-1377's two free-Black houses among them), drawn against
the resident layer's trade heads rather than against a census line, which is why they appear in
no bucket in § 3.

| | |
|---|---:|
| reconstructed firms standing at the scene date | **32** |
| carrying a `replaceable_by` rule | **32** (all) |
| carrying a survival or backdating liberty | **0** |
| by ordering ticket | T-1419 15 · T-1408 4 · T-1424 4 · T-1418 3 · T-1184 2 · T-1185 2 · T-1377 2 |

The zero in that table is a reading and not an omission. `survival_required` and
`backdating_required` are the flags a **documented** house carries when it stands on 1 July
because nothing says it closed (L211) or because the only paper naming it was printed afterwards
(L232) — liberties taken with somebody else's evidence. A reconstructed house has no evidence to
take a liberty with; it is declared invented on its face, and the liberty it stands on is the
one that authorised its whole cohort.

Every one of them can be retired by a reading: `tools/substitute_reconstruction.py --dry-run`
takes a new attested or inferred house and prints the reconstructed records its `replaceable_by`
matches, with the retirement it would perform — redirect the id, carry the roof, free the
order-book row (T-1441, documented in `docs/PROVENANCE.md`). **That is the whole point of the
band**: the reconstructed town is a scaffold with a written demolition order on every piece of
it, not a set of inventions that harden into facts.

Seven liberties authorise the 32 between them, each restating the whole count rather than
narrowing its selector, so `businesses.records[reconstructed]` keeps saying how many
reconstructed houses of trade the town carries in total: **L254** two apothecaries' shops ·
**L255** two Black-owned firms · **L257** four boarding houses · **L258** a brewery and a
jeweller's shop · **L259** two law offices and a physician's room · **L260** two livery stables
and two lumber yards · **L262** fifteen service houses. 2+2+4+2+3+4+15 = 32.

The liberties the *documented* layer stands on are counted and agree with the compiler
(`tools/compile_liberties.py --check`, 266 liberties): **L211** 95 businesses standing because
nothing says they closed · **L232** 26 standing because the only paper naming them was printed
afterwards · **L218** 18 on a street a directory printed after 1835 · **L212** 19 seated on
reconstructed roofs.

## 7 · What this report does not close

- **Staff.** The businesses carry their proprietors and their clergy; `staff[]` is T-1189's, and
  the order book's `every_business_has_staff` invariant still reads "not yet measurable".
  T-1448 mints the shortfall and T-1449 closes the employment join.
- **Division.** Every business bucket is `unassigned` by division. The register carries a street
  where the paper printed one and no division at all; assigning premises to a division is
  T-1182's audit and T-1198's seating, and the bucket key carries the axis so they can fill it
  rather than re-cut the book.
- **The fifth church.** Not a hole, not an order, and not this band's to spend: if a source ever
  names a fifth congregation standing on 1 July 1835, it enters the layer as a reading and the
  crosswalk row can be ruled comparable then.
