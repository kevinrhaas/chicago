---
id: T-1229
title: The dated plural resident role schema, the generated 1835 compatibility view, and the gates that refuse an undated or later role in it
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1145
opened: 2026-09-17
closed: 2026-09-17
pr: 1387
claimed_by: run 9/17/2026, 3:38:35 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T10:06:41.845Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35200021551
---

The dated plural resident role schema, the generated 1835 compatibility view, and the gates that refuse an undated or later role in it.

Piece 1 of 3 of **T-1145 — Replace the one-occupation resident field with dated plural roles and migrate every matched trade, profession and civic office without back-projecting later evidence**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (parent clauses 1, 2, 4 and the resident-card half of 6)

1. `data/residents/index.json` declares the role vocabulary — `role_kinds`
   (`trade`, `profession`, `office`, `employment`, `business_interest`) and
   `role_date_precision` — and every person record carries `roles[]`: a controlled
   role from the manifest's occupation vocabulary, the source's own wording, a kind,
   `from`/`to` (or a point date) with a precision, a confidence, the source ids and,
   where the source record offers one, the claim/entry id. An unknown date stays
   unknown; it is never widened to the scene date.

2. `roles[]` is canonical and the singular `occupation` is a GENERATED compatibility
   view of the roles that actually cover 1835-07-01. Where two roles cover the day,
   both stay in `roles[]` and `occupation.roles_at_scene_date` names both — the
   singular field can no longer erase the second.

3. `tools/derive_resident_roles.py --write|--check|--self-test` builds `roles[]` from
   the evidence the card already carries: the `occupation` block (dated by the
   `describes_date` of the sources it cites) and T-0693's `later_occupation` pointer
   (dated by its `describes_date`). Its `--check` re-derives and refuses drift.

4. T-0991 is resolved for the six trades `tools/audit_scene_window_trades.py` still
   reports: each is retained as a DATED PRE-SCENE ROLE carrying the printing it rests
   on, and its claim to be an attested 1835 occupation is withdrawn. The audit's
   standing population falls to zero, and the ledger's verdict and note travel onto
   the role so nothing is lost.

5. `tools/validate.py` gates the shape: a role that loses its source or its date, a
   role outside the controlled vocabulary or the kind vocabulary, and — the clause
   this ticket exists for — an undated or non-covering role standing in the 1835
   compatibility field. `tools/check.sh` runs the generator's `--check` and
   `--self-test`.

**Not this ticket:** the external structured evidence (gazetteer, 1839 directory and
civic register, 1843/1844 identity master), the role's place and employer, and the
migration table are T-1254; the people view's dated timeline is T-1255.

**Stop condition:** no card-local trade or later trade is held by a field that can
only say one thing, and the 1835 field cannot carry a role that does not reach 1835.

