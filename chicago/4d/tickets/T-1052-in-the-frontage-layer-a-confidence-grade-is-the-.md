---
id: T-1052
title: In the frontage layer a confidence grade is the only thing keeping street furniture off an unoccupied invented building, because the hitching rule deliberately omits the anonymity clause the signboard rule applies
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-14
pr: 1320
claimed_by: run 9/14/2026, 6:53:06 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T12:19:29.000Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34840138482
---

In the frontage layer a confidence grade is the only thing keeping street furniture off an unoccupied invented building, because the hitching rule deliberately omits the anonymity clause the signboard rule applies.

Found by **T-0230**, which was asked whether `physicians_office.function.confidence`
was under-graded and answered that it cannot be upgraded at all — the trade is the
argument that raised the roof, not a reading of one. Writing that answer down exposed
what the grade is holding up.

`tools/generate_business_signboards.py` refuses a frontage on TWO independent clauses:
clause 1, the record is an anonymous slot (`inf_`/`recon_` id, or a name beginning
"Reconstructed"), and clause 3, the trade is not held on evidence.
`tools/generate_frontage_works.py` imports clause 3 verbatim and **deliberately does not
copy clause 1**, and says so in writing at `EDGE_HITCH_ALONG`:

> Note that the signboard rule's OTHER exclusion — an anonymous slot has no name to
> paint — does NOT apply here and is deliberately not copied: a post carries no
> lettering. The clause that bites is the trade's grade, not its anonymity.

The reasoning is sound on its own terms — a post is furniture, not a sign — but it
leaves the hitching rule with ONE clause where the signboard rule has two, and that one
clause is a confidence field on a data record. `physicians_office` is refused a board by
BOTH clauses and refused a post by only the grade. Its occupant was retired to anonymous
stock on 2026-09-02 (T-0516): the roof stands, and nobody is in it. So a grade change on
one JSON field — exactly the change T-0230 was opened to consider — would stand a post
for a stranger at the door of a building this project invented and that nobody occupies,
and no second clause would catch it.

**The question is which of two things is true**, and it is the owner's kind of question
because it is about what furniture means rather than about a bug:

1. a post at an anonymous slot is fine as long as the TRADE is evidenced — the slot
   stands for a real trade the town had, and the furniture dresses the trade rather than
   the name — in which case the omission is correct and the single clause is the whole
   rule, and this ticket closes by saying so and by naming the grade as load-bearing; or
2. furniture of any kind belongs only at a frontage somebody can be said to have kept,
   in which case `_edge_hitching` needs its own anonymity clause — refusing in writing
   like every other clause in that generator — and the count of posts is stated before
   and after.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- One of the two readings above is adopted, in writing, at `EDGE_HITCH_ALONG` where the
  present reasoning stands — not by deleting the paragraph quoted above but by answering
  it.
- If reading 2: `_edge_hitching` refuses anonymous slots by name, every refusal says
  which clause refused it, and `data/frontage/town_street_edge.json` re-derives with the
  post count stated before and after. If reading 1: no code moves and the paragraph gains
  the sentence that says what the grade is holding up.
- No named, evidenced frontage loses a post either way. `bash tools/check.sh` green. No bake.

**Links:** T-0230 (found it) · T-0194 (stood the posts) · T-0516 (retired the occupant) ·
`tools/generate_frontage_works.py` § EDGE_HITCH_ALONG clause 3.
