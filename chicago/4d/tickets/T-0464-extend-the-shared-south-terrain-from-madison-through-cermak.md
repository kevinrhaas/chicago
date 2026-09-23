---
id: T-0464
title: Extend the shared south terrain from Madison through Cermak
state: done
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-01
closed: 2026-09-14
pr: 1257
claimed_by: run 9/13/2026, 10:21:08 AM CT
blocked_on: T-0219
needs_bake: true
closed_at: 2026-09-14T22:42:53.145Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34765142411
---

After T-0219 carries the current 1835 heightfield through Madison, extend the project’s durable geographic frame south far enough to contain the 1812 battle corridor and the Prairie Avenue district: at minimum through modern Cermak/22nd, with a measured buffer so terrain, shoreline and structures do not terminate inside the historical area.

Do not make this a generic flat rectangle. Re-derive the required local-ENU south bound from the project datum, verify whether the present E -320..+1700 width contains the South Branch and historic lakefront over the whole reach, and expand west/east only where evidence requires it. Preserve the current 2.5 m field resolution unless a measured performance/storage reason supports a documented change.

Acceptance: a baked terrain epoch can cover Madison-to-Cermak without out-of-bounds fallback; the exact ENU and modern-street bounds are documented; existing downtown terrain is unchanged within tolerance; and the new field is large enough for both the 1812 and 1880s scene tickets below.
---

**Raised by T-0436, 2026-09-13 — the corporate boundary reaches only to Jackson, and this
ticket goes past it.** The Town of Chicago's limits are now committed geometry
(`data/reconstruction/1835_corporation_limits.json`), resolved from the Trustees' own
survey walk of 7 November 1833. Its south leg is **Jackson Street**. Nothing drawn today
stands south of it, so the boundary is complete for the town as modelled — but this
ticket carries the field to Cermak, 22nd Street, and the moment a building stands down
there, whether the town's by-laws reached it is decided by the extension of **11 February
1835**, which is recorded and NOT resolved: the act's text has not been found in this
corpus, Andreas misprints its year, and Chicago Avenue and Twelfth Street are not
committed as centrelines. See `docs/RESEARCH/corporation_limits.md` § what is still open.
Answer that before this ticket ships a chimney south of Jackson, or the eighteen-inch gate
starts conforming buildings to a by-law that may never have bound them.


---

**ACCEPTANCE, STATED 2026-09-13 BEFORE WORKING, AND WHERE IT STANDS.**

1. A baked epoch covers Madison-to-Cermak with no out-of-bounds fallback — the
   HEIGHTFIELD reaches the street, not the apron. **MET.** N -3800.
2. The south bound is derived from the datum, with the buffer measured against
   the control's own uncertainty rather than rounded. **MET.** Two committed
   section corners (State & Madison N -525.27, State & Roosevelt N -2149.40) are
   the School Section's mile; Twenty-Second is the next mile line south at
   N -3758.74; -3800 clears it by 41.3 m, clears the surveyed-spacing reading
   (-3773.5) by 26.5 m, and clears the 16.95 m picking spread.
3. Existing downtown terrain unchanged. **MET, ASSERTED NOT CLAIMED** — the
   overlapping 373 x 809 sub-array is bit-identical to the pre-change bin.
4. E/W width verified against the traced South Branch and lake shore over the
   whole reach, widened only where evidence requires. **MET, AND IT REQUIRED
   NOTHING**: over the traced reach the South Branch spans local E -43..+339 and
   the lake shore E +314..+1459, both well inside -320..+1700; below Twelfth
   Street there is no trace to widen for. The question re-opens when T-0465 lands
   the trace.
5. Nothing south of the evidence graded better than conjectural. **MET** —
   `evidence_limit`, and the surface there is carried, not computed.

Also landed because the extension forced them: `southern_lake.beyond_the_trace`
(without it 355 x 1640 m of Lake Michigan came out as dry land);
`skirt_margin_m()` derived against the widest horizontal span, since north-south
is now the wider and the old east-west derivation would have brought T-0152's plan
displacement back; `south_sand_ridge` declared west to E +890; micro-relief stopped
at Madison Street (9.10 MB of master, 807 KiB of payload, for ground nothing walks
on); Heacock's house on Monroe finally standing on ground, which its own record
had asked for.

**PARKED ON `hold` IN PR #1257 — the field is done and gated, the town's response
to it is a second demonstration.** `tools/check.sh` is at 7 of 377 steps and every
one is a record that BANKS the heightfield box re-deriving against the new one:
the Kinzie Block reading, the corridor strip, the dooryard plantings,
`reconcile_665`, `compile_scene`'s sidecars, and the platted-block gate. The last
is the reason to stop rather than push through: `blk_washington_clark` stood off
the modelled ground and now stands ON it, so the roof schedule will deal to it —
new geometry, a structure bake and a measured before/after. Three banks were
re-run inside this PR already (`measure_planting_reach --update`,
`measure_far_timber --update`, `compile_liberties`).

NEXT RUN, in order: `reconcile_665.py`, the three re-derives, `compile_scene.py`,
then what `blk_washington_clark` gaining ground means for the schedule.
