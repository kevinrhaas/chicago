---
id: T-0775
title: Volume 4's OCR reading stitched, re-parsed and re-sampled, now that every band is in
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0621
opened: 2026-09-05
closed: 2026-09-05
pr: 888
claimed_by: run 9/5/2026, 8:45:06 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T14:42:21.123Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33969615940
---

Volume 4's OCR reading stitched, re-parsed and re-sampled, now that every band is in.

Piece 2 of 2 of **T-0621 — Volume 4 read by OCR, pages 613-918: the shards, then stitch, re-parse and re-sample the volume**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Blocked on T-0619** (pages 1-306, the last unread band). `--extract --ocr` with no range refuses
to assemble over a gap, which is the backstop: this ticket cannot be started early by accident.
Pages 307-612 landed on T-0620, 613-918 on T-0769.

**Acceptance:** (one demonstration, never weakened to pass)
- `--extract --ocr --volume 4` with no range: stitch every shard, assemble, and REPLACE
  `text/vol_04_locality_cards.txt`. MANIFEST records the engine, its version, the dpi, the psm,
  the crop boxes and every shard's sha256, so the reading stays reproducible from a PDF this repo
  does not carry.
- `--parse --volume 4`: `records/entries_vol_04.json` re-parsed, every record still
  `transcription_mediated`, every `as_read` rebuilt from the committed text by `--check`, and
  `leads.json` / `follow_up.json` / `entries.json` / `lead_crosswalk.json` re-parsed to match.
- A FRESH forty-card hand-adjudicated draw for the re-read, appended to `precision_sample.json`
  as its own block. The 0.475 belongs to the text-layer reading and MAY NOT be carried forward —
  it measured a different reader.
- The README's volume 4 section and its comparison table updated, and its warning that volume 4's
  row is not comparable with the other three either withdrawn or restated against the new figures.
- Counts in the PR against T-0613's table: cards assembled, kept, Chicago-or-Cook, leads by layer,
  and the before/after against the 308.
- Volumes 1-3 are NOT re-read here. If the re-OCR would beat their text layers too, that is a
  finding to report and a separate ticket, not scope to take on quietly.
- No resident, household, structure or business is added or regraded.
