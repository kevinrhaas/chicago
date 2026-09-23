---
id: T-0987
title: The directories' ties and refusals, adjudicated one stretch per run — the 196 ties surname-plus-initial cannot decide, the 1,100 initial-absent refusals a page image can overturn, and every trade and 1839-44 address that lands spent onto the card and the street face; the run that closes this files the next stretch before it closes
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-09
closed: 2026-09-14
pr: 1345
claimed_by: run 9/14/2026, 6:28:50 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T00:25:23.155Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34908758559
---

**OWNER, 2026-09-10: "Directories as a succession ticket at the end of band 1."** This is the
open-ended-programme shape `tickets/README.md` describes: one unit, worked one stretch per run,
and **the run that closes a stretch files the next one's ticket before it closes** (T-0028 is
the worked example). It never closes on "there was nothing left" — it closes when the pools
below are empty, and says so with the counts.

**OWNER, 2026-09-14, AMENDING BOTH HALVES OF THAT — the closing condition and the unit of
work.** Asked how many more runs this would take, the answer was measured rather than
estimated, and it was bad: fourteen stretches in, the pools stand at 1,807 and the largest
has moved 6 %.

| pool | at filing | 2026-09-14 | change |
|---|---|---|---|
| ties the rule cannot decide | 196 | **52** | −144 |
| initial-absent refusals | 1,100 | **1,032** | −68 |
| forename-disagreed refusals | 142 | **194** | **+52** |
| could-carry trades and addresses | — | **529** | — |

The ties pool is nearly spent and that is the programme working. The other three are not,
and one of them GREW: stretches 10-14 were reader repairs — the surname the crosswalk
cannot see, the separator set as a point, the age read as a surname, the whole printed name
nothing had read past its first letter — and reading the page better finds more
disagreements than it settles. A programme that can add to its own backlog faster than it
drains it does not close on an empty pool, however long it runs. At the observed rate the
initial-absent pool alone is about two hundred more stretches.

It is still WORTH DOING, and that was measured too: **1,175 of the town's 1,308 people
(90 %) carry `occupation: none_recorded`**. The directories are the source that can fix
that, and 483 rulings have already carried 212 facts onto 234 people. The value is real;
the METHOD was the grind. So two things change and the goal does not:

**1. IT CLOSES ON YIELD, NOT ON AN EMPTY POOL.** When a stretch carries fewer than **five**
new facts onto cards, the seam is exhausted: close this ticket and write the final counts
and the unspent remainder into it, exactly as clause 4 already requires. An unemptied pool
is then a STATED liberty and not a silence — "surname present, printed initial absent:
N refusals not individually overturned, and why" — which is the answer this repository
prefers to an absence anyway.

**2. THE UNIT OF WORK IS A PAGE, NOT A NAME.** One page-image read per refusal is what
makes the initial-absent pool cost two hundred runs; the same image carries dozens of
entries. A stretch against that pool reads a PAGE and overturns every refusal on it,
reporting how many the page settled. Nothing about the evidence standard changes — each
overturn is still `scan_verified` and still names its leaf.

## What the directories are, measured, so the work is the right work

Fergus 1839, Fergus 1843 and Norris 1844 are **transcribed in full** — 8,258 claims across
eleven files, every page declared in `data/research/directories/coverage.json`. Nobody has to
read a page to start. `measure_research_spend.py` reads them as 8,258 read, 1,029 spent, 7,229
unspent, and the unspent seven thousand are not a backlog: they are entries whose surname has
no 1835 counterpart — people who arrived after the scene date — and the crosswalk cannot reach
them by construction. **Do not file a ticket to "read" them.**

What still has yield is three smaller pools the three crosswalks already name, and every unit
in them is a person of 1835 who may gain a trade, an 1839-44 address, or both:

| pool | where | count |
|---|---|---|
| **ties** the surname-plus-initial rule cannot decide (ambiguous + contested) | `fergus_1839_crosswalk_1835.json` residents 46+32 · `fergus_1843_crosswalk_1835.json` 41+17 · `norris_1844_crosswalk_1835.json` 23+16 · `norris_1844_advertiser_crosswalk_1835.json` 8+13 | **~196** |
| **initial-absent refusals** — surname present in 1835, the printed initial not | 276 · 349 · 335 · 140 in the same four files | **~1,100** |
| **forename-disagreed refusals** | 94 · 48 | **~142** |
| **could-carry** trades and addresses on matched entries | 1839: 98 trades, 96 streets · 1843: 83 addresses (trades read 0 until **T-0867** fixes `none_recorded`) · 1844: 63 trades, 73 addresses | **~410** |

T-0696 (landed) is the rule for the ties: **a trade may narrow a tie, a premises may not**, and
a narrowed tie is filed `discriminated`, never promoted to a match. T-0900 (band 1, above) is
one initial-absent refusal being overturned off the page image — that is the shape of the second
pool's work. `tools/back_project_addresses.py` (T-0633) and `tools/back_project_residences.py`
(T-0669) are how an address that lands becomes a **street face** — never a lot, never a roof —
and their refusals are readings, kept in full.

## A stretch

One run takes ONE bounded stretch and finishes it: a letter range of one directory's ties, or
one refusal class on one directory, or the could-carry pool of one directory once T-0867 lands.
Name the stretch in the claim commit. A stretch is done when every unit in it carries a ruling —
match, `discriminated`, or a refusal that names its clause — and everything that landed is
spent: the trade onto the card under the 1835/`later_occupation` rule T-0837 gated, the address
through the back-projection as a face.

**Order the stretches by yield, and say the yield.** The ties first (a tie is one page-read
from a match); then the initial-absent refusals of the directory whose scan is best; then
could-carry once its normaliser is fixed. The forename-disagreed pool is last — T-0670's
refusal is usually right.

## Acceptance — per stretch, one demonstration

1. The stretch is named, bounded, and every unit in it is ruled — nothing in it is left silent.
2. Every match or `discriminated` outcome cites the printed line (`quote`) and the 1835 card,
   and every refusal names its clause. A page-image read that overturns a refusal is
   `scan_verified` and says which leaf.
3. **Every trade and address that landed is spent in the same run** — the card carries it, the
   face is placed or the back-projection's refusal is recorded — and
   `measure_research_spend.py` shows the directories' `unwritten` column at 0 afterwards.
4. The three crosswalk `counts` blocks are re-derived and the PR body quotes the pool sizes
   before and after, so the programme's remaining size is always the last PR's number.
5. Gates green; the changelog entry says what a visitor can now see — a trade on a card, a
   business on a face — or states plainly that this stretch placed nothing and why.
6. **Before closing, file the next stretch with `ticket.mjs new "…" --after T-0987`**, naming
   its pool and its count from step 4. Do not file more than the next stretch; this ticket is
   the programme and the next stretch is its cursor.
7. **THE CLOSING TEST IS YIELD** (owner, 2026-09-14, amended at the head of this ticket).
   Close this ticket instead of filing another stretch when EITHER every pool reads 0 — the
   original condition, still good — OR this stretch carried **fewer than five** new facts
   onto cards. Write the final counts AND the unspent remainder into it: a pool left
   standing is a stated liberty, named with its size and its reason, never a silence.
8. **A STRETCH AGAINST THE INITIAL-ABSENT POOL READS A PAGE, NOT A NAME.** The same image
   carries dozens of entries; one read per refusal is what made that pool cost two hundred
   runs. Report how many refusals the page settled. The evidence standard is unchanged —
   each overturn is `scan_verified` and names its leaf, per clause 2.

## What this is not

Not a reading of the 7,229 post-1835 entries (no 1835 person to reach). Not a change to the
matching rule (T-0670, T-0696 stand). Not lots or roofs (L218, L223: a face). Not the Newberry
index, which is its own epic at the foot at a measured 0.0% match.

## Added by T-0989, 2026-09-10 — the 255 acceptance clause 3 is now measuring

Clause 3 above asks for `measure_research_spend.py`'s directories `unwritten` column at 0
after a stretch lands. Until this date that column read 0 for a reason that had nothing to do
with this programme: the second hop judged a ruling stating no source of its own against the
ONE source id at the top of its file, and counted the card as having learned it if the card
cited that id **anywhere, for any reason**. Every ruling in a generated crosswalk shares that
id, so one citation left by another pass passed all of them at once.

T-0989 closed that. A fallback ruling must now also NAME what it adjudicated — the read unit
it cites, or the sheet a sheet-and-line ruling sits on — and directories fell from **914 of
914 written to 659, with 255 unwritten**. That 255 is recorded in the write ceiling with its
reason; it is this programme's debt, and clause 3 is the thing that pays it down. Where it
sits, by file:

```
  159  fergus_1839_crosswalk_1835.json            all 159 — no entry named on the card
   49  fergus_1843_crosswalk_1835.json            of 120
   31  norris_1844_crosswalk_1835.json            of 99
   16  norris_1844_advertiser_crosswalk_1835.json all 16
```

The four sister files — the 1839 election, lots and register crosswalks, and the 394 rulings
in `spend_crosswalk_1835.json` that state their own sources — already reach their cards and
are unmoved. The instance checked by hand: `hh_garrett_a` cites `fergus_chicago_directory_1839`
because a later resident-research pass wrote a generic `directories` block on the card, while
Fergus 1839's ruling for Garrett — entry `f1839_e0527`, "Garrett, Augustus, auctioneer, real
estate, bds. Sauganash Hotel", printed page 15 — has never been written onto it. Nothing was
lost by the change; what was lost had already been lost, and was being reported as green.

A stretch that lands under clause 3 should quote the 255 before and after, the same way
clause 4 quotes the pool sizes.

## Stretch 1, 2026-09-11 — the write debt, paid in full: 263 → 0

**The stretch:** not a pool of ties but clause 3 itself. The 255 T-0989 exposed had grown
to **263** by the time this run measured it, and every other stretch's acceptance runs
through that number: clause 3 asks for the directories' `unwritten` column at 0 *after*
the stretch lands, and no stretch of ties could have reached 0 while 263 rulings that had
nothing to do with it sat unwritten. So the debt was taken first, as one unit.

**What the 263 were.** All of them, in all four files, were the same defect and none of
them was a reading:

```
  158  fergus_1839_crosswalk_1835.json             matches   card lacks the subject
   49  fergus_1843_crosswalk_1835.json             matches   card lacks the subject
   39  norris_1844_crosswalk_1835.json             matches   card lacks the subject
   17  norris_1844_advertiser_crosswalk_1835.json  matches   card lacks the subject
```

`tools/spend_directories.py` wrote the volume into the card's `directories.sources` and
the printed line into a note — but never the ENTRY ID. `card_block` is documented as
"deliberately thinner than the layer" and dropped the `claim_id` that `graded()` had
already computed; and for the 92 people the pass rules on and carries nothing for
(ambiguous or contested: no graded value, so no note at all) the card said only that
some volume had met somebody of the name. So the citation was doing the work of a
reading, exactly as T-0989 described for `hh_garrett_a`.

**The fix, in one place.** The block's own `note` now ends by naming, per person and per
volume, the printed entries this pass ruled onto that household and the status it ruled
them at. `hh_garrett_a` now reads:

> … garrett_a, Fergus's Chicago directory of 1839 — f1839_e0527 (a single entry);
> garrett_a, Fergus's Chicago directory of 1843 — f1843_e0109, f1843_e0110, f1843_e1051
> (ambiguous, so nothing crossed); garrett_a, Norris's Chicago directory of 1844 —
> n1844_e0679 (a single entry); garrett_a, the advertising cards in Norris's directory of
> 1844 — n1844_ad0110, n1844_ad0111, n1844_ad0112 (ambiguous, so nothing crossed).

It went into the NOTE rather than a new leaf on purpose: the note is already rendered
whole by `residents.js` and already declared `shown` in `measure_layer_reads.py`, so the
entry a reader would go back to arrives in front of that reader instead of into a field
nothing opens — and it is the only place that can speak for the 92 silent rows.

**Measured, before and after** (`tools/measure_research_spend.py`, whole town):

| | before | after |
|---|---|---|
| directories, on a card | 669 of 932 | **932 of 932** |
| directories, unwritten | **263** | **0** |
| town total, unwritten | 263 | **0** |
| on the file's word (the softer door) | 266 | 529 |

`unwritten_ceiling.directories` is tightened 264 → 0 in the same commit, so it cannot
regrow. **Every domain in the town now reads 0 unwritten**, and clause 3 is a gate a
stretch can actually pass rather than a debt it inherits.

**The pools are untouched and are what stretch 2 takes** — the ~196 ties first, as this
ticket orders them. No successor ticket is filed: `tickets/README.md` puts the succession
on the run that CLOSES the programme, and the owner's filing rule of 2026-09-10 asks for
fewer tickets, not one per stretch. This ticket stays open and is its own cursor.

## Stretch 2, 2026-09-11 (PR #1128) — the advertiser's ties: 14 ruled, 3 released, and the 64 silent refusals

**The stretch:** the ties of `norris_1844_advertiser_crosswalk_1835.json`, the smallest of the
four pools and the one stretch 1's claim had named before it took the write debt instead. Every
tie in it now carries a ruling; nothing in the stretch is silent.

**What was in it, and what a tie turned out to be.** The pool measured 3 ambiguous + 11
contested = 14. Three of the eleven contests were not contests. The generator keyed the contest
on the CARD:

```python
claimed[m["cards_1844"][0]["claim"]].append(m)     # the card, not the name on it
```

An advertising card is a FIRM's, and a firm's card names its partners. `n1844_ad0046` prints
"A. Loyd" and "H. A. Blakesley" over one grocery at 101 Lake street; `n1844_ad0116` prints
"William B. Ogden" and "William E. Jones" over the North-Western Land Agency. Keying on the card
made rivals of the partners — of men the card itself says stood in business together — and
withheld three matches the surname-plus-initial rule had already made. The key is now
`(claim, proprietor_as_printed)`, which is the only pair two readings can actually contest.

| | before | after |
|---|---|---|
| matched one card | 17 | **20** |
| contested | 11 | **8** |
| ambiguous | 3 | 3 |
| refusals (surname present, initial absent) | 130 | 130 |

Released: **Alexander Loyd** and **Harvey A. Blakesley** (Loyd, Blakesley & Co., grocers, 101
Lake street) and **William B. Ogden** (North-Western Land Agency, Kinzie street east of
Dearborn). The eight that remain are all one printed name read two ways — two Smiths on
"E. Smith", two Clarks on "J. Coe Clark", two Taylors on "Chas. Taylor", and the two Joneses on
the "William E. Jones" that stood under Ogden, who was never their rival.

**Every tie was offered the discriminator, and the offer is recorded.** The advertiser crosswalk
was the one of the four that never imported `tiebreak` — T-0696's ruling had no reach here at
all. It does now, on both shapes of tie, and it fired on none of the eleven:

```
ties_offered_the_trade_discriminator  11
ties_narrowed_by_a_trade               0
```

Nine of the eleven sides carry `none_recorded` in 1835, and a trade that names no side leaves
the tie standing (T-0696 term 2). The two that do carry one do not agree with what was printed:
Charles Taylor is a **carpenter** in 1835 against a "fashionable tailor" card, and Gurdon
Hubbard a **packer** against a forwarding merchant's and an insurance agency's. Neither is a
narrowing and neither was made into one. **This stretch placed nothing on the ground** (clause 5)
— an 1844 advertisement is evidence about 1844, and all three released men already carry an
earlier trade and address from Fergus 1839, which keeps them under the precedence rule.

**The 64 silent refusals, which clause 2 found.** `spend_directories.py`'s ledger says of itself
that "a refusal is declared as explicitly as a carry — the absence of one reads like a pair
nobody has looked at yet", and then wrote `why_refused: null` on **64 of its 161 refusals**,
including all three of this stretch's new matches. Only the untrusted-parse refusal had ever had
a reason. Each refused field now names its clause and the volume that beat it — the
earliest-volume precedence rule, stated at the head of `VOLUMES` and never carried onto a
ruling until now — and a `--self-test` invariant holds it:

| | before | after |
|---|---|---|
| rulings refusing something | 161 | 161 |
| …naming no clause | **64** | **0** |

**Measured** (`tools/measure_research_spend.py`): directories on a card 932 → **938 of 938**,
`unwritten` **0 → 0**. Clause 3 holds. No 1835 grade moved (`grades_1835_changed: 0`), and all
four crosswalks re-derive.

**The pools after this stretch**, for the next one to take:

**re-derived from the four files today, not copied from this ticket's 2026-09-09 table, which
had drifted** — ambiguous + contested, residents only:

| pool | before | after |
|---|---|---|
| ties, Norris 1844 advertiser | 14 | **11, every one ruled** |
| ties, Norris 1844 proper | 33 | 33 |
| ties, Fergus 1843 | 55 | 55 |
| ties, Fergus 1839 (`residents` block: 44 ambiguous + 29 contested) | 73 | 73 |
| **total ties left in the programme** | 175 | **172** |
| initial-absent refusals, four files | 276 · 349 · 335 · 130 = 1,090 | unchanged |

No successor ticket is filed, for the reason stretch 1 gave: `tickets/README.md` puts the
succession on the run that CLOSES the programme, and the owner's filing rule of 2026-09-10 asks
for fewer tickets. **Stretch 3 is the Fergus 1839 ties — 73, the largest pool and the volume
nearest the scene** — and it should check first whether that crosswalk, like this one, has never
been offered the discriminator at all: `tools/crosswalk_fergus_1839.py` does not import
`tiebreak` either, so T-0696's ruling still has no reach over the biggest pool of the four.

## Stretch 3, 2026-09-11 — Fergus 1839's ties, and the rule that had never been run on them

**The stretch:** the ties of `fergus_1839_crosswalk_1835.json` — 44 ambiguous and 29
contested, 73 of the 172 the stretch above re-counted, and the largest of the four pools.
This is the stretch the run above nominated, down to the reason it gave: "it should check
first whether that crosswalk, like this one, has never been offered the discriminator at
all." It had not. Bounded to one directory's resident ties; nothing was read off a page
image. Worked in parallel with that run, which is why the Norris advertiser pool it took is
untouched here.

**What was actually wrong, found before anything was ruled.** T-0696's discriminator and
T-0670's forename rule are both landed, both gated in `check.sh`, and both imported rather
than restated — and NEITHER had ever been wired into `tools/crosswalk_fergus_1839.py`.
`crosswalk_fergus_1843.py` and `crosswalk_norris_1844.py` import them; the 1839 file
imported only `trade_recorded`. So the largest tie pool in the programme had never met
either ruling.

Running the discriminator FIRST, before the forename rule, is what showed why the order
matters. It narrowed 8 of the 73 ties, and two of the eight were wrong in the same way:

> `Taylor, Augustin Deodat, carpenter and builder, 74 Lake st` was named for **both**
> Anson H. Taylor and Augustine Deodat Taylor, each an attested 1835 carpenter. One
> printed line, two people of 1835 — which is the CONTESTED shape the matching rule
> refuses by construction, manufactured by a discriminator weighing a line whose own
> forename contradicts one of the two names.

`Madore Benjamin Beaubien` was the other: narrowed onto `Beaubien, Medard B., merchant` on
a trade agreement, across a forename disagreement T-0670 refuses outright. Medard Beaubien
is a third card this town holds (T-1026).

**So the guard landed first, and the ruling second.**

1. `name_agreement.py` (T-0670) is applied to the residents pool: **75 refusals filed**,
   0 against a garbled reading, 39 residents left with no 1839 entry at all by it. The
   refusals are in `residents.forename_refusals`, each naming its clause and both
   forenames. Scope is the residents pool only — `forename_rule_scope` on the file says
   why: the three list pools mint nobody here and belong to T-0513/T-0514/T-0515.
2. `tiebreak.py` (T-0696) then reads what is left: **4 ties narrowed by a trade**, 30 left
   standing with `discriminator` stating on the record why the trade named two sides or
   none. Every one of the 34 surviving ties carries a ruling; nothing is silent.
3. A third gate is added because the invariant is worth keeping after its cause is gone:
   a narrowing may not name one printed line for two people of 1835. It reads 0 now that
   T-0670 runs first, and `narrowings_withdrawn_as_a_collision` is where it would show.

**Measured, before and after:**

| | before | after |
|---|---|---|
| resident ties (ambiguous + contested) | 44 + 29 = **73** | 22 + 12 = **34** |
| resident matches | 158 | **158** — 22 withdrawn, 22 arrived |
| forename refusals filed | 0 (rule not run) | **75** |
| ties narrowed by a trade | 0 (rule not run) | **4** |
| business street faces (L218) | 15 | **18** |
| residence street faces (L223) | 8 | **6** |
| directories `unwritten` (clause 3) | 0 | **0** |

**What a reader can see.** Three businesses of 1835 reach a street they had no position
on: **Mark Beaubien** on Lake Street, **James Kinzie** on Canal Street, and **Richard J.
Hamilton**, clerk of the circuit court, on the Clark and Randolph corner Fergus prints —
all carried four years, the narrowest gap in L218's set, and all three had been sitting in
the tie pool. Going the other way, **Charles L. Bristol**'s card loses the 1839 trade
`canal contractor`, which was read off `Bristol, Calvin, canal contractor` — the exact
instance T-0670's own docstring names as the defect it was written for — and
**`jones_es_high`** loses a Randolph Street house that stood on `Jones, Hiram`. The rule
gives where the printed name is the man's and takes where it is not, and both directions
are the same measurement.

**The pools after this stretch**, for the next one to order itself by:

```
  ties                        34 (1839, was 73) · 58 (1843) · 39 (1844) · 21 (1844 ad)  = 152
  initial-absent refusals    277 · 349 · 335 · 140                                     = 1,101
  forename-disagreed          75 (1839, NEW — the rule ran) · 94 · 48                  = 217
```

**Stretch 4 is the 1839 volume's could-carry pool, 92 trades and 96 streets on matched
entries** — the third of this ticket's four pools, now that the matched set it is drawn from
has been corrected rather than merely counted, and `trade_recorded.absent` (T-0867) is the
predicate that says which of them the 1835 layer has room for. The ties that remain are 34
here, 58 in Fergus 1843, 39 in Norris 1844 and 11 in its advertiser cards: 142, each one
carrying a written reason. No successor ticket is filed — `tickets/README.md` puts the
succession on the run that CLOSES the programme, and the owner's filing rule of 2026-09-10
asks for fewer tickets. This ticket stays open and is its own cursor.

## Stretch 4, 2026-09-11 — the 1839 could-carry pool, and the split that fed it

**The stretch:** the could-carry pool of `fergus_1839_crosswalk_1835.json` — 92 trades and
96 streets on matched entries, the third of this ticket's four pools and the one stretch 3
nominated. Bounded to one directory; nothing was read off a page image.

**What the pool turned out to be.** Both halves were already SPENT — the trades on the
cards as `occupation_later`, the addresses through both back-projections, with clause 3's
`unwritten` at 0. What was wrong was not the spending but the READING the pool is drawn
from. `tools/read_fergus_1839.py` splits one printed line into name / trade / address, and
the rule for where the name ends was "keep taking capitalised words, up to three":

```
Beaubien, John B., Michigan ave., bet. Lake and So. Water sts
  name 'Beaubien, John B., Michigan' · trade 'ave., bet. Lake and' · address 'So. Water sts'
```

The comma the compositor set was not a boundary to it. So the head street was eaten into
the name, the address became the tail of its own qualifier — **the wrong street** — and the
fragment between them was carried onto the card as a TRADE. `hh_beaubien_john_s` asserted
an occupation of `ave., bet. Lake and`; `hh_hunter_david` one of `street, near Rush`.

**Four defects, all in the reading, fixed at their one place:**

1. **The printed comma closes the name**, unless the token is a title or a suffix — the
   volume sets `Bates, jr., John` and `Baumgarten, jr., Morris`, whose comma is their own.
2. **A street's head word is a proper noun.** `STREET` was compiled `re.I`, so `[A-Z]`
   matched a lower-case letter and the volume's joining words became street names:
   `cor. Clark and Randolph sts` → "and Randolph sts", `bet Dearborn and State sts` →
   "and State sts", `clerk Steamer Geo. W. Dole, for St. Joseph` → **"for St"**. The name
   is now case-sensitive, the street WORD stays case-blind, and a joiner in front of a
   real head is dropped rather than kept.
3. **The compositor's end-of-line break rejoins**, `¬` as well as `-`, and takes the turned
   line's indent with it: `La¬ / Salle st` was read as a street called Salle, and
   `apothe¬ / caries` as two words.
4. **A host named with an initial is a person, tested BEFORE the street table.** Not a
   defect of the split but one it uncovered: with Wolcott's 1839 line no longer a false
   address, his 1843 `bds H. Wolcott` surfaced, and `back_project_residences.py` placed him
   on **Wolcott Street**. `BARE_PERSON` is only reached when no street name is found, so a
   host whose surname is also a street could never reach it. `INITIALLED_PERSON` is ordered
   in front of `street_words`, and excludes the compass initials or `res N. Water` reads as
   a man called Water. Both directions are self-tested.

**Measured, before and after:**

| | before | after |
|---|---|---|
| 1839 entries whose split changes | — | **192 of 1,655** |
| cards whose later trade or address changes | — | **16** |
| phantom streets read off a non-street phrase | 5 | **0** |
| `residents_could_carry_occupation` | 92 | **90** — two were the garbage above |
| `residents_could_carry_street` | 96 | 96 |
| business addresses adjudicated / placed | 150 / 18 | **151 / 18** |
| residence addresses adjudicated / placed | 44 / 6 | **45 / 6** |
| false placements (Wolcott Street) | 1 would have landed | **0** |
| directories on a card / `unwritten` (clause 3) | 938 / 0 | **938 / 0** |

The five streets that vanish are all refusals earned: `for St` and `schooner St` and
`mate steamer St` are vessels and destinations, `ake st` and `born st` are OCR damage that
the 1835 table refused anyway. No 1835 grade moved; `qualify_later_trades.py` re-derived
13 records.

**What a reader can see.** Sixteen cards. John B. Beaubien's directory line now reads as
the printer set it, from Michigan Avenue; David Hunter's trade of `street, near Rush`
becomes the address it was cut from; Tuthill King keeps the New York Clothing Store, and
Funk, Parsons, Hyde, Tucker and Austin each recover the first name of their own firm.
**No face was added and none was lost** — 18 business and 6 residence, as before.

**The pools after this stretch:**

```
  ties                        34 (1839) · 58 (1843) · 39 (1844) · 11 (1844 ad)  = 142
  initial-absent refusals    277 · 349 · 335 · 140                              = 1,101
  forename-disagreed          75 · 94 · 48                                      = 217
  could-carry, 1839           90 trades · 96 streets, all spent, the reading now correct
```

**Stretch 5 is the could-carry pool of Fergus 1843 and Norris 1844** — the same third pool
in the two volumes this one's defect does not reach, and it should check FIRST whether
their own splitters carry the same comma rule: `read_fergus_1843.py` and
`read_norris_1844.py` are separate files and this one's four defects were all local to the
1839 reader. **Two findings this stretch declined to take, recorded here rather than
filed as tickets** (owner's rule of 2026-09-10): the volume's shared street word
(`Clark and Randolph sts` names TWO streets and only the last is read — Eli B. Williams
loses Clark that way), and the 64 clause-1 refusals that are business-shaped addresses
against people the 1835 corpus gives no trade, which get one ruling on the business
question and none on any other. No successor ticket is filed; this ticket stays open and
is its own cursor.

## Stretch 5, 2026-09-11 — the could-carry pool of Fergus 1843 and Norris 1844, and the three characters their splitters cut at wrongly

**The stretch:** the could-carry pool of `fergus_1843_crosswalk_1835.json` (71 trades,
83 addresses) and `norris_1844_crosswalk_1835.json` (65 trades, 80 addresses) — the
third of this ticket's four pools in the two volumes stretch 4's defect did not reach.
Bounded to those two directories; nothing was read off a page image. It is the stretch
stretch 4 nominated, down to the question it told this run to ask FIRST: "whether their
own splitters carry the same comma rule". Both did, and two more besides.

**Both halves of the pool were already SPENT, as in stretch 4** — clause 3's `unwritten`
at 0 before and after — so what was wrong was again the READING the pool is drawn from.
`read_fergus_1843.py` and `read_norris_1844.py` are separate files from the 1839 reader
and from each other, and **151 of their 4,768 entries were split at a character the
compositor did not set a boundary at**.

**Four defects, in the two readers, each fixed at its one place:**

1. **The printed comma closes the name** — stretch 4's rule, never carried here. The
   test was a capital and a count of three (1844) or four (1843), so the run walked
   past the comma set after the forenames:
   `Baumgarteu, Morris, Illinois street, b Dearborn and Wolcott` read a forename of
   "Morris, Illinois" and lost Illinois Street, the only street in the line;
   `Hanson, Abraham, Methodist clergymen` and `Harrington, Joseph, Unitarian clergyman`
   lost the trade the comma opened; `Barker, Peleg A., Farmers Exchange, 35 Lake` lost
   the Exchange.
2. **A suffix or an initial standing on the far side of that comma is not the end of
   the name.** `still_the_name` states the three shapes the name runs THROUGH — a
   suffix's own comma (`Bates, jr., John`), a suffix standing after (`Bumpstead,
   Thomas, jr.`), and a comma the compositor set between two initials (`Hamlin, E. H.,
   Baptist clergyman`). Without it the rule in (1) took eleven of Fergus's `jr.`
   entries apart.
3. **A comma set with NO SPACE after it is the same comma**, and it sits inside a
   whitespace token where (1) could never see it: `Cleaver, T. B.,soap and oil factory`
   and `Wilson, Maihew,ship carpenter` were read as forenames "T. B.,soap" and
   "Maihew,ship". Keeping the comma on the kept half leaves the offset `rest` is sliced
   at unchanged, so the trade comes back whole.
4. **Norris's abbreviations are lower case and a man's initial is not** — the largest of
   the four, 106 entries. `h`, `r` and `b` are his own shorthand for house, residence
   and between, printed in his preface; the pattern that finds where the address begins
   was compiled `re.I`, so it stopped at the first CAPITAL initial in any name.
   `Adams, R. E. W, physician, corner of Clark and Lake streets` was left with no trade
   at all and an address of "E. W, physician, corner of Clark and Lake streets";
   `Beer, Adam, shoemaker, at J. B. Mitchell's` read a trade of "shoemaker, at J";
   `Bigelow, A. clerk at H. O. Stone's, house State street` read a trade of "clerk at"
   and filed his employer's shop as where he lived. The abbreviation WORDS stay
   case-blind; the three single letters do not.
5. **A hyphen is not a word boundary that rule may cut at** (7 entries, Fergus 1843).
   `\b` holds on the far side of one, so `light-house`, `boarding-house`, `packing-house`
   and `poor-house` each read as a trade ending in a hyphen and an address beginning
   "house …". Mark Beaubien keeps a light-house in 1843 and lives at River Street, not
   at "house keeper, res River street".

**Measured, before and after:**

| | before | after |
|---|---|---|
| Fergus 1843 entries whose split changes | — | **45 of 2,695** |
| Norris 1844 entries whose split changes | — | **106 of 2,073** |
| Norris trades cut at a capital initial | 106 | **0** |
| forenames carrying an unspaced comma | 3 | **0** |
| trades ending in a hyphen, 1843 | 7 | **0** |
| 1844 addresses that were the tail of a name (`could_carry_address`) | 80 | **79** |
| directories, on a card / `unwritten` (clause 3) | 927 of 927 / **0** | 927 of 927 / **0** |
| directories claims read / spent / unspent | 8,258 / 1,007 / 7,251 | unchanged |
| 1835 grades moved by the spend | 0 | **0** |
| business street faces (L218) / residence faces (L223) | 18 / 6 | **18 / 6** |

**What a reader can see — and the part that was not expected.** The cross-domain identity
index (`consolidate_resident_evidence.py`) keys an identity on the surname and forename the
reading gives it, so **51 identities were keyed on a forename with a street, a trade or a
denomination stuck to the end of it** — `id_anderson_john_washington_hall_n`,
`id_barker_peleg_a_farmers_exchange`, `id_wilson_maihewship`, `id_beaubien_mark_u_s`,
`id_hanson_abraham_methodist`. Such a key can never meet the man it belongs to. All 51 come
back to their own names, and **five men the index was carrying twice are one man again**:
Charles Billings Smith, David Lewis Roberts, William Rowlatt, James L. Howe and John P.
Bowes. Identities 6,851 → **6,846**; derived refusals 1,837 → **1,833** (four were refusing a
name nobody had); the directories domain's identities 2,897 → **2,892**; rungs R3 124 → 121
and R4 77 → 76. That file is gated (`--check`) and is where the fault would otherwise have
kept sitting.

**Six household cards correct the LINE they cite.** `mint_civic_residents.py` carries the
directory locator onto the card, and six were pointing a reader at a fragment that began in
the middle of a man's own firm: `hh_bowen_erastus_selden` cited "B. & Cole, house Michigan
avenue" and now cites "house Michigan avenue"; `hh_smith_e_kirby` cited "H. & E. Smith, h
Ohio jst. b Dear and Wolcott" and now cites "h Ohio jst. b Dear and Wolcott";
`hh_bradley_joseph`, `hh_goodrich_john`, `hh_jones_william` and `hh_sherman_rebecca` the
same. `ladder_spend.json` re-derives with them.

One card gives something up and it is the honest direction:
`hh_bradley_joseph`'s Norris 1844 line, "Bradley, Joseph, clerk, at W. H. Adams & Co.'s",
stops declaring that it HOLDS an address — the address it held was the second half of his
employer's name. **This stretch placed nothing on the ground** (clause 5): the four
volumes' precedence rule is untouched, every person whose reading changed already carries
an earlier volume's trade or an 1835 one, and the crosswalk counts are unmoved but for the
one false address above. What changed is that 151 printed lines now read as the printer
set them. `read_norris_1844.py --self-test` holds all three comma-and-capital rules on
seven named lines and sweeps the whole reading for either failure; the assertions fire
when broken.

**The 1839 reader was NOT changed.** The same three shapes exist there — `Morrison,
Ephriam, jr., teamster` reads a trade of "jr., teamster", `O'Meara, Timothy, Rev.,
Catholic priest` one of "Rev., Catholic priest", and `Dickey, Hugh, T. , attorney` loses
the T. — but that volume's `TITLES` includes `judge`, `hon` and `prof`, which are trades
there as often as titles, and the exception written for 1843 and 1844 walks straight into
them: it turned `Pearson, Hon. John, judge Circuit Court` into a forename of "Hon. John,
judge". Seven entries, three of them wrong today and four of them made wrong by the
naive fix. It needs the 1839 volume's own list, not this one's, and it is recorded here
rather than filed (owner's rule of 2026-09-10).

**The pools after this stretch:**

**re-derived from the four files today, not copied from stretch 4's table, which had
drifted** — ambiguous + contested, residents only:

```
  ties                        34 (1839) · 54 (1843) · 33 (1844) · 11 (1844 ad)  = 132
  initial-absent refusals    277 · 349 · 343 · 130                              = 1,099
  forename-disagreed          75 · 91 · 51                                      = 217
  could-carry, 1839           89 trades · 95 streets, spent, the reading correct (stretch 4)
  could-carry, 1843           71 trades · 83 addresses, all spent or refused with a clause
  could-carry, 1844           65 trades · 79 addresses, ALL 144 refused — see below
  could-carry, 1844 ad        12 trades · 15 places of business
```

Stretch 4's line read "34 · 58 · 39 · 11 = 142" and "277 · 349 · 335 · 140 = 1,101";
three of those eight numbers were carried forward rather than re-read, which is the
drift stretch 2 caught the first time and named. Every figure above comes from the
`counts` block of the file beside it, re-derived in this run.

**Stretch 6 is the 1844 half of that last line, and this stretch is what unblocks it.**
`spend_directories.py` carries a volume-level flag, `parse_trusted: False`, on Norris 1844
alone, and every one of that volume's 144 could-carry units is refused by it under one
clause — T-0569's `UNTRUSTED_SPLIT`, which says the split "yields a value containing no
trade at all rather than a trade with something extra on it" and cites `of Loyd`,
`of Horace Norton & Co` and twice simply `of`. Measured against the corrected reading:
**13 of the volume's 65 matched trades are that shape** (a partnership named where the
trade would go) and **52 are plain legible trades** — carpenter, baker, tailor, physician,
watchmaker, "grocery and provisions, South Water st". A great many of the rest of that
refusal's reputation was defect 4 above, now gone. A blanket refusal is not a ruling about
a line, and clause 1 of this ticket asks for one per unit: stretch 6 replaces the volume
flag with a per-entry, per-FIELD predicate (the partnership shape refuses a TRADE and says
nothing about the address beside it), and spends what survives. No successor ticket is
filed — `tickets/README.md` puts the succession on the run that CLOSES the programme, and
the owner's filing rule of 2026-09-10 asks for fewer tickets. This ticket stays open and
is its own cursor.

## Stretch 6, 2026-09-11 — Norris 1844's blanket refusal, replaced per entry and per field

**The stretch:** the could-carry pool of `norris_1844_crosswalk_1835.json` — 65 trades and
79 addresses, all 144 of them refused by one clause — and the volume flag that refused
them. It is the stretch stretch 5 nominated, in the words it nominated it: "replaces the
volume flag with a per-entry, per-FIELD predicate (the partnership shape refuses a TRADE
and says nothing about the address beside it), and spends what survives."

**What the flag was.** `spend_directories.py` carried `parse_trusted: False` on Norris
1844 alone, and `graded()` skipped every row of a volume that had it. The refusal's
GROUND, T-0569's, is sound and is unchanged here: the volume sets a partnership where the
trade would go — `of Loyd`, `of Horace Norton & Co`, twice simply `of` — so the split
yields "a value containing no trade at all rather than a trade with something extra on
it". What was wrong was the SCOPE: a sentence about three lines refusing a hundred and
forty-four, which is not a ruling about a line, and clause 1 of this ticket asks for one
per unit.

**The predicate.** `split_refusal(field, value)` returns the clause key this entry's
split is refused under for this field, or nothing — and `SPLIT_CLAUSES` holds the three
clauses, written into the layer so the sentence on the record and the sentence in the
ledger are the same sentence. Three shapes:

| clause | shape | refuses |
|---|---|---|
| `firm_where_a_trade_is` | the value BEGINS `of` — the volume's "Surname, initials, of <firm>" | the trade |
| `premises_where_a_trade_is` | the value BEGINS `at` — `at United States Hotel`, `at clerk's office` | the trade |
| `address_is_a_backreference` | a locative and then only a ditto — `res same`, `house same`, `res "` | the address |

Both trade patterns anchor at the START, which is what separates them from a trade with
something extra on it: `clerk, at T. King's` and `book-keeper at G. S. Hubbard's` are
trades and cross. No trade in the English of 1844 begins with either word.

**The shapes are a compositor's construction, not one volume's habit, so all four volumes
are asked** — and two of the three the flag TRUSTED print them and had been carrying them.
That is the finding the boolean could not make: under it nobody ever looked.

**Measured, before and after** (`spend_directories.py --report`, whole town):

| | before | after |
|---|---|---|
| people carrying a later trade | 126 | **138** |
| people carrying a later address | 149 | **165** |
| ledger rulings that carried something | 202 | **220** |
| `line_held_but_parse_refused` — held a line, got nothing | 17 | **0** |
| trades refused, by clause | 65 (one clause, one volume) | **16** (2 clauses, 2 volumes) |
| addresses refused, by clause | 79 (one clause, one volume) | **8** (1 clause, 2 volumes) |
| directories, on a card / `unwritten` (clause 3) | 927 of 927 / **0** | 927 of 927 / **0** |
| 1835 grades moved | 0 | **0** |
| business street faces (L218) | 18 | **18** |
| residence faces (L223) | 6 | **14** |

**What the retractions were.** `hubbard_henry_g` carried `at G. S. Hubbard & Co.’s
warehouse` as his 1839 trade — a door, not an occupation; Fergus 1843's `clerk, Circuit
Court` now wins the field, a real trade four years nearer the scene, so the clause
promoted a reading rather than costing one. `rue_john_c` carried `res same` and now
carries Norris's `h Clark, b Madison and Monroe`. `burton_edward` carried `res same` and
no other volume names him, so his card gives the address up: the honest direction.

**Two older faults the released lines walked into, both fixed here because leaving either
would have shipped a placement the policy documents forbid in writing.**

1. **`RESIDENCE_PREFIX` knew only Fergus's words.** `docs/ADDRESS-BACK-PROJECTION.md`
   clause 2 refuses an address the volume prints as a residence, and the pattern that
   reads it listed `res`, `bds`, `boards` — never `house`, `h` or `r`, which are Norris's
   own shorthand, declared in his preface. It had never been exercised on them because
   his parse never reached the clause. The first that did was `house N Water st (See
   card` — Silvester Marsh's HOME — and the business pass PLACED it as a shop face on
   North Water Street, the one street in the town no other rule can seat a building on.
   The pattern is shared by both passes, so adding the four words moves him to the
   residence pass, where he places as a home. Business faces end where they started, 18.
2. **A mis-set space defeated both personal-name tests.** `residence Hum phrey Clark's`
   is Humphrey Clark's house; `street_words` read `Clark` as Clark Street and placed
   Erastus Clark on it. `INITIALLED_PERSON` and `BARE_PERSON` both stand in front of the
   street table for exactly this collision and both key on the SHAPE of a name, which
   `Hum phrey` is not. `POSSESSIVE_HOST` does not: none of these four volumes ever prints
   a street possessively, so a body ending `'s` is refused as a householder before the
   street table is consulted. Four of the addresses this pass adjudicates are that shape.

**What a reader can see.** Fourteen households stand on a street face where six did this
morning, and three streets — Dearborn, Randolph and Wells — are reached by a house for the
first time; Norris prints a man's home far oftener than his shop, which is why this pass
and not the business half is the one his volume feeds. **L223 is restated 6 → 14** with
both faults above written into it; **L218 is unmoved at 18**. Nothing is drawn (L2).
`residents.js` names WHICH field's split does not cross instead of saying it of the whole
line, and the panel's summary sentence reports the two per-field counts in place of a
figure that is now always zero.

**The gates.** `check.sh` 308 steps green. Both back-projection passes gained self-test
rows for Norris's words, the possessive and the ditto, and the business pass gained two
holding that `Randolph st` and `Lake st` are still streets and not `r` and `h`.
`spend_directories.py --self-test` replaces its one-volume rule-3 assertion with two that
run over every volume: nothing a clause refused reached a card, and nothing that reached
one has a shape a clause names — the assertion the flag could never make.

**The pools after this stretch**, re-derived from the four `counts` blocks today:

```
  ties                        34 (1839) · 54 (1843) · 33 (1844) · 11 (1844 ad)  = 132
  initial-absent refusals    277 · 349 · 343 · 130                              = 1,099
  forename-disagreed          75 · 91 · 51                                      = 217
  could-carry, 1839           89 trades · 95 streets, spent (stretch 4)
  could-carry, 1843           71 trades · 83 addresses, spent or refused (stretch 5)
  could-carry, 1844           65 trades · 79 addresses — 50 and 75 SPENT, 15 and 4
                              refused per entry, per field, each naming its clause
  could-carry, 1844 ad        12 trades · 15 places of business, spent (stretch 2)
```

**The could-carry pool is now closed in all four volumes.** Stretch 7 takes the **ties**,
132 of them, as this ticket's own ordering asks — a tie is one page-read from a match and
they are the pool that stood first in the table before the write debt and the readers
took precedence. No successor ticket is filed: `tickets/README.md` puts the succession on
the run that CLOSES the programme, and the owner's filing rule of 2026-09-10 asks for
fewer tickets. This ticket stays open and is its own cursor.

## Stretch 7, 2026-09-12 — Fergus 1843's ties, and the man the volume prints twice

**The stretch:** the ties of `fergus_1843_crosswalk_1835.json` — 39 ambiguous and 15
contested, 54 of the 132 ties stretch 6's table counted, and the largest single-volume tie
pool. It is the stretch stretch 6 nominated ("stretch 7 takes the **ties**, 132 of them, as
this ticket's own ordering asks — a tie is one page-read from a match"). Nothing was read
off a page image: the answer was already in the transcription, in a field nobody had asked
about.

**What the ties were.** Fergus 1843 is TWO directories bound as one, and only this volume
of the four is: a `business directory` of 174 subscribers' notices set under trade headings,
each headed by the subscriber's name in capitals, and an `alphabetical directory` of 2,521
lines, one to a person. **A tradesman who paid for a notice also stands in the roll, so the
volume prints him twice** — and the crosswalk's ambiguity test counted PRINTINGS. Silas B.
Cobb's own advertisement arrived as a rival candidate for Silas B. Cobb, and the tie could
only ever be narrowed. Eighteen of the printings standing in the tie pool were a notice of
that kind. The `section` field that says which is which has been in the claims file all
along; no crosswalk had ever read it.

**The rule, and it is a new module so that it is one rule and not four.**
`tools/printed_twice.py` (self-test, 17 cases) folds a notice onto the roll entry it can
only be, in four clauses: the folded surnames agree; the printed names are CONSISTENT —
`name_agreement`'s first-forename rule plus every FURTHER initial both printings set; the
notice prints a surname and TWO OR MORE initials, or the two printings name a thing in
common (a street number, or a word of five letters or more that both set, one a prefix of
the other, street names and the compositor's furniture struck out); and EXACTLY ONE roll
entry in the whole volume satisfies the first three. **78 of the 106 notices fold. The
other 28 stand as their own candidate exactly as before**, and the clause that was silent
is written against each — all 106 notes are filed in the crosswalk's new `printed_twice`
block, because a refusal here is a reading. A folded notice is not discarded either: it is
carried on the roll entry's row as `also_printed`, quotable.

One thing the rule had to do that the imported one cannot. `name_agreement.agrees`
deliberately does not compare FIRST initials — the crosswalks get that from the bucket they
look a resident up in — so `G. S. HUBBARD` read as consistent with `Hubbard, Ahira` and
clause 4 refused every Hubbard notice for want of it. A module asking its question of two
PRINTINGS has to ask for the initial itself. With that, `Morris, Mrs` stops standing
between B. S. Morris and his own notice, and three more notices fold.

**What landed.** Six men of 1835 gain a listing that was ambiguous: `cobb_silas_b`,
`morris_b_s`, `hubbard_gurdon` (two notices onto one roll line), `harmon_charles_l`,
`bishop_j_e`, `funk_absolom`. 1843's matches 119 → **125**, ambiguous 39 → **31**,
contested 15 → **17** — and the two that became contested are the finding under the
finding: the exchange broker's notice is **Jonas Coe** Clark (`J. COE CLARK`, exchange
broker, Clark St.), not a candidate for either John Clark, so what is left is a true
collision of two residents over one roll line rather than a four-way muddle. Everything
that landed is SPENT in this run: the directories' `unwritten` column is **0** of 939
reached (927 before), and could-carry on this volume goes 71/83/82 → **74/89/86**, each
written.

**The comma that was hiding a house** (clause 3 of this ticket, the half that is a face).
A match carries its address through the two back-projection passes, and the nearer reading
this stretch landed arrives in a shape neither pass could read: the crosswalks split the
printed line on its punctuation, and where the trade's own trailing corner falls into the
address field the field opens with the SHOP and goes on to the HOME — `cor Clark, res
Dearborn, bet Washington and Madison`. Both passes tested the volume's residence word at
the HEAD of the field only, which is the fault stretch 6 fixed one clause earlier (`house N
Water st` placed as a shop face). `split_home()` now cuts the field at that word and each
pass reads its own half; the whole field stays the quote, and the record carries
`address_read_as_the_home` where the two differ.

It pays for itself twice over. **Doctor D. S. Smith's home stands on La Salle Street** — a
face no house had reached — off `office on Clark street … residence La Salle street,
opposite the First Baptist Church`, a residence clause that had been invisible because the
line opened with his office. And **Charles L. Harmon comes off Dearborn Street**, which
looks like a loss and is a repair: he stood there on Norris's `res Dearborn st. b Wash and
Mad sts`, where the abbreviation hid Madison — a street the 1835 layer does not carry — so
the R4 qualifier clause never fired. Fergus spells it out four years nearer the scene, the
clause reads it, and it refuses. **L223 is unmoved at 14** and L218 unmoved at 18; the
residence pass adjudicates 61 → **63**, because two fields it could not see are now read.

**Two findings this stretch declined to take, recorded here rather than filed, since this
ticket owns the question.**

1. **A title read as a forename.** `Doctor D. S. SMITH`, `Doctor Egan`, `Doctor Blaney` —
   14 printings in this volume open with a doctor's title spelled in full, and `doctor` is
   in neither `name_agreement.TITLES` nor the local `initial()` of any of the four
   crosswalks (all of which carry `dr`). So the title is read as the forename: it sets the
   bucket initial to `d`, and it defeats clause 2 of the fold. One ruling depends on it
   today — `smith_d_a`'s tie, where `Doctor D. S.` cannot be shown to be `David Sheppard`
   — and the exposure is larger than that, because a resident printed with the initial D
   can be offered `Doctor Egan`. It is one word in a shared module and it re-derives all
   four volumes, which is why it is stretch 8's and not this one's.
2. **One placement still resting on an unread qualifier.** `sherman_rebecca` stands on
   Clark Street off `h Clark st. b Mad. & Mon` — Madison and Monroe, abbreviated, and
   `NOT_1835` keys on the words spelled out. It is the same clause this stretch just
   applied to Harmon, escaping on a contraction. Filed as a ticket of its own because it
   belongs to the back-projection pass and not to the directories.

**The gates.** `check.sh` 310 steps green. `printed_twice --self-test` 17 cases; both
back-projection self-tests green; the derived layer re-derived with `rederive.mjs --run`
and both back-projections re-written. NOTE for the next run: the chain needed **two**
passes to converge, because `mint_civic_residents` rewrites a card's note from its own
template when the card's source list changes and `spend_land_sales`' prose — which runs
earlier — is re-appended only on the following pass. A card can therefore be one pass short
of its own provenance. Recorded here; it is not this ticket's.

**The pools after this stretch**, re-derived from the four `counts` blocks today:

```
  ties                        34 (1839) · 48 (1843) · 33 (1844) · 11 (1844 ad)  = 126
  initial-absent refusals    277 · 349 · 343 · 130                              = 1,099
  forename-disagreed          75 · 90 · 51                                      = 216
  could-carry                 closed in all four volumes (stretches 2, 4, 5, 6)
```

**Stretch 8 is the title read as a forename, and then Norris 1844's ties.** Finding 1 above
is the first thing to do, because it is cheap, it reaches matches and not only ties, and it
is the only known way a ruling in these four files can be made on a word that is not a
name. Then the 33 ties of `norris_1844_crosswalk_1835.json`, where the same
one-man-two-printings question takes a different shape: his advertising cards are a
SEPARATE crosswalk file, so a man with a card and a roll line is counted once in each, and
whether those two are one printing is the question this volume's fold has to answer. No
successor ticket is filed: `tickets/README.md` puts the succession on the run that CLOSES
the programme, and the owner's filing rule of 2026-09-10 asks for fewer tickets. This
ticket stays open and is its own cursor.

---

**LAPPED ONTO `dev` 2026-09-12, and the lap moved one of this stretch's two placements.**
Stretch 7's PR (#1167) was pushed, gated green and never merged — the run that opened it
ended at the merge — so twelve `dev` merges landed under it before this one picked it up.
The lap is not bookkeeping only, and the difference is recorded here rather than left in a
diff:

- **T-1049 (#1175) withdrew `hh_smith_d_a`.** The card was minted on a press notice printed
  against `Courtland, Alabama`; T-1048's resolved place vocabulary refuses that as a Chicago
  appearance, the ladder then reaches nothing for the identity, and the container goes with
  it. So `Doctor D. S. Smith … residence La Salle street` — the residence clause
  `split_home()` uncovered, and the headline placement of this stretch — has no person of
  1835 left to reach. The clause and the reading stand; the FACE does not. Recorded, not
  claimed.
- **L223 therefore restates 13 → 12**, not 14: `harmon_charles_l` still comes off Dearborn
  Street under the R4 qualifier, and `smith_d_a` cannot replace him. The twelve are six on
  Fergus 1843 and six on Norris 1844; the pass adjudicates 60 with 48 refusals. The
  changelog entry was corrected in the same commit — it had promised a visitor a house on
  La Salle Street that this tree does not place.
- The derived layer was rebuilt with `rederive.mjs --run` and both back-projections
  re-written, twice to convergence, exactly as the note above predicted.

Nothing about the `printed_twice` fold changed on the lap: 78 of 106 notices still fold and
the six 1843 listings still land. The pool table above is re-derived and unchanged.

---

## Stretch 8, 2026-09-12 — the title read as a forename, in all four volumes and on both sides of every comparison

**The stretch:** finding 1 of stretch 7 — "a title read as a forename" — taken across the
four crosswalks, the module they all import, and the reader that feeds one of them. It is
the stretch stretch 7 nominated, in the order it nominated it ("the first thing to do,
because it is cheap, it reaches matches and not only ties"). It is bounded to the
vocabulary and what re-derives from it; the 33 Norris 1844 ties, the second half of that
nomination, are NOT in it and are stretch 9 below. Nothing was read off a page image.

### What was wrong, measured before it was touched

`name_agreement.TITLES` held nine abbreviations. Each of the four crosswalks restated its
own copy — 1839's added `hon` and `esq`, the advertiser's added `doctor`, 1843's and
1844's were inline literals inside `initial()` — and **not one copy carried a rank spelled
out in full**. The corpus prints them on both sides of every comparison:

```
  printed, in the volumes      13   Fergus 1843  DOCTOR BLANEY · DOCTOR EGAN · DOCTOR
                                                 J. BRINKERHOFF · DOCTOR H. H. BRAYTON ·
                                                 DOCTOR JOHN W. ELDRIDGE · DOCTOR BENJAMIN
                                                 F. HALE · DOCTOR D. S. SMITH
                                    Fergus 1839  Campbell, Major James B · Handy, Major ·
                                                 McClure, Judge Samuel · Mulford, Major E. H ·
                                                 Noble, Major · Tew, Prof. Geo. C
                                    Norris 1844  none, in the roll or the advertising cards
  on the 1835 cards            14   Lieut. James Allen · Judge Sidney Breese · Major John
                                    Greene · Major Handy · Judge Silver · Major L Shapley ·
                                    Lieut J L Thompson · and the seven suffix names below
```

Eighteen entries in Fergus 1839 alone were indexed on the initial of a rank or a suffix
rather than of a name (`Archdale, jr` → J, `Campbell, Major James B` → M, `Noble, sen.,
Mark` → S, `Tew, Prof. Geo. C` → P). And the residents layer keys fourteen people the same
way, seven of them on a SUFFIX: `John Bates Jr.` was in the 1839 pool as a man whose
surname was **Jr**, and so were Joshua Hathaway and Elijah Wentworth.

The worst of it is not a miss but a match. `Major Handy` met `Handy, Major` on a shared
initial — the M of Major, on both sides, a rank agreeing with itself. `Lieut J L Thompson`
was matched to `Thompson, Leveret`, admitted to the Second Presbyterian church in **1889**,
on the L of Lieut. `Morgan Shapley` of the 1837 poll reached `Major L Shapley` on the M of
Major, and had written a paragraph onto his card.

### What was done

1. **One vocabulary, written once** (`tools/name_agreement.py`). Every rank now carries its
   abbreviation AND its full spelling, so the pair cannot drift apart again, plus `judge`,
   which these volumes print with no abbreviation at all. `SUFFIXES` gains `esquire`
   beside `esq`. Nothing is in it that the corpus does not print, and no token in it stands
   as a forename anywhere in the residents layer or the four transcribed volumes — measured,
   not assumed.
2. **The four crosswalks import it** rather than restate it. 1839 and the advertiser keep
   their own additions where they are the volume's own (`junr`, `md` — the advertiser's
   tokeniser splits on whitespace alone, so `M.D.` reaches the test as one word there and
   as two everywhere else).
3. **A no-forename refusal, shared** (`na.no_forename_refusal`). `split_name` used to
   return the rank AS the given; with the vocabulary fixed it would have returned nothing
   at all, and a row dropped there is a row no refusal is ever filed for. It now keeps the
   surname, empties the given, and the caller files a refusal that says a rank is standing
   where the given name should be. Four people reach it: Major Handy, Judge Silver, Jun
   Marknoble, Sen Marknoble.
4. **The loose suffix comma** (`tools/read_fergus_1839.py`). Six entries set the suffix's
   comma with a space before it — `Archdale, jr. , John, contractor` — so the comma arrived
   as a token of its own and broke the name loop: the forename was swallowed into the trade
   and `jr` stood as the given name. The waiver the reader already grants a tight `jr.,` now
   covers the loose form. Archdale, Butterfield, Frink, Johnston, King and Ludwig read their
   forenames; six trades lose a name off their head (`John, merchant` → `merchant`).
5. **A withdrawal** (`tools/spend_fergus_1839_later_lists.py`). `strays()` had always
   REFUSED a card carrying this pass's paragraph with no ruling behind it, and nothing could
   ever clear one — the gate could report the state and not leave it. `retract_from_person`
   undoes exactly what the applier does, the paragraph and the citation, and five self-test
   cases hold it. Shapley's card is the first to use it.

### What landed, and what it cost

**Two men gain a land purchase.** `ALLEN JAMES` (ls0954) reaches Lieut. James Allen and
`BREESE SIDNEY` (ls0651) reaches Judge Sidney Breese, both `forename_agrees` — the deed-book
reading had been weighing "James" against "Lieut" and "Sidney" against "Judge" and finding
two different names. Both refusals of rivals are re-derived and stand.

**Four of Fergus 1843's advertising doctors stop being two men each**: `f1843_e0134`
(Brayton), `e0137` (Eldridge), `e0138` (Hale), `e0140` (Smith) fold onto roll entries
`e0422`, `e0900`, `e1179`, `e2289` under stretch 7's clause 1, which the title had been
defeating. Notices folded 78 → 82; standing as their own candidate 28 → 24. The three that
still stand — DOCTOR BLANEY, DOCTOR EGAN, DOCTOR J. BRINKERHOFF — print one initial or none,
and the clause that is silent is written against each.

**Two false matches are withdrawn**, and this is the point of the stretch: Lieut J L
Thompson / Leveret Thompson (1889) and Major L Shapley / Morgan Shapley (1837 poll). The
Shapley paragraph is unwritten and the 1839 citation with it. Major Handy's 1839 listing
goes too, and is now a filed refusal rather than a match on a rank.

**One new match, and its weakness recorded.** Lieut J L Thompson now matches `Thompson,
Joseph, caulker, house Adams st. b Clark and Lasalle` (n1844_e1767) — the only J Thompson
in Norris 1844. It stands by the ratified rule (an initial against a full forename is a
match, T-0670) and no clause refuses it, but the 1835 card prints initials only and the
trades disagree in kind. Recorded here rather than dressed up.

**This stretch placed nothing on the ground** (clause 5). The two back-projections
adjudicate three and one more units than they did — 158 → 161 and 60 → 61 — and every one
of the four is refused: three on clause 1 (no 1835 business) and one on clause 3 (not on
the 1835 grid). **L218 unmoved at 18** and **L223 unmoved at 12**.

**Clause 3, the write ceiling:** `measure_research_spend.py` reads directories **912
reached, 912 judgeable, 912 on a card, 0 unwritten**.

**The pools after this stretch**, re-derived from the four `counts` blocks, and stated with
the formula so they can be compared: ties = `ambiguous` + `contested`; initial-absent =
`refusals`; forename-disagreed = `forename_refusals`. The same formula over `HEAD` gives
the before column, so the two are one measurement and not two.

```
                       1839        1843       1844      1844 ad      total
  ties              34 -> 37    44 -> 45   30 -> 31    11 -> 11   119 -> 124
  initial-absent   257 -> 260  323 -> 323 317 -> 316  124 -> 124 1021 -> 1023
  forename-disagr.  69 -> 68    83 -> 80   47 -> 46     0 ->  0   199 -> 194
  could-carry            closed in all four volumes (stretches 2, 4, 5, 6)
```

The ties RISE, and that is the repair rather than a regression: five collisions the rank's
letter had been hiding come into view. Mark Noble is the clearest — Fergus prints `Noble,
sen., Mark` and `Noble, Mark` and the senior was indexed under S, so the junior stood alone
and matched; both now stand under M and the tie is filed. Lieut. James Allen, refused under
L this morning, is a tie under J between `Allen, Capt. James` and `Allen, James P.`.

**Two entries gained a match off the suffix repair**: `Mulford, Major E. H` → E. H. Mulford,
and John Bates Jr., who had been in the pool under the surname "Jr". `John Lyle King` loses
his, because it had stood on the J of `jr.`; his entry now reads `King, jr., John, merchant`
and the 1839 volume holds a second J King, so it is a tie and not a match.

### The gates

`check.sh` **333 steps, none red**. `name_agreement --self-test` 18 cases. The later-lists
pass's self-test 5 cases longer, all on the withdrawal. `rederive.mjs --run` to convergence
(the derived tree is byte-identical on the following pass; only the audit **.xlsx** differs
run to run, because a zip carries its own timestamps — that is not a data difference and
should not be read as one). The two back-projections re-written, and the five steps the
rederive manifest does NOT cover re-run by hand: `qualify_later_trades`,
`back_project_addresses`, `back_project_residences`, `spend_fergus_1839_later_lists`,
`fergus_1839_street_faces`.

### Three findings this stretch declined to take, recorded here rather than filed

1. **The mints restate the same vocabulary again.** `mint_documented_residents.py`,
   `mint_letter_list_residents.py` and `crosswalk_census_1840_heads.py` each hold their own
   `TITLES` set, and each is missing the full spellings this stretch just added to the
   directories. They are not directory passes and their blast radius is the minting of
   cards, not the reading of a book, so they are outside this programme — but they are the
   same defect and a run that touches the residents layer should take them.
2. **`crosswalk_norris_1844_advertiser.py` DOES re-derive its committed file today.** The
   rederive manifest's `_only_gated_tools` note records that running it once rebuilt
   `norris_1844_advertiser_crosswalk_1835.json` from 443 lines to 195 and took
   `data/residents/directories.json` with it, which is why it is not in the manifest. Run
   against this tree, with the shared vocabulary in place, its output is **byte-identical to
   the committed file**. That is not an argument for adding it to the manifest — the
   manifest's rule is that `check.sh` must gate the tool, and `check.sh` still does not
   invoke it at all — but it is worth knowing that the tool is no longer the hazard the note
   describes.
3. **`Doctor Egan` of Fergus 1843 prints no forename**, and `egan_william_b` is on the cards
   as `Dr William Bradshaw Egan`. The two are almost certainly one man; the surname+initial
   rule cannot say so, because one side has no initial. It is the same shape as `Major
   Handy`, and it is what a page image or a second volume would settle.

**Stretch 9 is the 33 ties of `norris_1844_crosswalk_1835.json`**, the second half of what
stretch 7 nominated and unchanged by this one: 17 ambiguous and 14 contested, where the
one-man-two-printings question of stretch 7 takes a different shape, because this volume's
advertising cards are a SEPARATE crosswalk file — a man with a card and a roll line is
counted once in each, and whether those two are one printing is the question this volume's
fold has to answer. No successor ticket is filed: `tickets/README.md` puts the succession on
the run that CLOSES the programme. This ticket stays open and is its own cursor.

## Stretch 9, 2026-09-12 — Norris 1844's ties, and the middle initial no rule had ever read

**The stretch:** the 31 ties of `norris_1844_crosswalk_1835.json` — 17 ambiguous and 14
contested — which is the stretch stretch 8 nominated. It is answered by a clause, not by a
page image: nothing was read off a scan. The clause is in a shared module and it therefore
re-derives all four volumes and the 1837 poll besides, which is the same shape stretch 8
took and for the same reason.

### What the ties were, and it was not the question stretch 8 expected

Stretch 8 nominated this pool for the one-man-two-printings question — a man with a roll
line and an advertising card is counted once in each of two crosswalk files, so whether
those two are one printing is what this volume's fold has to answer. **It is not what these
ties are.** Measured before anything was touched: of the 31, every candidate on both sides
of every tie is a ROLL entry. Two of them (`Taylor, Charles … (Sec card)`, `Murphy, John,
United States Hotel … (See card.)`) point at a card, and in neither case is the card the
rival. The advertiser file's ties, all 11, fire nothing under this stretch's clause either —
measured, and recorded below. The cross-file fold has no case to answer today, so it was not
built.

What the ties actually are is one defect, and it is upstream of all four volumes.

```
  the rule, as it stood     SURNAME folds the same, AND the FIRST initial of the given
                            name matches. Since T-0670, where BOTH readings print a full
                            FIRST forename and the two disagree, the match is refused.
  what was never compared   every initial after the first
```

`name_agreement.agrees` judges the first forename and stops; the crosswalks take the first
INITIAL from the bucket they look a resident up in. So nothing in the chain had ever weighed
a middle initial both readings print. `H. B. Clarke` stood against `Clarke, H. W. attorney
at law` on the H they share. The module that DOES compare them has existed since stretch 7 —
`printed_twice.consistent`, clause 2 — but it asks its question of two PRINTINGS in one
volume and never of a printing against a person of 1835.

### What was done

1. **The comparison, written once** (`tools/name_agreement.py`). `initials()` is lifted out
   of `printed_twice._initials` and `printed_twice` imports it, so the module that folds two
   printings and the module that refuses a person count a name's initials the same way.
   `further_initials_disagree()` compares only the initials BOTH readings set, position by
   position. `narrow_by_further_initials()` is what a crosswalk calls.
2. **An unread initial refuses nothing**, and this is the half that took the measuring.
   Fergus 1839's H is set as two strokes and comes back as `II`, `I I`, `IT`, `IL`, `Ik`;
   its D comes back as `I)`. A first draft of this clause refused `Chapman, Charles II.`,
   `Beaubien, Charles IT`, `Caton, John I).` and `Taylor, Anson IT` — four men the 1835 layer
   holds under the very initial the artefact hides. Measured over the four transcribed
   volumes: 16 further-name tokens carry a character no compositor set and 22 more are two
   capitals with no name behind them. A further initial is READ when it is a single letter
   with nothing but a printer's point after it, or a middle name of three letters or more
   spelled out; `I` is excluded even so, because it is the shape every one of those artefacts
   collapses to and a middle initial I occurs nowhere else in this corpus. This is T-0695's
   principle one field along — a disagreement against a garbled reading is a transcription
   defect and not two people — and it errs in the safe direction.
3. **Silence is not agreement.** Where the refusal would leave exactly ONE candidate and that
   candidate sets fewer initials than the 1835 reading does, nothing is refused and the tie
   stands. `J. B. Cook`, baker, meets `Cook, Josiah P. baker` and `Cook, John, tailor`: the P
   refuses Josiah and what is left is John, silent. Refusing the rival for speaking and then
   promoting the survivor for its silence would deal the baker's listing to a tailor — and it
   would do it on the weaker of the two readings. Four rows decline on this clause across the
   five files (`J. B. Cook` and `William V Smith` in 1844, `D E Jones` in 1843, `William V
   Smith` in 1839, plus two in the poll), and each carries the declined narrowing in a
   `further_initials_declined` field, because a decision not to act is a reading.
4. **The four generators call it**, each filing into a `middle_initial_refusals` list of its
   own with the count beside it — never into `forename_refusals`, so the pool table below
   still means what it meant. Scope is exactly T-0670's: the pool whose rulings reach a CARD,
   and no other. `crosswalk_fergus_1839_election.py` is added to that scope for the first
   time (its residents pool reaches cards and had no forename rule at all).

### What landed

**Thirty-five printings refused** — 6 in Fergus 1839, 12 in Fergus 1843, 13 in Norris 1844,
4 in the 1837 poll — and **twenty matches withdrawn** with them. Every one names the letter
it turned on: `Edward A. Rogers` against `Rogers, Edward Kendall`, `John N Foster` against
`Foster, Dr. John Herbert`, `S W Reed` against `Reed, Stilman O.`, `John A Mills` against
`Mills, John Rodney`, `W B Clarke` against `Clarke, William Hull`.

**Five readings land, and two are people this town should always have had.**

- **Augustine Deodat Taylor**, the carpenter of the first balloon-frame building, reaches
  `Augustin D. Taylor` in the 1837 poll and `Taylor, A. D. builder, house Michigan ave.` in
  Norris 1844. Both had been CONTESTED by `Anson H. Taylor`, whose H the rule could not see.
- **H. B. Clarke** reaches `Clarke, Henry B., farmer, Michigan ave, n.e. cor 16th Street` in
  1843 and `Clarke, H. B. farmer, lake shore, below Michigan avenue` in 1844 — two volumes
  agreeing — instead of the attorney Henry Wilcox Clarke.
- **Eli B Williams** stops sharing his listing with `Williams, E. S. law student`.

**This stretch moved the ground, once, and it is a withdrawal** (clause 5). H. B. Clarke's
business stood on **Clark Street** on the authority of the attorney's `36 Clark`. That match
is gone and the face with it; the Michigan Avenue reading that replaces it is off the 1835
grid, so it places nothing. **L218 is restated 18 → 17** in `docs/LIBERTIES.md`, with the
prose that reasons from the number. **L223 unmoved at 12.** The address back-projection
adjudicates 161 → 156 and the residence pass 61 → 58, the difference being the withdrawn
matches that no longer carry an address to read.

**Clause 3, the write ceiling.** `measure_research_spend.py` reads directories **883 reached,
883 judgeable, 883 on a card, 0 unwritten**, and the town total 0. It did not get there for
free: the first re-derivation left ONE unwritten, and following it is what put the 1837 poll
in scope. `hh_clarke_w_b`'s card had carried the poll's `W. H. Clarke` only because the 1839
directory pass had put a citation there; withdraw the directory match and the poll line stood
naked on a card that never named it. The poll crosswalk had the same defect and no forename
rule at all, so it was given this clause. Three more poll matches fell out with it, including
`Timothy J Clark` against `Thomas A. Clark`.

### The pools after this stretch

The formula is stretch 8's, so the columns compare: ties = `ambiguous` + `contested`;
initial-absent = `refusals`; forename-disagreed = `forename_refusals`. The new column is this
stretch's clause. The advertiser file is unwired and measures **0** — every one of its 11 ties
and 18 matches was tested against the clause and none fires — so it is not carrying an unpaid
debt; `check.sh` does not invoke that generator at all and the rederive manifest's own rule
forbids running an ungated derivation, which is why the file is left alone rather than rebuilt
to add a zero.

```
                       1839         1843        1844      1844 ad      total
  ties              37 -> 37     45 -> 41    31 -> 24    11 -> 11   124 -> 113
  initial-absent   260 -> 260   323 -> 323  316 -> 316  124 -> 124  1023 -> 1023
  forename-disagr.  68 -> 68     80 -> 80    46 -> 46     0 ->  0    194 -> 194
  further initial    0 ->  6      0 -> 12     0 -> 13     0 ->  0      0 ->  35
  matches          152 -> 146   121 -> 115  102 -> 100   18 -> 18   393 -> 379
  could-carry            closed in all four volumes (stretches 2, 4, 5, 6)
```

The 1837 poll is not in that table because it is not a directory: its residents pool goes
matches 90 → 89, ambiguous 31 → 31, contested 21 → 18, further-initial refusals 4.

### The gates

`check.sh` green. `name_agreement --self-test` 18 cases, six of them new and four of those the
stroke artefacts. `printed_twice --self-test` 17 cases — **and it was RED on `dev` before this
stretch touched it**, which is its own finding: stretch 8 put `doctor` in the title vocabulary
and two of that module's cases had been asserting the DEFECT rather than the rule ever since
(`_initials("Doctor D. S.") == ["d","d","s"]`, and `Doctor D. S.` reading as inconsistent with
`David Sheppard`). Nothing was gating it. Both cases are corrected to the post-stretch-8
answer and **`check.sh` now runs `printed_twice --self-test`** beside `name_agreement`'s, so it
cannot go red unwatched again. `rederive.mjs --run` to convergence, both back-projections
re-written, and the five steps the manifest does not cover re-run by hand.

### Two findings this stretch declined to take, recorded here rather than filed

1. **The 1837 poll's residents pool still has no forename rule.** It got this stretch's clause
   because a ruling of its own went unwritten; T-0670's first-forename rule is still not applied
   there, and `Timothy J Clark` against `Thomas A. Clark` was caught on the J and not on the
   Timothy. Two full forenames that disagree should be refused in that file too. It is a
   different rule in a different pool and it belongs to whoever takes the poll, not to this
   programme.
2. **`could_carry` moved and nothing re-read it.** Norris 1844's `could_carry_occupation` goes
   61 → 57 and `could_carry_address` 79 → 78 with the withdrawn matches, and the same in 1843.
   Those pools were closed by stretches 4-6 and the spend passes re-ran clean, so nothing is
   owed — but a stretch that withdraws matches shrinks a pool that a later stretch's arithmetic
   may quote, and this is the note that says so.

**Stretch 10 is the initial-absent refusals of Norris 1844**, 316 of them and the largest
single pool left after the ties: a surname the volume prints and an initial it does not, which
is what a page image can overturn, and Norris's scan is the cleanest of the three. The ties now
stand at 113 across the three volumes and are no longer the biggest thing on the table. No
successor ticket is filed: `tickets/README.md` puts the succession on the run that CLOSES the
programme. This ticket stays open and is its own cursor.

---

## Stretch 10 — the surname the crosswalk cannot see, 2026-09-12

**The pool named by stretch 9 was Norris 1844's 316 initial-absent refusals, and the bound
this stretch put on it is the part a source already committed to this repository can rule
on.** Three hundred and sixteen page reads do not fit in a run. Twenty-five do, and they are
the twenty-five the project had already been told about and never gone back to.

### Why a surname is not one refusal among many

`crosswalk_norris_1844.py` reaches an 1835 person through the surname and nothing else — a
fold, then the first initial. A destroyed surname therefore does not make a bad match. It
makes **no match and no refusal**, and the entry is not in any pool the ticket's table counts.
Downstream, nothing distinguishes a name the volume does not print from a name it prints that
this reading could not read. That is a hole in the denominator, not the numerator, and it is
invisible to every count this programme has quoted.

`data/research/directories/second_readings/norris_1844_genealogytrails.json` is where they had
been sitting since T-0576: Kim Torp's independent transcription against the committed OCR,
2,065 of 2,073 matched, **67 differ — and 25 of the 67 differ about the surname.** Six of the
twenty-five are named in that file's own README, in prose, with nothing done about them. Its
rule says a reconciliation lands in `../claims/` and is said there; nothing had.

### What the ink said

All twenty-five cropped from the archive.org leaf image on their own `generaldirectory19norr_djvu.xml`
word box and read by eye, then read a second time cold on the same crop — the discipline
T-0900/T-0903 set for forenames, one field along, with each row carrying its own leaf, leaf
pixel size and word box so the crop is reproducible.

| | n | where |
|---|---|---|
| the image prints the second hand's surname | **16** | `read_norris_1844.py` § `SURNAME_IMAGE_REPAIRS` |
| the image prints the COMMITTED surname; the second hand is wrong | **2** | § `SURNAME_UPHELD` — `Sealey` (she reads `Scaley (Sealy?)`), `Kautenburger` (she reads `Kantenburger`) |
| left alone | **7** | four firms whose ampersand the scan set `<fc`/`it`/`6c`/`A;`, which T-1018 refuses by name as its own ruling; two firms whose garbled span the firm branch never reads; `Jones, K. K.`, right already, disagreeing only about a margin speck |

The repair moves the READING only: `quote` and `as_printed` keep the damage, and every
repaired claim states both readings in `normalized.surname_repair`. `--self-test` fails if a
row stops matching exactly one entry, if a repaired entry stops reading its surname, or if the
damage the row asserts leaves the committed text.

**Five carried the name separator away with them.** Norris sets `Surname, Given`; this
printing sets a proportion of those commas with the tail unprinted, and the image shows a
clean round point after Bates, Gilmore, Griswold and Woodbury. T-1018's cap catches most of
that class but not a two-word run-on, so `Bates. John` had a forename of `jr`, `Woodbnry.
Hiram` none at all, and `Ryat). John` a trade of `boaniing`. The surname is DOCUMENTED, off
the image. That the point stands where the format sets a comma is INFERRED, and the reason is
stated: a surname is never abbreviated, so a stop immediately after one cannot be an
abbreviation point. Three of T-1018's sixty-nine overruns are healed at the source by this and
move to `OVERRUN_HEALED`, where the ratchet now asserts the opposite.

### The pools after this stretch

```
                        1839        1843        1844      1844 ad     total
  ties               37 -> 37    41 -> 41    24 -> 24    11 -> 11   113 -> 113
  initial-absent    260 -> 260  323 -> 323  316 -> 317  124 -> 124  1023 -> 1024
  forename-disagr.   68 -> 68    80 -> 80    46 -> 46     0 ->  0    194 -> 194
  matches           146 -> 146  115 -> 115  100 -> 100   18 -> 18   379 -> 379
```

**Nothing was placed, and clause 5 asks that this be said plainly.** Not one of the sixteen
carries an initial an 1835 namesake shares, so there is no new match, no trade onto a card and
no business onto a street face. What moved: **Levi Cady gains a named refusal where the volume
had been silent** — the one Cady entry Norris prints had been filed under `ady` — and seven
refusals that had been understating their own candidate counts are corrected (Bates 3→4,
Butterfield 1→2 twice, Griswold 3→4, Holmes 3→4, Jones 10→11, Ryan 1→2). The pool grew by one
because the book got bigger, which is the right direction for a hole in a denominator.

Clause 3, the write ceiling: `measure_research_spend.py` reads directories **883 reached, 883
judgeable, 883 on a card, 0 unwritten**, and the town total 0 — unmoved, as it should be when
a stretch lands no ruling on a card. `check.sh` green, 345 steps.
`compare_norris_1844_readings.py --check` rebuilds the comparison byte for byte, and that is
not luck: the comparison reads the claims' `quote`, and the repair leaves the quote damaged on
purpose, so the 67 stay 67. A comparison that healed itself as one side was corrected would
erase the record of what had been disagreed about.

### Stretch 11 — the other thirty-seven, and no second reading to find them

Measured on the reading this stretch leaves: **68 person entries still hold a space inside
their surname**, and twelve of them are real (`De Wolf`, `La Croix`, `Van Sickle`, `St.
Palais`), eight are institutions and headings, and eleven are the firm-conjunction class
T-1018 has already ticketed. **That leaves 37 entries whose surname hides them from the
crosswalk exactly as these sixteen did**, and the second reading does NOT flag them — it
agrees with the OCR, or Kim Torp's line is damaged too. Three classes:

* **27 the separator** — `Connell. John`, `Frink. John`, `Pierce. Asahel`, `Merriam. Mrs.
  Mary`, `Taylor. Solomon`, `White. Isaac`… the same unprinted comma tail, on a two-word
  run-on T-1018's cap cannot reach. These are the cheap ones: the rule is already argued
  above and each needs one crop to confirm the surname.
* **4 no separator at all** — `Bandlej Willis`, `Brown Clement`, `Butterfield George`,
  `Carson James`.
* **6 a surname the scanner broke in two** — `Went worth`, `Lurk in`, `Brine kerb off`,
  `Me Ward`, `Woi thinglnm`, `Van Dre/er`; T-1018 named four of these as `split_surname` and
  refused to cap them, which is still the right refusal and not yet a reading.

Sized: 37 crops off leaves already known, at roughly the rate this stretch managed, is one
run. No successor ticket is filed — `tickets/README.md` puts the succession on the run that
CLOSES the programme, and the pools are not empty. This ticket stays open and is its own
cursor.

## Stretch 11 — the other thirty-seven, read off the page image (T-0987, 2026-09-13)

Stretch 10 closed by naming this one: **37 person entries whose surname still hides them
from `crosswalk_norris_1844.py`**, measured off the reading it left. All thirty-seven are
ruled, and the count was right — 68 hold a space inside a surname, of which 12 are real
two-word names, 8 are institutions, 11 are the firm conjunction T-1018 owns, and 37 are
damage.

### The second reading had the answer, in the bucket nobody counts

Stretch 10 worked the 25 entries `norris_1844_genealogytrails.json` lists under `differs`.
Every one of these thirty-seven is in the same file's **`identical` or `agrees`** bucket —
Kim Torp prints `Brinckerhoff` where the scan prints `Brine kerb off`, `Larkin` for `Lurk
in`, `Wentworth` for `Went worth` — and the comparison folds punctuation and spacing
before it compares, so a surname split at a space, or closed by a point instead of a
comma, reads to it as agreement. The file's summary counts `differs` and the readings sat
there from T-0576 unlooked at. That is the finding as much as the thirty-seven are.

Every one was still cropped from the archive.org leaf image on its own word box and read
by eye, then read a **second time** on a fresh crop at a different magnification, in a
shuffled order so the first pass could not be carried down the page. Both readings are on
every row (`reread`). The second hand agrees with the image on all thirty-seven; where she
and the image disagree about something else — `Klein` for `Klien`, `Marsallam` for
`Marsallani`, `Asabel` for `Asahel` — the committed reading stands and the row says so.

### What the ink said, and where it corrects stretch 10

Stretch 10 wrote that this printing "sets a proportion of those commas with the tail
unprinted". Over the ten it read, that is what the image showed. Over the twenty-seven
separator cases here it is the **minority**:

| | n |
|---|---|
| a comma, tail and all, that the SCANNER read as a point | **15** |
| a round point on the baseline, nothing below it | **10** |
| undecided — the two passes disagreed (`Klien`, `Lahy`) | **2** |

So the usual cause is the OCR, not the compositor, and `separator_mark` on every row says
which this entry is. The two undecided rows stay undecided; the split does not depend on
it, because a full stop cannot follow an unabbreviated surname either way.

The remaining ten are not separator cases. Five surnames the scan broke into words —
**Brinckerhoff, Larkin, McWard, Wentworth, Worthingham** — one comma welded into the letter
beside it (**Bandle**), one real two-word surname with a damaged letter (**Van Drezer**,
whose z was set as a solidus, and which therefore belongs with Van Sickle and Van Vlack and
not with the damage at all), and **three where the comma is not in the ink**.

### Three rows are `inferred`, and that is the point

`Brown Clement`, `Butterfield George` and `Carson James` show clean paper between surname
and forename at sixteen times magnification — no comma, no point, no mark. The letters are
DOCUMENTED; the separator this reading supplies is not, so those three rows carry
`confidence: inferred` and the reasoning: Norris sets `Surname, Given` throughout, and a
forename standing alone after a surname is that format with its comma omitted. Nothing
else in the entry moves, and `--self-test` fails if a row stops matching exactly one entry.

The whole `split_surname` class T-1018 refused to cap — its four entries — is repaired at
the source and moves to `OVERRUN_HEALED`, where the ratchet now asserts the opposite.

### What landed on the ground

**Three people of 1835 gain their 1844 line**, which is the first time this programme has
placed anything since stretch 7:

* **Tuthill King** — `King. Tuthill, clothing, dry goods, &c., 115 Lake st. h Clark st`.
  Fergus 1839 has him at 115 Lake and Fergus 1843 at 115 Lake with a residence at 198
  Clark; Norris corroborates both premises five years after the first.
* **Asahel Pierce** — `Pierce. Asahel, blacksmith. S. Water st. b Lake and Randolph sts
  house Lake st. 4th ward`. He is the one of the three with an 1835 trade and a placed
  1835 shop, so the address ledger rules it `already_better_placed`; what the line records
  is that he had moved off Market Street, where Fergus 1839 printed him.
* **John P. Simpson** — `Simpson. John, mason, house Canal st. b Adams and Jackson sts`,
  the same address Fergus 1843 prints, eight years after the scene and corroborating it.

**No new street face is placed, and clause 5 asks that this be said plainly.** The card
carries ONE `address_later` per person — the volume nearest 1835 — and all three already
held a nearer 1839 or 1843 address, so `back_project_addresses.py` and
`back_project_residences.py` re-derive byte for byte. What the 1844 lines add is
corroboration and a trade, on the card and in `data/residents/directories.json`.

Of the thirty-seven, **4 now touch an 1835 person at all** — the three matches and one
forename refusal. The other 33 have no 1835 counterpart, which is what nine years does to
a directory and is not a shortfall.

### The pools after this stretch

```
                        1839        1843        1844      1844 ad     total
  ties               37 -> 37    41 -> 41    24 -> 24    11 -> 11   113 -> 113
  initial-absent    260 -> 260  323 -> 323  317 -> 315  124 -> 124  1024 -> 1022
  forename-disagr.   68 -> 68    80 -> 80    46 ->  47    0 ->  0    194 -> 195
  matches           146 -> 146  115 -> 115  100 -> 103   18 ->  18   379 -> 382
```

Clause 3, the write ceiling: `measure_research_spend.py` reads directories **889 reached,
889 judgeable, 889 on a card, 0 unwritten**, and the town total 0. The three matches were
spent in the same run — `spend_directories.py` wrote the layer, the ledger and the cards,
and because a new match re-grades nothing but does re-derive the identity master,
`consolidate_resident_evidence.py --build`, `mint_civic_residents.py --build` and the three
per-domain spends that write onto a re-minted card (Fergus 1839 later lists, the land tract
sales, the old-settlers citation) were run behind it. `check.sh` green, 359 steps.

### Stretch 12 — the same defect, in the Fergus volumes

Measured on the reading this stretch leaves: **Fergus 1843 holds 63 person entries with a
space inside the surname and Fergus 1839 holds 11**. Setting aside the 9 institutions and
the one real particle in 1843, and the 1 institution, 1 particle and 2 firms in 1839:

* **26 in Fergus 1843 are the separator class** — `Boyington. Charles H`, `Calighan.
  Mathew`, `Carr. William`, `Cook. George`… the same mark, on a volume with its own scan
  and its own compositor, so the comma/point split this stretch measured for Norris is an
  open question there and not an answer carried over.
* **2 more in 1843 have no separator at all** — `Harding Charles`, `Seger Joseph`.
* that is **28**, and at the rate this stretch managed it is one run. The six
  page-citation run-ons 1843 also holds (`84-5-6] Cutmore`, `46] Smith`, `59] Wright`…)
  are a DIFFERENT defect — a previous entry's bracketed page number running onto the next
  line — and belong with Fergus 1839's eight in the stretch after.

No successor ticket is filed: `tickets/README.md` puts the succession on the run that
CLOSES the programme, and the pools are not empty. This ticket stays open and is its own
cursor.

## Stretch 12 — the separator Fergus 1843 sets as a point, and the second reading this repository already held (T-0987, 2026-09-13)

Stretch 11 closed by naming this one: the same defect as Norris 1844's, in the Fergus
volumes. **Its sizing does not survive measurement and this stretch says so first.** It
counted "26 in Fergus 1843 … the separator class" and "2 more with no separator at all";
measured on dev at 1e82d25c2, the separator class is **24**, because the 26 included
`Eagle Tavern. 10 Dearborn`, which is a house and not a person, and `Jan. 18`, which is
not an entry at all. 24 + 2 = **26 person entries** whose surname runs on into the
forename. The other 37 of the 63 that carry a space inside a surname are 30 institutions
and real particles (`St. Palais`, `Farmers' Exchange`, `Young Men's Association`), 6
page-citation run-ons, and `Jan. 18`.

### Why a run-on surname is not one refusal among many

The argument is stretch 10's, one volume along. `crosswalk_fergus_1843.py` reaches an 1835
person through the surname and nothing else, and `split_entry` takes the surname to be
everything before the first comma — which is the format Fergus sets. Where the compositor
set a POINT the head runs on, the surname is `Cook. George`, and the entry makes **no match
and no refusal**. It is in no pool this ticket's table counts. The write-up quoting "323
initial-absent refusals in 1843" was quoting a denominator 26 entries short, and nothing
downstream could tell a name the volume does not print from a name it prints that this
reading could not read.

### The second hand, and it was already committed here

The committed text of this domain is K. Torp's 2007 transcription on Genealogy Trails.
This repository ALSO holds `data/research/books/text/fergus_26_29.txt` — the Internet
Archive's own OCR of the PRINTED volume, item `fergushistorical2629unse`, the Allen County
copy, of which **No. 28 is this directory** (source record `fergus_historical_series_26_29`,
deposited on T-0499/T-0500 for the civic pages). Two independent extractions of one
printing, neither made from the other, sitting in the same repository for ten days without
being set against each other. No fetch was needed for this stretch and none was made.

Every row in `read_fergus_1843.py` § `SURNAME_SEPARATOR_REPAIRS` carries what that second
hand prints, verbatim with its own OCR damage, so the comparison re-runs.

### What the two hands said, and the confidence follows it

| | n | reading | confidence |
|---|---|---|---|
| the printed volume sets a COMMA where this transcription sets a point | **5** | Boyington, Goodwin, Graff, Houfe, Tarbox | `documented` |
| the printed volume sets a COMMA where this transcription sets NOTHING | **2** | Harding, Seger — the whole no-separator class | `documented` |
| BOTH hands read the point | **18** | Calighan, Carr, Case, Constantine, Cook ×2, Cooley, Corbidge, Fish, Gauch, Heald ×2, Herrick, Howe, Lyman, Mann, Munson, O'Neil | `inferred` |
| left alone | **1** | Glansman | — |

The eighteen are `inferred` and the reason is stated rather than assumed: the letters are
documented — two readings agree on them — but that the point stands where the format sets
a comma is the inference, and it rests on stretch 10's argument that a surname is never
abbreviated, so a stop immediately after one cannot be an abbreviation point. **The five
rows above them are the corroboration that argument had lacked.** In five places out of
twenty-three the second hand reads the comma outright, which makes the point a defect
class in this printing rather than a punctuation Fergus chose.

**Glansman is left alone, and the reason is the second hand's.** `Glansman. John, butcher,
Western Market, cor N. Water and Clark` carries the same point as the eighteen. But the
printed volume's OCR dropped the head of that line: between `Gilson` and `Gleason` it runs
`…AVater and Clark | Trleason, Alichaol, cooper…` and prints no name. The one argument the
eighteen rest on — two hands agreeing on the letters — is unavailable, and repairing him
would be assuming the class rather than reading it. The entry is not spurious: its own tail
is in the second hand, in the right place in the alphabet.

**The repair moves the READING only.** `quote` and `as_printed` keep the damage — a tidied
quote cannot be found again — and every repaired claim states both readings, the verdict
and the second hand's own line in `normalized.surname_repair`. Nothing was fetched, no
confidence was raised to make a count look better, and `docs/LIBERTIES.md` gains no entry
because nothing was invented.

### What landed on the ground

**Three people of 1835 gain their 1843 entry**, and one of the three is a knock-on rather
than a new reading:

* `herrick_ira` → `f1843_e1256`, *Herrick, Ira N., contractor*
* `cook_josiah_p` → `f1843_e0696`, *Cook, Josiah P., baker, res Michigan ave*
* `cook_john` → `f1843_e0695`, *Cook, John* — **not a repaired entry.** It had been
  CONTESTED: with Josiah's own line invisible, two residents stood against one entry and
  the crosswalk refused both. Josiah taking his own line released the contest, and John
  Cook's match is what the pool had been hiding.

**Seventeen identities enter `identity_master.json`, every one at `not_1835_resident`
(rule G0).** That is the honest half of the repair and it is the direction a closed hole
in a denominator moves: the book got bigger, the town did not.

**No grade was raised.** One `resident_subtype` moved: `herrick_ira` loses
`projected_resident` under G2e, by the committed rule and on an exact forename agreement —
`projected_resident` means *documented once and corroborated by nothing else*, and he is
now printed in a second source class. The grade stayed `inferred`. `--regrade` reports
`direction: subtype_only` and the synthesis records it: projected residents 733 → 732,
letter-list people carrying a ladder rung 65 → 66.

### The pools after this stretch

```
                        1839        1843        1844      1844 ad     total
  ties               37 -> 37    41 -> 40    24 -> 24    11 -> 11   113 -> 112
  initial-absent    260 -> 260  323 -> 323  315 -> 315  124 -> 124  1022 -> 1022
  forename-disagr.   68 -> 68    80 -> 81    47 -> 47     0 ->  0    195 -> 196
  matches           146 -> 146  115 -> 118  103 -> 103   18 ->  18   382 -> 385
```

The 1843 ties fall by one because a contest was released, not because a tie was decided.
The forename-disagreement pool GAINS one, which is the right direction too: an entry that
used to be invisible is now visible enough to be refused for a reason.

Clause 3, the write ceiling: `measure_research_spend.py` reads directories **895 reached,
895 judgeable, 895 on a card, 0 unwritten**, and the town total 0. The three matches were
spent in the same run — `spend_directories.py` wrote the layer, the ledger and the cards,
and `consolidate_resident_evidence.py --build`, `mint_civic_residents.py --build` and
`--regrade`, `spend_ladder_rungs.py`, `qualify_later_trades.py` and both back-projections
were iterated to a fixpoint behind it (two passes; the second changed nothing), then
`synthesize_resident_research.py`, `export_resident_audit.py --build` and
`compile_scene.py --all`. `check.sh` green, **372 steps, none red**.

### The gates

`read_fergus_1843.py --self-test` is new and is wired into `check.sh` beside the existing
`--check`. It is a ratchet on four ways the table rots: a row stops matching exactly one
entry; a repaired entry stops reading a bare surname; a repair TIDIES the quote it was
meant to leave damaged; or a new run-on surname arrives with no row. It also holds the
counts of what stands outside the table — 6 page-citation run-ons, 30 institutions and
particles — and asserts that the confidence of every row still follows its verdict, so a
row cannot be quietly promoted from `inferred` to `documented`.

### Three findings this stretch declined to take, recorded here rather than filed

* **`f1843_e1434` is not an entry.** `Jan. 18, 1868, aged 77¼.` is the tail of the
  preceding entry's obituary bracket, wrapped onto its own line by the transcription and
  segmented as an entry of its own. It has the run-on shape and none of the defect: there
  is no surname to repair. A segmenting fault, named in `SURNAME_SEPARATOR_LEFT_ALONE` so
  the ratchet does not have to file it under institutions, which it is not.
* **`f1843_e0561` carries two entries on one line.** Torp runs `Case. Elan, carpenter,
  Scoville & Gates` straight into `Case. John Roman (Norton & C), bds City Refectory`; the
  printed volume sets them as two, and reads the second with a comma. The surname repair
  reaches Elan Case and leaves John Roman Case inside the occupation field. Splitting it
  would change an entry count `coverage.json` declares, which is a different defect and a
  different ticket's.
* **`Cook. Isaac` and `Cook. Thomas` are in the second hand and not in the pool.** The
  printed volume sets a point after both; Torp reads a comma. That is the same compositor
  defect, caught by the transcription rather than propagated by it — evidence for the
  eighteen, and nothing to repair.

### Stretch 13 — the page citations, and Fergus 1839's own eleven

**Stretch 12's filing said "Fergus 1839's eight" page-citation run-ons. There are none.**
Measured on this branch: Fergus 1839 holds **0** person entries whose surname carries a
digit or a bracket, out of 1,584. The reason is the corpus, not the printer — Fergus 1839's
committed text is archive.org's OCR of the scan (`fetch_fergus_1839_pages.py`), while the
bracketed page citations are an artefact of the 1843 WEB transcription, where Torp
interpolates a cross-reference that the segmenter then takes for the head of the next line.
So the defect is one volume's and one corpus's.

What is actually left, and it is small:

* **6 in Fergus 1843, the page-citation run-on** — `84-5-6] Cutmore`, `84.] Lindebner`,
  `74.] Loomis`, `71.] Otis`, `46] Smith`, `59] Wright`. All six hide a real person with a
  real trade, Theophilus Washington Smith and Mrs Hulda Wright among them, and the printed
  volume can be asked about every one of them the way this stretch asked about the
  twenty-six.
* **7 workable in Fergus 1839**, out of the 11 that carry a space inside a surname: 3 with
  no separator (`Densmore Eleazer W`, `Johnson John`, `Scammon J. Young`) and 4 the scanner
  broke in two (`Gilbert on`, `Snow hook`, `Stark weather`, `Wick wire`). The other 4 are
  `St. Palais`, `State Bank Branch`, and the two `Wheeler k` firms whose ampersand the scan
  set as a `k` — T-1018's class, not this one. **A second hand for 1839 is an open question
  this stretch did not settle:** its committed text is already the archive.org OCR, so the
  second reading would have to be the genealogytrails transcription of the same volume, and
  whether one exists has not been checked.

Thirteen entries, of which six can be ruled off a source already committed. One run, and
comfortably. No successor ticket is filed: `tickets/README.md` puts the succession on the
run that CLOSES the programme, and the pools are not empty. This ticket stays open and is
its own cursor.


## Stretch 13 — the age read as a surname, and the surname the scan broke in two (T-0987, 2026-09-13)

Stretch 12 named this stretch and sized it at thirteen entries: "6 in Fergus 1843, the
page-citation run-on" and "7 workable in Fergus 1839". **The count is right and the
diagnosis is not, and this stretch says so before it repairs anything.** There is no page
citation. Every one of the six is the TAIL OF THE OBITUARY BRACKET ON THE ENTRY ABOVE,
wrapped by the transcription onto the next line and closed there:

```
  Cushing, Nathaniel Sawyer, house painter, 41 State near Lake, res same [died, Lombard, Ill., May 13, 1889, aged
  84-5-6] Cutmore, Henry, grocer. West Randolph, bet W Water and Canal
```

`84-5-6` is an age — eighty-four and five-sixths, the fraction Fergus sets for a part
year — and it is CUSHING's. The same for `84.]` (Lind), `74.]` (Long), `71.]` (Otis, Seth
T.), `46]` (Smith, Samuel P.) and `59]` (Wright, John Stephen). So the defect is
`f1843_e1434`'s, one step worse: there the wrapped tail became a nameless entry of its
own, here a REAL person follows it on the same line and is filed under the age.

### The correction that matters more than the six: what the hole actually was

Stretches 10 to 12 all rest on one sentence — a surname carrying a space makes no match
and no refusal, so the entry is in no pool this ticket counts. **Measured against
`name_agreement.fold`, that is true of the class those stretches repaired and FALSE of
this one.** `fold` strips whitespace and punctuation:

```
  fold('Cook. George')          -> 'cookgeorge'     the forename is IN the key: invisible
  fold('84-5-6] Cutmore')       -> 'cutmore'        reaches the right shelf already
  fold('Stark weather')         -> 'starkweather'   reaches the right shelf already
  fold('Densmore Eleazer W.')   -> 'densmoreeleazerw'  invisible
```

The defect that hides an entry is **the head running on into the FORENAME**, not a space
inside the surname. Stretch 12's twenty-five rows are that shape and its argument holds
for them. Of this stretch's thirteen, only THREE are — the 1839 comma-absent heads. The
other ten were reaching the crosswalk all along, and what was lost was the READING: who
the person is, what the trade is, where the obituary ends. That is why the pools below
barely move and the book grows anyway, and it is the honest size of this pool.

### Fergus 1843 — six obituary tails, cut back onto the entry above

The segmenter already had the answer and never reached it. `alpha_entries` cuts an entry
mid-line and locates both halves with `spans` — the seven run-ons of page 2 go that way.
These six never got there because the test for "does an entry begin here" strips leading
non-letters before it looks, so the line PASSES and is then recorded from column 0, junk
and all. `OBITUARY_TAIL_RUN_ONS` takes the same cut at the bracket. No new locator kind, no
new claim, and 2,695 entries before and after, which is what `coverage.json` declares.

**The second hand is stretch 12's, and it settles all six**, so every row is `documented`:
the Internet Archive's OCR of the printed volume closes the age onto the obituary above and
sets the next entry after it in each case — `[died, Ann Arbor, Mich., January 23, 1S82,
aged 71. r^tis, Seth, county ])Oor-house keeper`. Nothing was fetched.

### Fergus 1839 — seven, and there is no second hand for this volume

Eleven person entries carry a space inside their surname. Four stand outside and are not
this defect: `St. Palais`, `State Bank Branch`, and the two `Wheeler k` firms whose
ampersand the scan set as a `k` (T-1018's class). The seven are two shapes:

| | n | rows |
|---|---|---|
| the scan broke one surname in two | 4 | Gilbert on, Snow hook, Stark weather, Wick wire |
| the comma is absent and the head runs on | 3 | Densmore Eleazer W., Johnson John, Scammon J. Young |

Stretch 12 left "is there a second hand for 1839?" open. **There is not** — the committed
text here is ALREADY archive.org's OCR of the Allen County scan, so stretch 12's trick has
nothing to set against it. This stretch answers a different question instead, and every row
cites a committed witness or admits it has none:

* **the same volume, elsewhere.** `Gilberton, Ralph, laborer,` is the NEXT LINE after
  `Gilbert on, Francis, laborer,` on leaf 27 — one surname set twice on one page, broken
  once. `J. Young Scammon,` is set whole in the volume's own subscriber list on leaf 54,
  with four further `J. Y. Scammon` printings.
* **a later directory**, a different printing and a different transcription: Fergus 1843
  through stretch 12's second hand (`Starkweather, Charles Robert, assistant postma-ter`;
  `Densmore, Eleazer "Woodworth, clerk.`) and Norris 1844 (`Snowhook, W.B., grocer`;
  `Starkweather, C. Robt, ast P.M.`). The Calumet Club's 1879 registry prints `Densmore,
  Eleazer W. | 1835, Sept.`
* **the alphabet**, which every row passes and none rests on alone: `Snowhook` between
  `Snow, Ira` and `Soden`, `Wickwire` between `Wicker, Joel II.` at the foot of leaf 47 and
  `Wiggins` at the head of 48.

**Five are `documented` and two are `inferred`, and the two say why.** `Wick wire` is the
one row of the seven no committed source speaks for in any spelling — the format and the
alphabet are its whole argument. `Johnson John` has no hand printing a separator for that
line; `Johnson, John` is printed with its comma by Fergus 1843 and Norris 1844, but of
OTHER men, which is exactly why it is not `documented`.

### What landed, and what did not

**Four identities enter `identity_master.json`** — `id_cutmore_henry`,
`id_lindebner_joseph`, `id_smith_theophilus_washington`, `id_wright_hulda` — each standing
in one domain, none of them a person of 1835. Appearances 10,540 → 10,546 (the six 1843
entries; Loomis and Otis folded onto identities already there) and derived refusals 1,827 →
1,821. The book got bigger; the town did not, and clause 5 is answered plainly: **this
stretch placed nothing on the ground.** Not one of the thirteen is an 1835 resident.

**One thing a reader sees.** `f1843_e2675` — John Stephen Wright, founder of the Prairie
Farmer — is quoted on three contested Wright rulings, and the quotation used to end at
`aged` and now ends at `aged 59`, with the obituary out of the occupation field and into
`death_note_1843` where it belongs. The same repair cleans `occupation_1843` and
`address_1843` on all six.

**No grade moved, no confidence was raised, `docs/LIBERTIES.md` gains nothing** — nothing
was invented. `mint_civic_residents --regrade` reports 0 regraded.

### The pools after this stretch

```
                        1839        1843        1844      1844 ad     total
  ties               37 -> 37    40 -> 40    24 -> 24    11 -> 11   112 -> 112
  initial-absent    260 -> 260  323 -> 323  315 -> 315  124 -> 124  1022 -> 1022
  forename-disagr.   68 -> 68    81 -> 81    47 -> 47     0 ->  0    196 -> 196
  matches           146 -> 146  118 -> 118  103 -> 103   18 ->  18   385 -> 385
```

**Nothing moves, and that is the finding, not a failure of the stretch** — see the
correction above: ten of the thirteen were already folding to the right shelf, so repairing
their reading cannot move a pool. The one composition change is inside a bucket: `Johnson
John` becomes the 8th candidate under `Johnson` on three no-forename rulings, where there
were 7.

Clause 3, the write ceiling: `measure_research_spend.py` reads directories **895 reached,
895 judgeable, 895 on a card, 0 unwritten**, town total 0 — measured before and after and
identical, so no spend was lost. The chain was iterated behind the readings:
`spend_directories.py`, `consolidate_resident_evidence.py --build`, `mint_civic_residents
--build` and `--regrade`, `spend_ladder_rungs.py`, `qualify_later_trades.py`, both
back-projections, `synthesize_resident_research.py`, `export_resident_audit.py --build`.

### The gates

`read_fergus_1839.py --self-test` is NEW and is wired into `check.sh` beside its `--check`,
matching what stretch 12 built for 1843. Both ratchets hold four ways their table rots: a
row stops firing, a repaired entry still reads a spaced surname, a repair TIDIES the quote
it was meant to leave damaged, or a new broken surname arrives with no row. 1843's
`PAGE_CITATION_RUN_ONS = 6` becomes `OBITUARY_TAIL_RUN_ONS_LEFT = 0` and gains a sixth
check: every cut still fires on BOTH halves and the age still closes the obituary above.

### Stretch 14 — the ties, which stretch 12 said were next and are

With the thirteen closed, the reading defects this ticket knows of in Fergus 1839 and 1843
are empty: 4 spaced surnames standing in 1839 (St. Palais, the State Bank Branch and
T-1018's two `Wheeler k` firms) and in 1843 the 30 institutions and particles plus the 2
stretch 12 left alone with its reasons. The pools are what is left, in the order
this ticket sets: **the 112 ties first** — 37 in Fergus 1839, 40 in Fergus 1843, 24 in
Norris 1844, 11 in the advertiser — and a tie is one page-read from a match. Stretches 3, 7
and 9 each took one volume's ties under T-0696's rule (a trade may narrow a tie, a premises
may not); 1839's 37 are the largest single pool left and nothing has been run on them since
stretch 3. After the ties, the 1,022 initial-absent refusals, beginning with the volume
whose scan is best. No successor ticket is filed: `tickets/README.md` puts the succession on
the run that CLOSES the programme, and the pools are not empty. This ticket stays open and
is its own cursor.


## Stretch 14 — the whole printed name, which nothing had ever read past its first letter (T-0987, 2026-09-13)

Stretch 13 named this stretch: "the 112 ties first — 37 in Fergus 1839, 40 in Fergus 1843, 24
in Norris 1844, 11 in the advertiser — and a tie is one page-read from a match." **No page was
read.** Every one of the 112 could be ruled off text this repository has held since the volumes
were transcribed, and the reason they were standing is the same in all four files.

### The hole, stated once

The crosswalks make a candidate on SURNAME PLUS FIRST INITIAL. Everything the compositor set
after that letter — `Byram` against a `Byra`, `John S. C.` against a bare `John`, `Elston,
Daniel T.` beside `Elston, Daniel` — was read, transcribed, committed and never weighed. Two
shapes of tie come out of that, and they are one piece of arithmetic with the arguments
swapped:

* **AMBIGUOUS** — one person of 1835, several printed entries under the initial.
* **CONTESTED** — one printed entry, several people of 1835 under the initial.

T-0987 stretch 9 built the further-initial comparison **for the first of the two only**, and it
compares only the initials BOTH readings set, so a reading that stops early is a silence and
refuses nothing: `H. B. Clarke` against `Clarke, Dr. Henry` and `Clarke, Henry B.` sets a B that
neither entry contradicts, because the first prints no second word at all. **Nothing in the
chain had ever run on the contest axis.** Not one line in four crosswalks asks which of two
people of 1835 a printed entry names; the collision is detected, filed, and answered "neither".

### The ruling — `tools/named_by_the_page.py`, imported by all four

A printed forename and a reading of 1835 are THE SAME NAME when they set the SAME NUMBER OF
WORDS and agree word by word. Where exactly one candidate is that name, and more closely than
any rival, the page names it. The fits are RANKED, and the ranking is the whole of it:

```
  0  letter for letter                     Byram against a printed Byram
  1  a contraction or a one-letter         Russel against Russell, Byra against Byram
     spelling variant — na.agrees' own
     tolerance, not a new one
  2  a single initial for a whole word     R. against Russell
```

An initial is the weakest because an initial fits every man of the letter. Run without the
ranking the clause named `Heacock, jr., R. E., civil engineer, on the canal` for **Russel E.
Heacock** — the attorney, Chicago's first lawyer — over `Heacock, Russell E., att'y, justice of
peace, Adams cor. Clark`, on nothing but a doubled L. It was caught before it landed and the
ranking is what fixes it.

**The word-count test makes the rule fire on what a reading SAYS and never on what it omits.**
`Hogan, John S. C.` sets three words, the town's John S. C. Hogan sets those three and its bare
John Hogan sets one: the fit is the reading that SPOKE and was right, never the one that was
silent. That is the safe direction of stretch 9's own warning. `Cook, John, tailor` against
`J. B. Cook`, baker, still decides nothing — one word against two, no fit, the tie stands.

**It is not a discriminator.** T-0696 rules that a trade may narrow a tie, a premises may not,
and a narrowed tie is filed `discriminated` and never promoted. Nothing here weighs a trade, a
premises or a year. This is the MATCHING RULE, which was always about the name, applied to the
whole of the name instead of its first letter — so a single survivor is a match by the
crosswalk's own rule, exactly as `narrow_by_further_initials` already works.

### Three things it refuses to do, and each cost more than it gave

1. **A WIFE IS NOT HER HUSBAND — R6 arriving where it was always true.** The identity layer
   holds `Mrs Rufus Brown` apart from `Rufus Brown` (R6, T-0723) because the honorific strip
   leaves the husband's forename tokens on both readings. The crosswalks strip titles the same
   way and had no such rule, so the town's wife and the town's husband met `Brown, Rufus B.,
   warehouseman, Bristol & Porter` together and were filed as a CONTEST — a man contesting a
   printed line with his own wife. **R6's guard is kept as it stands: one body has to set both
   readings.** Fergus 1843 prints `Brown, Rufus B.` at e0458 and `Brown, Mrs. Rufus B., dress
   and cloak maker, 189 Lake, up stairs` at e0459, so the volume separates them and each takes
   her own; **Mrs Seth Johnson** keeps her boarding-house and **Capt. Seth Johnson** the custom
   house. Where no candidate agrees the clause refuses NOTHING, which is what keeps it off
   `Taylor, Mrs. C.` — T-0960 has already ruled that no page holds her pair, and her tie stands.
2. **A SON IS NOT HIS FATHER.** `name_agreement.tokens` strips `jr.` before anything is
   compared, so Fergus 1843's `Heacock, Russel E., jr., clerk, Charles Walker & Co.` arrived
   letter for letter identical to the town's Russel E. Heacock and beat `Heacock, Russel
   Easton` on the spelling. Where the page separates two generations and the reading of 1835
   says nothing about which it holds, the comparison DECLINES — choosing the unsuffixed one on
   the town's silence is the move stretch 9 refuses by name. Heacock keeps no 1843 line rather
   than his son's; `King, John, jr., fancy dry goods` is left standing for the same reason.
   Only JR/SR are weighed: `namesake.suffix_of` reads ESQ and 2D as well, and neither separates
   a father from a son.
3. **A PAGE THAT SETS FEWER WORDS THAN A READING SEPARATES NO TWO READINGS** — and this is the
   one place the two axes are not the same rule. Where the candidates are the entries of ONE
   VOLUME, a word one sets and another does not is the volume's own distinction: R6 states the
   principle and this borrows it, *a directory does not enter one person twice under two
   spellings*, so Fergus 1839 printing both `Elston, Daniel, brickmaker, Elston road` and
   `Elston, Daniel T., student` has separated two men and the town's bare Daniel Elston is the
   bare entry. Where the candidates are READINGS OF 1835 that guarantee is gone, and **this
   programme is the reason** — the town demonstrably holds one man on two cards, `Byra` and
   `Byram` King, `Ordemus` and `Orsemus` Morrison. So on the contest axis a page setting fewer
   words than some reading decides nothing: Norris's advertising card for `E. Smith` fits
   **Elded Smith** exactly and **E. Kirby Smith** not at all, and the only thing standing
   between them is a word the compositor did not set. Caught and refused before it landed.

And the unreadable stops everything: stretch 9's stroke artefacts (`Collins, Jas. PL`, `Anson
IT`) make the whole comparison DECLINE rather than fail, which is the direction that invents
nobody.

### Measured, before and after

| | 1839 | 1843 | 1844 | 1844 ad | total |
|---|---|---|---|---|---|
| matches | 146 → **165** | 118 → **135** | 103 → **112** | 18 → **19** | 385 → **431** |
| ambiguous | 25 → **10** | 27 → **15** | 14 → **9** | 3 → **3** | 69 → **37** |
| contested | 12 → **2** | 13 → **2** | 10 → **2** | 8 → **6** | 43 → **12** |
| **ties standing** | 37 → **12** | 40 → **17** | 24 → **11** | 11 → **9** | **112 → 49** |
| initial-absent refusals | 260 | 323 | 315 | 124 | 1,022 — **unmoved** |

**Forty-six matches, and not one of them is a new reading**: every one is a printed line this
repository already held, ruled onto the person it already named. The refusals are filed in full
— `whole_name_refusals`, `female_honorific_refusals`, `not_named_by_the_page`,
`held_off_a_husbands_entry` — each naming its clause, and a declined comparison is recorded on
the tie as `whole_name_declined` so that a decision NOT to act reads like the reading it is.

### What a reader can see

**John S. Wright**, founder of the Prairie Farmer, takes his forwarding business onto **North
Water Street** off `Wright, John S., forwarding commission merchant, N. Water st` — the
eighteenth business standing on a back-projected face, carried four years, the narrowest gap in
the set, and **L218 is restated 17 → 18** with the reason. The town's bare **John Wright** takes
`Wright, John, Michigan ave. cor. Madison st` by the same clause, which is why the stretch adds
one face rather than moving one. On the cards: **Henry B. Clarke** at Michigan Avenue and 16th,
against a `Clarke, Dr. Henry` of 159 Lake; **Ira Couch** the hotel-keeper at the Tremont House,
against his son boarding there; **Major James B. Campbell**'s real-estate office on North Clark
against two other James Campbells of the same page; **William Hubbard Brown**, cashier at 8
LaSalle and school agent, whose 1843 and 1844 entries had both been ambiguous three ways.

**And two heads on the 1840 sheets stop being guesses.** `crosswalk_census_1840_heads.py`
adjudicates against these same pools, so **Samuel C. Jackson** (printed 207, line 5) and **Chas
Taylor** (printed 224, line 13) move `candidate → matched`: 13 matched → 15. Nothing was
back-projected from 1840 and no grade moved.

### Clause 3, the write ceiling

`measure_research_spend.py`, whole town: directories **987 reached, 987 judgeable, 987 on a
card, 0 unwritten** (dev: 941/941/941/0 measured on the same tree before the chain ran), town
total **0 unwritten**. The `unwritten_ceiling` for directories is tightened 1 → 0 in the same
commit so it cannot regrow, and the unspent ceiling 7,315 → 7,279. The chain was iterated to a
fixed point behind the readings: `spend_directories`, `consolidate_resident_evidence --build`,
`mint_civic_residents --build` and `--regrade`, the six other spend passes,
`spend_ladder_rungs --build`, `qualify_later_trades`, both back-projections,
`crosswalk_census_1840_heads --build`, `consolidate_town_cards --apply`,
`synthesize_resident_research`, `export_resident_audit --build` and `compile_scene --all`.
**0 regraded** (`mint_civic_residents --regrade`), nothing minted, `docs/LIBERTIES.md` gains
nothing invented.

### The gates

`tools/named_by_the_page.py --self-test` is NEW and wired into `check.sh`: 22 printed names
weighed word for word, the ranking that keeps the attorney off his son's entry, the two-fits
refusal, both directions of R6, both directions of the suffix clause, and the one-body guard in
both of its states. `./tools/check.sh` — **382 steps, none red**.

### The pools after this stretch

```
                        1839        1843        1844      1844 ad     total
  ties                37 -> 12    40 -> 17    24 -> 11    11 ->  9   112 -> 49
  initial-absent     260 -> 260  323 -> 323  315 -> 315  124 -> 124  1022 -> 1022
  matches            146 -> 165  118 -> 135  103 -> 112   18 ->  19   385 -> 431
```

**Stretch 15 is the 1,022 initial-absent refusals, beginning with Fergus 1843**, whose scan is
the best of the four and for which stretch 12's second hand — the Internet Archive's OCR of the
printed volume — is already committed and already used twice. Those 1,022 are now the largest
pool in the programme by a factor of twenty, and the 49 ties that remain are each one of three
things the page cannot settle: two entries fitting equally (`Noble, Mark` twice, `Cook, John`
twice), a page saying less than the readings offered it (`Clark, John` between a John A. and a
John K.), or a generational suffix this town's record does not answer. No successor ticket is
filed: `tickets/README.md` puts the succession on the run that CLOSES the programme, and the
pools are not empty. This ticket stays open and is its own cursor.

### Stretch 14 re-measured on the merged tree (the lap of 2026-09-14)

The table above is a reading of the tree the stretch was worked on. `dev` moved seventy-odd
commits under the branch before it landed — T-1110, T-1122 and T-1123 among them — and the
residents layer gained cards, so the crosswalks were re-derived on the merged tree and the
pools are restated here rather than edited above:

```
                        1839        1843        1844      1844 ad     total
  matched              165 -> 163  135 -> 136  112 -> 113   19 -> 19   431 -> 431
  ambiguous             10 ->  11   15 ->  15    9 ->   9    3 ->  3    37 ->  38
  contested              2 ->   4    2 ->   2    2 ->   2    6 ->  6    12 ->  14
  ties standing         12 ->  15   17 ->  17   11 ->  11    9 ->  9    49 ->  52
```

**The total of matches does not move**: 431 before, 431 after. What moved is the distribution,
and in the direction a new card is supposed to move it — two 1839 entries that named exactly
one person now name two, so they go back to the tie pool, and one entry each in 1843 and 1844
that named nobody now names somebody. Nothing was regraded to hold the number still. The
figure the next stretch works from is **52 ties, 1,022 initial-absent refusals**; the stretch
named for it is unchanged, the 1843 initial-absent pool.

---

## Stretch 15 — the page had already been read, and what the pool turned out to be a symptom of (T-0987, 2026-09-13→14)

Stretch 14 named this stretch and the owner's amendment of 2026-09-14 set its method:
**the 1,032 initial-absent refusals, beginning with Fergus 1843 whose scan is the best of
the four, and A STRETCH AGAINST THAT POOL READS A PAGE, NOT A NAME** — because one image
carries dozens of entries and one read per refusal is what made the pool cost two hundred
runs. That is what was done, and the answer came back in the direction nobody had priced.

### The page was read. It overturned nothing, and that is the finding

The whole alphabetical directory of the PRINTED volume — pages 31 to 103 of Fergus'
Historical Series No. 28, the Internet Archive's own OCR of the Allen County copy at
`data/research/books/text/fergus_26_29.txt`, committed here since T-0499 and set against
Torp's transcription twice before (stretch 12) — was put against all **326** initial-absent
refusals of `fergus_1843_crosswalk_1835.json`, over **252** surnames. 2,194 entry heads came
off those pages; 1,201 of them carry a surname this repository's reading already holds
letter for letter, and the rest carry the OCR's own damage to a surname it also holds.

**Not one printed entry sets a surname-plus-initial that the committed reading lacks.**
Three looked at first as though they might — `Carpenter, AVilliam`, `Day. AVilliam`,
`Goodrich, Crrant` — and all three are the second hand's own damage to a letter, not a
name: AV is how this OCR sets a W.

So the initial-absent pool of Fergus 1843 is **NOT a transcription defect**. Where the
volume is silent about a person of 1835, both hands are silent together, and no amount of
further page-reading will change that. This is the one thing the owner's amendment could
not know when it set the method, and it is worth more than the stretch it ends: the
1,032 are not unread pages. They are people the directories do not print.

### What the pool DOES hide — the surname one letter away

`crosswalk_fergus_1843.py` reaches a person of 1835 through the folded surname and then
compares it EXACTLY, while `name_agreement.agrees` allows a FORENAME one letter of
variation (`Russel` against `Russell`, minimum length five) and states why. Nothing allows
a surname any. So an entry the volume sets one letter off the town's spelling is invisible
to the join, while the resident's own surname bucket — populated by other families — makes
the refusal read `surname present, initial absent`.

**Twelve entries of Fergus 1843 are one letter from a refused resident's surname and carry
that resident's own initial. They reach fifteen residents, sixteen times.**
`tools/surname_one_letter_away.py` is new, enumerates them, and **refuses all sixteen**:

1. **The volume sets both spellings, and sets them apart.** Brooks (2 entries) beside
   Brookes (6), Pearson (2) beside Pearsons (1), Harman (1) beside Harmon (6), Barnard
   beside Bernard, Barry (3) beside Berry, Walker (9) beside Walter, David beside Davis
   (6), Clarke (8) beside Clark (16), Green (4) beside Breen, Wight (2) beside Wright (6),
   Bates (6) beside Yates and Barnes (4). *A directory does not enter one person twice
   under two spellings* — R6's principle, borrowed by stretch 14's clause 3 and borrowed
   again — so a one-letter distance between two surnames the volume itself distinguishes
   is its distinction and not its damage.
2. **And the second hand sets the same letters.** Every one of the twelve was looked up in
   the printed volume line by line — thirteen lines, the extra one the business-directory
   notice `L. W. CLARK` that stretch 7 folds onto Lewis W. Clark's roll entry — and it
   reads Torp's spelling every time: `Pearsons, Hiram, speculator, l)ds Trejnont House`,
   `Harmon. Isaac Xewton`, `Clark, Lewis AY.`, `Bernard, Jacob, teamster`, `Walter, Joel
   Clarke`, `Davis, John, tailor`, `Breen, John. ])ackcr`, `Ihookes, George`. The one
   repair stretch 12 had — the second hand reading what Torp could not — is unavailable
   here, in all thirteen. The lines are carried verbatim in `SECOND_HAND`, OCR damage left
   in, and `--self-test` fails if one stops being findable at its line.
3. **And eight of the sixteen would have been contests anyway** — two residents reach
   `Bernard, Jacob`, two `Berry, Joseph`, two `Walter, Joel Clarke`, two `Brookes, George`.

Nothing is promoted. No fold is widened, no confidence raised; the crosswalk's matches,
ties and refusals are unchanged to the entry across this stretch (136 / 15 / 2 / 326, the
same numbers as the tree it was worked on). The sixteen are filed under
`surname_one_letter_away` with the clause and the printed line on each.

### The one thing worth carrying, and it is not in this domain

`Hiram Pearson` is refused by Fergus 1843 because the volume prints `Pearsons, Hiram,
speculator, bds Tremont House`. The volume is not at fault. **The town is.** It holds
BOTH: `hh_pearsons_hiram`, Andreas's man, `attested`, came in the spring of 1833, city
treasurer 1837-9 — whose own card note quotes the roster printing **`Hiram Pearson`** — and
`hh_pearson_hiram`, a civic-mint card off the 1833 poll list, `unplaced`,
`occupation: none_recorded`, `present_on_scene_date: uncertain`. One man, minted twice by
two of this project's own passes, under the two spellings one source sets.

`surname_one_letter_away.town_pairs` puts that test over the whole resident layer: **22**
cards stand one letter apart in the surname and identical in the forename, and **19 have
never been put to the merge machinery at all** (T-0839, T-0844, T-0993, T-1001, T-1002).
`compatible()` in `consolidate_town_cards.py` buckets the surname as one string, so two
spellings never meet — the hole T-1002 found by hand one bucket along — and T-1001 already
answered NO to the blanket fold, so each is a hand ruling. **Filed as T-1130**, under this
ticket, sized as more than one run. No card is touched here.

### Clause 7 fires, on its first test: THIS TICKET CLOSES

The owner's amendment of 2026-09-14 replaced the closing condition: *close when a stretch
carries fewer than five new facts onto cards, because an unemptied pool is a stated
liberty and not a silence.* **This stretch carried NONE.** It took the stretch its
predecessor named, by the method the amendment prescribed, against the largest pool in the
programme and the volume with the best scan — and the page was already read. So the
programme closes here rather than spending another two hundred runs proving it again.

**The final counts**, re-derived on this tree across all four volumes:

```
                        1839        1843        1844      1844 ad     total
  matched                163         136         113          19        431
  ambiguous               11          15           9           3         38
  contested                4           2           2           6         14
  ties standing           15          17          11           9         52
  initial-absent         263         326         317         126      1,032
  forename-disagreed      66          81          47           0        194
```

**The unspent remainder, stated as a liberty and not left as a silence** — this is what
clause 7 asks for, each pool named with its size and its reason:

* **1,032 initial-absent refusals, not individually overturned, and the reason is
  measured rather than assumed.** For Fergus 1843's 326 the printed volume was read
  entry-head by entry-head against the whole pool and overturned none, so the refusals are
  the volumes' own silence and not this repository's. For the other 706 the same reading
  was not made volume by volume, and that — not the refusals — is the liberty: the class
  is judged on one volume of four. Each of the 1,032 already names its clause on its own
  row and none is a silence.
* **52 ties standing.** Stretch 14 left them as three things a page cannot settle: two
  entries fitting equally, a page saying less than the readings offered it, or a
  generational suffix this town's record does not answer. Every one carries
  `whole_name_declined` with the reason.
* **194 forename-disagreed refusals.** Ordered last by this ticket's own yield rule from
  the day it was filed, on T-0670's judgement that the refusal is usually right. The pool
  GREW across stretches 10-14 (142 → 194) because reading a page better finds more
  disagreements than it settles, which is the arithmetic the amendment was written on.
* **7,229 unspent directory entries.** Not a backlog and never was: entries whose surname
  has no 1835 counterpart, people who arrived after the scene date, unreachable by
  construction. `measure_research_spend.py` counts them and says so.

**What the programme carried, over fifteen stretches:** 431 of the town's people take a
line from a printed directory, 987 directory rulings reach a card with **0 unwritten**,
the write debt of 263 was paid to zero and its ceiling tightened so it cannot regrow, and
eighteen businesses stand on back-projected street faces. The method is closed; the
result stays.

### The gates

`tools/surname_one_letter_away.py --self-test` is NEW and wired into `check.sh`: the
distance test in both directions, the five-letter floor that keeps `Cook`/`Cool` apart,
the refusal's only outcome being a refusal, the contest sentence firing only on a contest,
the town-pair test needing an identical forename, and all thirteen second-hand lines
re-read at the line they were read on. `./tools/check.sh` green.

---

## Added on the way past by T-1035 (2026-09-12): the initial rule the FIRM route now states does not reach the PERSON route, and cannot

T-1035 asked how much initial agreement a one-surname join needs when both sides print
more than one initial, and answered it for `date_norris_1844_businesses.py`'s firm route:
CONTAINMENT. One side's printed initials must all be printed by the other. `{W}` against
`{W, H}` is one man printed two ways and is admitted; `{W, H}` against `{R, E, W}` meets
on W, and agreeing on one of three is not agreeing, so it is refused. That is landed.

T-1035 carried a note asking the same rule be tested against the PERSON pair T-1034's
cohort C1 found — `foster_amos`, an Amos Foster off one line of the 1833 poll list,
carrying `Foster, A. H. (Jennings & F.)` from Fergus 1843 and Norris 1844. **The test was
run, and the rule does not refuse it.** The person route's forename test is
`tools/name_agreement.py`'s `agrees()`, and it weighs only the FIRST word of each reading:
`is_full_forename('A. H.')` is false, so the pair returns `(True, "initial")` before any
initial past the first is looked at. Transplanting containment changes nothing — the
1835 side prints the full forename *Amos*, which yields the single initial `A`, and
`{A} ⊆ {A, H}` is exactly the abbreviation case containment is written to ADMIT.

**So the shapes are different and the fix is not the same fix.** The firm pair is two
initial RUNS that each print one the other lacks. The Foster pair is a full forename on
one side against an initial run on the other, where the middle initial is simply never
weighed — and it cannot be weighed by name arithmetic alone, because an Amos H. Foster is
a perfectly possible man. What actually stands against this join is EVIDENCE, not a name
rule: no Amos Foster is printed in Fergus 1839, Fergus 1843, Norris 1844 or the newspaper
run at all, while A. H. Foster boards the American Temperance House in two volumes and is
a partner in Jennings & Foster.

**Re-measured against stretch 9, 2026-09-13**, because stretch 9 landed on `dev` after the
paragraphs above were written and it added the middle-initial clause they say does not
exist. `further_initials_disagree` / `middle_initial_refusal` now compare every initial
BOTH readings set, position by position — so the sentence "the middle initial is simply
never weighed" is no longer true of the module in general. It is still true of THIS pair,
and for the reason stretch 9 states itself: only initials both readings set are compared,
and `tokens('Amos')` is `['Amos']`, so the pair sets no second initial at all.
`further_initials_disagree('Amos', 'A. H.')` returns `(False, '')` — a silence, not a
disagreement — and `middle_initial_refusal` files nothing. The clause fires the moment the
1835 side prints one: `Amos V` against `A. H.` refuses on `initial 2 disagrees: V against
H`. So stretch 9 narrowed the shape this note describes without closing it, and the fold
stands.

It belongs here because this ticket owns the directories' ties and refusals, and because
`agrees()` is imported by all six crosswalks — a change to it is a stretch of this
ticket's work, not a one-line repair. The stretch that takes it should decide whether an
initial run printed against a full forename, with nothing past the first initial on the
1835 side, may carry a SPEND at all, or only a tie filed for adjudication — which is the
one shape stretch 9's clause is written to leave alone. T-1034 cohort C1 has already
refused FOSTER AMOS for its own purposes (25 register rows, $468) after stripping the
fold, so nothing is bleeding while this waits.
