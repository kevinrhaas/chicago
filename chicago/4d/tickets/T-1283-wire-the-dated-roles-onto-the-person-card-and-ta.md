---
id: T-1283
title: Wire the dated roles onto the person card, and take the ready renderer from the duplicate branch rather than writing it twice
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1255
needs_bake: false
closed_at: 2026-09-17T19:19:27.387Z
claimed_run: null
---

`dev` carries the dated plural role schema and its gates — T-1229 landed them in #1387 —
and **no renderer reads a role.** That was deliberate and is stated in that merge's own
commit: "The role fields are shipped to the browser and no renderer reads one yet". Measured
on `dev` at d1ae03268, `roles` appears in the renderer tree only in `changelog.js` and in the
three plant modules, which are a different `roles`.

**A working renderer for exactly this already exists and should not be written a second
time.** PR #1386 was a duplicate claim of the same split — two runs each took a child of
T-1145, dev merged the other one — and it is closed. But the half that did NOT collide is
the half dev is missing:

    git fetch origin steward/t-1145-plural-roles
    git show 27c30072b -- chicago/4d/renderers/web/js/residents.js   # 99 lines, the card
    git show 27c30072b -- chicago/4d/tools/roles.py                  # 164 lines, the helper

**Read it against dev's schema before using a line of it.** The two runs wrote the role
shape independently, so the branch's `validate.py` is NOT dev's and the field names may not
agree. `roles.py` is a helper over the branch's own shape and may need rewriting against
dev's; the renderer is the part most likely to carry over close to intact. Take what fits and
rewrite what does not — the point of this ticket is that the design work and the layout are
done, not that the code drops in.

**Acceptance:** a person card shows the roles that cover the scene date and the ones that do
not, each with its dates and its source, so that Daniel Elston reads as a candle and soap
manufacturer in 1833 AND a school inspector in 1839 without either erasing the other; the
1835 occupation field remains the derived view it now is; zero page errors at 390x780 and
desktop; and the PR says which lines came from `steward/t-1145-plural-roles` and which were
rewritten, so the duplicate's work is credited rather than silently reproduced.
