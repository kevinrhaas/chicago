---
id: T-0034
title: Raise the bloom, which has no bar left to raise it to
state: done
epic: FLORA
requested_by: loop
seen: false
effort: M
legacy_id: R-W4c(b2)
parent: null
opened: 2026-08-17
closed: 2026-08-27
pr: 390
claimed_by: run 8/26/2026, 11:27:08 PM CT
blocked_on: null
needs_bake: false
---

"Raise the bloom" has no bar: the 4–6 % target is unsourced and unreproducible, and
density_per_ha is sourced data. Routes in blocked_on and § R-W4c(b1) (~1424 area).


---
**OWNER RULING, 2026-08-17: "I think you can adjust that without source."** The bloom
density may be tuned as a **reconstructed** value — bounded by the July-prairie references
already committed, recorded in `docs/LIBERTIES.md`, never promoted to inferred or attested
(AGENTS.md § RECONSTRUCTED IS A TIER). The implementing run picks the bound, states it, and
adjusts `density_per_ha` scaling or the draw as a declared liberty. His second observation
in the same message — flowers growing out of the ground on approach — is **T-0035**.

---
**DONE 2026-08-27. The bound taken is the RECORD ITSELF, and the ceiling that clipped it is the
lattice.** Full write-up in ROADMAP § R-W4c(b2) and STATUS; `node tools/measure_bloom_headroom.mjs`
(new, `--assert`) re-derives every figure below.

- **The bar that governs the bloom is `forbShareOf`'s clamp**: one plant per lattice slot, four
  slots to a 3.4 m cell, **0.346 forbs per m²**. Six of ten forb layers were already ON it, so a
  raise applied to their `density_per_ha` draws nothing — the K55 failure, exactly.
- **Nothing had to be invented.** Every abundance in `data/flora` is a range and the renderer was
  reading its midpoint, which no source states. The forb stratum is dealt off the recorded **top**
  now: mesic prairie **0.2800 → 0.4080 /m²** asked, share **0.809 → 1.000**; wet prairie
  **0.798 → 1.000**; sand prairie **0.210 → 0.329**; the other seven unmoved. Declared **L182**,
  reconstructed tier, bounded by the records — no species denser than its own record's larger
  figure. The species lottery still runs on the midpoints, so the mix did not move.
- **The records ask for 18 % more bloom than the lattice can draw** (0.408 against 0.346). That
  overflow is ROADMAP **K58**, not this ticket.
- **Visible:** `prairie_west` **206 forbs / 1,617 heads → 256 / 1,968**, +8,191 sward triangles;
  `prairie_south` 125 / 949 → 155 / 1,122. **And it is the last raise either prairie can take** —
  both read 1.000 with no headroom.
- **No ceiling constant was raised.** `TUNE.forb.cell`, `TUNE.forb.perCell` and `TUNE.cap.head` are
  untouched.
- **Opened, not caused:** **T-0208** (`flora-head-spike` and `flora-head-dome` stand at 820/820 and
  truncate silently, before this raise as well as after) and **T-0209** (the head ring reaches
  23.65 m against the sward's 175 m, so bloom covers **1.8 %** of the ground the sward covers — the
  real answer to "raise the bloom" is a distance, not a density).
