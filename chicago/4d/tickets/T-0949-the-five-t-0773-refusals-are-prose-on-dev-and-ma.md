---
id: T-0949
title: The five T-0773 refusals are prose on dev and machine-checked only on a closed branch: the corner-crossing guard, REFUSED_ANCHOR_KINDS and the declared refusals never landed
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-11
pr: 1151
claimed_by: run 9/11/2026, 4:45:32 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T22:26:25.937Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34650613262
---

**Found by T-0927, 2026-09-07,** checking PR #962's claim against `dev` before closing it as
the self-declared duplicate of the landed #959. The claim is true, so the gate it names is a
gate nobody has.

#959 landed the T-0773 ruling — seven houses whose printed address a later printing
outranks — and wrote the five refusals as **prose**, in
`docs/RESEARCH/outranked_printed_addresses.md`. #962 wrote the same five as **declarations a
tool checks**. None of that machinery is on `dev`:

| what #962 holds | on `dev` |
|---|---|
| `identity.json` § `refused_anchor_changes` — the five refusals as data | absent (0 occurrences) |
| `compile_gazetteer.py` § `REFUSED_ANCHOR_KINDS` — the enum a refusal's `kind` must be one of, with a failure when it is not | absent |
| `compile_gazetteer.py` self-test — *"a REFUSAL re-placed the house it refused to re-place"* | absent |
| `compile_register.py` — the corner-crossing guard: a `street` resolution whose whole reach is crossed by a `corner` in the SAME window is not a second landmark, with two self-test cases (a street the window's corner does cross; one it does not) | absent |
| `measure_placement_silence.py` — `ruled_by` / `refusal_kind` on each row and the three-way split of the outranked population into ruled / declared-refused / waiting on a judgement nobody has made | absent |

The corner-crossing guard is the sharpest of these because it fires on a live case: G.
Spring's office is printed as 'the corner of Franklin and South Water streets' four times
and as 'Franklin and South Water streets' once, on 1834-05-28, where only the word 'corner'
is missing so the `CORNER` pattern never fires — and the register then calls one place two
places. #959's landed text says the gate "refused the rule outright" and describes excusing
the window by hand; #962 makes the excuse a rule with a test.

**The three structure records** `recon_1835_blk_randolph_dearborn_d3_15`,
`recon_1835_blk_randolph_dearborn_h1_14` and `recon_1835_south_c3_040` carry the declared
refusal on #962 and carry nothing about it on `dev`.

**Acceptance:**

1. The five T-0773 refusals exist as data a tool reads, not only as prose, and a refusal
   whose `kind` is not one of the declared kinds fails the gate.
2. The corner-crossing guard lands with both of its self-test cases — the one that must
   pass and the one that must still refuse — and G. Spring's window resolves as a corner.
3. `measure_placement_silence.py` reports the outranked population split three ways, and
   the "waiting on a judgement nobody has made" count is stated as a number.
4. `bash tools/check.sh` green, and nothing in the town moves as a side effect: this is a
   gate, not a re-placement. Any record that does move is reported, not folded in.
5. PR #962's branch is the source. It is closed, not deleted; take the code from it rather
   than rewriting it from this description.

**Links:** T-0773 · T-0440 · T-0927 · T-0948 · PR #959 (landed) · PR #962 (closed,
branch `steward/t-0773-anchor-changes-seven`).
