---
id: T-0930
title: Empty the hold label: rule on every PR parked for the owner, closing what is superseded and putting the genuine questions in one place
state: done
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-07
pr: 1028
claimed_by: run 9/7/2026, 4:14:23 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T09:38:54.300Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34104583371
---

`hold` means a person is needed. It is not a parking space, and a PR left under it
indefinitely is a decision nobody has made.

Standing: `#1015`, `#1002`, `#978`, `#975`, `#968`, `#962`, `#925`.

**Sort them into three, and empty the label:**

1. **Not actually held.** `#975` and `#962` are self-declared duplicates; `#968` is
   superseded on the rule and refuted on the placement. Nothing in them is waiting on a
   judgement — they belong in T-0927 and should be closed there, with the label removed so
   it stops meaning nothing.
2. **Held on a real question.** `#1015` (an independent reading that disagrees with the
   landed one on line count, pairs and footing) and `#925` (R6, which `#998` now rules on)
   are genuine. **Two readings of one leaf that disagree is a finding, not a stalemate** —
   file the disagreement as its own ticket carrying both readings and what separates them,
   so the question survives whatever happens to the branch.
3. **Held on the owner.** Whatever is left. Put ALL of it in one comment on one PR, each
   item stated as a question with the options and a recommendation — not scattered across
   seven threads he has to find.

**Do not re-close a PR another run has reopened.** #968 was closed, reopened by its own
steward run, and labelled `hold` within two minutes; two agents opening and closing the same
PR at each other is worse than one label and a written record. Where two runs disagree, put
the evidence in a comment and leave the label for the owner.

**Acceptance:**

1. Every PR above is closed, merged, or carries a written question addressed to the owner.
2. The `hold` label means what it says: applied only where a person is genuinely needed.
3. Every disagreement between two readings is filed as a ticket before either branch closes.
