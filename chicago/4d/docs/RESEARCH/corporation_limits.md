# The limits of the Corporation

**T-0436.** Two ordinances in this corpus bind only *"within the limits of the
Corporation"* and neither could be tested, because the line was not in the repository.
The ticket asked for one of two outcomes: the limits committed as geometry at the tier
the evidence actually carries, or the search recorded as a negative finding with what was
looked for and where.

**The answer is the first, and the evidence was already in the corpus.** The ticket's own
premise — that the only thing held is a prose note on a rung-3 compilation page — is
wrong, and finding that out is half of what this run did.

## The search

Everything below was searched in the tree at `dev` e8b61a085.

| where | what was looked for | result |
|---|---|---|
| `data/sources/` (285 records) | `corporation`, `incorporat`, `limits` | 8 hits. Seven are prose about the town code or about a building; one is `pal_chicago_incorporation_1835`, a Papers of Abraham Lincoln document entry at tier 4, held `text_only` and asserting nothing. |
| `data/research/newspapers/extracted/` | the boundary's own nouns — Jackson, Jefferson, Ohio, Kinzie's addition, the pier, the Canal Commissioners | **FOUND.** `chicago_democrat_1833_11_26#c024`. |
| `data/research/books/text/` (7 volumes) | the Illinois session law of 11 February 1835 enlarging the town — `February 11, 183*`, `11th of February`, `enlarge the boundaries/limits`, `an act to enlarge` | **no hit in any of the seven.** The act's text is not in this corpus in any printing. |
| `data/research/civic/claims/` | the extension chronology | `town_findings_andreas_v1.json` carries Andreas's two sentences on it, at tier 3 and with the year misprinted as 1834. |

## What was found, and why it outranks everything the project had been quoting

`chicago_democrat_1833_11_26` is **tier 1**: the first number of the first newspaper
printed in Chicago, verified against the page images, public domain. Claim `c024` is the
Trustees' own first village ordinance, passed 7 November 1833 and printed nineteen days
later, and it does not describe the boundary — **it walks it**, as a survey line, corner
by corner:

> beginning at the corner of Jackson and Jefferson streets, thence north along said last
> mentioned street and its continuation to Ohio street, in "Kinzie's addition to the town
> of Chicago," thence in a line eastward to the Lake shore, thence southwardly with the
> Lake shore to the northern United States' Pier, thence westwardly along said pier to
> the termination thereof, thence to the channel of the river until it intersects the
> eastern boundary line of the town of Chicago, as laid out by the Canal Commissioners,
> thence southwardly along said line until it intersects Jackson street, to the place of
> beginning.

The column is heavily damaged and every supply in the transcription is bracketed. The
walk survives complete anyway, because what survives is the **nouns**, and it is the
nouns that carry the geometry.

Against that, the page the project had been quoting for the same fact —
`chicagology_prefire278`, whose own record grades this half of it rung 3 because it is
Colbert's *Chicago* (1868) reprinted on a modern website — is **wrong twice**:

- it dates the ordinance 6 November 1833; the corporation's own printing says the 7th;
- it gives the west line as "Jefferson and Cook"; the ordinance names Jefferson alone,
  and no Cook Street appears in it.

No confidence in `data/reconstruction/1835_corporation_limits.json` is graded off that
page. It is cited there for exactly one thing, and it earns it: its independent "barely
seven-eighths of a square mile" is a check on the arithmetic, and the ring resolved from
the committed geometry comes out at **0.832 square miles** — 5 per cent under, which is
the direction an extrapolated corner should err in.

## What the boundary changed

Twenty-four drawn structures stand **outside** the limits. Every one of them is east of
State Street and north of Jackson: the United States Reservation and the harbour ground
beyond it, which the ordinance's river-and-State legs walk around. Eight of the
twenty-four carry chimneys — the fort's six, the US factor's house and J. B. Beaubien's
homestead, twelve stacks between them — and **section 18's eighteen inches never bound
one of them.** `tools/measure_stack_ordinance.py` still gates all 249 stacks, because
they all clear the figure anyway and the ratchet costs nothing, but it now reports the
reach instead of assuming it. That is the failure T-0436 predicted, already real: the
gate had been holding the fort to a town by-law that did not reach the fort.

The same run retracts a mistake in that gate's own docstring. It said section 22 of the
ordinance of 5 August 1835 "walks those limits street by street". **It does not** —
section 22 draws the hay-stacking boundary, which is a different and narrower line, and
is T-0334's — landed while this ran, at `data/reconstruction/1835_hay_limits.json`, and
199 acres against this boundary's 532. Section 22 is sometimes read as describing the
corporate limits and it does not describe them.

## What is still open

**The extension of 11 February 1835 is recorded and not resolved.** Andreas: *"The
corporate limits were again extended, by virtue of an act adopted February 11, 1834, so
as to include all land lying east of State Street to the lake shore, from Chicago Avenue
and Twelfth Street, except the military reservation, which lay from the river south to
Madison Street."* Wood 1881 reads the same event from the other side. Both are tier 3,
Andreas misprints the year, Chicago Avenue and Twelfth Street are not committed as
centrelines in this scene, and the act's own text has not been found in this corpus in
any printing. A boundary this project gates on cannot rest on that.

**It does not matter yet, and there is a date on which it will.** The extension adds
ground east of State and explicitly withholds the Fort Dearborn reservation, which is
where all twenty-four of the structures outside the 1833 ring stand. It adds nothing west
of State, and nothing drawn stands north of Ohio's line or south of Jackson's — so the
split is identical under both readings, and the gate scopes on the 1833 ring because it
is the narrower of the two and the only one held at tier 1. **T-0464 extends the modelled
terrain from Madison to Cermak.** The moment ground south of Jackson carries a building,
the February 1835 line is what decides whether the town's by-laws reached it, and this
question has to be answered before that ticket ships a chimney down there.

## How the extrapolations are priced

Four of the six legs are resolved by carrying a committed centreline past its own end,
and an extension is only honest while nothing stands near enough for it to decide a
building's side of the line. `tools/measure_corporation_limits.py` prices that rather
than asserting it: **±20 m** — the project's standing planimetric tolerance for a line
resolved off a cadastral plat — plus the length of the extension times how far the
committed surveys disagree about which way east runs. That disagreement is measured, not
chosen: **0.008225 in slope**, off `lake`, `ohio_north` and `madison`, because the School
Section's committed east-west lines are drawn exactly east-west while the Original Town's
and Kinzie's Addition's carry a real bearing.

| leg | extended | nearest building beside it | drift there |
|---|---|---|---|
| west — Jefferson, north to Ohio | 1,188.8 m | 78.4 m | 23.2 m |
| north — Ohio, west to Jefferson | 1,210.8 m | 287.4 m | 22.5 m |
| north — Ohio, east to the lake shore | 65.3 m | 312.3 m | 20.2 m |
| east — State, north to the river | 72.4 m | 238.2 m | 20.2 m |
| east — State, south to Jackson | 540.1 m | 301.2 m | 22.3 m |

Every clearance beats its drift by more than three times, so no extrapolation decides
anybody's side of the line today. The gate fails the day one does — and the instruction
in the failure is to trace the street or leave the structure's side unstated, never to
widen the tolerance.

One more disagreement is reported rather than averaged away: **the two committed State
Streets differ by 18.2 m** at Madison's line — `state` extended gives x = 823.6,
`state_school_section` starts at x = 841.86. The ordinance's line is the Original Town's
east boundary as the Canal Commissioners laid it out, so `state` is the one read.
