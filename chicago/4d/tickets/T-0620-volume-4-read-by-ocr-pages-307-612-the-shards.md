---
id: T-0620
title: Volume 4 read by OCR, pages 307-612: the shards
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0613
opened: 2026-09-03
closed: 2026-09-05
pr: 870
claimed_by: run 9/5/2026, 4:25:33 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T10:25:55.131Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33957713792
---

Volume 4 read by OCR, pages 307-612: the shards.

Piece 3 of 4 of **T-0613 — Volume 4 of the Newberry index has a much worse text layer than volumes 1-3, and a tesseract re-OCR reads the cards it loses**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `--extract --ocr --volume 4 --pdf <path> --pages A-B` over pages 307 to 612, in as many foreground
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

Blocked on T-0618 until the reader exists.
