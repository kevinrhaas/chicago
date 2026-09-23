---
id: T-0039
title: Signboards on the businesses that attest one
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: K5
parent: T-0003
opened: 2026-08-17
closed: 2026-08-18
pr: 237
claimed_by: run 8/18/2026, 2:44:14 AM CT
blocked_on: null
needs_bake: false
---

Signboards on the businesses that attest one.

Piece 2 of 4 of **T-0003 — Town furniture: fences, signboards, wagons, porches, docks**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance (stated 2026-08-18, before working):** a signboard hangs on every named business
frontage the rule selects, drawn by the renderer from a GENERATED record that `tools/check.sh`
re-derives byte for byte; the Wolf Point Tavern's one attested board is not duplicated; no board
carries lettering, an image or a trade device (L25); every vertex is graded `reconstructed` and
the invention is claimed in `docs/LIBERTIES.md`; and the demonstration is that a board reaches
the screen from the street at both viewports, asserted in `tools/smoke_renderer.mjs` rather than
described.

**Read strictly, "the businesses that attest one" is a job already finished** — exactly one
record in this dataset carries `form.sign`, and it has a board. The reading taken instead is
AGENTS.md § RECONSTRUCTED IS A TIER's: build the boards at the tier that honestly carries them,
name what bounds the invention, and record it. See `docs/STATUS.md` and L130.
