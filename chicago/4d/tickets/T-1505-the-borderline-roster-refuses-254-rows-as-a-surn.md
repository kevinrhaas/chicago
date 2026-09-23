---
id: T-1505
title: The borderline roster refuses 254 rows as 'a surname and no person' and three of them are forenames: Matanacqua, Lieu and Miranda are each named as the parent of a named child, so the refusal is right and its sentence is false
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-21
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The borderline roster refuses 254 rows as 'a surname and no person' and three of them are forenames: Matanacqua, Lieu and Miranda are each named as the parent of a named child, so the refusal is right and its sentence is false.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1383, 2026-09-21, which reached this rule and then established that it should
never have been reached for its own two women. It is still reached by 254 rows.

`tools/export_borderline_roster.py` rule 9 refuses a row whose normalised name is a
single token, in these words: *"The reading gives a surname and no person, and no
household of this town carries it; a surname alone names nobody to re-admit."* The
predicate is `surname_only()`, which is `len(normalised.split()) == 1` and nothing more,
so it cannot tell a clipped surname from a mononym forename.

For 249 of the 254 the sentence is true — `Dr. Clark`, `Blinn`, `Whistler`, `HUMFRIES`,
the directory and census clippings, and the marriage rows the register itself prints with
the forename blanked (`_____ Quinn`, `_____ Deigan`, `_____ Cismoinyrkyum`). For five it
is not a surname at all:

| row | the register's words | role |
|---|---|---|
| `st_marys_bapt_1833_08_3_mother` | *"Marie Josette fille de Jacob Vieau et de Matanacqua"* | mother |
| `st_marys_bapt_1833_06_3_mother` | *"John David son of William Dird[?] and [of] Lieu[?]"* | mother |
| `st_marys_bapt_1835_03_2_father` | *"Geneviève Medera fille de Miranda et de [blank]"* | father |
| `st_cyr_death_08_1` | `John . . .` | decedent |
| `st_marys_bapt_1835_03_4_witness` | *"Témoins: L. Chevalier, Bourrasso"* | witness |

The first three are each named as the PARENT of a named child on one dated line: a single
token there is a forename, and the filiation says which person it is. The last two are a
forename and a surname the page clipped, standing alone.

**The refusal is right for all five and this ticket does not ask to overturn it** — the
roster's licence for R2 is to MINT a resident under the read name, and a mononym parent
of a 1833 baptism is not that on this evidence. What is wrong is the sentence: a card
stating a false reason for a true refusal is the provenance defect this project does not
round off (the same fault as T-1395).

**Acceptance:** (state it before working — never weakened to pass)

1. Rule 9 distinguishes a clipped surname from a mononym the reading places in a stated
   kinship to another NAMED person on the same dated line, from the record's own
   `locator.role` / `cells.role` and not from a guess about the name's language.
2. Each gets a refusal that is true of it. The 249 keep theirs word for word.
3. No row changes CLASS: every one of the five stays `R0_ineligible`. If the work
   concludes otherwise, that is a ruling and it goes to the owner rather than into a
   re-cut — `--check` re-derives and the counts are stated before and after.
4. `--self-test` fires on both directions, as T-1383's does.

Note Matanacqua is Jacob Vieau's wife and her name is almost certainly Indigenous, and
this ticket does NOT credit her with a community: no source gives her a term, and
guessing one from the shape of a name is the reading this project refuses. She reaches
R6 only if a source is found that says so.
