# The two lines down a platted street, and which one each reader follows

**T-0419 · the owner's ruling of 2026-09-21 · status: settled, and the odd number is
written down rather than resolved.**

Two lines run down each street of the 1835 plat in this project, and on two streets they do
not coincide. This file says what they are, which the owner ruled is the block grid's
control, what the disagreement between them is, and the rule that every module reading
either of them has to say which it took.

## The two lines

| | where it comes from | what it is the control for |
|---|---|---|
| **drawn** | the committed centreline in `data/streets/1835.json` | the **block grid**: `generate_plat_lots.block_edges` offsets this line by the platted half-module (12.192 m) to get the block faces, so every block, lot and roof in the town is seated on it |
| **control** | the same corridor re-centred onto the street's committed survey control in `data/traces/street_control.json` — `plat_corridors.control_offsets` | the **platted corridor**, per the owner's earlier ruling of 2026-08-29 (T-0009): what the intrusion table measures a body against |

`plat_corridors.corridors()` answers on the drawn line. `corridors(from_control=True)` and
`control_offsets()` answer on the control line. Neither call moves any data: the drawn line
in `data/streets/1835.json` is never rewritten by either.

A street acquires a re-centring from what its control says, not from a list of street ids —
`control_offsets` returns `centred`, `recentred`, `disagree`, `off_line`, `refused` or
`no_control` and is re-derived every run. **Two streets are `recentred` today**: `kinzie` by
+2.91 m and `south_water` by +8.58 m. Both figures are pinned by
`tools/measure_corridor_strip.py --gate` against `tools/corridor_strip_baseline.json`.

## The ruling: the block grid is NOT re-cut onto the control

The owner ruled on 2026-09-21, on T-0419, that the corridor and the blocks are answers to
**two different questions** and that the drawn line is the block grid's own control. The
alternative — re-deriving the grid through `generate_plat_lots` with the control-centred
line as `block_edges`' input — was priced first, and refused at that price:

| what branch A would cost | pinned figure |
|---|---|
| platted lots re-cut | **32** |
| committed roofs standing on them | **53** |
| blocks that leave the grid entirely (a corner falls on water) | **`blk_south_water_lasalle`** |
| committed roofs on that block | **18** |
| the grid after | 71 blocks / 218 lots |

The band branch A would abandon is **99.1 % dry**, which is the wrong shape for ground a
survey put in a river. The evidence does not carry the price, so the grid stays where it is.

**If the sheet is ever re-read** and the drawn line turns out to be survey control rather
than draughtsmanship, branch A comes back with evidence behind it. Nothing here forecloses
that; the price above is recorded so a future reading knows what it is buying.

## The disagreement, stated plainly and not resolved

On `south_water` the control line stands **8.58 m** north of the block faces derived from
the drawn one, and on `kinzie` **2.91 m**. **Nothing in the record says which of the two the
surveyor drew, and this project does not know.** That is written down here rather than
tidied away, and it is **not evidence that either line is wrong**:

* `data/streets/1835.json` already records that south_water's line "is shifted into the dry
  half of the platted riverfront corridor", 8.28 m perpendicular, "with 3.91 m to spare
  before its south edge". A plat corridor half in the water with the built street drawn in
  its dry half is consistent with both halves of the record.
* the control-derived corridor on that reach is **54.0 % river**. That reads oddly, and
  under this ruling it stands.

What lies between the two lines, measured on the committed 1834 heightfield
(`tools/measure_corridor_strip.py`):

| street | band | area | dry | platted lots in it | footprints lapping |
|---|---|---|---|---|---|
| `south_water` | **abandoned** — in the drawn corridor, outside the control one | 6,132 m² | **99.1 %** | 0 | `hogan_store`, `newberry_dole_warehouse`, `lasalle_slough_crossing`, `slough_log_bridge` |
| `south_water` | **claimed** — in the control corridor, outside the drawn one | 6,132 m² | 46.0 % | 0 | `dearborn_street_drawbridge` |
| `kinzie` | **abandoned** | 4,133 m² | 87.5 % | 0 | none |
| `kinzie` | **claimed** | 4,133 m² | 88.3 % | 0 | none |

Zero lots is measured as **area**: every lot on the South Water row *touches* its band along
the frontage, and a contact test answers sixteen. The band is 19.6 % of a lot's 43.83 m
depth and cannot hold a lot under either branch.

## The rule this leaves: every reader declares

The fault T-0419 found was **not a wrong line**. It was a reader that never said which line
it took, so nobody could tell whether its number was about the plat or about the town. So:

> A reader answering a question about a **block, a lot or a roof** stands on the **drawn**
> line. A reader answering a question about **where the plat put the roadway** stands on the
> **control** line. A reader whose subject **is the disagreement** takes **both**, on
> purpose, and says what each is for. Neither line is the other's control.

Every module that calls `corridors`, `control_offsets`, `intrusion` or `block_edges`
carries two module-level constants saying so, which is why they are greppable:

```python
CORRIDOR_LINE = "drawn"        # one of plat_corridors.LINES
CORRIDOR_LINE_WHY = "…"        # the question this module is asking, in one line
```

`tools/check_corridor_line.py` is the gate. It reads the **syntax tree** rather than the
text — every one of these modules discusses both lines at length in its prose, so a grep
for `from_control` would report almost all of them as control readers — and it fails a
module that declares nothing, declares a word that is not one of the three, declares
without a reason, or declares a line its own calls disagree with. `check.sh` runs it with
its self-test. **Fifteen readers today (2026-10-05): 10 drawn, 2 control, 3 both.** A
sixteenth that does not declare is red before it can ship.

`tools/plat_corridors.py` is excluded by name: it *derives* both lines rather than reading
one, and `plat_corridors.LINES` is the one place the three words live.

## The platted layer and the drawn town are two layers (T-1726, 2026-10-05)

`corridors()` covers **44 of the 80** streets `data/streets/1835.json` draws. The other 36
are out of it on purpose, and T-1726 decided they **stay out**: the platted layer is a
module-width rectangle on the block grid's rows and columns, read by gates that hold a
corridor edge against a block face, and on these streets that rectangle would assert a
plat nobody drew.

| out of the platted layer | streets | why |
|---|---|---|
| cut from a riverbank | `north_water`, `west_water` | the line is the bank offset half a corridor (`street_control.json` § north_bank, § west_bank) |
| held on an open question | `jefferson` | north of Kinzie it crosses Wabansia block 59, which Wright draws whole (T-2018) |
| laid by another survey | the School Section's 21 lines and tiers, `monroe`, `adams`, `jackson` | 66 ft and 80 ft lines of the 1833 subdivision, not the Original Town's module |
| | `michigan_north_tract`, `market_north_tract`, the tract's two alleys | their own widths from `seat_michigan_st_tract.py` |
| not platted at all | `fort_road`, `fort_bank_track`, `state_road_south` | roads, 6 m wide as drawn |

**What changed is the generators' question.** Asking "may I put a roof here" is a question
about the street, not the plat, so every generator's no-roof-in-the-road assertion now reads
`plat_corridors.every_corridor()`: the platted layer plus each omitted street at its **own
declared width** (`omitted_corridors()`, which was `generate_west_infill`'s private
`omitted_street_corridors` until now). `check_corridor_line.py` counts it as the DRAWN line.

**What turning it on found**, measured over every phase of every record on 2026-10-05: 20
footprints in an omitted street, and **one** of them a generator's. That one was
`inf_boatman_cabin_north`, an invented cabin standing 1.0 m from North Water Street's
centreline. The household programme's `corridor_clearance` now moves it `toward` north (south is
the river), 20.04 m, to 0.5 m clear of the drawn street. The other 19 are hand-placed or
sourced bodies, and `check_structure_corridors.py` already banks every one at its depth: 15
on North Water's bank, which is where the North Side's oldest houses were placed from
sources, the two Wabansia doctor's bodies in Jefferson (T-2018's question), and the two
bridges. One generator position was a false alarm. The household pass still derives
Heacock's pre-T-0884 house, in a School Section street, but it no longer owns that position,
so the assertion skips positions the ownership settlement withholds.

**A tension this records rather than settles.** North Water's record declares an 80 ft
corridor, and that width is what the generators now clear. But its frontage rule
(`measure_north_bank_frontage.py`) is the travelled track, with faces 5 m from the
centreline, so a roof dealt onto that rule would stand inside the declared width. No
generator deals one today. A future one that does has to choose between the two
figures, and the choice belongs to that parcel's ticket.

## Links

T-0419 · T-0009 (the 2026-08-29 ruling) · T-0827 (`not_corridor_control_for`) ·
T-0429 (the roofs on `blk_south_water_lasalle`) · `tools/plat_corridors.py` ·
`tools/generate_plat_lots.py` · `tools/measure_corridor_strip.py` ·
`tools/check_corridor_line.py` · T-1726 (`every_corridor()`)
