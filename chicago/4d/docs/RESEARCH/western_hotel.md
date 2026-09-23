# Western Hotel — research dossier

**Record:** `data/structures/western_hotel.json` · **Scene status:** standing and in operation on
1835-07-01 under the adopted 1834 date · **Milestone 1, west bank**

The west-side wagon-trade house: a 40 ft front with a 60 ft wing in an L, a large stable, and a
yard the teams drove into with gateways from both streets. Distinct in clientele from the Green
Tree a block north and from the Sauganash across the river.

This is the one record in the parcel where a disputed date could have changed what stands in the
scene, and it is the one where the **phase mechanism was considered and deliberately not used**.

---

## 1. Conflict: built 1834 or 1835?

| reading | source | what it says |
|---|---|---|
| **1834** *(adopted)* | `chicagology_prefire278` | **W. H. Stow**, who "came to Chicago about 1833", "said it was built in 1834" |
| 1835 | `drloih_hotels` | "opened in 1835. It was a small structure built and operated by W.H. Stow on the S.E. corner of Canal and Randolph streets" |

**1834 is adopted because it is the builder's own statement about his own building**, recorded in
the same passage that supplies the 40 ft front, the 60 ft wing, the stable, the yard and the
clientele — against an undated one-line entry in a chronology that is unfootnoted, internally
inconsistent elsewhere (it also mis-dates the Wolf Point Tavern and mis-locates the Miller
House), and that mis-sizes this building in the same sentence.

`data/exclusions.json`'s `watch_list` already flags exactly this: "built 1834 by W. H. Stow per
chicagology, 1835 per the hotel chronology. If the later date is right it is brand new or still
going up on the scene date." This dossier resolves that watch-list item in favour of 1834 and
records the reasoning; the watch-list entry itself has not been edited (shared file).

## 2. Why the phase mechanism was NOT used

If the 1835 date were right, the hotel might have been unfinished or brand new on 1835-07-01,
and a `construction_1835` phase would be the honest way to render that — partial frame, no
cladding, a builders' yard.

**It would require inventing more than it records.** A construction phase needs a start month, a
build duration and a degree of completeness at the scene date. **No source gives any of the
three.** Worse, creating it would silently adopt the *weaker* of the two dates in order to have
something to model, which is the opposite of what the phase mechanism is for. The date gate
permits exactly one phase covering a scene date, so there is no way to represent "either
complete or under construction" as two overlapping phases; something has to be chosen.

**Decision: one completed phase on the better-attested date, with the alternative written into
the phase's `documented_range` note, this dossier, and the record's `research_note`.** It claims
less. If the 1835 date is ever confirmed, split the phase then.

## 3. Conflict: 40 × 60 ft in an L, or "a small structure"?

chicagology, from Stow's account:

> "The front was about forty feet and the wing sixty feet. It was in an L."

`drloih_hotels` calls it "a small structure". **chicagology's figures are preferred**: they come
with the builder's account and with the yard and stable description, while the chronology gives
no dimensions at all — "small" is an impression, not a measurement. A two-storey 40 × 60 ft L is
not small for 1835 Chicago, which is presumably why the chronology's author, working without
dimensions, guessed the other way.

## 4. The footprint — envelope attested, plan invented

- 40 ft = **12.19 m**, 60 ft = **18.29 m**; that is the polygon's bounding box exactly.
- The source does **not** give the arms' width. The 7.0 m (~23 ft) depth of the front range and
  the wing is invented — chosen as the shallowest width that makes an L rather than a solid
  block, enough for a room and a passage.
- Ground area ~164 m² (1,770 sq ft) follows from that and is **not** attested.
- The word "about" in "about forty feet" is the source's own.

Tagged `inferred`, citing chicagology, with the attested/invented split stated in the note.

**Which street the 40 ft front faced is not attested.** Randolph is adopted because it was the
through street from the west and this was the house "for all the farmers town from the west".
If the front was on Canal instead, the same L rotates to bearing 270° and the wing runs east
rather than south — testable once the lot geometry is read off Wright 1834.

## 5. The stable and the yard — an attested absence

> "the large stable and the yard into which the trains were driven. There were entrances to the
> yard from both streets."

**This is the point of the building.** It is the teamsters' house, and the enclosed wagon court
is most of what a visitor standing on Randolph would have seen. Neither the stable nor the yard
is dimensioned, and neither is built by the `frame_tavern` archetype, so both are an **attested
absence in the geometry** — recorded as `stables: true`, `documented`, on the record, and as a
liberty in `docs/LIBERTIES.md`.

Rendering the hotel block alone, with no yard, understates the site more than any confidence tag
can express. That is a real limitation of modelling buildings rather than parcels.

## 6. Placement

Corner documented by both sources; coordinate derived, so the tag follows the weaker half
(`inferred`).

Method, the Sauganash's: modern intersection centre from OpenStreetMap
(E 446919.6, N 4637148.5), offset **12.2 m east and 12.2 m south** — half an 80 ft platted street
in each direction — so the west face sits on the Canal frontage and the north face on the
Randolph frontage of a south-east corner lot. The southward offset is taken from the footprint's
north face, which is 18.29 m above its origin, so the origin's northing is
4637148.5 − 12.2 − 18.29 = 4637118.0.

Working uncertainty ~20 m, the georeference's, not an additional guess.

## 7. Construction — a deliberate difference from the Sauganash

`construction: balloon_frame`, `inferred`. Balloon framing was developed in Chicago in 1832–33
and had become the dominant local method by 1834, so it is the better reading here — **the
opposite conclusion from the Sauganash of 1831**, where the same reasoning argues for a braced
frame. Recorded explicitly so the dataset's two frame taverns do not silently carry the same
value for different reasons, and so nobody "fixes" one to match the other.

## 8. Open questions

| question | where to look |
|---|---|
| 1834 or 1835 | Any account independent of Stow; Andreas vol. 1 pp. 626–631 |
| Which street the 40 ft front faced | Lot geometry on Wright 1834 |
| Arm widths of the L | Unattested |
| Size and position of the stable and yard | Unattested; the yard's gateways are the only clue — one on each street |
| Exterior finish | Unattested; by 1834–35 painted siding was less remarkable in Chicago than in 1831, so `unpainted` is a weaker inference here than for the log buildings |
| The building's fate | No source reached gives one |
