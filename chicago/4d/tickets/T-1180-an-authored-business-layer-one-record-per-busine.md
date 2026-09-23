---
id: T-1180
title: An authored business layer: one record per business with tiered proprietors, partners, staff, dated primary and secondary locations and sources — compiled into the register beside the newspaper-derived firms, with the structure function vocabulary normalised
state: open
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

There is no `data/businesses/`. The business layer is three derived files —
`data/research/newspapers/extracted/*.json` (claims) → `gazetteer.json` (196 businesses) →
`register_1835.json` (joined to the town, an `action` per firm) — and a business is visible in the
scene only as a structure whose `function`/`occupants` block names it (`data/structures.schema.json`).
The register row has NO staff field, no tier, no `sources[]`, no dates beyond first/last issue, and
a person's `works_at` is a bare structure id. The owner's ask — *"reconstruct the staff of the store
… as part of their resident profile … a complete list of data of attested and inferred … businesses
… and added to that reconstructed … businesses"* — has nowhere to be written. This ticket builds the
place. It reconstructs nothing.

**The record** — `data/businesses/<id>.json`, schema `data/businesses.schema.json`, tiers per
attribute in the shape T-1158 defines:

- `id` (`biz_<surname>_<trade>` for a sole trader, `biz_<firm_style>` for a firm, `rcb_…` for a
  reconstructed one), `name` (the firm style as printed, or the period form for a reconstruction),
  `type` (the census class of `trade_class_rulings.json` — the ONE taxonomy — plus a finer
  `trade` from `vocabulary.occupations`), `goods[]`.
- `proprietors[]`, `partners[]`, `staff[]` — each `{ person_id, role: proprietor|partner|clerk|
  journeyman|apprentice|servant|bar_keeper|hostler|printer|teacher|…, from, to, tier, basis,
  source_id }`. Roles agree with the household `relationships` vocabulary.
- `locations[]` — `{ kind: premises|yard|warehouse|office|stand|street_only|unplaceable, structure_id?,
  street_id?, face?, primary: bool, from, to, tier, basis, limit_reason? }` — the register's
  `anchor`/`action` folded in, so the 56/61/62 location limits survive as data.
- `dates` — `{ opened, closed, precision }` per tier; `evidence` (first/last printing) kept.
- `proprietor_community` and `customers[]` (the community vocabulary of T-1158/T-1177 — the
  Indian trade and the Black-owned businesses are identifiable on one field), `sources[]`,
  `claim_ids[]`, `exclusion` (the register's), `review_required`, `replaceable_by`.

**The compile.** `tools/compile_businesses.py --build|--check` emits one record per register
business (present at the scene date, plus excluded ones flagged) from the derived layer — no
hand edits to the 196 — and reads authored records from `data/businesses/authored/` (the
inferred-by-audit and reconstructed firms T-1182 and T-1184… will write). The
register gains `business_record_id`; `compile_register.py` refuses a business the layer lacks.
Persons' `works_at[]` entries gain `business_id`.

**Vocabulary repair, in the same commit:** the 109 free-string structure `function` values include
`blacksmith_shop` AND `blacksmith shop`, `store_residence` AND `store-residence`, two spellings of
the cooper/wheelwright shop. Enumerate `function` in the structure schema (the signage rule's
`public_trades` + `works_trades` + the dwelling/civic set), migrate by tool, refuse the rest.

**Acceptance:**

- Schema + validator + `compile_businesses.py` land; `--check` in `check.sh` with a mutation
  self-test; 196 records compile, counts printed by type, by action and by tier.
- `works_at[]` on every person that has one resolves to a business record AND a structure;
  `tools/validate.py` refuses a dangling id.
- The structure `function` enumeration lands with zero free strings left and the signage
  generator re-derives byte-for-byte.
- Visible: the building card's "Use" and "Keepers" lines now read from the business record
  (name, type, proprietors with tier), so a visitor sees the same firm on the roof and in the
  layer.
- `docs/PROVENANCE.md` gains the business record shape; `docs/RESEARCH/business-layer.md` is the
  page.

**Stop condition:** a business is a record with a tier on every field, and the register, the
persons and the structures all point at it by id.

**Links:** T-1158 · T-1147 · `data/research/newspapers/README.md` · `trade_class_rulings.json`
· `docs/STATUS.md` § T-0354/T-0416/T-0417 (what a street-only business gets).
