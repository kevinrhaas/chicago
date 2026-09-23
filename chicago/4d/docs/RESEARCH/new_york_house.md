# New York House — research dossier

**Record:** `data/structures/new_york_house.json` · **Scene status:** standing, open and letting
office rooms on 1835-07-01 · **T-0380**, the first piece of T-0306

A two-storey frame hotel on the north side of Lake Street near Wells, raised in 1834 and opened
the following year by Lathrop Johnson and George Stevens. It is the only building in this dataset
whose record began life as one of this project's own **mistakes**: it stood on the EXCLUDE list of
the first structures dossier, was falsified against Andreas on 2026-08-11, and has waited
eighteen days for somebody to build it.

---

## 1. Why it was excluded, and why the exclusion was wrong

`docs/research/04-structures-south.md` § 6 lists it among the Lake/Randolph date guards:

> **New York House** — *"a frame building on the north side of Lake Street, near Wells"*, *"a
> two-story building, with eaves to the street."* Build date **not attested in Andreas**;
> drloihjournal dates it **1836**. **EXCLUDE or flag as high-uncertainty.**

The clause that did the work is "build date not attested in Andreas", and it is simply not true.
Andreas I p. 635:

> "The New York House was built in 1834 and opened to the public the following year by Lathrop
> Johnson and George Stevens, who conducted it until the fall of 1839."

That was found on 2026-08-11 and `data/exclusions.json` was rewritten to say so — kept visible
rather than deleted, on this project's rule that *a wrong exclusion is a claim this project made
and should be seen retracting*. The rewritten entry named what a record would have to carry
(frame, north side of Lake near Wells, two storeys, eaves to the street) and named the residual
question as the **opening month** in 1835 rather than the build date.

## 2. The opening month, answered from the other side

Andreas's "the following year" leaves 1835 open at both ends, and the scene date is 1835-07-01 —
so on Andreas alone, whether the house is open on the scene date is an argument rather than a
reading.

The **Chicago American** closes it. Two advertisements in the issue of **13 June 1835** give this
house as a professional address:

| who | what the paper prints | claim |
|---|---|---|
| Dr. J. B. Barnard, physician | "DR. J. [B.] BARNARD, a[t] t[h]e New Yor[k] Ho[u]se, La[k]e [s]t[r]eet" | `chicago_american_1835_06_13#c009`, p. 3 col. 3 |
| J. C. Bradley, dentist | "His office at the New York House, where he will remain until after the Land [S]ale" | `chicago_american_1835_06_13#c008`, p. 3 col. 2; repeated `1835_06_20#c001`; dateline "Chicago, June 14, 1835" |

A house letting office rooms to two professional men, and advertised as a landmark address a
reader was expected to know, **was open and trading seventeen days before the scene date**. This
is contemporary evidence where Andreas is a recollection published in 1884.

Both readings are **transcription-mediated** under the owner's ruling of 2026-08-28: they come
from this project's OCR-assisted transcriptions and not from the page scans, and the
transcriptions' own uncertainty brackets are preserved above rather than tidied away. Barnard's
heading is among the worst-damaged lines in the American's file — it transcribes as "ar tie New
Yous Horse, Lane atneet" — so the page images would settle it, and a scan read outranks this.

## 3. The dissent: drloihjournal's 1836

The hotel chronology at drloihjournal dates the house 1836, and that date is what put it on the
EXCLUDE list. It is departed from, and the reasoning is recorded rather than the preference:

- Andreas states a **build year plainly**, in a sentence that also names both proprietors and the
  season they gave the house up. An unfootnoted chronology entry contradicts a named standard
  history that is specific in the same breath.
- A **contemporary printing** puts working offices in the house eleven months before
  drloihjournal's date. A secondary chronology cannot outrank the newspaper on this point.
- The same chronology is independently unreliable in this dataset's experience:
  `docs/RESEARCH/western_hotel.md` § 1 records it mis-dating the Wolf Point Tavern, mis-locating
  the Miller House and mis-sizing the Western Hotel in a single entry.

The disagreement is **recorded, not resolved by preference** — it is carried on the record's
`documented_range` note and in `data/exclusions.json`'s watch-list entry.

## 4. Which side of Wells?

This is the weakest part of the record and the reason it sits on the watch list rather than
leaving `exclusions.json` altogether.

Andreas says "near Wells". Wells has two sides, and the north side of Lake Street exists on both:

| candidate | committed block | state |
|---|---|---|
| west of Wells *(adopted)* | `blk_south_water_franklin`, south tier, lot 7 | lot free — the block's dealt Lake-face roofs are on lots 3 and 5 |
| east of Wells | `blk_south_water_wells`, south tier | Lake face already carries three dealt roofs |

**Nothing reached decides between them.** The western block is adopted because its Wells-end lot
is empty, so standing the house there displaces nothing and needs no re-deal — *a reason about
this dataset, not evidence about 1835*, and it is claimed as a liberty in `docs/LIBERTIES.md`
rather than argued away. A source naming the side, or a lot, moves the building one block east at
no cost to anything else on the record.

**The corner is refused in writing.** Pushing the house east to the Lake and Wells corner would
read better in the scene and would give the two American offices a smarter address. Andreas says
*near* Wells, not *at the corner of*, and this project's rule is that a placement inference never
sharpens its source (T-0196). Centring the footprint on the Wells-end lot is the least specific
placement that still satisfies the words; the residual is one lot, about 24 m of frontage, which
is inside the georeference's own working uncertainty.

## 5. What this record unblocks

"The New York House" is an **anchor** in the American's advertising.
`data/research/newspapers/register_1835.json` refused two placeable businesses with the same
sentence — *"The anchor 'the New York House' names nothing the committed town holds."* Rebuilt
against the committed town with this record in it, both resolve: Bradley matches the house's own
occupants block, and Barnard's placement now names `new_york_house` as its landmark. That is why
T-0306 was split and this piece taken first; the remaining pieces are T-0381 (Holbrook) and
T-0382 (the three the town still cannot anchor).

## 6. What is NOT claimed

No dimension is documented and the footprint is invented inside this dataset's stock period
rectangle (40 × 25 ft), which is a claim about the type and not about this building. No source
says how many rooms it had, who else lodged in it, whether either proprietor slept under its roof,
or where in the building either office was. No figure is drawn for any of them: v1 ships no human
figures, uniformly (AGENTS.md § Standing constraint).

**Sources:** `andreas_1884_v1` (I, scan pp. 635, 913, 971) · `chicago_american_1835`
(1835-06-13, 1835-06-20) · `drloih_hotels` (the dissent) · `thompson_plat_1830`, `wright_1834`
(the committed lot grid the placement is taken from).
