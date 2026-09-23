---
id: T-1310
title: The business record layer: data/businesses/ with a schema and tiered fields, tools/compile_businesses.py --build|--check|--self-test emitting one record per register business, and the register, the persons' works_at and the structures pointing at it by id
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1180
opened: 2026-09-18
closed: 2026-09-18
pr: 1447
claimed_by: run 9/18/2026, 3:02:00 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T09:05:52.306Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35321895713
---

The business record layer: data/businesses/ with a schema and tiered fields, tools/compile_businesses.py --build|--check|--self-test emitting one record per register business, and the register, the persons' works_at and the structures pointing at it by id.

Piece 1 of 2 of **T-1180 — An authored business layer: one record per business with tiered proprietors, partners, staff, dated primary and secondary locations and sources — compiled into the register beside the newspaper-derived firms, with the structure function vocabulary normalised**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Scope, stated before working.** The parent asks for three things: the record layer, the
structure `function` enumeration, and the building card reading from the record. The
enumeration is T-1311. The **card** is NOT here either, and the reason is not budget: T-1181 is
the Businesses view and is the parent's own visible surface, and a card that reads a layer no
gate has ever re-derived shows a reader a number nobody has checked. The layer and its gate come
first; T-1181 spends them.

**The id scheme, and the deviation from the parent.** The parent names `biz_<surname>_<trade>`.
Derived over the 196, that scheme collides 27 times — five firms land on `biz_montgomery_other`,
four on `biz_wentworth_tavern` — and every collision is a question about whether two printed
notices are one house, which is exactly the adjudication T-1182 owns. A compiler must not answer
it with an ordinal suffix that reads like a ruling. So the compiled records take
`biz_<register id minus its `business_` prefix>`: 1:1 with the printed notice they come from, no
collisions, and reversible. The schema still admits `biz_<surname>_<trade>` and `rcb_…` for the
authored and reconstructed records T-1182 and T-1184 mint by hand.

**Acceptance:**

- `data/businesses.schema.json` and 196 records under `data/businesses/` land, one per register
  business, every attribute carrying a tier.
- `tools/compile_businesses.py --build|--check|--self-test`: `--check` re-derives all 196 and
  refuses a hand edit; `--self-test` breaks each assertion and requires it to fire. Both in
  `check.sh`.
- Records resolve people: a proprietor or partner the register matched to a town resident carries
  that person's id, and the rest carry the read name with `person_id: null` and a basis saying so.
- Records carry locations: the register's `enrich_existing` / `new_building` / `street_only` /
  `unplaceable` actions become `locations[]` entries with kind, structure or street id, tier and
  `limit_reason`, so the 61 street-only and 62 unplaceable limits survive as data rather than prose.
- The register gains `business_record_id`; `compile_register.py` refuses a business the layer lacks.
- `works_at` on a household that names a structure a business sits in resolves to that business:
  the crosswalk is emitted and `validate.py` refuses a dangling business id.
- `docs/RESEARCH/business-layer.md` is the page; `docs/PROVENANCE.md` gains the record shape.

**Stop condition:** a register business is a record with a tier on every field, the register points
at it by id, and `check.sh` re-derives the lot.
