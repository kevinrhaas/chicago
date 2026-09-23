---
id: T-1025
title: The directories spend writes the SOURCE onto a card and not the ENTRY, so all 264 of that domain's unwritten rulings are matches that reached a card which cannot say which printed line it rests on
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-13
pr: 1274
claimed_by: run 9/13/2026, 3:33:20 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T21:07:36.374Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34780984463
---

The directories spend writes the SOURCE onto a card and not the ENTRY, so all 264 of that domain's unwritten rulings are matches that reached a card which cannot say which printed line it rests on.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**MEASURED ON DEV AT 19e0f249c**, by a second run that reached T-1018 from the other side and
found its work already landed. The finding is not the repair — that shipped in #1107 — it is
what the repair's ceiling raise was charged to, and the reason recorded against it is wrong.

`tools/research_spend_baseline.json` carries, dated 2026-09-11:

> "…every one of the four new MATCHES was spent onto a card in the same pass (Charles L. Harmon,
> Leonard C. Hugunin, Edmund S. Kimberly, John H. Kinzie). The residue of four is the new
> REFUSALS the repair made visible … and a refusal is not a card's to carry."

**A refusal is never counted by this hop at all.** `count_written()` walks `ruling_lists()` and
skips any ruling whose `outcome` is outside `WRITTEN_OUTCOMES` unless its container is a
`MATCH_CONTAINER`; a refusal is neither. Re-running that walk against dev and printing the
unwritten rulings by hand gives 264 — and **every one of the 264 is a `matches` row**:

    159  fergus_1839_crosswalk_1835.json          matches
     49  fergus_1843_crosswalk_1835.json          matches
     39  norris_1844_crosswalk_1835.json          matches
     17  norris_1844_advertiser_crosswalk_1835.json  matches

The four that moved the ceiling from 260 to 264 are in that list by name —
`hh_harmon_brothers`, `hh_pruyne_kimberly`, `hh_kinzie_john_h`, `hh_hugunin_leonard_c` — the
very four the note says were spent. They WERE spent, and they are unwritten anyway.

**WHY, AND IT IS ONE CAUSE FOR ALL 264.** The write hop has two doors (T-0989). A ruling that
names its own sources is judged against those. A ruling that rests on the FILE's one source id
must ALSO have the card name what the ruling was ABOUT — `subject_of()`, which for these is the
claim id, `n1844_e1031` — because a file-level source id is shared by every ruling in the file
and one citation from any other pass would otherwise pass all of them at once. None of the
directory crosswalks writes a per-ruling `rests_on`, so all 264 go through the softer door, and
`tools/spend_directories.py` writes only `directories.sources += "norris_directory_1844"` and the
person's id. It never writes the entry. The cards that DO pass are the ones a minting pass gave a
`book_evidence` row carrying `record_id` — `hh_knickerbacker_a_v` names `n1844_e1039` and passes;
`hh_kinzie_john_h` is a hand-authored household no minting pass rewrites, and does not.

**So the ratchet is measuring something real, and it is a provenance gap rather than accounting.**
A reader of John H. Kinzie's card is told Norris 1844 met him and cannot find the line.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `spend_directories.py` writes the entry beside the source for every ruling it carries, in the
  shape the cards already hold one — `record_id`, `as_read`, `describes_date`, `source` — and it
  does so for hand-authored households too, which is the whole point.
- Counted before and after: how many of the 264 this clears. Whatever it clears,
  `measure_research_spend.py --tighten directories --hop write --why "..."` reclaims in the same
  PR, and T-1018's raise from 260 comes back down with it.
- The `why` quoted above is corrected in place, or the correction is recorded beside it: a raise
  nobody can re-derive is worse than no raise.
- Nothing is regraded and no 1844 line becomes an 1835 fact — this writes a citation, not
  evidence.
- `bash tools/check.sh` green. No bake.
