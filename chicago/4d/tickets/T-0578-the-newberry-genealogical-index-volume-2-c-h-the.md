---
id: T-0578
title: The Newberry Genealogical Index, volume 2 (C-H): the Chicago, Cook County and Illinois cards, their leads and the works they point at
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0562
opened: 2026-09-03
closed: 2026-09-03
pr: 726
claimed_by: run 9/3/2026, 2:37:04 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T20:26:19.204Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33796895418
---

The Newberry Genealogical Index, volume 2 (C-H): the Chicago, Cook County and Illinois cards, their leads and the works they point at.

Piece 2 of 4 of **T-0562 — The Genealogical Index of the Newberry Library (4 vols., Internet Archive chicago1835-newberry-genealogical-index): read the index for every 1835 surname and every Chicago, Cook County and Illinois citation, and follow the pointers into the genealogies that date and place residents, households and businesses**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

The volume is not committed. `data/research/newberry_index/text/MANIFEST.json` names the
Internet Archive file, its size and its sha256; fetch it to a scratch path and run

    python3 tools/read_newberry_index.py --extract --volume 2 --pdf <path>
    python3 tools/read_newberry_index.py --parse   --volume 2
    python3 tools/read_newberry_index.py --check

The tool crops each page into its four columns before laying it out, because
`pdftotext -layout` weaves four columns of cards into single lines and separates a
heading from its own citation. Volume 1 is the worked example and its README says what
the reading is worth.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `text/vol_02_locality_cards.txt` committed, and MANIFEST carrying the volume's sha256,
  its crop boxes and the sha256 of every intermediate, so the extraction is reproducible.
- `records/entries_vol_02.json` in the T-0492 records shape, every record
  `transcription_mediated`, every `as_read` rebuilt from the committed text by
  `--check`, and `leads.json` / `follow_up.json` / `entries.json` re-parsed to include it.
- A fresh forty-card hand-adjudicated draw appended to `precision_sample.json` for THIS
  volume, with its own precision figure. A number carried over from another volume is
  not a measurement of this one.
- Counts in the PR: cards assembled, locality cards kept, Chicago/Cook cards, leads by
  layer, works ranked.
- No resident, household, structure or business is added or regraded. The index is a
  finding aid; `--check` fails if the source id ever appears behind a person.
