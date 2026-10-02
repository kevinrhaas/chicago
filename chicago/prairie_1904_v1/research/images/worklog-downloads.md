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
- Phase A finished ~16:25: 216 downloaded, 3 failed (above). Rights changes applied to 40
  records (listed below).
- Phases B/C/D finished ~17:35, 0 failures: 33 newly cleared images, 14 HABS measured
  drawings (Second Presbyterian sheets 11–22, Clarke sheets 3–4; LoC's IIIF server returned
  HTTP 500 for these and its v.jpg service copy is only 1024 px, so the bilevel TIFF masters
  — 0.4–17 MB each — were fetched and reduced to 2000 px), and 53 single-page periodical /
  book text pages from archive.org (Inland Architect, American Architect, Industrial Chicago,
  House Beautiful, Monroe, Engineering Record, American Artisan; located by the `page/nNN`
  in the record's catalog URL; 1400 px is legible for these page sizes).
- Reynertson 1893 Grand View (st-reynertson-1893-grand-view-of-chicago): downloaded as a
  region crop of the near South Side lakefront (LoC IIIF region 4600,5200,2800,1300 →
  2000 px) instead of the whole 14336 px city view; the record's note "Not downloaded" now
  predates this copy.
- AIC: the rights_basis quotes of the AIC holder statement were corrected to each record's
  verbatim CONTENTdm `rtssta` text (three variants) after the first write.

## Totals

| stream | downloaded this pass | MB (display+thumb) | left link-only although PD/NKR (why) |
|---|---|---|---|
| stream-1600-1700.json | 6 | 1.4 | 7 — no direct image (CHM Clark scrapbook PDFs ×4, Inland Architect notices without a page locator ×2, Newberry DPC postcard record is description-only) |
| stream-1800.json | 62 | 7.5 | 5 — 3 chicagology transcriptions (no image), Artistic Houses text (pp. 55–59, multi-page), Cornell ADW record (Cornell returns HTTP 403) |
| stream-1900.json | 14 | 2.6 | 10 — 3 AIC Renwick drawings (www.artic.edu IIIF: HTTP 403), HABS index card (PDF), whole Tribune page 1900-03-09, 1 chicagology transcription (no image), 3 Real Estate & Building Journal notices and Moore 1921 (no page locator) |
| stream-2000-2100.json | 11 | 2.2 | 2 — Monroe 1896 text pp. 154–156 and pp. 281–285 (multi-page) |
| stream-chicagology-north.json | 85 | 18.4 | 23 — chicagology page-text records (no image) |
| stream-chicagology-south.json | 55 | 12.5 | 0 |
| stream-drawings.json | 69 | 17.7 | 6 — HABS data pages (PDF), 3 whole Tribune pages, 2 AABN notices without a page locator |
| stream-newspapers-north.json | 7 | 2.0 | 35 — whole newspaper-page scans of text items (skipped by rule) |
| stream-streetscape.json | 8 | 3.3 | 7 — NRHP 1972 PDF pages ×2, multi-page texts ×3, UChicago maps ×2 (Luna behind reCAPTCHA), Newberry Robinson atlas (JS-only viewer; no plate URL) |
| **total** | **317** (incl. 73 Robinson crops given a display copy) | **67.5** | |

Store after the pass: `tools/sync_image_store.py --check` → 822 files, 102.5 MB, 0 missing,
0 orphans (before: 37.6 MB, 253 files). `research/images/STORE.json` is stale until the next
sync (build_images then reports "missing local" for this pass's files — not a real gap).

Failures (fetch failed twice): a19-aic-2ndpres-renwick-east-elevation, -north-elev,
-transverse (HTTP 403 from www.artic.edu's IIIF to scripted clients). Left link-only.

## Rights changes (unknown — link only → public domain), 40 records

Evidence for each is the stated publication (title, date) — from the record, the holder's
catalogue (AIC CONTENTdm `illust`/`refere`/`datea`/`rtssta` fields, read 2026-10-02), the
archive.org OCR of the issue, or a side-by-side comparison with a public-domain copy already
held. Format: `id` (stream) → rights — basis (as now in the record).

- `a16-ghm-blog-1720-atlas-crop` (stream-1600-1700.json) → public domain — published fire-insurance atlas plate (pre-1929, US): its content pre-dates the 1886–87 Glessner house and its colour scheme, lettering and water-main notes match Robinson's Atlas of the City of Chicago (1886); Glessner House Museum blog reproduction (arrows and a label added — not original expression)
- `a16-newberry-dpc7474-pullman-residence-postcard` (stream-1600-1700.json) → public domain — published as a Detroit Publishing Co. postcard (series no. DPC7474; the firm issued postcards c. 1898–1924) — pre-1929, US. Newberry use statement (a permissions policy, not a copyright claim): 'Images from the Detroit Publishing Company Collection may be re-purposed for personal or educational use. For permission on other uses, contact Digital Initiatives and Services, Newberry Library'
- `a18-gh-hitchcock-galloway-1874-sketch` (stream-1800.json) → public domain — published May 1874 in The Land Owner (Chicago) (pre-1929, US); Glessner House Museum blog reproduction
- `a18-gh-landowner-1874-plate` (stream-1800.json) → public domain — published May 1874 in The Land Owner (Chicago) (pre-1929, US); Glessner House Museum blog reproduction
- `a18-gh-landowner-1874-glessner-site` (stream-1800.json) → public domain — published May 1874 in The Land Owner (Chicago) (pre-1929, US); Glessner House Museum blog reproduction
- `a18-gh-chicago-herald-1887-illustration` (stream-1800.json) → public domain — published late 1887 in the Chicago Herald (pre-1929, US); Glessner House Museum blog reproduction
- `a18-gh-american-contractor-1921-sullivan-1808` (stream-1800.json) → public domain — published 3 December 1921 in The American Contractor (pre-1929, US); Glessner House Museum blog reproduction
- `a18-gh-1811-for-sale-1894` (stream-1800.json) → public domain — published 27 May 1894 in the Chicago Tribune (pre-1929, US); Glessner House Museum blog reproduction
- `a18-gh-1812-first-house-1874` (stream-1800.json) → public domain — published 1874 in The Land Owner (Chicago) (pre-1929, US); Glessner House Museum blog reproduction
- `a18-cgy-1815-meeker-sold-1915` (stream-1800.json) → public domain — published 1 January 1915 in the Chicago Tribune (pre-1929, US); chicagology reproduction
- `a18-cgy-1827-tribune-1882-description` (stream-1800.json) → public domain — published 2 November 1882 in the Chicago Tribune (pre-1929, US); chicagology transcription
- `a18-cgy-1827-fire-1927` (stream-1800.json) → public domain — published 1 January 1927 in the Chicago Tribune (pre-1929, US); chicagology reproduction
- `a18-cgy-1804-tribune-1885-sale` (stream-1800.json) → public domain — published 19 April 1885 in the Chicago Tribune (pre-1929, US); chicagology transcription
- `a18-rba-casc-glessner-1920s` (stream-1800.json) → public domain — published 1926 in the Chicago Architectural Sketch Club annual exhibition catalogue, p. 10 (AIC illustration index, identifier casc.1926_10.jpg) (pre-1929, US); AIC reproduction. Holder's statement: "For publication information please contact the Ryerson and Burnham Archives at archives@artic.edu." (a permissions contact, not a copyright claim).
- `a18-cgy-inter-ocean-1887-palace-avenue` (stream-1800.json) → public domain — published 2 January 1887 in the Chicago Inter Ocean (pre-1929, US); chicagology transcription
- `a19-cgy-1936-tribune-1869` (stream-1900.json) → public domain — published 30 October 1869 in the Chicago Tribune (pre-1929, US); chicagology reproduction
- `a19-cgy-1912-tribune-permit-1882` (stream-1900.json) → public domain — published 18 June 1882 in the Chicago Tribune (pre-1929, US); chicagology transcription
- `a19-cgy-1923-randmcnally-1893` (stream-1900.json) → public domain — published 1893 in Rand, McNally & Co.'s Bird's-Eye Views and Guide to Chicago (pre-1929, US); chicagology reproduction
- `a19-cgy-robinson-1886-crops-1900-block` (stream-1900.json) → public domain — published 1886 in Robinson's Atlas of the City of Chicago (pre-1929, US); chicagology reproduction (crop and arrow added)
- `a20-chicagology-2013-reid-ia1895` (stream-2000-2100.json) → public domain — published February 1895 in The Inland Architect and News Record vol. 25 no. 1 (pre-1929, US); chicagology reproduction
- `a20-chicagology-robinson-1886-crops` (stream-2000-2100.json) → public domain — published 1886 in Robinson's Atlas of the City of Chicago (pre-1929, US); chicagology reproduction (crop and arrow added)
- `a20-glessner-hanford-engraving` (stream-2000-2100.json) → public domain — published December 1883 in The Inland Architect and Builder, p. 147 ('Residence of P. C. Hanford, Esq., Chicago — Jaffray & Scott, Architects'; Paul C. Lautrup del.) (pre-1929, US); Glessner House Museum blog reproduction
- `a20-aic-ia-robbins-plate` (stream-2000-2100.json) → public domain — published 1905 in The Inland Architect and News Record vol. 45 no. 4 (AIC record 'Inland Architect, vol. 45, no. 4') (pre-1929, US); AIC reproduction. Holder's statement: "For Rights information please contact the Ryerson and Burnham Archives at archives@artic.edu" (a permissions contact, not a copyright claim).
- `a20-aic-ia-reid-plate` (stream-2000-2100.json) → public domain — published 1895 in The Inland Architect and News Record vol. 25 no. 1 (AIC record) (pre-1929, US); AIC reproduction. Holder's statement: "For Rights information please contact the Ryerson and Burnham Archives at archives@artic.edu" (a permissions contact, not a copyright claim).
- `a20-aic-quarter-century-tucker-residence` (stream-2000-2100.json) → public domain — published 1898 (AIC record: date 1898, printed matter, Ryerson and Burnham Libraries Book Collection 720.973 I290cv, p. 13) (pre-1929, US); AIC reproduction. Holder's statement: "For Rights information please contact the Ryerson and Burnham Archives at archives@artic.edu" (a permissions contact, not a copyright claim).
- `a20-aic-ia-dewey-residence-drawing-1887` (stream-2000-2100.json) → public domain — published 1887 in The Inland Architect and News Record vol. 10 (AIC record) (pre-1929, US); AIC reproduction. Holder's statement: "For Rights information please contact the Ryerson and Burnham Archives at archives@artic.edu" (a permissions contact, not a copyright claim).
- `cgn-1729-massacre-monument-statue` (stream-chicagology-north.json) → public domain — published 7 February 1909 in the Chicago Tribune (pre-1929, US) — the printed caption 'Statue Commemorating Fort Dearborn Massacre' occurs in that issue (archive.org per_chicago-daily-tribune_1909-02-07_68_6, OCR text); chicagology reproduction
- `cgs-1905-field-library` (stream-chicagology-south.json) → public domain — photograph published 1883–84 in G. W. Sheldon, Artistic Houses (D. Appleton & Co.), as 'Mr. Marshall Field's Library' (pre-1929, US); chicagology reproduction
- `cgs-1905-field-hallway` (stream-chicagology-south.json) → public domain — photograph published 1883–84 in G. W. Sheldon, Artistic Houses (D. Appleton & Co.), as 'Mr. Marshall Field's Hall' (pre-1929, US); chicagology reproduction
- `dw-rb-inland-kimball-1801-entrance-plate` (stream-drawings.json) → public domain — published January 1893 in The Inland Architect and News Record vol. 20 no. 6 (AIC record) (pre-1929, US); AIC reproduction. Holder's statement: "For Rights information please contact the Ryerson and Burnham Archives at archives@artic.edu" (a permissions contact, not a copyright claim).
- `dw-rb-inland-ames-coleman-1811-plate` (stream-drawings.json) → public domain — published October 1888 in The Inland Architect and News Record vol. 12 (AIC record dated 10/1888) (pre-1929, US); AIC reproduction. Holder's statement: "For publication information please contact the Art Institute of Chicago Archives at archives@artic.edu." (a permissions contact, not a copyright claim).
- `dw-rb-building-budget-1887-entrance-sketch-18xx-prairie` (stream-drawings.json) → public domain — published 30 July 1887 in The Building Budget (Chicago) v. 3 p. 97 (AIC record) (pre-1929, US); AIC reproduction. Holder's statement: "For publication information please contact the Art Institute of Chicago Archives at archives@artic.edu." (a permissions contact, not a copyright claim).
- `dw-rb-inland-second-presbyterian-shaw-interior-plate` (stream-drawings.json) → public domain — published 1902 in The Inland Architect and News Record vol. 39 (AIC record dated 1902) (pre-1929, US); AIC reproduction. Holder's statement: "For Rights information please contact the Ryerson and Burnham Archives at archives@artic.edu" (a permissions contact, not a copyright claim).
- `dw-rb-sketch-club-second-presbyterian-shaw-details` (stream-drawings.json) → public domain — published 1902 in the Chicago Architectural Sketch Club annual exhibition catalogue, p. 29 (AIC illustration index, casc.1902_29.jpg) (pre-1929, US); AIC reproduction. Holder's statement: "For publication information please contact the Ryerson and Burnham Archives at archives@artic.edu." (a permissions contact, not a copyright claim).
- `dw-rb-sketch-club-second-presbyterian-shaw-interior` (stream-drawings.json) → public domain — published 1902 in the Chicago Architectural Sketch Club annual exhibition catalogue, p. 28 (AIC illustration index, casc.1902_28.jpg) (pre-1929, US); AIC reproduction. Holder's statement: "For publication information please contact the Ryerson and Burnham Archives at archives@artic.edu." (a permissions contact, not a copyright claim).
- `dw-rb-architects-club-house-kimball-1801` (stream-drawings.json) → public domain — published 1926 in the Chicago Architectural Sketch Club annual exhibition catalogue, p. 11 (AIC illustration index, casc.1926_11.jpg) (pre-1929, US); AIC reproduction. Holder's statement: "For publication information please contact the Ryerson and Burnham Archives at archives@artic.edu." (a permissions contact, not a copyright claim).
- `dw-rb-artistic-houses-doane-1827-hall-stair` (stream-drawings.json) → public domain — photograph published 1883–84 in G. W. Sheldon, Artistic Houses (D. Appleton & Co.) v. 2 pt. 1, and in Chicago and Its Makers (1929) p. 465 (AIC record) (pre-1929 first publication, US); AIC reproduction. Holder's statement: "For publication information please contact the Art Institute of Chicago Archives at archives@artic.edu." (a permissions contact, not a copyright claim).
- `dw-rb-artistic-houses-doane-1827-hall-side` (stream-drawings.json) → public domain — photograph published 1883–84 in G. W. Sheldon, Artistic Houses (D. Appleton & Co.) v. 2 pt. 1 (AIC record: 'duplicate plate from Artistic Houses') (pre-1929, US); AIC reproduction. Holder's statement: "For publication information please contact the Art Institute of Chicago Archives at archives@artic.edu." (a permissions contact, not a copyright claim).
- `st-uchicago-blanchard-1897-street-car-lines-se` (stream-streetscape.json) → public domain — published 1897 by Rufus Blanchard ('New map showing street car lines…') (pre-1929, US). UChicago: 'freely available for personal or scholarly use', attribution requested
- `st-uchicago-1902-surface-street-railroads` (stream-streetscape.json) → public domain — published 1902 in 'Maps on the Chicago transportation problem' (pre-1929, US). UChicago: 'freely available for personal or scholarly use', attribution requested

## Reviewed and left `unknown — link only` (238)

- Glessner House Museum blog/site reproductions of unpublished photographs (George Glessner
  c. 1888–1901 snapshots, family/house photos, 1950s–1980s views) — no publication shown.
- Chicagology copies with no source or publication named (photos, undated engravings incl.
  1701 Hibbard, 1823 Dent, 1906 Keith, 1936 Thompson etching, 2031–35 and 2036 street
  engravings — compared with the Land Owner 1874 plate, Andreas 1884 and Pictorial Chicago
  1893/96: no match), post-1928 Tribune/NYT items (1934–1965), and multi-source page texts.
- AIC Ryerson & Burnham unpublished photographs (J. W. Taylor, Lowe/CHM copies, Earl Reed
  1941–42) and the 8 Renwick 1874 microfilm frames (unpublished drawings; not verified to be
  the same sheets as AIC's three public-domain Renwick artworks).
- NARA/NRHP nominations 1972–2007 and City landmark reports (preparers' photos/drawings),
  UIC 'Copyright not evaluated' items, CPL finding-aid items, the 1911 map annotated 2021.
