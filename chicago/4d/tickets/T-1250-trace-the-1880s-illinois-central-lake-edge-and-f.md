---
id: T-1250
title: Trace the 1880s Illinois Central lake edge and fill shore_1880s_ic_edge from a sourced period sheet
state: open
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0473
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Trace the 1880s Illinois Central lake edge and fill shore_1880s_ic_edge from a sourced period sheet.

Piece 2 of 4 of **T-0473 — Create an 1880s South Side terrain and urban-ground epoch**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Settled upstream by T-1249, and binding here:** the state addresses **1 July 1888**
(`data/terrain/1880s_scene_date_constraints.json`). Trace the edge that date asks for.

1. Identify a **period sheet** that draws the lake edge, the Illinois Central corridor and the
   post-fire fill on the South Side, commit it as a source, and georeference it the way
   `rees_rucker_1849` was (GCP file, fitted affine, stated RMS). **No sheet has been identified
   yet** — that search is part of this ticket.
2. `shore_1880s_ic_edge` gets its own `geometry`, with `dated_lines` naming the sheet and the
   feature. It may not alias `shore_1835_harbor_cut` or `shore_1812_pre_cut`; a sheet of the
   wrong date **bounds** the line and does not become it, the same rule the 1849 lower bound
   already runs under.
3. **Rule on the 1852 trestle claim.** The epoch's placeholder note used to assert that "the
   Illinois Central trestle line already fixed the shore in 1852" and nothing in this corpus says
   so. T-1249 removed the sentence without deciding it. Either source it or record the refusal.
4. `tools/check_shoreline_states.py` extends to cover the new active geometry, and the 1812/1835
   separation assertions still fire.

**Retrieval notes (measured 2026-09-17, T-1249):** LOC *item* endpoints answer 200 but rate-limit
to 403 under a burst — `curl --retry 4 --retry-delay 15` recovered every time; LOC *search* with
`fo=json` answered 403 outright, so reach HABS and map records by item id. And
`www.encyclopedia.chicagohistory.org` did not resolve from the runner at all.
