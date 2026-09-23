---
id: T-0301
title: Every visible ticket at the top of the queue is parked on hold or in flight, and five straight invisible runs merged under it
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: the held PRs it names (#418, #456, #432) were closed on 2026-09-05
needs_bake: false
closed_at: 2026-09-10T04:20:11.590Z
claimed_run: null
---

Every visible ticket at the top of the queue is parked on hold or in flight, and five straight invisible runs merged under it.

AGENTS.md § THE VISIBLE-PROGRESS RULE caps the loop at **one invisible run in any four**, and
names the tell: an entry opening *"Nothing you can see changed today"*. On 2026-08-28 the last
**five** merged entries open with it — v331, v332, v333, v334, v335 — and this run's own entry
makes six. The rule says the next run MUST be visible and that the exemptions do not extend the
cap.

**The cause is not the ordering, and that matters, because the rule's remedy assumes it is.**
AGENTS.md's remedy is *"if everything at the top of the queue is invisible ... pull a visible
parcel up"*. The top of this queue is not invisible. It is visible and UNAVAILABLE:

| row | ticket | why a run cannot take it |
|---|---|---|
| 1 | T-0028 build out the next anonymous block | PR #456, labelled `hold` |
| 2 | T-0192 the cross streets' street edge | PR #418, labelled `hold` — `balanced` 16,196 triangles over its ceiling with Market in |
| 3 | T-0219 the heightfield south to Madison | PR #432, labelled `hold` |
| 4 | T-0096 the fort's flagstaff | PR #466, in flight this batch |
| 5–8 | T-0258…T-0261, the four newspaper reading passes | in flight or a sibling slice's row; research, not a screenshot |
| 9–11 | T-0262…T-0264 | `blocked_on` the four reading passes above, in writing |

So the first row a displaced run can actually claim is row 15, and rows 12 onward are the
measurement-and-gates band by the owner's own ordering. **Five invisible merges is what that
arrangement produces**, and it will keep producing it for as long as three visible tickets sit
parked. Filed rather than routed around, because an agent may not reorder QUEUE.md — that is the
owner's, and it is the right rule.

**The three `hold`s are not equivalent and should not be cleared as a batch.** T-0192's is a
measured refusal with the number in the PR body (the triangle ceiling, T-0146/T-0209/T-0247), and
it merges the day the budget is won back. The other two want reading before they are judged.

**Acceptance:** the visible band at the top of QUEUE.md contains at least one ticket a run can
claim on the day it looks — by the owner clearing or re-ranking the parked rows, or by the loop
being told in writing what to do when the whole visible band is unavailable, which the
visible-progress rule does not currently say. Whichever it is, it is written where the next run
will meet it, in AGENTS.md beside the cap.

**Links:** T-0192 (PR #418) · T-0028 (PR #456) · T-0219 (PR #432) · T-0156 (the run that hit
this) · AGENTS.md § THE VISIBLE-PROGRESS RULE · `tickets/README.md` § the owner orders the queue.
