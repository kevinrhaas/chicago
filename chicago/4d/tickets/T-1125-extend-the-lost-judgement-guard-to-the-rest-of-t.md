---
id: T-1125
title: Extend the lost-judgement guard to the rest of the hand-authored evidence in data/research/, one domain's arrays adjudicated at a time
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0999
opened: 2026-09-14
closed: 2026-09-14
pr: 1327
claimed_by: run 9/14/2026, 9:41:09 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T15:15:56.621Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34856777109
---

Extend the lost-judgement guard to the rest of the hand-authored evidence in data/research/, one domain's arrays adjudicated at a time.

Piece 2 of 2 of **T-0999 — Nothing in the gate can see a ruling that is simply GONE: a smaller resident_rulings.json is a legal one, and #1055 lost forty judgements under a green check.sh**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

T-1124 guards ONE file, and the shape of the problem is general: this repository's
hand-authored evidence files are all append-mostly — rulings, the trade-census spend rulings,
the newspaper trade classes, the card merge crosswalk, `docs/LIBERTIES.md`, the smoke register
— and every gate it has re-derives DOWNSTREAM of them. A derivation cannot see a shrinking
input; it just derives less. `tools/dev-smoke-state.json` got a merge driver for exactly this
reason. The rest did not.

T-1124 ships `tools/check_rulings_not_lost.py` with a REGISTRY at the top of it — one entry per
guarded file, naming the arrays that hold judgements and the fields that identify one — so the
mechanism is already general and what is missing is the READING. That reading is the work here,
and it is why this is not one run: each candidate file has a different notion of what a
judgement is and what a legitimate shrink looks like, and a count over the wrong arrays is a
gate that cries wolf until somebody deletes it.

Candidates found on dev 2026-09-14 (`grep -rl 'hand_authored\|do not hand-edit' data/research/`):

    data/research/books/trade_census_1835_spend_rulings.json      classes_ruled, practitioners, institutions, documented_absences
    data/research/newspapers/trade_class_rulings.json
    data/research/residents/card_merge_crosswalk.json
    data/research/residents/town_card_candidates.json
    data/research/residents/scene_window_trade_audit.json
    data/research/church/st_marys_baptisms_crosswalk.json
    data/research/directories/fergus_1839_lots_corrections.json
    data/research/land_sales/school_section_sale_1833.json
    data/research/newspapers/place_vocabulary.json

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- each file taken one at a time, with the arrays that hold a JUDGEMENT named and the ones that
  hold a derived or transcribed list left out, and the reason for each written down;
- a file whose arrays are legitimately re-derivable is REFUSED entry to the registry with that
  stated, rather than added for completeness;
- every added file gets its own self-test fixture the way land sales has the #1055 commits, and
  the refusal fires on a tree with an entry removed;
- `check.sh` stays under its second-scale budget — the guard reads committed JSON only.
