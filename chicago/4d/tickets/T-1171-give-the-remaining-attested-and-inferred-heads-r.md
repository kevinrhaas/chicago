---
id: T-1171
title: Give the remaining attested and inferred heads reconstructed families from the household model: wives, children, servants and apprentices drawn by the head's age, trade and household type, seeded, named from the pools, every member marked reconstructed
state: blocked-tech
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: 1476
claimed_by: run 9/20/2026, 3:23:50 PM CT
blocked_on: T-1179's convergence must re-house T-1174's 856 and T-1347's 308 women and children into the 310 married houses the household model drew; until it does, the order book has no woman left in their cells and this stage may draw nobody. The re-cut's remaining 227 are men aged 20+ in family households, which the kin core cannot draw (child age is capped at head_low-20) — they are T-1183/T-1173's hands and T-1175's boarders, adjudicated in the ticket.
needs_bake: false
closed_at: null
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35535214426
---

After T-1170, most of the 1,263 heads still stand alone — a letter-list name with a
sex and an age band and nothing else. The owner: *"make sure that family compositions included
children are complete."* Stage `families_model` of T-1167: the household model
(T-1163) is applied to every head that has no source-named family, deterministically.

**Rules:** the head's bucket (age band, trade, division, presence) → household type drawn from
the model's shares; married → a wife (age from the spacing rule, a pool forename, the head's
surname), children by marriage duration and the spacing rule (none born after 1835-07-01), a
servant/domestic where the type has one, an apprentice/journeyman where the trade's shop
household has one (agreed with T-1183); single → alone, or boarding (the type says which,
and T-1175 seats him). `presence` of members follows the head's. Every member: `grade:
reconstructed`, `name_basis`, `basis` (the model row), `seed`, `replaceable_by` ("a source naming
this head's family").

**Order-book discipline:** the tool fills the order book's person buckets (sex × age × division)
as it draws and refuses to overfill one — so the drawn town matches the population model in the
aggregate, not just per household.

**Acceptance:**

- Every head has a household type and the members it implies; the resulting person count,
  sex ratio (target ~147 men per 100 women aged 20+, from 1840, corrected by the model), age
  pyramid and household-size distribution printed against the model, all within the model's
  brackets; the order book buckets read filled to their `to_reconstruct` and not beyond.
- Deterministic: two builds are byte-identical; `--check` in `check.sh`.
- LIBERTIES entry for the whole reconstructed population, `Scope:` counted.
- Visible: the People view's reconstructed filter shows them; the household card shows the family
  with each member's tier and the rule that drew them; the "Reconstructing the town" card's
  person bars move.

**Stop condition:** the town's households look like the model's town in every printed table.

**Links:** T-1167 · T-1163 · T-1161 · T-1166 · T-1170.


---

## REOPENED 2026-09-20 by T-1463, for 227 persons — measured, not assumed

**The dates are the finding.** This ticket closed **2026-09-18** on PR #1476 having drawn
124 of 556. T-1386's presence rulings landed **2026-09-19**, the day after, and put 827
people into the town of 1 July 1835 who had been counted `uncertain`. Every quota this
stage worked to was therefore cut against a town that did not yet hold them, and the 432
it was still owed on 2026-09-20 was an unknown mixture of real work and that lag.

T-1463 summed the rulings into the order book's `known` and measured the split:

| leg | owed before the re-cut | owed after | verdict |
|---|---:|---:|---|
| households | 58 | **0** | DISCHARGED — the quota was 182 against 124 drawn; the re-cut takes it to the drawn figure |
| persons | 374 | **227** | part artifact, part real |

So 205 of the 432 was the staleness and **227 persons are genuinely owed**. That is why
this reopens rather than closing with a note: the answer was measured, and half of it is
work. T-1174 (856/856) and T-1347 (308/308) closed exact on the same counter, which is
what made 432 worth adjudicating rather than explaining away.

**What the re-taker is owed, and what they are not.** 227 persons in the `T-1171` person
buckets of `data/reconstruction/1835_reconstruction_order_book.json`; no households. And
the person buckets this stage already overdrew are REFUSED rather than re-cut — they are
named in the book's `recut_refusals` with both numbers, held at what was drawn. Nobody
this stage has already drawn is un-drawn (the owner's ruling of 2026-09-20, T-1459).

---

## 2026-09-20 — the staleness is fixed, and the 227 is adjudicated

**What was wrong, and it was the same fault T-1463 found one layer up.** This stage's
first refusal reads `present_on_scene_date` OFF THE CARD. T-1386 adjudicated the 827
attested and inferred people the layer had left on an unruled `uncertain` and wrote its 820
household rulings to `data/reconstruction/1835_presence_rulings.json` — a DERIVED sidecar
the card does not carry. The order book reads that file (`population_ruled_in`, summed into
`known` by T-1463); so do the town census and the population profile. This stage did not.
So while the book counted a town of 2,267, this stage measured itself against one of 1,140
and refused 822 households the project had already ruled were in it.

| | before | after |
|---|---:|---:|
| heads eligible for a family | 89 | **429** |
| the town this stage measures against | 1,140 | **2,267** |
| widest gap, drawn household sizes against 1840 | 0.0584 | **0.0274** |
| people this stage drew | 300 | 300 |
| heads carrying a household type | 89 | **119** |

**What it bought, measured.** Not new people — the book has none left to give here (see
below) — but thirty more of the town's own named men are now drawn `solitary`, and
`seat_lodgers_1835.py` seats THOSE men in beds it had been minting strangers for. L252's
invention falls from 75 minted against 17 seated to **47 against 47**: twenty-eight invented
people gone, twenty-eight real ones asleep in their place, the same 94 of 135
ordinary-night beds filled.

**A second rule, and it closes a hole rather than a gap.** A married house the order book
has no woman left for is now refused WHOLE. It used to keep its children — a cottage of
infants with no mother, reading as evidence of a family nobody drew.

**THE 227 IS NOT THIS STAGE'S TO DRAW, and here is the arithmetic.** The re-cut's 227 sit
in twelve buckets, every one of them `persons/male/{20_29,30_39,40_49,50_plus}/*/family/none`
— men aged twenty and over in family households. This stage draws the KIN CORE and nothing
else, and its own marriage rule caps a child at `head_low - 20` years (never above 19), so it
cannot put an adult man in a house that is not its head. An adult man in somebody else's
family house in 1835 is an apprentice, a journeyman, a clerk or a hired hand — priced by
T-1183's staffing model and seated by T-1173 — or a boarder, seated by T-1175. None of them
is kin.

**What IS still owed here, and what blocks it.** 310 married houses this stage drew stand
refused for want of a woman in their cell, 147 of them in
`persons/female/20_29/south/family/none`. The women exist: T-1174 drew 856 and T-1347 drew
308, exact on the counter — but as records of their own rather than into these heads'
houses. **Re-housing them is T-1179's convergence**, and until it runs there is no woman in
the book for house number 90 onwards. That is the one bullet this ticket now adds to its
acceptance:

- The 310 married houses the order book refuses a wife are seated once T-1179's convergence
  puts T-1174's and T-1347's women under the roofs the household model drew for them. No
  new woman is drawn for them; the ones already in the town are moved.

`--report` prints all of it, and the ticket stays open on that bullet alone.
