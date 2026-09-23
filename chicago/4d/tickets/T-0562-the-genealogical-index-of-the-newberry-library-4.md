---
id: T-0562
title: The Genealogical Index of the Newberry Library (4 vols., Internet Archive chicago1835-newberry-genealogical-index): read the index for every 1835 surname and every Chicago, Cook County and Illinois citation, and follow the pointers into the genealogies that date and place residents, households and businesses
state: split
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: run 9/3/2026, 10:51:43 AM CT
blocked_on: null
needs_bake: false
---

The Genealogical Index of the Newberry Library (4 vols., Internet Archive chicago1835-newberry-genealogical-index): read the index for every 1835 surname and every Chicago, Cook County and Illinois citation, and follow the pointers into the genealogies that date and place residents, households and businesses.

**The owner's ask, verbatim (2026-09-03):** "make sure you have a resident household business city data
improvement ticket for https://archive.org/details/chicago1835-newberry-genealogical-index if you do not already
i am starting to move the research corpus to the internet archive".

**What the item is.** *The Genealogical Index of the Newberry Library, Chicago*, volumes 1–4 — the printed
edition of the Newberry's genealogical card index: hundreds of thousands of surname entries, each pointing at
the published genealogies, local histories and periodicals in which that family is treated, with locality and
the citation. The owner has put all four volumes on the Internet Archive under the identifier
`chicago1835-newberry-genealogical-index` (four "Text PDF" files of ~200 MB each: `FL2091539_CP-130151_01.pdf`,
`FL2091536_CP-130151_02.pdf`, `FL1982465_CP-130151_03.pdf`, `130151_04.pdf`; uploaded 2026-09-03 14:58Z, in the
`opensource` collection). It is a FINDING AID, not a primary source: an entry never places a person in 1835 by
itself, but it says where a genealogy exists that may — and that is the whole use of it here.

**The research corpus is moving to the Internet Archive.** Treat the IA identifier as the canonical locator for
this item: the source record `newberry_genealogical_index` carries `url:
https://archive.org/details/chicago1835-newberry-genealogical-index`, the per-file names, and the volume/page of
each entry cited. Do the same for any other corpus item you find at `archive.org/details/chicago1835-*` — the
owner is moving the corpus there item by item, and a source record that names the IA identifier survives the
move; one that names a local path does not.

**How to read it.** The PDFs carry a text layer ("Text PDF"): `pdftotext -layout` (installed on the runner) per
volume, cached under `data/research/newberry_index/text/` and never re-fetched — one volume at a time, they are
large. Do not commit the PDFs. Parse the entries into `entries.json`: surname, given names as printed, locality,
the citation (work, volume, page), and the volume/page of the index itself. Where the text layer is garbage on a
page, `tesseract` the page image and say so on the record.

**What to extract, in this order.** (1) Every entry whose locality or citation names Chicago, Cook County or
Illinois. (2) Every entry whose surname is in the residents, households, voter-list (T-0493), 1840-census
(T-0494–T-0496) or business layers, with the name-match discipline T-0505 uses (a shared surname is a lead, not a
match). (3) For each lead, the pointer: which genealogy or local history, and whether it is reachable
(HathiTrust, the Internet Archive, Google Books) — a `follow_up` file listing the works to open, ranked by how
many 1835 leads each one carries, so the next run reads the most productive genealogy first. Anything the index
entry itself states (a locality and a date for a family) goes on the lead with `describes_date` and never grades
a person above what the ladder allows for a finding aid.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `data/research/newberry_index/README.md` (what the index is, how it was read, what was not), `entries.json`
  for the categories above, `leads.json` (surname → resident/household/business/voter/census ids it may bear
  on, with the citation), `follow_up.json` (the genealogies to open, ranked), and the source record with the IA
  identifier as its locator.
- Counts in the PR: entries parsed per volume, Chicago/Cook/Illinois entries, leads by layer, works to follow.
- No resident, household or business is added or regraded from the index alone; leads that a follow-up
  genealogy confirms are written under the ratified ladder in the follow-up's own PR.

**Effort.** Four volumes at ~200 MB is four runs at least: text-extract and parse ONE volume as this ticket's
demonstration, then `ticket.mjs split` by volume so the pieces keep this place in the queue; the follow-up reads
of the genealogies become their own tickets, filed from `follow_up.json`.

**Links:** T-0492 (research-domain shape) · T-0493 (voter lists) · T-0505 (name-match discipline) · T-0513
(consolidation — waits on this) · T-0554–T-0557 (the owner's other four sources, same band).

**This is overall expansion, not a residents-only pass.** The owner's words, 2026-09-03: "this is overall
expansion because while you are parsing for residents and household people you might as well improve the
business and structure and occupation and other surrounding data and attributes that will help us render the
most complete reconstruction possible of chicago 1835." Every lead this index yields is read WITH the trade, the
business, the place and the year the cited genealogy carries, and each goes to the layer it belongs to, under the
T-0492 shape, date-flagged, and under the ratified ladder.
