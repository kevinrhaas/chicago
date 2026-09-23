---
id: T-0866
title: The card rename of T-0721 broke the register's link to two townspeople: Abbot and Gabbs are proposed as new residents the town does not hold
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-10
pr: 1092
claimed_by: run 9/10/2026, 5:53:24 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T23:38:09.352Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34539411529
---

**Measured on `dev` at 4366ffbba, 2026-09-06, against 37b3c03a9~1 — the commit before
T-0721's PR #921 landed.**

`data/research/newspapers/register_1835.json` crosswalks every name the papers print
against the town's own cards, and says of each one whether the town already holds the
person (`enrich`, with the `action_target` naming the card) or does not (`new_resident`).
It matches on the card's stored NAME.

PR #921 settled T-0721 by rewriting the stored display name of the three digit-bearing
letter-list cards — `8. G. Abbot` became `[?] G. Abbot`, `James I1. Gabbs` became
`James [?] Gabbs` — and the crosswalk's match went with it:

| printed name | before #921 | on dev now |
|---|---|---|
| `Abbot, 8. G.` | `enrich` → `abbot_8_g` | `new_resident`, target `null` |
| `Gabbs, James I1.` | `enrich` → `gabbs_james_i1` | `new_resident`, target `null` |
| `Perry A. 8.` | `new_resident` | `new_resident` (unchanged) |

`counts.persons.by_action`: `enrich` **1373 → 1371**, `new_resident` **1233 → 1235**.

So the register now states, of two people the town holds under `hh_abbot_8_g` and
`hh_gabbs_james_i1`, that they are "a named person the town does not hold. Known only from
the post-office letter lists." That sentence is false of both, and it is the exact class of
untruth T-0692 was opened over: a derived file whose stated reason does not describe the
record it is about. `tools/compile_register.py` line 1407 is where it is written.

Nothing appears to have been minted twice as a result — `mint_letter_list_residents.py`
derives its household id from `plain_fragment()` over the PRINTED name, not the card's
display name, so it still lands on the existing card, and its `--gate` is green. The fault
is the register's ASSERTION, and the fragility underneath it: the crosswalk's link to a card
is only as stable as that card's display string, and this project renames display strings
whenever a reading is corrected (T-0638 moved 36 of them).

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. `Abbot, 8. G.` and `Gabbs, James I1.` read `enrich` against `abbot_8_g` and
   `gabbs_james_i1` again, with the counts back to 1373/1233 for those two rows.
2. The link survives a display rename. Whatever the fix — matching on the printed name the
   card was minted from, on the person id, or on the bracket-stripped name — a card whose
   display string changes must not silently become a stranger to the register. State which
   was chosen and why.
3. A gate says so. The register is derived and re-derives on `check.sh`; add the assertion
   that no `new_resident` row names a printed name a committed card was minted from, or
   demonstrate why that invariant cannot hold.

**Found by** the run that was building a rival fix for T-0721 (PR #963, closed unmerged
when #921 landed): it measured the two register states above while comparing the two
approaches.

**Links:** T-0721 · T-0638 (the rename pass that moves display strings) · T-0692 (a stated
reason has to be true of the record).

---

## WHAT WAS DONE — the link is the mint's own key (PR pending, 2026-09-10)

**The fault was wider than the two rows this ticket was filed over.** Measured on `dev`
at b2a5a3c7d, the register's person actions moved:

| | before | after |
|---|---|---|
| `enrich` | 1355 | 1392 |
| `new_resident` | 1244 | 1207 |
| `replace_invented` | 24 | 24 |

**54 rows changed.** 37 of them read `new_resident` — "a named person the town does not
hold" — while a mint pass held a card written from that very printed name; `Abbot, 8. G.`
and `Gabbs, James I1.` are two of the 37, and `Perry A. 8.`, which this ticket recorded as
"unchanged", is a third: it was never a stranger either, and the display-string match had
simply never seen it. The other 17 were worse than lost — the register had handed the row
to a DIFFERENT person of the same surname, because the identity policy compares as far as
the shorter initials run reaches and a printed forename shares its first letter with the
card's:

    Alanson B. Vaughan   → vaughan_angeline   → vaughan_alanson_b
    Charlotte Wesencraft → wesencraft_charles → wesencraft_charlotte
    Jeremiah Smith       → smith_james        → smith_jeremiah
    Johnson, Seth        → johnson_samuel     → johnson_seth
    Simmons, Medad I.    → simmons_marion     → simmons_medad_i
    [R]osice Hunter      → hunter_robert      → hunter_osice
    …and eleven more, listed in the register diff.

**Acceptance 2 — which link was chosen, and why.** The card's id, not its printed name and
not its display string. Every mint in this project writes a person id as
`plain_fragment(<printed name>)`, so the id IS the printed name normalized — and an id
does not move when a reading is corrected, which is exactly the property the display
string lacks. Matching the printed name itself would have needed a field no card carries;
matching the bracket-stripped display name would have decayed the same way the next time a
name is corrected, only more slowly.

It is exactly as sound as the mint's own identity decision and no sounder: two printed
names collide on one fragment only when they carry the same surname and the same given
words, which is the case the mints already refuse to mint twice. A HAND-AUTHORED card is
excluded — its id was never derived from a printing, so an id that happens to equal a
fragment is a coincidence and not a link. That is why 3 of the 43 fragment-equal rows
found in the first sweep were left alone.

**AND THE TWO MINTS DO NOT AGREE ON THE KEY**, which is the finding this repair turned up.
`mint_letter_list_residents.plain_fragment` and `mint_documented_residents.plain_fragment`
are textual duplicates of each other except in `surname()`: the letter-list pass knows the
lists' surname-first setting and the documented pass does not, so `Mills Joel C.` is
`mills_joel_c` to one and `c_mills_joel` to the other. Importing one copy and using it for
every card recovered only 15 of the 54. `compile_register.py` now asks EACH pass for the
key it would have written and matches only against the cards that pass actually wrote
(`MINT_KEY`), which is the only reading of "the name it was minted from" that is true of
both.

**Acceptance 3 — the gate.** `minted_link_problems()`, a module-level function so it can
be handed rows the matcher can no longer produce, asserts both halves: no non-`enrich` row
may name a printed name a mint made a card from, and an `enrich` row that does must target
THAT card. It runs inside `compile_register()`, so `check.sh` re-derives it on every build.
Three self-test units prove it fires on each half and is silent on a correct row.

**Also in the same commit,** because the register is an input to them: `hh_morris_b_s.json`
re-derived (its prose count of people-held-in-the-same-claim falls 4 → 3, the residency
test's own verdict and the minted set unchanged — 5 minted, and the candidate pool falls
93 → 88 because five of its candidates are now recognised as held), and
`docs/RESEARCH/letter-list-surname-collisions.md` re-derived (the two households recorded
as "no longer in the pool the register offers" were never out of it).

**Verification:** `./tools/check.sh` — CHECK PASS. `compile_register.py --self-test` — 67
cases.
