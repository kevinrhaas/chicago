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

T-0660 asks for this list before anything is retired, and the reason is in the third
section: the pass's own ranking would not always keep the better record, and two of
these collisions are not duplicates at all but two different men who cannot both hold
one family name.

## The two readings, over the same pool

* the pool the register offers this pass: **1879** candidates
* accepted under the pre-T-0638 reading: **704**
* accepted under the corrected reading: **716**
* candidates the correction REFUSES that the old reading accepted: **8**
* candidates the correction ADMITS that the old reading refused: **20**

## The collisions — what the paper printed, and who holds the surname instead

`old` and `new` are the family name each reading takes off the printing. `holds it`
is the record the refusal defers to — the survivor, if a survivor is what the owner
rules for. `carries` is what a retirement would strand.

| printed | as a card shows it | old | new | refused because | holds it | returns | carries |
|---|---|---|---|---|---|---|---|
| `Es,Jones, High` | High Es Jones | `es` | `jones` | the town already names a Jones | Benjamin Jones (hh_jones_benjamin); D E Jones (hh_jones_d_e); M Jones (hh_jones_m) … | 1 | research row T-0481 (no_corroboration_yet) |
| `Esther Preston` | Esther Preston | `preston` | `preston` | surname already minted | Stephen II. Preston | 1 | research row T-0479 (no_corroboration_yet) |
| `Frederick W. Page` | Frederick W. Page | `page` | `page` | surname already minted | Elisha S. Page | 1 | research row T-0510 (no_corroboration) |
| `Mason Sabrina A.` | Sabrina A. Mason | `a` | `mason` | the town already names a Mason | Matthias Mason (hh_mason_matthias) | 1 | research row T-0482 (no_corroboration_yet) |
| `Mills Joel C.` | Joel C. Mills | `c` | `mills` | the town already names a Mills | John A Mills (hh_mills_john_a) | 1 | research row T-0482 (no_corroboration_yet) |
| `Norton Wm. H.` | Wm. H. Norton | `h` | `norton` | the town already names a Norton | Nelson R. Norton (hh_norton_nelson_r) | 1 | research row T-0483 (no_corroboration_yet) |
| `Perry A. 8.` | A. [?] Perry | `8` | `perry` | the town already names a Perry | Calvin Perry (hh_perry_calvin) | 1 | research row T-0483 (no_corroboration_yet), directory fergus_chicago_directory_1839, directory fergus_chicago_directory_1843, directory norris_directory_1844 |
| `Wm. Osborn` | Wm. Osborn | `osborn` | `osborn` | surname already minted | B. Osborn | 1 | research row T-0485 (candidate_identity), directory fergus_chicago_directory_1839, directory fergus_chicago_directory_1843 |

## Why a tool may not pick the survivor

* **They are not all duplicates.** `Joel C. Mills` and `Philo C. Mills` are two
  different men. Refusal 8 is a rule about how much one pass may assert on a family
  name, not a statement that two records are one person — so applying it here
  removes a person rather than merging two.
* **`rank()` is blind to how good a record is.** It orders single-return names by
  the NEWEST return, so where two printings of one surname both stand, the survivor
  is whichever letter was printed later — not the one with the fuller name, the
  research row or the directory match.
* **The loser can be the better-attested record.** The `carries` column above is the
  measure of that, and it is not empty.

## The committed cohort against its own derivation

The tree holds **743** letter-list households. The pass, run today
against that same tree, derives **716**. `check.sh` runs this pass's
`--gate` and not its `--check`, so the gap has never been red. Split by cause:

| households | cause |
|---|---|
| 66 | the town gained this surname from another pass after the mint (the town already names that family) |
| 8 | THIS FAULT — the corrected reading collides it with another record |
| 3 | the record stands under a different id (a rename, not a retirement) |
| 3 | no longer in the pool the register offers |
| 1 | the town gained this surname from another pass after the mint (surname already minted) |

**This is the finding that resizes T-0660.** The ticket was filed believing the
retirements were the collisions. Most of them are not: they are records whose
surname the town acquired from a LATER pass, long after this cohort was minted, and
retiring them is a separate ruling about a separate rule.

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
whole cohort — the thing this ticket exists to put to the owner before it happens.

| printed | reads the surname as | after the comma |
|---|---|---|
| `Augustus H, Conant` | `augustus` | `Conant` |

A comma says the family name is the group BEFORE it. When that group ends on an
initial, `surname_is_first_token()` fires and takes the first full word of the
whole printing — the given name — instead of the full word after the comma.

---

Generated by `tools/report_letter_list_collisions.py --write`. Do not hand-edit:
`--check` compares this file against a fresh derivation.
