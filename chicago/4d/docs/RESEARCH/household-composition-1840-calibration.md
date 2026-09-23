# What a Chicago household looked like in 1840

**T-0507.** The calibration the reconstructed-household work never had, and the line it
must not be read across.

Derived file: `data/research/census_1840/composition_1840.json`
Built and gated by: `tools/census_1840_composition.py --build | --check | --self-test`
Sources: `ipums_1840_chicago_households`, `ipums_nhgis_1830_illinois_counties`,
`census_1840_chicago_name_crosswalk`

---

## Why this exists

The retired reconstructed-household programme
(`data/reconstruction/1835_inferred_household_programme.json`) was calibrated on five
in-dataset figures, because — STATUS.md's own words at the time — "no period trade table
for a comparable western town exists in `data/sources/`".

One does now, and it is better than comparable: it is this town. The Sixth Census counted
Chicago in June 1840, and the IPUMS full-count household extract holds all 964 of its
households as the enumerator left them — thirteen male and thirteen female free-white age
bands per family, the free-coloured bands, and the seven industry columns. That is a
household-composition model for a frontier lake port, taken five years after the scene, of
the same place.

## The line, stated first

**A count is not a person.** Nothing in the derived file names anybody, ages anybody or
houses anybody. It carries no head-of-household name and no household serial, and
`--self-test` refuses the build if one ever reaches it. The owner's synthesis rule governs
every figure below: *1840 household members are never minted into 1835 solely from census
counts.*

1840 Chicago was a city and the scene is a town. Against the recorded November 1835 town
census the step is ×1.48 in people; against the smaller town of the previous July it is
larger still. So these are **shapes to test the reconstruction against**, never a
population to fill it from.

## What the count says

**964 households, 4,834 people.** 2,646 male, 2,188 female. 4,781 free white, 53 free
coloured, no slaves.

### Household size

| | |
|---|---|
| mean | **5.015** |
| median | **4** |
| p10 / p25 | 2 / 3 |
| p75 / p90 | 6 / 9 |
| p95 / p99 | 11 / 21 |
| range | 0 to 35 |

The distribution is not symmetric and its tail is long: half the town lives in households of
four or fewer, and one household in a hundred holds twenty-one people or more — boarding
houses, hotels and crews, which is what a port under construction looks like. Two households
return zero people; they are kept in every denominator here, because dropping them would be
a reading of the schedule rather than a count of it.

**The figure worth holding against 1835.** The November 1835 town census gives 3,265 people
in 398 dwellings: **8.20 people per dwelling**. Five years later the mean *household* is
5.02. The two are not in conflict and the gap is the point — in 1835 a dwelling held more
than one household. A roof programme that seats one family per roof and stops there will
undercount the town it is reconstructing.

### Who they were

The age bands are steep at the young-adult end. Men aged 20–29 are 18.6% of all free white
persons, the largest band by a wide margin; women 20–29 are 13.2%. Children under 10 are
1,306 people, **27% of the town**. Nobody in the extract is over 80 but one woman in her
nineties.

The sex ratio is **120.9 males per 100 females**, and among those aged 20 and over it is
**146.8** — three adult men for every two adult women. That is the single most
characteristic number here, and the one a reconstruction of 1835 is most likely to get
wrong by populating households symmetrically.

### What they did

870 people are returned in the seven industry columns — 18% of the town, 0.90 per
household.

| Column | Persons | Share of employed |
|---|---|---|
| Manufactures and trades | 405 | 46.6% |
| Commerce | 185 | 21.3% |
| Agriculture | 136 | 15.6% |
| Learned professions and engineers | 71 | 8.2% |
| Navigation of canals, lakes and rivers | 62 | 7.1% |
| Navigation of the ocean | 9 | 1.0% |
| Mining | 2 | 0.2% |

Read carefully: the 1840 schedule asks how many persons *in each family* are employed in
each pursuit, so these are persons in households and not occupations of named men, and one
household may appear in several columns. Even so, the shape is legible — nearly half the
employed town in manufactures and trades, a fifth in commerce, and a farming fraction that
has not gone away. Agriculture at 15.6% five years *after* the scene is a caution against
reconstructing 1835 as a purely mercantile street.

## What it may calibrate

- **household size** — the mean, the median and the whole histogram, as the distribution the
  1835 occupancy should be tested against, with the dwelling-versus-household gap above
  applied first;
- **the sex ratio**, overall and among adults, as the shape of a frontier port;
- **the child share**, as a check on how many under-tens a reconstructed household may carry;
- **the trade split**, as the relative weight of manufactures, commerce, agriculture and
  river navigation in this town.

## What it may not do

- **name anybody**, or supply a person to any 1835 household;
- **supply the members of a specific household**, however well the sizes match. A household
  of six in 1840 is not the same six as a household of six in 1835 even when it is the same
  family;
- **date a residence.** A household counted in June 1840 says nothing about 1 July 1835;
- **evidence a trade for a named man.** The columns count persons in families;
- **be read as a growth rate for one place.** See below.

## Three counts, five years apart, of three different things

| | Counted | What it is |
|---|---|---|
| 1830 | 1,310 | the published county total for Putnam, where NHGIS prints the return for the district headed "Peoria & Putnam Counties & Territory attached" — a district of northern Illinois, most of it nowhere near the river |
| 1835 | 3,265 people, 398 dwellings | the town census of November 1835, four months after the scene, as Andreas prints it |
| 1840 | 4,834 enumerated / 4,470 published | the city |

Ratios: 1835 over the 1830 district ×2.49; 1840 enumerated over the 1835 town ×1.48;
1840 published over the 1835 town ×1.37. **These are arithmetic between three different
units and not a growth rate.** They are printed because the size of the step is the reason
every figure above is a shape and not a population.

## Three things the count does not settle, recorded rather than resolved

1. **4,834 against 4,470.** Every row carries `citypop` 4,470 — the published 1840 city
   population — while the 964 households enumerated sum to 4,834, eight per cent more. It
   may be the boundary IPUMS assigns households to the city, or the published figure, or
   both. Cite whichever you mean and say which.
2. **The foreigners and illiteracy columns are not carried.** `nforeign`, `nwforeign` and
   `nlit` are present and read `0` in all 964 rows. Zero in 964 of 964 is a column that was
   not coded into the extract, **not a count of none**, and the derived file says so in
   `columns_the_extract_does_not_carry`. The 1840 schedule did ask both questions; answering
   them here needs the page images, not this extract.
3. **Peoria has no row in NHGIS.** Peoria County existed from 1825, and NHGIS ds5 prints 49
   Illinois counties for 1830 without it. Whether NHGIS merged it into Putnam or the return
   itself was credited there is not settled here.

## By page, not by ward

The ticket asks for the same figures by ward where T-0504 attached one. It attached
**pages**: no 1840 material this project has read divides Chicago into wards, and inventing a
ward boundary to report against would be worse than reporting the unit that exists. 19 pages
carry 254 attached households in `by_page`.

That section is **not a sample of the town**. T-0504's age-band fingerprint can only ever
resolve 531 of 964 households — the other 433 share their pattern with at least one other
household — so the attached set is the resolvable set, and page means must not be compared
as if they were neighbourhoods.

## How it re-derives, with no restricted file and no network

The IPUMS extract itself is not in git: the Conditions of Use forbid redistribution, and
`chicago/reference/ipums/README.md` records the owner's decision to publish it to the
Internet Archive under that restriction instead. But a copy of the same 964 rows, with eleven
reading columns added by the T-0504 name work, **is** committed at
`chicago/reference/census1840/validation/H_1840_chicago_with_names_partial.csv`. On
2026-09-04 the restricted original was fetched, compared against it cell by cell — 964 rows,
all 134 IPUMS columns, zero differences — and deleted. The tool reads the committed copy and
records the original's sha256, so a reader holding their own IPUMS extract can prove they
hold the same bytes without this repository ever shipping them.

The band labels are not authored either. They come from T-0504's own `column_map` in
`data/research/census_1840/serial_crosswalk.json`, the committed statement of which IPUMS
variable is which column of the schedule. Correct that mapping and this file moves with it.
