# The surname collisions the corrected letter-list reading uncovered

DERIVED, NOT WRITTEN. Every number and every row below is produced by
`tools/report_letter_list_collisions.py`, which runs
`mint_letter_list_residents.mint()` twice over the committed tree — once under the
pre-T-0638 reading of a printed name, once under the corrected one — and reports the
difference. `--check` re-derives it and fails if this file has drifted from what the
tree now says, so it cannot quietly go stale.

T-0843 MOVED ONE ROW OUT OF THIS REPORT AND THE REASON IS WORTH READING. The pass
now consults the cross-domain identity master before it writes a card, so
`Norton N. R.` is refused under BOTH readings — the master resolves the initials
onto the committed Nelson R. Norton whichever token the old rule took for a
surname. It was never a difference between the two readings; the surname test was
simply too blunt to see it under one of them. The count below fell by one
accordingly, and nothing was retired to make that happen.

THE OWNER RULED, 2026-09-18: option (c). Refusals 7 and 8 are MINT-TIME rules and
do not un-mint a record that already stands. NOTHING IS RETIRED. The pass keeps every
standing record a mint-time refusal lands on and SAYS the collision on its card — a
`surname_collision` block naming the other holder — so a reader sees both records and
why both are here. `rank()` is unchanged, the cohort is not re-derived, and the
population does not move. This report is therefore no longer a list of proposed
retirements; it is the derivation behind the blocks, and the rows below are the same
rows they were, read now off what the pass says rather than off who it drops.

## The two readings, over the same pool

* the pool the register offers this pass: **1877** candidates
* accepted under the pre-T-0638 reading: **769**
* accepted under the corrected reading: **789**
* standing records a mint-time refusal lands on, corrected reading: **75**; pre-T-0638 reading: **67**
* THE COLLISIONS THIS FAULT UNCOVERED — said under the corrected reading and not under the old one: **8**
* candidates the correction ADMITS that the old reading refused: **20**

## The collisions — what the paper printed, and who holds the surname instead

`old` and `new` are the family name each reading takes off the printing. `holds it`
is the record the refusal defers to, and under the ruling it defers by SAYING so and
not by standing down. `carries` is what a retirement would have stranded, and is kept
in the table because it is the measure of what option (c) declined to throw away.

| printed | as a card shows it | old | new | the refusal it says | holds it | returns | carries |
|---|---|---|---|---|---|---|---|
| `Es,Jones, High` | High Es Jones | `es` | `jones` | the town already names a Jones | Benjamin Jones (hh_jones_benjamin); D E Jones (hh_jones_d_e); M Jones (hh_jones_m) … | 1 | research row T-0481 (no_corroboration_yet) |
| `Esther Preston` | Esther Preston | `preston` | `preston` | surname already minted | Stephen II. Preston | 1 | research row T-0479 (no_corroboration_yet) |
| `Frederick W. Page` | Frederick W. Page | `page` | `page` | surname already minted | Elisha S. Page | 1 | research row T-0510 (no_corroboration) |
| `Mason Sabrina A.` | Sabrina A. Mason | `a` | `mason` | the town already names a Mason | Matthias Mason (hh_mason_matthias) | 1 | research row T-0482 (no_corroboration_yet) |
| `Mills Joel C.` | Joel C. Mills | `c` | `mills` | the town already names a Mills | John A Mills (hh_mills_john_a) | 1 | research row T-0482 (no_corroboration_yet) |
| `Norton Wm. H.` | Wm. H. Norton | `h` | `norton` | the town already names a Norton | Nelson R. Norton (hh_norton_nelson_r) | 1 | research row T-0483 (no_corroboration_yet) |
| `Perry A. 8.` | A. [?] Perry | `8` | `perry` | the town already names a Perry | Calvin Perry (hh_perry_calvin) | 1 | research row T-0483 (no_corroboration_yet), directory fergus_chicago_directory_1839, directory fergus_chicago_directory_1843, directory norris_directory_1844 |
| `Wm. Osborn` | Wm. Osborn | `osborn` | `osborn` | surname already minted | B. Osborn | 1 | research row T-0485 (candidate_identity), directory fergus_chicago_directory_1839, directory fergus_chicago_directory_1843 |

## Why no tool picks a survivor, and why the ruling asked none to

These were the three reasons the loop could not answer the survivorship question,
and they are why the owner answered it with (c) — keep both, say the collision.

* **They are not all duplicates.** `Joel C. Mills` and `Philo C. Mills` are two
  different men. Refusal 8 is a rule about how much one pass may assert on a family
  name, not a statement that two records are one person — so retiring on it would
  have removed a person rather than merging two.
* **`rank()` is blind to how good a record is.** It orders single-return names by
  the NEWEST return, so the survivor would have been whichever letter was printed
  later — not the one with the fuller name, the research row or the directory match.
  The ruling leaves `rank()` alone precisely because it no longer has to pick.
* **The loser would have been the better-attested record.** The `carries` column
  above is the measure of that, and it is not empty.

## The committed cohort against its own derivation

The tree holds **743** letter-list households. The pass, run today
against that same tree, derives **789**. `check.sh` runs this pass's
`--gate` and not its `--check`, so the gap has never been red. Under the ruling the
mint-time causes are gone from this table by construction — a standing record is no
longer out of step with its own pass for colliding on a family name. What is left is
split by cause:

| households | cause |
|---|---|
| 3 | the record stands under a different id (a rename, not a retirement) |
| 3 | no longer in the pool the register offers |

**This is the finding that resized T-0660, and the ruling then dissolved it.** The
ticket was filed believing the retirements were the collisions. Most of them were
not: they were records whose surname the town acquired from a LATER pass, long after
this cohort was minted — T-0691's 76, filed as a separate ruling about a separate
rule. Option (c) answers both with one sentence, because neither kind of collision
un-mints anything now. What survives of T-0691 is wiring its `--check` into
`check.sh`, which is a gate question and not a retirement question.

## The candidates the correction admits

The other half of the same diff, and none of them is committed today.

| printed | as a card would show it | old | new | returns |
|---|---|---|---|---|
| `Augustus H, Conant` | Conant Augustus H | `h` | `augustus` | 1 |
| `Chester Marshall 2` | Marshall [?] Chester | `2` | `chester` | 1 |
| `Eliphalet Atkins 2` | Atkins [?] Eliphalet | `2` | `eliphalet` | 1 |
| `Julius Perrin 2` | Perrin [?] Julius | `2` | `julius` | 1 |
| `Lauretta Plympton 2` | Plympton [?] Lauretta | `2` | `lauretta` | 1 |
| `Levi Hills 2` | Hills [?] Levi | `2` | `levi` | 1 |
| `Loweley. Watere e` | Watere e Loweley | `e` | `loweley` | 1 |
| `Miranda Miner 2` | Miner [?] Miranda | `2` | `miranda` | 1 |
| `Mr. Roult 2` | Roult [?] Mr | `2` | `roult` | 1 |
| `Nett Robert A.` | Robert A. Nett | `a` | `nett` | 1 |
| `Nicholson Joshua F.` | Joshua F. Nicholson | `f` | `nicholson` | 1 |
| `Orisbee Edgar I..` | Edgar I.. Orisbee | `i` | `orisbee` | 1 |
| `Ormshee S. B.` | S. B. Ormshee | `b` | `ormshee` | 1 |
| `Osborn B.` | B. Osborn | `b` | `osborn` | 1 |
| `Pedrick Robert c.` | Robert c. Pedrick | `c` | `pedrick` | 1 |
| `Root Ez c.` | Ez c. Root | `c` | `root` | 1 |
| `Salmon Rutherford 3` | Rutherford [?] Salmon | `3` | `salmon` | 1 |
| `Swanwick F.` | F. Swanwick | `f` | `swanwick` | 1 |
| `Timothy B.` | B. Timothy | `b` | `timothy` | 1 |
| `W. Vanzandt 2` | Vanzandt [?] W. | `2` | `vanzandt` | 1 |

## A residual fault in the corrected reading

Reported here rather than fixed, because a change to `surname()` re-derives the
whole cohort, and the ruling of 2026-09-18 explicitly declined to pay for that: it
is option (b)'s cost, and (b) is not what was chosen.

| printed | reads the surname as | after the comma |
|---|---|---|
| `Augustus H, Conant` | `augustus` | `Conant` |

A comma says the family name is the group BEFORE it. When that group ends on an
initial, `surname_is_first_token()` fires and takes the first full word of the
whole printing — the given name — instead of the full word after the comma.

---

Generated by `tools/report_letter_list_collisions.py --write`. Do not hand-edit:
`--check` compares this file against a fresh derivation.
