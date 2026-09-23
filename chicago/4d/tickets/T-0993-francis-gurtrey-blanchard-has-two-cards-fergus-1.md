---
id: T-0993
title: Francis Gurtrey Blanchard has two cards: Fergus 1843 prints the man T-0990 ruled on, and 'Gantry Blanchard' is very likely the same person
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-10
pr: 1084
claimed_by: run 9/10/2026, 5:31:11 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T20:54:33.293Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34466140871
---

Francis Gurtrey Blanchard has two cards: Fergus 1843 prints the man T-0990 ruled on, and 'Gantry Blanchard' is very likely the same person.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**FOUND BY T-0990**, ruling cohort A of the land-sale proposals. The residents layer holds
two Blanchards that on the directories' own printing are one man:

- `blanchard_f_gantry` — **F Gantry Blanchard**. Fergus 1843: *"Blanchard, Francis Gurtrey,
  capitalist, res 45 Wells [died, Brooklyn, N.Y., 1872.]"*; Fergus 1839: *"Blanchard,
  Francis G., real estate dealer, Lake street"*; Norris 1844: *"Blanchard, Francis G.
  residence Wells st"*.
- `blanchard_gantry` — **Gantry Blanchard**, a card whose forename is the OTHER man's middle
  name.

The land register prints four spellings of the surname — `BLANCHARD F G` (2 rows),
`BLANCHARD F G AS` (1), `BLANCHARD FRANCIS G` (1) and `BLANCHARD GURTREY` (6) — and if the
two cards are one man, all ten rows are his. T-0990 ruled only the first three, against
`blanchard_f_gantry`, and said in the ruling that it was not deciding this.

**Why this one is not T-0844's kind.** T-0844's six clusters are the ones the evidence does
not decide. This one the evidence may well decide: *Francis Gurtrey* is printed whole, in
one line, by the town's own 1843 directory. What the run must check is whether
`blanchard_gantry`'s evidence is the same evidence read a second time, or a genuinely
separate reading — and `data/residents/card_merge_rulings.json` is where the answer goes.

**Acceptance.** Either the two cards are merged under the card-merge rule with the reasoning
on the ruling, or the ticket records why they must stand apart; and whichever way it goes,
the six `BLANCHARD GURTREY` rows get a ruling in
`data/research/land_sales/resident_rulings.json` under this ticket's number.

---

## CLOSED ON THE EVIDENCE, 2026-09-10 — the work landed under another ticket's number

This ticket was still `claimed` on `dev` by a run that ended without closing it, and its row
stood third in QUEUE.md, which is the row a three-slice cold fill hands to slice 3. Both
halves of the acceptance are already on `dev`. Nothing was re-decided here; each clause was
checked against the tree and is recorded below with where it landed.

**It landed in commit `0e27b87a0` — *"T-0996: the land-sale ruling layer gains `named`, and
BLANCHARD GURTREY reaches its card"*, PR #1066.** `git log --diff-filter=A` on the merged
card and `git log -S'"ruling": "named"'` on the ruling file both name that one commit.

**Clause 1 — the two cards are merged, with the reasoning on the ruling.**
`data/residents/merged/hh_blanchard_gantry.json` carries the fold: `blanchard_gantry` into
`blanchard_f_gantry`, household `hh_blanchard_f_gantry`, **rule C8**, cluster `blanchard`,
ticket `T-0993`, on 2026-09-10, with the superseded record kept whole beneath it. The
reasoning is in `data/residents/card_merge_rulings.json`; `data/residents/index.json`
redirects the id, and `data/research/residents/town_card_candidates.json` records the
cluster under `landed` rather than proposing it again.

**Clause 2 — the six `BLANCHARD GURTREY` rows are ruled under this ticket's number.**
`data/research/land_sales/resident_rulings.json` holds `BLANCHARD GURTREY` →
`blanchard_f_gantry`, `"ruling": "named"`, `"ticket": "T-0993"`, ruled 2026-09-10 against
six sources. The three spellings T-0990 had already ruled stand beside it as `upheld`. That
`named` kind is what T-0996 added so the ruling could exist at all: the forename rule
structurally cannot reach a man's middle name printed where his forename belongs, and the
gate had been calling a ruling on it *"a ruling on nothing"*.

**The rows reach the card.** `data/residents/households/hh_blanchard_f_gantry.json` now
prints all ten register rows as one person — `ls0073`–`ls0081` and `ls0715`, 1833-10-22 to
1835-12-15, one federal entry plus nine parcels of the school section, 163.69 acres stated,
$920.00 — with the register's own Residence column still reading unknown, so the purchases
place nobody.

**Why the ticket outlived its work.** Two slices reached the same fold independently on the
morning of 2026-09-10; the collision is described in #1066's own body (*"at the moment I
claimed, T-0993 carried no remote branch and no PR"*). The owner ruled *"land 1066 instead
of 1065"*, PR #1065 was closed as superseded, and its branch
`steward/t-0993-blanchard-two-cards` — real work, but work `dev` already carries by another
route — is deleted with this closure so no later run mistakes it for a live claim. #1066
closed T-0996 and left T-0993 claimed, which is the whole residue this PR clears.
