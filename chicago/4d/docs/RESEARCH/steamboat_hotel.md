# Steamboat Hotel — research dossier

**Record:** `data/structures/steamboat_hotel.json` · **Scene status:** standing and kept as a
hotel *in 1835*; whether it was open on 1 July is the record's central risk · **north bank,
North Water Street near Kinzie**

A hotel that is all business and no building. Two sources give a street, a cross-street, a year
and a keeper, and **not one word about the fabric, the size, the plan, the storeys or the
finish**.

---

## 1. The evidence, in full

Andreas, *History of Chicago* vol. 1, p. 636, "Wharfs, Piers and Early Hotels":

> "**The Steamboat Hotel, on North Water Street, near Kinzie, was kept in 1835 by John Davis, and
> from 1836 to 1839 by William McCorrister, as the American Hotel.**"

DRLOIH, *A Chronology of Early Chicago Area Hotels*:

> "**The Steamboat Hotel, later known as the American Hotel or American Inn, opened in 1835 on
> North Water Street, near Kinzie Street, and was operated by John Davis.** On November 9 that
> year, J. Dorsey and J. Force announced in the *Chicago Democrat* that they had assumed
> management … It was renamed the American Hotel … in 1836 when it was acquired by William
> McCorristen."

And, third, an advertiser's name rather than a statement: Andreas lists the advertising patrons
of the *Chicago American*, whose first issue he dates **8 June 1835**, and among them is
"**John Davis, Steam-boat Hotel**".

Note that these are not three independent witnesses. DRLOIH follows Andreas on the street and the
keeper; what it adds is the dated November notice.

## 2. The date problem

Neither source gives a month. The scene date sits six months into the attested year and every
dated anchor is **after** it:

| date | what it fixes |
|---|---|
| 8 June 1835 | the first issue of the paper Davis advertised the house in — the run in which the advertisement appears begins three weeks before the scene date |
| 9 Nov 1835 | Dorsey and Force take over the management, closing Davis's tenure at the far end |

This project excludes the town's **first fire engine** on exactly this ground — bought
1 December 1835, right year, wrong month. The difference here is that nothing dates the opening
at all, so the question is a balance rather than a contradiction: a house "kept in 1835 by John
Davis" and advertising in a paper that began in June was more likely than not in business by
1 July. The record adopts that reading, tags `documented_range` **inferred**, and says in the
note that a dated advertisement or licence putting the opening after 1 July sends it to
`data/exclusions.json`.

One more thing worth keeping in view: **"opened in 1835" is a statement about a business, not
about a building.** The fabric may be older, in which case the risk disappears.

## 3. Position — "near Kinzie" is not a corner

On the Wright 1834 sheet, read through this project's fitted affine:

- North Water Street runs along the north bank; **east of Wolcott (State) Street it swings
  north-east with the river**, reaching about local N +284 at E +1004.
- The Kinzie Street alignment runs due east at about local **N +276**.
- The two therefore converge about **165 m east of State Street**, near local E +990.

Modern OpenStreetMap agrees in kind: E North Water Street's west end joins E Kinzie Street about
70 m east of State today. "Near Kinzie" is read as that convergence, because a house on North
Water Street *west* of Wolcott would have been described against Kinzie Street's **parallel**
line, which locates nothing.

The building is set on the **north** side of the street just short of the convergence. On the
1834 plat the south side of North Water Street east of Wolcott is a single row of riverbank lots
between the street and the water; a hotel is likelier on the block side than on the wharf side.
**That is an argument, not evidence.** Along-street uncertainty about ±80 m; the side of the
street is a coin flip.

## 4. Why `frame_tavern` and not `log_dwelling`

The archetype choice **is** the conjecture, and it is argued on `form.construction` rather than
buried in the filename.

- **For frame:** every Chicago hotel this dataset can date to 1833 or later is frame — the Green
  Tree of 1833, the Western of 1834, the Tremont of 1833. The log taverns at the forks all belong
  to the 1828–31 generation. By 1835 the town had sawn lumber, carpenters and a building boom,
  and was raising a three-storey **brick** hotel half a mile east on the same bank.
- **Against treating that as evidence:** this project's own line, set in `docs/LIBERTIES.md` L18
  — the ordinary reading of a *type* is not evidence about a *building*. Nobody described this
  house at all.

So `construction` is `conjectural`, and if it is wrong the building is wrong **in kind**.

## 5. What is invented

| attribute | state |
|---|---|
| `footprint` (15 × 8 m) | `conjectural` |
| `form.construction` (braced frame) | `conjectural` — and it chose the archetype |
| `form.stories` (2), `form.wall_height_m` (5.2) | `conjectural` |
| `form.roof_type` (gable), `form.paint` (unpainted), `form.gallery` (false) | `conjectural` |
| `form.roof_pitch_deg` (38°) | `inferred` from framing practice |
| `form.chimneys` (2) | `inferred` from the frontage and the use |
| `ground_contact` | `outside_modelled_ground` — 648 m east of the terrain box |

**What would upgrade almost all of it at once:** the *Chicago American* and the *Chicago
Democrat*. Davis was advertising this house; hotel advertisements of the period routinely count
rooms, name the builder and describe the premises, and a dated one would settle § 2 as well.
