---
id: T-0621
title: Volume 4 read by OCR, pages 613-918: the shards, then stitch, re-parse and re-sample the volume
state: split
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0613
opened: 2026-09-03
closed: 2026-09-05
pr: null
claimed_by: run 9/5/2026, 6:35:29 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T12:05:51.348Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33963528564
---

Volume 4 read by OCR, pages 613-918: the shards, then stitch, re-parse and re-sample the volume.

Piece 4 of 4 of **T-0613 — Volume 4 of the Newberry index has a much worse text layer than volumes 1-3, and a tesseract re-OCR reads the cards it loses**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `--extract --ocr --volume 4 --pdf <path> --pages A-B` over pages 613 to 918, in as many foreground
  commands as the range needs — size them off `text/vol_04_probe.json`'s measured
  `seconds_per_page` and the 10-minute foreground ceiling, not off a guess. Commit each
  shard AS IT FINISHES; a shard that lives only in /tmp when the run ends is gone.
- The shards under `text/ocr/vol_04/` and nothing else. Do NOT stitch, do NOT touch
  `text/vol_04_locality_cards.txt`, `records/entries_vol_04.json` or the leads: the
  volume's committed reading stays the 308-card text-layer one until every band is in.
  `--extract --ocr` with no range will refuse to assemble over a gap, which is the
  backstop for exactly this.
- `python3 tools/read_newberry_index.py --check` green, `./tools/check.sh` no redder
  than dev.
- Counts in the PR: pages read, shard files committed, their compressed size, and the
  cards the assembler finds in this band against what the text layer found in it.

THEN, in this same ticket, because the volume is finally whole:
- `--extract --ocr --volume 4` with no range: stitch every shard, assemble, and REPLACE
  `text/vol_04_locality_cards.txt`. MANIFEST records the engine, its version, the dpi,
  the psm, the crop boxes and every shard's sha256, so the reading stays reproducible
  from a PDF this repo does not carry.
- `--parse --volume 4`: `records/entries_vol_04.json` re-parsed, every record still
  `transcription_mediated`, every `as_read` rebuilt from the committed text by `--check`,
  and `leads.json` / `follow_up.json` / `entries.json` / `lead_crosswalk.json` re-parsed
  to match.
- A FRESH forty-card hand-adjudicated draw for the re-read, appended to
  `precision_sample.json` as its own block. The 0.475 belongs to the text-layer reading
  and MAY NOT be carried forward — it measured a different reader.
- The README's volume 4 section and its comparison table updated, and its warning that
  volume 4's row is not comparable with the other three either withdrawn or restated
  against the new figures.
- Counts in the PR stated against T-0613's table: cards assembled, kept, Chicago-or-Cook,
  leads by layer, and the before/after against the 308.
- Volumes 1-3 are NOT re-read here. If the re-OCR would beat their text layers too, that
  is a finding to report and a separate ticket, not scope to take on quietly.
- No resident, household, structure or business is added or regraded.

Blocked on T-0618, T-0619 and T-0620 — this one closes the volume.
