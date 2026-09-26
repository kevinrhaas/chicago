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
its self-test. **Thirteen readers today: 8 drawn, 2 control, 3 both.** A fourteenth that
does not declare is red before it can ship.

`tools/plat_corridors.py` is excluded by name: it *derives* both lines rather than reading
one, and `plat_corridors.LINES` is the one place the three words live.

## Links

T-0419 · T-0009 (the 2026-08-29 ruling) · T-0827 (`not_corridor_control_for`) ·
T-0429 (the roofs on `blk_south_water_lasalle`) · `tools/plat_corridors.py` ·
`tools/generate_plat_lots.py` · `tools/measure_corridor_strip.py` ·
`tools/check_corridor_line.py`
