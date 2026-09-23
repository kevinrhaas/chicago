---
id: T-0276
title: The 'Verified' 1833 transcription reads NOV. 19, and the Democrat published no such issue
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: 457
claimed_by: null
blocked_on: null
needs_bake: false
---

`chicago/reference/newspapers/Transcriptions/Chicago_Democrat_1833-11_to_1835-08/Chicago_Democrat_1833_11-16-Verified_Transcription.docx`
is the one artifact in the deposit whose filename carries no issue date, and its
identification is the only judgement in `data/research/newspapers/corpus.json` that is
not a reading. T-0256 attached it to **1833-11-26** as an `alternate` witness at
`inferred`, with the reasoning on the record, and it should not stay there
unexamined.

## What the artifact says about itself

- It is headed *"Best-effort verified reading transcription of the three supplied scan
  pages"*. THREE supplied images of an 1833 Democrat is exactly the scan set
  `data/sources/chicago_democrat_1833_11_26.json` describes and was verified against
  ("THREE page images, and they are NOT in issue order"). That is the whole of the
  reasoning for attaching it to 1833-11-26.
- Its filename says `1833_11-16`. The Democrat published no November 16 issue.
- Its own first page reads **"Visible date at the top of this supplied page: NOV. 19,
  1833."** The Democrat published no November 19 issue either: Vol. I, No. 1 is
  November 26, 1833, and nothing preceded it.

Two different non-dates for one artifact, and the corpus workflow's rule 2.3 forbids
silently repairing a visibly printed date — so both are preserved and neither is
resolved.

## Why this is the owner's

It is settled by looking at the scan, and the scans are his. The question is one
sentence: **does the top of the first supplied page read NOV. 19 or NOV. 26?** If 19,
the deposit holds a Democrat issue this project does not know about and the per-issue
source record's account of the scan set is wrong. If 26, the transcription misread its
own masthead and the attachment is correct.

Note what rides on it: the 1833-11-26 record is this dataset's **first contemporary
Chicago document** and its senior tier-1 textual source.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The owner has read the date at the top of the first supplied scan page.
- `corpus.json`'s `identification` for that artifact is `documented` with the source
  record naming the scan, or the artifact is moved to its own issue entry — not left
  at `inferred`.
- If a November 19, 1833 Democrat exists, `data/sources/chicago_democrat_1833_11_26.json`
  is corrected, because everything downstream inherits its account of the scan set.

---

## THE RULING, 2026-08-28

The owner, asked the one-sentence question above, answered:

> **"NOV. 26 is the first issue date I have scanned."**

**So the second fork is the live one: the transcription misread its own masthead, and
the attachment to 1833-11-26 is correct.** The deposit holds no Democrat issue this
project did not know about, and the per-issue source record's account of the scan set
stands unamended — the third acceptance line was conditional on a November 19 issue
existing, and none does. `data/sources/chicago_democrat_1833_11_26.json` is therefore
**untouched by this ticket**, which is the outcome the publication record's standing
instruction ("STAYS EXACTLY AS IT IS") wanted anyway.

### Read the answer for exactly what it settles, and no more

The owner answered at the level of his *holdings*, not of that one masthead: the
earliest issue he has scanned is November 26. That is enough, and it closes the
question by **elimination against the deposit** rather than by a second reading of the
page:

1. The Democrat published nothing before Vol. I, No. 1 — already on the record.
2. The deposit's scans now provably begin at that same issue — the ruling.
3. So the "three supplied scan pages" this artifact transcribes cannot belong to an
   earlier issue, and the only three-image 1833 Democrat set in the deposit is the
   November 26 one.

That warrants `documented`. It does **not** warrant saying anyone re-read the masthead,
because nobody did. `NOV. 19` stays on the artifact, quarantined and unexplained rather
than corrected, exactly as rule 2.3 requires — and a future scan read of that first page
would still outrank every word of this, per the standard at the top of the publication
record. The note written into the corpus says all of that in place, so a reader who
finds the artifact never has to find this ticket to know what its grade rests on.

### What changed

- `tools/newspaper_corpus.py` — `UNDATED` carries `documented` and the ruling's
  reasoning. **The note is edited in the builder, not in `corpus.json`**: the corpus is
  generated and a hand-edit there would be overwritten by the next `--build`. Verified
  the way that claim deserves — a rebuild from the deposit before the change was a
  byte-for-byte no-op, so the two lines the rebuild after it changed are the whole of
  the diff, with all 23 derived text files untouched.
- `data/sources/chicago_democrat_1833_1835.json` — **RULING 4** recorded verbatim in
  the house form, and the "AN ARTEFACT WHOSE IDENTIFICATION IS NOT SETTLED" paragraph
  rewritten, since it now is. Ruling 4 is stated as a bound on the **deposit**, not on
  the publication, because that is the bound the project can check anything against and
  it generalises: no future artifact may claim a pre-November-1833 Democrat either.
