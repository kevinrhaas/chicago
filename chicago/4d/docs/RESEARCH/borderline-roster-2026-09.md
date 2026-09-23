# The borderline roster — the names the research read and withheld

DERIVED, T-1159, by `tools/export_borderline_roster.py --build` from the T-1143 ledger and the resident layer, as of 2026-09-18. Do not hand-edit: `--check` re-derives this page byte-for-byte and `tools/check.sh` runs it.

The research spend was, correctly, conservative. This page does not overturn one refusal of it. A refusal was a ruling about EVIDENCE and it stands — what changes is that the reconstruction band is now shown the corpus's own names first, each with its evidence limit stated, so it names real people before it invents any.

**Nothing here is minted.** No card, grade, presence or ledger disposition is written by the tool that builds this file.

## What the roster holds

| | count |
|---|---:|
| rows | 15226 |
| ledger units considered (every non-`asserted` unit) | 23693 |
| of those, units naming no person | 9384 |

## By class

| class | rows | who | what reconstruction may do |
|---|---:|---|---|
| `R1_in_window_uncertain` | 804 | A card exists, its source is inside the window, and its presence on 1 July 1835 is `uncertain`. | Fix presence `present` at tier `reconstructed`, basis = the dated appearance plus the population model's persistence rate. |
| `R2_in_window_single_source` | 309 | One appearance inside the window, no card, the ledger withheld it as a single source or on insufficient identity. | Mint a reconstructed resident under the read name. |
| `R3_1834_return_or_muster` | 29 | A name on the 1 April 1834 post-office return (T-1153) or the 1832 Black Hawk muster enrolled at Chicago, with no 1835 corroboration and no card. | Mint reconstructed, presence bounded by the persistence rate. |
| `R4_surname_only_census` | 432 | A census reading that gives a surname this town already holds and no person of its own — the 1830 surname-only refusals and the 1840 heads. | May supply a FAMILY (spouse and child bands) to an existing head at `reconstructed`. Never a new head. |
| `R5_later_only_backprojectable` | 53 | A later-only name — the 1839 directory, the 1840 census, the old-settler rolls — whose own biography dates an arrival before 1 July 1835. | Mint reconstructed with arrival at the biography's date. |
| `R6_native_metis_black` | 143 | A Native, Métis or free Black person a source names in or near the town inside the window, whatever the ledger disposition. | Mint at the ladder's grade the evidence allows, else `reconstructed`. Always `review_required` for Native and Métis rows; `community` set. Owned by T-1177. |
| `R0_ineligible` | 13456 | Outside Chicago, the Bear Creek marriages (T-1129), the declared `researched_not_resident` names, post-scene arrivals with nothing to back-project from, and names this town already carries. | Never. |

## By class and domain

| class | domain | rows |
|---|---|---:|
| `R1_in_window_uncertain` | `residents_layer` | 804 |
| `R2_in_window_single_source` | `books` | 28 |
| `R2_in_window_single_source` | `church` | 136 |
| `R2_in_window_single_source` | `land_sales` | 145 |
| `R3_1834_return_or_muster` | `civic` | 29 |
| `R4_surname_only_census` | `census_1830` | 63 |
| `R4_surname_only_census` | `census_1840` | 369 |
| `R5_later_only_backprojectable` | `old_settlers` | 53 |
| `R6_native_metis_black` | `books` | 12 |
| `R6_native_metis_black` | `census_1840` | 7 |
| `R6_native_metis_black` | `church` | 4 |
| `R6_native_metis_black` | `civic` | 93 |
| `R6_native_metis_black` | `directories` | 4 |
| `R6_native_metis_black` | `old_settlers` | 7 |
| `R6_native_metis_black` | `residents_layer` | 16 |
| `R0_ineligible` | `books` | 135 |
| `R0_ineligible` | `census_1830` | 136 |
| `R0_ineligible` | `census_1840` | 661 |
| `R0_ineligible` | `church` | 1609 |
| `R0_ineligible` | `civic` | 357 |
| `R0_ineligible` | `directories` | 7025 |
| `R0_ineligible` | `genealogytrails` | 1 |
| `R0_ineligible` | `land_sales` | 1427 |
| `R0_ineligible` | `old_settlers` | 1025 |
| `R0_ineligible` | `residents` | 1080 |

## Every rule that put a row where it is

| class / rule | rows |
|---|---:|
| `R0_ineligible/already_carried_as_present` | 1065 |
| `R0_ineligible/carried_by_the_cards_own_row` | 1097 |
| `R0_ineligible/carried_under_a_crosswalk_merged_name` | 161 |
| `R0_ineligible/earlier_than_the_window` | 149 |
| `R0_ineligible/later_only_and_not_backprojectable` | 9849 |
| `R0_ineligible/ledger_a_sale_is_never_a_residence` | 413 |
| `R0_ineligible/ledger_earlier_evidence_adds_no_1835_fact` | 19 |
| `R0_ineligible/ledger_identity_refused_in_the_crosswalk` | 13 |
| `R0_ineligible/ledger_named_as_a_visitor_not_a_resident` | 2 |
| `R0_ineligible/ledger_pre_1830_settler_roster` | 6 |
| `R0_ineligible/ledger_suspicion_is_not_a_reading` | 9 |
| `R0_ineligible/ledger_the_purchaser_is_a_corporate_body` | 27 |
| `R0_ineligible/ledger_the_purchaser_is_a_firm_style` | 2 |
| `R0_ineligible/ledger_the_registers_date_is_unreadable` | 7 |
| `R0_ineligible/not_a_town_finding` | 9 |
| `R0_ineligible/outside_chicago` | 108 |
| `R0_ineligible/researched_not_resident` | 9 |
| `R0_ineligible/surname_only_and_unmatched` | 254 |
| `R0_ineligible/undated_reading` | 257 |
| `R1_in_window_uncertain/card_presence_is_uncertain` | 804 |
| `R2_in_window_single_source/in_window_read_and_withheld` | 181 |
| `R2_in_window_single_source/in_window_unspent_inside_an_asserted_claim` | 128 |
| `R3_1834_return_or_muster/blackhawk_muster_1832_at_chicago` | 29 |
| `R4_surname_only_census/census_1830_crosswalk_refused_on_surname_only` | 63 |
| `R4_surname_only_census/census_1840_head_surname_matches` | 340 |
| `R4_surname_only_census/census_surname_matches_a_held_head` | 29 |
| `R5_later_only_backprojectable/own_biography_dates_the_arrival` | 53 |
| `R6_native_metis_black/community_term_in_the_reading` | 123 |
| `R6_native_metis_black/community_term_on_the_card` | 16 |
| `R6_native_metis_black/community_term_written_onto_the_name` | 4 |

## Twenty worked examples — five per class, R1 to R4

Five rows of each class, in the roster's own order, with the reason each name was withheld from the town. These are the rows a reader should check the rules against.

### `R1_in_window_uncertain` — 804 rows

| name as read | dated | source | why it was withheld |
|---|---|---|---|
| A. A. M'Grigg | 1834-10-22 | `hh_mgrigg_a_a` | The layer holds this household and no source follows it to 1 July 1835, so its presence stands `uncertain`. Reconstruction may fix it `present` at tier `reconstructed` against the persistence rate. |
| A B Sasoton | 1834 | `hh_sasoton_a_b` | The layer holds this household and no source follows it to 1 July 1835, so its presence stands `uncertain`. Reconstruction may fix it `present` at tier `reconstructed` against the persistence rate. |
| A. Beegle | 1834-07-16 | `hh_beegle_a` | The layer holds this household and no source follows it to 1 July 1835, so its presence stands `uncertain`. Reconstruction may fix it `present` at tier `reconstructed` against the persistence rate. |
| A Filer | 1835 (a window over the scene date, so no day before it) | `hh_filer_a` | The layer holds this household and no source follows it to 1 July 1835, so its presence stands `uncertain`. Reconstruction may fix it `present` at tier `reconstructed` against the persistence rate. |
| A. M. Wing | 1834-07-02 | `hh_wing_a_m` | The layer holds this household and no source follows it to 1 July 1835, so its presence stands `uncertain`. Reconstruction may fix it `present` at tier `reconstructed` against the persistence rate. |

### `R2_in_window_single_source` — 309 rows

| name as read | dated | source | why it was withheld |
|---|---|---|---|
| Rev. Allan B. Freeman | 1833 | `bk_mose1_005` | A dated appearance inside the window under a read name that no card in this layer carries. The ledger closed the unit `asserted`, but the claim is the ledger's unit and an assertion closes the whole reading: being inside a spent claim is… |
| Rev. Allen B. Freeman | 1833 | `bk_mose2_010` | A dated appearance inside the window under a read name that no card in this layer carries. The ledger closed the unit `asserted`, but the claim is the ledger's unit and an assertion closes the whole reading: being inside a spent claim is… |
| Betsey Crane | 1833 | `bk_mose2_010` | A dated appearance inside the window under a read name that no card in this layer carries. The ledger closed the unit `asserted`, but the claim is the ledger's unit and an assertion closes the whole reading: being inside a spent claim is… |
| Charles Cleaver | 1833 | `bk_mose1_005` | A dated appearance inside the window under a read name that no card in this layer carries. The ledger closed the unit `asserted`, but the claim is the ledger's unit and an assertion closes the whole reading: being inside a spent claim is… |
| Ebenezer Crane | 1833 | `bk_mose2_010` | A dated appearance inside the window under a read name that no card in this layer carries. The ledger closed the unit `asserted`, but the claim is the ledger's unit and an assertion closes the whole reading: being inside a spent claim is… |

### `R3_1834_return_or_muster` — 29 rows

| name as read | dated | source | why it was withheld |
|---|---|---|---|
| TAYLOR, A W | 1832 | `blackhawk_1832_110` | Enrolled at Chicago in the 1832 muster, with no 1835 corroboration and no card; presence is bounded by the persistence rate. |
| HARRIS, BENJAMIN | 1832 | `blackhawk_1832_034` | Enrolled at Chicago in the 1832 muster, with no 1835 corroboration and no card; presence is bounded by the persistence rate. |
| MOSELLE, CHARLES | 1832 | `blackhawk_1832_073` | Enrolled at Chicago in the 1832 muster, with no 1835 corroboration and no card; presence is bounded by the persistence rate. |
| SHEDAKER, CHRISTOPHER | 1832 | `blackhawk_1832_100` | Enrolled at Chicago in the 1832 muster, with no 1835 corroboration and no card; presence is bounded by the persistence rate. |
| LAFROMBOISE, CLAUDE | 1832 | `blackhawk_1832_051` | Enrolled at Chicago in the 1832 muster, with no 1835 corroboration and no card; presence is bounded by the persistence rate. |

### `R4_surname_only_census` — 432 rows

| name as read | dated | source | why it was withheld |
|---|---|---|---|
| Aaron Friend | — | `hh_friend_charles` | The 1830 crosswalk weighed this head against the town and REFUSED the join on a surname match alone, which is exactly a surname this town holds attached to a person it does not. It may shape a family for the head it matched, and never a… |
| Abner Young | — | `hh_young_gideon` | The 1830 crosswalk weighed this head against the town and REFUSED the join on a surname match alone, which is exactly a surname this town holds attached to a person it does not. It may shape a family for the head it matched, and never a… |
| Amos Leonard | — | `hh_leonard_anson` | The 1830 crosswalk weighed this head against the town and REFUSED the join on a surname match alone, which is exactly a surname this town holds attached to a person it does not. It may shape a family for the head it matched, and never a… |
| Ashbell Merrill | — | `hh_merrill_george_w` | The 1830 crosswalk weighed this head against the town and REFUSED the join on a surname match alone, which is exactly a surname this town holds attached to a person it does not. It may shape a family for the head it matched, and never a… |
| Bailey Hobson | — | `hh_hobson_jesse` | The 1830 crosswalk weighed this head against the town and REFUSED the join on a surname match alone, which is exactly a surname this town holds attached to a person it does not. It may shape a family for the head it matched, and never a… |

## What this page does NOT claim

* **`R6` is a recall rule, not a verdict.** It is assigned by a declared term list read over the reading's own words, so that no evidence limit becomes the reason a community goes unbuilt. Every R6 row names the term that put it there; T-1177 owns the judgement and the review.

* **An `R0` row is not a person disproved.** It is a name this roster will not offer: already carried, outside Chicago, later-only with nothing to back-project from, a surname with no person, or owned by an open ruling.

* **Kin named in PROSE are out of reach, and that is a stated gap.** The rule for kin a review-flagged household names and no card carries is implemented and finds 0 today: every structured `kin` row on those eight households resolves to a household this town holds. It cannot reach a person who is named only inside a note — J. B. Beaubien's first wife Mah-naw-bun-no-quah is the case the tree states in as many words ('not a person in this dataset and no row is written for her'). Naming her here is the finished answer; guessing at prose with a pattern would not be.

* **`R4` never mints a head.** Under T-0507 an 1840 household is a SHAPE for a head that 1835 evidence already carries, never a person minted into 1835 on census counts alone.

