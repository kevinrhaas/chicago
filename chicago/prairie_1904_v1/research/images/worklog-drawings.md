# Work log — stream-drawings (architects' drawings, measured drawings, permits, period publications)

Session 2026-10-01. Output: `stream-drawings.json` (prefix `dw-`). Local files: `files/dw-*` (public-domain /
no-known-restrictions only). Duplicates with the parallel block streams were removed after a cross-check by holder
item id + page (see "Overlaps" below).

## Searched (per source)

| source | how | result |
|---|---|---|
| LoC Prints & Photographs (JSON API `loc.gov/pictures/search/?fo=json`, `loc.gov/photos/?fo=json`) | queries: prairie avenue chicago (habs); Second Presbyterian; Clarke; Wheeler Calumet; Cullerton; Keith/Reid Prairie; Marshall Field (1905 Prairie, Nannie S. Field, Hunt); Pullman; Kimball; Artistic houses; Doane; Beman; Burnham & Root | **Hunt's Field principal-floor plan (ppmsca-58353)** + 2 Artistic Houses plates; HABS IL-328 Second Presbyterian (22 sheets, 2010–11 + 1998 plan); HABS IL-135 Clarke (7 sheets, 1935). Kimball HABS il0136 has photos only (no sheets). No HABS for Keith, Reid, Wheeler-Kohn, Cullerton rowhouses. Glessner il0118 already held — not redone. |
| HABS data PDF il0992 | downloaded, pdftotext | materials (Joliet limestone S+E, common brick N+W), tower at SE corner |
| Art Institute API (api.artic.edu) | Second Presbyterian, Renwick and Sands, Beman, Kimball, Pullman, Field, Shaw, Robbins | Renwick 1874 originals 2000.4.2/.4/.11 (already in stream-1900 → dropped here). IIIF download refused (HTTP 403 via proxy). Nothing for Shaw's 1900 rebuild or any Prairie house. |
| Ryerson & Burnham CONTENTdm (artic.contentdm.oclc.org API; `mqc` collection) | searchterm by ~40 owner names; street-field search "Prairie" (222 items) | Inland Architect clippings (Kimball entrance photogravure, Ames/Coleman, Second Pres. interior), Building Budget 1887 entrance sketch, Sketch Club pages (Second Pres. by Shaw; Kimball as Architects' Club), **Renwick drawings for Second Pres. on Burnham Library–UIUC microfilm (roll 26, frames 354–362)**, Artistic Houses Doane plates, Gorton 2120. Rights: holder says contact archives → link-only. |
| Internet Archive — The Inland Architect (879 items 1883–1911) | downloaded every item's hOCR search text + page index (59 MB, scratch only) and regex-scanned for ~50 owner names and 16xx–21xx Prairie / 20xx Calumet / 19xx Michigan addresses | dozens of hits; plates for Hanford (1883), Robbins (1905), Gorton (1896) downloaded/linked; architects' reports with footprints/costs (Murray 1919, Meyer 2009, Buckingham portico, Farwell 1625, Hibbard 1616, Moulton, O. R. Keith/Dixon, Ream). Photogravure-edition plates (Kimball entrance 1893, Reid 1895, Pullman conservatory 1894, Dexter 1891) are NOT in the IA microfilm/bound scans — found as Ryerson clippings instead. |
| Internet Archive — American Architect and Building News (1,000 items ≤1911) | same method | Chicago "Building Intelligence" permit lines: Doane 1881, Dent 1881, Marsh barn 1881, Murray barn 1882 + house 1884, Einstein barn 1628 (1882), Hibbard 1616 (1883), Shortall 1608 (1884), Hanford barn 2010 Calumet (1884), Hamlin 1621 / Farwell 1626 (1885), O. R. Keith (1886), High rear addition (1887), Rees (1888), Dexter alteration + McBirney (1889), Springer flats 1625–35 (1896), Lowden 1712 addition (1898), Second Pres. rebuild (1900); Sherman finished (1876); Dexter gelatine plate (1893, international edition only). |
| Internet Archive — American Architect, second pass (remaining 1,121 of 2,122 items ≤1911; first pass was capped at 1,000 rows) | same method | **Sherman house plate + first-floor plan (Sept. 30, 1876) with full materials text**; Sears plans 1879 (Burnham & Root, 35 × 75 ft); O. R. Keith 1901 permit 1881 (52 × 82 ft, $60,000); Moulton 1912 permit 1882 (45 × 80, Treat & Foltz); Hanford 2008 permit 1883; Schwartz added storey 1887 (1919); Shortall 1600 (Alexander, 1885); Van Arman 2015 (1881); E. G. Keith '916' addition (1878); Strauss warehouse plans for 1609–1611 (Aug. 1905); Wheeler barn 1812 (1884). |
| Chicago Tribune on IA (`per_chicago-daily-tribune_*`, 32k issues) | not bulk-downloadable; IA full-text phrase queries '"NNNN Prairie" cost/architect' for 20 addresses | Hibbard permit 1638 (May 1881); 1638 lot 70 × 160 (1892 ad); 1815 sale with lot 76 × 140 and 'stone, three stories' + Lowden's purchase of 1912 (Dec. 31, 1898). Most phrase hits are social notes. |
| Internet Archive — Industrial Chicago v.1–5, Andreas v.1–3, Western Architect, Sanitary News, Monroe's *John Wellborn Root* | text scan | Industrial Chicago v.1: 1867 Evening Journal review (Wheelock, Cochrane & Garnsey, Van Osdel lists), Moulton/Treat & Foltz, Sherman/Burnham & Root, Edson Keith stone. Monroe: Meyer illustrations + App. B — already in stream-2000-2100 (dropped here). Andreas v.3 text file failed to download (HTML error page); Western Architect/Sanitary News: no Prairie-house hits beyond biographies. |
| Internet Archive full-text search API (`services/search/beta/page_production/?service_backend=fts`) | owner names; quoted "NNNN Prairie" phrases | works; mostly society/directory noise; surfaced the IA collections *National Register Nominations for Chicago* and *City of Chicago Landmark Designation Reports* |
| IA "National Register Nominations for Chicago" / "City of Chicago Landmark Designation Reports" | file lists; downloaded Rees, Kimball, Clarke, Prairie Ave, Glessner NRHP; Prairie Ave District, Wheeler-Kohn, Clarke, Glessner landmark reports | **Rees NRHP (2006): site + 4 floor plans, lot 24.08 × 178.5 ft, permit citation**. Kimball NRHP: photo/text only. Clarke NRHP restoration plans and WK landmark report already in stream-1900/2000 → dropped. |
| NARA S3 NRHP PDFs (72000452 district/Keith, 03000783 Reid, 99000975 Wheeler-Kohn, 74000754 Second Pres.) | re-fetched the held PDFs (byte sizes identical to acquired-files.json) and rendered pages | District p.11 Coleman/Ames sketch plan + elevation, p.22 boundary map, p.24 ownership lot map (lot depths 176 ft / 176 ft 8 in). Reid p.32 plans, WK p.22 plan, Keith p.13 sketches, Second Pres. photos — already in other streams. |
| City of Chicago building-permit ledgers (UIC Digital Collections; IIIF manifests per ledger book) | Book E manifest `iiif/manifest/ark:/81984/d3x921t63`; browsed pages by date | **Rees permit no. 1988 (June 18, 1888) found on folio 257**; incidental find D. Harrison addition at 1818 Prairie (Aug 1886). O. R. Keith 1808 permit not found on Book E pp. 62–91 (June–Aug 1886). |
| 1973 Commission report (reports.chicagolandmarkreports.org) | rendered all 24 pp. | no drawings; bibliography lead: Inland Architect Feb 1888 Keith plate (already held by stream-1800) |
| HathiTrust full-text search | curl + WebFetch | **blocked (HTTP 403 / Cloudflare challenge)** — not searched |

## Overlaps removed (records already in other streams, same holder item/page)
Keith 1888 IA plate + 1886 notice (stream-1800); Kimball 1890 notice (1800); Alexander obituary, Dexter/McBirney/Pullman
Ryerson clippings (1600-1700); Hanford 1883-10 notice, Meyer 1889 note, Reid 1895 plate + Ryerson clipping, Tucker,
Monroe ×4, Reid/WK NRHP plans, WK landmark report (2000-2100); AIC Renwick ×3, Keith NRHP p.13, Clarke HABS sheet 5,
Clarke NRHP (1900); Industrial Chicago p.433 Shortall (1600-1700). Local files for the removed Keith/Monroe duplicates
were deleted.

## Buildings with NO drawings, plans or permit/publication records found in this stream
(only directory/social mentions, if anything)
pa-1612-1 Goodman/Studebaker · pa-1701-3 Hibbard (only the ambiguous 1616 permit) · pa-1812-7 Wheeler (barn permit only) ·
pa-1905-16 exterior elevations (only Hunt plan + interiors) ·
pa-2115-19 Kelley/Armour · pa-1800-22 (held elsewhere) · pa-1900-25 (in stream-1900) ·
pa-213–217-e.-cullerton-street-27 · pa-1816-33 Henderson (cf. 1818 permit) · pa-1906-34 (stone note only) ·
pa-1923-35 Kellogg · pa-2027-37 · pa-2112-39 Rothschild · pa-2108-40 Mark Kimball · pa-2109-41 Roloson · pa-2130-42 Murdoch ·
pa-1702-43 (architect attribution only) · pa-1804–1808 predecessors-44 · pa-1637-45 · pa-1709-46 · pa-1709 successor-47
Palmer Kellogg · pa-1635-48 · pa-1630-50 · pa-1726–1728-51 · pa-1700-52 / pa-1706-53 (Shepley, Rutan & Coolidge Glessner-family
townhouses — nothing found in IA/AABN/Ryerson under Lee or George Glessner) · pa-1708-54 Thorne · pa-1720-55 Tyrrell/Walker ·
pa-2031/2033/2035 rowhouses · pa-1609/1611/1620.

## Unresolved leads (holders identified, not retrieved)
1. **Hunt Collection, LoC (AIA/AAF gift 2010:100, "Unprocessed in PR 13 CN 2010:100")** — the Field plan is "No. 2, office
   copy"; other sheets of the Field set (elevations, sections, upper plans) are likely in the unprocessed lot. Ask LoC P&P
   reference about lot 2010:100 item 78.7080 neighbours; Sam Watters, *The Gilded Life of Richard Morris Hunt* (2024) fig. 3.16.
2. **Photogravure / international editions** — Inland Architect photogravure edition (Reid 1894–95 second plate; others) and
   AABN International/Imperial edition gelatine print of the Dexter house (Apr. 8, 1893). Holders: Ryerson & Burnham bound
   sets; HathiTrust (blocked from here).
3. **Building Budget (Chicago, 1885–1890s)** — July 1887 Cobb & Frost entrance sketch (house no. illegible, 1809/1811?) shows
   it published Prairie Ave. plates; no digitized run found on IA. HathiTrust/Ryerson.
4. **Permit ledgers (UIC)** — use the street-index cards (digital.library.uic.edu/permits-index) to get permit numbers/dates,
   then the ledger books via IIIF. Priority: O. R. Keith 1808 (1886), Kimball 1801 (Oct 1890), Murray 1919 (1884), Doane 1827
   (1881), Dent 1823 (1881), Sears 1815 (1879), Robbins 2126 (1903–04: Book P "North and South Aug 1901–Jun 1904" / Book R),
   Reid 2013 (1894), Second Pres. rebuild (1900, Book N).
5. **Glessner-family townhouses 1700/1706 (Shepley, Rutan & Coolidge)** — SR&C drawings are at the Boston Public Library /
   Shepley Bulfinch archive (not searched); also check AABN 1890s Chicago permits under "Lee" / "Glessner".
6. **Industrial Chicago / Evening Journal 1867** — the original Evening Journal annual review (Jan. 1868) would give the full
   list with exact addresses; Chicago Tribune annual building reviews (Dec./Jan., 1870s–1890s) on IA (`per_chicago-daily-tribune_*`)
   are searchable only by quoted phrase via IA full text; not exhausted.
7. **Andreas, History of Chicago v.3 (1886)** — text download failed (`historyofchicago03andruoft` returned HTML); re-fetch and
   scan for "Prairie avenue" residence descriptions.
8. **Ryerson microfilm (Burnham Library–UIUC 1950–52)** also holds Glessner/Richardson drawings (dozens of frames) — copies of the
   Houghton set already held; not recorded.
9. **Treat & Foltz 1883 "dwelling on Prairie Ave. near Sixteenth St., $21,000"** vs. Hibbard 1616 permit — identify client.
10. **1608 vs 1638 Prairie (Shortall)** and **1712 Prairie (Lowden addition 1898)** — reconcile with the building index.
11. Second Presbyterian 1900 rebuild drawings by Howard Van Doren Shaw — not at AIC API; Shaw papers (Ryerson & Burnham, finding
    aid) to check.
