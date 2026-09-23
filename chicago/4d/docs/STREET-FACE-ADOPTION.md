# Street-face adoption — what a business does when the paper names a street and nothing narrower

**Status: policy, in force.** Recorded 2026-08-29 for T-0354, on the owner's ruling of the
same day, and **extended 2026-08-30 for T-0416 by his ruling that a corner side is a
face**. A later run applies this without re-deciding it; a run that wants to change it
opens a ticket and asks. The implementation is `tools/adopt_street_faces.py`, the derived
table is `data/research/newspapers/street_face_adoptions.json`, the liberty is **L212**,
and `tools/check.sh` re-derives both on every commit.

## The problem this answers

`data/research/newspapers/register_1835.json` reads 221 businesses out of the *Chicago
Democrat* and the *Chicago American* and finds 203 standing on 1 July 1835. It resolves
**58** of them to a building — 32 `enrich_existing`, where the advertisement's anchor names
a roof this project already holds, and 26 `new_building`, where it names a place precise
enough to raise one. The remaining **145** divide into two piles, and neither is a defect
in the register:

| pile | count | what the paper gives |
|---|---|---|
| `street_only` | **60** | a platted street and nothing narrower — "the east end of South Water-street" |
| `unplaceable` | **84** | no street this model holds — Flag Creek, "on the road to Ottawa", or no address printed at all |

Without a policy, the papers yield fifty-odd buildings. With one, they yield most of a
town. That is the whole of what is at stake here.

## The ruling

Asked what a business does when the paper names a platted street and nothing narrower, and
offered the three options T-0354 set out — adopt a standing roof, raise a new frontage
record with a conjectural along-street position, or wait for a corner — **the owner chose
adoption, 2026-08-29:**

> Adopt a reconstructed roof already standing on that street face and attach the business
> to it.

So they join the town on the streets their advertisements name, using roofs the
reconstruction programme has already raised there. Nothing new is built and nothing is
promoted.

## The four limits, and they are the whole of the care

**1. A STREET FACE, NEVER A LOT.** The paper's constraint is the face; the lot is the
reconstruction's. A record that says which lot a street-only business stood on has
asserted something no source carries. Every adoption declares `lot: null` and
`claims_lot: false`, and the gate refuses a record that has grown a lot field of any name.

*The plat may still be read.* `tools/fronting_street.py` asks the Thompson lot grid which
tier a footprint stands in, because that is what says which street a roof faces. **Reading
a lot to learn a frontage is not asserting that a business held that lot.** The distinction
matters and is the reason the gate checks field names rather than trusting the derivation.

**2. THE ROOF STAYS `reconstructed`.** Adopting it does not promote the building. The
business is documented; the building under it is not; the card must be able to say both in
one breath. This is the pattern **T-0264/#518 and L205** already set for a documented head
on a reconstructed dwelling — followed, not reinvented. The gate re-reads the adopted
structure's own phase and fails if its confidence has stopped saying `reconstructed`, so a
later pass that promotes one of these roofs cannot do it silently.

**3. THE ALONG-STREET POSITION IS THE RECONSTRUCTION'S, NOT EVIDENCE.** Which roof on the
face a business is given is an allocation, not a reading. Businesses are ranked by evidence
— most printings, then earliest sighting, then id — and paired with that face's free roofs
in id order. Deterministic, so it re-derives; and a statement about nothing, so it claims
nothing. Every record says so in its own note.

**4. ORDER WITHIN A FACE IS NOT A CLAIM.** If two street-only businesses land on one face,
neither is nearer the corner than the other on any authority. Every record carries
`order_is_a_claim: false`.

## What "already standing on that street face" means

`tools/fronting_street.py` answers the frontage question three ways, and they are three
different claims:

| reading | what it means | adopted? |
|---|---|---|
| `lot front` | the roof's platted lot faces this street. The plat says it. | **yes** — 2026-08-29 |
| `corner side` | the roof ends its tier and abuts this street on the SIDE; its front is the cross street | **yes** — 2026-08-30 |
| `centreline band` | the roof is off the platted grid, within 25 m of this centreline | no — declined 2026-08-30 |

### The narrow reading shipped first, and it refused the whole of Dearborn Street

For one day only `lot front` was adopted, on the reasoning that an advertisement's street
is where the door is. That refused **the whole of Dearborn Street**, which has eighteen
roofs showing it a corner side and not one whose lot fronts it, and T-0416 was opened to
put the cost in front of the owner rather than let the policy absorb it.

### The owner's ruling of 2026-08-30 — a corner side IS a face

> **Yes — a corner side is a face. The band is NOT added.**

**A corner building genuinely fronts two streets.** It has a side on each, and a business
advertising on either one is describing where its door is. Saying a corner roof stands on
BOTH its faces is a fact about a corner lot, not a weakening of the reading: nothing about
the roof changes, no geometry is raised, no building is promoted, and no lot is claimed.
Every limit above holds unchanged, and a corner adoption's own note says which face it
took — `face: "corner side"` on the record, and a card that reads "the roof ends its
platted tier against Dearborn Street" rather than implying the plat put its front there.

**The centreline band was considered in the same question and DECLINED.** A band is a
distance from a line and not an orientation: a roof 20 m from Dearborn's platted
centreline may show it a wall, a gable end or nothing at all, and no reading of the plat
can say which. It is recorded as declined in `reading.considered_and_declined` in the
derived table, with what it would have seated, so a later run does not re-open it as an
oversight. The gate refuses a record that reaches its street only that way, in both
`adopt_street_faces.py --self-test` and `inferred_occupancy.py --self-test`.

### What each reading actually seats — dealt, not estimated (T-0416)

`refused_for_want_of_a_face` counts the businesses refused **for want of any face** — how
many a wider reading would let back into the deal. **It is not how many one would seat**,
and quoting it as one overstates the ruling by half: those businesses still meet refusal 3
and refusal 4 afterwards, and the supply a wider reading adds is already net of refusals 5
and 6, because a corner-side roof can be a household's home or a privy exactly as a
fronting one can. So the tool deals every costed reading out in full, in
`reading.costed_readings` and under `--report`:

| reading | seated | against the reading in force | still refused | where the difference lands |
|---|---|---|---|---|
| lot front only | 30 | −10 | 31 | — |
| a corner side is a face — **in force** | **40** | — | 21 | Dearborn +6, La Salle +3, Canal +1 |
| a corner side **or the band** is a face | 40 | 0 | 21 | nothing further |

The absolute counts move as the register and the roofs do — they were 19 / 29 / 29 when the
ruling was made and are 30 / 40 / 40 today — and the table is re-derived on every rebuild,
so read the shape rather than the numbers: **the widening is worth ten shops and the band is
worth none**, and it has been all three times it has been dealt.

#### One roof, one business is counted TOWN-WIDE, not once per face (T-0422)

Under the narrow reading a roof reached exactly one face, so "spent on this street" and
"spent" were the same sentence. **The corner-side widening separated them**, and the ledger
that keeps them separate is the one this pass keeps: `allocate()` holds a single town-wide
set of spent roofs, and a corner building dealt to a La Salle advertisement is no longer
free to the South Water one whose platted lot it actually is.

It is not a hypothetical care. Every roof a corner-side reading adds to a face **already
fronts another street by its lot** — that is what a corner is — and dealt under the older
per-face ledger the widening today seats *forty-one* businesses on *thirty-nine* roofs:

- `recon_1835_blk_south_water_lasalle_d1_08` — James Grant, by La Salle's corner side, into
  the building Rockwell's cabinet furniture warehouse already holds by its South Water lot;
- `recon_1835_blk_south_water_lasalle_d2_09` — the unnamed *New Store, La Salle street*,
  into Samuel Lewis's.

So the per-face ledger prices the widening at **+11**, and eleven is wrong: the eleventh
shop is a second shopfront on a building that already has one. The reading in force spends
each roof once and prices it at **+10**.

**The counterfactuals are gated, because they are the numbers a ruling is made on.**
`reading.costed_readings` carries `would_seat_on_distinct_roofs`, `deals_a_roof_twice` and —
derived on every rebuild, so the difference stays measured rather than argued —
`per_face_ledger_would_seat` and `per_face_ledger_would_deal_twice`. `limits()` fails the
gate if a costed row's seat count ever runs ahead of the roofs it dealt, and `--self-test`
both breaks that gate to show it fires and deals all three readings under both ledgers to
show it is not vacuous. A wrong price on a decision the owner has not yet made would
otherwise never fail anything, because it is never adopted.

**The +12 measured when the question was asked is +10 once it is applied, and the
difference is a refusal the measurement could not see.** Refusal 5 refuses a roof
`data/residents/` seats a NAMED household in — and the inferred-household programme's 101
households are not in `data/residents/` under a name, so its roofs were invisible to this
pass and counted as free supply. The very first re-derivation under the widened reading
handed Elmira Fowler's Dearborn Street millinery `recon_1835_south_w4_032`, a roof the
inferred layer already holds, and `tools/inferred_occupancy.py` — the ledger that spends
both programmes into the structure records — raised on it, which is exactly what that
ledger exists for. Two of the twelve were that shape, and the refusal now covers both
layers (see refusal 5 below). **This is the same class of correction T-0417 made when it
found nine of the original twenty-four seated in privies: an allocation nothing consumes
is an allocation nothing checks.**

**And the band's one shop was of the same shape.** North Water Street's single band roof,
`recon_1835_north_c1_020`, is an inferred household's home too, so the reading the owner
declined would have seated nobody at all — not the Wm. Sabine the question named. The
declination cost nothing, which is a stronger answer than the one the ticket promised and
is recorded as such rather than glossed.

**Dearborn Street's eighteen advertisements are not eighteen shops.** Of the eighteen roofs
showing it a corner side, five are named households' homes, two are inferred households',
five are yard buildings, and six are free — so six are seated and twelve refused on supply.
That is refusal 4 doing its job, and **T-0375** is where more Dearborn frontage comes from.

## The six refusals

1. **`not present at the scene date`** — the register already excluded it: contradicted
   before 1 July 1835, or first printed after it.
2. **`the face holds no roof standing on it`** — since 2026-08-30 this is **North Water
   Street alone**, and it is now the narrowest refusal in the policy: no roof's lot faces
   it, no roof ends a tier against it, and its one roof in the centreline band is not a
   face. Dearborn, La Salle and Canal left this refusal when the corner side became a
   face. North Water waits on the reconstruction raising frontage there, which is
   **T-0375's** neighbourhood, and it is why **Wm. Sabine** and **John Dave** are still
   not seated.
3. **`this face already holds this proprietor`** — the corpus prints one house under more
   than one heading ("Peter Cohen" and "Peter Cohen's store"). One house, one roof per
   face; the better-evidenced heading keeps it. Matched on the **exact** normalised
   proprietor surname set and never on resemblance: whether a firm sharing one partner
   surname with a sole trader is the same house is **T-0338's** open question over
   thirty-one such groups, and a placement pass must not answer it by seating or refusing.
   Variant spellings escape it too, which **T-0408** measures.

   **And where the corpus HAS already ruled, the collapse obeys the ruling instead of
   re-deciding it (T-0414, 2026-09-05).** `data/research/newspapers/identity.json`
   § `refused_firm_merges` is where this project writes down that two headings are not one
   business, and a refusal of kind `two_houses` says exactly what the surname collapse
   would otherwise assume away. Inside a surname set carrying such a ruling the collapse
   keys on **(surname set, occupation)** rather than on the surname set alone — because
   the trade is the axis the ruling itself used. `identity.json` on W. Montgomery: *"a
   different trade, a different stand and eighteen months later."* Before this, refusal 3
   answered that identity question by refusing, and answered it *against* the corpus's own
   written ruling: L. W. Montgomery the bootmaker took the roof and W. Montgomery the
   auctioneer was refused for being called Montgomery.

   The rule is narrow in three ways on purpose. It admits a `two_houses` refusal **only
   when both headings' surname sets are equal**, because a refusal between "New York
   Clothing Store" and "Peter Cohen's store" is not about anything this collapse does.
   It reaches **five** surname groups in the register today — Curtiss, Kinzie, Montgomery,
   Mulford and Taylor — and every other surname is still keyed on the surname alone. And
   two headings of the **same** trade inside a ruled group still collide and one is still
   refused: whether the three surplus Montgomery auction headings are one house is the
   gazetteer's question, and this pass still does not answer it.
4. **`every roof on the face is spoken for`** — the supply ran out. This is a count, not a
   failure, and it is the number this policy exists to produce.
5. **the roof is a household's dwelling — under EITHER layer** — a refusal of a ROOF
   rather than a business. A roof some layer seats a household in is that household's
   home; hanging a documented store on it asserts a relation between two claims nothing
   supports. The documented tradesmen this leaves standing on South Water are **T-0375's**,
   and this policy must not quietly answer that ticket.

   **Both layers, since 2026-08-30, and until then it saw only one.** `data/residents/`
   holds the NAMED households; the inferred-household programme
   (`data/reconstruction/1835_inferred_household_programme.json`) holds 101 more that
   hypothesise an occupant from the town's arithmetic without naming anybody, and those
   have no resident record to be found by. Under the narrow reading it never mattered — no
   roof the inferred layer held had its platted lot on a street the register named — and
   the corner-side ruling made it matter on the first re-derivation. That the inferred
   household is itself an invention makes the refusal stronger, not weaker: seating a
   printed advertisement on top of it would assert a relation between a source and a
   hypothesis. `tools/inferred_occupancy.py` raises on the collision and always did;
   refusing it here is what keeps the table derivable rather than merely gated.
6. **the roof is a yard building** — the other refusal of a ROOF, and the one this policy
   shipped without. The anonymous parcels deal ANCILLARY roofs as well as principal ones —
   privies, stables, woodsheds standing behind a lot, `reconstruction.inventory_class:
   "ancillary"` on the record — and for one day this pass counted them as free supply. **Nine
   documented businesses were seated in outbuildings, and Peter Cohen, the best-attested
   shopkeeper in the corpus, was in a privy.** The rule against it is older than this policy
   and was already enforced one layer down: `tools/generate_block_infill.py` refuses to write
   an `occupants` block onto an ancillary roof, because "a yard building serves the lot it
   stands behind, and an adoption is a claim about who lived or worked in a building".
   **T-0417 found it by trying to SPEND the allocation**, which is the argument for spending a
   table rather than admiring it: an allocation nothing consumes is an allocation nothing
   checks. Four of the nine took a principal roof instead; five had none left on their street
   and joined refusal 4.

## What it moves, measured 2026-08-30

**Every number below is DERIVED, and none of it is authored.** `python3
tools/adopt_street_faces.py --report` reprints all of it from the register as committed, so
a figure that has gone stale shows as a disagreement rather than rotting quietly in prose.
The register moves — it was read six times while this policy was being written and the
`street_only` pile went 47 → 45 → 60 → 59 — and the POLICY does not move with it: the four
limits, the six refusals and the two readings of "face" the owner has adopted are unchanged
by any of that, which is the point of deriving the allocation instead of listing it.

Re-measured 2026-08-30 for the corner-side ruling. The two readings before it: **24 adopted
and 36 waiting** over a supply that counted sheds (before T-0417's refusal 6), then **19 and
40** on lot fronts alone.

| | | was, lot fronts only |
|---|---|---|
| `street_only` in the register | **59** | 59 |
| adopted a street face | **29** | 19 |
| waiting | **30** | 40 |
| — the face holds no roof standing on it | 2 | 24 |
| — this face already holds this proprietor | 10 | 9 |
| — every roof on the face is spoken for | 18 | 7 |
| `unplaceable`, outside this policy and still open | **76** | 76 |

Refusals 3 and 4 GROW as the policy seats more, and that is the shape a supply-bound deal
has: the ten new shops take ten roofs, so the next advertisement on that face is refused
for supply rather than for want of a face. Twenty-two of the thirty that wait are now
waiting on a ROOF and not on a reading.

`free` below is the supply this pass may actually take: roofs on an adopted face, less the
households' homes under either layer (refusal 5) and less the yard buildings (refusal 6).

| street face | ads | took | lot front | corner side | free | in band (declined) |
|---|---|---|---|---|---|---|
| South Water Street | 23 | 9 | 19 | 0 | 9 | 0 |
| Dearborn Street | 18 | 6 | 0 | 18 | 6 | 0 |
| Lake Street | 11 | 9 | 51 | 0 | 17 | 4 |
| La Salle Street | 3 | 3 | 0 | 8 | 3 | 0 |
| North Water Street | 2 | 0 | 0 | 0 | 0 | 1 |
| Canal Street | 1 | 1 | 0 | 3 | 2 | 0 |
| Randolph Street | 1 | 1 | 64 | 0 | 27 | 0 |

**The ten the corner-side ruling seated**, all of them on roofs that were already standing:
Cooley and Halsman (tailors), Fullerton & Botsford, J. B. Brown's grocery, J. L. Wilson &
Co., James Grant, Magie & Wilkinson, the New York Clothing Store, Pierce & French, S. Abell
(attorney and counsellor) and the unnamed new store in La Salle Street. **Dearborn Street
goes from nought shops to six**, La Salle from nought to three, Canal from nought to one.

**Where the rest wait, named rather than implied:**

- **North Water Street (2).** The last face with no roof standing on it under any adopted
  reading, and the reason **Wm. Sabine** and **John Dave** are still unseated. Its one roof
  in the centreline band is an inferred household's home, so even the reading the owner
  declined would not have seated them. Their answer is frontage — **T-0375's**
  neighbourhood — and **T-0416** says so on the record rather than closing over it.
- **Dearborn Street (12 refused).** Eighteen roofs show it a corner side: five are named
  households' homes, two are inferred households', five are yard buildings and six are
  adopted. So twelve advertisements are short of a roof, not short of a reading. The
  **Dearborn Street wine store** is among them, which is the third of T-0416's storefronts
  and is refused on supply under every reading costed. Two more Dearborn advertisements —
  the New York Clothing Store and W. H. Taylor's boot and shoe store — have their own
  tickets (**T-0385**, **T-0387**) that place them from an anchor and do not need this
  policy at all.
- **South Water Street (14 refused).** Nineteen roofs front it: five are households' homes,
  five are yard buildings and nine are adopted, so fourteen advertisements are short of a
  roof — seven a second heading of a house already seated, seven short purely on supply.
  **T-0375** is the ticket that notices South Water's reconstructed roofs are all a
  labourer's, and any roof it adds to that face is a roof this pass will take on its next
  re-derivation, automatically.

  **T-0375 closed refuted on 2026-08-29, and the reason belongs here because it is a cost
  of this policy rather than of that ticket.** It asked whether an inferred household could
  be reseated onto a South Water roof of its own family band so a documented tradesman
  could take it. **Not one roof on this face is free**, so taking two is one-for-one:
  re-deriving this pass with them marked as households' homes drops the town's adoptions
  from 24 to 22 and this face's from 14 to 12, evicting `E. L. Thrall` and `the New Store at
  the corner of Water and Clark streets`. **This face is exhausted, so every roof a
  household takes on it now comes out of a documented business.** One of the two is
  John Holbrook's own adoption, so the seat would evict the man it was meant to seat; and
  both men it would go to — L. W. Montgomery and John Holbrook — are already standing on
  this face under limit 3 above, which would have put them on the street twice. The remedy
  is unchanged and is T-0375's own: raise more frontage on South Water, and this pass takes
  it automatically.
- **Lake Street (2 refused)** — both a second heading of a proprietor already seated.

## The 84 `unplaceable` are NOT covered, and stay open

The ruling does not reach them and this policy does not extend it. Some are outside the
plat entirely — E. Wentworth's public house on Flag Creek, on the road to Ottawa — and
adopting a roof for them would put a business in a town it never stood in. Some simply
never printed an address. **T-0354's second half is still open**, and the honest answer for
these 84 today is that the corpus records them and the model does not hold them.

## How it is spent

This file and its table are the POLICY and the ALLOCATION. **The CARD is spent by
`tools/inferred_occupancy.py` (T-0417)** — the ledger the anonymous-infill generators
already read for the inferred-household programme. It turns each adoption into the
`occupants` block the owning generator writes onto that roof, so `generate_block_infill.py
--check` re-derives it byte for byte and no generated record is ever hand-edited. It
re-asserts limits 1, 3 and 4 at the point of spending rather than trusting the table, it
refuses a record whose `face` is the reading the owner declined, and it raises if a roof is
claimed by both programmes at once; `tools/check.sh` runs its self-test. **A card names the
face it took**, in the roof's own words — "the roof's platted lot faces South Water Street"
for a lot front, "the roof ends its platted tier against Dearborn Street, so it is a corner
building" for a corner side — because the two are different claims and the visitor is owed
the difference.

Nothing here writes a SIGNBOARD or a frontage, and that is not an oversight:
`tools/generate_business_signboards.py` refuses a `recon_*` record by name, so a board on
one of these roofs would be a change to the signage rule and needs its own argument. The
frontages are **T-0263's** and the seeding tickets'.

## Two more houses reached the policy on 2026-09-04 (T-0440)

The population this policy works on is the register's `street_only` businesses, and that
population is set by what the gazetteer holds as a house's LIVE placement. Until T-0440
that was whatever the earliest printing the corpus carries happened to say, so a firm whose
opening notice gave no address stood at `{"class": "none"}` for good and never reached this
table at all. Thirteen houses were repaired; two of them name South Water Street and take a
face here.

| | before | after |
|---|---:|---:|
| `street_only` in the register | 58 | **60** |
| adopted a street face | 35 | **37** |
| refused, all four reasons | 23 | 23 |
| `unplaceable` at the scene date | 76 | **73** |

**Clark, Filer & Co.**'s cabinet warehouse and **Rockwell's cabinet furniture warehouse**
are the two, both on South Water Street, and the face absorbed them without evicting
anybody: the businesses naming that street went 22 to 24, the adoptions on it 15 to 17, and
no refusal count moved. What DID move is which roof each business on that face holds,
because the allocation is an ordering and two new entrants shift the ones below them —
eleven roofs carry a different name and two that were anonymous now carry one. That is the allocation working as documented (limit 3: the order
on a face is not a claim), and it is recorded here because a reader diffing the roofs will
see eleven changes for two additions and should not have to guess why.

A future pass that spends an adoption some other way reads `street_face_adoptions.json`,
takes `structure_id` and `cites`, and carries limits 2, 3 and 4 into whatever it writes: the
roof stays reconstructed, the along-street position is not evidence, and the order on a face
is not a claim.

**Related:** T-0354 (this) · T-0416 (the corner-side ruling of 2026-08-30, and refusal 5's
second layer) · T-0417 (spent into the roofs, and refusal 6) · T-0262 (the
register) · T-0263, T-0384–T-0387 (the seeding) ·
T-0375 (South Water's roofs) · T-0440 (the live placement that decides who reaches this
policy) · T-0338, T-0340, T-0408 (identity) · L205, L212 ·
`docs/PROVENANCE.md` · `docs/LIBERTIES.md`
