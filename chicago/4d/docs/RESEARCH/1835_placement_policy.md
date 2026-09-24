# The placement policy of 1835 — who lived and worked where

**Ticket:** T-1195 · **Built by:** `tools/placement_policy_1835.py` ·
**File:** `data/reconstruction/1835_placement_policy.json` · **Target date:** 1835-07-01

The owner asked for this in one sentence:

> *"spread the businesses and residences and all other civic and other structures across
> the city correctly along lot lines and corners and lots … I think you will have multiple
> buildings per lot in many cases in the major streets and probably it's spread out
> naturally over time, do what you can to make the location of reconstructed businesses
> and residents as reasonable and accurate as a historian would."*

The project already held most of an answer, in six places, none of them readable as a
rule: the face rule's non-dwelling clause (T-0024 — a store never on a `light` street),
the end rule (T-0023 — the better roof nearer the drawbridge), the frontage-fabric ruling
(T-0022 — log trade buildings DO stand on principal streets), the density standard
(T-0079 — three party-line units per lot), the trade-share measurement (T-0213), and
ROADMAP K1's "businesses toward the river and the built streets, residences further out".
Three of those were modules that each re-typed the same numbers.

This document is the prose; the JSON is the contract. **No roof moves** — T-1195 writes
one file and never a structure.

---

## 1. What is authored and what is measured

The **clauses** are authored. They are this project's reading of how an 1835 lake town
arranged itself, and each carries a `tier` under the project's own provenance rule: a
`documented` clause must cite records, an `inferred` one must state its reasoning.

Everything printed **beside** a clause is re-read from the committed tree on every run —
how many of its cited records stand, the traffic class of the street each is nearest, and
the setbacks they keep. `tools/placement_policy_1835.py --check` rebuilds the file from
the tree and refuses any drift, which is what makes a clause a reading of the record
rather than a preference about frontage. `tools/check.sh` runs it.

## 2. The twelve clauses, and what the record puts behind each

```
clause                               tier          applies to             n  prin  ord  light  on-line
commercial_front                     documented    C1 C2 C3 C4 F1–F4     12    12    0      0       11
professional_row                     inferred      C1                     4     1    3      0        4
mechanics_streets                    documented    W1 W2 W3 W4            4     2    2      0        3
heavy_and_noxious_trades             documented    W5                     4     1    3      0        1
merchant_and_professional_dwellings  inferred      H1 H2 D7               2     1    0      1        0
tradesman_dwellings                  inferred      D3 D4 D5 D6            2     1    1      0        2
labourer_dwellings                   inferred      D1 D2                  3     0    2      1        1
lodging_near_the_landings            documented    T1 T2 T3 H3            8     4    4      0        7
farms_and_country_seats              documented    D1 A2                  4     0    2      2        0
institutions_stand_where_named       documented    I1 I2 I3               9     1    4      4        4
ancillary_behind_its_own_roof        documented    A1 A2 A3 A4 A5         4     1    1      2        1
garrison_reservation                 documented    M1                     4     0    0      4        0
```

`n` is how many of the clause's cited records the census can put on a street today; the
three class columns and `on-line` are re-derived on every build. Regenerate with
`tools/placement_policy_1835.py`.

**A letter may be covered by more than one clause, and the clauses are ALTERNATIVES.** A
D1 is a labourer's cabin under one clause and a pre-plat country place under another;
Clybourn's cabins are the second and not the first. A record conforms if any clause of its
letter accepts it. This is deliberate: the town of 1835 is two settlements and a plat laid
over them, and a policy that made the clauses a conjunction would have to call the older
settlement wrong.

### The load-bearing zero

`commercial_front` does not rest on an opinion about frontage. It rests on a count: **not
one documented store or warehouse in this town stands on a light street** — 0 of 15 and
0 of 9 when T-0024 measured it, **0 of 17 and 0 of 9 today**. An invented store on a light
street would be the first one in Chicago. The same reading gives the second half of the
clause: **14 of the 17 documented stores stand ON the street line** rather than back at a
dwelling's 4.0–7.5 m typology setback, and the three that do not are all off the platted
grid — Robert Kinzie's at the forks, the Miller house on the north bank, and the factor's
house inside the fort's fence.

### What the clauses say in one line each

- **commercial_front** — trade takes the built streets and the river front, corners first,
  on the line. C and F.
- **professional_row** — offices sit by the public square and the hotels rather than the
  river front, because their traffic is the town's own and not the lake's. *Inferred*,
  and the evidence is thin: the two printing offices and the auction room are on Clark
  and Dearborn within a block of the square, the old bank building is on Lake, and the
  1835 court house is cited for its position but credited no family, so it is not in the
  witness count.
- **mechanics_streets** — a shop needs to be found but not to have the best frontage in
  town: State, Dearborn and Clark south of Lake, the Canal Street approach, on the line,
  yard behind.
- **heavy_and_noxious_trades** — packing, tanning, slaughtering, soap-boiling go to the
  branches and out of the town's nose, on the water that carries the waste away. All four
  documented instances stand well off any platted street line.
- **merchant_and_professional_dwellings** — the better houses take the
  Randolph–Washington tier a block back from the trade, and the north tier under Kinzie.
  *Inferred*: the town holds one documented H roof, and it is Cobweb Castle, which is
  itself this clause's outlier.
- **tradesman_dwellings** — the frame cottages fall on the side streets behind the
  principal frontages, which is how a block parcel comes to deal its meanest roof to its
  worst street.
- **labourer_dwellings** — cabins and shanties take the small lots, the fringes and the
  ground nobody is bidding on.
- **lodging_near_the_landings** — an inn stands where the traveller arrives: the bridge
  head, the forks, the stage and wagon approaches, the lake landing — with its stable in
  the yard behind it.
- **farms_and_country_seats** — the places held before the plat stay where they were held.
  Beaubien's, Clybourn's, Robinson and Caldwell's. They are the reason the policy has to
  say "outside the plat" at all.
- **institutions_stand_where_named** — a public building nobody named is the claim that an
  institution stood here and left no record. `generate_block_infill.py` refuses the
  institutional families to a block parcel by name (L93), so this clause seats nothing: it
  records where the nine named ones stand so a future parcel cannot invent a tenth.
- **ancillary_behind_its_own_roof** — stables, privies, woodsheds and smokehouses go off
  the block alley behind the roof they serve. A rule about the LOT, which is why `A` is not
  one of the face rule's letters.
- **garrison_reservation** — the military reservation was unplatted and no street crossed
  it. A building inside the fence has no street frontage to take a better or worse face of.

## 3. Multiple buildings per lot

The owner's "multiple buildings per lot in many cases in the major streets", as a number:

| lot | rule | principal roofs | basis |
|---|---|---|---|
| principal street | `party_line_run` | up to **3** | the core density standard, T-0079: three party-line units per lot, each `party_line_unit_m` = 6.072 m wide, sharing side walls |
| back street | `one_principal_roof` | **1** | the dwelling typology setback and the block parcels' own arrangement notes — the lot is not subdivided |

The documented instance is **Wright's pair of buildings-to-let**, standing 5.00 m and
4.99 m off the Randolph line side by side on one frontage. The back-street rule is stated
as the complement: no documented back-street lot in this town carries two principal roofs.

## 4. The outliers are evidence

`--score` puts every documented roof against the clauses of its own family letter.
**55 of 77 conform; 22 do not**, and the 22 are not a fault in the record — they are the
record telling you something the clauses do not say. Each one carries a written reason in
the module, and **assertion 3 refuses an outlier nobody has explained**, so a new one
cannot appear silently. It also refuses a reason left behind by an outlier that has gone
away, which is how the explanations stay honest.

They fall into three groups, and every group is the same fact in a different place —
**the class printed beside a record is the class of the nearest committed centreline, and
for a quarter of this town that centreline is not a frontage at all**:

1. **The federal reserves** (6 records). No street crossed the military reservation in
   1835, so the fort's shop at 381 m from the State Street line, the factor's house at
   288 m and the out buildings at 312 and 323 m are not standing badly — they have nothing
   to stand on. The council house on the lakefront reservation and the lighthouse on the
   harbour reserve are the same case on different ground.
2. **Wolf Point and the north bank** (13 records). Robert Kinzie's store is 27 m from
   Lake's line because Lake ENDS at the river; the north-bank freight sheds, the brickyard,
   the tannery, the north-side school and Kinzie & Hunter's warehouse all front the WATER,
   which is what a forwarding trade wants, and the street class beside them is the
   south-side line across the channel.
3. **The north and west divisions' absent street control** (3 records). The Steamboat
   Hotel at
   203 m and the Watkins school house at 390 m from the State Street centreline front
   nothing this project has yet platted, and Walker's meeting house sits 48 m off Canal at
   the edge of what was. T-1191 and T-1192 are the tickets that seat those corridors, and
   when they land this group should thin.

That third group is a measurement of the project's own state, not of 1835, and it is
recorded here so that T-1191's effect on it can be seen.

## 5. One source of truth

Five numbers were typed into four modules under seven names. They are now in
`constants` and the modules import them:

```
street_line_m        2.71    STREET_LINE_M         measure_frontage_fabric
party_line_unit_m    6.072   PARTY_LINE_UNIT_M     measure_end_rule
trade_letters        C F W   TRADE_LETTERS         measure_frontage_fabric
                             LIGHT_STREET_ZERO     generate_block_infill
non_dwelling_letters CFTWI   NON_DWELLING          measure_face_rule
                             NON_DWELLING_LETTERS  generate_block_infill
commercial_letter    C       COMMERCIAL            measure_face_rule
```

**Assertion 5 reads each of those seven lines** and fails if one of them carries a literal
again. A single source of truth that nothing checks is a comment.

## 6. What this file does NOT gate

`prefers` is declarative throughout, and so is every `division:`, `lot:` and `ground:`
term in `avoids`. This project holds no committed lot-position field for a documented
record and no division index, so scoring them would be scoring an absence. Only two terms
are measured here: `class:*` in `avoids`, and `setback_class: street_line`. The seating
tickets — T-1198 and T-1199 — spend the rest, against the lot grid T-1194 generates.

**Links:** T-0022 · T-0023 · T-0024 · T-0079 · T-0213 · T-1191 · T-1194 · T-1198 ·
T-1199 · `docs/ROADMAP.md` K1/K29/K31/K32 ·
`docs/RESEARCH/1835_north_division_extent_and_infill.md` ·
`docs/RESEARCH/west_division_infill_1835.md` · L256.
