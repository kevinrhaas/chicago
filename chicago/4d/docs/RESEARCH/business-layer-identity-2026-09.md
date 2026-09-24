# The business layer's people, re-matched to the cards the rulings had already settled

**T-1440, piece 1 of T-1190. 2026-09-20.** Fifty-four rows of
`data/research/newspapers/register_1835.json` change here and not one of them is a new
reading. Every one is a ruling this project had already made, applied at last by the
matcher that had never been told it.

## What was wrong

`compile_register.py` matched a printed name to a town card on the gazetteer's identity
policy — the surname, then the forename initials the two share, because the papers
abbreviate. That rule is right and it is not what failed. Two things around it were:

**It read only the LIVE cards.** A card the merge rulings folded is not in
`data/residents/households/`: its record is kept whole under `merged/` and
`data/residents/index.json`'s `merged` table redirects its id. So the printings the folds
were made ON — *J. H. Kinzie*, *John S. Kinzie*, *J. S. C. Hogan*, *T. Temple* — reached
the matcher with the one card that could answer them removed.

**And among what remained it took the first, not the best.** The loop returned the first
key `sorted` reached, and a tuple sorts before its own extension, so a one-initial card
was always reached before the longer card a printing actually spelled. The least specific
card of a surname swallowed every fuller printing of it. There was also nowhere for a tie
to be refused, so where the town held two equal candidates the register wrote one of them
down as a fact.

## What it cost, and the rulings that were standing there the whole time

`kinzie_james` — James Kinzie, merchant, of the Green Tree Tavern — held **three houses
printed for his half-brother**: *J. H. Kinzie, merchant*, *John H. Kinzie* and *John S.
Kinzie, forwarding and commission merchant*, twelve claims between them, all three seated
on `jh_kinzie_forwarding_store`, a structure whose own occupants line reads "J. H. Kinzie;
forwarding and commission merchant". John Harris Kinzie's card held no workplace at all.

`hogan_john` — a card carrying no recorded trade — held both of **John S. C. Hogan's**
houses, `biz_brewster_hogan_co` and `biz_j_s_c_hogan`, while the postmaster's own card,
`hogan_john_s_c`, stood empty.

And `card_merge_rulings.json` had ruled all of it:

| rule | ruling |
|---|---|
| C2 | `kinzie_j_h` → `kinzie_john_h`: *"the Kinzie surname holds a James as well as a John, so the bare initial J would be two rivals and refused, but 'J. H.' agrees with John Harris and no card and no source reached reads James Kinzie with a middle initial at all."* |
| C3 | `kinzie_john_s` → `kinzie_john_h` (T-0844, folding T-0854: the contradicting S is a digit 8, not a letter) |
| D1 | `kinzie_james` / `kinzie_juliette` distinct: *"John H. Kinzie and James Kinzie are brothers, not a duplicate."* |
| C2 | `hogan_j_s_c` → `hogan_john_s_c` (T-0839) |

T-1432's staffing join is what made it visible. It put each card's own name beside every
name the register printed for it, and three cards disagreed mechanically.

## The rule now

Candidates are found exactly as before — same surname, every compared initial agreeing, an
unread initial agreeing with nothing — and the folded cards join them as aliases of their
survivors. They are then RANKED:

1. an **exact reading** — the card spells the same forenames the printing spells, and no
   more. Nothing outranks a printing and a card that say the same thing;
2. fewest **spelled forenames that disagree** — *James* against *John* is a disagreement
   the initials cannot see and a reader can;
3. most spelled forenames that agree, then most initials that agree — the fuller of the two
   readings, which is what "J. H. agrees with John Harris" means.

One card at the top is the match. Two is a refusal: `person_id: null`, this layer's own way
of saying a printed name has no town card. Refusing loses no evidence — the row keeps its
name, its claims and its dates, and declines only to say whose they are.

`initials` and the new `forename_readings` now come off one parse in
`compile_gazetteer.py`. The parse keeps the abbreviating point, because that point is the
tell that separates *Wm.* from *William*; `initials`' own answer is unchanged, and the
gazetteer re-derives byte for byte.

## Every row that moved

### Re-matched — the printing moves to the card a ruling names (24)

| the register printed | was | is |
|---|---|---|
| [uncertain: W. H. Taylor] | `taylor_william` | `taylor_william_h` |
| [W. H.] Taylor | `taylor_william` | `taylor_william_h` |
| Alanson Sweet | `sweet_a` | `sweet_alanson` |
| Elijah Smith | `smith_elded` | `smith_e_kirby` |
| Hogan, J. S. C. | `hogan_john` | `hogan_john_s_c` |
| Hogan, John S. C. | `hogan_john` | `hogan_john_s_c` |
| J. H. Kinzie | `kinzie_james` | `kinzie_john_h` |
| J. S. C. Hogan | `hogan_john` | `hogan_john_s_c` |
| J. S. Wright | `wright_j` | `wright_john_s` |
| Jno. H. Kinzie | `kinzie_james` | `kinzie_john_h` |
| John H. Kinzie | `kinzie_james` | `kinzie_john_h` |
| John S. C. Hogan | `hogan_john` | `hogan_john_s_c` |
| John S. Kinzie | `kinzie_james` | `kinzie_john_h` |
| John Wright | `wright_j` | `wright_john` |
| Kinzie, John H. | `kinzie_james` | `kinzie_john_h` |
| Lyman Smith | `smith_lawrence` | `smith_l_w` |
| Medore B. Beaubien | `beaubien_mark` | `beaubien_madore` |
| Rider, E. A. | `rider_elia` | `rider_eli_a` |
| Sanford Johns[o]n | `johnson_samuel` | `johnson_sanford` |
| Taylor, Wm. H. | `taylor_william` | `taylor_william_h` |
| Wm. H. Taylor | `taylor_william` | `taylor_william_h` |
| Wm. V. Smith | `smith_william` | `smith_william_v` |
| Wright, John | `wright_j` | `wright_john` |
| Wright, John D. | `wright_j` | `wright_john` |

### Matched at last — a folded card answers to its own printed name (21)

| the register printed | was | is |
|---|---|---|
| [uncertain: Th. Temple] | `new_resident` | `temple_john_t` |
| A. Clybourn | `new_resident` | `clybourne_archibald` |
| Anight, Clark | `new_resident` | `knight_clark` |
| Anson W. Taylor | `new_resident` | `taylor_anson_h` |
| Beaubien, John B. | `new_resident` | `beaubien_jean_baptiste` |
| E. S. Kimberley | `new_resident` | `kimberly_edmund_s` |
| E. S. Kimberly | `new_resident` | `kimberly_edmund_s` |
| E. W. Haddock | `merchant` | `haddock_edward` |
| Edmund S. Kimberly | `new_resident` | `kimberly_edmund_s` |
| G. N. Sproat | `new_resident` | `sproat_grenville` |
| Isaac Scarritt | `new_resident` | `scarrett_isaac` |
| J. Allen | `new_resident` | `allen_lieut_james` |
| J. B. Beaubien | `merchant` | `beaubien_jean_baptiste` |
| J. B[t]. Beaubien | `new_resident` | `beaubien_jean_baptiste` |
| J. T. Temple | `new_resident` | `temple_john_t` |
| J. W. Eldredge | `new_resident` | `eldridge_john_w` |
| John T. Temple | `new_resident` | `temple_john_t` |
| Stephen M. Salsbury | `new_resident` | `salisbury_stephen_m` |
| T. Temple | `new_resident` | `temple_john_t` |
| T[e]mple, John T. | `new_resident` | `temple_john_t` |
| Temple, John T. | `new_resident` | `temple_john_t` |

### Refused — two cards of the surname stand equal (9)

| the register printed | was | is |
|---|---|---|
| Dr. Temple | `temple_john_t` | `new_resident` |
| E. Rider | `rider_elia` | `new_resident` |
| George Walker | `walker_george_e` | `new_resident` |
| Johnson, Solon | `johnson_samuel` | `new_resident` |
| Jones, W. or Abrabam | `jones_willard` | `new_resident` |
| Jones, Wm. | `jones_willard` | `new_resident` |
| King, Bradford | `king_byram` | `new_resident` |
| Wm. Jones | `jones_willard` | `new_resident` |
| Wm. Taylor | `taylor_william` | `new_resident` |

## What the layer did with it

Four authored placeholder houses retire and one is raised, all by
`complete_inwindow_trades.py`'s existing rule and none of them by hand.
`biz_kinzie_john_h_forwarding_and_commission` was a house invented for a man the layer
believed had none; he has three printed ones now, so it goes, and James Kinzie — whose
attested trade is merchant and who now holds no printed house — gains the inferred
placeholder instead. `biz_clybourne_archibald_butcher`, `biz_haddock_edward_tavern_keeper`
and `biz_wright_john_merchant` retire the same way.

The staffing join's `questions_for_the_convergence` falls from three cards to two, and what
is left of those two is not this piece's to answer:

- **`kinzie_john_h`** now holds all three printings and the only disagreement left is
  between the printings themselves — *H.* against *S.* — which C3 has already settled as a
  misread digit. The row stands because the join reports what the printings say, not what
  the rulings say about them.
- **`bradley_joseph`** stands untouched. The town holds exactly one Bradley card, the
  printing *J. C. Bradley* is compatible with it, and deciding that a travelling surgeon
  dentist at the New York House for one week of June 1835 is not the Joseph Bradley who
  clerks for William H. Adams & Co. in the 1843 directory is a reading of evidence, not a
  mechanical rule. It is T-1190's to rule, with a source in hand.

## Nine coin tosses, now refused

Each of these was a printed name the town could answer two ways, and the register picked
one and wrote it down. The cards behind them:

- **Dr. Temple** — `temple_john_t` "Dr John Taylor Temple" and `temple_peter` "Dr Peter
  Temple". Two doctors Temple.
- **E. Rider** — `rider_eli_a` and `rider_elia`, which T-1291's D9 ruling holds DISTINCT.
- **George Walker** — `walker_george_e` and `walker_george_h`.
- **Johnson, Solon** — Samuel, Sanford and Seth Johnson, three S's and none of them Solon.
- **Jones, Wm.** / **Wm. Jones** / **Jones, W. or Abrabam** — `jones_willard` and
  `jones_william`. The register had been giving *Wm.* to Willard.
- **King, Bradford** — `king_byram` and `king_byron`.
- **Wm. Taylor** — `taylor_william` and `taylor_william_h`.

## One generator gained a retraction

`spend_press_bounds.py` writes a dated press appearance onto the card of every person the
register enriches, and it visits those cards and no others — so a card that LEAVES that
set was never visited again and kept the bound it had been given. `strays()` has always
caught it ("carries a press bound and the committed register enriches no press person onto
it") and there was no build step the message could send you to: the tool could write a
bound and not take one back. `hogan_john` and `wright_j`, which had been holding another
man's notices, are the two cards that found it. The retraction clears this pass's own
groups only — the block is shared, and the voter and land registers' rows stay — and it
removes the emptied block rather than leaving `dated_bounds: []` behind, which is a figure
no renderer reads and one `measure_layer_reads.py --gate` rightly refuses.
