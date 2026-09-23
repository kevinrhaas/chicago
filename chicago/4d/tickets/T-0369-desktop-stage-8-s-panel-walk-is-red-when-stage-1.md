---
id: T-0369
title: Desktop stage 8's panel walk is red when stage 1 runs before it and green when stage 8 runs alone
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 578
claimed_by: run 8/29/2026, 9:13:23 PM CT
blocked_on: null
needs_bake: false
---

Desktop stage 8's panel walk is red when stage 1 runs before it and green when stage 8 runs alone.

**Acceptance:** the desktop smoke's stage 8 gives the same verdict whether it runs alone or after
stage 1, and the reason for today's difference is written down rather than worked around.

**Measured 2026-08-29 on an UNMODIFIED `dev`** (published mirror, `--published`), by T-0316's run
while establishing whether its own branch was red:

```
SMOKE_VIEWPORT=desktop SMOKE_STAGE=8    → 37 passed, 0 failed   SMOKE PASS
SMOKE_VIEWPORT=desktop SMOKE_STAGE=1,8  → 75 passed, 1 failed
  FAIL desktop 1280x800: the suite body ran to completion
       Error: clickChrome: .panel-tab[data-tab="settings"] is covered at its own centre by <h2>
```

Same commit, same viewport, same target, one command apart. Stage 8 alone reaches the settings tab;
stage 8 after stage 1 finds it covered by an `<h2>` — so a run's verdict on stage 8 depends on which
other stage it was asked for in the same invocation, and the stage split exists precisely so a run
can ask for a subset.

This is the SECOND instance of the shape **T-0349** records ("The signboard gate is red when stage 1
runs before it and green when stage 2 runs alone"), on a different gate. Whatever stage 1 leaves
behind in the page — the panel it opened, a scroll position, a `localStorage` key — is the shared
cause worth finding once. Both tickets should probably be answered by the same repair; whoever takes
one should read the other.

**Why it matters beyond the two gates.** A steward run cannot take the whole desktop gate (T-0346),
so it takes stages — and a subset that is red only because of its own composition costs every branch
an argument about whose failure it is. This run had to re-run `dev` twice to establish that its own
change was innocent.

## Answered 2026-08-30 — a card left standing over the tab strip, and it is not T-0349's fault

Reproduced on this runner against the published mirror of an unmodified `dev`, exactly as filed:
`SMOKE_STAGE=8` 37/0, `SMOKE_STAGE=1,8` 75/1 on `clickChrome: .panel-tab[data-tab="settings"] is
covered at its own centre by <h2>`.

**The `<h2>` belongs to `#popup`, the building inspect card, and part 1 opened it.** `clickChrome`
reported the tag and not its owner, so it now walks up to the nearest ancestor with an id and says
`covered at its own centre by <h2> inside #popup`. Part 1's last page interaction is `boardPick` —
twenty-five `pick()` calls proving that aiming at the Tremont House's signboard opens the business
behind it — and a `pick()` that lands on a structure opens the card. Part 1 never closed it.
`#popup` is `position: fixed; z-index: 30; top: 58px; right: 12px` and 392 px wide; the HUD panel
is 380 px wide at the same corner, so at 1280×800 the card lies on the panel's tab strip. Parts
2–7 read the scene graph rather than chrome, which is why nothing noticed for as long as the split
has existed; part 8 is nothing but chrome and its first statement clicks a tab.

**Repair, at both ends.** Part 1 closes the card it opened and asserts the teardown (`part 1 hands
the page on with nothing standing over the chrome`, over `#popup` and `#control-help`), so the next
leak is named at its own boundary. Part 8 clears the card in the preamble that already re-opens the
panel, so its verdict is independent of every predecessor and not just of part 1. No assertion was
weakened or deleted.

**The shared-cause hypothesis with T-0349 is REFUTED, not inherited.** T-0349's third reading names
its own cause: its seventh clause counts `frontage.meshes === 62`, and a run with stage 1 behind it
carries five extra `frontage-far-merge` meshes the desktop camera's history caused — a census clause
reading a distance-merge artefact. This ticket is an overlay left standing over a control. The two
share the phrase "red after stage 1" and nothing else, so T-0349 still wants its own repair and is
untouched by this one.

**Verification.** `./tools/check.sh` PASS. desktop `SMOKE_STAGE=1,8` 105/0 (was 75/1), desktop
`SMOKE_STAGE=8` 37/0 — the same verdict both ways. mobile `SMOKE_STAGE=1,8` 105/0.

**THE PART NUMBERS IN THIS TICKET ARE DATED (T-0346, 2026-08-30).** Part 4 was cut into
parts 4, 5 and 6 — the scene-detail ladder was 6 m 17 s of a part the ten-minute ceiling was
killing — and the old parts 5-9 are now 7-11. So read this ticket's numbers through
`old 5→7, 6→8, 7→9, 8→10, 9→11`, and old part 4 as new parts 4+5+6. The mobile legs are
`1-2 3-6 7-8 9-11` and carry exactly what they carried. The readings themselves stand; only
the labels moved.


**AND AGAIN, THE SAME DAY (T-0173, 2026-08-30).** Part 7 was halved — the three road-legibility
stations were 7 m 04 s of a part killed at 9 m 25 s — so old part 7 is now parts 7 + 8 and old
parts 8-11 are 9-12. Read this ticket's post-T-0346 numbers through `old 8→9, 9→10, 10→11,
11→12`, and old part 7 as new parts 7+8. The mobile legs are `1-2 3-6 7-9 10-12` and carry
exactly what they carried. The readings themselves stand; only the labels moved.
