# A printed address outranked by a later printed address — the seven, ruled one by one

**Tickets:** T-0773 (the reading) · T-0949 (the refusals, landed as data a tool checks)
· **Records touched:** `data/research/newspapers/identity.json`
(`anchor_changes`, `refused_anchor_changes`) · **Tools:** `tools/measure_placement_silence.py`,
`tools/compile_gazetteer.py` § the dated anchor change ·
**Corpus:** `data/research/newspapers/extracted/` (the *Chicago Democrat*, 1833-11 to
1835-08; the *Chicago American*, 1835-06 to 1835-08)

T-0440 repaired the half of this population that is not a judgement — a house whose live
placement placed NOTHING while one of its own printings placed it, where silence does not
contradict speech. Thirteen houses were repaired by taking the earliest printing that said
something. This note is the other half: the houses whose live placement DOES place them and
which one of their own printings outranks. Preferring one printed address to another is a
statement about a house that moved or about copy that was reset, and the corpus rarely says
which, so the only instrument that may make it is the authored `anchor_changes` rule.

T-0773 listed seven. P. Pruyne & Co. left the list when T-0412 landed — the corner it
carried came off a building offered for sale by the firm and was never its own address —
so six were open when this pass ran. Each is ruled below. **One gained a rule, two were
already ruled elsewhere, two are the scene-date bound working, and one is deferred to the
ticket that owns it.** None was re-placed except through the authored rule, and the
compiler was not taught to prefer one printed address to another.

## What the report says now

`python3 tools/measure_placement_silence.py` counted all six on one line, "waiting on an
`anchor_changes` judgement". Only three of them were waiting on anything. The report now
separates the three populations, because a count that calls a settled house unsettled is
the kind of number a queue works from and should not have to correct:

| line | before | after |
|---|---:|---:|
| outranked, and waiting on an `anchor_changes` judgement | 6 | 3 |
| outranked, and the judgement has been WRITTEN | — | 1 |
| outranked only by a printing after 1835-07-01 | — | 2 |

The last two lines are not a weakening of the gate. `--check` still fails on exactly what
it failed on before — a house placed by a printing that gave no address — and the three
that are genuinely waiting are still named, still on one line, still counted.

---

## 1. G. Spring — RULED, and the placement moved

`business_g_spring`, `anchor_changes` written in `identity.json`.

Giles Spring, attorney and counsellor at law, advertised one card copy-dated **17 December
1833** through eleven printings from 1833-12-17 to 1834-11-26: *"OFFICE second door west
from the corner of Franklin and South Water streets."* From **1835-05-20** the paper carries
a different card, copy-dated **3 December 1834** — seven days after the last printing of the
old address — reading *"OFFICE, first door north from the Tre[mont] House, on
Dearborn-street"*, and it runs again on 1835-08-05.

These are two crossings of this town and not two spellings of one: Franklin and South Water
is at the west end of the business row, and the first Tremont House stands at the north-west
corner of Lake and Dearborn, some four blocks east. The identity merge of *Giles Spring* into
*G. Spring* already read both cards off the page and said the second one moves him; the rule
applies that reading to the placement rather than making a new judgement. The live placement
at the scene date of 1835-07-01 is now the Dearborn Street office.

**What the rule cannot say** is when — or whether — the office actually moved. The card that
first appears on 20 May 1835 was written five and a half months earlier, the deposit is not
the paper's whole run, and a lawyer taking a second set of rooms would read exactly like a
lawyer moving. The full `cannot_say` is on the rule; the earlier anchor is kept with its own
dates and its own eleven printings so a later pass can still tell the two cases apart.

The five readings of the Franklin corner are grouped as one landmark with its own `why`:
four spellings and one wreck of a line — *"PEHICE second door vcot from tho corner ee / of
Frankli s"* — which could only carry `the corner of Franklin [street]` with the second street
name lost to the type.

### The street had to go with it

A house's `street` is taken from whichever claim MINTS it, and `compile_register` adopts a
street face off that field rather than off the placement. So the first build of this rule
put Spring's office on Dearborn-street and left his row reading **South Water Street** — the
frontage the ruling had just retired, and the one the adoption pass would have set him on.
The street now follows the live reading wherever a rule names a single one; a corner reading
names two, and a `street` field holding both is not a street this town can adopt against, so
those are left alone. Matthias Mason & Co. is unaffected — its live reading names Main Street
and its row already did.

His register row is `street_only` on Dearborn Street rather than a building, because *"the
Tremont House"* resolves to nothing the committed town holds even though `tremont_house_1` is
in it. That is **T-0406**'s question — the Tremont House answering to the name the papers
print — and it is open with a branch on it. Nothing here touches it.

### The guard this rule broke first

Writing it exposed a defect in the mechanism. `anchor_changes` collected a house's readings
into a dict keyed by the anchor STRING, one reading per key — but a reading is grouped by its
whole placement, not by its anchor alone, and G. Spring is the one house in the corpus that
carries **one anchor string under two readings**: `the corner of Franklin and South Water
streets` is read `relative` across seven printings from 1833-12-17 and `corner` once on
1834-09-03. Keyed one-to-one, the later overwrote the earlier and the rule's history lost
seven claims and eleven months of window — and guard 4, the guard that exists to catch a
printing silently dropped, could not see it, because the anchor was still claimed. An anchor
now holds every reading printed under it. The Matthias Mason rule is unaffected: it has no
repeated anchor string, and neither does any other house.

### And the gate that then refused it

With all eleven printings visible, `compile_register.py` refused the rule outright: *"the
readings grouped under the anchor 'the corner of Franklin and South Water streets' resolve
to 2 different things in the committed town"* — a `corner` of Franklin and South Water, and
a `street` reach of South Water alone. That gate is right in principle and was wrong here,
for a reason worth writing down.

The reading it objected to is 1834-05-28, and what survives of that printing is *"[corne]r
[F]ra[n]klin and South W[at]er-str[ee]t"*. The word **of** went with the type, so
`resolve_anchor`'s corner pattern — which looks for "corner of X and Y" — does not match,
and all that resolves is the reach of South Water Street. It is the same corner, read
through a broken line.

`resolve_anchor`'s own docstring says a `street` resolution does not put a building on the
ground, and `ANCHOR_KIND_RANK` ranks it below everything that does; the anchor history
already resolves a group on its BEST reading for exactly this reason — *"'Graves' Tavern'
resolving where 'Graves' Tavern, on Main-street' does not is a fact about how much of the
sentence one reading pass swept into the field."* The gate nonetheless excused the reading
that swept in NOTHING (`unresolved`) and refused the one that swept in half. It now excuses
a `street` reach too — **but only where the placing resolution names that street.** A reach
the landmark does not name is still two places declared one landmark and still fails, and a
group that resolves to two different reaches and to nothing that places fails as well. Three
self-test cases, all firing.

## 2. J. K. Botsford — ALREADY RULED, by T-0324, and no rule may be written

`business_j_k_botsford` holds *"next door to Graves' Tavern"* (1834-02-18) and is outranked
by *"corner of Dearborn and Lake streets"*, printed from 1834-02-25 and unbroken to the end
of that year.

T-0324 read every printing of both and ruled: **the two addresses are one frontage.** Graves'
Tavern is the Mansion House, on the north side of Lake Street just east of Dearborn, and the
corner is the corner it stands on. A move was refuted outright. So no reordering is owed —
the outranking reading names the same ground the live one does.

No `anchor_changes` rule may be written here even if one were wanted, and the mechanism is
right to refuse it: the two anchors were printed in **overlapping weeks** — the tavern
reading runs 1834-02-18 to 1834-04-01, the corner reading starts 1834-02-25 — and guard 6
holds that a change is a change only where one anchor stops before the next starts.
Overlapping anchors are two standing descriptions of one house, which is exactly what T-0324
found this to be. See `docs/RESEARCH/botsford_graves_1834.md`.

## 3. Newberry & Dole — DEFERRED to T-0396, which owns the question

`business_newberry_dole` holds a `street_only` reading from 1834-03-04 and is outranked by
*"opposite to Fort Dearborn"* (1834-05-14).

T-0396 is open on this firm and asks something prior to its address: whether the partner is
Oliver Newberry or Walter L. Newberry, which the corpus reads one way in 1834 and the other
in 1835. T-0773 states plainly that it must not overtake that ticket, and the placement is
not ordered here. The reading is kept with its own date and the row stays on the waiting
line.

## 4. J. S. C. Hogan — WAITING, and the instrument is wrong rather than the evidence

`business_j_s_c_hogan` holds `{"class": "street_only", "anchor": null}` from a single
printing, 1834-03-25 c010, and is outranked by *"in South Water Street, one [door … of] the
Post Office"* — printed eight times from 1834-08-13 to **the scene date itself**, 1835-07-01.

Read the minting claim and the row dissolves. It is a two-line notice of three hundred cedar
posts under a scrap of song about fencing a garden: *"300 CEDAR POSTS, for sale che[ap] by J.
S. C. HOGAN. March [24]."* **It names no address at all.** The `street_only` class and the
`South Water Street` beside it come from the extraction's business-level `street` field,
supplied by a reader who knew where Hogan's store was, not from anything the advertisement
printed.

So this is T-0440's population — silence that does not contradict speech — wearing a
`street_only` mask, and it is invisible to that repair because the repair fires only where
the live rank is zero. Ordering these two readings needs no judgement about a house that
moved. What it needs is the compiler taught that a `street_only` naming no street and no
landmark places nothing, and T-0773 forbids teaching the compiler anything of the kind.
**Filed as its own ticket** rather than done here.

### T-0859 ruled it, and the row dissolved (2026-09-06)

The ticket filed here was taken up the same night and the answer is the one this section
predicted, with a count behind it.

**The ruling.** A `street_only` placement carrying neither a `street` nor an `anchor` names
no street, and puts a storefront on no more ground than `{"class": "none"}` does. It is a
statement about the PLACEMENT RECORD and not about the advertisement. `places_nothing()`
lives beside `placement_rank` in `compile_gazetteer.py` so the two cannot drift, and the
T-0440 repair now uses it on BOTH sides — a pass may not take up a reading it would itself
refuse to be held by. Nothing else changed: same earliest-placing tie-break, same scene-date
bound, same refusal to let one printed address override another.

**The count: twelve claims across eleven houses.** Four houses moved, and only four:

| house | before | after |
|---|---|---|
| `business_j_s_c_hogan` | `street_only` off the cedar posts | **`relative`, one door from the Post Office**, off eight printings to the scene date |
| `business_newberry_dole` | `street_only` naming no street | `relative`, *"opposite to Fort Dearborn"* — see below |
| `business_brewster_hogan_co` | `street_only` naming no street | `none` — the dissolution notice says *"at the old stand"* and no more |
| `business_david_carver` | `street_only` naming no street | `none` — the lumber notice says *"at his Store"* and no more |

The last two are the ruling paying its own way in the other direction: two houses stop being
placed on a street their own printings never named. Neither is re-placed, neither loses its
business-level `street`, and both read `unplaceable` in the register as they did before.

**Newberry & Dole is the one to argue with, and the argument is that this is not the
judgement §3 deferred.** Its `street_only` reading names no street; once that places
nothing, the firm has exactly ONE printing that places it, *"opposite to Fort Dearborn"*
(1834-05-14), and taking it is T-0440's ordinary rule — silence does not contradict
speech — applied as it is to twelve other houses. No printed address is preferred to
another, because there is only one. **T-0396's question is untouched**: it asks which
Newberry is the partner, and nothing here answers, prejudges or depends on that. The
register row is still `unplaceable` — *"Fort Dearborn"* resolves to nothing this row can
enrich — so the town does not move on it either.

**And the count turned up a defect the ruling does not fix.** Eight of the twelve notices DO
print a street in their own prose — *"a lot and Store[hous]e on South Water Street"*,
*"Dearborn-stree[t]"*, *"a shop, on Randolph street"* twice, *"at the corner of […] and
Canal streets"*, *"at his room on south water street"*, *"Montgomery's Auction Room, South
Water Street"* — and the reading pass put it in the claim's business-level `street` field
and left the placement empty. Nothing is mis-placed by it today, because
`compile_register` adopts a street face off that field; what is wrong is that the reading
does not say what the printing said. **T-0861** carries it.

**One thing written here was wrong and is corrected.** The compiler's own comment named
Jones, King & Co. as the house the scene-date bound holds — *"silent through its 1834
printings and given South Water Street on 1835-08-05"*. It is not: that 1835-08-05 notice
is a fire-insurance agency card printing no address at all, and the South Water Street
beside it is again the business-level field. The house is silent on both counts and the
bound is not what holds it. The bound is unchanged and still asserted, now on a fixture
rather than on a house that turned out not to be one.

### T-0861 carried it, and the twelve are five (2026-09-11)

The defect the count turned up is repaired at the reading, and the arithmetic above is
corrected with it: **seven** of the twelve print a street, not eight. The table in the
section above lists six quotes and one corner, and five notices are correctly silent —
David Carver *"at his Store"*, Brewster, Hogan & Co. *"at the old stand"*, Newberry &
Dole's assortment card, Hogan's three hundred cedar posts, and the Jones, King & Co.
page, which carries a fire-insurance card printing no address at all. Five, not four.

**The six that print a plain street now carry it in the placement, quoted off their own
type.** Each takes `street`, an `offset_text` that is a verbatim substring of the claim's
own `quote`, and an `offset_normalized` beside it — the same three fields every other
`street_only` in the corpus carries:

| claim | placement street | printed |
|---|---|---|
| `chicago_democrat_1834_03_04#c004` Hiram Pearsons | South Water Street | *"that he has purchased a lot and Store[hous]e on South Water Street"* |
| `chicago_democrat_1834_11_05#c008` Jno. S. Wilson & Co | Dearborn Street | *"Dearborn-stre[et]"* |
| `chicago_democrat_1834_11_12#c005` Briggs & Humphrey | Randolph Street | *"[for] a shop, on [R]andolph street"* |
| `chicago_democrat_1834_12_03#c016` Briggs & Humphrey | Randolph Street | *"for a shop, on Rando[l]ph street"* |
| `chicago_democrat_1835_08_05#c004` Samuel Lewis | South Water Street | *"at his room on sout[h] water street"* |
| `chicago_democrat_1835_08_05#c016` W. Montgomery | South Water Street | *"re[c]eived a[t] Montgomery's Auction Room, South Water Street"* |

**Pierce & French is the seventh, and it is NOT read as a corner.** The 17 December
impression carries neither the word *corner* nor the first street name: what survives is
*"and Canal streets, oppor"*, and the plural is the only trace of a junction. The same
standing advertisement — one dateline, 25 June 1834 — does print the corner, four times
(1834-06-25 c005, 1834-07-02 c051, 1834-09-10 c017, 1834-11-19 c007), and those readings
carry `corner` on their own type. Reading THIS printing as a corner would take the word
off its sister impressions rather than off this page. So it stays `street_only` and
carries the one street the page does print, Canal Street, with the reasoning on the
placement itself. What is repaired is the silence, not the class.

**And the five that print nothing keep an empty placement, and now say why.** Each
carries a placement `note` stating that the prose names no street and that the
business-level `street` beside it is not read back into a placement the page never had —
which is the distinction the whole of §4 turns on, written where the next reader of the
claim will meet it rather than only here.

**Nothing moved in the town.** No house's live `placement`, `placement_from` or `street`
changes across the rebuild — the register adopts a street face off the business-level
field, so nothing had been mis-placed by the silence, exactly as the ruling said. What
changes is `places_nothing`'s population: **twelve claims to five**, and the five are the
population proper. `measure_placement_silence.py --check` re-derives and still passes,
with three houses under *no printing of theirs ever named any ground*.

## 5 and 6. Rockwell, and Samuel Lewis — NO JUDGEMENT IS OWED

Both are outranked only by a printing that ran **after the scene date**.

* `business_rockwell_cabinet_furniture_warehouse` is placed by 1835-06-27, *"Apply to […]
  ROCKWELL, [S]outh Wate[r street]"*, and outranked by 1835-07-04, *"[F]urniture a[t] the stand on
  S[outh] Water [s]tre[e]t, formerly occ[u]p[i]ed by Clark, [Fils?] [C]o."* — three days after the
  scene. The two do not even disagree: same street, and the later adds the stand.
* `business_samuel_lewis` is placed by 1835-07-22 and outranked by 1835-08-12, whose
  anchor is read `A. Garrett's Auction Room` off *"call at ita room pa South | ter street,
  (A. Gartetl's Auctiog Rowe)"* — **both** printings after the scene.

AGENTS.md rule 3 and the compiler's own scene bound say an address first printed after 1 July
1835 was not up on 1 July 1835. A rule preferring either of these later readings would place
a house on the strength of an advertisement that had not run yet, which no `anchor_changes`
rule may do — its live anchor is computed from the scene date for this exact reason. The
report now says so on its own line instead of counting them among the houses waiting for
someone to decide something.

---

## T-0949 — the refusals, landed as data the compiler checks (2026-09-11)

Everything above was written as PROSE. T-0927 found, checking PR #962 against `dev`, that
the machinery which made the same five refusals *declarations a tool reads* had never
landed on any branch that merged: `identity.json` had no `refused_anchor_changes`,
`compile_gazetteer.py` had no `REFUSED_ANCHOR_KINDS`, and `measure_placement_silence.py`
could not tell a refusal from a house nobody had opened. T-0949 lands it.

**What a declared refusal is now.** `identity.json` § `refused_anchor_changes` holds one
entry per house: the `business`, a `kind`, and a `refused_because` that must name VERBATIM
one of the anchors it refuses to be reordered by. `compile_gazetteer.py` checks the kind
against the readings rather than taking the author's word:

| kind | what the compiler makes it prove |
|---|---|
| `printed_in_the_same_weeks` | a reading of the LIVE anchor and one that outranks it have overlapping windows |
| `silence_is_not_an_anchor` | the live placement names no anchor at all |
| `after_the_scene_date` | every printing that outranks the live placement was first set after 1835-07-01 |

and, whatever the kind: the house is compiled, it is not ALSO declared an
`anchor_changes`, the reasoning is not empty, and — the load-bearing one — **something
still outranks it.** A refusal whose pair has gone is a judgement about nothing and is a
compile error, exactly as T-0399's firm refusals are. Nine of the ten guards are asserted
in `compile_gazetteer.py`'s self-test — the tenth, a set of outranking readings that name
no anchor at all, is unreachable from any placement the corpus produces and is left as a
compile error without a fixture. The self-test includes *a REFUSAL re-placed the house it
refused to re-place*, which is the one that keeps this from becoming a re-placement
mechanism by accident.

**Two of the five could be declared, and that is the pair guard working.** Between
T-0773's reading on 2026-09-06 and this landing on 2026-09-11, three later tickets
repaired their own halves of the population, and each left a refusal with nothing to
refuse:

| house | T-0773's refusal | why it could not be declared |
|---|---|---|
| `business_j_s_c_hogan` | `silence_is_not_an_anchor` | T-0859/T-0440 place it from 1834-08-13; nothing outranks it |
| `business_newberry_dole` | `silence_is_not_an_anchor` | same — placed from 1834-05-14 |
| `business_rockwell_cabinet_furniture_warehouse` | `after_the_scene_date` | T-0948 narrows it on its own street under its own dateline |

The compiler refuses all three with *"no printing of this house outranks its live
placement — a refusal whose pair has gone"*. Writing them anyway would have been the
rotten record this whole mechanism exists to prevent, so they are recorded here and not in
`identity.json`. `silence_is_not_an_anchor` is consequently declared by no house today; the
kind stays, because the next silent-then-anchored house will need it and its guards are
asserted in the self-test.

The two that stand:

* **`business_j_k_botsford` — `printed_in_the_same_weeks`.** Live anchor *Graves' Tavern*,
  outranked by six `corner` readings of *the corner of Dearborn and Lake streets* running
  1834-02-25 to 1834-12-03. Both cards run in one issue, 1834-04-01, and Graves' Tavern IS
  that corner (T-0324). The overlap guard confirms the concurrency from the readings' own
  windows.
* **`business_samuel_lewis` — `after_the_scene_date`.** Live placement `street_only`, South
  Water Street; outranked by the `relative` reading *A. Garrett's Auction Room* of
  1835-08-12. The guard re-derives that 1835-08-12 is after 1835-07-01, so the refusal
  cannot outlive its own reason: the day the corpus carries a printing of that room on or
  before the scene date, the compile fails rather than the house quietly changing bucket.

**The report's three ways became six, and the number the ticket asked for is zero.**

| line | count |
|---|---:|
| outranked, and waiting on an `anchor_changes` judgement | **0** |
| outranked, and the judgement has been WRITTEN | 1 |
| outranked, and DECLARED REFUSED a change | 2 |
| outranked only by a printing after 1835-07-01 | 0 |

Nothing in the town moved: `--build` on the gazetteer and the register leaves the same
206 houses with the same actions, and the only new field is `anchor_refusal` on the two
houses above. The corner-crossing guard T-0773's branch also carried had already landed on
`dev` in a more general form — `street` resolutions are excluded from the one-landmark set
and a street reach is required to be CONTAINED by the placing resolution, with both of its
self-test cases — and G. Spring's superseded window duly resolves as `corner`, checked here
rather than taken on trust.

---

**Links:** T-0773 · T-0949 (the refusals, landed as data) · T-0440 (the silent half,
repaired) · T-0345 (readings kept with their own dates) · T-0324 · T-0396 · T-0407 ·
T-0412 · T-0859 · T-0927 · T-0948 · `tools/measure_placement_silence.py` ·
`tools/compile_gazetteer.py` § the dated anchor change and its refusal.
