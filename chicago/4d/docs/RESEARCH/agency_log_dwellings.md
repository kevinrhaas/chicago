# The ring of log buildings round the Agency House

T-1714, 2026-09-28. Piece 1 of 4 of T-1204. Records:
`data/structures/mckee_log_house.json`, `data/structures/caldwell_agency_log_house.json`,
`data/structures/agency_striker_log_house.json`.

Sequel to [indian_agency_1835.md](indian_agency_1835.md) (T-1374), which wrote the agency's six
offices down and said in as many words what it could not write: *"six offices with no house to be
offices of."* This raises three of the houses.

**AGENTS.md's standing constraint governs this page and all three records.** The final removal of
the Potawatomi from Chicago is August 1835, six weeks after the scene date. The agency was kept at
Chicago against a treaty obligation to the Potawatomi; one of these three buildings is the house
Andreas gives a Potawatomi chief. All three carry `review_required`. Nothing here is depicted or
narrated, and no figure is drawn for anybody.

---

## 1. The evidence is better on who slept here than on anything a visitor can see

Two sentences carry the whole group.

> Around the Agency House were grouped a collection of log buildings, the residences of the
> different persons in the employ of Government … blacksmith, striker, and laborers.
> — *Wau-Bun*, of 1831

> In its vicinity were small log buildings occupied by the blacksmith, Mr. McKee, and Billy
> Caldwell, an Indian chief, who was also interpreter for the agency.
> — Andreas, of the settlement about 1830

Between them the group is attested four ways over: **that it existed**, **that it stood round the
Agency House at the foot of State Street**, **that it was of logs**, and **who lived in it**. A
third statement corroborates the fabric from inside the group — McKee's own recollection of
reaching the north bank in June 1823, finding *"but two houses on the north side of the river"*,
building the fourth himself, and *"All these houses were of logs."*

**Not once is a single building given a shape, a size, or a place of its own.** That asymmetry is
the whole difficulty of this parcel and it is why the footprints are placeholders and the positions
are offsets. `docs/LIBERTIES.md` **L283** is the admission.

## 2. Why these three, and why the fourth was refused

| raised | on what | seated |
| --- | --- | --- |
| `mckee_log_house` | Andreas names the building AND its occupant | **yes**, `hh_mckee_david`, `inferred` |
| `agency_striker_log_house` | Wau-Bun names the OFFICE among the residences; Andreas and the 1830-31 staffing name Porthier as the striker | **yes**, `hh_porthier_joseph`, `inferred` |
| `caldwell_agency_log_house` | Andreas names the building AND its occupant | **no** — see §4 |
| a house for the *laborers* | nothing | **refused** — see below |

**The laborers get no building.** Wau-Bun's *"laborers"* is a plural noun, not a count.
[indian_agency_1835.md](indian_agency_1835.md) §3 has already ruled on exactly this — *"a remainder
cannot be drawn out of a count that does not exist"* — and nothing about raising three roofs
changes the arithmetic. Employees the corpus counts without naming: zero. So three, not four.

## 3. Two households had no home, and the reason was this

Both seats closed a gap the household cards had already written down about themselves.

`hh_mckee_david.lives_at` read: *"Andreas puts him in one of the 'small log buildings' near the
agency house at the foot of State Street, alongside Billy Caldwell. **Those buildings are not in
`data/structures/`** … so there is nothing to link to and nothing to date."* They are now. Nothing
about the evidence moved: Andreas gives this man a log building in that vicinity and gives him no
other house anywhere, so the seat is the only candidate the corpus holds, and it is graded at the
inference rather than at his sentence.

`hh_porthier_joseph.lives_at` read: *"Not attested in anything this project holds."* That was true
of his **name** and not of his **office**. Wau-Bun's ring is *the residences of the different
persons in the employ of Government … blacksmith, striker, and laborers*, and Porthier is the
striker — *"and Joseph Porthier as striker"*, with the 1830-31 agency staffing listing the pair.
The office is attested among the residences and the man is attested in the office; the seat is the
join of the two, at `inferred`. His `works_at` already put him at `blacksmith_shop_state_st` at
`attested`, twenty metres east of this house.

## 4. Billy Caldwell's house is raised and NOT seated, and that is the finding

`hh_caldwell_billy.lives_at` holds **two candidate residences and refuses to choose**:

1. the frame house *"built for him by the Department for Indian Affairs on the North Side near
   where is now the corner of State Street and Chicago Avenue"*, which Andreas elsewhere calls
   probably the first frame building in Chicago after Robert Kinzie's store, erected in 1828 —
   **frame, not log**, and well north of the modelled blocks;
2. the small log building in Cobweb Castle's vicinity, from the sentence quoted in §1.

Raising (2) makes one of the two candidates a thing a visitor can see. **It does not settle which
house the man was in on 1835-07-01**, and a seat written now would be this project choosing on the
strength of which house somebody got round to modelling. So `caldwell_agency_log_house` carries no
occupant, its `resident_assignment` is `unassigned` **as a refusal rather than as an absence of
work**, and the household card is amended to say the choice is *narrowed, not settled*.

What would settle it: a source that dates either house to 1835, or one that places this man in
either on the scene date.

## 5. The positions, and what is invented in them

All three stand on the riverbank strip between the 1834 drawn bank (local N ≈ +98) and the
north-bank block row (N ≈ +128), which is the strip `cobweb_castle` and `blacksmith_shop_state_st`
already stand on and the strip both of their notes argue for. The row, west to east:

| record | local E | local N | gap to the next east | ground |
| --- | ---: | ---: | ---: | ---: |
| `agency_striker_log_house` | +727 | +117 | 21 m | +1.28 m |
| `mckee_log_house` | +748 | +122 | 21 m | +1.30 m |
| `blacksmith_shop_state_st` *(stands)* | +769 | +119 | 23 m | +1.32 m |
| `caldwell_agency_log_house` | +792 | +124 | 22 m | +1.34 m |
| `cobweb_castle` *(stands)* | +814 | +122 | — | +1.34 m |

**The direction and the distances are invented**, exactly as the shop's own note admits of itself.
*Around* and *in its vicinity* are unquantified and nobody says which side of the agency house
anything stood on; west was taken because it keeps the group inside the ring the sources describe,
off the State Street frontage, and clear of the Wolcott Street corridor this project derives, whose
west edge is local **E +814.8**. Working uncertainty about **40 m** — the georeference's 20 m plus
the unquantified *near*. Every one of the five stands on traced `e1834_harbor_cut` ground at about
+1.3 m above the summer-1835 water surface, so none of the three new records declares a ground
contact.

**The ORDER within the row is reasoned, not read.** The smith is put beside his forge, the
interpreter nearest the agency house he interpreted for, and the striker at the far end because he
is the junior of the two men at the anvil. Those are arguments about a trade, an office and a wage.
The striker's house stands **87 m** from the Agency House, which is further out than the other two
and is stated in its record rather than hidden.

## 6. What this did not move

- **No presence verdict.** A roof is a house a source gives a man; it is not a statement that he
  stood in the town on 1835-07-01.
- **No occupation, and no resident card.** All three men were already carded on Andreas's words.
- **No source record, and no new source.** Both sources were already pinned: `andreas_1884_v1`,
  `kinzie_waubun_1856`.
- **No confidence upgraded anywhere.** `blacksmith_shop_state_st` keeps its own grades; its
  construction note already observed that the two sentences describe the blacksmith's **residence**
  among the group and that the shop taking the same fabric is a reading. This parcel raises the
  residence that note was pointing at and leaves the shop alone.

**Sources:** `andreas_1884_v1`, `kinzie_waubun_1856`.
**Links:** T-1714 · T-1204 · T-1374 · `indian_agency_1835.md` · `blacksmith_shop_state_st.md` ·
`docs/LIBERTIES.md` L283 · AGENTS.md § Standing constraint.
