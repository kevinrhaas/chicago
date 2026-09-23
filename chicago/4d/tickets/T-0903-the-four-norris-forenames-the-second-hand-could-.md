---
id: T-0903
title: The four Norris forenames the second hand could not lift, read off the page image — Iia is Ira Couch of the Tremont House
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-06
pr: 997
claimed_by: run 9/6/2026, 1:07:36 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T18:25:43.205Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34048091257
---

The four Norris forenames the second hand could not lift, read off the page image — Iia is Ira Couch of the Tremont House.

**FOUND BY T-0695's OWN SUCCESSOR CLAUSE.** PR #995 repaired eleven garbled forenames
against Kim Torp's independent transcription and wrote an `UNREPAIRED` list naming the one
she could not lift, with what it would take: *"there is no second hand to correct it with,
and reading 'Ira' into it would be reading the wanted match into the page. It needs the page
image."* That entry is `Couch, Iia` — the Tremont House, at Lake and Dearborn, which the town's
attested Ira Couch kept. This ticket reads the page image.

Three more come with it, and they are a class nobody could have swept for. `VV` is the
compositor's **W** set by the scanner as two V's. `name_agreement.garbled()` looks for a
character no compositor set, and `VV` is made entirely of letters, so that test is blind to it:
`Abbott, VV.`, `Day, VVm.` and `Hequenbourg, G. VV.` sat in the claims file with nothing said
about them.

**Acceptance:**

1. The four are read off the page image itself — the scan the OCR is made from — each line
   located by its own word coordinates, cropped on that bounding box and read by eye, and each
   repair citing the leaf image so a reader can go back to it.
2. The repair goes in `normalized.given` and the quote keeps the damage, on T-0695's own
   convention, and every row asserts the token it replaces so a re-read that moves a line fails
   the build.
3. The `VV` class is asserted by hand in `--self-test`, because the sweep cannot see it.
4. Both crosswalks re-derive and the movement is reported. `bash tools/check.sh` green.
