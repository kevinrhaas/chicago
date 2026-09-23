---
id: T-0239
title: Nothing tests the party-line note's prose against the placement it describes
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

Nothing tests the party-line note's prose against the placement it describes.

Found while fixing T-0208, which was itself found while fixing T-0189. **Three faults now, all
in `FRONTAGE_NOTE` in `tools/generate_block_infill.py`, all the same shape**: a sentence written
for the run it was first used on, printed verbatim on every run since, making a claim about the
building that the placement code does not support.

- **T-0189** — the note told a house on Washington Street, 400 m from the water, that it stood
  on "the town's river business front".
- **T-0208** — the note said the EAST wall was the anchored one on a run that anchors WEST, on
  nine of the twenty-seven records carrying it.

`generate_block_infill.py --check` is not the guard for this and cannot be. It re-derives every
committed record byte for byte **from the same template**, so a template that says the wrong
thing re-derives the wrong thing perfectly and the gate stays green. Both faults were found by a
person reading the file.

## What a real gate would read

The note makes checkable geometric claims, and the geometry is in the record beside it:

- *"its {wall} wall is fixed by {anchor}"* — the named wall's along-face coordinate should equal
  the anchor's own datum (the face's `along_min + clear_m`, the face's `along_max - clear_m`, or
  a named neighbour's measured extent) to the tolerance the party-wall joins already use.
- *"its front wall is {setback} m back from that lot line"* — a measurement of the footprint
  against the committed block face, which `tools/measure_street_line.py` already knows how to take.
- *"the bearing is the face's own"* — already asserted in `place_frontage`, and the only one of
  the three that is.

That is the difference between a gate that checks the generator against ITSELF and one that
checks the PROSE against the GEOMETRY, which is the only kind that could have caught either
fault.

## Why it is worth a ticket rather than a note

**Provenance is the product.** These notes are the card a visitor opens to ask which of this was
invented and on what warrant; a note that misdescribes the placement is a provenance defect, not
a typo. Twenty-seven records carry this one today and every new platted block adds more.

**Acceptance:** a check that reads the committed party-line records' `position.note` and asserts
its geometric claims against the committed footprint and block face — at minimum the anchored
wall — fails when the template is made to name the wrong wall (a self-test that fires when
broken, as the neighbouring gates do), and runs in `tools/check.sh`.

**Links:** T-0208 · T-0189 · `tools/generate_block_infill.py` `FRONTAGE_NOTE` /
`place_frontage` · `tools/measure_street_line.py`.
