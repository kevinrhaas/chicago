# Download & rights-review pass — 2026-10-02

Owner brief (2026-10-02): download as many images as possible, always keeping the source;
collection budget 300 MB (`tools/validate.py`), this pass stops at ~250 MB.
Streams edited: every `stream-*.json` except `stream-newspapers-north-owners.json` and
`stream-newspapers-south.json` (other agents). Fields touched: `local`, `rights`,
`rights_basis`, and an appended sentence in `notes` where rights changed.

## Budget

- Before: `research/images/files` = 37.6 MB (253 files).

## Rules applied

- Download only `public domain` / `no known restrictions` records.
- Skipped: whole newspaper-page scans of text items (Tribune / Abendpost / Chronicling
  America full pages) — unreadable at 1400 px. Chicagology's *crops* of newspaper
  headlines/ads (a few hundred px tall, legible) are not page scans and were downloaded.
- `--max 2000` for maps, atlas plates, bird's-eye views, aerials, measured drawings and
  the Renwick drawings; 1400 px otherwise.
- Robinson 1886 crops (73, previously thumb-only) re-fetched with a 2000 px display copy.

## Progress log

(in progress — updated every ~25 records)

- 15:26 phase A started: 219 eligible PD/NKR records with an image URL (73 Robinson crops
  re-fetched at 2000 px; chicagology crops; AIC Ryerson & Burnham microfilm frames and
  plates; archive.org plates; Sanborn 1911/1950 sheets at 2000 px).
- ~15:50: 122 downloaded, 3 failed (AIC www.artic.edu IIIF returns HTTP 403 to scripted
  requests — the three Renwick drawings a19-aic-2ndpres-renwick-*; left link-only).
- Rights review drafted for 39 records (applied after phase A finishes; see below).
