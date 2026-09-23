---
id: T-0417
title: Harmon, Loomis & Co. spends its South Water street face, and the 24 street-face adoptions reach the structure records
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0387
opened: 2026-08-29
closed: 2026-08-29
pr: 561
claimed_by: run 8/29/2026, 2:31:32 PM CT
blocked_on: null
needs_bake: false
---

Harmon, Loomis & Co. spends its South Water street face, and the 24 street-face adoptions reach the structure records.

Piece 1 of 2 of **T-0387 — The four storefronts the American puts on a street and nothing narrower: Harmon Loomis, Wm. Sabine, John Dave and the Dearborn Street wine store**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**The demonstration.** Every one of the 24 adoptions in
`data/research/newspapers/street_face_adoptions.json` reaches the structure record it
names, so a visitor who opens one of those anonymous roofs is told which documented
business the register seated on that face — `business_harmon_loomis_co` on
`recon_1835_blk_south_water_clark_d5_01` among them, which is this ticket's quarter of
the parent. Today the table allocates and nothing spends it: `docs/STREET-FACE-ADOPTION.md`
§ *How to spend it* says so in as many words, and the 24 roofs still card as anonymous
count-units.

- **Derived, never authored.** The `occupants` block is built in
  `tools/inferred_occupancy.py` — the ledger the anonymous-infill generators already read
  — and handed to whichever generator owns the roof, so `generate_block_infill.py --check`
  re-derives it byte for byte. No generated record is hand-edited.
- **The four limits of `docs/STREET-FACE-ADOPTION.md` are re-asserted where the block is
  built, not trusted:** no lot is claimed, the roof's own phase stays `reconstructed`,
  which roof on the face is an allocation rather than a reading, and the order on a face
  is not a claim. Each refusal has a self-test case and `tools/check.sh` runs them.
- **The occupants claim is graded `reconstructed`,** because the invented part is the
  whole of the placement. The business, its trade and its street are documented and the
  note cites the claims that carry them; that THIS roof held it is L212 and nothing else.
- **A collision fails loudly.** A roof the inferred-household programme already seats and
  an adoption both claiming one structure raises rather than overwriting.
- **No bake.** `generators/mesh_inputs.py` hashes archetype, phase and resolved params;
  an occupants block moves no vertex and stales no mesh.
