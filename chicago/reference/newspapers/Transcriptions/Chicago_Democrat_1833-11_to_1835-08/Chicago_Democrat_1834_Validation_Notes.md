# Chicago Democrat, 1834 - Validation Notes

## Delivery scope

The five supplied PDFs contain 192 physical scans. They represent 46 unique newspaper issues from February 4 through December 24, 1834. October 1, 1834 (Vol. I, No. 44) appears in both the August-September and October-December PDFs; it is delivered once, using both copies as alternate witnesses.

Each issue is delivered separately as TXT and DOCX. The TXT preserves explicit issue-page, source-PDF-page, and printed-column markers. The DOCX is a research reading copy with the same markers and red treatment for bracketed uncertainty.

## Issue and layout audit

- `Jan1834-Mar1834.pdf`: seven four-page issues, February 4-March 25, Vol. I Nos. 11-17. Each page has six printed columns. No March 11 issue is supplied; the printed sequence resumes March 18 with No. 16.
- `Apr1834-May1834.pdf`: nine unique four-page issues, April 1-May 28, Vol. I Nos. 18-26. These pages genuinely use eight printed columns. Four additional scans are alternate witnesses rather than separate issues: PDF pages 25-26 and 31-32.
- `Jun1834-Jul1834.pdf`: nine four-page issues, June 4-July 30, Vol. I Nos. 27-35. Each page has six printed columns. Several leaves sit off-center on a larger backing sheet; all 216 columns were rebuilt against page-specific detected newspaper bounds, with a manual bound for page 8 where pale show-through confused automatic detection.
- `Aug1834-Sep1834.pdf`: eight unique issues from August 6 through September 24, Vol. I Nos. 36-43, plus the duplicate October 1 witness. Each canonical page has six printed columns.
- `Oct1834-Dec1834.pdf`: October 1 through November 26, Vol. I Nos. 44-52, followed by December 3-24, Vol. II Nos. 1-4. Each page has six printed columns.

The publication day printed on the masthead changes from Tuesday to Wednesday after the April 8 issue. Volume II begins with the December 3 issue.

## Transcription and reconciliation method

1. Source pages were rendered at 300 or 400 DPI and reviewed in full-page contact sheets.
2. Mastheads were independently read and visually checked for date, volume, and number.
3. Pages were segmented by their true printed layout: six columns for most of the year and eight for April-May.
4. Every canonical column received an Apple Vision and Tesseract reading. Where the Vision reading was substantially incomplete, the cleaner Tesseract reading was used and labeled as a fallback.
5. Vision confidence below 0.80, unsupported non-Latin OCR glyphs, and fallback conditions were converted to explicit `[uncertain: ...]` markings.
6. Repeated standing matter was compared across issues. Secure recurring readings include J. Calhoun, John H. Kinzie, Gurdon S. Hubbard, Henry G. Hubbard, Hubbard & Co., Newberry & Dole, P. F. Peck, P. Pruyne & Co., Philo Carpenter, Edward W. Casey, G. Spring, and Chicago, Illinois.
7. Structural QA requires the expected number and sequence of issue-page/column markers, valid UTF-8, no NUL bytes, and no unsupported Cyrillic OCR residue.

## Accuracy qualification

These are high-coverage OCR-assisted research transcriptions, not finished diplomatic editions. The scans are extremely dense, and a complete character-by-character human collation of roughly 1,176 printed columns was not feasible in this batch. Ordinary OCR errors may remain even on lines not bracketed, particularly in:

- small advertisements and agent lists;
- price tables, election returns, land descriptions, and columns of figures;
- proper names that occur only once;
- outer and bound edges;
- faded October-December pages and pages with show-through;
- decorative display type.

Names, locations, and figures should be checked against the scan before scholarly quotation. Bracketed passages identify the clearest known risks but should not be treated as an exhaustive error inventory.

## Recommended next scholarly pass

For publication-grade text, collate the delivered TXT column by column against the saved high-resolution crops, beginning with bracketed text and numeric/name-heavy advertisements. The October 1 duplicate and the April-May alternate page witnesses should remain available as comparison sources.
