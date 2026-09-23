# Walker Meeting House — research dossier

**Record:** `data/structures/walker_meeting_house.json` · **Scene status:** standing on
1835-07-01 · **Milestone 1 — the least settled record in the parcel**

The log building Father Jesse Walker put up at Wolf Point for worship and schooling. On
1835-07-01 it is the settlement's only building erected for either purpose. Walker himself died
in 1835.

It is also the only record in this parcel where the unresolved question is **which side of a
river a building stood on**.

---

## 1. The dispute, stated in full

### The west-bank reading — **adopted**

Two near-primary witnesses, both placing a log worship-and-school building in the west-side
row at Wolf Point:

> "North of this tavern was an oblong building which had been erected by Father Walker, a
> missionary of the Methodist Episcopal Church, for a place of worship, and for a school house."
> — `chicagology_prefire273`, immediately after describing Wentworth's (the Wolf Point) tavern

> "Facing down the river from the west was, first a small tavern kept by Mr. Wentworth … Near him
> were two or three log cabins occupied by Robinson, the Pottowattamie chief, and some of his
> wife's connexions. A little remote from these residences was a small square log building,
> originally designed for a school-house, but occasionally used as a place of worship whenever
> any itinerant minister presented himself."
> — `kinzie_waubun_1856`, describing 1831

Wau-Bun's building is inside an explicitly **west**-side sequence. chicagology's is fixed
**relative to the tavern**, which is itself on the west bank. Both are placeable.

### The north-bank reading — **not adopted**

> "in 1834 the growing congregation built a log cabin north of the Chicago River."
> — `chicago_temple_history`, the successor congregation's own history page

### Why west wins

- **Two near-primary witnesses against one modern page.** Wau-Bun is tier 2 and contemporary with
  the building; chicagology transcribes pioneer recollection. The Chicago Temple page is a
  modern, unfootnoted institutional history.
- **The west-bank sources give a position; the north-bank source gives a division.** "North of
  the Chicago River" names the whole North Division. "North of this tavern", with James Kinzie's
  house next south, places a building in a row.
- The 1838 move does **not** discriminate. The congregation floated the cabin across the river
  and rolled it on logs to Washington and Clark — a South Division destination reachable across
  the south branch from the west bank *or* across the main stem from the north bank.

### The reconciliation that is probably right

**Both readings may be true of different buildings**: an **1831 school-house on the west bank**
that Walker erected and Wau-Bun saw, and a **purpose-built 1834 cabin on the north bank** that
the congregation raised for itself and moved in 1838. The two sets of sources are date-specific
in exactly that way — the west-bank testimony describes 1831, the north-bank claim is dated 1834.

If that is what happened, the building standing on 1835-07-01 could be either or both, and this
record may model the wrong one. **This is not resolvable from the sources reached and is left
open rather than papered over.** A small corroborating detail sits on each side: the
congregation's first meetings in 1831 were reportedly in a house on the site of the Merchandise
Mart, which is the north bank; and Wau-Bun's "small **square**" against chicagology's "**oblong**"
is a disagreement about shape that would be explained neatly by there being two buildings.

## 2. Two flags for whoever owns the shared files

1. **`data/exclusions.json` disagrees with this record.** Its `methodist_meeting_house_south`
   entry — which correctly excludes a *south-side* Methodist church — states in passing that "In
   1835 the Methodist meeting house is on the NORTH bank". That statement and this record take
   opposite sides of §1. **Neither has been edited to match the other**, because the exclusion
   itself is sound and because rewriting a shared research record to agree with a new record
   would hide the disagreement rather than resolve it. Someone with authority over that file
   should reconcile them.
2. **Indigenous history — a judgement call worth a second opinion.** Jesse Walker's Chicago
   mission was a mission to the Potawatomi, so interpretive text about this building sits close
   to the project's standing constraint in `AGENTS.md`, even though the structure itself is a
   settler building and no human depiction is involved. `review_required` is set **false**,
   consistent with `sauganash_hotel` (named for Billy Caldwell, *Sauganash*). Flagged rather than
   decided unilaterally.

## 3. Placement

**No surviving intersection.** The coordinate is derived from the datum origin at the forks and
from bank geometry, and it is **stacked on the Wolf Point Tavern's own inferred position**, which
compounds the error.

- The footprint's south face is set **35 m north of the Wolf Point Tavern's north face**, which
  honours chicagology's "north of this tavern" and Wau-Bun's "a little remote from these
  residences".
- Its east face sits **9–14 m back from the modern west-bank line** (OpenStreetMap water
  polygons).
- It lies between the modern bank and Canal Street — i.e. on the West Water Street strip, which
  is where the river-front row belongs.

**Uncertainty:** ~20 m from the georeference; ~40 m along the bank inherited from the tavern's
placement; and **a step change of about 150 m, across the North Branch, if the bank is wrong.**
That last figure is the honest headline number for this record.

**Facade bearing 90°**, east onto the water — taken from the orientation of the river-front row,
not from any statement about this building. Nothing attests which way it faced.

Position tagged **`inferred`**, not `conjectural`: there *is* evidence for this placement and the
note states the reasoning, which is what `inferred` means. The residual risk is a disputed bank,
which belongs in the note and this dossier rather than in a tag that would claim no evidence
exists.

## 4. Footprint — an attested proportion at an invented scale

Only two adjectives are attested and **they conflict**: Wau-Bun's "small **square** log building"
against chicagology's "an **oblong** building".

**Square is adopted** for the proportion, because Wau-Bun is the earlier and nearer-primary
witness and was describing what she saw, while chicagology's is a recollection transcribed at
further remove. But a 7 × 7 m square is a **guess at scale wearing an attested proportion**, so
the polygon is tagged `conjectural` and cites no sources. 7 m ≈ 23 ft: a single-pen log building
large enough for ten founding members and a school.

## 5. Dates

| | |
|---|---|
| **from 1831-01-01** | Wau-Bun describes it standing in 1831; the first Methodist society was organised **14 June 1831**, ten members, in a log cabin |
| **to 1838-12-31** | the congregation floated the cabin across the river and rolled it on logs to Washington and Clark in 1838 |

Tagged `inferred`, because the start rests on identifying the 1835 building with the 1831 one —
the whole question of §1. Under the competing reading the phase begins three years too early.

The 1838 move is, incidentally, the second example in this dataset of why phases carry their own
position: early Chicago moved buildings routinely, and the Sauganash's log core had already
been relocated off a platted street in 1830.

## 6. Open questions

| question | where to look |
|---|---|
| **Which bank in July 1835** | Andreas vol. 1 on the early Methodist society; the First Methodist congregation's own archives; any pre-1838 depiction of the forks showing the building's side of the water |
| One building or two | The same sources — the 1831 school-house and the 1834 cabin may be distinct |
| Any dimension | Unattested in anything reached |
| Square or oblong | Unresolved; possibly a symptom of the two-buildings hypothesis |
| The 1835 painting reported to show Wolf Tavern, Miller's House and Walker's cabin in one view | Chicago History Museum — this would settle both the bank and the massing in a single image, and it has not been located for this record |
