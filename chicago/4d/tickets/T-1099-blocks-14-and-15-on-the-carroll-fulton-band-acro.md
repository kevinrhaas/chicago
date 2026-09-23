---
id: T-1099
title: Blocks 14 and 15 on the Carroll-Fulton band across the North Branch, where no committed street line reaches
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1095
opened: 2026-09-12
closed: 2026-09-13
pr: 1228
claimed_by: run 9/12/2026, 10:25:01 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T15:26:05.693Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34735274376
---

Blocks 14 and 15 on the Carroll-Fulton band across the North Branch, where no committed street line reaches.

Piece 2 of 2 of **T-1095 — The West Division past Clinton (8-13, 22-27, 46-51) and 14-15 on the North Branch's west bank: still no committed street line reaches them**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** the collision is settled by a demonstration, not a preference — it is shown which of the
two possibilities holds, and the losing side is corrected in the file that carries it. Blocks 14 and 15 are
then each read from a box cut by a tool the gate re-runs, or refused in writing with the figure that would
change the answer. No numeral located by eye. Where a box's side is not a committed line, the rule standing
in for it is stated in the tool and in the memo, corroborated against control this repository already holds,
and graded no better than `inferred`.

---

**FOUND BY T-1098, 2026-09-13 — what is left, and one collision the next run must settle.** With the
West Division's eighteen read, fifty-six of Wright's fifty-eight blocks are in
`data/traces/thompson_block_numbering.json`. The two outstanding are 14 and 15. T-1098's
boustrophedon places the first of them: the Carroll-Fulton band runs 11 12 13 rising eastward and
does not stop at Canal Street, so 14 is the next block east of 13, across the North Branch.

**Why it is still refused.** No committed street line reaches that ground. The North Division's
north-south lines — `market_north` and its six neighbours — all stop between north +108 and +126 m,
a hundred metres short of the Carroll-Fulton band, and nothing carries Carroll or Fulton across the
North Branch; T-0446 recorded that modern Carroll Avenue does not survive inside the plat at all. So
there is no pair of flanks to cut a box from, and a numeral found without one is a numeral placed by
the reader.

**AND THE COLLISION, which is the real work here.** A numeral that reads as 14 stands on the sheet at
raster px 1464, 1697 (Wright 1834, commonwealth:js957744g) — local east +24.6, north +83.8. That
point lies INSIDE the box T-1088 cites for block 7 (`1376,1452,178,298`, the North Branch bank to
Market Street, Kinzie Street to the river), whose own numeral was read at `1436,1460,118,147`, two
hundred pixels north of it. Two block numerals cannot stand in one block. Either that column is two
blocks and not one — which would make T-1088's box too tall and its southern half block 14 — or one
of the two readings is wrong. Settling that is this ticket, and it is worth more than the numeral:
it is a test of the one box in the North Division tier whose south side is not a street but "the
southern endpoint of the flanking platted lines, where they stop at the river".


---

**Done, 2026-09-13 — PR #1228. Fifty-eight of fifty-eight.**

**The collision fell the first way: the column is two blocks, and T-1088's box was too tall.** Both readings
stand. T-1088's south rule takes *the southern endpoint of the flanking platted lines, taking the northern of
the two*; block 7 is the one block in that tier with a SINGLE flank, so there was no northern of the two and
the rule collapsed onto Market Street's endpoint — the one line in the tier that does not stop at the tier.
`market_north` ends at north **+46.35 m** at the bank in the forks where `franklin_north` beside it ends at
**+151.61 m**. The box ran **89 m** past block 7 and cited a crop with two block numerals in it. Block 7's
south is now Carroll continued east; its reading never moved.

**14** — the block between the two rivers and Market Street, box `1376,1624,177,126`, read at
`1458,1679,52,40`. **15** — the right triangle inside North Water Street at the forks, box
`1552,1628,178,126`, read at `1592,1652,46,32`. Both flanked by Market Street; the river side of each is
Market stepped one module (123.36 m), which is blocks 7, 22, 51 and 52's rule. The fourth side of both is
Carroll continued east along the bearing of its own committed path, 68 to 315 m past its committed end, and
it is not carried further east than that.

**Corroborated** by the street Wright draws between the tiers — faces at north +155.7 / +130.5 at east +40,
and +153.0 / about +120 east of Market, with Carroll continued landing at +135.5 and +134.5, inside the drawn
street at both longitudes. Read by eye, so stated and not gated. **Gated** instead: `read_wolf_point_numerals.py`
re-cuts both boxes, checks each read window lies inside its box, and asserts that neither numeral lies inside
the other's crop; `read_north_division_numerals.py`'s self-test now fires on Carroll; and 14 15 join the
Carroll–Fulton band's tail in the boustrophedon assertion, so they must continue the run 11 12 13 fixes.

The trace's refusal is marked spent. Its claim that the North Division's streets "stop between +108 and
+126 m, a hundred metres short of the band" is corrected with the measured endpoints — that error is what hid
block 14.
