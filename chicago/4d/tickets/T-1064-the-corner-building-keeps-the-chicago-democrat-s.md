---
id: T-1064
title: The corner building keeps the Chicago Democrat's name, board and function after the press has left it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-12
pr: 1188
claimed_by: run 9/12/2026, 5:19:58 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T11:07:32.412Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34688023030
---

The corner building keeps the Chicago Democrat's name, board and function after the press has left it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0403**, which moved the press and deliberately left the building alone.

`data/structures/chicago_democrat_office.json` is documented at the corner of South Water
and Clark by the imprint of the Democrat's first issue, 26 November 1833, and it does not
move: a building does not move when its tenant does. What T-0403 established is that the
tenant went. The colophon of 1835-05-20 c007 prints the office *over Messrs. Jones & King['s]
Hard[ware store]* in South Water street, and `identity.json` now declares the change; the
record's occupants line dates John Calhoun's clause `1833-1834`, and
`business_chicago_democrat_printing_office` no longer enriches this building in the register.

Three things are still pointed at a business that is not inside:

    name       "The Chicago Democrat Office"
    aka        "John Calhoun's printing office"
    function   printing_office_and_store  (and with it the sign generator's `trade`)
    signage    data/signage/town_business_signboards.json signs[4] paints
               CHICAGO DEMOCRAT / Printing Office / South Water & Clark Streets
               on this facade, `facade_painted`, 3.11 x 0.98 m

A NAME AND A BOARD ARE NOT THE SAME KIND OF THING and that is the whole question here. A
building keeps the name it was known by — plenty of houses in this town are named for a
trade that has left, and renaming this record would throw away the one fact that makes it
findable. A signboard is different: it is a visible assertion standing in the scene, a
walker reads it as the present tense, and the register no longer agrees with it. So the
board is the part that has to be decided rather than inherited.

AND IT IS NOT A ONE-LINE EDIT, which is why T-0403 filed it instead of doing it.
`tools/generate_business_signboards.py` deals boards by rule and T-0405 records that
changing one repaints every board alphabetically after it, some of them losing a line. So
this is a board change plus a re-deal plus whatever T-0405 turns out to owe.

WHAT THE CORPUS ACTUALLY OFFERS FOR THE REPLACEMENT is thin and must not be padded.
`chicago_democrat_1834_10_08` c005 offers 'the store now occupied by W. Kimball, and as the
office of the Democrat' for sale with possession in November 1834. That is the only word on
Kimball's tenancy, it OFFERS the store rather than reporting it sold, and nothing reached
says whether he stayed — which is why T-0403 left his occupants clause undated. So the
honest candidates are: Kimball's store alone, or a building this reconstruction cannot name
the occupant of on 1835-07-01.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The board on this facade either states something the corpus supports at the scene date,
  or it is not there, and which of those was chosen is argued on the record.
- Whatever the record's `name`, `aka` and `function` end up saying, the reason a NAME may
  outlive a tenancy and a BOARD may not is written once, where the next such building will
  read it — not settled at this one house.
- No confidence is upgraded to make the replacement look better, and no occupant is dated
  in or out beyond what the 1834-10-08 notice actually says.
- T-0405's repaint cost is measured, not discovered: the PR states how many boards the
  change re-deals and whether any loses a line.
- `check.sh` green.

Links: T-0403 (which moved the press and filed this), T-0405 (one board repaints the rest),
T-0411 (the paper and its office are two records).
