# T-2380 — exact 1902 published plate found

**Ready:** `T-2380-gale-1902.patch`, prepared against the current sourceS working tree. `git apply --check`, source/structure schemas and focused checks pass. Repositories remain unchanged by this agent. This supersedes the earlier artwork-level rights hold through direct publication evidence; it does not use owner clearance for another building.

## Actual evidence

Internet Archive item **reminiscencesofe00ingale**, Edwin O. Gale, *Reminiscences of Early Chicago and Vicinity*:

- Actual title page, [n12](https://archive.org/details/reminiscencesofe00ingale/page/n12/mode/1up): **ILLUSTRATED BY W. E. S. TROWBRIDGE**; Fleming H. Revell Company; Chicago / New York / Toronto; **MCMII**.
- Actual copyright page, [n13](https://archive.org/details/reminiscencesofe00ingale/page/n13/mode/1up): **COPYRIGHT, 1902, BY FLEMING H. REVELL COMPANY — October**.
- Actual unnumbered plate facing printed p53, [n79](https://archive.org/details/reminiscencesofe00ingale/page/n79/mode/1up): the **exact detailed jail artwork**, captioned **Cook County’s First Jail as it was in1836. Located on the Northwest Corner of the Public Square**. The full composition matches the later cropped surrogates: keeper-house sash/doors, barred-looking log gable light, stockade/gate, oxen, paired dogs, foreground figures, street crowd, tents and both flocks of birds. This is visual identification, not a claimed numerical pixel match. A small cursive signature ends **02**; the full illustrator credit rests on the legible title page rather than an uncertain signature transcription.

These actual pages establish publication in 1902, independently of the UCR copy’s combined creation/issuance date. The published 1902 illustration is public domain by age. Use the Gale plate as the independent project source. The UCR catalogue’s date, credit and item-specific rights statement remain as read; no publication in1930 is inferred. No added 1947 newspaper text/layout is cleared by this finding.

All downloaded evidence was actually viewed. Exact direct-page URLs, byte counts and SHA256 values are in `evidence-files.json` and appended to the repo audit proposal. Captures live in `../T-2380-rights-next/`. No binary is added to the repository patch.

## Narrative and date limits

Actual p25 [n40] dates arrival to **25 May 1835**. Actual p43 [n66] begins an early-breakfast/morning stroll in the newly arrived family’s town narrative; it does not independently date that walk to a precise day. Actual p51 [n76] says the courthouse is “just started,” the small log jail is concealed within a high plank palisade, and John Beach occupies a house partly within the same enclosure, facing Randolph. Actual pp52–55 [n77/n80/n81/n82] continue the walk, without a jail construction or alteration sequence.

This is a memoir published1902, framed in1835, while the plate itself says1836. It supports the distinction between jail core, palisade and keeper’s house. It does not measure the core, resolve the original1833cell/later separate oaken cell, or prove every pictured detail existed by1July1835. The independent Andreas hip/pyramidal-cap conflict remains. **Rights are now independently supported; geometry/date/camera work still needs its own review.** No numerical proposal is applied in this increment.

## Patch scope and checks

Eight files: new `trowbridge_first_jail_gale_1902.json`; existing textual UCR catalogue note/rights-note supersession; both image inventories; only `log_jail.research_note`; dated supersession additions to LIBERTIES, owner-brief README and the T2380 source audit. Historical hold entries remain, explicitly superseded by later same-day evidence.

- UCR catalogue keeps `rights_status=check_required`, `asset_use=text_only`, its exact date, identifier, credit and every other field. Its own copy is not relabeled as cleared.
- New independent Gale illustration source uses `public_domain`, `cross_check`, with actual publication proof and caption/narrative limits.
- All structure phases/forms, existing source linkages, confidence, footprint, placement and dates remain exactly equal. Only the research note changes.
- Exact mesh recipe and SHA remain equal: `daf789e64dede9497de8d144326e728980e2e0e484f9797cfc03ec7e4c74b6f9` (`recipe-proof.json`). No master/web GLB changes or bake is needed for this source increment.
- Automatic card picture join adds exactly the one independent Gale plate. Pure grade remains unchanged in this current tree (`inferred`): the current automatic grade rule needs a library depicting-view, solved camera or explicit ruling. No such verdict is invented here. The source/card compiler can expose the plate now; actual camera work remains next.
- `verify.py`/`verify.log` pass evidence hashes, schemas, exact recipe/phase/grade constraints and patch applicability.

Parent should integrate, compile source/card metadata and run its required full checks. No application/ticket writes, full gate, browser, Blender, export, bake, `matches` verdict or closure were performed by this agent.

## Bounded search

Candidate metadata/OCR was retrieved for Gale1902, Kirkland1892 and Moses/Kirkland1895; the initially guessed Blanchard/Flinn identifiers returned no text and were not counted as searched books. Gale’s illustration list led directly to the exact pictured plate, so no further broad search was necessary. The decisive proof is the actual plate plus actual title/copyright pages, not OCR or a caption match alone.
