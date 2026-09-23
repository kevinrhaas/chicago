---
id: T-1001
title: Two cards for one physician, and the fold that hid it: KIMBERLEY EDMUND S is upheld against 'Ed Kimberley' while the layer also holds Dr Edmund Stoughton Kimberly, whom namesake.py's exact surname fold never gathers
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-10
pr: 1079
claimed_by: run 9/10/2026, 1:33:32 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T19:02:37.172Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34509743375
---

Two cards for one physician, and the fold that hid it: KIMBERLEY EDMUND S is upheld against 'Ed Kimberley' while the layer also holds Dr Edmund Stoughton Kimberly, whom namesake.py's exact surname fold never gathers.

FOUND BY T-0990 COHORT B, which upheld the purchaser against the wrong-looking card and said so.

**The two cards.** `kimberley_ed`, "Ed Kimberley", is minted from a press reading — *E. S.
Kimberley*, the Chicago Democrat of 1 July 1835 — and the 1840 census, *Ed. Kimberley*. It holds
no trade and no street. `kimberly_edmund_s`, "Dr Edmund Stoughton Kimberly", is attested off
Andreas, the poll lists and a history of medicine at Chicago, printed *Kimberly, Dr. Edmund S.*
in Fergus 1839 and *Kimberly, Edmund Stoughten, physician, 101 Lake* in Fergus 1843, and sits in
a household with Peter Pruyne because the two opened a shop together. Same forename, same middle
initial, one letter of difference in the surname. They are very probably one man, and one of them
carries the land entry.

**The fold is why nothing caught it.** `tools/namesake.py` folds surnames EXACTLY, so Kimberley
and Kimberly are two surnames to it. `build_resident_crosswalk()` therefore reported `rivals[]`
empty on KIMBERLEY EDMUND S — no namesake — when the layer holds the closest namesake it could
have. **Cohort B is DEFINED by that field** (`rivals[]` empty, twenty-four proposals), so the
fault is load-bearing: an empty `rivals[]` means "no namesake of that spelling", not "no
namesake". The register itself prints KIMBERLEY IRA while the layer holds `kimberly_ira`, so the
same fold is in play at least twice on this one surname.

**Two questions, and they are separable.** Whether the cards merge is a card-merge ruling and
belongs with T-0844's clusters and T-0993's Blanchard pair. Whether `rivals[]` should be gathered
on a fold that admits a one-letter surname difference is a change to the mechanical rule, and it
would re-open cohort B's twenty-four — so it is measured before it is made: how many of the 431
purchaser spellings gain a rival under a looser fold, and does any RULED proposal change shape.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- the two Kimberl(e)y cards are ruled on in `data/residents/card_merge_rulings.json` — merged or
  held apart, with the reasoning and its sources, and no confidence raised to make it tidy;
- if they merge, the land entry KIMBERLEY EDMUND S carries to the surviving card and
  `resident_rulings.json` is amended to name it, with `read_land_sales.py --check` green;
- the fold question is ANSWERED WITH A COUNT, not an opinion: how many spellings gain a rival
  under a fold that admits one letter, and which ruled proposals would change;
- `bash tools/check.sh` green, and what moved itemised in `data/residents/README.md`.

