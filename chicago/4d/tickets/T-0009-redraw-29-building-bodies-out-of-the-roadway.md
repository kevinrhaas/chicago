---
id: T-0009
title: Redraw 29 building bodies out of the roadway
state: done
epic: TOWN
requested_by: loop
seen: true
effort: M
legacy_id: K30(c)
parent: null
opened: 2026-08-17
closed: 2026-08-29
pr: 567
claimed_by: run 8/29/2026, 4:27:24 PM CT
blocked_on: null
needs_bake: true
---

29 buildings on eight streets are drawn standing in the roadway — K30(b) proved the cause
is the DRAWING (bodies grow north from the frontage corner instead of onto their own lot
side). The analysis is banked; this is the repair. Deep history: § K30(c) (~5910).

**Acceptance:** the 17 deep intrusions fall to ~0 by reflection onto the correct side;
no record's frontage moves; NEEDS THE BAKE for the placeholder meshes.

---

**REFUTED 2026-08-22 — ROADMAP § K30(d), and the test is a command:
`tools/measure_corridor_intrusion.py --anchors`.**

K30(b) read one flag — is the body drawn toward the street from the anchor? — and concluded
the anchor stands on the frontage. That flag is true of two opposite drawings, and the one
this dataset actually uses is the other one: the point is set back by the footprint's own
depth so the street-facing **face** lands on the frontage. `--anchors` separates them by
measuring which face the anchor coincides with, and it finds the **back corner on all 17**
records in the deep mode and the kerb face on **none**. The three records that DO carry the
point at the kerb are `tremont_house_1`, `exchange_coffee_house` and `western_hotel` — the
three K30(b) itself named as already correct and ruined by reflection.

So the repair this ticket asks for would move twelve documented buildings a full depth
BEHIND the frontage their own committed control was offset to. The lap is not the drawing:
`data/streets/1835.json` says of `south_water` that east of Franklin the line *"is shifted
into the dry half of the platted riverfront corridor"*, and that shift measures 4.3–8.8 m
south of the intersection centres the ten placements were derived from.

Blocked on the owner because every way out changes something with a source behind it.

---

## THE OWNER'S RULING, 2026-08-29 — OPTION 2

Asked which of the three the South Water corridor is, the owner chose:

> **Derive the platted corridor from the street CONTROL rather than from the drawn line.**

**Nothing in the scene moves.** The ten buildings stay where they stand, and the twelve
documented buildings keep the frontage their own control was offset to — which is what
K30(d) said the evidence supports, since none of the 17 deep records has its point on the
kerb face and the ticket's original premise (bodies drawn across their frontage) is refuted.

**What changes is what the intrusion table measures against.** The committed
`south_water` centreline was deliberately shifted 4.3–8.8 m south of the control to keep
the street on dry ground; that shift is a drawing decision about where a street can be
drawn, not a claim about where the platted corridor was. Measuring building bodies against
the drawn line therefore reported an intrusion into a corridor the plat does not put there.
The corridor is re-derived from the control, and the table is re-run against it.

**Say what this does NOT settle**, so the next run does not over-read the ruling:

- It does not assert the north half of that reach was dry. Option 3's reading — that the
  drawn line is south of the control because the ground north of it was water — remains
  available as a description of the same facts and is not refuted here.
- It does not license moving the drawn centreline back onto the control. The street is
  drawn where it is for a stated reason and stays there.
- Any record whose intrusion survives re-derivation against the CONTROL is a real
  intrusion and still owed an answer.

**What this unblocks, which is why it was asked.** T-0365 measured that every platted
block still carrying headroom is gated on this ticket or on T-0183. With this answered,
`blk_south_water_franklin`, `blk_south_water_lasalle`, `blk_south_water_clark` and
`blk_south_water_dearborn` are workable — 20 roofs of headroom between them, and the
refusal T-0143 and T-0188 both made (a run may not be tightened against a line that may
move) is discharged: the line is not moving.

**Acceptance for the run that takes this:**

- The corridor is derived from the street control, the derivation is stated, and the
  intrusion table is re-run against it with before/after counts.
- Any intrusion that SURVIVES the re-derivation is listed and left open, not absorbed.
- Nothing in `data/streets/1835.json` moves; if a run finds it must move the drawn line to
  make this work, it stops and says so rather than moving it.
- The four blocks above are confirmed workable (or the reason one is not is recorded).

---

## DONE 2026-08-29 — THE CORRIDOR IS DERIVED FROM THE CONTROL, AND THE TABLE IS RE-RUN

Carried out under the owner's Option 2. Full reasoning in `docs/ROADMAP.md` § K30(e).

**Nothing in the scene moved.** No structure record, footprint, coordinate or confidence was
touched, and `data/streets/1835.json` is byte-identical.

**The derivation** is `plat_corridors.control_offsets()`: every committed control point in
`data/traces/street_control.json` is measured against the drawn centreline of each street it
names — cross-axis, at the control's own along-axis value. No street ids appear in the rule.

| verdict | streets | offset |
|---|---|---|
| `recentred` | `south_water` | **+8.58 m** |
| `centred` | `lake`, `market`, `randolph` | 0.00–0.01 m, under the centimetre a depth is quoted to |
| `disagree` | `canal` | three points spread **2.33 m** — left on the drawn line, filed as **T-0421** |
| `off_line` | `franklin` | `south_water_franklin` is beyond franklin's drawn span |
| `no_control` | 13 others | — |

`tools/measure_corridor_intrusion.py --control` prints it; `--drawn` re-runs every mode against
the pre-ruling corridor, so the before-and-after is two commands.

**Before → after.** 19 of 359 phases lap, both ways; 17 buildings, both ways; 5 in the deep mode,
both ways; centroid-in **5 → 4**; generated roofs lapping **0 → 0**. Four records moved:
`newberry_dole_warehouse` 12.10 m on `south_water` → 9.81 m on `franklin`; `hogan_store`
10.06 → **3.98 m**, centroid out; `lasalle_slough_crossing` (furniture) 11.39 on `south_water` →
3.17 on `lasalle`; `dearborn_street_drawbridge` **newly laps `south_water` by 7.13 m** — furniture,
a drawbridge in a street corridor is the bridge doing its job; `slough_log_bridge` clears.

**INTRUSIONS THAT SURVIVE, listed and left open, not absorbed:** `newberry_dole_warehouse` laps
`franklin` by **9.81 m** and still laps `south_water`; `hogan_store` is still in the deep mode at
**3.98 m**. Both are ratcheted in `tools/corridor_intrusion_baseline.json`. The three T-0195
refusals are on other streets and outlive their laps unchanged.

**Scope, and it is the ruling's own** — *"what changes is what the intrusion table measures
against"*. `plat_corridors.corridors()` still answers the DRAWN corridor by default and every
generator keeps asking it that, because a generator asks where a roof may stand relative to the
street a visitor walks. Swapping the default was tried and measured: five gates that read a
corridor edge against a block face or a frontage line went red, because the re-centred corridor
stands 8.58 m off block faces that do not move. Filed as **T-0419**.

**The four blocks are confirmed workable.** T-0143 and T-0188 refused to tighten a row against a
line that may move; the line is not moving, so the refusal is discharged and
`blk_south_water_franklin` (4), `blk_south_water_lasalle` (8), `blk_south_water_clark` (4) and
`blk_south_water_dearborn` (4) carry **20 roofs**. Filed as **T-0420**.
`blk_south_water_market` stays gated on T-0183, unchanged.
