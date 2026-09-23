---
id: T-0618
title: The OCR reader for volume 4: --extract --ocr, resumable by page range, and the measured recovery it buys
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0613
opened: 2026-09-03
closed: 2026-09-03
pr: 749
claimed_by: run 9/3/2026, 9:03:06 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T02:19:38.696Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33823914688
---

The OCR reader for volume 4: --extract --ocr, resumable by page range, and the measured recovery it buys.

Piece 1 of 4 of **T-0613 — Volume 4 of the Newberry index has a much worse text layer than volumes 1-3, and a tesseract re-OCR reads the cards it loses**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `text/vol_04_probe.json`: a fixed page sample read BOTH ways — the committed pdftotext
  path and the new one — with cards assembled, locality cards kept and characters
  emitted for each, plus the whole-volume text-layer figures, plus volumes 1-3 out of
  MANIFEST for scale, plus the measured cost per page. Written by a command (`--probe`),
  not by hand, so it can be re-run and disagreed with. The parent's own cost estimate
  (300 dpi, 3.8 hours) is superseded by whatever this measures.
- `--extract --ocr` in `tools/read_newberry_index.py`: renders each page, crops it into
  the SAME four column windows the pdftotext path uses — T-0580 measured that those are
  the right boxes and that is why they stay — reads each strip with tesseract, and hands
  the four column texts to the SAME card assembly. The two readers differ only in where
  the characters come from, and the grade does not move off `transcription_mediated`.
- Resumable by `--pages A-B`, because the volume does not fit in one run's foreground: a
  range writes a shard, `--extract --ocr` with no range stitches the shards in page
  order. Stitching REFUSES shards that disagree on settings or on which pdf they read,
  and REFUSES a gap — a volume assembled over a gap is a partial read wearing a finished
  volume's file name, and the next run would believe it. `--check` holds committed shards
  to MANIFEST's sha256 in both directions: named-but-missing, and committed-but-unnamed.
- `--self-test` covers the stitch and every refusal.
- `./tools/check.sh` no redder than dev, and `--check` green.
- NO new volume 4 reading is committed here. The 308-card text-layer read T-0580
  committed stays exactly as it is until a full OCR pass replaces it — that is T-0619 to
  T-0621. A partial OCR read committed here would be a third state of the volume, and
  worse than either of the two.
