---
id: T-1228
title: Three inferred-household passes still derive the 96 households the owner retired in T-0489, so none of them can be gated: settle what each pass still owns
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1108
opened: 2026-09-17
closed: 2026-09-17
pr: 1392
claimed_by: run 9/17/2026, 6:26:54 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T12:20:10.086Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35215510528
---

Three inferred-household passes still derive the 96 households the owner retired in T-0489, so none of them can be gated: settle what each pass still owns.

Piece 2 of 2 of **T-1108 — Three generators refuse together and none is gated: inf_cooperage_south_branch stands 2.1 m inside the platted Market Street corridor**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Why the parent split.** T-1108 read three tools refusing on one line and concluded "one
ruling makes three gates possible". That is false, and nothing could have known it: in
`generate_inferred_households.py` the corridor check lives in `validate()`, which raises
BEFORE the drift diff runs, so the corridor refusal was standing in front of everything
behind it. T-1227 settled the corridor on 2026-09-17. This is what came out from behind it,
measured the same day:

    $ python3 tools/generate_inferred_households.py --check
    INFERRED HOUSEHOLD PROGRAMME DRIFT
      - 96 household files this pass derives ARE NOT ON DISK
      - 5 more households, data/residents/index.json and 34 structure records have drifted

    $ python3 tools/generate_inferred_names.py --check
    FileNotFoundError: data/residents/households/hh_inf_carpenter_south_01.json

    $ python3 tools/replace_invented_residents.py --check
    5 file(s) differ from what this pass derives

**One cause, and it is an owner ruling.** On 2026-09-02 T-0489 retired the reconstructed
resident population and kept the geometry — "keep as anonymous stock". 96 of the 101
households these three passes derive were removed by it. Nothing told the generators. So
`generate_inferred_households.py` in WRITE mode would put every retired household back and
rewrite the retired roofs' own records — this run watched it try: regenerating
`inf_cooperage_south_branch` whole re-claimed the withdrawn occupant, put `status` back to
`inferred_household` and dropped the `resident_assignment` block T-0489 wrote. Running
these tools is a reversal of a ruling, which is why T-1227 spliced one position block
rather than running the generator.

Two smaller faults ride along and are this ticket's too: `generate_inferred_names.py`
`--check` CRASHES rather than reporting drift (`p.read_text` on a file that may be gone),
and the tree's structure files are 1-space indented while this generator writes 2-space, so
its structure output could not be byte-identical even with the data settled.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- It is written down what each of the three passes still OWNS after the retirement, and the
  tools agree with it: a `--check` that dies on a missing input is not a report, and a
  generator that would revert an owner ruling is not gateable.
- All three `--check` modes are green, and all three are gated in `tools/check.sh` in the
  same commit that makes them green — the parent's ask, unweakened.
- `tools/audit_check_gates.py --write` re-run in that commit, so the ratchet tightens by
  three and the three rows in `data/research/check_gate_baseline.json` go away.
- NO CONFIDENCE IS UPGRADED AND NO RETIREMENT IS UNDONE to get there. If the honest answer
  is that these passes are spent one-shots whose outputs the owner has withdrawn, that is a
  finding and retiring the modes is a valid way to close this — but it is HIS call, so
  `block --owner` it rather than deciding it here.

