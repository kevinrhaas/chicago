---
id: T-0869
title: Clark, Filer & Co. advertise a warehouse five doors east of a corner the plat does not have: is the Democrat's 'Randolph st.' a mis-set cross street, or a firm naming a corner it did not stand on?
state: done
epic: PAPERS
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-11
pr: 1154
claimed_by: run 9/11/2026, 5:31:03 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T23:16:05.276Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34654072147
---

Clark, Filer & Co. advertise *"their ware house on South water St. five doors east of the
corner of Randolph st."* — the Chicago Democrat, 1834-06-11, 1834-06-18 and 1834-07-02.

**T-0771 settled why the reader refuses it, and left open what the ad means.** That ticket
closed on the finding that Randolph Street and South Water Street are both east-west lines
of the Original Town, run parallel for their whole length, and never meet on the committed
plat — so `compile_register.streets_cross` now refuses the pairing, and the store keeps the
`street_only` reading it already had. That is the right register answer and it is not a
reading of the page. **Something on that page is wrong, and nobody has said which thing.**

Measured on the committed centrelines (`data/streets/1835.json`, `path_local_enu_m`):
Randolph runs at y ≈ -250 to -260 and South Water from (100, -101) to (805, 4), with Lake
between them at y ≈ -110. Segment intersection over the three finds no crossing in any
pair. The test is not over-strict — South Water and Clark share the point `[576, 9]` exactly
and count as a T-junction.

**Two readings, and the sources do not obviously decide between them:**

1. **The cross street is mis-set.** One printing reads `"Rando!ph"`, which is a compositor's
   hand slipping, and a slip that produced the wrong street name entirely is the same class
   of error. Lake Street is the parallel line one block south of South Water and Randolph is
   two; a warehouse "five doors east of the corner of" a street that DOES cross South Water
   would place cleanly. Naming which street was meant is a claim about ink, not about
   geometry, so it needs the column.
2. **The firm named a corner it did not stand on.** An 1834 advertisement giving a rough
   bearing to a landmark its readers knew is not the same as a surveyed address, and the
   town holds other printings that gesture rather than locate.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. The three printings are re-read from the column images, and what each actually sets for
   the cross street is written down — including whether `"Rando!ph"` is the damaged one.
2. A ruling that says which of the two readings the evidence supports, or states plainly
   that it supports neither and the address is unreadable. **A guess dressed as a reading
   is worse than the refusal that stands today.**
3. If the ruling names a different cross street, it lands as a reading of the source with
   its quote and its `where`, and the ordinal is re-run against it — it does NOT go in as a
   correction to the transcription.
4. If the ruling is that the ad gestures rather than locates, that is recorded on the
   business record, so the next pass does not re-open the same question.
5. Either way the refusal in the register is left true: nothing here may place the warehouse
   on a corner the plat does not have.

**Found by:** PR #966 (which closed T-0771 and named the question without deciding it) and
PR #968, a rival branch that reached the opposite outcome — it read the same torn
transcription, restored the sentence, and placed the warehouse off the Randolph corner,
because it had no test asking whether the two streets meet. Two independent runs reaching
opposite answers on one sentence is the reason this is worth a ticket of its own.
