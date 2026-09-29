# The bridge heads, and the ferry that was not there — research memo

**Record:** `data/yard/bridge_head_timber.json` · **Gate:** `tools/measure_bridge_head_timber.py`
**Written:** 2026-09-29 · **Ticket:** T-1763 (piece 4 of T-1207) · **Scene:** 1835 (target 1835-07-01)

T-1207's acceptance asked for two things at the crossings: *"the ferry landing and the North
Branch bridge head (`north_branch_bridge.md`, `south_branch_raft_bridge.md`) with their
furniture"*. One of them is built and one of them is refused, and the refusal is by the same
sentence that gives this project its bridge.

---

## 1. The ferry is refused, and Andreas refuses it

Chicago had ferries. The **Miller–Clybourn ferry** was licensed on 2 June 1829 to cross the
North Branch between Samuel Miller's house on the point and the Wolf Point Tavern on the west
bank — `docs/RESEARCH/miller_house.md` § 2 uses that route to settle which bank Miller's house
stood on, so the ferry is load-bearing evidence in this dataset already. **Mark Beaubien's canoe
ferry**, worked by rope, crossed the South Branch from the Point; `docs/RESEARCH/sauganash_hotel.md`
§ 7 has it.

Both are gone by the scene date, and the first one is ended in the same clause that starts this
record's first two piles. Andreas, transcribed at `chicagology_kinzie_bridge`:

> In the summer of 1832 Samuel Miller, **the original possessor of the old ferry scow**, built
> the first bridge over the North Branch.

The ferryman built the crossing that replaced his own ferry, three years before 1835-07-01, on
the alignment the North Branch Bridge record already stands on. The Sauganash memo reads
Beaubien's ferry the same way one branch over — *"probably superseded by the log raft bridge near
Lake Street"* by July 1835 — and grades that an inference rather than an attestation, which is
the right grade and is kept here.

**So a ferry landing at the forks would be a reconstruction of the wrong decade.** This project's
rule is that a reconstruction is invention *within bounds*; a landing for a ferry the bridge
beside it had replaced is invention against the evidence, which is a different thing. It is
refused on the record, in `refused[0]`, with these sentences.

**Two ferries are left open rather than closed**, because neither is this ticket's and neither is
read:

| ferry | where it is | why it is not here |
|---|---|---|
| the **Ferry** labelled on the Harrison 1830 plan of the river mouth | `docs/RESEARCH/fort_dearborn.md` § named ground | still on that memo's list of labels the plate gives *"a symbol and a label and no form"*, beside the Well and the Cultivated Field. A main-stem crossing at the fort, not a forks crossing, and the Dearborn Street drawbridge of 1834 is the question it has to be read against. |
| the free **Lake House ferry** | `chicagology_prefire112` | belongs to a hotel that broke ground in 1835 and opened in the autumn of 1836. `data/exclusions.json` already carries the building as a shell. |

## 2. What the heads get instead, and what attests it

Four piles of the crossings' own stock, one at each end of each branch bridge. The upkeep is
documented; the piles are not. The documented half is entirely made of citations the two bridge
records already carry on their phases, read for a different fact:

| date | what it says | what it gives this record |
|---|---|---|
| 7 Nov 1833 | a fine on *"every person who shall remove from either of the bridges in said town, any plank or any piece of timber belonging thereto"* | the corporation's first fortnight legislates about **loose bridge timber, by name**, as a thing that could be carried off |
| 4 Dec 1833 | the Board appoints Dole, Beaubien, Kimberly and Miller *"to make a contract with some person, for repairing the Bridges on the North and South branches"* | **both** these crossings under contract for repair, eighteen months before the scene date, in one instrument |
| 14 May 1834 | five dollars from anyone who rides or drives over a town bridge *"faster than a walk"* | the deck carries ridden and driven traffic, so a head is a place a team stops |
| 19 Aug 1835 | *"No person shall ride or drive on the side walk of the bridges in said town"* | the corporation is still legislating for these decks seven weeks **after** the scene date |

And the fabric is attested by the 1883 old-settlers statement both bridge records are built from:
*"stringers of heavy logs stretched from the abutments to the bents, and between the bents"*, and
*"on these stringers puncheons or split logs were laid for a floor."* A crossing of split logs,
carrying teams, repaired by contract and protected by name from having its timber removed, is a
crossing with stock at it.

**What is not documented is everything else** — that a pile stood at any of these four heads on
1835-07-01, how much stock there was, whose it was, how it was stacked. The record is graded
`reconstructed`, which is the grade this layer's water cart carries for the same shape of claim
(`docs/LIBERTIES.md` L227), and the liberty is L305.

## 3. The set-out is derived, and the side is derived too

No coordinate is added by this record. Each structure record's `position` and `footprint` give a
deck origin, a bearing and a **measured** length — the North Branch deck 71.83 m, the South Branch
55.96 m, both measured between the traced 1834 waterlines rather than chosen — so a deck END is
origin plus length along the crossing's own axis and nothing else. The committed heightfield of
`e1834_harbor_cut` confirms it: sampled along each deck, the ground is **+2.16 to +2.20 m at both
ends and under water everywhere between them**, which is the same fact the footprints were written
from, read back off an independently committed surface.

From each end, the rule is **6 m back along the axis, 6 m off the centreline**:

- the back-off puts the pile behind the abutment, on the ground the heightfield already grades
  down from the deck (+2.2 m) to the plain (about +1.0 m over 15 m);
- the offset leaves **4.48 m of clear ground** outside the attested 3.048 m roadway, so nothing is
  stacked on a way the corporation fined men for riding fast over.

**Which side is not a preference.** The rule takes the side whose committed ground is higher, so
no pile stands in a hollow. All four came out on the **north** side, which is a result of the
ground and not a rule — the margins are 0.30, 0.28, 0.65 and 0.56 m.

| head | deck end (local ENU) | ground | pile (local ENU) | ground | other side |
|---|---|---:|---|---:|---:|
| North Branch, west | (−117.50, 260.50) | +2.20 | (−123.50, 266.50) | +1.30 | +1.00 |
| North Branch, east | (−45.67, 260.50) | +2.16 | (−39.67, 266.50) | +1.34 | +1.06 |
| South Branch, west | (6.86, −178.07) | +2.16 | (0.83, −172.10) | +1.57 | +0.92 |
| South Branch, east | (62.82, −177.78) | +2.18 | (68.79, −171.75) | +1.19 | +0.63 |

`tools/measure_bridge_head_timber.py --gate` re-derives every one of those numbers from the
structure records and the heightfield and refuses the record if it has drifted; `--self-test`
breaks each assertion and proves it fires. `tools/check.sh` runs both. So a re-measure of either
deck, a re-trace of the waterline or a re-carve of the bank moves these piles or says why.

## 4. The stock's one real dimension

The stick is drawn **3.048 m** long. That is not chosen: it is the ten feet Cleaver and the 1883
old-settlers statement both give for the **width** of both branch bridges, and a puncheon is cut
to the width of the way it floors. So the stock is drawn at the length the deck it repairs would
take, and the gate holds the number against both structure records rather than against a constant
written here. The 0.2 m square section is this layer's own stick, unchanged from
`data/yard/lot_building_material.json`.

Four sticks across, three courses high — 0.8 m by 0.6 m by 3.05 m, eleven sticks a pile, 44 in
all. Deliberately small: nothing measures this, and the only two facts it has to be compatible
with are that it is stock for repairs rather than a yard's inventory, and that it stands where a
team turns. A larger pile would be a claim about how much timber the town kept. This one is a
claim that it kept some.

## 5. What else was refused at the heads

`refused[1..4]` on the record, in full. In short: **no pile at the Dearborn Street drawbridge** (a
third crossing with its own record, and the December 1833 repair contract names the north and
south branches and not it); **no sawn plank drawn as a board** (the ordinance says *"plank or any
piece of timber"* and this layer has no board primitive, so the plank half is cited and left
undrawn rather than misdrawn); **no toll house, keeper's shelter or bridge tender's hut** (nothing
puts a building at any head, and a shelter would be a structure record with no evidence to open
it); **no hitching posts, mounting block, rail or notice board** (all four plausible, none named
by any source, and a notice board would additionally invent the wording and letterform of an
ordinance's publication — T-1211 is where the town's posts, stoops and walks are dealt by a rule).

## 6. Open questions

| question | where to look |
|---|---|
| The Harrison 1830 plan's **Ferry** — where its landing was, and whether anything crossed there in 1835 | the plate at page-image level; `docs/RESEARCH/fort_dearborn.md` § named ground; the Dearborn Street drawbridge's own phases |
| Whether either branch ferry was still worked alongside its bridge | Cook County commissioners' ferry licences and bonds after 1832; the Chicago Democrat's own columns |
| Where the town actually kept its bridge stock | the Board's repair contract of December 1833, if the contract itself survives |
