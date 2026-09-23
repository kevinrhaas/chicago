---
id: T-1005
title: Seven cards are flagged letter_list_only while carrying press readings that are not letter lists — Chas. H. Chapman carries three
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-13
pr: 1289
claimed_by: run 9/13/2026, 6:00:52 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T00:07:04.476Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34788257430
---

Seven cards are flagged letter_list_only while carrying press readings that are not letter lists — Chas. H. Chapman carries three.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**FOUND ON THE WAY PAST T-0990 COHORT C1**, which had to overturn the flag by hand to
rule CHAPMAN CHARLES H.

`letter_list_only` is not decoration. The residents renderer prints a whole paragraph off
it — *"Only from the post office's lists of uncalled-for letters … it is the weakest
evidence this project accepts for a resident"* — and the land-sale ruling rule reads it as
the written form of its own refusal test (cohort B: *"six refused cards are marked
`letter_list_only` … look for it first"*). A card carrying the flag while ALSO carrying
ordinary press readings tells a visitor, and the next run, the opposite of the truth.

Seven cards do:

| person | non-letter-list press readings |
|---|---|
| `chapman_chas_h` | **3** — Democrat 26 Nov 1833 (`#c008`), Chicago American 24 Dec 1833 (`#c010`), Democrat 13 Aug 1834 (`#c012`) |
| `fitzgerald_thos` | 1 |
| `simons_e` | 1 |
| `neff_r_a` | 1 |
| `murray_alonzo` | 1 |
| `ambrose_joshua` | 1 |
| `bradford_harriet` | 1 |

The test is one line: a person is `letter_list_only` only if every row of
`press_evidence[]` has `list: "newspaper_letter_list"`.

**Acceptance.** The flag agrees with the evidence on all seven — either cleared, or the
press row shown to be a letter list read under the wrong `list` — the card notes that say
"KNOWN ONLY FROM THE POST OFFICE" are corrected with them, and the rule is a GATE in
`check.sh` so an eighth cannot arrive. Note the flag is spent by
`tools/mint_civic_residents.py`, so the repair belongs where that writes it, not on the
card by hand.

**Links:** [[T-0990]] (the ruling that found it) · [[T-0992]] · [[T-0837]].
