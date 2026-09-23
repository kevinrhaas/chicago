---
id: T-1002
title: Three duplicate-card pairs the candidate test cannot see, because each differs by ONE letter: Madore/Medore Beaubien, Clybourn/Clybourne Archibald, Russel/Russell E. Heacock
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-11
pr: 1112
claimed_by: run 9/11/2026, 1:45:45 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T07:31:48.944Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34570959296
---

Three duplicate-card pairs the candidate test cannot see, because each differs by ONE letter: Madore/Medore Beaubien, Clybourn/Clybourne Archibald, Russel/Russell E. Heacock.

**FOUND BY T-0961**, transcribing Moses and Kirkland's LIST OF ACTUAL SETTLERS AT CHICAGO,
PRIOR TO 1830 and ruling all thirty-six rows against `data/residents/`. Three of the twelve
merges landed on a card the layer holds TWICE, and in all three the second card is one
letter away from the first:

| the attested card | the thin civic-mint card | the letter |
|---|---|---|
| `beaubien_madore` — Madore Benjamin Beaubien, merchant, one of the five first trustees | `beaubien_medore_b` — Medore B Beaubien, `none_recorded` | a for e |
| `clybourne_archibald` — Archibald Clybourne, butcher, "came in 1823" out of Andreas | `clybourn_archibald` — Archibald Clybourn, `none_recorded` | a trailing e |
| `heacock_russel_e` — Russel E. Heacock, attorney, "who had come in 1827" | `heacock_russell_e` — Russell E Heacock, `none_recorded` | a doubled l |

**WHY THE EXISTING MACHINERY MISSED ALL THREE, WHICH IS THE POINT OF THE TICKET.** The
candidate clusters behind `data/residents/card_merge_rulings.json` are built by grouping on
the SURNAME AS A STRING. Clybourn and Clybourne are two strings; Heacock and Heacock are one
string but Russel and Russell are two forenames; Madore and Medore are two forenames. So none
of the three pairs ever reached the T-0839 pass, the T-0844 pass or the T-0993 pass — not
refused, not deferred, **never proposed**. The forty-one clusters that file holds are the
pairs the string test could see, and the file has no way to say how many it could not.

**The shape is the same in all three, and it is a shape and not a coincidence:** one
hand-authored card out of Andreas carrying a trade, an arrival and a source, and one card
minted by `tools/mint_civic_residents.py` off a poll list or the Chicago Democrat carrying a
name and `none_recorded`. That is a MINTING pass spelling a name the way its list spelled it,
beside a research pass spelling it the way Andreas did. T-0843 stopped the cause for exact
duplicates — a minting pass must consult the identity master before it writes a card — and an
identity master keyed on strings does not stop this one.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The three pairs RULED in `data/residents/card_merge_rulings.json`, each under a named rule,
  in that file's own shape and appended under `also_ruled_on` as T-0844 and T-0993 were. The
  evidence for each is already gathered and cited on the T-0961 merges in
  `data/research/books/crosswalk.json` — the arrival years, the trades and the trustee seat —
  so this ticket is the ruling and not the research.
- Whichever way each goes, `data/research/books/crosswalk.json`'s three `does_not_follow`
  notes stop saying "named, not ruled" and name the ruling instead.
- **AND THE CLASS, NOT ONLY THE THREE.** The candidate test runs again with a fuzzy key —
  edit distance 1 on the surname, and on the forename where the surname folds — and the
  pairs it newly proposes are listed. That list is the ticket's real yield: three were found
  by hand in one afternoon's reading of one table, and nothing says three is all there are.
  If the list is long, it is an EPIC and the queue's filing rule says so; if it is short,
  rule it here.
- `bash tools/check.sh` green. No bake: nothing here moves geometry.

**WHAT MUST NOT HAPPEN.** A fold is a card DELETION and the town's resident count moves by
it. Nothing here may be folded to tidy a duplicate away — the rule that decides it is the
same rule T-0839 wrote, and a pair the evidence does not decide STANDS, which is what
`D1`/`D4` are for.
