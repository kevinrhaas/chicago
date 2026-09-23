---
id: T-0699
title: Six men on the 1835 poll AND other lists are graded "the 1835 poll alone", and nothing has ever applied a regrade to an existing card: fix the test, add the convergence rung, spend it
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 817
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T01:15:26.204Z
claimed_run: null
---

**The owner, 2026-09-04:** *"if the letter list places someone as likely there, and then there are
voter records, and then other records later, then that is fairly strong attestation route that they
are a real person… can we change or improve the grading system for these people like this with
multiple sources that are identifying them there in and around 1835?"* And, naming the pair:
*"like to me alone these two sources together would be attestation —
`chicago_democrat_1833_1835`, `chicago_voter_lists_1833_1835_irad`."*

**He is right, and this ticket exists because the first review of his question pushed back on it and
was wrong.** The objection raised was that the ladder grades by CLASS and not COUNT, and that a
count rule would make a man attested on two 1843 directory entries. That conflated two different
things: the *number of appearances* and the *convergence of independent classes*. Two 1843 directory
entries are one class, one era, possibly one lineage. The town's own poll list and the town's
newspaper are two different bodies recording the same man in the same window, and that is not the
same claim at all. The measurement below is what settled it.

## FINDING 1 — six men are graded on a false description of their own evidence

`grade()` reaches `G1a` (**attested** — *"The 1835 poll list and at least one other independent
source"*) only when:

```python
if POLL_1835 in classes and len(sources) > 1:
```

`sources` is the set of **`source_id`s** — archival provenance. Every Chicago poll, tax and muster
list in this project was digitised by IRAD and carries the single id
`chicago_voter_lists_1833_1835_irad`. So a man on the 1833 tax list, the 1834 poll AND the 1835 poll
has `len(sources) == 1`, misses `G1a`, and falls to **`G2a` — *"The 1835 poll list alone."***

That description is **factually untrue of the record it is applied to**. Willard Jones:

```
civic: tax_1833  | Jones, Willard | source: chicago_voter_lists_1833_1835_irad
civic: poll_1834 | Jones, Willard | source: chicago_voter_lists_1833_1835_irad
civic: poll_1835 | Jones, Willard | source: chicago_voter_lists_1833_1835_irad
   grade: inferred | rule: G2a  ("The 1835 poll list alone")
```

Three lists, taken in three different years, by the town, of who could vote and who paid tax. **They
are three independent records.** That one archive published them together is a fact about the
archive, not about the evidence. Under the ladder **exactly as the owner ratified it** these six are
already `G1a`, attested — no rung needs inventing:

| | in-window records | graded |
|---|---|---|
| Willard Jones | tax 1833 · poll 1834 · poll 1835 | G2a |
| Peter Pryne | tax 1833 · poll 1834 · poll 1835 | G2a |
| Ira Kimberly | tax 1833 · poll 1835 | G2a |
| John Foot | tax 1833 · poll 1835 | G2a |
| Dexter Hapgood | poll 1833 · poll 1835 | G2a |
| Edmund L Kimberly | poll 1834 · poll 1835 | G2a |

**This half is a defect fix, not a policy change**, and it should land first and separately.

## FINDING 2 — the ladder cannot express convergence at all

`grade()` is a **first-match cascade**: it asks "does any ONE class reach this rung?" and stops. It
never asks "do several independent classes agree?" So Edward Richards Allen —

| record | date | body that made it |
|---|---|---|
| `poll_1834` | 1834 | the town's electors |
| Chicago Democrat letter list | **1835-05-20** | the town's newspaper |
| Fergus directory | 1839, 1843 | a commercial directory |
| Tribune, Old Settlers' reception | 1882 | the Calumet Club, criterion = Chicago before 1840 |

— reaches `G2b` and stops, and would reach `G2b` on two of those four just as well. **Four
independent bodies naming one man across 1834 → 1835 → 1843 → 1882 grade identically to two.** That
is the gap the owner is pointing at, and no ruling on the letter list alone closes it.

## What is measured

Over `data/residents/households/` on dev, 2026-09-04:

| | |
|---|---|
| people graded `inferred` | 922 |
| …on the 1835 poll **plus** another in-window record (Finding 1) | **6** |
| …with 2+ distinct in-window classes but no 1835 poll (the Allen shape) | **14** |
| …carrying **both** the Democrat and the IRAD voter lists — the owner's named pair | **17** |
| of those 17, carrying no `ladder_rule` at all | 6 (T-0692's population) |

**Roughly twenty people.** Not the ~1,500 the letter-list-as-G1b reading would have moved — because
this rung asks for CONVERGENCE, not for a letter list to be promoted on its own. That distinction is
what makes it safe.

## The ask

1. **Fix `G1a`'s independence test.** Independence is a property of the RECORD — a distinct list,
   taken on a distinct occasion, by a distinct body — not of the `source_id` that digitised it.
   Count distinct `(list, describes_date)` records, not `source_id`s. The six above become `G1a`
   under the existing rung and no new policy is needed.
2. **Add a convergence rung — `G1c`, attested.** Two or more independent in-window records **of
   different class families**, naming the same identity. The families are: the town's civic lists
   (poll/tax/muster), the contemporary press (the 1833-35 papers, letter lists included), and the
   parish register. Allen qualifies on civic + press. **A letter list is not promoted on its own** —
   `G2e`/`G3` still hold it down alone — it only counts toward convergence, which is precisely the
   owner's reading: *"the letter list places someone as likely there, AND there are voter records."*
3. **`G0` SURVIVES UNTOUCHED.** Later evidence never constitutes attestation by itself. Allen's 1843
   directory and 1882 reception corroborate and date; the two in-window records are what earn the
   rung. A man with four later sources and nothing in-window stays `not_1835_resident`.
4. **Independence must be defined before it is counted**, or convergence becomes an artefact:
   - nine printings of one letter list are ONE record, not nine — T-0318, T-0424, T-0428 are the
     tickets that establish which printings are the same list;
   - the same man minted twice from two printings is one identity, not two — that is T-0660;
   - the identity merge must be sound first, or two men wrongly merged manufacture their own
     corroboration. `crosswalk.json`'s refusal rules already govern this and are the gate.
5. **Land it as a proposal.** `consolidate_resident_evidence.py --build` prints proposed changes
   without writing household files; the regrade is a separate PR with before/after counts and the
   twenty names listed, each checkable by hand. At this size they should be checked by hand.

## FINDING 3 — nothing applies a regrade to a card that already exists

**Found by asking the owner's own follow-up: "so what will this fix them going forward and the
existing ones?" The honest answer is going forward only, and that makes findings 1 and 2 invisible
until this third piece is built.**

The write path, traced:

| tool | what it does |
|---|---|
| `consolidate_resident_evidence.py` | computes the grade, writes `grading_proposal.json`. Its own docstring: ***"It writes NO household file."*** |
| `mint_civic_residents.py` | reads the proposal and mints a person **"for every identity … that the town does not already carry"** |
| anything that applies the proposal to an EXISTING card | **does not exist** |

Those two tools are the only readers of `grading_proposal.json` in the repo. So a card, once written,
is never revisited. **Fixing `grade()` corrects what is PROPOSED; Willard Jones stays `G2a` for ever.**

**And there is already a backlog proving the gap is real, independent of this ticket.**
`docs/RESEARCH/resident-grading-policy.md` records that the ratified ladder
***"moves 159 of 849 people — 19 up, 63 down, 77 subtype only"***, and then, in the same section:
***"It is a proposal. No household file was changed by this pass."*** Those 159 have been unspent
since 2026-09-03. The ~20 this ticket finds would land on top of them.

This is the same shape as the hop `tools/measure_research_spend.py` measures one layer up — research
RULED but never ON A CARD, which read 109 reached and 0 written on 2026-09-03. The computation gets
done; the spend never happens. It is the owner's original complaint of this session, one layer down.

## The ask — part (c), and it is the half that a visitor can see

6. **Build the regrade pass.** A tool that reads `grading_proposal.json` and applies it to the
   household records that already exist — the piece between the proposal and the card. It carries
   the same shape every other pass here has: `--build`, `--check`, `--report`, `--gate`,
   `--self-test`.
7. **UPGRADES APPLY. DOWNGRADES DO NOT.** The standing proposal holds **63 downgrades**, and demoting
   sixty-three residents unattended is not a thing a run may do. A downgrade goes to a conflict list
   with its reason and its evidence, for the owner, exactly as `consolidate_resident_evidence.py`
   already lists its 77 conflicts rather than resolving them. An upgrade is safe because it is the
   ladder finding MORE evidence, never less.
8. **Reconcile the 159 first, and separately.** They predate this ticket and are not its work; the
   ~20 found here must not be smuggled in beside them. Land the 159 as its own pass with its own
   before/after counts, then this ticket's twenty on top, so each set can be read on its own.
9. **A regrade must show its working on the card.** When a person moves rung, the record says which
   rung it came from, which it went to, what evidence moved it and on what date — the same way
   `directories…occupation_later` already carries its provenance. A grade that changes silently is
   how the layer got into a state where 742 of 825 households cite one source and nobody noticed.
10. **The gate that keeps it honest.** Extend `measure_research_spend.py`, or write its sibling, so
    the distance between *what the ladder proposes* and *what the cards carry* is a reported number
    with a ratchet — the same instrument that caught the research-to-card gap. Without it this
    backlog silently rebuilds the moment the next pass runs.

**Done when** no person record is described by a rung that contradicts its own evidence blocks,
`G1c` exists with its independence rule written down, **the twenty are regraded ON THEIR CARDS and
not merely in a proposal**, the 159 standing changes are reconciled or listed, every downgrade is a
conflict for the owner rather than an applied demotion, and
`docs/RESEARCH/resident-grading-policy.md` carries the owner's words and the date.
