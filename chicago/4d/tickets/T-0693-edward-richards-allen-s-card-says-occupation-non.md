---
id: T-0693
title: Edward Richards Allen's card says occupation none_recorded while the same file quotes him as a druggist twice: say what is known and when, not nothing
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 908
claimed_by: run 9/5/2026, 1:25:32 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T18:53:58.482Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33983763641
---

**The owner, 2026-09-04:** *"and there is evidence in there he is a druggist but that is not in his
person record"* — quoting the block that carries it:

```json
"book_evidence": [
  { "list": "directory_1843",
    "as_read": "Allen, Edward Richards, druggist, Leroy M. Boyce, [now at Aurora, Ill.]",
    "record_id": "f1843_e0192", "describes_date": "1843",
    "source": "fergus_chicago_directory_1843", "rule": "G2b" } ],
```

## The defect, in one file

`hh_allen_edward_richards.json` states the man's trade **three times** and then says he hasn't got one:

| where in the file | what it says |
|---|---|
| `persons[0].book_evidence[0].as_read` | "Allen, Edward Richards, **druggist**, Leroy M. Boyce" (1843) |
| `directories.people[0].occupation_later.value` | "**druggist**, Leroy M. Boyce" — `confidence: attested`, `describes_date: 1839` |
| `persons[0].note` | quotes the 1843 line again |
| **`persons[0].occupation.value`** | **`"none_recorded"`** |

The field a reader and every downstream tool actually reads is the last one, and it is the only one
that is not true. The project knows this man's trade, from two independent directories, nine and
thirteen years after the scene date.

## Why this is NOT "back-project the trade", and must not be closed by doing that

The ratified ladder is right and stays: a trade printed in 1839 or 1843 is evidence about 1839 or
1843. **T-0633 already landed the back-projection rule** for positioning a business from a later
documented address, and this ticket does not reopen it. Nobody is proposing that Allen be given a
druggist's shop in the 1835 scene.

The defect is narrower and entirely about honesty of the record: **`none_recorded` is the wrong
value.** It asserts an absence the file itself contradicts on the next screen. What is true is
"none recorded FOR 1835, and a trade is recorded for 1839 and 1843" — and the note under the field
says exactly that in prose while the value says the opposite.

## The ask

1. **Distinguish "no trade anywhere" from "no trade in the scene window".** A person the project
   holds a dated later trade for should not read identically to a person it holds nothing for. The
   narrow fix is a value that says so (`none_recorded_in_1835`, or `none_recorded` plus a
   `later_occupation` pointer at the `directories` block already in the file) — the shape is the
   implementer's call, but the two states must stop being the same string.
2. **Measure the population first, as a `--report`.** How many person records read
   `occupation.value: "none_recorded"` while their own household file carries a
   `directories…occupation_later` for them? Allen is one; the count decides whether this is a
   one-card repair or a sweep, and it belongs in the PR either way.
3. **Whatever is written stays dated.** The 1839 line is `describes_date: 1839` and the 1843 line
   1843; neither becomes an 1835 claim, and the grade on the 1835 record does not move. The card
   already says this in prose — the ask is that the DATA say it too.
4. Do not delete or weaken the `directories` block. It is correct, it is dated, and it is where the
   evidence should live; the gap is that nothing on the person points at it.

**Done when** no person record asserts `none_recorded` while its own file carries a dated trade for
that person, the report names how many cards that was, and Allen's card reads as a man whose trade
is known for 1839 and unknown for 1835 — which is what the sources actually support.
