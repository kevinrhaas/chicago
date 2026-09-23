# Dearborn Street Drawbridge — research memo

Record: `data/structures/dearborn_street_drawbridge.json` · Archetype: `bridge_timber`
Written 2026-08-11.

---

## 1. What this record is for

Chicago's first movable bridge: built March–summer 1834 by the ship-carpenter Nelson R.
Norton, in line with Dearborn Street across the main stem, with a sixty-foot draw hoisted
between two "gallows" frames. Ordered removed by the Common Council in July 1839 and
chopped to pieces by a crowd before dawn the next morning.

## 2. The length dispute, and the first time a measurement has settled one here

Two figures have circulated for over a century, and **this project's own two dossiers
took one each.**

| figure | source | dossier |
|---|---|---|
| "about three hundred feet long" | Andreas, *History of Chicago* vol. 1 (scan p. 415), read verbatim in the chicagology transcription (`chicagology_dearborn_st_bridges`) | 04 §4 |
| "200 feet long" | *Chicago Pictorial*, Historical Chicago National Bank, 1902, transcribed by chicagology as "The First Bridge Across the Chicago River, 1834" | 03 §5 |

**The third witness is the river.** The distance between the two traced 1834 waterlines
along the Dearborn Street alignment is **76.33 m = 250.4 ft** of open water.

Method:

1. The modern Dearborn Street centreline was read from OpenStreetMap at its Randolph
   crossing (node 28290271) and its Kinzie crossing (node 4336042974) — two points 528 m
   apart, straddling the river, on a street that survives on its 1830s alignment. The
   line through them runs at **359.419°** from grid north.
2. Its ends are set where the traced 1834 waterlines cross it, off
   `data/terrain/epochs/e1834_harbor_cut/shoreline.geojson`, which carries the main stem
   east of the forks box.

| | local E | local N |
|---|---|---|
| south bank | +699.17 | +20.72 |
| north bank | +698.39 | +97.05 |

**A bridge two hundred feet long does not cross two hundred and fifty feet of river.** A
bridge "about three hundred feet long" crosses it with about twenty-five feet of timber
over land at either end — exactly the long low causeway with approaches that dossier 04
§4 describes. Two numbers from evidence that shares no input, fitting each other without
adjustment.

**The error bar is smaller than the headline ±20 m.** That figure is dominated by a
common-mode shift: an affine that puts the whole neighbourhood 20 m north puts both banks
20 m north and the distance between them does not move. What survives into a *width* is
the sheet's local scale error — the fit records a 3.7 % difference between its two axis
scales, real paper stretch — plus the 1.78 m tracing tolerance. Even a generous 10 %
leaves the water gap above 225 ft.

The 1902 figure is quoted on the record and **deliberately not cited**: this project holds
no source record for that text, and naming a `source_id` that does not resolve would be
inventing a citation.

## 3. The correction: double-leaf and chain hoist are not attested

This record was drafted with both in it, from the brief. **Neither word is in any
underlying text.**

What Andreas actually gives: "gallows pattern"; the frames, "one at either end"; the
draw "hoisted"; and, of the occasion the machinery jammed, "for forty-eight hours the
gallows frames held the draw suspended in mid-air." That establishes it **lifted rather
than swung** and says nothing about leaves, chains, ropes or windlasses.

On the chicagology page that transcribes him, "leaves" and "double-leaf" occur **only** in
descriptions of the 1890s bascule and the 1907 and 1963 bridges — sixty to a hundred and
thirty years later. The one windlass on the page belongs to the State Street *ferry* rope.
The two dossiers gloss the same silence incompatibly: 03 says double-leaf and chains, 04
models a single hoisted leaf at midstream.

**Three arrangements fit every word of the evidence** and the record refuses to choose:

1. one leaf hinged at one end, hoisted from both frames;
2. two leaves, each hoisted by the frame at its own end;
3. the whole sixty-foot section lifted bodily between the two frames — the most natural
   reading of "suspended in mid-air", and the least often repeated.

Recorded on `form.draw_lifting_gear` (value `false`, `conjectural`, `geometry:
record_only`) — a negative finding: there is no lifting gear in this model and its form
is not evidenced.

## 4. What the mesh does with the draw

`bridge_timber` grew a draw for this record on 2026-08-11:

- **`draw_span_m: 18.288`** (60 ft, `documented`) clears the intermediate supports out of
  the opening — four of the sixteen evenly spaced stations fall inside it, so twelve are
  built — and stations the frames at its ends.
- **`gallows_frames: 2`** (`documented`) builds two heavy posts straddling the deck under
  a lapped cross-head at each end of the opening.
- **`gallows_height_m: 6.4`** (`conjectural`) is the archetype's own number and carries
  the whole frame's confidence, so the most conspicuous object on the crossing is the one
  the confidence view dithers hardest. That is the right way round.
- **The draw is built CLOSED.** The deck runs continuously across the opening, which is
  the state that fits all three readings at once. A raised leaf would have to pick one, in
  the most visible position on the bridge.

The earlier draft declared the draw and the frames `geometry: absent` and built neither.
That was defensible and it was overturned by a working-policy decision — *build liberally,
grade honestly* — on the argument that a dithered translucent frame says "this shape is
ours" in a way no footnote can, while an absent one tells a visitor the town's one piece
of engineering was a plain causeway.

## 5. What else is invented

| attribute | grade | why |
|---|---|---|
| `width_m: 3.048` | conjectural | Nobody ever wrote down how wide this bridge was. The value is the archetype's default — the branch bridges' documented ten feet — kept deliberately rather than replaced with a fresh guess, the same choice L29 made. Almost certainly too narrow for the main crossing of the town's principal street. |
| `pier_count: 16` | conjectural | The archetype's 4.5 m fallback spacing made visible as a count, per the repair L29 earned. Twelve are actually built. |
| `pier_kind: crib` | conjectural | Nothing says. Crib is preferred because federal engineers were building timber cribs at the mouth of the same river that year — a reason, not evidence. |
| `clearance_m: 1.83` | inferred | Borrowed from the branch bridges and labelled as borrowed. A bridge needing a sixty-foot opening for craft cannot have been high — a high fixed deck is the *alternative* to a draw. Complicating: the main stem carried masted vessels where the branches carried scows. |
| `deck_kind: plank` | inferred | Norton "commenced cutting the lumber" over the winter and built to a premium-winning design; riven puncheon is not what a ship-carpenter frames a hoisted draw from. First record in the dataset to carry this value. |
| `construction: timber_crib` | inferred | Sawn and framed carpentry, not the branch bridges' round logs. `bridge_timber` offers only `log` and `timber_crib`; this record sits at the edge of its archetype and says so. |

`stringer_count`, `stringer_d_m` and `plank_t_m` are left at the archetype's defaults and
not stated, because the record would only be repeating a default with "nobody said".

## 6. The dates

**Opening, 1834-08-01.** Norton's own letter says "I think it was completed by the 1st of
June"; Andreas corrects him on the spot — "the Democrat states that it was formally
accepted by the Trustees in August, the first proposals having been received in
February." The range opens on the later of the two, because the question a range answers
is when the structure certainly stood as a working public crossing. Nothing turns on it
for this scene. The `inferred` tag is for the opening, not the close: the August
acceptance rests on an 1834 issue of the *Chicago Democrat* this project does not hold.

**Close, 1839-07-31.** The best-attested date on the record — an order and a demolition
within a day of each other.

## 7. Condition at the scene date

Worn. The corporation paid $166.67 for repairs in September 1834, within weeks of
acceptance; Andreas records the bridge repaired again "in 1835 and 1837"; it "received
the blows of passing vessels and the curses of pedestrians and drivers". No source dates
or describes any repair closely enough to justify a second phase, so the record models one
state and its `change_note` says it was a patched one.

## 8. The structure stands off the edge of the modelled world

At local E +699 it is 380 m east of the committed heightfield, which stops at E +320.
Neither the river it spans nor the banks it lands on are modelled. `ground_contact` is
declared `outside_modelled_ground` for that reason; the smaller `approach_not_modelled`
finding is still underneath it and will surface when `docs/ROADMAP.md` S2e extends the
box east to about E +1560, from vectors already traced and committed.
