---
id: T-0638
title: A trailing middle initial took the surname slot, so 19 letter-list households are named 'The C household' and can never match a directory
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 778
claimed_by: run 9/4/2026, 6:19:12 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T11:58:27.587Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33867101519
---

A trailing middle initial took the surname slot, so 19 letter-list households are named
"The C household" and can never match a directory.

**Filed on the owner's instruction of 2026-09-04**, after the queue re-rank surfaced
`"Perry A. 8."` with the id `8_perry_a`: *"go ahead and file it and land it in a logical
location in queue."*

## Where it comes from

`tools/mint_letter_list_residents.py`'s `surname()` reads the LAST token as the family name
when the printed string has no comma:

```python
def surname(name: str) -> str:
    parts = words(name)
    if "," in name:
        head = words(name.partition(",")[0])
        return (head[-1] if head else parts[0]).lower().strip("'")
    return parts[-1].lower().strip("'")          # <- this line
```

That is right for `Joel C. Mills`. The post office's lists also print **surname first with
no comma** — `Mills Joel C.` — and then the last token is a middle initial. The bad surname
then propagates into three places at once: the household **id**, the household **name**, and
the person's **display name**, which is why a card reads `Mills Joel C.` rather than
`Joel C. Mills`.

## Fault A — the trailing initial. 19 households, and this is the one that blocks work.

| id | household name | person, as the card shows it | should read |
|---|---|---|---|
| `hh_8_perry_a` | The 8 household | Perry A. 8. | A. 8. Perry |
| `hh_a_mason_sabrina` | The A household | Mason Sabrina A. | Sabrina A. Mason |
| `hh_b_merrich_j` | The B household | merrich J. B. | J. B. Merrich |
| `hh_c_mills_joel` | The C household | Mills Joel C. | Joel C. Mills |
| `hh_e_hhelps_theodore` | The E household | Hhelps Theodore E. | Theodore E. Hhelps |
| `hh_f_mabbet_benjamin` | The F household | Mabbet Benjamin F. | Benjamin F. Mabbet |
| `hh_h_norton_wm` | The H household | Norton Wm. H. | Wm. H. Norton |
| `hh_ii_preston_stephen` | The Ii household | Preston Stephen II. | Stephen II. Preston |
| `hh_is_bobinson_george` | The Is household | Bobinson George IS. | George IS. Bobinson |
| `hh_k_pugsley_john` | The K household | Pugsley John K. | John K. Pugsley |
| `hh_l_pixley_john` | The L household | Pixley John L. | John L. Pixley |
| `hh_p_clapp_a` | The P household | Clapp. A. P. | A. P. Clapp |
| `hh_r_norton_n` | The R household | Norton N. R. | N. R. Norton |
| `hh_s_page_elisha` | The S household | Page Elisha S. | Elisha S. Page |
| `hh_t_orinsbey_martin` | The T household | Orinsbey martin T. | Martin T. Orinsbey |
| `hh_v_regera_john` | The V household | Regera John V. | John V. Regera |
| `hh_w_oakley_benjamin` | The W household | Oakley Benjamin W. | Benjamin W. Oakley |
| `hh_wm_nelts` | The Wm household | Nelts Wm. | Wm. Nelts |
| `hh_es_jones_high` | The Es household | Jones, High Es | see Fault C |

Two more carry the same fault in a different token: `hh_abbot_8_g` (`8. G. Abbot`) and
`hh_gabbs_james_i1` (`James I1. Gabbs`) have a sound surname and a mangled initial, so their
ids are already right — they belong to Fault C only.

Also: `hh_i_mcloud` (`McLoud I.`), `hh_g_willinm` (`Willinm G.`) and `hh_o_ranwin`
(`Ranwin O.`) are the same shape but have no forename at all in the printing.

**WHY IT BLOCKS THE SPEND.** Every crosswalk in this project matches on surname first —
`fergus_1843_crosswalk_1835.json`'s rule is literally *"Surname 'Gould' folds to the same
string as the 1843 entry's"*. A household whose surname is `c` cannot fold to `Mills`. So
these 19 are structurally unmatchable by T-0632, T-0515 and every future crosswalk, and no
amount of further reading will reach them.

## Fault B — the `M'` prefix, split by the slug. 8 households, ids only.

`M'Clintock`, `M'Dolold`, `M'Ewen`, `M'Fadin`, `M'Grigg`, `M'Kean`, `M'Lean`, `M'Vaughton`
(and `P'aylor`). The apostrophe in the period's Scots and Irish prefix is not alphanumeric,
so `slug()` cuts it and the id becomes `hh_m_clintock_thomas`. **The household name and the
display name are CORRECT here** — only the id is wrong, and eight Scots and Irish surnames
sort under `m`. Milder than Fault A, same one-line cause.

## Fault C — OCR misreads inside the surname. A REGISTER, NOT A FIX.

`Hhelps` (Phelps?), `Bobinson` (Robinson?), `Willinm` (a forename in the surname slot),
`Orinsbey` (Ormsby?), `Merrich` (Merrick?), `Regera` (Rogers?), `Ranwin` (Rankin?),
`M'Dolold` (M'Donald?), `Nelts` (Welts?), `Conkiin` (Conklin?), `Jones, High Es` (a run-on
of two entries?), `8.` and `I1.` as initials.

**Do not correct these.** Each is a reading judgement and this project does not invent
readings. Several of these lists were printed nine times (T-0318, T-0424, T-0428) and the
right repair is a cleaner impression, not a guess. This ticket's job is to WRITE THE LIST
DOWN with the printing each came from, so a later pass working the page images has a
worklist instead of a hunt.

## A false positive to leave alone

`hh_st_cyr_john_mary` — *The presbytery household at St Mary's*, Rev. John Mary Irenaeus
St Cyr. `St Cyr` is a genuine two-part surname; the id and the name are both right. Any
tool written here must not "repair" it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. `surname()` learns the surname-first-without-a-comma shape: when the last token is a
   bare initial (one letter or one letter and a stop, a digit, or a two-character
   initial-cluster) and an earlier token is a full word, the surname is the FIRST full
   token. Self-tested against every row of Fault A's table AND against the given-first
   forms it must not break (`Joel C. Mills`, `John Bates Jr.`, `Joshua Hathaway jr.`).
2. `slug()` keeps the `M'` prefix joined — `M'Clintock` → `mclintock`, not `m_clintock` —
   and `St Cyr` still slugs as it does today.
3. The 27 affected households are renamed with **`tools/rename_household_ids.py`**, which
   exists for exactly this and updates `index.json`, the crosswalks, the frozen selector
   scripts, the findings ledgers, the CSVs and the smoke test in one pass. Do not hand-edit
   ids; do not run a mint tool in write mode (it would overwrite the T-0485 enrichment on
   hundreds of unrelated files — the migration plan records why).
4. Household `name` and person display name are corrected with the id, so a card reads
   `Joel C. Mills`.
5. Fault C is committed as a register — one row per name, with the printing, the source id
   and the suspected reading marked explicitly as a SUSPICION, graded nothing.
6. Re-run the crosswalks afterwards and state how many of the 27 newly fold to a directory,
   voter or land-sales surname. If the answer is zero, say zero — the fix is still right,
   and the number is the evidence either way.
7. `bash tools/check.sh` green, and `st_cyr` unchanged.
