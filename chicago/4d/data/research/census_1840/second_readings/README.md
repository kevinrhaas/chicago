# Second readings

Page files read INDEPENDENTLY of the reading committed in `../pages/`, kept verbatim so that a
disagreement between two readings of the same sheet is a thing that can be examined rather than a
thing that was lost when the second PR merged. Nothing downstream reads this directory; `coverage.json`
and the census README point at it where a second reading exists.

| file | printed page | read by | committed reading | disagreement |
|---|---|---|---|---|
| `33S7-9YYJ-9M5.json` | 229 | the run that claimed T-0534 (PR #698, its first commit) | T-0550, PR #697 | 20 of 30 lines' cells; footings read differently in columns 1, 6 and 14 |
| `33S7-9YYJ-38.json` | 231 | the same run | T-0550, PR #697 | 25 of 31 lines' cells; footings read differently in columns 15, 18 and 20 |

The names agree on every line of both. The cells differ systematically (see the census README,
"a second reading of 229 and 231"). A file here is superseded, not corrected: when a reconciliation
lands in `../pages/`, say so in that page file's `cells_note` and leave this one as it was read.
