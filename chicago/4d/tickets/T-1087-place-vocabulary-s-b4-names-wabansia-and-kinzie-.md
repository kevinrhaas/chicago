---
id: T-1087
title: place_vocabulary's B4 names Wabansia and Kinzie's Addition as surveys this project commits none of, and it commits both: the owner's ruling, at a cost of one person
state: blocked-owner
epic: META
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-09-12
closed: null
pr: null
claimed_by: null
blocked_on: resolution and basis for Wabansia and Kinzie's Addition: both surveys are committed now, so B4's stated reason has expired — outside, inside, or B4 with a new reason? It moves exactly one person in the register.
needs_bake: false
closed_at: null
claimed_run: null
---
place_vocabulary's B4 names Wabansia and Kinzie's Addition as surveys this project commits none of, and it commits both: the owner's ruling, at a cost of one person.

FOUND BY T-1086, 2026-09-12, closing Wabansia's tract outline. This is a ONE-LINE edit to two
fields and it is not the loop's line to write: `resolution` and `basis` in
`data/research/newspapers/place_vocabulary.json` are B-rules, and § boundaries says so.

**What has changed under the rule.** B4's own text reads "a survey adjacent to the town that
this project commits none of (Kinzie's Addition, Wabansia — T-0789, T-0790)". Both surveys are
committed now:

* **Kinzie's Addition** — T-1060 committed its streets. T-0789 is closed (split).
* **Wabansia** — T-1070 seated its seven streets and its block grid; T-1086 seated its
  river-front water lots and closed its tract outline, 78.63 acres, off the same `kinzie`
  datum. T-0790 is closed (split).

So both entries resolve `undecided` on a stated reason that has expired, and the two notes now
say so in their own words. What they do NOT do is move the ruling.

**What the ruling costs, measured rather than feared.** T-1086 named the fear — "moving a place
off B4 changes what counts as a Chicago appearance, which re-scores the register's person
counts". Measured against the committed gazetteer, it re-scores ONE person:

| string | persons naming it | already decided by another place | moved by a re-ruling |
|---|---|---|---|
| `Wabansia` | 1 — `person_uncertain_doctor_kimberly` | 0 | **1** |
| `Kinzie's Addition` | 2 — `person_john_h_kinzie`, `person_mr_rezigue` | 2, both `inside` on `Chicago` | **0** |

`persons_by_bucket` stands at `{inside 1119, outside 141, undecided 25}`. It becomes
`{1119, 142, 24}` if both go `outside`, or `{1120, 141, 24}` if both go `inside`. The string
counts go from `{inside 48, outside 71, undecided 9}` to `{48, 73, 7}` or `{50, 71, 7}`.

The one person is the doctor in the Democrat of 16 July 1834 — a dwelling of four rooms, a
kitchen, a barn and a garden in Wabansia, his name cut at the column's right edge. Wabansia is
the only place the register holds for him, so he is the whole of the re-scoring either way.

**The question, in the owner's terms.** T-1086 read the likely answer as `outside` — both tracts
are adjacent to the platted town, not in it — and refused to write it. Kinzie's Addition's own
note argues the other way for itself and has since T-1048: "a man in Kinzie's Addition was in
Chicago by every contemporary reading and refusing him would be the error this vocabulary exists
to prevent." The two tracts may not want the same answer.

**Acceptance:**

1. `Wabansia` and `Kinzie's Addition` re-ruled — `resolution` and `basis` — by the owner, or
   left on B4 with a reason that is true of the committed ground.
2. B4's own example list corrected to match, if the ruling moves either tract off it.
3. `tools/resolve_place_vocabulary.py --write` re-run so `counts` measures the result, and
   `--check` green in the gate.

**Links:** T-1086 · T-1060 · T-1070 · T-1077 · T-1048 (the vocabulary) · T-0789 · T-0790 ·
`data/research/newspapers/place_vocabulary.json` § boundaries B4
