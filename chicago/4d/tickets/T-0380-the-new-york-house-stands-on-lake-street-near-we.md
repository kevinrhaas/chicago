---
id: T-0380
title: The New York House stands on Lake Street near Wells, and the American dates its opening
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0306
opened: 2026-08-29
closed: 2026-08-29
pr: 536
claimed_by: run 8/29/2026, 7:12:42 AM CT
blocked_on: null
needs_bake: false
---

The New York House stands on Lake Street near Wells, and the American dates its opening.

Piece 1 of 3 of **T-0306 — The American names six Chicago storefronts with usable placements and none of them is standing in the model yet**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Why this piece is first.** Two of the parent's six give their address as *the New York
House* and nothing else — Dr. J. B. Barnard, physician, "at the New York House, Lake
street" (American, 13 June 1835), and J. C. Bradley, the travelling dentist, "his office
at the New York House, where he will remain until after the Land Sale" (American, 13 and
20 June 1835). `tools/compile_register.py` refuses both with the same sentence: *"The
anchor 'the New York House' names nothing the committed town holds."* The anchor is the
block. Standing it is what makes those two placeable, and it is visible in its own right.

**And the building is already this project's own retracted mistake.**
`data/exclusions.json` carries `new_york_house` under a reason that begins "EXCLUSION
FALSIFIED 2026-08-11" — Andreas p. 635 has it "built in 1834 and opened to the public the
following year by Lathrop Johnson and George Stevens". That entry says in its own words
that it "stays here only until a structure record replaces it", and names the open
question as the OPENING MONTH in 1835. The American closes that question from the other
side: professional offices are advertised AT the house on 13 June 1835, seventeen days
before the scene date, so the house was open and letting rooms by then. The exclusion has
stood retracted-but-unbuilt for eighteen days.

**Acceptance:**

- `data/structures/new_york_house.json` stands the house on the north side of Lake Street
  near Wells, per Andreas — two storeys, frame, **eaves to the street** — with the
  placement derived from the committed Thompson lot on that frontage and every invented
  value graded and noted.
- `data/exclusions.json`'s `new_york_house` entry is discharged the way its own text says
  it should be, pointing at the record that replaced it rather than being deleted.
- Barnard and Bradley are carried on the record as documented occupants with their
  citations (publication, issue, column) and the quotes their address rests on.
- `docs/RESEARCH/new_york_house.md` holds the reading, including the drloihjournal 1836
  date this project is departing from and why.
- `docs/LIBERTIES.md` carries the invention: the footprint, and the choice of lot within
  "near Wells".
- Every gate green — `tools/check.sh` and the renderer smoke — the GLB baked from the
  record rather than hand-authored, and `site/chicago/4d/` republished.
