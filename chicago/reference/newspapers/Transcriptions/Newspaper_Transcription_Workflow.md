# Repeatable Historic Newspaper Transcription Workflow

## Purpose

This workflow is designed for image-only, multi-issue newspaper PDFs with narrow columns, damaged edges, uneven exposure, and nineteenth-century typography. Its goal is a high-coverage research transcription that distinguishes readable text from reconstruction and genuine uncertainty.

## Deliverables per issue

- One UTF-8 plain-text transcription in printed page and column order.
- One DOCX transcription with issue metadata, source-page divisions, column headings, running headers, page numbers, and visibly styled uncertainty markers.
- Manifest entry recording title, date, volume, issue number, source PDF page range, word count, uncertainty-marker count, and output filenames.

## 1. Preserve and inventory the source

1. Work from a copy of the original PDF; never recompress the archival source.
2. Record the source filename, total PDF page count, and whether pages contain embedded text or only images.
3. Extract or render each page at 300-400 dpi. Keep stable filenames such as `page-001.png`.
4. Check page order, rotation, missing pages, duplicates, bleed-through, tears, clipped edges, and skew before OCR begins.

## 2. Identify issue boundaries and metadata

1. Inspect mastheads and publication lines to identify every issue start.
2. Record newspaper title, publication place, date, volume, issue number, publisher, and source PDF page span.
3. Confirm that page counts and issue numbering form a plausible sequence. Do not silently repair a visibly printed date or number; note the discrepancy.

## 3. Segment pages by their actual layout

1. Crop columns page by page rather than assuming one grid for the entire PDF.
2. Include a small overlap at column boundaries so letters touching rules are not lost.
3. Make separate crops for display advertisements, tables, decorative type, and irregular narrow columns.
4. Deskew individual pages or columns when necessary, while preserving an untouched rendering for comparison.

## 4. Run independent recognition passes

1. Run at least two genuinely independent OCR passes: different engines, different segmentation modes, or both.
2. Retain raw OCR outputs with engine, resolution, crop, and settings recorded in filenames or a log.
3. Use whole-page OCR to recover reading context and column OCR to improve narrow type.
4. Treat OCR as evidence, not as the transcription. Agreement between engines is useful but does not override the image.

## 5. Reconcile against the page image

1. Assemble text in printed page order, then left-to-right column order.
2. Compare conflicting readings at enlarged scale, especially the first and last words of lines.
3. Visually check headings, names, places, dates, monetary figures, vote totals, legal citations, and advertisement addresses.
4. Compare recurring standing matter across issues, but only use another issue to support letters that are consistent with the target image. Preserve genuine variants.
5. Retain historical spelling and capitalization where legible. Correct only obvious recognition errors such as confused `rn/m`, `cl/d`, or long-s forms when the image supports the correction.
6. Do not modernize grammar or silently join doubtful line-end hyphenations.

## 6. Apply a conservative uncertainty policy

Use square brackets so editorial intervention is searchable:

- `[uncertain: reading]` when a tentative reading is plausible but not secure.
- `[illegible]` when no responsible reading can be made.
- `[missing at edge]` when the physical image omits the text.
- `[uncertain block begins]` and `[uncertain block ends]` around a sustained damaged passage.

Reconstruct only when the visible letters, grammar, and independent evidence strongly support the reading. Never fill a gap merely because a phrase sounds likely.

## 7. Validate names and locations

1. Make a separate pass over every personal name and place name.
2. Compare repeated names elsewhere in the same issue and in adjacent issues.
3. Check initials, honorifics, postal abbreviations, possessives, and period spelling variants.
4. Use external reference sources only as corroboration. The newspaper image remains the authority for what was printed.
5. If a reference source conflicts with a legible printed form, transcribe the printed form and mention the variant in a validation note if important.

## 8. Independent review

1. Have a second reviewer examine the transcription without relying solely on the first reviewer's conclusions.
2. Prioritize metadata, proper names, locations, numbers, headlines, clipped edges, and all bracketed passages.
3. Record corrections with source page and column context so changes can be audited.
4. Apply only corrections that are supported by the scan or strong repeated evidence.

## 9. Package and quality-check each issue

1. Give each file a stable name: `Newspaper_YYYY-MM-DD_VolX_NoY_Transcription.ext`.
2. Include a transcription note explaining reading order, preserved features, and uncertainty notation.
3. Verify the expected number of source-page and column markers.
4. Count words and uncertainty markers; investigate unexpectedly low or high values.
5. Search for recognition debris, duplicated lines, missing column sections, editor comments, and stray processing tokens.
6. Open the TXT as UTF-8 and confirm that punctuation and brackets are intact.
7. Render every DOCX page to images and visually inspect headers, page breaks, paragraph flow, uncertainty styling, page numbers, clipping, blank pages, and orphaned headings.

## 10. Preserve the audit trail

Keep the original PDF, rendered pages, crop coordinates, raw OCR outputs, reconciled working files, review reports, and final deliverables in separate folders. This makes later corrections reproducible without obscuring which text came from the source and which text reflects editorial judgment.

## Suggested project layout

```text
project/
  source/
  rendered_pages/
  crops/
  ocr_raw/engine_a/
  ocr_raw/engine_b/
  reconciled/
  validation/
  outputs/
  issue_manifest.csv
```

## Release standard

Call the result a high-accuracy, OCR-assisted research transcription, not a fully diplomatic edition, unless every line has received human visual verification. Before quoting a bracketed passage in publication, return to the cited source page and column.
