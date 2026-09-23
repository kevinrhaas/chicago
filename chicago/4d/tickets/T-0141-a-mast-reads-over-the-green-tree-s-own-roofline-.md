---
id: T-0141
title: A mast reads over the Green Tree's own roofline, which its committed placement forbids
state: open
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0122
opened: 2026-08-22
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

A mast reads over the Green Tree's own roofline, which its committed placement forbids.

Piece 2 of 2 of **T-0122 — Masts behind the Green Tree: moored craft at the Wolf Point landings**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Measured 2026-08-22, while shipping T-0140** — this is the half of T-0122's acceptance that
the committed dataset forbids, not the half that needed more work.

T-0122 asked that a mast read *above/behind the inn's roofline* from the Green Tree's own
visitor stand, because that is what plate "11" draws. With the two schooners now moored at
the Wolf Point landings, the masts read **beside and beyond** the inn — above the roofline of
the west-bank cabins across the water — and **not above the Green Tree's own roof**. The
geometry says it cannot, and the arithmetic is short:

* the `green_tree` anchor stands at local **E −159.7, N −108.4**, 24 m west of the inn;
* the inn's ridge subtends about **10°** from there;
* a 14.5 m mast on a hull whose deck rides 1.1 m above the water subtends 10° only inside
  **~83 m** of the stand;
* the nearest water the committed heightfield gives on that bearing is **~157 m** out.

**The cause is a placement question the record already carries.** `green_tree_tavern`
`placement.position_note` records the residual: DRLOIH gives the corner as *"Lake and West
Water Streets"*, and West Water ran **along the west bank** while Canal lay a full block
further west — *"if the tavern actually stood on the riverbank street rather than on Canal,
it belongs about 145 m east of where this record puts it."* The plate's masts are evidence
on that side of the question. Moving a documented building is the owner's call, not the
loop's, and L152 already leans on the same open question for the rear ell.

**Acceptance:** either the Green Tree's placement is settled (with the check ROADMAP § S2e
names — the lot geometry on Wright 1834 or Hathaway 1834) and a mast then reads above its own
roofline from the `green_tree` anchor, or the plate's composition is recorded as
unreproducible at this placement with the measurement above written where the placement is.

**Links:** T-0122 (parent) · T-0140 (the piece that shipped) · L152 (the same open question) ·
`data/sidecars/1835/green_tree_tavern.json` `placement.position_note`.

## THE OWNER'S RULING, 2026-09-21: MOVE the Green Tree to Lake and West Water

Adopt DRLOIH's placement — about 145 m east of the committed position, at Lake and West
Water. The tavern comes forward to the bank, and the plate's composition is reproducible
from the visitor's own stand.

THE MOVE IS ARGUED FROM THE SOURCE, NOT FROM THE PICTURE'S FRAMING, and this is the whole
of how it must be written. DRLOIH states a location; that statement is the evidence, and it
is what the new placement cites. The mast over the roofline is the SYMPTOM that sent
somebody to look — it is not a reason to move a building, and a placement note that reads
'moved so the plate would work' would be this project fitting the town to a depiction.

WHAT THE OLD PLACEMENT WAS IS PART OF THE RECORD. The position_note keeps what put the
tavern a full block back, says that DRLOIH is preferred and why, and names the date of this
ruling. A committed building that moves without its previous reading surviving is a town
quietly rewriting itself, and the next person to find a source on the Green Tree needs to
see both readings to weigh a third.

CHECK WHAT ELSE STOOD ON THE OLD POSITION. 145 m is far enough to change what the tavern
neighbours, what lot it sits on and what the visitor sees from the stands around it. If the
move collides with anything already placed, T-0251's ruling of the same day governs:
attested placement displaces inferred, and the loser is re-seated on its own evidence before
it is withdrawn.
