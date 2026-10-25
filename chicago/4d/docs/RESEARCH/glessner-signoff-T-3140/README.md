# T-3140 — Glessner's photographic sign-off

The last Glessner photo ticket (owner, 2026-10-25: "Full rule, close 5 now"). After T-3136's
reading, T-3137 (gable light), T-3147 and T-3148 (stable end) and T-3143 (pigeon holes, #1312),
six readings were still `open` across the twelve match records, and eight records read
`differs`.

**Acceptance, stated before the work:** every match record reads `matches` with nothing open;
what is under the 1 ft bar, or rests on one camera's fit, is ruled `within tolerance` with what
was read (T-3153); anything over the bar is fixed in this PR; the discrepancy register's
`final_acceptance` is written, saying what is attested and what is inferred, with the courtyard
and rear faces reviewed. No follow-up ticket.

## Ruled within tolerance

| record | what | why |
|---|---|---|
| HABS 01 | the stable's coping apex, 1.0-1.5 ft low | this print's doorway fits only; the record gives that reading 1.5 ft either way, and the stable-fitted cameras carry nothing open there |
| HABS 13 | the gable pairs' light widths and jambs | 0.25-0.5 ft on the lights; the jambs ride on a camera this one print cannot part from the plan |
| HABS 16, Taylor 2135 | the Prairie pair's north light and pier | 0.3-0.5 ft, under the bar; the drift is HABS 16's scale |
| HABS 17 | the 18th Street stack's proportion | a camera 8 px off the stack; two other prints put the junction 0.3-0.8 ft off |

## Fixed: the window over the great arch

Looking at each side-by-side again turned up one difference over the bar that no reading had
named. The window over the great arch on 18th Street was built as three lights between two
stone piers. Every picture that shows it has one opening under one lintel:

- `great-arch-window-cornell-c1887.jpg`: the c. 1887 Cornell print (top), unglazed, the house just
  finished, against the old render (bottom);
- `great-arch-window-habs01-1963.jpg`: HABS photograph 1, a sash of small panes about eleven
  lights wide in two rows;
- `great-arch-window-habs15-1965.jpg`: HABS photograph 15, the same sash.

Three pictures across 78 years make it attested. That is the wrong number of openings, which is
over the bar, so it is fixed here rather than left in the register. It is rebuilt as one opening
on its old span (W 97.7-110.1) and heights. Re-rendered through HABS 01 at 4x, its jambs stand
within about 5 px of the print's. The sash is the kit's (`L-glessner-great-arch-window-3140`).
Glessner was rebaked (`bake.sh --only glessner_house`'s build and derivative steps), and all
twelve views were re-rendered and looked at again.

## The register

`../glessner-final-comparison-T-2228/discrepancies.json` stands on master `ad7c9ce4…`, with
nothing open. `final_acceptance` is `true`, and its `acceptance` block says what is attested,
what is inferred and what is within tolerance, and how the courtyard and rear faces were
reviewed.

    node tools/image_gate.mjs --structure glessner_house   # every reference view matches
