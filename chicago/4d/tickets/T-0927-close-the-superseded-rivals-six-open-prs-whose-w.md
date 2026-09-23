---
id: T-0927
title: Close the superseded rivals: six open PRs whose work already landed under another number, read and closed with anything they hold salvaged first
state: done
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-07
pr: 1025
claimed_by: run 9/7/2026, 12:32:29 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T05:50:15.548Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34087017525
---

Six open PRs propose work that is already on `dev` under another number. Each is closed —
**after** it is read against `dev` and anything it holds that the winner does not is
salvaged into a ticket or a follow-up commit.

**The rule this band runs on: read before you close.** In the 2026-09-06 drain, six of six
parked rivals held something real — a man's record on the wrong Hubbard, three families, a
family nearly deleted as invented when a verified source states it, two tickets existing
nowhere, a self-test no landed tool had. Closing on the duplicate label alone would have
lost every one. Assume the loser holds something until you have looked.

| PR | why it is superseded | check before closing |
|---|---|---|
| #1013 | T-0744 landed as **#1014** | #1014 read the same leaf; does #1013 disagree on any line? |
| #1015 | T-0744, second reading, `hold` | it SELF-DECLARES disagreement on line count, pairs and footing — that is a finding, not a duplicate. See T-0930; do not close it silently |
| #1011 | T-0912's footing did not close; **#1012** closes it at 198 | #1011's four closing columns — are they identical in #1012? |
| #975 | self-declared duplicate of **#974** | whether #974 actually landed, and whether the reconciliation wording differs |
| #962 | self-declared duplicate of **#959** | #962 claims to machine-check five refusals #959 left as prose — if that is still true on `dev`, it is a gate nobody has, and belongs in a ticket |
| #968 | T-0771 landed as **#966** | already read: the rule DID land (`wholer`/`unbracketed`); its placement is refuted by the plat. `hold` — see T-0930 |

**Acceptance:**

1. Every PR above is closed, or a written reason says why it is not.
2. Each close carries a comment naming what was checked, what landed instead, and what was
   salvaged — or states plainly that nothing was, having looked.
3. Anything salvaged is a filed ticket or a commit on a branch that is going to land. A
   finding recorded only in a closing comment is a finding lost.
4. No PR here is closed on its title or its label alone.

---

**CLOSED BY PR #1025, 2026-09-07.** All six were read against `dev` before anything was
closed, and six of six held something the winner did not — as the band predicted.

**Closed, winner on `dev`:** #1013 (winner #1014), #975 (winner #974), #962 (winner #959).
Each carries a comment naming what was checked, what landed instead and where its findings
went. No branch was deleted.

**Left open with a written reason** (acceptance 1's alternative): #1015 — self-declared
disagreement with the landed reading, which is a finding and belongs to T-0930; #1011 —
its stated winner #1012 is still open, so closing would risk leaving printed 232 unread,
and it disagrees with #1012 in one cell; #968 — already read, the rule landed as #966 and
the `hold` label is T-0930's to rule on.

**Salvaged (acceptance 3).** Every one of the five tickets these PRs filed carried an id
that has never existed on `dev`; two of those ids (T-0860, T-0874) have since been taken
there by unrelated tickets and T-0923 was used by two different rivals for two different
findings. Refiled with the collisions resolved, plus four findings that only appear on
reading:

| new | was | from |
|---|---|---|
| T-0941 | T-0923 | #1013, widened once #1015 was read: three passes name line 1 three ways |
| T-0942 | T-0924 | #1013 |
| T-0943 | T-0923 | #1015 |
| T-0944 | T-0922 | #1011 |
| T-0945 | — | #1011 against #1012: one cell apart, and it decides the column |
| T-0946 | T-0874 | #975 |
| T-0947 | — | #974 against #975: the same ruling, 36.79 m apart, and no gate that would see it |
| T-0948 | T-0860 | #962 |
| T-0949 | — | #962's machine-check is real and is on none of `dev` |
