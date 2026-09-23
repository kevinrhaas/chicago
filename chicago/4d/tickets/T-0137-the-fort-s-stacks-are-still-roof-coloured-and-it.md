---
id: T-0137
title: The fort's stacks are still roof-coloured, and its 1816 date fits neither chimney answer
state: done
epic: RENDERING
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-22
closed: 2026-08-28
pr: 438
claimed_by: run 8/28/2026, 1:10:53 AM CT
blocked_on: null
needs_bake: false
---

The fort's stacks are still roof-coloured, and its 1816 date fits neither chimney answer.

T-0008 gave every framed building's stack brick and every log cabin's stick-and-clay, and left
`fort_structure` building its stacks with `M_ROOF` — so the ten garrison buildings are now the only
roofs in Chicago whose chimneys are painted the colour of the roof they pass through. It was left
out deliberately and the reason is in `docs/RESEARCH/chimneys.md` §4: the second Fort Dearborn is
**1816**, seventeen years before Blodgett's brick-yard opened, it stands on federal ground outside
the corporation, and its ten records run `construction` across log, brick, earth and stone. Neither
of T-0008's two answers reaches it without inventing a third.

Ask the evidence question first — what a garrison post of 1816 built its flues of, and whether
anything in this repository (Andreas on the fort's rebuilding, the plates) says — then either a
third row on the sheet or a stated reason for taking one of the two that exist.

**Acceptance:** the fort's stacks carry a fabric argued from its own date and ground, at a stated
tier with a LIBERTIES entry if it is reconstructed, and no stack in the town is roof-coloured; or
the fort is refused in writing on the record, with the refusal reaching a reader. Gates green,
before/after frame at the fort.

**Links:** T-0008 (the parcel that made this the exception) · `docs/RESEARCH/chimneys.md` §4 ·
`generators/archetypes/fort_structure.py::_chimneys` · docs/LIBERTIES.md L26.
