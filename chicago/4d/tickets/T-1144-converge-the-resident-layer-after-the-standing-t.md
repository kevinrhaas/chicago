---
id: T-1144
title: Converge the resident layer after the standing truth tickets: zero synthesis and mint drift, no false Chicago resident, and no 1835 claim above its dated evidence
state: split
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-15
closed: 2026-09-18
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T19:57:45.318Z
claimed_run: null
---

Converge the resident layer after the standing truth tickets: zero synthesis and mint drift, no false Chicago resident, and no 1835 claim above its dated evidence.

**Measured on `dev`, 2026-09-15.** A fresh resident synthesis would change 150 files although
`synthesis_drift_baseline.json` is empty. The documented and letter-list mint checks would change
41 and 798 files respectively, but `check.sh` invokes `synthesize_resident_research.py --check`
under both labels instead of the passes whose output the labels promise. A green generic synthesis
therefore does not mean either cohort agrees with its derivation.

This is the convergence pass, not a second ticket for each source-reading question. It consumes
the standing truth tickets after they land: T-1129 (four Bear Creek people are not Chicago
residents), T-1115 (uncertainty brackets), T-1121 (Leonard C. Hugunin), T-1136 (presence brackets),
T-1137 (one writer deleting another's findings), T-0662/T-0691 (the two mint drifts), and T-1145
(dated roles, which supplies T-0991's honest home for pre-scene occupations). If one is still open,
do not re-decide it here: state the dependency and leave this ticket open.

**Acceptance:**

1. Run all three writers against throwaway copies, review their exact diffs, and make the
   committed resident layer a fixed point: synthesis drift 0, documented-mint drift 0 and
   letter-list-mint drift 0. Do not bless drift with a nonzero baseline.
2. Correct `check.sh` so each label invokes its own writer's `--check`/drift contract. A self-test
   changes one output of each writer and proves the matching gate fires.
3. Rebuild away Mary Durbin, John Simmons, John Vincent and Cery Logdson unless a new independent
   Chicago source is committed; no resident may rest solely on church readings whose
   `at_chicago` values are all false.
4. Apply the bracket, name and writer-ownership repairs from T-1115, T-1121, T-1136 and T-1137
   through the generators, never as hand edits. Re-run every affected presence and identity rule.
5. `audit_scene_window_trades.py --check` reaches zero after T-1145: a pre-scene or later role may
   remain dated on the person, but it cannot call itself an attested 1 July 1835 occupation.
6. Rebuild `index.json`, sidecars, town census, published residents and the final resident audit;
   the closing report gives the exact household/person/grade deltas and names every retired id's
   redirect. Relevant resident and ticket gates pass.

**Owner review, 2026-09-17 — added acceptance** (the owner asked that the research-spend tickets
be reviewed and enhanced before the reconstruction bands below them run):

7. The convergence report names, per person, which of the plural `roles[]` (T-1145) and which
   home/work/other locations (T-1147) reach 1 July 1835, so the sign-off ticket T-1157 can read
   coverage per axis off one table rather than re-deriving it.
8. The `reconstructed` grade stays at zero in this ticket and the three writers refuse to emit it:
   reconstruction begins only at T-1167 under its own programme file, never inside a mint.
9. Every household `present_on_scene_date: uncertain` keeps the dated evidence leg that made it
   uncertain (the last appearance and its date) as a structured field, because T-1159 classifies
   the 893 uncertain presences by that date.

**Stop condition:** the three resident derivations agree byte-for-byte with the tree and every
standing confirmed false/overstated resident assertion has either moved or gained new evidence.

**Links:** T-0660 · T-0662 · T-0691 · T-0838 · T-0991 · T-1115 · T-1121 · T-1129 · T-1136 · T-1137 · T-1145.


## IT WAS FOLDED INTO T-1157 AND THE GATE REFUSED IT (2026-09-17)

Same refusal as T-1241, and the same invariant. `research_spend_ledger.py` holds that *a
unit may only defer to work that is still going to happen*, and unresolved research units
name THIS TICKET BY ID as the work they wait on. Closing it as folded made those units defer
to finished work, and `measure_research_spend.py --check` failed on every one.

**A ticket that research units defer to by id cannot be consolidated away** — not without
repointing every unit that names it, which is a bigger and riskier change than a shorter
queue is worth. That is the real constraint on tightening this band, and it is worth knowing
before anyone tries again.

**The tightening that DOES apply:** run this in the SAME PASS as T-1157 and T-1241. The drift
checks here are the sign-off report's evidence section, not a separate expedition, and one run
produces all three.


## ACCEPTANCE 8 IS DONE, AND THE TICKET STAYS OPEN (2026-09-18)

`tools/refuse_reconstructed_grade.py`, gated in `check.sh` as *"no research writer can
mint a reconstructed resident"* with its self-test beside it, and called by all four
writers of `data/residents/` on the way out — `synthesize_resident_research.py`,
`mint_documented_residents.py`, `mint_letter_list_residents.py`,
`mint_placed_residents.py`.

The refusal runs in EVERY mode, including `--check` and `--report`, so a mint is red on
the same rule its write is. What it checks is the **call**, not the import: a refusal
imported and never called is the failure shape it exists for, so `WIRED_WRITERS` names
the exact call each writer must carry and `--check` fails if one goes missing.

What it deliberately leaves alone: per-attribute `confidence: "reconstructed"` — the
`{"value": null, "confidence": "reconstructed", "note": "Not attested."}` block on one
field of a real attested person. That is a statement about a fact, not about whether the
person existed; hundreds of committed records carry it and refusing it would be wrong.
The self-test asserts that distinction directly, so a later tightening cannot quietly
widen the refusal onto it.

Measured before the wiring and unchanged after it: `synthesize_resident_research.py
--check` 1,282 people, 410 attested, 872 inferred, 0 reconstructed; documented mint 39
minted / 96 refused, no drift; placed mint 5 minted / 165 refused, no drift; letter-list
mint the standing 798 (T-0691's, untouched here). Proved end-to-end as well as by
self-test: `mint_documented_residents.record()` was monkeypatched to grade one person
`reconstructed` and `build()` refused all 39, naming each household.

This was the one acceptance clause that does not wait on anything — and it is the one the
bands below need FIRST, because T-1167 is what turns the grade on. The boundary is now one
line per writer to see, and the reconstruction generator T-1167 brings simply does not
call it.

**Why the ticket is still open.** Acceptance 1 is not reachable today: letter-list-mint
drift is 798 files, that drift is T-0691's, and T-0691 is `blocked-tech` behind T-0660 —
which is still `open` at row 2 of the queue. Per this ticket's own rule, that dependency
is stated rather than re-decided here. Acceptances 3 and 5 are satisfied on `dev` and were
re-measured today: Mary Durbin, John Simmons, John Vincent and Cery Logdson hold no
household or person record, and `audit_scene_window_trades.py --check` reads 0 standing
rows and re-derives. Acceptance 2 was closed by T-1228 except for the letter-list slot,
which is acceptance 1's blocker again. What remains for the convergence run is 1, 2's last
slot, 6, 7 and 9 — and the note above still holds: take it in the same pass as T-1157 and
T-1241.

`claimed_by` is cleared with this, and the `claim/t-1144` marker released: nobody holds
this ticket.


## ACCEPTANCE 9 IS DONE, AND THE TICKET STAYS OPEN (2026-09-18, second pass)

`tools/derive_presence_evidence_leg.py`, gated in `check.sh` as *"every uncertain
presence carries the dated evidence leg under it"* with its self-test beside it, and
carried through all four mints by `tools/resident_mint_carry.py`.

820 uncertain presences, 820 legs, **779 of them dated**: 733 a dated reading of the
person, 43 the far end of a cited source's SPAN, 3 an arrival bound, 41 no date at or
before the scene date. The leg is derived from the blocks the card already holds —
`press_evidence`, `civic_evidence`, `book_evidence`, `church_evidence`,
`census_evidence`, `profile_facts`, `letter_list_returns`, `roles[]`, `arrival` — and
never from prose.

**The tiers are the honesty, and they are asserted.** A sighting outranks a span even
when the span reaches further, because the role's own note says that bound is the
source's and not the man's: a Democrat run covering 1833-11 to 1835-08 is not a sighting
in August. And a reading is NOT clipped to the scene date — a source that says `1835`
does not say which half, so `reaches` stays 1835-12-31, `includes_scene_date` is true,
and the card states that it pins no last sighting before the day. 102 legs are in that
position. Clipping them would have been a confidence upgrade by arithmetic, which is
the thing this field exists to prevent; the self-test holds both rules.

**The field may not outlive the verdict.** A leg is written only under `uncertain` and
removed when the presence is settled — `--check` holds both halves, and
`resident_mint_carry.py --self-test` proves a mint that now derives `present` does not
get the leg back.

`tools/export_borderline_roster.py` was the reason to do this: its
`last_dated_appearance()` reached into `present_on_scene_date.note` with a regular
expression, which found a date on the handful of notes that happened to print one and
fell back to the arrival bound for the rest. It reads the derived field now — one
implementation — and each R1 row carries `describes_date` (the source's own words),
`dated_evidence_reaches` (the comparable day) and `dated_evidence_includes_scene_date`.
T-1159's 814 R1 rows are 773 dated where they were a scattering before. The resident
card prints the leg under the presence row and names which of the three kinds it is.

**Why the ticket is still open.** Acceptance 1's letter-list slot and the last slot of
acceptance 2 are one and the same, they are **T-1222's** — read that ticket, it holds
the measurement — and they are not a hand's turn: `mint_letter_list_residents.py
--check` reports 798 files, of which 648 differ in nothing but the five keys the
synthesis owns, 81 are households the mint no longer derives, 54 are ids the name
splitter now mints differently and 14 are genuinely mint-owned. T-0662 read that drift
and found byte-identity to be the WRONG CONTRACT for a pass that is not the last writer
of its files; the shape it wants is T-1228's field-level ownership settlement, and
`data/research/check_gate_baseline.json` carries the row saying exactly that. It is
re-measured and unchanged today, and this pass did not make it worse.

Acceptances 6 and 7 remain, and they are a pass of their own: 7 is a per-person table
of which `roles[]` and which locations reach 1 July 1835, and this ticket's leg is the
presence axis of it — `days_before_scene_date` and `includes_scene_date` are the two
columns that axis needs, so 7 now has one of its three axes derived rather than
re-argued.

**A WARNING PAID FOR HERE.** `node tools/ticket.mjs restamp T-1144` does not re-stamp a
ticket's dates — it RENUMBERS it, and it renumbered this one to T-1305 mid-run. That is
the one edit this ticket's own tombstone note forbids: research units defer to T-1144 BY
ID, and `measure_research_spend.py --check` fails on every one of them the moment the id
moves. It was reverted in the same minute (the `site/` mirror is generated and
gitignored, so nothing escaped). To leave this ticket open with its claim released, edit
`claimed_by` and `claimed_run` by hand, as the pass before this one did.

`claimed_by` is cleared with this: nobody holds this ticket.


## ACCEPTANCE 7 IS DONE, AND THE TICKET STAYS OPEN (2026-09-18)

`tools/report_convergence_coverage.py`, gated in `check.sh` as *"every person says which
roles and which places reach the scene date"* with its self-test beside it, writing
`data/research/convergence_coverage.json.gz` (1,288 rows, one per person) and
`docs/RESEARCH/convergence-coverage-2026-09.md`. Listed in `tools/derived_manifest.json`
so a lap that rebuilds roles, the reconciliation or the register rebuilds this join too.

**It re-decides nothing.** Every reach flag is COPIED from the derivation that owns it — a
role from `roles[].covers_scene_date` (`derive_resident_roles.py`), a home or a workplace
from the reconciliation's `resolved`-at-`scene_date` grading, a business premises from the
firm's own `present_at_scene_date`. The step sits below all three in `check.sh` for that
reason: a drift here means one of those layers moved and the join was not rebuilt with it,
never that this file formed a second opinion. The `later_home_address` and
`later_workplace_address` kinds can never reach the day, by construction rather than by
measurement, which is why the reconciliation holds them as separate kinds at all.

**The verdict vocabulary is three-valued, deliberately.** Per person per axis: `reaches`
(at least one claim reaches the day), `limited` (claims, none reaching — a preserved
refusal with a date on it) and `none` (the corpus says nothing). The queue's own header
holds that zero unclassified research does not mean forcing uncertain people into 1835, so
these may not be totalled. The trap is the reconciliation's `no_claim` home row: all 1,258
households carry one, and 1,186 of them say the corpus places that household nowhere.
Reading those as `limited` would manufacture a gap out of the project's own honesty; the
self-test asserts the distinction directly, so a later change cannot quietly lose it.

Measured on this branch: 1,288 people in 1,258 households. `roles[]` 138 reach / 189
limited / 961 no claim; home 34 / 67 / 1,187; work 72 / 0 / 1,216; other places 93 / 128 /
1,067. Two people are reached by all four axes, 1,093 by none. Underneath: 687 dated role
rows of which 160 reach the day (the sign-off's own figure, unchanged), and 1,719 location
rows carried to a person of which 225 reach it. Section 2 of
`docs/RESEARCH/research-signoff-2026-09.md` now points at the table — that section counts,
this table names, which is what acceptance 7 asked for.

**What is still open here.** Acceptance 1's letter-list leg is T-1222's 798-file drift and
is not re-decided here; acceptance 6's closing rebuild and deltas remain. Acceptances 3, 5
and 9 measure clean on this branch (no Mary Durbin, John Simmons, John Vincent or Cery
Logdson; `audit_scene_window_trades.py --check` reports 0 standing rows; all 820 uncertain
households carry their `last_dated_appearance` leg), but they are left to the closing pass
to state as deltas rather than claimed closed from a spot reading.


## ACCEPTANCE 6'S REDIRECT LEG IS DONE, AND THE TICKET STAYS OPEN (2026-09-18, third pass)

Acceptance 6 asks the closing pass to *name every retired id's redirect*. The table that
does the naming — `data/residents/index.json`'s `merged` — turned out to be the one list
in the manifest that nothing re-derived, and it had drifted in both directions. A report
written over it would have reported the drift as fact, so the table is derived first.

`tools/rebuild_resident_index.py` now derives `merged` and `counts.merged_away` from the
`merged_into` block of each record under `data/residents/merged/`, exactly as T-0715 put
`households` and `counts` on the cards. The existing gate step re-derives it; the existing
self-test proves each new refusal fires.

**The two drifts it found on `dev`, both repaired by re-derivation and neither by hand:**

1. **`hh_vanderbogart_h` had a record and no row.** Folded onto `hh_vanderbogart_henry`
   under T-0842 (rule C7, the particle rule — Vanderbogart against Vandenbogart), and left
   out of the table, so the id resolved to nothing. Its own note says "data/residents/
   index.json's `merged` table redirects the id", which is the failure sitting inside the
   record that promised it could not happen. 65 redirects become 66.
2. **`hh_blanchard_gantry` was carried under `C7`, and its record says `C8`.** The record
   is right and the table was stale. T-0993 minted C8 *for this fold* — "A MIDDLE NAME IN
   FULL, STANDING ALONE, WHERE A SOURCE PRINTS THE SAME MAN BOTH WAYS", C6's shape with the
   initial replaced by a word — and `card_merge_rulings.json` carries `"rule": "C8"` on the
   ruling itself and calls it "the `blanchard` cluster's C8 merge" where it rules the
   Blanshards distinct. C7 today is the compound-surname rule, a different argument about a
   different kind of name, so the table sent a reader to reasoning that was not this fold's.

**A TALLY THAT RE-DERIVES CAN STILL BE A DEAD END,** so the gate asks a second question:
does each redirect ARRIVE? `redirect_faults()` refuses a `merged_into_household` that is no
household card, a `merged_into_person` in no card, a redirect pointing at another retired
card, a retired id that is also a live one, and a row missing any of its fields. Measured
on this branch: all 66 arrive, no chains, no id both retired and live. The refusal runs in
`--write` as well as `--check`, because writing a dead end publishes it.

**What was deliberately NOT touched.** Two prose fields in `card_merge_rulings.json` still
say "C7" for the Blanchard fold — the ruling's `for:` opens "C7, AND THE TOWN'S OWN
DIRECTORY PRINTS THE NAME WHOLE", and the `also_ruled_on` note says "folds onto
`blanchard_f_gantry` under C7". They are the ticket's own words written while the letter was
being minted, the structured `rule` field beside them already says C8, and editing an
authored reasoning field to tidy a letter is the kind of retroactive smoothing this project
refuses. They are named here instead, which is where a reader who follows the citation will
now land.

**Why the ticket is still open.** Acceptance 6's other half — the closing rebuild with the
exact household/person/grade deltas — is the closing pass, and acceptance 1's letter-list
leg is still T-1222's 798-file drift behind T-0691/T-0660, unchanged and not made worse
here. `rebuild_resident_index.py --check`, `town_census.py --check` and
`export_resident_audit.py --check` all re-derive on this branch (1,258 households, 1,288
people, 371 buildings standing of 668, 1,288 audit rows), so the layers acceptance 6 names
are fixed points today; what remains is the report that states their deltas, and it wants
the letter-list leg under it first.

`claimed_by` is cleared with this: nobody holds this ticket.


## AND NOW IT IS SPLIT, AFTER THE SECTION ABOVE (2026-09-18)

The section above was written by the run that closed acceptance 6's redirect leg, and it
ends "the ticket stays open". That was right when it was written. This one supersedes it:
**T-1144 is split, not open**, and the two things it says are left are exactly the two
children.

Seven passes have closed acceptances 4, 7, 8, 9 and acceptance 6's redirect leg, each on
its own PR. What is left does not fit one more run, and it is not one question:

**T-1333 — the closing convergence rebuild.** Acceptance 6's other half, in the words the
section above uses for it: "the closing rebuild with the exact household/person/grade
deltas". Acceptances 3, 5 and 9 measure clean today but were deliberately left "to the
closing pass to state as deltas rather than claimed closed from a spot reading" (the
2026-09-18 second pass, above), so they are banked here and stated by the same rebuild.

**T-1334 — the letter-list mint's drift and the one-letter-apart identity rule.**
Acceptance 1, and the last slot of acceptance 2. The section above names the blocker
itself — "acceptance 1's letter-list leg is still T-1222's 798-file drift behind
T-0691/T-0660" — and that drift is read by T-1222, not by this layer's closing pass.

**WHY THE SPLIT HAPPENS NOW RATHER THAN AT THE END.** One research unit defers to this
ticket by id: `identity_open_one_letter_apart` in `data/research/spend_rulings.json`, whose
statement is "the convergence ticket owns mint drift and false residents". Under the T-1237
rule a unit cannot defer to spent work, and a split parent whose children have all closed
IS spent work — so had T-1144 been split on the day its last child landed, that unit would
have been stranded in the same breath. It is repointed to **T-1334** with this, which is
the child that actually owns mint drift.

The line is left `unresolved` and **open**, not `blocked`: `blocked` is not in the ticket
system's `WORKABLE` set, and a unit whose owner is unworkable is a strand wearing a
different word.

`claimed_by` is cleared: nobody holds this ticket, and nobody should — the children are
where the work is.
