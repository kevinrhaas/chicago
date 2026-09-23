---
id: T-0872
title: Eight cards already carry a later trade in the 1835 occupation field, landed before T-0837 gated it
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-10
pr: null
claimed_by: run 9/10/2026, 1:16:05 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T06:23:55.791Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34444266608
---

T-0837 gated the synthesizer so a trade may only enter the 1835 `occupation` field out of a
source whose own `describes_date` covers 1835. The gate is a WRITE gate: it stops a new
promotion, and it leaves alone what earlier runs already committed. Running the gated writer
over the tree names eight people whose 1835 trade would be refused if it were proposed today,
and each of them is standing on the card right now at `confidence: attested`:

| person | 1835 occupation as committed | cited source | that source's `describes_date` |
|---|---|---|---|
| `clarke_h_b` | physician | fergus_chicago_directory_1839 | 1839 |
| `collins_j_h` | attorney | fergus_chicago_directory_1839 | 1839 |
| `elston_daniel` | merchant | chicago_democrat_1833_11_26, fergus 1839, uiuc papers | 1833-11 / 1839 / nineteenth century |
| `kimball_walter` | merchant | chicago_democrat_1833_11_26 | 1833-11 |
| `lampman_henry_s` | brickmaker | chicagology_chicago_brick | 1833 |
| `marshall_j_a` | forwarding_and_commission | fergus_chicago_directory_1839 | 1839 |
| `moore_henry` | attorney | chicago_tribune_1882_04_25, fergus 1839 | 1881-82 / 1839 |
| `stewart_r` | attorney | fergus_chicago_directory_1839 | 1839 |

**Acceptance:** each of the eight is either kept — because a source that DOES describe the
scene window says the trade, and that source is now the one cited — or moved to the
`occupation.later_occupation` pointer T-0693 mints, leaving the 1835 field as
`none_recorded` with the note that says why. Not one is left cited to a volume about a
later year. `tools/synthesize_resident_research.py` prints the list: the refusal branch
that names them is suppressed only because the field is already filled.

Three are not simply late and want a reading rather than a sweep. `kimball_walter` and
`elston_daniel` are cited to a single issue of the Democrat of 26 November 1833 — twenty
months before the scene, close enough that a second notice inside the window may well
exist in the corpus already read. `lampman_henry_s` is cited to an 1833 secondary page
about Chicago brick. The other five are Fergus 1839 and nothing else.

Found while landing T-0837; the write gate is in, so the count cannot grow.

**Links:** [[T-0837]] (the gate) · [[T-0693]] (the later-trade pointer) · [[T-0509]].
