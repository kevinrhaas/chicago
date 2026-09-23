# The one-letter card pairs, ruled — the closing report

**T-1291, 2026-09-17.** Identity is closed for the purposes of the 1835 reconstruction,
with a stated ambiguous residue. This is the report the ticket's third acceptance clause
asked for: how many pairs merged, how many were kept apart, how many were left ambiguous,
and what the ambiguous ones do to the town's count.

## What the ticket folded, and why it is one job

T-1291 folded five open tickets into one on the owner's instruction of 2026-09-17 — *the
research spend is a CHECK before reconstruction, not a programme*: **T-1027** (the
one-letter card pairs, filed as an EPIC), **T-1140**, **T-1153**, **T-0835** and
**T-0958**. Every one asked the same question — *are these two readings the same person?*
— and every landed answer to it rests on the same four facts. Splitting that into an epic
plus four satellites turns one pass over the pool into five runs that each re-establish the
same context.

## The count

`tools/measure_card_fuzzy_candidates.py` proposes **54** pairs that one letter of slack
would add to the exact candidate test. **11** already carried a ruling naming both their
cards. The remaining **43** are ruled here.

| outcome | pairs |
|---|---|
| **merged** | **0** |
| kept apart (`distinct`) | 42 |
| ambiguous (`undecided`, U2) | 1 |

By rule: D7 13 · D9 7 · R2 6 · D6 5 · R5 4 · D8 3 · D10 3 · R3 1 · U2 1.

**THE TOWN'S COUNT DOES NOT MOVE.** 1,282 cards on 1,258 households before this pass and
after it; the 65 merge redirects in `index.json` are untouched. A fold is a card DELETION
and nothing here folds.

## What the ambiguous one does to the count

One pair — `mcgregor_ashor` / `mgregor_a` — is recorded **ambiguous under U2**, and its
effect on the town's count is a range of **one**: 1,282 cards if the pair is two men,
1,281 if it is one. The reason is not a missing page. The Democrat of 2 July 1834 sets
"A. M'Gregor" and this project's own normaliser rendered that `mgregor` rather than
`mcgregor`, which is the only reason a one-letter test sees a difference; M'Gregor and
McGregor are the same surname, so what actually stands between the cards is an initial
against its one full forename, which is C2's shape and a MERGE rule. The obstacle is how
the layer renders Scots and Irish particles — the class C7 settled for Dutch and French
ones — and that is not a decision to take from inside one pair of cards. Both readings are
kept and no ticket is filed, per the ticket's fourth acceptance clause.

## The two pairs a page would most cheaply settle

Neither is filed as a new ticket. Both arguments are kept verbatim in their rulings so the
next pass reads them instead of re-deriving them.

**`lloyd_alexander` / `loyd_alexander` — the town is carrying its own fourth mayor twice.**
Fergus 1843: *"Loyd, Alexander, carpenter and builder, (L., Blakesley & Co.), res 52 Wells
[4th mayor…]"*. Norris 1844: *"Lloyd, Alexander, builder, of L. Blakesly & Co. res Wells b
Lake and Randolph sts"*. Same given name, same trade, same firm, same street — non-name
discriminators, and they agree. Moses & Kirkland's History sets both spellings inside one
work for one man, and the Democrat prints "A. Lloyd" on 29 October 1834 and "A. Loyd" three
weeks later. It is refused under D7 anyway, because **C9** wants one publication caught
setting both spellings for one man *inside the window* and the catch here is an 1895 history
describing 1840, while **C11** — the rule this evidence actually fits — requires the surname
to agree letter for letter and varies the forename. That asymmetry is the one C14 was
written to fix for C12. Fixing it for C11 is a new MERGE rule, and T-1027 is explicit that
the pool may not be closed by widening the join. What would settle it: one in-window
printing setting both spellings for the builder, or C11 drawn onto the surname on the firm
and the Wells Street address the two directories already agree on.

**`smow_george_w` / `snow_george_w`.** "Smow" is set twice in the whole deposited corpus and
both settings are the single poll-list line; George W. Snow is the documented surveyor and
lumber merchant. No roll sets both spellings, so D9 refuses — and T-0695 already owns the
image that would repair the garble.

## The method, and the two things it changed

`tools/rule_fuzzy_card_pairs.py` gathers, for every pair at once, the four facts every
landed one-letter ruling rests on: whether either card is an **anchor**; whether either
**stem is populated** at this town; a word-boundary **corpus census** of each spelling over
every deposited transcription; and whether any single **printing** is caught setting both
spellings of the man's name. It rules nothing. Two things came out of running it over the
whole pool rather than one cluster at a time.

**1. "Ruled" did not mean the pair was ruled.** T-1027 counted a pair as ruled when *either*
card stood in some ruled cluster, and said so in its own table. A ruling weighing `wright_j`
against two Wrights says nothing about `wight_j_f`. Measured at pair level the pool was 43
open, not 32. `--check` now asks for a ruling naming BOTH cards and is gated in `check.sh`,
so the pool cannot silt up to 68 rows again unseen.

**2. A shared source id is not a shared printing — the new rule D9.** Two of this project's
source ids are corpora, not printings: `chicago_voter_lists_1833_1835_irad` bundles four
separate closed rolls (the poll of 10 August 1833, the 1833 tax list, the poll filed 11
August 1834, the 1835 poll) into one transcription, and `chicago_newspapers_1833_1835` is
three years of two papers. A pair whose two spellings sit under one such id — Foot/Foote,
Harman/Harmon, Dell/Dill, Rider "Elia."/"Eli A." — falls through the gap between C9's
missing demonstration and D7's *"the two bodies of evidence do not touch"*, which is
literally false for them. D9 is D7's reason measured at the **roll** or the **issue**
instead of at the source id. It refused seven pairs that would otherwise have read as
unrulable, and one of them is instructive: the poll filed 11 August 1834 enters "Harman,
Isaac" and then "Harmon, C. L." and "Harmon, M. D." within three lines — a printing caught
*keeping* the spellings apart, which is the opposite of what C9 asks for.

Two further refusals were drawn narrowly to cover shapes no landed rule reached: **D8**,
D7's mirror on the forename, and **D10**, for pairs whose forenames disagree beyond the one
letter (a middle name against a middle initial, Walter against William, "Mrs. H." against
"H. C."). **U2** records that ambiguity is a finished answer. All four are refusals or a
held question; this pass added no merge rule.

## What is NOT closed, and is not pretended to be

The four garbled cards — `chark_john_a`, `gabbs_james_i1`, `stoel_c_ii`, and `smow_george_w`
alongside its D9 — are refused under R5 and their images belong to **T-0695**, which is
where they already belonged. R5 refuses a reading, not a person: "a fold here would repair a
wreck by guessing at it" is T-1027's own sentence and it is still the answer.
