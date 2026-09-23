---
id: T-1383
title: The two women the St Mary's priest wrote down as Indigenous are the only adults on their own entries the borderline roster ruled ineligible, so the town carries their husbands and children and not them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-21
pr: 1614
claimed_by: run 9/21/2026, 2:02:52 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T08:19:52.867Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35570784801
---

The two women the St Mary's priest wrote down as Indigenous are the only adults on their own entries the borderline roster ruled ineligible, so the town carries their husbands and children and not them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1376, 2026-09-19, while reading the corpus for Native and Métis people the
sources NAME.**

`data/research/church/records/st_marys_baptisms_1833_1835.json` is the only source this
project holds in which a contemporary STATES an Indigenous identity for a named person at
Chicago — not a term in a later biography, the priest's own parenthesis on the page. Four
entries of 1833 carry one:

| entry | the words | people |
|---|---|---|
| 7 (at Ottawa, not Chicago) | *"of Ottaway"* | Francise Nowbonnois, Josette Ashkam |
| 14 | *"Marianne (sauvage)"* | wife of Antoine Aspam |
| 17 | *"Marianne (sauvage)"* | the same woman, second child |
| 18 | *"Jaespquaa (sauvage de Green Bay)"* | wife of Paul Vieaux |

The reading's own note on entry 14: *"'Sauvage' is his word for an Indigenous woman and it
is kept in as_read because it is the register's own vocabulary; it is not this project's."*
Entry 18 carries the only origin the book ever gives for a mother.

**The defect.** The borderline roster carries every other adult on those entries — Antoine
Aspam (twice), Josette Aspam (twice), Paul Vieaux, Jacob Vieau, and the children Jean
Baptiste, Magdelene, Susanne and Marie Josette — and T-1172 minted four of them into
`data/residents/readmitted/`. It does NOT carry **Marianne** or **Jaespquaa**: both sit in
the roster's `ineligible` list, normalised to `marianne` and `jaespquaa`. So the town holds
these two families' husbands and their children and not the two women the priest wrote down
as Indigenous — and the four cards that ARE in the town carry `community: null`,
`touches_removal: false` and no kinship to each other, though the register puts the whole
family on one dated line.

**Why T-1376 filed it rather than spending it.** A baptism is not a residence, and the
ineligibility ruling is the RESEARCH layer's, not a reconstruction stage's to overturn from
outside with a one-line patch — the roster is generated, and a stage that hand-edited its
output would be un-derivable by the next run. The honest fix is in the roster's own
eligibility rule, and it wants its own demonstration.

**What it should answer.** Why the two readings are ineligible (a forename-only name? the
parenthesis? something else — the `ineligible` rows carry a `rule` key and the reason should
be read, not guessed); whether the rule is right in general and wrong here; whether the
Aspam and Vieaux cards should be one household each rather than one person each, since the
register states the kinship on one line; and whether those cards should carry
`review_required` + `touches_removal` and a community, which they do not today. Stage
`underdocumented` (T-1177) is the only stage licensed to write the last of those.


## WHAT IT ANSWERED, 2026-09-21

**Why the two readings were ineligible.** Not the parenthesis and not a ruling about
them — `R0_ineligible/surname_only_and_unmatched`, the roster's rule 9, which refuses a
name whose normalised form is a single token as "a surname and no person". `Marianne`
and `Jaespquaa` are mononyms, so the rule caught them. It is the rule that reads LAST of
the ones that could have applied, and the reason it was reached at all is the answer
below.

**Whether the rule is right in general and wrong here.** Neither, as it turns out: the
rule should never have been reached. R6 — the Native/Métis/Black class — is rule 4, five
rules ABOVE it, and it sits there deliberately ("an evidence limit must never be the
reason a community goes unbuilt", the owner on T-1177). It did not fire because
`COMMUNITY_TERMS` is an English word list and the priest wrote `sauvage`. Measured on the
committed roster before this change: the `church` domain contributed **zero** rows to
R6. The one source this project holds in which a contemporary states an Indigenous
identity for a named person at Chicago was invisible to the class built for exactly that.

So the fix is a second, stricter R6 rule rather than a loosening of rule 9. Rule 9 stands
untouched, and its 254 remaining rows are a real finding, handed on below.

**Why the term is not simply added to `COMMUNITY_TERMS`.** That list is read over
`words_of(unit["record"])`, and `entry_as_read` is carried by EVERY row of an entry.
`sauvage` appears 23 times in the register file for three entries. A shared-text match
would have credited Antoine Aspam, Paul Vieaux, Jacob Vieau, four children and five
sponsors and godparents — Augustin Bonné, Monique Nodeau, Joseph Beaubien, Jean Baptiste
Lavigne, Josette Aspam — with a community the priest wrote about one person. That is the
careless reading `NOT_A_COMMUNITY` exists to prevent, run the other way.

`NAME_BORNE_COMMUNITY_TERMS` is therefore read only where the term FOLLOWS the row's own
name — the clerk's parenthesis as he printed it. Attachment is the guard, in place of the
recall the shared-text list can afford. `NOT_A_COMMUNITY` is struck first, so an office
carrying a community word cannot be read as one even in a parenthesis.

**Measured.** Exactly four rows move, all four the two women; twelve sibling rows on the
same three entries are credited with nothing and stay `R2_in_window_single_source`.

| | before | after |
|---|---:|---:|
| `R6_native_metis_black` | 139 | 143 |
| `R6` from the `church` domain | 0 | 4 |
| `R0_ineligible/surname_only_and_unmatched` | 258 | 254 |
| roster offered | 1,812 | 1,816 |

**What happened when the rows reached T-1177's stage — and the second defect.**
`reconstruct_underdocumented.py` withheld all four as
`the_term_is_prose_and_not_a_statement`, whose own words are "a word in a paragraph is
not a statement by the source about this person's community". That is FALSE of these four:
the term is written onto the name, which is the same stage's own test for "the source's
own structure says it". A card stating a false reason for a true refusal is the
provenance defect this project does not round off, so the stage now tells the truth about
them: `the_statement_is_not_on_the_roll_this_stage_reads`. Nothing is minted and no card
moves — that stage reads the 1832 muster roll and a baptismal register is not on it.
The two women are out for want of a READER, not for want of evidence.

**Not done here, and why.**
- *One household each rather than one person each.* Not attempted. The register does
  state the kinship on one dated line, and T-1335 is the family pass that owns exactly
  that handoff — every one of these rows already carries T-1335 in its `ledger_reason`.
  Doing it from here would be a second stage inventing a join a named stage owns.
- *`community`, `review_required` and `touches_removal` on the four cards already in the
  town.* Still not written, and still correct that they are not: stage `underdocumented`
  is the only stage licensed to write them and it cannot reach these rows. That is now a
  stage that does not exist rather than a rule that refused them.

**Findings handed on.**
- **A register reader.** Four R6 rows now stand refused only because no stage reads the
  church register. Filed as **T-1504**.
- **Rule 9 still mis-names what it refuses.** 254 rows carry "The reading gives a surname
  and no person". Five of them are not surnames: `Matanacqua` and `Lieu[?]` (mothers,
  1833 entries 8 and 6), `Miranda` (a father, 1835 entry 3) — each named as a parent of a
  NAMED child on a dated line — and `John . . .` (a decedent) and `Bourrasso` (a witness),
  which are forenames and surnames clipped by the page. The refusal is right for all five;
  the sentence is wrong for the first three. Filed as **T-1505**. No source gives any
  of them a community term, so none of them is R6 and none is touched here.
