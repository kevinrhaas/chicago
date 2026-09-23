# The Old Settlers of Chicago — the Calumet Club's receptions

The owner's ask, 2026-09-03: *"there was a group called the old settlers club and they
have some names can you research them and their meetings and add residents accordingly
make sure you include citations"* — with a pointer to
<https://chicagology.com/goldenage/goldenage063/>. Ticket **T-0554**.

## What this is

The Calumet Club of Chicago, organised 1878, invited every surviving resident of Chicago
"prior to the 1st day of January, 1840" who had been of age by then to an annual
reception, and the Chicago Tribune printed the rosters, the speeches and the year's
deaths. Those receptions are a **source series**, and this directory reads it.

| file | what it holds |
|---|---|
| `receptions.json` | one row per reception — date, venue, host, where its roster is printed, how many names it carries, and `roster_read` |
| `death_notices.json` | Fergus's 757 death notices of Chicago's old settlers, ages at death kept verbatim beside the birth window each one implies (T-0574) |
| `death_notices_crosswalk_1835.json` | those notices against the 1835 residents layer, and Wentworth's roll of 1882 held against Fergus's list |
| `coverage.json` | what has been read out of a page and where it stops |
| `people.json` | every name on the three rolls read so far, `as_read`, matched against the residents layer, with the ladder rung this source **proposes** |
| `crosswalk.json` | the identity decisions: merges, probables, refusals, each with the rule that fired |
| `claims.json` | what the documents say *about the town*, each with its verbatim quote |
| `text/` | the three 1882 Tribune documents as the page reprints them, and the 1879 register as the plate prints it, so every quote can be rebuilt |
| `resident_spend_1835.json` | the ledger of T-0678's consolidation pass 4: which rulings were written onto the card they name, what each card was told, and — group by group, with the reason — what was not written |

`tools/old_settlers.py --build | --check | --self-test | --apply-citations` owns all of
it. The gate rebuilds the JSON out of the committed text, refuses a quote that differs by
a character, refuses a source id that does not resolve, and refuses a merge that has not
been written onto the resident record it names.

## The two things to read before using this

**1. The club's criterion is not the scene date.** A guest had to be here before 1 January
1840 — not on 1 July 1835. So no name here mints a resident and no name here regrades one.
Under the ratified ladder (T-0513) a later recollection *corroborates, enriches and dates*;
`people.json` carries a **proposed** rung with its reason for T-0513 to consolidate and
T-0514/T-0515 to apply. Only an OS1 or OS2A merge is written onto a record, and what it
writes is a citation and a caveat, never a grade.

**2. The 1882 reading is transcription-mediated; the 1879 reading is not.** This project
has not opened the Tribune of 1882. Every name there is carried exactly as the page prints
it — `Aux. 25`, `William H. stow`, `Chiengo`, `Carter, 1. B.` — and the three Tribune
source records keep `verified: false` until someone reads the newspaper itself. The 1879
register is different: it was read off the **page images** of the printed proceedings
(`reading: "page_image"`), because the Internet Archive's OCR destroys that plate.

## What is read, and what is not

Read: the fourth annual reception of **18 May 1882** — 128 printed guest entries (the
report's own count is 118, and both numbers are carried) and John Wentworth's roll of
**40** old settlers dead since 1 January 1881. Twelve of those 168 names are people the
residents layer already holds; six of the twelve gained a date of death.

Read (T-0577): the **first** reception of **27 May 1879**, whose printed proceedings
(*Early Chicago*, Calumet Club, 1879; Internet Archive `earlychicagorece00calu`) set the
register as a five-column plate on pages 84-90 — **159 entries**, each with the man's own
date of arrival, his birthplace, his age and his 1879 post-office address. It is the one
roster in the series that dates its people: 159 of the 327 names in `people.json` now
carry a year of arrival where before none did, and 70 of them give a year at or before
1835. Twenty-one are men the residents layer already holds.

**159, and the proceedings say 149.** Page 72 states that "one hundred and forty-nine
registered their names", and all three of its aggregate tables — places of birth, years of
arrival, ages — sum to exactly 149. The register printed after them carries ten more. The
document explains itself on the same page: *"Many left without knowing that there was a
registry being kept. A few called afterward and signed the registry."* So the tables count
the evening and the register is the fuller book. Which ten are the later signers is not
stated and is not guessed; `receptions.json` → `reconciliation_1879` sets the printed and
the read count of **every** table cell side by side, and the differences are not all
positive, so the tables are not a clean subset of the register either. One corroboration
that the register outruns them: Robert Fergus registered as born at Glasgow, Scotland, and
the PLACES OF BIRTH table has no Scotland at all.

Also read off the same plate: the **YEARS OF ARRIVAL** table (1818: 1 · 1826: 3 · 1831: 4
· 1832: 5 · 1833: 16 · 1834: 15 · 1835: 22 · 1836: 40 · 1837: 20 · 1838: 11 · 1839: 12 ·
Total 149), which this project had previously recorded as unreadable. Only its OCR is
destroyed; the plate is perfectly legible.

**A contradiction the merges surface.** Four merges — two on each roll — put a man at a
reception whose own resident record carries a Fergus death notice from *before* it.
`receptions.json` → `os_q_registered_after_a_documented_death` names all four, and the
citation written onto each card states it. The clearest is `wolcott_alexander`: the card
carries both Dr Alexander Wolcott the Indian agent, "died Oct. 25, 1830, aged 40" (born
about 1790), and the 1843 directory's "Wolcott, Alex., surveyor … [died Aug. 11, 1884, a.
69]" (born about 1815) — and the register's man gives his age as 64 in 1879, which is the
surveyor's birth year and not the agent's. Splitting a card is an identity ruling, so
nothing is withdrawn here: it goes to T-0513.

Not read: the receptions of **1880** and **1881**, declared from the 1882 report's own
arithmetic, whose Tribune reports have not been located. Nor the 1879 proceedings
themselves — the speeches of Wentworth, Caton, Bross and the rest, which are old settlers'
recollections of exactly this town and are a reading pass of their own (`coverage.json`
says so, and the OCR is sound in the prose, so that pass will not need the page images).

## The second list: Fergus's death notices (T-0574)

`tools/read_fergus_obits.py --build | --check | --self-test` owns
`death_notices.json`, `death_notices_crosswalk_1835.json` and the domain's byte-for-byte
copy of the transcription. This is the same **genre** as the receptions and a different
**list**: Robert Fergus printed an OBITUARY in his 1896 reprint of the *Directory of the
City of Chicago for 1843* — "Names, places, dates, and ages at death of some of Chicago's
Old Settlers" — and 757 entries were read out of K. Torp's 2007 transcription of it.

**Why it was worth a run: an age at death is a birth year.** 725 entries carry a death
date and 608 a printed age, and 598 of them yield a window the birth falls in — 165 of
those narrow enough to name a single year. Nothing else this project has read dates its
people that way. The residents layer is shorter of birth years than of names, and the
crosswalk offers twenty of them.

**The trap, and it is the whole reason to read this section before using the file.** The
list's own header admits it names "some of Chicago's Old Settlers, prior to 1843, **and
other well-known citizens who arrived after 1843**, together with others prominently
connected with Illinois history". So presence here establishes *nothing* about arrival —
not before 1843, and certainly not residence on 1 July 1835. Gov. Richard Yates, Henry
Ward Beecher, Marquette and La Salle are all printed in it. Every record carries
`places_in_1835: false` with the admission quoted verbatim, and the crosswalk repeats it
above the first match, because a reader meeting a matched name is exactly the reader who
will forget it.

**The arithmetic is this project's, not the page's**, so every birth window is `inferred`
and carries its own subtraction written out. An age printed to the day ("aged 82-2-15") is
exact; an age in years and months ("a. 48-6", and the fractions "89½" and "24 2/3", which
are months the volume elsewhere spells out) gives a window of a month; a bare age in years
gives a window of a year, and therefore two candidate birth years. Where the age is
truncated in the transcription ("aged 5-"), hedged ("aged about 50"), or the death carries
no year, **no window is derived** and the record says which of those it was.

Four entries print a date of birth outright — Daniel O'Hara, John Phillips, John Harrison
Whistler and Ellen Marion Kinzie. Those are `documented`, and there the subtraction becomes
a *check*. Three of the four agree. The fourth misses by **one day**: Fergus gives Ellen
Kinzie's birth as 20 December 1804 and her age at death as 55-7-11, which counts back from
1 August 1860 to the 21st. A one-day gap is what two different conventions for counting the
day of death look like, and it is recorded rather than reconciled.

### Read beside the receptions, as the ticket asked

Wentworth's roll of forty old settlers dead since 1 January 1881 and Fergus's list are two
compilations of the same kind of fact, made fourteen years apart by different hands, and
Fergus's runs late enough to cover Wentworth's years. Held against each other on surname
and first initial: **five agree**, **two pairs are the rule's doing and not one man**
(Mark and Medore Beaubien, Harlow and Henry R. Kimball — recorded rather than dropped,
because a reader running the same rule meets the same pair), and **one is a real
disagreement**: both lists spell Simon Doyle, Wentworth kills him in September 1881 and
Fergus in November 1851. Neither is corrected against the other; this project has opened
neither printed page. **Thirty-two of Wentworth's forty are not in Fergus at all**, which
is evidence of nothing — his list is explicitly "some of" the old settlers, so a silence
in it is a silence.

### What the crosswalk says, and what it does not

847 residents tried; 34 meet exactly one entry, 11 are ambiguous, 4 are contested by two
residents apiece and no match is made, and 126 are refused for surname-only agreement. 32
matches could carry a date of death and 20 a birth year — including Thomas J. V. Owen, the
Indian agent, who died 15 October 1835 aged 34½ and was therefore born in 1801, three and
a half months after the scene date. **The file changes no resident record.** Under the
ratified ladder a later compilation corroborates, enriches and dates; T-0513 consolidates
and T-0514/T-0515 apply.

One entry is left as printed and flagged rather than corrected: "Seipp, Conrad, brewer,
died January 28, 1590" is a slip for 1890, and no birth is derived from a year earlier
than the earliest death the volume means to print.

## Known future work, in the ticket queue rather than here

- The 1879 registry and its years of arrival (its own ticket).
- A structured death-date field on a resident. Six records now carry a date of death **in
  prose**, because a `died` block is new schema surface for the residents layer and is a
  decision for a pass that owns that layer, not for a source reading.

## Registered, measured, and spent (T-0678)

This domain was read from T-0574 and T-0577 and adjudicated after, and until 2026-09-05 it
was **registered in no `data/research/domains.json` entry**. So
`tools/measure_research_spend.py` printed it as *"not registered in domains.json (not
measured)"* and measured neither hop: 1,094 units read and 109 rulings naming a person the
town holds a card for, none of it on any instrument. T-0678 registered it and closed the
gap it exposed.

Registering it took two accommodations in `tools/research_domains.py`, both of which are
about SHAPE and neither of which lets anything past:

- **`units_in`.** This domain's reading lives in files at the top of its own directory
  rather than under `records/`, and `people.json` calls its array `people`. The registry
  and the measure count `records` and `claims`, so 327 roll entries counted as zero. The
  file now declares which array is the reading, in one key, and the gate fails if the
  array it names is not there.
- **The roster crosswalk.** `crosswalk.json` rules a printed name against the whole
  residents layer — `as_read` against `resident_name` — rather than a spelling against a
  spelling, and its refusals have no second spelling because what was refused is the layer.
  It is now held to the roster shape's own four rules (both spellings, a rule declared in
  the file's `rules` block, no surname-only merge, evidence behind every merge) instead of
  being reported as 45 malformed pairwise merges.

**What is on a card, and what is not.** The 45 OS1/OS2A roster merges were already written
by `tools/old_settlers.py` as it builds. The 64 death-notice matches were not, and
`tools/spend_old_settlers.py` writes them: an `old_settler_deaths` block on the household,
carrying the record id, the date of death and the birth interval the printed age implies,
with the list's own header admission quoted above the note. **No grade moves**, and the
block is excluded from OS2A's text scan for the same reason the `directories` block is —
left in, a death notice that prints "Flint, Dr. Austin" would hand the roster rule the
spelling it is supposed to find independently, and two merges appeared the moment the
block landed. The contested, ambiguous and refused rows are rivals still standing and are
written nowhere; the ledger states each group and why.
