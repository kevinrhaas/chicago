---
id: T-0650
title: The Illinois Catholic Historical Review says where St Cyr's first church stood, and nothing has read it out
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 830
claimed_by: run 9/4/2026, 8:15:40 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T02:01:05.710Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33935471720
---

The Illinois Catholic Historical Review says where St Cyr's first church stood, and nothing has read it out.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0503**, which searched archive.org for a second reading of St Mary's BAPTISMAL
register and did not find one — the Illinois Catholic Historical Review printed St. Cyr's
marriages and his deaths and left his baptisms in manuscript. That negative is filed at
`data/research/church/search_log.json`. Reading vol. 4's OCR for it turned up something the
sweep was not looking for and had no standing to spend.

**The finding.** Vol. 4 of the Review (`illinoiscatholic04unse_1` on the Internet Archive,
already cited here as `st_cyr_register_ichr_v4`) says of Father O'Meara's arrival that he
"found the little church that Father St. Cyr had built standing near the southwest corner of
what is now State and Lake Streets, upon ground controlled by the Canal Commissioners", and
goes on about the Catholics' intention to buy the lot at the canal auction and a friendly
local agreement not to run the price up against them.

**Why it matters.** THE FIRST CATHOLIC CHURCH IS NOT IN THE SCENE. The register scans name no
church building at all — T-0503 checked all eleven pages and filed that as the finding — so
this passage is the only located statement of the building this project has, and it is a
STRUCTURE at a NAMED CORNER inside the scene window. It also carries a land fact (Canal
Commissioners' ground, unsold in 1835) that bears on what the lot looked like.

**The ask.**

1. Read the passage and its surrounding pages under the committed-corpus discipline the books
   domain uses — a `data/research/books/` claim with a verbatim `quote` the gate rebuilds, a
   `normalized` sibling and a `locator` into committed text. It is a BOOKS claim, not a church
   one: its source is the Review, not the register.
2. Say what the passage does and does not fix. "Near the southwest corner of what is now State
   and Lake" is written in 1921 about 1839 and is a retrospective; the church was built in 1833
   and MOVED later, and this ticket must establish which building and which date the sentence
   describes before any footprint is proposed.
3. Only then, and in a SEPARATE ticket, consider a structure record. Do not site a building off
   one retrospective sentence.

**Acceptance:** the claim is committed with its quote rebuilding character for character; what
the passage fixes and what it does not is written down; no structure record is created by this
ticket.

**Links:** T-0503 · `st_cyr_register_ichr_v4` · `data/research/church/search_log.json`
