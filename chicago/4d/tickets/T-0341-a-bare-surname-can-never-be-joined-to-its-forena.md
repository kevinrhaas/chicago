---
id: T-0341
title: A bare surname can never be joined to its forename: the family rule reads 'no initials' as 'different initials'
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: null
claimed_by: run 8/29/2026, 11:18:31 AM CT
blocked_on: Superseded by T-0397 (#544) and T-0392. T-0397 made an unread [?] a position rather than an absence, so the three T-0323 readings this ticket wanted to free are [?] cases and belong to T-0392, already blocked-owner on exactly that question. Re-measured after T-0397, the widening this ticket proposed reaches 2 names — Stuart and Patterson — and the same evidence says both must be refused: the page set no forename at all, and Stuart is already a confectioner and a schooner master. No widening left to rule on. The measurement and the un-automatable 'not contradicted' clause are written into the ticket for T-0392.
needs_bake: false
---

A bare surname can never be joined to its forename: the family rule reads 'no initials' as
'different initials'.

`tools/compile_gazetteer.py` refuses a merge when `surname(into) == surname(frm)` and
`initials(into) != initials(frm)`, "with or without a rule (the letter lists are full of
families)". That rule is right and it should stay. But `initials()` returns an empty tuple
for a name with no forename at all, and an empty tuple is not equal to `('a','o','t')`, so
the guard fires on the one case it was never aimed at: joining a bare surname to the SAME
surname with a forename supplied.

**Measured on 2026-08-29 while working T-0323**, by compiling the real corpus with one probe
merge at a time:

| merge probed | verdict |
|---|---|
| `[?] Blodget` → `[uncertain: Avice] Blodget` | refused, "same surname, different initials" |
| `[?] Breed` → `A. O. T. Breed` | refused, same |
| `[?] Devoe` → `[…]nel Devoe` | refused, same |
| `[?] Temple` → `[Lew]is Temple` | refused, same |
| `Lewis Tem[…]` → `[Lew]is Temple` | accepted — because the CUT surname is a different string |

The last row is the tell. A name cut in its SURNAME can be repaired, because the truncation
changes the surname slug; a name cut in its FORENAME cannot, because the truncation changes
nothing the guard looks at. That is backwards: a surname repair is the riskier of the two,
and it is the one the policy lets through.

**What it costs, today.** T-0323 read the third printing of the 1 January 1834 letter list
and closed the readings of four January bare surnames — `[?] Blodget` is A[l]vice Blodget,
`[?] Breed` is [A]. O. T. Breed, `[?] Devoe` is Samuel Devoe, `[uncertain: Dagenet]` is Noel
Dagenet. Two of those four have the completed person already standing in the gazetteer from
another issue, and neither could be declared. The evidence exists, the judgement is written
out, and there is no admissible way to record it — so the gazetteer keeps counting one man
twice, which is exactly T-0299's complaint.

**This is a policy question and not only a code one.** `identity.json`'s own note says the
family rule binds "rule or no rule", so widening it is the owner's call, not a refactor. The
narrowest change that would do the work: allow a merge when one side has NO forename at all
and the other's initials are not contradicted by it — refuse `[?] Cohen` → `P. Cohen` while
`J. Cohen` also stands, and refuse it whenever more than one forenamed bearer of that surname
is in the corpus, which is the family case the rule was written for.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The owner rules on whether a bare surname may be joined to a forenamed bearer of the same
  surname, and on what test guards it. `block --owner` until he has.
- If allowed: `compile_gazetteer.py` implements exactly that test, the self-test carries a
  case per branch — allowed, refused for a second bearer, refused for contradicted initials —
  and `identity.json`'s note states the widened rule in the same words the code enforces.
- The four T-0323 readings above are then declared or explicitly left undeclarable, with the
  reason on T-0318.

---

## WITHDRAWN, 2026-08-29 — T-0397 moved the ground, and what is left is two names that must both be refused

This ticket was measured across the whole corpus rather than the four examples it was
filed on, and the measurement withdraws it. `tools/probe_bare_surname_merges.py` (added by
the same run; a probe, not a gate — nothing in `check.sh` runs it) borrows
`compile_gazetteer.py`'s own `surname()` and `initials()` so it cannot drift from the guard
it reasons about.

**Measured first at `44995edc`, before T-0397 landed.** 2,634 persons, **126** carrying no
forename at all; of those, 18 had exactly one forenamed bearer of the surname and would
have been admitted by the widening this ticket proposed, 51 kept the family refusal, 57 had
nothing to join. Bounded, and it still refused `[?] Temple`, which has twelve forenamed
Temples standing.

**Then T-0397 (#544) landed, and the premise changed.** This ticket's diagnosis was that
`initials()` returns an EMPTY tuple for `[?] Blodget`, so the family guard fires on a case
it was never aimed at. T-0397 fixed the parse: an unread `[?]` is now a POSITION, not an
absence, so `initials('[?] Blodget')` is `('?',)` and not `()`. The merge is still refused —
`('?',)` against `('a',)` — but it is refused for a **different reason**, and that reason
already has its own ticket and its own question in front of the owner: **T-0392**, "may an
unread forename initial be merged with a read one at the same entry of the same list",
`blocked-owner`, under T-0348. All three of the T-0323 readings this ticket wanted to free —
`[?] Blodget`, `[?] Breed`, `[?] Devoe` — are `[?]` cases and are therefore T-0392's, not
this ticket's. (The fourth, `[uncertain: Dagenet]`, is the only Dagenet in the corpus, so it
was never a merge case at all; T-0318's table already says "nothing minted to merge into".)

**Re-measured at `109ef385`, the ticket has two names left and both must be refused.**

| | at 44995edc | at 109ef385, after T-0397 |
|---|---|---|
| persons compiled | 2,634 | 2,628 |
| **carrying no forename at all** | **126** | **71** |
| — exactly one bearer → the widening would ADMIT | 18 | **2** |
| — two or more bearers → the family refusal stands | 51 | 27 |
| — no forenamed bearer at all → nothing to join | 57 | 42 |

The two survivors are exactly the pair the first measurement had already singled out as the
dangerous ones, because in both the page set **no forename at all** — as against the `[?]`
names, where it set one and the reader could not make it out:

- `Stuart` → `Samuel Stuart`. `Stuart` is a **confectioner** AND a **schooner master**, seen
  Oct 1834 – Jun 1835 and not letter-list-only; `Samuel Stuart` is three letter-list mentions
  in Jul 1834. `Stuart` is probably two men before any merge is even considered.
- `Patterson` (Jul 1834) → `Patterson, Daniel W,` (Aug 1835 letter list). Nothing but the
  surname connects them.

**So there is no widening left to rule on.** Every case with evidence behind it is a `[?]`
case and belongs to T-0392; the only cases this ticket's own test would still reach are two
the same evidence says to refuse. Asking the owner a second question here would put a
duplicate of T-0392 on his board.

**One finding worth keeping, and it is recorded here because T-0392 will need it.** The
"not contradicted by the printing" clause cannot be automated. `[?] Conger` is set
`Ca Conger` — two forename letters WERE read and then discarded to `[?]` — while
`n Whitcomb` and `_ Winson` are OCR debris in exactly the same shape. Only a reader can say
which is which, so that clause belongs in `identity.json`'s `merge_rule` prose, where it is
stated and can be read back, and not in a new code guard. T-0392's bounded exception
("no competing letter") is the same clause, and it has the same problem.

Reproduce any of this with:

    tools/probe_bare_surname_merges.py           the counts and the admissible set
    tools/probe_bare_surname_merges.py --all     the 27 refused and the 42 unjoinable too

**Links:** T-0323 (the reading that hit this) · T-0318 (the names waiting on it) · T-0337 and
T-0338 (the same question asked of FIRMS, where the initial rule was deliberately dropped) · T-0299
(the same-list-different-OCR duplicates) · `data/research/newspapers/identity.json`
