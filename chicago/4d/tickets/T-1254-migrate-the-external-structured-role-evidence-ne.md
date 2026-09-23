---
id: T-1254
title: Migrate the external structured role evidence — newspaper gazetteer, 1839 directory and civic register, 1843/1844 identity master — with each role's stated place and employer, and publish the migration table
state: open
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1145
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Migrate the external structured role evidence — newspaper gazetteer, 1839 directory and civic register, 1843/1844 identity master — with each role's stated place and employer, and publish the migration table.

Piece 2 of 3 of **T-1145 — Replace the one-occupation resident field with dated plural roles and migrate every matched trade, profession and civic office without back-projecting later evidence**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Found by T-1229, 2026-09-17 — four scene-date trades cite a corroborating volume the
person does not.** `tools/validate.py`'s new role gate was first written to require every
source of a scene-date role to appear in the person's own `sources[]`, and it caught
`cohen_peter` (chicago_democrat_1833_1835), `couch_ira` (chicagology_prefire021),
`murphy_john` (drloih_hotels) and `walters_william` (drloih_wolf_point). Each also cites a
listed source, so none of the four is floating and the shipped gate — at least one source
in common — passes them. But a volume good enough to be cited for a man's trade and absent
from the list his grade stands on is worth a ruling, and this ticket is where the external
evidence those four volumes belong to is read. Rule it when you reach them: either the
source joins the person's list, or the role says why a corroborator does not.
