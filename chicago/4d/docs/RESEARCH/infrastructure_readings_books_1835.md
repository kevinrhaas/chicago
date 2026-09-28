# The thirteen infrastructure readings in the books, the directories and the civic corpora

**T-1592, 2026-09-28.** Piece 2 of T-1586 — *spend the 92 unasserted `infrastructure`
readings* — beside T-1591, which takes the 79 in the Chicago Democrat and the Chicago
American. These thirteen are the ones printed in books, in a directory and in a civic
finding: ten in the books domain, two in Norris's 1844 directory, one in the Andreas town
findings. Every one of them is now closed against a stated rule in
`data/research/spend_rulings.json`, and `python3 tools/measure_research_spend.py --check`
is green with 582 unresolved units where it had 595.

## What was asked, and the state each unit ends in

The parent's acceptance says each unit ends **asserted**, **limited** (with the clause) or
**refused** (naming rule and evidence), one state per unit and stated. In this ledger's
own vocabulary *limited* is `aggregate_only`: taken, and taken on something larger than
any thing that can be placed at a coordinate.

| unit | corpus | disposition | rule |
|---|---|---|---|
| `bk_fer_052` | Fergus No. 28 | **asserted** | written onto `biz_chicago_post_office` § `service` |
| `bk_hub_061` | Hubbard 1911 | **asserted** | written onto `fort_dearborn_well` § `existence` |
| `bk_afc_002` | Hurlbut 1881 | aggregate_only | `the_infrastructure_reading_is_the_town_and_not_a_work` |
| `bk_fer2_003` | Fergus No. 29 | aggregate_only | same |
| `n1844_tf_040` | Norris 1844 | aggregate_only | same |
| `bk_hub_070` | Hubbard 1911 | aggregate_only | `…corroborates_a_work_the_town_already_holds` |
| `n1844_tf_027` | Norris 1844 | aggregate_only | same |
| `c008` | Andreas town findings | aggregate_only | `the_boundary_reading_is_recorded_in_the_limits_file…` |
| `bk_fer_028` | Fergus No. 27 | refused | `the_earlier_infrastructure_reading_is_a_fact_about_the_year_it_names` |
| `bk_hub_072` | Hubbard 1911 | refused | same |
| `bk_fer2_006` | Fergus No. 29 | later_only | `the_canal_reading_is_dated_after_the_scene_and_only_corroborates` |
| `bk_fer2_007` | Fergus No. 29 | later_only | same |
| `bk_hub_027` | Hubbard 1911 | later_only | same |

Two asserted, three refused or later-only on the canal, two refused on their own dates,
six taken in the aggregate. **No vertex moved, no corridor was cut, no confidence was
raised and no coordinate was invented by any of the thirteen.**

## 1. The one reading that lands on the scene year

`bk_fer_052` is the eastern mail's carriage set out year by year: weekly on horseback in
1832 under postmaster Bailey, weekly by one-horse wagon the next year under Hogan, a
two-horse wagon in 1833, a semi-weekly four-horse stage line from 1834, **tri-weekly in
1835**, daily from 1837. 1835 is in that list by name, and nothing else in this corpus
dates the mail's frequency at all.

`data/businesses/authored/biz_chicago_post_office.json` held the office established 31
March 1831, its removal to near the corner of Franklin and South Water about July 1834,
and John S. C. Hogan attested as postmaster from 2 November 1832 — and it had **nowhere to
say how often the mail came**. `locations` says where a firm stood, `dates` when it opened
and `staff` who kept it; for a public service none of the three is the thing a visitor
would ask it. So the businesses schema gained an optional `service` block (frequency,
carriage, window, tier, basis, source, claims) and the Post Office is the first record to
carry one. `renderers/web/js/businesses.js` prints it on the card under **How it served
the town**.

**Graded `inferred`, not `attested`, and the grade is admitting three things.**
`data/sources/fergus_historical_series_26_29.json` sits at tier 2, which would permit
`attested` — but Fergus's Number 28 is the *Directory of the City of Chicago for 1843*
**compiled in 1896** by a man who reached Chicago in 1839, so it is a late recollection of
a directory's own history section rather than a contemporaneous printing; the reading gives
a year and no month, so carrying a tri-weekly stage from an unnamed month of 1835 to 1
July is an inference about continuity within the year; and there is no second witness to
agree or disagree with. The basis on the block says all three.

**What the assertion does not do.** It claims no premises, no seat and no coordinate: the
office stays on South Water Street at the tier `locations` gives it, and T-0859's live
conflict — eight printings put Hogan's store "one door" from the Post Office, and one door
is not four blocks from Franklin — is untouched. Jonathan Nash Bailey, named by the same
reading as the 1832 postmaster, is **not** carried onto the record: this corpus's
crosswalk refuses him against the letter-list Bennet Bailey, so the staff row stays Hogan
alone.

**It needed no ruling, and that is the better outcome.** The ledger's own derivation closes
a unit `asserted` when a source-bearing structured field on a target record names the
unit's record id and cites a source the unit lists. The `service` block does all three, so
`bk_fer_052` closes off the record itself with nothing in `spend_rulings.json` vouching for
it — exactly as nine of T-1600's ten did. A first draft of this pass ruled it anyway and
the gate refused the ruling as one that "was already closed without it", which is the check
working.

## 2. The sentence the fort's well already stood on

`bk_hub_061` is Hubbard's "The well was in the outer inclosure and near the south gate."
`data/wells/fort_dearborn_well.json` has cited `hubbard_autobiography_1911` for both the
well's existence and its position since T-0881 — as one of the two independent witnesses
that agree on the place — **without ever naming the claim**, so the citation could not be
checked in a grep. It names it now, in the existence note, beside the sentence it quotes.

Nothing is promoted. The 1830 Harrison plate stays preferred over the 1911 memory where
they disagree: the ring is 52.6 m south of the stockade's ink, nearer than "near the south
gate" would put it, and the record already recorded that disagreement rather than smoothing
it. No grade moves and no vertex moves.

**The reading's second half is not asserted.** "About two hundred feet from the north gate
was the river, a stream of clear, pure water, fed from the lake" is Hubbard's fort of 1818.
The bar was cut through in 1834 and the committed banks are read off Wright 1834, so
neither the distance nor the water's clarity is carried to 1 July 1835; the existence note
now says so in as many words.

## 3. The harbour's origin, which the town already holds and was not written from

`bk_hub_070` credits Captain Fowle with "the first attempt to make a harbor of the Chicago
River", dated by Hubbard's own roll of commands to Fowle's tenure of 3 October 1828 to 21
December 1830. `n1844_tf_027` is the appropriation that followed: Congress called to the
necessity of a harbour, General Scott's letter laid before it, read at 1832 — the
appropriation, in the reading's own words, "that produced the piers whose construction leaf
23 dates to late 1833 — the works standing, half-built, in the scene."

**The works are already the town's**, as `north_pier` and `south_pier`, whose line is read
off Wright 1834's two red lines with HARBOR lettered between them and whose dating rests on
`andreas_1884_v1`. Grep those two records for `hubbard_autobiography_1911` or
`norris_directory_1844` and neither is there. So this is corroboration of the works' origin
and not the page they were written from, and the rule says *corroborates* rather than
*spent*. Nothing moves — no bearing, no length, no confidence — and the south pier's
disputed starting figure stays disputed, because an agreement manufactured between a survey
and a recollection is not evidence. Offering the corroboration to those two records is the
structures layer's own PR and its own judgement.

## 4. The corporation's boundary, held in text and resolving to no line

`c008` is Andreas on the corporate limits in two steps: the November 1833 extension to the
lake east, State west, Ohio north and Jackson south, and the act of 11 February 1834 taking
in all land east of State to the lake shore between Chicago Avenue and Twelfth Street,
excepting the military reservation from the river south to Madison.

`data/reconstruction/1835_corporation_limits.json` § `the_february_1835_extension` already
carries this reading **word for word**, beside Wood 1881 reading the same act from the other
side, and it is the file that caught Andreas's year: the act is of 11 February **1835**. It
holds the reading at `documented_in_text_only` for three reasons written out there — Andreas
is tier 3 and misprints the year, Chicago Avenue and Twelfth Street are not committed
centrelines in this scene, and the session law has not been found in this corpus in any
printing. So this pass records it `aggregate_only` and **not** `asserted`: grading that
block `documented` would mean inventing the two centrelines the extension walks on, and a
boundary this project gates an ordinance on cannot rest on that.

There is a second disagreement worth stating. The first half of Andreas's summary puts
State Street on the west, and the corporation's **own** printing — the ordinance of 7
November 1833, held here at tier 1 and the line the ring is actually walked on — begins at
Jackson and **Jefferson**, well west of State. Andreas understates the town he is
describing. Recorded, not smoothed, and not resolved by this pass.

Nothing that is drawn changes either way: the extension adds ground east of State and
expressly withholds the Fort Dearborn reservation, where the twenty-four drawn structures
outside the 1833 ring stand, so every drawn roof's inside/outside answer is identical under
both readings and the stove-pipe by-law's gate keeps scoping on the narrower 1833 ring.
**What would move it:** the act of 11 February 1835 in a contemporaneous printing, or
Chicago Avenue and Twelfth Street committed as centrelines — and T-0464's extension of the
modelled ground south of Jackson is what would make the difference visible.

## 5. The canal: three readings, and it is not drawn

`bk_fer2_006` is Duncan's written message to the special session of December 1835 reporting
that every attempt at a loan under the previous session's act had failed. `bk_fer2_007` is
that session passing the loan law, at "December 1835 onward". `bk_hub_027` has Hubbard at
every session urging a canal bill "until it was effected in the session of 1835-36" — filed
`infrastructure`, and its content is a man's whereabouts in a winter the scene does not
reach. All three are dated **after** 1 July 1835, so under the ladder ratified 2026-09-03
they corroborate and never promote: `later_only`.

They corroborate something real, which is the absence. The canal was unfunded in December
1835 and the special session's first act that month was to admit it, so a July town with a
canal in it would be wrong twice over. `bk_fer2_003` — Duncan lobbying the War Department
in March 1829 to send engineers to *locate* the line — is the same story from the other
end of the decade and is taken in the aggregate: the canal is why 1835 Chicago was the size
it was, and not one metre of it is dug on this ground.

## 6. Two refusals on their own dates

`bk_fer_028` is the open bower with seats for the chiefs and headmen put up on the green
along the north bank for the treaty of **1821**, near the old John Kinzie house and directly
under the guns of the fort. It is placed by two landmarks this project holds, and it is
still refused: what it places is a temporary council shelter of fourteen years before the
scene, and the reading's own note already says that nothing in it argues the bower stood in
1835 and that no structure record is minted from it. Its other half — that the bank was
open enough in 1821 to seat several thousand people — is a fact about 1821; the bank's 1835
state is read off Wright 1834 and the committed structure layer. The standing constraint
applies twice over: the 1821 council is Indigenous history, this project stages no
gathering and draws no human figure, and a bower is not a thing this scene would raise even
if the date allowed it.

`bk_hub_072` — "Fort Wayne, Indiana, was the nearest post-office, and the mail was carried
generally by soldiers on foot and was received once a month" — is Hubbard's Chicago of
1818-23, and the scene **refutes** it rather than receiving it: the town has had its own
office since 31 March 1831. Read against `bk_fer_052`, which the same pass asserted, the
two readings are the measure of seventeen years: a soldier walking from Indiana once a
month, and a four-horse stage three times a week.

## What this leaves open

- **T-1591** still owns the 79 `infrastructure` readings in the Chicago Democrat and the
  Chicago American; T-1586 is not done until it lands.
- **The harbour corroboration is offered and not taken.** `north_pier` and `south_pier`
  could cite Hubbard and Norris for their origin; that is a structures-layer judgement and
  is not made here.
- **The corporation's February 1835 extension still has no geometry**, and will not until
  the act turns up in a printing or the two centrelines are committed.
