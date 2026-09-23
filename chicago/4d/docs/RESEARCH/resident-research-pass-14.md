# T-0509 — Fourteenth resident-research cohort (76)

Status: **manifest frozen 2026-09-03 · research pending** · opened by T-0492

This pass covers the frozen 76-person T-0509 cohort. The ledger at
`data/research/residents/pass_14_findings.json` lists all 76 under `pending` and
`completed_person_ids` is empty, so nothing here changes a resident record yet.
`tools/select_resident_research_pass_14.py --gate` holds the manifest and is wired into
`tools/check.sh`.

## What the cohort is drawn from, measured

The frame is **228 named residents carrying no `resident_research` block**, not the 237 the
ticket estimated. The arithmetic, so nobody has to measure it again:

| | |
|---|---|
| people with no research block at all | 238 |
| less unnamed placeholders ("The rest of the Beaubien household, unnamed" and four like it) | −5 |
| less real named people held in `inf_*` / `hh_inf_*` records, retained unplaced by T-0489 | −5 |
| **the frame** | **228 = 76 + 76 + 76** |

The five `inf_*` people — J. Garland, J. W. Reed, Dr. Josiah C. Goodhue, Thomas S. Eels and
J. Shrigley — are real and are worth researching. `select_resident_research_pass_5.py` refuses an
`inf_` id outright and this follows it rather than quietly widening the rule; they have a ticket of
their own instead.

## The overlap that is intended, and the one that is refused

**225 of the 228 are the pilot, pass 2 and pass 3 cohorts** — reserved in an earlier pass and never
researched: no findings ledger, no reference package, no row on any person. That is T-0511's finding
seen from the other side, and it is why T-0492's acceptance clause *"zero overlap with passes 1–12"*
could not be met as written: the population satisfying it is three people.

So the manifest states the two non-overlaps that carry the meaning, and the selector enforces both:

- **zero overlap among cohorts 13, 14 and 15** — the collision lock the three parallel runs need;
- **zero overlap with the 611 people who already carry a research row**, which is passes 4–12 and the
  reference packages behind them.

Researching a person the pilot reserved and never reviewed is the work the owner asked for.
This cohort holds 76 such reservations.

## Selection

Frozen 2026-09-03 from `data/residents/households/*.json` — the household records themselves and not
`index.json`, which on that date listed 824 households against 825 on disk (T-0491). Every named
person with no research block, sorted inside the `established_profile`, `letter_list_only_present` and
`letter_list_only_uncertain` strata, interleaved one from each stratum in turn, and chunked 76/76/76
in fixed order. Cohort 14 runs `boles_george` … `curtenius_fredk`, and its strata are
25 established_profile, 26 letter_list_only_present, 25 letter_list_only_uncertain.

A member that later acquires a research row does **not** make this manifest stale — that is what the
pass is for. A member that leaves the town, or turns back into a placeholder, does, and
`--gate` fails on it.

## Method, when the research runs

The reviewing run works the repository corpus first, then the six source domains T-0492 scaffolded
under `data/research/` — civic lists, the 1830 and 1840 census, church registers, books, directories —
then the wider literature. An exact-name hit stays a search lead until a dated place, occupation,
kinship, migration or paired-name discriminator bridges it to this person. A source behind a login is
recorded as **inaccessible**, never as absent. No canonical household or person fact is silently
promoted: corroborated facts are applied field by field with provenance, and conflicts are preserved
rather than resolved by preference.
