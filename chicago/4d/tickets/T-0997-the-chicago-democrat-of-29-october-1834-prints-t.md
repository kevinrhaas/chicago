---
id: T-0997
title: The Chicago Democrat of 29 October 1834 prints the committee of seventy a town meeting appointed against gambling, and the issue has never been extracted: about thirty townspeople named in one claim
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-13
pr: 1277
claimed_by: run 9/13/2026, 2:53:05 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T21:52:13.308Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34778903769
---

The Chicago Democrat of 29 October 1834 prints the committee of seventy a town meeting appointed against gambling, and the issue has never been extracted: about thirty townspeople named in one claim.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0842, 2026-09-10**, searching the deposited Democrat run for the Van der Bogart
stem. The issue of 29 October 1834 (Vol. I No. 48) is in `data/research/newspapers/corpus.json`
and its transcription is deposited at
`chicago/reference/newspapers/Transcriptions/Chicago_Democrat_1833-11_to_1835-08/Chicago_Democrat_1834-10-29_VolI_No48_Transcription.txt`.
There is no `data/research/newspapers/extracted/chicago_democrat_1834_10_29.json`, so not one
claim has ever been taken from it.

What is on page 2, column 2 (transcription lines ~930-1000) is a TOWN MEETING against gambling,
chaired by J. H. Kinzie with Hans Crocker as secretary, which appoints a committee of seventy.
The OCR of that column ran on the Tesseract fallback and is interleaved with its neighbour, so
the names come out damaged and doubled up — but they are legible in outline and there are about
thirty of them, among them Daniel Whittier, E. Mosely, H. Ven De Bogart, A. N. Ful[lerton],
Avery, Beaubien, L. C. Saxton, C. L. Harmon, Isaac Harmon, W. Sherman, A. Clybourn, Aaron
Russell, G. South, J. S. Wright, L. Clarke, A. Lloyd, G. Hubbard, W. H. Kennicott, V. Owen and
E. K. [Hubbard].

**Why it is worth a run.** A committee of seventy named in one place is one of the largest
single lists of townspeople this corpus holds, it is dated squarely inside the scene window,
and it carries something the letter lists never do: it says these people were HERE, acting, on
a stated evening. T-0842 could use one line of it as reasoning and left the rest unread.

**Acceptance:** the issue is extracted into `data/research/newspapers/extracted/` in the same
shape as its neighbours, with the interleaving of the two-column OCR resolved or declared
unresolvable per name; every name that cannot be read is left `[?]` rather than guessed at, in
the position it was printed in (T-0397); the gazetteer and `register_1835.json` rebuild; and
the run says how many of the committee the town already carries a card for.
