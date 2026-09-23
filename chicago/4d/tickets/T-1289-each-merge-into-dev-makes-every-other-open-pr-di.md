---
id: T-1289
title: Each merge into dev makes every other open PR dirty, so N pull requests cost N-squared lap-and-gate rounds
state: open
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Every merge into `dev` moves the base, which makes every other open pull request `dirty` —
GitHub reports it conflicting because its server-side merge never runs this repo's merge
drivers (T-0857). So each merge costs a lap over every remaining PR plus a full gate on each
new head, and only then can the next one merge. With N pull requests waiting that is N rounds
of N laps and N gates.

**Measured on 2026-09-17.** Draining six pull requests took four laps and, at two gates per
push (T-1288), roughly forty gate runs of about ten minutes each. Every one of the four
remaining PRs went `dirty` twice in forty minutes purely because other PRs merged, with
nothing wrong in any of them.

Three things would each cut it, and they are independent:

1. **Merge the whole clean set before lapping.** `merge-ready` already loops over the open
   PRs, but each merge it makes invalidates the next one it looks at, so it merges one and
   reports the rest as `needs-a-lap`. If it merged every PR that was `clean` AT THE START of
   its pass — they were all mergeable against the same base — one lap would follow instead of
   one lap per merge. The risk is real and has to be faced: two PRs clean against the same
   base can still conflict with EACH OTHER, so a merge that GitHub refuses must stop the pass
   rather than be forced.
2. **A fast lane for pull requests that change only `chicago/4d/tickets/`.** Those carry no
   scene, no derived layer and no renderer, and today they run the whole 439-step suite —
   #1408 and #1411 both did. A path-filtered gate that runs `ticket.mjs check` and the
   changelog contract alone would turn a ten-minute round into seconds, and this project
   files a lot of tickets.
3. **GitHub's own merge queue**, which is built for exactly this and would replace the
   hand-rolled lap-then-merge cycle. Weigh it honestly against T-0857: the queue builds each
   candidate on the tip, and if its merge still does not run this repo's drivers it buys
   nothing.

**Acceptance:** pick ONE of the three, state why the other two were not taken, and measure
the same drain before and after — number of laps, number of gate runs, wall-clock from first
merge to empty queue. A change here that is not measured is not this ticket, because the
whole complaint is a cost.
