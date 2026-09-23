---
id: T-0593
title: A documented 'large Dwelling-House' stands on a 5.36 x 6.38 m D3 count-unit, and the block's family mix was dealt before the address resolved
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 823
claimed_by: run 9/4/2026, 5:41:21 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T23:40:46.407Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33926179612
---

Four legible printings of G. Spring's For-Sale notice say "There is on said lot a large
**Dwelling-House**". T-0423 seated that address on the roof standing on lot 7 of block 16 —
`recon_1835_blk_south_water_dearborn_d3_03` — and that roof is a **5.36 x 6.38 m one-room
frame cottage**, dealt to the D3 family by the 665-roof programme long before the address
resolved to anything. The card now carries the notice's own word LARGE beside a small house.

T-0423 declined to repair it, on purpose and stated: the fabric under a documented address is
not itself documented (that is L216's whole argument), and re-dealing a block's family mix is
a second demonstration with a bake behind it. This is that demonstration.

**The question is which way the mismatch should be resolved, and there are three answers.**
(1) Re-deal lot 7's roof to a family whose footprint band answers to "large" — which changes
the block's scheduled mix and has to be reconciled through `tools/reconcile_665.py` so the
block's count and the town census stay balanced, and re-baked. (2) Leave the fabric and let
the seam show, on the argument that a documented adjective about an undocumented building is
evidence about the LOT and not about the massing. (3) Rule that an address may re-deal the
family it lands on, as a general rule rather than a one-off, and write it into
`docs/LOT-ADDRESS.md` — which matters because a second lot-and-block address would then
inherit it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- One of the three is chosen and the reasoning is written where the next address will read it.
- If the roof is re-dealt: `tools/reconcile_665.py` re-derives, the block's headroom and the
  town census both balance, `./tools/bake.sh --only` regenerates the mesh in the same commit
  (`validate.py --stale` hard-fails otherwise), and `tools/publish.sh` mirrors it.
- The seating's grade does not move either way. What is documented is the address; the fabric
  under it stays at the bottom tier whatever family it is dealt.
- `docs/LIBERTIES.md` L216 is not edited — it is append-only — so a changed answer is a new
  entry that says what it supersedes.

**Links:** T-0423 (the seating) · `docs/LOT-ADDRESS.md` · **L216** · **L92** ·
`tools/reconcile_665.py` · `data/reconstruction/1835_665_roof_programme.json` ·
T-0592 (the well, the other half of the same notice).
