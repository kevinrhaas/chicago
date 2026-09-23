---
id: T-0811
title: Volume 4 read by OCR, pages 613-918: the shards
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0621
opened: 2026-09-05
closed: 2026-09-05
pr: 881
claimed_by: run 9/5/2026, 7:06:13 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T12:31:50.564Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33963528564
---

Volume 4 read by OCR, pages 613-918: the shards.

Piece 1 of 2 of **T-0621 — Volume 4 read by OCR, pages 613-918: the shards, then stitch, re-parse and re-sample the volume**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Why the parent was split.** T-0621 asked for two demonstrations in one run: the last 306 pages
read by OCR, and THEN the stitch, re-parse and forty-card re-sample of the whole volume. The stitch
cannot run until every band is in, and the first band — pages 1-306, **T-0619** — was claimed by
another run at the same minute this one started and is not on `dev`. So the reading is this ticket
and the stitch is **T-0775**, blocked on T-0619.

**Acceptance:** (one demonstration, never weakened to pass)
- `--extract --ocr --volume 4 --pdf <path> --pages A-B` over pages 613 to 918, in as many foreground
  commands as the range needs, sized off `text/vol_04_probe.json`'s measured `seconds_per_page`
  and the 10-minute ceiling. Each shard committed as it finishes.
- The shards under `text/ocr/vol_04/` and nothing else. No stitch, and no touch to
  `text/vol_04_locality_cards.txt`, `records/entries_vol_04.json` or the leads: the volume's
  committed reading stays the text-layer one until T-0775.
- `python3 tools/read_newberry_index.py --check` green, `./tools/check.sh` no redder than dev.
- Counts in the PR: pages read, shard files committed, their compressed size, and the cards the
  assembler finds in this band against what the text layer found in it.
