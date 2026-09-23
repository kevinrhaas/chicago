---
id: T-0268
title: A building held under the standing constraint says so nowhere a visitor can see
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-13
pr: 1249
claimed_by: run 9/13/2026, 6:53:25 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T12:26:30.645Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34755436969
---

Nine structures carry `review_required: true` — the agency at Cobweb Castle, the council
house, the Beaubien homestead, Robinson and Caldwell's cabins — and AGENTS.md's standing
constraint is the one rule this project puts above the work. A visitor who opens one of
those cards is told none of it. The flag reaches the browser exactly once, as a console
line in `renderers/web/js/scene-loader.js` ("this scene cannot be released"), which is a
developer's message about a scene rather than a reader's note about a building. The reason
IS written down — T-0025 made that a rule, and eight of the nine already kept it — but it
is written inside 400-word notes the card shows verbatim and folded away.

Epic is really RENDERING rather than META: the work is a card section, and the field it
would show does not exist yet, which is the part to think about first. `compile_scene.py`
already carries `review_required` into every sidecar; a short reason string is a second
carrier for prose that exists, and K35 declined exactly that for the gate's sake — so the
honest options are a section that surfaces the sentence the census already extracts, or a
line of standing text keyed on the boolean, and the choice is the ticket.

**Acceptance:** a visitor opening any of the nine flagged buildings is told, on the card
and without unfolding anything, that the record is held pending consultation and what it
is held for; the census in `tools/measure_review_constraint.py` and the card do not
disagree about which buildings those are; both viewports green.

Opened by T-0025 (ROADMAP K35), which closed the data half and deliberately shipped no
visitor-facing change.
