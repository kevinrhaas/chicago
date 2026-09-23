---
id: T-1027
title: EPIC: the 68 one-letter card pairs the exact candidate test cannot see, ruled on pages one cluster at a time
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1291
needs_bake: false
closed_at: 2026-09-17T19:18:44.652Z
claimed_run: null
---

EPIC: the 68 one-letter card pairs the exact candidate test cannot see, ruled on pages one
cluster at a time.

**THE LOOP DOES NOT WORK THIS UNTIL THE OWNER PROMOTES IT.** It is filed under EPICS on the
queue's own filing rule — finishing it takes far more than five tickets — and it is ONE ticket
carrying the list rather than 68 lines the owner would have to rank.

**WHERE IT COMES FROM.** T-1002 folded three duplicate pairs the candidate test in
`tools/consolidate_town_cards.py` could not see, because that test buckets the cards by the
surname as a STRING and then weighs the forenames with `compatible()`, which admits a full
word against the same word, an initial the word begins with, or a card printing a title and no
forename. Nothing in it admits a LETTER. The ticket's third acceptance clause asked how large
that blind spot is rather than assuming three was all of it, and the answer is
`tools/measure_card_fuzzy_candidates.py`: run the same test with one letter of slack — on the
surname, and on the forename where the surname is exact — and over 1,373 cards it proposes 68
pairs the exact test does not, 62 folding the surname and 6 the forename, 12 of them already
carrying a written ruling.

**THE LIST IS NOT A WORKLIST OF 68 MERGES, AND THAT IS THE POINT.** It mixes at least four
kinds, which is why a run takes ONE cluster and rules it on a page:

  * **A spelling the sources really do set two ways** — Foot/Foote, Forsyth/Forsythe,
    Lloyd/Loyd, Pearson/Pearsons, Pruyne/Pryne, Eldredge/Eldridge, Wesencraft/Wessencraft,
    Kingston/Kingstone, Salisbury/Salsbury, Scarrett/Scarritt, Vanderbogart/Vanderbogert.
    These are the C7/C9/C10 shape and each wants the page that demonstrates the variation.
  * **A card minted off a garble** — `chark_john_a` for Clark, `tmple_john_t` for Temple,
    `smow_george_w` for Snow, `canp_george_s` for Camp, `mgregor_a` for McGregor,
    `blanshard_f_g` for Blanchard, `stoel_c_ii`, `trall_e_l`, `gabbs_james_i1`. Rule R5
    refuses these by rule and T-0695 is the ticket that reads them; a fold here would repair a
    wreck by guessing at it.
  * **An initial gathered across a folded surname** — J. Green against Major John Greene,
    J. B. Falker against two Walkers, J Ambrose Wight against three Wrights. The slack is on
    the surname and the forename inference is `compatible()`'s own, so the test cannot decline
    it; R2's two-rivals refusal does most of the work.
  * **Two people one letter apart** — J. H. Collins against John Rollins, John Hale against
    John Vale, Mark Noble against Mary Noble, James Sheldon against James Wheldon, Byram King
    against Hyram King. A distance cannot tell these from the first kind. It is the same answer
    T-1001 reached over the land register's 427 purchaser spellings, reached again over the
    cards, and it is the standing argument against ever widening `clusters()`.

**HOW A RUN WORKS IT, once promoted.** Take the topmost pair in the table below that carries no
ruling; find the page; rule it in `data/residents/card_merge_rulings.json` under an existing
rule or a new one drawn as narrowly as C6 through C11 are; land it with
`tools/consolidate_town_cards.py --apply`; rebuild the derived crosswalks that gather by name
(`tools/read_land_sales.py --build`, and check what else drifts); strike the row here. A run
that rules one pair and writes out what would have said two men is a whole unit of work. A run
that folds several on the resemblance has done the thing this epic exists to prevent.

**THE 68, as measured on the tree T-1002 shipped.** `ruled` names the cluster in
`card_merge_rulings.json` that already covers one or both cards — it does not mean the PAIR is
ruled, and several of those are refusals under R5 or R2 that a page could reopen. Regenerate
with `tools/measure_card_fuzzy_candidates.py --detail`.

| card | name | card | name | folds | ruled |
|---|---|---|---|---|---|
| `allan_richard_b` | Richard B. Allan | `allin_richard` | Richard Allin | surname | — |
| `anight_clark` | Clark Anight | `knight_clark` | Clark Knight | surname | — |
| `babeu_joseph` | Joseph Babeu | `babeue_joseph` | Joseph Babeue | surname | — |
| `barre_john_s` | John S. Barre | `barry_john_s` | John S. Barry | surname | — |
| `beech_reuben` | Reuben Beech | `bench_reuben` | Reuben Bench | surname | — |
| `blanchard_f_gantry` | F Gantry Blanchard | `blanshard_f_g` | F G Blanshard | surname | blanchard |
| `bread_a_o_t` | A O T Bread | `breed_a_o_t` | A O T Breed | surname | — |
| `burk_james` | James Burk | `burke_james` | James Burke | surname | — |
| `camp_g_t` | G T Camp | `canp_george_s` | George S. Canp | surname | — |
| `cary_john_marshall` | John Marshall Cary | `cory_john_l` | John L Cory | surname | — |
| `chark_john_a` | John A. Chark | `clark_john_a` | John A Clark | surname | clark-john |
| `chark_john_a` | John A. Chark | `clark_john_k` | John K Clark | surname | clark-john |
| `collins_j_h` | J. H. Collins | `rollins_john` | John Rollins | surname | — |
| `curtin_l_g` | L. G. Curtin | `curtis_liman` | Liman Curtis | surname | — |
| `curtis_jacob_s` | Jacob S Curtis | `curtiss_j` | J. Curtiss | surname | — |
| `curtis_liman` | Liman Curtis | `curtiss_l_g` | L G Curtiss | surname | — |
| `david_john` | John David | `davis_john` | John Davis | surname | — |
| `dell_frank` | Frank Dell | `dill_frank` | Frank Dill | surname | — |
| `eldredge_john_w` | John W Eldredge | `eldridge_john_w` | John W Eldridge | surname | — |
| `falker_j_b` | J. B. Falker | `walker_james` | James Walker | surname | — |
| `falker_j_b` | J. B. Falker | `walker_jeremiah` | Jeremiah Walker | surname | — |
| `foot_john` | John Foot | `foote_john` | John Foote | surname | — |
| `foot_s` | S. Foot | `foote_star` | Star Foote | surname | — |
| `forsyth_william` | William Forsyth | `forsythe_william` | William Forsythe | surname | — |
| `fraser_wm_h` | Wm. H. Fraser | `frazer_wm_h` | Wm. H. Frazer | surname | — |
| `gabbs_james_i1` | James [?] Gabbs | `gibbs_james_h` | James H. Gibbs | surname | — |
| `green_j` | J Green | `greene_john` | Major John Greene | surname | — |
| `hale_john` | John Hale | `vale_john` | John Vale | surname | — |
| `hands_george_e` | George E Hands | `handy_major` | Major Handy | surname | handy |
| `harman_isaac` | Isaac Harman | `harmon_isaac_d` | Isaac Dewey Harmon | surname | harmon-isaac |
| `hoit_thomas` | Thomas Hoit | `hoyt_thomas` | Thomas Hoyt | surname | — |
| `hussey_robert` | Robert Hussey | `hussy_robert` | Robert Hussy | surname | — |
| `inf_joiner_north_02` | J. W. Reed | `reid_j_chester` | J. Chester Reid | surname | — |
| `kimbal_wm` | Wm. Kimbal | `kimball_walter` | W. Kimball | surname | — |
| `king_byra` | Byra King | `king_byram` | Byram King | forename | — |
| `king_byram` | Byram King | `king_hyram` | Hyram King | forename | — |
| `kingston_paul` | Paul Kingston | `kingstone_paul` | Paul Kingstone | surname | — |
| `lewie_wm` | Wm. Lewie | `lewin_w_y` | W. Y. Lewin | surname | — |
| `lloyd_alexander` | Alexander Lloyd | `loyd_alexander` | Alexander Loyd | surname | — |
| `ludb_john` | John Ludb | `ludby_john` | John Ludby | surname | — |
| `mcgregor_ashor` | Ashor Mcgregor | `mgregor_a` | A Mgregor | surname | — |
| `morrison_ordemus` | Ordemus Morrison | `morrison_orsemus` | Orsemus Morrison | forename | — |
| `murray_alonzo` | Alonzo Murray | `murry_alonzo` | Alonzo Murry | surname | — |
| `noble_mark` | Esq. Mark Noble | `noble_mary` | Mary Noble | forename | — |
| `paine_william` | William Paine | `payne_william` | William Payne | surname | — |
| `pearson_hiram` | Hiram Pearson | `pearsons_hiram` | Hiram Pearsons | surname | — |
| `pruyne_peter` | Peter Pruyne | `pryne_peter` | Peter Pryne | surname | — |
| `rider_eli_a` | Eli A Rider | `rider_elia` | Elia Rider | forename | — |
| `rose_niles` | Niles Rose | `ross_niles` | Niles Ross | surname | — |
| `salisbury_stephen_m` | Stephen M. Salisbury | `salsbury_stephen_m` | Stephen M Salsbury | surname | — |
| `scarrett_isaac` | Isaac Scarrett | `scarritt_isaac` | Isaac Scarritt | surname | — |
| `shearman_h_c` | H. C. Shearman | `sherman_h` | Mrs. H. Sherman | surname | — |
| `sheldon_james` | James Sheldon | `wheldon_james` | James Wheldon | surname | — |
| `smow_george_w` | George W Smow | `snow_george_w` | George W. Snow | surname | snow |
| `square_geo` | Geo. Square | `squire_george` | George Squire | surname | — |
| `stoel_c_ii` | C. II. Stoel | `stoer_clement` | Clement Stoer | surname | — |
| `teal_william` | William Teal | `teall_wm` | Wm. Teall | surname | — |
| `temple_john_t` | Dr John Taylor Temple | `tmple_john_t` | John T Tmple | surname | temple |
| `temple_mrs_john_t` | Mrs Temple | `tmple_john_t` | John T Tmple | surname | temple |
| `thrall_e_l` | E. L. Thrall | `trall_e_l` | E L Trall | surname | — |
| `vanderbogart_henry` | Henry Vanderbogart | `vanderbogert_henry` | Henry Vanderbogert | surname | vanderbogart |
| `vandine_john` | John Vandine | `vandino_john` | John Vandino | surname | — |
| `wesencraft_charles` | Charles Wesencraft | `wessencraft_charles` | Charles Wessencraft | surname | — |
| `wight_j_ambrose` | J Ambrose Wight | `wright_j` | J Wright | surname | wright |
| `wight_j_ambrose` | J Ambrose Wight | `wright_john` | John Wright | surname | wright |
| `wight_j_ambrose` | J Ambrose Wight | `wright_john_s` | John S. Wright | surname | wright |
| `wilson_john` | John Wilson | `wilton_john_l` | John L Wilton | surname | — |
| `wooley_jeddiah` | Jeddiah Wooley | `wooley_jedidiah` | Jedidiah Wooley | forename | — |

**WHAT MUST NOT HAPPEN.** A fold is a card DELETION and the town's resident count moves by it.
Nothing in this list may be folded to tidy a duplicate away, nothing may be folded because its
neighbour in the table was, and `clusters()` may not be widened to close the epic in one pass —
the measurement that prices that widening is gated in `check.sh` precisely so the argument
stays available to whoever next wants to.

**TWO FACTS FROM THE FORT, FOUND BY T-1348 AND NOT ACTED ON (2026-09-19).** Both bear on
rulings in this epic's territory and both are left here rather than spent, because a merge
ruling is not a seating ticket's to reopen.

- **`green_j` carries, as printed, "Major, 5th Infantry, commanding the post"** — the American
  of 27 May – 13 June 1835, via the newspaper gazetteer. The T-1291 ruling held `green_j` and
  `greene_john` distinct at D7, and one of its stated reasons was that "Major John Greene is
  Andreas and the fort literature, with **no letter-list or poll reading at all**" — the anchor
  on the wrong side of the fold. This printing is on the other side: a press reading, in the
  scene year, carrying the command itself. It does not overturn D7 — the 1835 poll roll is
  still on the Green side, and a serving major on a town poll roll is what the ruling refused —
  but the ruling did not weigh it.
- **`wilcox_d`, printed 4 February 1834, falls inside DeLafayette Wilcox's gap.** The commandant
  chronology in `docs/RESEARCH/fort_dearborn.md` has DeLafayette Wilcox in command to 18
  December 1833 and again from 16 September 1835, with Greene between; a "D Wilcox" at Chicago
  in February 1834 sits inside that interval, where an officer of the post who was not
  commanding it would be. One notice, an `inferred` soldier's trade and an `uncertain`
  presence — so T-1348 refused it on presence whatever the identity is.

The evidence for both is set out in `docs/RESEARCH/fort_dearborn_garrison_1835.md` § 4.
