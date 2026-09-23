---
id: T-1162
title: The 1835 occupation model: how many of each trade, profession, office and employment a lake-port town of this size held in July 1835, from the 1839 directory, the 1840 industry columns, the 1833 roster and Andreas's business lists, net of the documented practitioners
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
closed_at: 2026-09-17T20:06:17.707Z
claimed_run: null
---

The retired inferred-residents programme argued each trade count from five in-dataset figures
because "no period trade table for a comparable western town exists in `data/sources/`"
(`docs/RESEARCH/residents_1835_inferred.md` § 2). That is no longer true: the project now holds
the 1839 directory crosswalk (`data/research/directories/`, a trade beside nearly every name),
the Fergus 1843 and Norris 1844 directories, the 1840 IPUMS industry columns
(`composition_1840.json`), the newspaper gazetteer's `occupations[]` (1833–35), and T-1145's
dated `roles[]`. This ticket derives the occupational structure the town SHOULD have on
1 July 1835, so that T-1166 can say how many shoemakers are missing rather than guess.

**Deliverable** — `data/reconstruction/1835_occupation_model.json`, built by
`tools/build_occupation_model_1835.py --build|--check|--self-test`:

1. **A controlled trade list** = `data/residents/index.json` `vocabulary.occupations` (extend it
   where the directories print a trade it lacks — e.g. sawyer, teamster, boatman, mason,
   plasterer, painter, tinsmith, brickmaker, hostler, bar-keeper, laundress, domestic, seamstress,
   schoolmistress, clerk, apprentice), each mapped to a role kind and to the archetype family
   that houses its workplace (`1835_family_archetype_crosswalk.json`: W1 forge, W2 joiner, W3
   cooper/wheelwright, C1–C4 stores, T1–T2 taverns, F1–F4 warehouses, H3 boarding house…).
2. **The 1839 share** per trade (count / all 1839 entries with a trade), the **1840 industry
   share** (agriculture / commerce / manufactures-and-trades / navigation / learned professions),
   and the **1833 roster share**, side by side.
3. **The 1835 target** per trade = the 1839 share applied to the 1835 working population
   (T-1161's male 15+ plus the female service trades the sources show), corrected by named
   rules: building trades UP for the 1835 boom (the roof programme's 662 roofs, most raised
   1834–35), navigation UP for the harbour season, professions capped by what the press attests,
   labourers as a residual not a share (the largest trade and the one no roster records).
4. **Documented count** per trade (in-window `roles[]` after T-1145), **gap** = target −
   documented, and the **workplace count** the gap implies (a smith per forge; clerks per store
   per T-1183 once it lands — until then the ratio stated here).
5. Every row: `{ target, low, high, documented, gap, tier: reconstructed, basis, source_ids[] }`.

**Acceptance:**

- Builds, re-derives, `--check` in `check.sh`; `docs/RESEARCH/1835_occupation_model.md` prints
  the table with the derivation of every correction rule in prose.
- The trade vocabulary extension lands in `data/residents/index.json` with each new trade's
  archetype family and role kind; `validate.py` accepts them.
- Cross-check printed: the model's workplace counts against the roof programme's family targets
  (52 stores, 30 workshops, 42 boarding houses, 10 inns, 20 warehouses) — where they disagree,
  the ticket says which is corrected and why (the programme is a production decision, not a
  count; the occupation model may move it in T-1196).
- Visible: the "The town's people" card lists the top twenty trades — known vs implied.

**Stop condition:** for every trade in the vocabulary the file states how many the town should
hold, how many it has, and where the difference should work.

**Links:** T-1161 · T-1145 · T-0669 (later printings carry a trade forward, dated) ·
`docs/RESEARCH/1835_family_archetype_crosswalk.md`.
