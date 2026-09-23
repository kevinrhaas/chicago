---
id: T-1329
title: Spend the 1830 schedule lines, the church register sponsorships and the press notices onto the cards they name, each as a dated bound on a held resident's presence and never more
state: split
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1318
opened: 2026-09-18
closed: 2026-09-18
pr: null
claimed_by: run 9/18/2026, 12:54:27 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T17:58:31.741Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35376396531
---

Spend the 1830 schedule lines, the church register sponsorships and the press notices onto the cards they name, each as a dated bound on a held resident's presence and never more.

Piece 2 of 2 of **T-1318 — Spend the roll-and-appearance units: the 1830 schedule lines, the poll books, the 1833 tax roll, the 1832 Black Hawk enrolment, the church register sponsorships and the press notices, each as a bound on a held resident's presence and never more**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**What this ticket inherited on the day it was made.** T-1326 spent its sibling's corpus and
repointed at this one everything of T-1318's it did not spend, because a hand-off must name the
piece that holds the corpus rather than a split parent:

* 15 units of `data/research/census_1830/spend_rulings.json` — the 1830 schedule lines that
  bound a held resident's presence, and the one surname variant the crosswalk holds as a
  candidate (`tools/spend_name_on_a_roll_rulings.py`, constant `ARRIVAL`).
* 223 units of `a_dated_appearance_bounds_a_presence` — 95 church register sponsorships and
  128 press notices (`tools/spend_remainder_rulings.py`).

238 units, and `measure_research_spend.py` reports them owned here. Only 10 of the 95 church
units and none of the 128 press ones sit on a card today, so unlike T-1326 this is not a
legibility pass: the identification has to be made before a bound can be written, and where it
cannot be made the answer is a refusal in writing, not a fourth deferral.

**The shape T-1326 left to follow.** `persons[].dated_bounds[]`, written by a generator with
`--check`, `--report` and `--self-test`; one row per reading; `bounds`, `describes_date`,
`precision`, `reaches`, `here_by`, `covers_scene_date`, `confidence`, `sources`, and a note
that says what the row does NOT say. See `tools/spend_civic_roll_bounds.py`.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
