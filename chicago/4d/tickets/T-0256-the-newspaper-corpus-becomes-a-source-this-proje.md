---
id: T-0256
title: The newspaper corpus becomes a source this project can cite
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 448
claimed_by: run 8/28/2026, 4:31:14 AM CT
blocked_on: null
needs_bake: false
---
The project holds ~103 transcribed newspaper issues it cannot yet cite:
`chicago/reference/newspapers/Transcriptions/` — the **Chicago Democrat** from
its first issue (1833-11-26, Vol I No 1) through 1835-08-26, and the **Chicago
American** 1835-06-08 through 1835-08-29. The scene date sits inside both runs;
a Democrat was PRINTED on 1835-07-01. Each issue carries page/column markers
(`===== ISSUE PAGE n / PDF PAGE m / COLUMN k OF 6 =====`), searchable
uncertainty brackets (`[uncertain: …]`, `[illegible]`, `[missing at edge]`),
per-set manifests (CSV) and validation notes (MD). Read
`Newspaper_Transcription_Workflow.md` there first — it is the corpus's own
methodology and this epic inherits its conservatism.

This ticket makes the corpus a citable, machine-resolvable source. Nothing is
extracted yet.

## The owner's three rulings, 2026-08-28 — every ticket in this epic works under them

1. **A letter-list name is enough to mint a resident.** The post-office letter
   lists name people by the hundred; the owner ruled a listed name alone makes a
   resident candidate, not merely a gazetteer entry. Record `letter_list_only:
   true` so the two evidence strengths stay distinguishable forever.
2. **Transcription-mediated readings grade `documented`, carrying a flag.** The
   corpus is read through OCR-assisted transcriptions, not the page scans. Every
   claim taken this way carries `reading: transcription_mediated` and preserves
   the transcription's own uncertainty brackets. This EXTENDS, and does not
   overturn, `data/sources/chicago_democrat_1833_11_26.json`'s standard — where
   a scan exists and is read, the scan remains the authority (it caught 'C. & I.
   HARMON' where the transcription had 'C. & L. Harmon'), and a
   transcription-mediated claim upgrades when a scan read confirms it.
3. **A documented business is BUILT at the scene date unless contradicted.** A
   dissolution, removal or replacement notice is the only thing that keeps a
   documented business out of the 1835 town. A business whose last evidence is
   1833-1834 is built WITH a survival liberty stated on the record (existence
   documented, survival to 1835-07-01 assumed) — docs/LIBERTIES.md carries it.


## The work

1. **Two publication-level source records**, `data/sources/`:
   `chicago_democrat_1833_1835.json` and `chicago_american_1835.json` — `type:
   newspaper`, tier 1, `rights_status: public_domain` (1830s imprints; the
   transcriptions are the owner's work product). Model the notes on the existing
   `chicago_democrat_1833_11_26.json` — the traps it documents (stock cuts are
   not pictures of Chicago buildings; ad-copy dates are not issue dates; a later
   pencilled gloss is not letterpress) apply corpus-wide and must be restated.
   Record ruling 2 verbatim in both notes. The per-issue record for 1833-11-26
   STAYS as is — scan-verified, senior to this epic's readings for that issue.
2. **The citation convention**, stated in both records: publication, issue date,
   Vol/No, issue page + column from the transcription's own markers, plus the
   transcription file path and line range. A claim that cannot name its column
   cannot be made.
3. **`tools/docx_text.py`** — extract plain text from the ~35 `.docx`-only
   issues (the 1835 Democrat tail and the entire American) using ONLY stdlib
   (`zipfile` + `xml.etree`; a .docx is a zip of XML — no new dependencies, the
   fleet is static-first). Deterministic: same input, same bytes out. Output to
   `data/research/newspapers/text/<issue_id>.txt`. Issues that already have a
   committed `.txt` under `chicago/reference/` are NOT copied — they are cited
   at their reference path.
4. **`data/research/newspapers/corpus.json`** — one entry per issue:
   publication, date, vol/no, text path (reference or derived), source docx
   path, completeness (the 1835-07-08 Democrat is explicitly partial — its
   fourth page is absent from the source PDF; the validation notes flag others),
   word count from the manifests where present, validation-note pointer. This
   file is what every later ticket resolves citations against.
5. **A check.sh step**: every corpus entry's text path resolves; dates parse and
   are strictly increasing per publication; the issue count is stated (~103) and
   asserted, so a silently dropped issue is loud; `data/research/` reaches
   NOTHING under `site/chicago/4d/` (the corpus is research, not payload — the
   publish-sync gate must stay green without it).

## What NOT to do

- Do not start extracting entities. That is T-0257 onward.
- Do not modify anything under `chicago/reference/` — it is the owner's
  archival deposit and this project reads it only.
- Do not let 14 MB of text into the published mirror.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `corpus.json` lists every issue in `Transcriptions/` with a resolvable text
  path; the count is asserted in the gate, not observed.
- `tools/docx_text.py` is deterministic (run twice, `diff` the outputs, assert
  byte-identical in a self-test) and its output for one American issue and one
  1835 Democrat issue spot-matches the .docx read by eye — quote the passage
  checked in the PR.
- Both source records pass check.sh and carry ruling 2 and the corpus-wide
  traps.
- check.sh is green with the corpus committed, and `site/chicago/4d/` is
  byte-identical to before this branch.
