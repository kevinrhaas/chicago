# Peter Pruyne against Peter Pryne — the count, and where the ground is

**Ruled:** 2026-09-15 · **Ticket:** T-1135 · **Domain:** `residents` ·
**Tool:** `tools/exhaust_tax_1833.py` · **Measurement:**
`data/research/civic/tax_1833_exhaustion.json` · **Ruling:**
`data/residents/card_merge_rulings.json` → `clusters` → `pruyne-pryne` · **Rule:** C14

Re-derivable end to end:

```
python3 tools/exhaust_tax_1833.py --report      # the three gates
python3 tools/exhaust_tax_1833.py --build       # re-measure and write
python3 tools/exhaust_tax_1833.py --check       # re-measure, diff, assert the invariants
python3 tools/exhaust_tax_1833.py --self-test   # the assertions, broken on purpose
```

---

## 1. The question, and who left it

The town held two cards one letter apart. `pruyne_peter` is Peter Pruyne the druggist:
with Edmund Stoughton Kimberly he opened Chicago's second drug store early in 1833, he
bought at the school-section auction that October, he married Rebecca Sherman on 20
August 1835, he polled in ward 1 at the first city election of 2 May 1837, and Fergus's
old-settler notices print him dead in November 1839. `pryne_peter` is a civic mint and
nothing else — `Pryne, Peter` on the tax list of 1833, the poll list of 1834 and the
poll list of 1835, with no trade, no dwelling, no origin and no family behind it.

T-1132 weighed the pair and **refused to rule it**, filing it `undecided` under U1 with
the question written out:

> Not a page but a COUNT, in C12's shape moved from the forename to the surname. […]
> That is a reading of the roll and not a rule, so U1 and the cards stay two. T-1135
> owns it.

It was right to refuse. The rule C9 would have needed is a page — the same publication
caught setting both spellings for one man — and no such page exists in this corpus. The
IRAD rolls print Pryne three times and Pruyne never; the deposited 1833-1835 Democrat run
prints the stem 239 times and every one of them is Pruyne; the ISA land register prints
Pruyne eighteen times and Pryne never. **The two bodies of evidence never touch.** What
was left was one letter, and T-1001 measured what folding on one letter costs.

## 2. The three gates

### A — does the roll have to carry him, and is the ground inside the line?

C12's second condition asks for an **independent non-name fact** putting the survivor on
the closed roll. The fact is ground, and it takes two committed readings to become one.

First, what the roll is. **The 1833 tax list is a property roll and not a residence
check** — T-1117's finding, settled out of the list's own membership rather than by
reasoning about tax law: its entry 110 is `Wolcott, Alexander`, a man three years dead by
1833, and what was taxed was the ground his probate carried. The list names **owners and
estates of ground inside the town**.

Second, where Pruyne's ground is. The Illinois State Archives tract register carries four
1833 rows of the stem, all four at the school-section auction of 22-25 October. Each is
placed on the block polygon T-0797 measured off J. S. Wright's 1834 survey, and each
polygon is tested — **all four corners, not a centroid**, because the lot inside the block
was never placed — against the ring `tools/measure_corporation_limits.py` resolves from
the Trustees' first village ordinance of 7 November 1833 (`chicago_democrat_1833_11_26`
`#c024`, tier 1, the corporation walking its own boundary corner by corner):

| row | date | as read | parcel | block | against the line |
|---|---|---|---|---|---|
| ls0322 | 22 Oct 1833 | PRUYNE P AND CO | BL97 | 97 | **inside**, 4/4 corners |
| ls0323 | 24 Oct 1833 | PRUYNE PETER | LOT1BL23 | 23 | outside, 0/4 |
| ls0324 | 24 Oct 1833 | PRUYNE PETER | LOT8BL23 | 23 | outside, 0/4 |
| ls0321 | 25 Oct 1833 | PRUYNE P | LOT3BL119 | 119 | **inside**, 4/4 corners |

The row the ruling stands on is **ls0321**, which T-0850 upheld to this survivor on the
PEARSONS H argument — the same register writes the purchaser out in full on four other
rows and the town holds no second Pruyne for the initial to belong to. Block 119 sits
north of Jackson, east of Jefferson and west of State: inside the corporation.

**The test discriminates, which is the only reason it is worth anything.** His own
fullest rows — lots 1 and 8 of block 23, bought under the register's clearest spelling —
fall *outside* the line, west of Jefferson. A gate that said yes to every parcel of his
would be saying nothing about any of them, and the measurement asserts that at least one
1833 row of his falls outside.

`PRUYNE P AND CO` is the firm and is not relied on: the crosswalk reads it as naming
`PRUYNE P` as a partner, but no ruling stands on it and none is made here.

### B — is any other entry left for him?

The exhaustion, over the **whole** 115-entry roll. Every entry is scored by the letters
between the surname it prints and `pruyne`:

| letters | 1 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| entries | **1** | 1 | 4 | 37 | 37 | 18 | 11 | 4 | 2 |

One entry stands within one letter and it is number 86, `Pryne, Peter` at line 138 — a
single deletion. The next nearest entry **on the whole roll** is number 85, `Price,
Jeremiah`, three letters away, printing a forename that is not Peter and carrying a card
of its own that this survivor is not. **Nothing stands in the gap.**

**Why the count is over the surname and not the forename.** C12 exhausts the bearers of
the half that agrees; transposed here, that would be the bearers of `Peter`. It cannot
close: **thirteen of the 115 entries print no forename at all** — Blinn, Bourison,
Church, Jameson, Kingsbury, Magill, Nale, Norton, Post, Sherman, Washburn, Weaver,
Whistler — so the roll never states how many Peters it holds. Each of those thirteen is
excluded on its surname instead, at five letters or more.

**The rule excludes; it does not fold.** Saying that `Beaubien` is not a printing of
`Pruyne` asks nothing of a reader's willingness to believe, where saying that `Pryne` *is*
one would ask everything. The count would read exactly the same way if the two strings
looked nothing alike, which is what makes it a count. What it is held to is the **gap**:
a second entry arriving anywhere between one letter and three reopens the ruling, and
`--check` asserts it has not.

### C — is a clerk caught distinguishing them?

D5 refuses a pair where one closed roll enters both spellings side by side, as the 1833
tax list does for John David and John Davis at its entries 23 and 24. The measurement
scores every committed source **text** in the corpus for the stem. Twenty carry it and
**none carries both**: the IRAD rolls and Genealogy Trails' republication of them print
Pryne only, and Fergus, Moses & Kirkland, the old-settler death notices, the Chicago
American and the whole Democrat run print Pruyne only. Only this project's own derived
files hold both, which is catching ourselves rather than a clerk, and they are not read.

The same split is what left C9 with no page. It cuts both ways and both are recorded.

## 3. What the rule is, and what it is not

C14 is C12 with its two halves swapped — there the surname agrees and the forename
varies, here the forename agrees and the surname varies. Four conditions, and dropping
any one leaves the card where it is. It is written rather than stretched out of C12
because C12's text reaches a forename only, and quietly reading it wider would have been
a rule change made by application.

**This is D7's answer, and D7 is where the pair otherwise lands.** T-1134 wrote D7 the
night before this ruling: the standing refusal for two cards one letter apart in the
surname with an identical forename, the corpus searched, and the two spellings standing on
instruments that never touch — *"a tax roll against a newspaper"* in its own words, which
is this pair precisely. All three of its conditions hold here. It is not applied because
D7's own reasoning says what displaces it — it refuses on the ground that *nothing reached
folds them*, and it says *"a later page reopens it"*. No page has turned up and none is
claimed. What reopens it is a count, which is admissible where a page is not for the same
reason it is admissible at all: it never weighs how alike the two strings look. **C14 says
to reach for D7 first**, and it requires a closed roll *and* a re-derivable fact putting
the survivor on it. Most one-letter pairs have neither and stay D7's.

**The argument this ruling does not use.** "He bought at the town's own school-section
sale, so he is the kind of man its tax roll carries" is T-1017's question, and T-1017
measured it and **refused** it: thirteen of the sale's 105 buyers carry a surname the
residents layer holds nobody of, only 50 of 105 carry an upheld match, and the sale prints
twenty surnames more than one way — with **PRUYNE — P, P AND CO, PETER — expressly among
them**. Admitting the weaker form here would have been that refusal reversed by momentum.
What is relied on instead is one step narrower and is geometry: where two named parcels of
his lie against a line the gate re-derives, with two more of his lying outside it.

## 4. The residual, which is not smoothed away

**The roll prints no day within 1833.** Nothing here dates the assessment, and if it was
taken before 22 October 1833 the ground argument reaches nothing. That end is *bounded*
and not closed: the Town of Chicago did not exist before 10 August 1833, and this corpus
holds no statement of its bounds earlier than the ordinance of 7 November 1833 — thirteen
days *after* the purchase that carries the ruling. So the roll is a roll of the town's
last months of 1833 at the earliest, and Pruyne stood inside its line for all of them.
That is an inference about the assessment's date; it is graded as one in the
measurement's `what_it_does_not_say`, and **a dated 1833 assessment turning up before 22
October reopens this ruling.**

## 5. What the ruling changes, and what it costs

- The town's cards fall by one and its persons from 1,305 to **1,304**. L220's civic-mint
  count falls 413 → 412.
- `pryne_peter`'s whole record is carried: its three roll appearances arrive on the
  survivor through the card-merge crosswalk, and the card itself is kept entire under
  `data/residents/merged/hh_pryne_peter.json` and redirected by `index.json`.
- **Nothing is promoted to make this tidy.** No grade moves, no dwelling is assigned, and
  `present_on_scene_date` is untouched: T-1117 already refused `tax_1833` as a leg of the
  presence bracket and that refusal stands, so the survivor is no more placed in the town
  on 1 July 1835 after this merge than before it.
- T-1132's `for_merge` and `against_merge` are kept verbatim on the standing ruling, and
  its `undecided` ruling moves into `withdrawn[]` with the reason — it does not vanish.

## 6. The ruling is gated, so it can be wrong out loud

Seven figures are **asserted** by `check.sh`, not merely printed: the roll is still 115
entries; exactly one of them stands within a letter of `pruyne` and it is number 86; the
next nearest is three or more away; some row of the register puts the survivor's own
upheld ground inside the limits; some 1833 row of his falls outside them; no source text
prints both spellings; and the corpus holds exactly two bearers of the stem, folded cards
included. All seven can move — the roll is re-derived by `read_voter_lists.py`, the ground
by `measure_corporation_limits.py`, and the corpus grows every week. If one flips the
build goes red and names which, and T-1135 reopens.

## 7. What was not done

- **No page was found and none is claimed.** C9 does not fire here and is not invoked.
- **`compatible()` is not widened.** T-1001's measurement of a blanket one-letter surname
  fold stands untouched, and nothing here is a licence to fold on a distance.
- **The other seventeen one-letter pairs are not ruled by this.** C14 needs a closed roll
  and a fact that puts a man on it; most pairs have neither.
- **`PRUYNE P AND CO` is not adjudicated.** The firm's row falls inside the line too and
  is printed, but the ruling rests on `PRUYNE P`, which carries an upheld reading already.
