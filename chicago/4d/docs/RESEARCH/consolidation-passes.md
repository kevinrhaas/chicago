# The consolidation passes — the ledger of the series

A consolidation pass takes the rulings CLOSED SINCE THE LAST PASS and writes them onto the
cards they name. It reads nothing new. The series exists because of an instruction the
owner gave on 2026-09-03 — *"dont land those tickets at the very end maybe every few you
should do that consolidation"* — and it is a numbered series (T-0634, T-0635, T-0636)
rather than one recurring ticket because a `done` ticket cannot be re-claimed.

**This file is the starting line for the next pass in the series.** Each entry says what
its window was, which crosswalks it consumed, which it skipped as already spent, and what
the two hops of `tools/measure_research_spend.py` read before and after. A pass that finds
nothing newly closed writes an entry saying so and costs a run almost nothing; that is the
design, not a failure.

The two hops, and they are different questions:

* **Hop 1 — read vs ruled.** Of the units a domain has READ, how many has anything ruled
  on? A source volume read and never adjudicated is unspent.
* **Hop 2 — ruled vs on a card.** Of the rulings that NAME A PERSON IN THIS TOWN, how many
  reached that person's card? A ruling that never leaves `data/research/` is a ruling a
  visitor cannot see.

---

## Pass 1 — T-0634, 2026-09-04

**Window:** everything closed after T-0513 (2026-09-03T22:01Z) up to dev at `80330dc7`.
Fifty tickets closed in that window.

**Consumed:** `data/research/civic/voter_crosswalk.json` — the four early Chicago lists
(the 1833 trustees' poll, the 1833 tax list, the 1834 poll, the 1835 poll), 345 entries,
99 of them matched to people this town holds and NONE of the 99 written onto a card. The
pass is `tools/spend_civic_voter_lists.py`; its ledger is
`data/research/civic/voter_spend_1835.json`.

**Skipped as already spent:** `data/research/directories/` — T-0632 spent all four
directory crosswalks the same morning and hop 2 already read 235 reached / 235 written / 0
unwritten for that domain. `data/research/census_1840/resident_crosswalk.json` — nine of
its ten rulings were already on their cards, and the tenth (John H. Kinzie) is closed by
this pass as a consequence rather than by a separate write: his record now cites
`chicago_voter_lists_1833_1835_irad`, which is one of the four sources that ruling rests
on, and the instrument's test is whether the card learned ANYTHING from the ruling.

**Skipped as not a ruling about a person:** every domain whose crosswalk holds only
refusals and pass notes — church, books, land_sales, newberry_index, and civic's own
`crosswalk.json` (90 refusals, 2 passes). A refusal names no person to write to. These are
hop-1 work and belong to the spend tickets (T-0514, T-0515, T-0609, T-0633), not here.

### Hop 2 — ruled onto a town person, and whether their card learned it

| domain | reached | before: on a card | after: on a card | before: unwritten | after: unwritten |
|---|---|---|---|---|---|
| civic | 99 | 0 | **99** | 99 | **0** |
| census_1840 | 10 | 9 | **10** | 1 | **0** |
| directories | 235 | 235 | 235 | 0 | 0 |
| **TOTAL** | **344** | **244** | **344** | **100** | **0** |

**Every ruling in this project that names a person in this town is now on that person's
card.** The `unwritten_ceiling` for civic and census_1840 is tightened to 0 in
`tools/research_spend_baseline.json`, so it cannot regrow silently.

### Hop 1 — read vs ruled

Unmoved, and unmoved on purpose: this pass reads nothing and adjudicates nothing, so it
cannot spend a unit. Measured either side of it the totals read `16,322 read · 4,553 spent
· 11,769 unspent · 502 id pairs`, unchanged. (T-0664 merged into dev while this pass was
in flight and added 765 directory claims of its own, so the totals a later reader measures
will be larger; the figure this entry holds is the pass's own delta, which is zero.) Hop 1
is what T-0514, T-0515, T-0609, T-0610 and T-0633 move.

### What the layer looks like after it

The defect T-0513 measured was *breadth of citation*: how many sources a household record
rests on. Counted across all 848 household records:

| distinct sources cited | before | after |
|---|---|---|
| 1 | 664 | **656** |
| 2 | 71 | 71 |
| 3 | 45 | 41 |
| 4 | 46 | 44 |
| 5 | 19 | 23 |
| 6 | 3 | **11** |
| 7 | 0 | **2** |

Eight households come off a single source. The movement is concentrated at the top of the
table rather than the bottom, and that is what a voter roll would predict: the men who
stood at a town election are the men the rest of the corpus already names, so the roll
mostly deepens records that were already several sources thick. The 656 that still rest on
one source are the letter-list people, and they are T-0515's.

**Grades changed by this pass: 0.** The ratified ladder is applied by T-0515 against every
source at once; a pass that wrote the evidence and graded off it in the same breath would
be marking its own work.

---

## Pass 2 — T-0635, 2026-09-04

**Window:** everything closed after pass 1 (T-0634, 2026-09-04T13:42Z) up to dev at
`36d1dde2`. Twenty-three tickets closed in that window.

**What the pass found first, and it was not a ruling: the instrument was blind.** The
opening measurement read **0 unwritten across every domain it could see** — a clean bill
of health, and an artefact. The second hop asked for the verdict in an `outcome` field, and
the crosswalks that landed in this window say "match" by the NAME OF THE ARRAY a row is
filed in — `matches: [...]`, `merges: [...]` — or file their rulings one level down, under
the pool each name was matched against. The spend half above had already learned this
lesson the hard way and its own comment says so; this hop had the mirror of that bug for
its whole life. Repairing it made 510 rulings visible that the pass would otherwise have
reported as nothing at all.

The heading could not simply be ignored the way the spend half ignores it, because for THIS
hop the heading is the only verdict some files give and the difference between `matches`
and `refusals` is the whole question. So the repair is two narrow, named things rather than
a wider whitelist: `MATCH_CONTAINERS` is `matches` and `merges` and deliberately excludes
`refusals`, `ambiguous`, `contested`, `probable` and `passes` — a rival still standing is
not a ruling to spend — and `RULING_DEPTH` is 1, so the walk descends through one level of
POOL grouping and no further, because a table three dicts deep is a structure this
instrument has no business reading as a list of rulings. Both are held by tests that fail
if either is undone.

**Consumed:** `data/research/directories/fergus_1839_election_crosswalk_1835.json` (T-0664,
the poll of Chicago's first city election, 2 May 1837) and
`fergus_1839_register_crosswalk_1835.json` (T-0665, the city register of 1839) — **101
rulings written onto 97 cards** by `tools/spend_fergus_1839_later_lists.py`, gated in both
directions like the civic pass before it.

**Skipped as already spent:** `civic/voter_crosswalk.json` — pass 1 wrote all 99.
`census_1840/resident_crosswalk.json` — 10 of 10 on their cards. The 1843 and 1844
directory crosswalks — T-0632 spent them. `old_settlers/crosswalk.json` — T-0577 landed in
this window and its own enrichment pass wrote every OS1/OS2A merge as it went, which is the
pattern this series wants: a reading ticket that spends what it rules on leaves the
consolidation nothing to do, and that is a success, not a gap.

**Skipped as not a write, by the file's own rule:** `old_settlers/crosswalk.json`'s six
`probable` rows ("PROBABLE, NOT MERGED: no record is written on it") and
`old_settlers/death_notices_crosswalk_1835.json`'s `contested` and `ambiguous` blocks ("no
match is made"). A refusal is a ruling that the card must NOT learn from it.

**Blocked, with the crosswalk that owes it and a ticket that will pay it** — acceptance
clause 2, and none of the three is invented work:

| owed by | rulings | ticket |
|---|---|---|
| `land_sales/resident_crosswalk.json` — 35 purchasers matched to households, no card citing the register | 35 | **T-0677** |
| `directories/fergus_1839_lots_crosswalk_1835.json` — T-0666's Fort Dearborn lot sale, 11 bidders matched, 3 uncited | 3 | **T-0681** |
| `old_settlers/` — registered in no `domains.json`, so BOTH hops are blind to a domain holding 327 people and 745 death notices | not measured | **T-0678** |

The land-sales file had also never stated what it was adjudicated from, so even once seen
not one of its rulings was judgeable. `tools/read_land_sales.py` now states its `source_id`
at the top of the crosswalk — T-0598's ratified narrow form — which turns 35 unanswerable
blanks into 35 debts with a number on them. A working `tools/spend_land_sales.py` that pays
them is pushed on `steward/salvage-t0635-mine` for whoever takes T-0677.

### Hop 2 — ruled onto a town person, and whether their card learned it

| | reached | judgeable | on a card | unwritten |
|---|---|---|---|---|
| before, hop as it stood | 472 | 472 | 472 | **0** |
| before, hop repaired — the honest opening state | 982 | 982 | 918 | **64** |
| after | 982 | 982 | 944 | **38** |

510 rulings that were invisible to the hop are now measured. Of the 64 the town genuinely
owed, the 26 this pass could pay are paid; the 38 left are the two ceilings above, each
recorded against a ticket rather than absorbed.

### Hop 1 — read vs ruled

Unmoved, and unmoved on purpose: this pass reads nothing and adjudicates nothing, so it
cannot spend a unit. `18,537 read · 5,556 spent · 12,981 unspent · 276 id pairs`, measured
either side of it. Hop 1 is what T-0515, T-0610 and the source tickets move.

**Grades changed by this pass: 0.** The ratified ladder is applied by T-0515 against every
source at once; a pass that wrote the evidence and graded off it in the same breath would
be marking its own work.

### The starting line for pass 3 (T-0636)

Its window opens at this entry. Three crosswalks are knowingly unspent and each has a
ticket — T-0677, T-0681, T-0678 — so pass 3 should check whether those landed before
looking for anything new.

**And one thing this pass repaired only as far as it had to.** A container name that is
neither in `MATCH_CONTAINERS` nor a known refusal heading is still dropped in silence, and
a ruling grouped two levels down is still invisible. That is the same shape of hole this
pass opened with, one turn of the screw further out, and the honest thing to say is that
the instrument is now right about the dialects this corpus actually uses and makes no
promise about the next one. A pass that finds a domain reporting a suspiciously clean zero
should suspect the reader before the data.
