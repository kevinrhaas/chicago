---
id: T-1219
title: The three re-spelled cards still say in prose that the papers print the reading T-1139 overturned: hh_fraser_wm_h reads 'Wm. H. Frazer' and its own note says the papers print 'Wm. H. Fraser'
state: open
epic: META
requested_by: loop
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

The three re-spelled cards still say in prose that the papers print the reading T-1139 overturned: hh_fraser_wm_h reads 'Wm. H. Frazer' and its own note says the papers print 'Wm. H. Fraser'.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1218**, which gated the card NAMES against the ids and left the prose alone.

T-1139 ruled that the scan-verified reading of the ninth impression overturns the
transcription-mediated one, so `hh_fraser_wm_h` displays `Wm. H. Frazer`. The generated
`note` on the same person still reads *"The papers print 'Wm. H. Fraser' in a single
return of letters uncalled-for at the Chicago post office — the Democrat of 28 January
1834, column 1"*. Same on `provis_joshua` (`Joshua Provis`) and `vandino_john` (`John
Vandino`). A card names one reading and asserts the other as the printing.

**It is not obviously a typo, which is why it is a ticket and not a patch.** The ruling's
own reasoning is that these are *"two impressions of one return, re-keyed by the
compositor"* — so the 28 January impression may genuinely have set the overturned
letters, and a note naming that impression may be telling the truth about it while the
card tells the truth about the ninth. The note is minted by `record()` in
`tools/mint_letter_list_residents.py` off the gazetteer candidate name, so whatever is
decided is a change to the template and not to three files.

**Acceptance:** a ruled card's prose and its displayed name agree about what stands —
either the note names the impression each reading belongs to, or it takes the ruled
reading — and the mint derives it rather than three cards carrying a hand repair.
