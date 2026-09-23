---
id: T-0518
title: The census, voter and research packages are on dev and indexed nowhere: index them and close the publish ask
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-05
pr: 845
claimed_by: run 9/4/2026, 11:59:06 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T05:22:49.160Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33945847348
---

**The owner's concern, 2026-09-03, verbatim:** "I am concerned that there are only adjudicated mappings
through v4 and none other and we did at least 11 slices of residents to get to households but most of
your census work needs to be published, I think. Add any other tickets to queue for this also." Asked
what "published" should deliver, the owner chose (2026-09-03): **"Reference packages + final audit"** —
"Fill the missing chicago/reference/resident-research/ packages for the pilot and passes 2–3, and
deliver the final/audit master XLSX/CSV/README that T-0490 promised and never produced."

**The finding.** **T-0511** and **T-0512** do the two things the owner named. What is left when they
land is that nobody can find any of it: `chicago/reference/` has no index at its root or in
`census1840/`; the v1/v2 workbooks, the 55-name crosswalk, the T-0504 successor, the 1840 page
readings, the voter, church, book and directory domains, fifteen cohort packages and the final audit
sit in eight folders with no page that says what each is, what it may assert about 1835, and which
ticket produced it. The "adjudicated mappings through v4" the owner is counting are, on `dev`, the v1
and v2 workbooks plus #670's 210-row recovery of v4 (v3 and v4 themselves ruled lost — "They are lost;
rebuild" — and rebuilt by **T-0504**).

**The ask.**

1. `chicago/reference/census1840/README.md`: every file in the folder and `validation/` — what it is,
   where it came from (workbook version, ticket, PR), what it may and may not assert about 1835, and the
   fingerprint method in one paragraph.
2. `chicago/reference/resident-research/README.md`: the index table **T-0511** started, completed —
   every package folder T-0442 … T-0510 and `final/audit/`, with ticket, cohort size, outcome counts and
   date.
3. `docs/RESEARCH/census-and-civic-evidence-2026-09.md`: one dossier over the whole sweep — the voter
   lists, 1830, 1840, the baptismal register, the books, the directory — what each supplied, its tier,
   its coverage declaration, its crosswalk counts, and the rule for what it may assert (the ratified
   ladder, by reference to `resident-grading-policy.md`).
4. Confirm the gate still proves nothing under `data/research/` reaches `site/` (it does today; say
   so with the step name).

**Dependency:** T-0517 must be `done`.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Both index READMEs list every file/folder present with counts; the dossier links every domain's
  coverage file; `tools/check_dossier_links.py` green.
- `check.sh` green; nothing under `data/research/` published.

**Links:** T-0511 · T-0512 · T-0504 · T-0513 · T-0517 · PR #670.
