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
