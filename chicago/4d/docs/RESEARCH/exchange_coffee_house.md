# Exchange Coffee House — research dossier

**Record:** `data/structures/exchange_coffee_house.json` · **Scene status:** standing and open on
1835-07-01, John and Harriet Murphy keeping it · **Lake Street parcel**

Mark Beaubien's second hotel, built 1834 on the north-west corner of Lake and Wells after he left
the Sauganash. **Documented in everything except its fabric**: two independent passages of
Andreas agree on the builder, the corner, the year, the keepers and the name, and neither says
what it was made of, how big it was, or how many storeys it had.

---

## 1. The two passages

**The hotel chapter, printed p. 633:**

> Mr. Beaubien kept the Sauganash until 1834, when he left it, and in January, 1835, a Mr. Davis
> assumed control. **Mr. Beaubien had meanwhile built a new house on the northwest corner of
> Wells and Lake streets. In August of 1834, Mr. and Mrs. Murphy took charge of this new hotel,
> which they christened the Exchange Coffee House. They remained there until 1836**, when they
> removed to the old Sauganash, the name of which they changed to United States Hotel.

**The life of Mark Beaubien**, in the biographical chapter:

> In the latter year [1834] he **completed another house on the northwest corner of Wells and
> Lake streets, which was called the "Exchange Coffee House," and first kept by Mr. and Mrs. John
> Murphy.**

`drloih_hotels` agrees on the corner and the year. The scene date sits eleven months inside the
Murphy tenancy with a documented date on either side of it, which makes this **the best-attested
occupancy in the parcel**.

### The advertisement that looked like a conflict, and the ruling on it (T-1604, 2026-09-26)

Russell E. Heacock's standing advertisement in the *Chicago Democrat* ends with an address, and the
surviving type of the 8 July 1835 printing reads:

> [Office in the 2d st]ory, opposite the Ex[cha]n[ge], [corne]r of Lake and Franklin-sts.

Read as putting **this house** at the corner of Lake and Franklin, that is one block west of the
corner Andreas gives twice, and on 2026-09-25 it was written onto the record as a source conflict
(T-1600). **It is not one.** The corner in the notice is the address of the *office being
advertised*; the Exchange appears as the landmark opposite it. The claim's own placement block says
so — `class: corner`, `anchor: "the Exchange"` — and `data/businesses/biz_russell_e_heacock.json`
already carries Heacock at the `franklin`+`lake` crossing with `structure_id: null`, the register's
`new_building`. So the disagreement was between two readings of one advertisement, not between two
sources about one building, and Andreas's north-west corner of Wells and Lake is unopposed.

Two smaller things the ruling fixes. The page prints **"the Ex[cha]n[ge]"**, not "the Exchange
Coffee House": the longer form was the reader's expansion and had been quoted back as the paper's
words. And the anchor the paper actually prints, *the Exchange*, resolves to no building in this
town, because the register matches an anchor by whole-set equality of identity-bearing words
(T-0406) and {exchange} is not {exchange, coffee, house}. That is filed as its own job.

**What the ruling leaves open, because the notice does not say it.** "Opposite" has to carry about
one block of Lake Street to reach this corner. It does if Heacock's second story stood on the
**south** side of Lake at Franklin — the block face across Lake from there runs Franklin to Wells
and this house holds its east end. On the north side it is the loose usage for the way across the
street. Nothing states which side, so nothing here chooses; the position is unmoved on either
reading and stays `inferred`.

## 2. The stage office — the project has been a year generous, and this record corrects it

`data/exclusions.json` excludes a separate Frink & Walker stage office on the ground that "in
1835-36 stage seats were taken at Markle's Exchange Coffee House at Lake and Wells", and
`docs/research/04-structures-south.md` line 144 says the same, citing Andreas scan p. 945.

The sentence behind it, read in the volume, is Andreas on Dr John T. Temple's stage line:

> An advertisement that appeared in the American on **August 6, 1836**, specifies that "John T.
> Temple & Co., are proprietors of a stage line from Chicago to Peoria;" … and that "**seats can
> be taken at Markle's Exchange Coffee House.**"

**That is thirteen months after the scene date.** Temple's line itself is older — it carried the
mail to Ottawa from 1 January 1834 — so seats were being sold somewhere in 1835 and nothing
reached says where.

**The exclusion still stands on its own feet**: no separate stage-office *building* is attested
before the 1840s, and Andreas's own illustration of "Frink & Walker's Stage Office" sits in his
account of the later town. What does not stand is the claim that this house was the stage office
in 1835, and the record does not make it. Recommended amendment to `data/exclusions.json` is
supplied with the parcel's report: change "In 1835-36 stage seats were taken at Markle's Exchange
Coffee House" to "By August 1836 stage seats were taken at Markle's Exchange Coffee House at Lake
and Wells; where they were taken in 1835 is unattested."

## 3. Markle, and a name that belongs to two houses

Andreas has **Abram A. Markle** taking the **Mansion House** in 1835 and keeping it two years,
and separately quotes the August 1836 advertisement calling the Lake and Wells house "Markle's
Exchange Coffee House". The Murphys, on Andreas's own account, "remained there until 1836".
Either Markle held both houses, or one of the two datings is loose. The record carries the Murphy
tenancy, because it is the one with dated ends either side of 1835-07-01, and records the
conflict.

The `aka` list carries two names that **post-date the scene** and are there only so the record
can be found under them: "Markle's Exchange Coffee House" (the 1836 advertisement's form) and
"Illinois Exchange" (how Andreas lists a house at this corner among the minor houses of 1845).
Whether the 1845 Illinois Exchange is the same fabric is not established.

## 4. What is invented, and why the archetype choice is the biggest of it

Every attribute of the form is `conjectural`: construction, storeys, wall height, roof, paint,
gallery, and the 14 × 9 m footprint. The consequential one is `construction`, because it also
chose the archetype — a frame reading makes this a `frame_tavern` and a log reading would make it
a `log_dwelling`, so if it is wrong the building is wrong in kind and not merely in detail.

The argument for frame: every Chicago hotel this dataset can date to 1833 or later is frame — the
Green Tree of 1833, the Tremont of 1833, the Western of 1834-35 — while the log taverns at the
forks all belong to the 1828-31 generation. The argument against treating that as evidence is
this project's own line, `docs/LIBERTIES.md` L18: the ordinary reading of a **type** is not
evidence about a **building**. And the man who built this one had made his last hotel by adding a
frame block onto a log cabin.

The facade bearing is the second-weakest thing here. No source says which street the house
fronted; a corner house called an *Exchange*, at which stage seats were later booked, could as
easily have turned its front to Wells. Lake is chosen because it was one of the town's two
principal thoroughfares.

## 5. What would resolve what

- The **Chicago Democrat** (from November 1833) and the **Chicago American** (from 8 June 1835).
  This house was a standing address in both — Temple advertised seats here — and a hotel
  advertisement of the ordinary period kind would count its rooms and describe the building.
- The 1834-36 Cook County **tavern licences**, which would fix the keeper year by year and settle
  the Markle overlap.

## 6. "the Exchange" — the name the town wore the house's down to (T-1607, 2026-09-26)

The Democrat prints this house's name two ways, and until this ticket only one of them
reached the record.

| printing | issue | what it prints |
|---|---|---|
| full | 1835-05-27 `#c007` | Heacock: "opposite the Exchange Coffee House, corner of Lake and Franklin-sts" |
| bare | 1835-07-08 `#c012` | Heacock, same standing advertisement reset: "the Exchange" |
| bare | 1834-11-19 `#c004` | Marshall's dancing school: "one door north of the Exchange" |
| bare | 1835-08-05 `#c021`, 1835-08-19 `#c014` | Kennicott, dentist: "OFFICE OPPOSITE THE EXCHENGE, LAKF-STRYE" |

T-1604 reached the same reading of `#c012` from the other side, and ruled that the fuller
name there was a reader's expansion and must not be quoted as the paper's words. It is the
May setting, `#c007`, that prints "Coffee House" — damaged, but the words are on the page.

**Heacock's two settings are the proof.** One advertiser, one office, one advertisement,
reset six weeks apart with the name long in May and short in July. Nothing has to be
inferred about what the shorter one means; the longer one is the same man saying it.

**The register could not follow.** `match_landmarks` resolves an anchor by WHOLE-SET
equality of identity-bearing words against a record's name and its akas (T-0406, ruled on
the Tremont, where loosening to containment would have put "the store" on the first store
in town). `{exchange}` equalled neither `{exchange, coffee, house}` nor `{markle, exchange,
coffee, house}` nor `{illinois, exchange}`, so the anchor named nothing and the business
hanging off it fell to `street_only`.

**The ruling is that the record answers to the short name, and the match is not touched.**
`"the Exchange"` joins `aka`. That is T-0406's own mechanism — an aka is how a record
answers to the name the papers print — used the way the Tremont uses it. Whole-set
equality is unchanged; what grew is this record's list of names, which is a claim about
this building and is sourced above.

**Measured, on the whole register:**

| | before | after |
|---|---:|---:|
| businesses anchored on `exchange_coffee_house` | 1 | 2 |
| `new_building` | 26 | 27 |
| `street_only` | 61 | 60 |

Exactly one business row differs — `business_wm_h_kennicott_surgeon_dentist`, from
`unresolved`/`street_only` to `structure`/`new_building` — and all 2,667 person rows and
every other business row re-derive byte-identical.

**What the short form does NOT reach.** The town holds a second house carrying the word:
the Sauganash began as the **Eagle Exchange Tavern** and still answers to it. That is
`{eagle, exchange, tavern}`, a superset, which whole-set matching refuses now as it did
before — and it is the reason this was ruled rather than assumed. "the Exchange Tavern"
would be a third form and names nothing. The other coffee houses in Andreas's index —
Lincoln's, the Eagle, the Lake Street — are not in the structure layer, and none of them
is called the Exchange. Three self-test cases in `tools/compile_register.py` (§ 4c) hold
each of those shut.

**The 1834 trustees' venue mentions are untouched.** The Board of Trustees met at "the
Exchange" later in 1834, in the list recorded on `data/structures/mansion_house.json` that
brackets the Graves-to-Haddock handover of the Mansion House. Those are prose inside a
note, not anchors in the gazetteer: the register never resolved them and does not resolve
them now, and nothing about them moves. They are worth keeping in view for one reason
only — they corroborate that the short name was current in the town a year before Heacock
used it. They remain what that record already calls the whole venue list: convenience, and
never by itself a tenancy.

**This does not touch the corner.** Where the house stood — Andreas's Lake and Wells
against Heacock's Lake and Franklin — is T-1604's question and is unaffected: Kennicott is
anchored to the building, not to a coordinate, and the building has not moved.
