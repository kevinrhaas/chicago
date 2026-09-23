# The strength of Fort Dearborn on 1 July 1835 — an establishment, not a return

Research memo for T-1349, the second half of T-1176. Written 2026-09-19.

`docs/RESEARCH/fort_dearborn.md` settles that the post was **held** on the scene date and
says, in its own voice, what it could not settle: *"How many men is not attested. Andreas
gives two companies of U.S. infantry in 1833 and nothing later. No strength figure for
mid-1835 was found, so none is recorded."* The order book says the same from the other end
— `persons/garrison/fort` and `households/garrison/fort` carry **no target**, with the
basis *"NOT APPORTIONED. The garrison of 1 July 1835 is a return to be read."*

This memo is that return. It reads the establishment from the statute that fixed it, takes
the company count from the only source this project holds, writes the men, and states — at
every step — the difference between what the law authorised and what a frontier post
actually had.

**The headline, so it cannot be mistaken: 108 all ranks is a CEILING, not a count.** No
muster roll, post return, descriptive book or monthly return of Fort Dearborn for 1835 has
been read by this project. The Army kept all four. Frontier companies stood below
establishment as a matter of course. Everything below is what the establishment says a held
post of two companies was authorised to hold.

---

## 1. The establishment, read from the act that fixed it

`data/sources/us_statutes_1821_army_peace_establishment.json` — *An Act to reduce and fix
the military peace establishment of the United States*, ch. 13, 2 March 1821, **3 Stat.
615**. Section 2, verbatim:

> That each regiment of infantry shall consist of one colonel, one lieutenant colonel, one
> major, one sergeant major, one quartermaster sergeant, two principal musicians, and ten
> companies; **each of which shall consist of one captain, one first lieutenant, one second
> lieutenant, three sergeants, four corporals, two musicians, and forty-two privates**.

| | per company | two companies |
|---|---|---|
| commissioned | 3 | 6 |
| sergeants | 3 | 6 |
| corporals | 4 | 8 |
| musicians | 2 | 4 |
| privates | 42 | 84 |
| **all ranks** | **54** | **108** |

That was the law of the peace establishment on 1 July 1835. This project has read no act
between 2 March 1821 and the scene date that moves an infantry company's strength; if one
exists it retires this reading, and the source record says so on its own face.

## 2. The company count, and exactly how weak it is

Andreas gives **two companies** of U.S. infantry at the post in 1833 and nothing later, and
has the post held continuously from June 1832 to 29 December 1836. Two companies in **1835**
is therefore a 1833 reading **carried forward two years**, not a reading of the scene year,
and it is graded `reconstructed` for that reason and no other. It is the single figure in
this memo that a one-line post return would overturn.

## 3. What is written, and what is deliberately not

| | written | note |
|---|---|---|
| commissioned officers | **0** | refusal 1, below |
| sergeants, corporals, musicians, privates | **102** | the establishment, filled |
| laundresses | **8** | four a company; § 5 |
| soldiers' children | **14** | drawn from the household model; § 5 |
| sutler | **1** | § 6 |
| **persons** | **125** | in **11** households |

**Refusal 1 — no officer is invented.** The establishment gives each company a captain and
two lieutenants. None of the six is written. T-1348 adjudicated every officer this layer
can place at Chicago in the scene window against the post, admitted **one** — Lieut. James
Allen — and refused eleven with the clause that refused each; minting six more under
invented names would put commissioned officers of the United States Army into this town
that no source has, in the one part of the layer a reader is likeliest to take a name for a
finding. The establishment is printed and the gap is stated. Maj. John Greene (commanding)
and Asst. Surgeon Philip Maxwell are already in the layer and are not touched.

**Refusal 2 — no reviewed community is drawn.** Recruiting Service art. 19 of the Army's own
regulations enlisted *"All free white male persons"* and no others. That is the Army's
colour bar, recorded here as a fact about the institution rather than passed over in
silence, and it is why the rank and file are drawn only from the pools this project holds
for the Yankee and Irish communities. The Native, Métis and free Black reconstruction is
T-1177's under AGENTS.md's Indigenous-history review, and nothing here trespasses on it.
The parent ticket names German recruiting too; **there is no German pool**, and that gap is
stated rather than filled from another.

## 4. Two things the Army's own book settles, and one it does not

`data/sources/us_army_general_regulations_1835.json` — *General Regulations for the Army of
the United States* (Washington, 1835), the standing orders in force in the scene year.

**The enlistment band.** Recruiting Service art. 19:

> All free white male persons, above the age of 18, and under 35 years, being at least 5
> feet 6 inches high … may be enlisted. This regulation, so far as it respects the height
> and age of the recruit, shall not extend to musicians, or to those soldiers who may
> re-enlist into the service.

So a private's age band is drawn **uniform over 18–35** and banded on the order book's own
cut, weighted by the eligible years that fall in each band — the regulation states who may
be enlisted and nothing about the shape of the ages inside that window, so a flat draw is
the only one that adds no claim. A **sergeant** is a re-enlisted man and the same article
exempts him, so he is drawn across the serving ages. A **musician** is exempt at the bottom
and is drawn young. No birth year is written for anybody.

**The quartering check, which is the most interesting thing in this memo.** Quarter Master's
Department art. 31:

> To every six non-commissioned officers, musicians, privates, and servants, including the
> authorized number of washerwomen, two hundred and twenty-five square feet of room, at
> posts above the 38th degree of north latitude.

Chicago is above the 38th parallel. `data/structures/fort_dearborn_barracks.json` draws the
east range at 27.55 × 11.01 m — **303 m², 3,265 sq ft** — off the 1830 Harrison plan, and
its own footprint note argues the size partly from coherence: *"It is the largest building
in the complex, which is what a barracks for two companies of infantry should be, and that
coherence is the only check available on it."*

**The Regulations turn that argument into a number, and on one floor it does not reach.**

| | |
|---|---|
| the allowance | 225 sq ft to every six |
| the barracks, one floor | 3,265 sq ft → quarters **84** |
| to quarter (102 enlisted + 8 washerwomen) | **110** |
| **short by** | **26**, or 31 % |

Three readings survive and **this stage picks none of them**: the barracks had more than one
floor (the usual form for a post of this kind, and the record asserts no storey count at
all); or the drawn footprint is short, which its own note already invites at ±20 %; or the
companies stood **below establishment**, which is the likeliest of the three and is exactly
what an establishment ceiling cannot see. Nothing was reduced to fit — the check is reported
on the ledger and acted on nowhere. It is filed as a finding for the structure record and
for whoever rules on the barracks' storeys.

**What the book does NOT settle: how many laundresses a company was allowed.** It quarters
them inside the men's own allowance (art. 31), pays them at a rate the council of
administration fixes (art. 30), and settles their accounts against the soldier's pay (arts.
27, 29) — and refers throughout to *"the authorized number of washerwomen"* **without ever
printing it**. The only proportion it prints is a straw allowance, art. 82: washerwomen
quartered *"in the proportion of one to every seventeen persons"*, which over this
establishment would give **six**, not eight.

## 5. The laundresses, and the one place this memo carries an instruction rather than a reading

T-1349 states **four a company**, so four a company is what is written. It is not what the
one regulation that prints a proportion would give, and that divergence is stated here and
on the ledger rather than resolved by quietly preferring whichever number reads better. The
figure is graded `reconstructed`, and `docs/LIBERTIES.md` carries it.

Each is written as the wife inside a **married soldier's household** of her own company,
for a reason worth stating: an unattached woman resident at a United States post is the
*stronger* of the two claims, and no source supports either. Her children are drawn from the
1840 schedule's household-size histogram cut to a married soldier's quarters. **That
histogram is civilian.** Nothing this project holds counts the families of a frontier
garrison, so a civilian town's own distribution stands in for one; the cut is this stage's
own and it is a liberty, not a reading.

The married households are seated at the barracks, and that is the weakest line in the whole
stage. The 1830 Harrison plan labels no married quarters and no plan of them at Chicago has
been reached. A hut outside the palisade — where married soldiers at a post of this kind
often were — would be a structure nobody drew, and this project does not draw structures to
house its own inferences. The card says all of that in its own words.

## 6. The sutler

`fort_dearborn_sutlers_store` is an `attested` building with an `attested` function on
Andreas and Wentworth, and its own record states that **who held the sutlership at Chicago
on 1835-07-01 was not established** — Andreas's sutler of about 1830 is five years early and
a different question. One man is drawn to fill the function and nothing else is claimed: no
family, no partners, no stock. A source naming the sutler of 1835 retires the card.

## 7. What this returns to the order book

The garrison bucket the book refused to apportion now has a return: **125 persons in 11
households**, all in `division: fort`, all seated in roofs that were already in the record —
two company cards and eight married households at `fort_dearborn_barracks`, the sutler at
`fort_dearborn_sutlers_store`. No coordinate is invented anywhere in this stage. The fort's
own building cards now name their garrison instead of describing it.

The civilian quota **does not move**. The fort is outside the order book's civil
apportionment by its own rule 4, and the town model states in its own voice that the
garrison is not modelled there.

## 8. A finding this stage had to fix, and the next stage will meet again

The first run of this stage minted a **393rd civic resident** where dev mints 392. The cause
was not the garrison's numbers but its **names**: a hundred men drawn over a pool of
thirty-six surnames put three men of each name into the town, and
`tools/mint_civic_residents.py`, which RESOLVES a printed civic-roll name against the
resident layer, found six invented Tuttles standing beside the town's one real Tuttle and
could no longer resolve `id_tuttle_james_b` to the person it had always resolved to. **An
invention that changes how a source is read has stopped being a reconstruction and become
evidence**, which is the one thing this project cannot let it be.

The fix is refusal 4: **a drawn soldier may not bear a family name any attested or inferred
person of this town bears.** Forty-nine of the pools' sixty-five surnames are free of the
named layer, which is enough. With it in force the civic mint returns to 392, the letter-list
mint is unmoved, and stage `women_and_children` redraws **nothing** — the garrison touches no
civilian card at all.

Two consequences are recorded rather than acted on:

* **Every stage below `women_and_children` will meet this.** T-1173's trade households and
  T-1175's lodgers draw hundreds more invented names over the same pools, and they resolve
  against the same research passes. Refusal 4 is written generally enough to lift, and the
  finding is carried onto T-1179, which owns the convergence of the whole band.
* **`reconstruct_sex_age.py` had to be told about this stage.** Its own rule is *"A DRAW IS
  NEVER EVIDENCE, WHOEVER DREW IT"*, and its `SELF_DESCRIBING_STAGES` list is how it keeps
  another stage's drawn sexes out of the male rate it measures off the town's rolls. A
  company of infantry is male by the statute that constitutes it, so leaving `garrison` off
  that list moved the measured male share of every roll by a hundred men nobody read off a
  roll. It is on the list now, with the reason beside it.

**Links:** T-1349 · T-1348 (the officers) · T-1176 (the parent) · T-1179 (the convergence) ·
T-1198 (the placement sweep) · `docs/RESEARCH/fort_dearborn.md` ·
`docs/RESEARCH/fort_dearborn_garrison_1835.md` ·
`data/reconstruction/1835_garrison.json` (the return itself).
