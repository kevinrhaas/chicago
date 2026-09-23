---
id: T-1163
title: The 1835 household and family model: household types, sizes, and the rules that give a head a wife, children, servants, boarders or a partner — from the 1840 composition, the attested 1835 families, the baptism register and the boarding-house evidence
state: withdrawn
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1293
needs_bake: false
closed_at: 2026-09-17T20:06:18.430Z
claimed_run: null
---

The owner, 2026-09-17: *"make sure that family compositions included children are complete …
including what I think are a fair number of missing women and children."* The known layer has
a mean household of 1.02 against 8.2 people per dwelling; the difference is families and
lodgers the sources name only as "and family". This ticket writes the RULES the reconstruction
bands will draw families with, so that every reconstructed wife and child is bounded by a
distribution a reader can inspect rather than by taste.

**Deliverable** — `data/reconstruction/1835_household_model.json`, built by
`tools/build_household_model_1835.py --build|--check|--self-test`:

1. **Household types** with shares of all households and typical sizes: nuclear family; couple
   without children; single man (cabin/shanty); single man boarding; widow-headed; family +
   servant(s); family + boarders; family + clerk/apprentice/journeyman (the shop household);
   boarding house; hotel/tavern; garrison company; crew/gang (harbour, construction); Indian
   Agency establishment (attested only — never reconstructed). Shares from the 1840 size
   distribution and the attested 1835 households, shifted by the rules stated.
2. **Family formation by head's age and trade** — probability married; children count by
   marriage duration; children's age spacing (the register's baptism intervals as the sample);
   the share of families who came WITH children vs formed here (arrival model, T-1165).
3. **Service and shop members** — servants/domestics per merchant/professional household
   (from the attested households that show one and the 1840 female 15–29 surplus in large
   households); apprentices/journeymen per workshop; clerks per store (agreed with
   T-1183).
4. **Lodgers** — share of single men boarding in a family house vs a boarding house vs a hotel;
   the "three in a bed" evidence (`residents_1835_inferred.md` § 3) as the capacity note.
5. **Naming of reconstructed family members** — the rule: forenames from
   `1835_invented_name_pools.json` by the head's community; surname = the head's; a wife may
   carry a maiden name only where a register names it; children's birth years by the spacing
   rule; every draw seeded by the household id so a rebuild reproduces it.
6. **Where a source names family** (baptism parents/godparents, marriages, Andreas biographies,
   old-settler reminiscences, the 1840 row of a head the 1835 layer carries), the source wins:
   those members are `inferred` (named) and the model fills only around them.

**Acceptance:**

- Builds, re-derives, `--check` in `check.sh`; `docs/RESEARCH/1835_household_model.md` prints
  every table and rule with its evidence; the file refuses a rule without a basis.
- A **dry-run** command applies the model to the known heads in memory and prints the household
  count, person count and size distribution it WOULD produce against T-1161's targets —
  the calibration is shown before any card is written; no card is written here.
- Cross-check: the dry-run's implied dwellings per household vs the census's 398 dwellings.
- Native and Métis households get their own composition rows (the traders' extended households,
  the register's families), evidenced from the attested ones and the treaty schedules, applied
  only by T-1177 and always `review_required`; the file says so.

**Stop condition:** T-1170 and T-1171 can generate families from this
file alone, deterministically, and say for every member which rule produced them.

**Links:** T-0507 · T-1161 · T-1165 · `1835_invented_name_pools.json` ·
`data/residents/kin_rulings.json` (the kin ties already ruled).
