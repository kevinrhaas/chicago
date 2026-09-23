# The Traveller's Home — research dossier

**Record:** NONE, and that is the finding. · **Scene status:** already in the dataset, under
another name · **Proposed for `data/exclusions.json` as an identity guard**

A structure `travellers_home` was proposed for this parcel on the strength of a primary
document — an advertisement in the first issue of the *Chicago Democrat*, 26 November 1833.
**It is not a separate building. It is the Wolf Point Tavern, renamed by a new landlord in the
autumn of 1833**, and `data/structures/wolf_point_tavern.json` already carries "Travelers' Home"
in its `aka` list. Building it would have put a second tavern in the scene at a second position
with a second invented footprint, and the two would have been the same house.

---

## 1. The primary document, transcribed from the scan

`data/sources/assets/chicago_democrat_1833_11_26/page1.jpg`, right-hand advertisement column,
immediately below the "Died" notices. Read at native resolution and again at 4x and 5x on
2026-08-11:

> **TRAVELLER'S HOME.**
> KEPT BY
> **CHESTER INGERSOLL,**
> **Chicago--Illinois.**
> The subscriber has taken that noted Tavern Stand in Chicago, lately occupied by Mr. *Wm.
> W. Wattles*, which he will make every possible exertion to render the **Traveller's Home.**—
> The patronage of the public will be gratefully acknowledged. *Oct. 4, 1833.*

**Four corrections to the brief this parcel was given**, all from the page itself:

1. The predecessor is **Wattles**, not "Barlow". The surname is set in italic and reads
   unambiguously at 4x. "Barlow" appears nowhere in the issue.
2. The heading is **TRAVELLER'S HOME** — singular possessive — not "TRAVELLERS' HOME". The
   running text repeats "the Traveller's Home". Andreas spells it both ways in different
   chapters, which is why the alias list should keep both.
3. The tavern stand is "in Chicago", not "at Chicago".
4. The copy is dated **Oct. 4, 1833** — seven weeks before the paper's first issue. The date is
   when Ingersoll took the house, not a prior insertion.

A second item in the same issue, verified on the same scan, puts Ingersoll's house in public use
that autumn:

> NOTICE is hereby given, to the Electors of the Chicago Magistrates District, that an Election
> will be held **at the house of Chester Ingersoll**, in said district, on the 9th day of
> December next, for the choice of one Constable for said District.—Chicago, Nov. 22, 1833.
> **R. E. HEACOCK**, *One of the Judges of Election.*

## 2. What it is — Andreas says so three times, in three different chapters

The parcel brief asked whether this was an existing house under new management. It is, and the
identification is not a judgement call: A. T. Andreas, *History of Chicago* vol. 1, names the
building, the predecessor and the new landlord in one sentence.

**(a) The hotel chapter, printed p. 632**, on the succession at the Wolf Point taverns:

> The old Wolf Hotel, after Wentworth left it, next came into the possession of Mr. and Mrs.
> Charles Taylor, Mr. Kinzie and family boarding with them in part payment for the rent. This
> was in 1832. In 1833, the house again changed hands, **William W. Wattles** becoming its
> proprietor and landlord. In November, he sold out to **Chester Ingersoll**, who ran it an
> uncertain length of time, first as the **"Traveller's Home,"** and afterward as the Western
> Stage House. It went out of sight as a hotel in 1834.

**(b) The town inventory for the fall of 1833**, listing the four hotels then standing:

> There were four hotels; The old Wolf Point Tavern, formerly kept by Caldwell & Wentworth, then
> by **Chester Ingersoll, who had re-christened it "The Travelers' Home;"** the Sauganash …
> still kept by the original proprietor, Mark Beaubien; the Green Tree Tavern, just built by
> James Kinzie, and leased to David Clock, who was the landlord; the Mansion House, where are
> now numbers 84 and 86 Lake Street.

**(c) The chapter on public entertainments**, on a travelling ventriloquist's engagement:

> The next performances of which any record is preserved were given at the **Travelers' Home, a
> hotel kept by Chester Ingersoll, on Wolf Point**, during June, 1834.

Same page 632 also has the wolf sign hung in 1833 "at which time either Charles Taylor, or his
successor, **William Wattles**, was the landlord" — a fourth mention of Wattles at this building
and nowhere else in the volume. Wattles appears exactly twice in Andreas vol. 1: here, and in
the index.

## 3. What rules out every other candidate

| candidate | what rules it out |
|---|---|
| **Green Tree Tavern** | Andreas's Green Tree succession is Clock → Edward Parsons → "two young men, Snow and Spear" → John Gray in 1838. **Ingersoll is not in it at all**, and the fall-1833 inventory names the Green Tree and the Travelers' Home as two of the four hotels in the same sentence. The house was also "just built" in 1833, which does not fit "that **noted** Tavern Stand … **lately occupied by**". |
| **Sauganash** | "still kept by the original proprietor, Mark Beaubien" in the same sentence; Beaubien to 1834, then a Mr. Davis in January 1835. |
| **Mansion House** | named separately in the same sentence, "an unpretentious log tavern kept by Dexter Graves". |
| **Tremont House I** | built 1833 by Alanson Sweet, who kept it with "a man from Canada, named Darwin" until the Couch brothers bought it. Also brand new, so not a noted stand with a predecessor. |
| **Exchange Coffee House** | does not exist until 1834. |
| **Western Hotel**, **Steamboat Hotel** | 1834–35. Neither exists in October 1833. |
| **Miller's house** | out of innkeeping by 1832 and in store use under P. F. W. Peck. |

## 4. The contradiction this creates, and it moves a dossier claim by a year

`docs/research/03-structures-north.md` §2.1 and `data/structures/wolf_point_tavern.json` both
say the Travelers' Home and Western Stage House names are **post-1834** renamings, and both give
**William Walters** as landlord **1833–1836**, covering the scene date. Against that:

- The renaming is **October 1833 at the latest**, over Ingersoll's own name, in the town's own
  newspaper, in its own week — a tier-1 contemporary document against an unfootnoted tier-4
  chronology.
- Andreas has **Wattles** in 1833 and **Ingersoll** from November 1833. "William Walters" and
  "William Wattles" are plainly the same man's name in two spellings, and `drloih_wolf_point`'s
  chronology has him running the house three years after Andreas has him selling out.
- Andreas says the house "went out of sight as a hotel in 1834", which is `drloih_hotels`'
  "ceased operations as a public house in 1834" corroborated from a second direction — and it
  bears directly on `wolf_point_tavern.json`'s `function`, which currently adopts ordinary
  innkeeping on the scene date as `inferred`.

**None of that is edited here**, because `data/structures/wolf_point_tavern.json` belongs to
another parcel. It is written up so the next agent on that record has the primary document, the
page reference and the three Andreas passages in one place.

## 5. What should happen

1. **Do not create `travellers_home`.** It is `wolf_point_tavern` under Ingersoll's sign.
2. Add an identity guard to `data/exclusions.json` (text supplied with this parcel's report) so
   the next reader of the *Chicago Democrat* advertisement does not re-propose it.
3. On `data/structures/wolf_point_tavern.json`, when that record is next opened: correct the
   landlord to **William W. Wattles (1833) → Chester Ingersoll (from November 1833)**, date the
   "Traveller's Home" name to **1833**, and re-weigh the `function` tag against Andreas's "went
   out of sight as a hotel in 1834" — which, if adopted, would make the building standing but
   **not** a public house on 1835-07-01.
4. Correct `data/sources/chicago_democrat_1833_11_26.json`'s `what_it_supplies` entry, which
   currently reads "a tavern stand kept by Chester Ingersoll, lately occupied by Wm. W. Barlow".

## 6. Sources

- `chicago_democrat_1833_11_26` — *Chicago Democrat* vol. I no. 1, 26 November 1833, page 1,
  advertisement columns. Read from the page images, not from the accompanying transcription.
- `andreas_1884_v1` — Andreas, *History of Chicago* vol. 1, printed p. 632 (the Wolf Point
  hotel succession); the town inventory for the fall of 1833; and the public-entertainments
  chapter on the June 1834 engagement at the Travelers' Home.
- `drloih_wolf_point`, `drloih_hotels` — the unfootnoted chronologies whose dates this
  contradicts.
