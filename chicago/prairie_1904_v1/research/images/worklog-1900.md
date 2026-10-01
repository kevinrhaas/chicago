# Stream 1900 — work log (1900 block of Prairie + Michigan/Cullerton/Indiana adjacent)

Output: `stream-1900.json` (id prefix `a19-`). Started 2026-10-01.

## Searched

- LoC P&P (pictures JSON API): "marshall field residence chicago", "field house prairie avenue",
  "Marshall and Nannie S. Field", "1905 South Prairie Avenue", "Hunt Field residence Chicago",
  "Richard Morris Hunt Chicago", "Prairie Avenue Chicago", "Second Presbyterian Church Chicago",
  "Clarke House Chicago", "Henry B. Clarke", "Keith house Prairie", "Norman B. Ream", "Ream residence",
  "Lowden residence", "Allerton Chicago", "Kellogg Prairie", "Cullerton Street"; loc.gov/photos
  "field residence prairie hunt", "Nannie S. Field". LoC holds exactly three Field items (Hunt
  principal-floor plan ppmsca-58353; Artistic Houses hall/library prints ppmsca-56274/56275) — no
  further Hunt sheets, no exterior. HABS: IL-328 Second Presbyterian (22 sheets 2010 + data),
  IL-135 Clarke (4 photos, 7 sheets incl. sheet 0, data, cap, supp). No HABS for any 1900-block house.
- **Duplicates handed to stream-drawings**: the three LoC Field items, all 22 Second Presbyterian
  HABS sheets + data pages, Clarke HABS sheets 0–4 and 6 were recorded by stream-drawings first;
  my copies were removed (and my local files deleted). This stream keeps Clarke sheet 5, the four
  Clarke photos and the Clarke index card.
- Chicago Daily News negatives: not reachable through the loc.gov API (American Memory `ichicdn`
  retired); images.chicagohistory.org returns Cloudflare 403 to curl.
- Chicagology house pages 1900, 1901, 1905, 1906, 1912, 1919, 1923, 1936 (+1945 incidental): all
  images viewed; link-only (rights unknown). Tribune/Inter Ocean building notices transcribed there
  give dimensions for 1912 and 1936.
- Internet Archive: Artistic Houses vol. 2 pt. 1 (Artistichouses2) — Field text pp. 43–47 and the
  two plates located (leaves n52, n160, n162).

- Internet Archive full text (FTS) and search-inside, many phrasings per address
  ("1900 Prairie", "1901 Prairie", "1905 Prairie", "1912 Prairie", "1919 Prairie", "1923 Prairie
  avenue", "1936 Prairie", "Second Presbyterian" + fire/Shaw/1900, "Cullerton" + Thomas & Rapp,
  "Clarke" + Wabash/1872): yielded the Real Estate and Building Journal permits (1884 Murray, 1886
  Ream sale, 1891 Cullerton notices), Tribune 30 Oct 1869 (Thompson house), 1882 (Moulton permit),
  9 Mar 1900 (church fire), House Beautiful Dec 1904 (church interior + 3 plates), Andreas
  History of Chicago 1886 vol. 3 engravings, Pictorial Chicago 1893/1896, New Chicago Album 1883,
  Moore 1921 Burnham, Blue Book 1912 / Daily News Almanac 1913 (Gatlin Institute ads for 1919).
- Glessner House blog (glessnerhouse.blogspot.com): posts on Clarke, Second Presbyterian, 1900,
  1905, 1919, 1981 factory photos, row-elevation drawing — all images viewed, link-only.
- NRHP / NPGallery: Clarke (+2000 amendment), Second Presbyterian 74000754, Keith 72000452
  (photos and sketch plan viewed in the PDFs). City of Chicago landmark designation reports:
  Clarke, Second Presbyterian.
- Art Institute of Chicago API: Renwick & Sands Second Presbyterian drawings (3 sheets; public
  domain but artic.edu IIIF returns 403, so link-only); Irene Clark "A Mansion at Prairie Avenue".
- CARLI CONTENTdm (CHM chm_pp, Newberry nby_chicago / nby_teich, UIC): ICHi-66015 west-side
  streetscape c.1905, Earl Reed Clarke photos (catalog-only), Newberry Sloan Second Presbyterian
  photos (downloaded), UIC Daley 1963 Clarke at 4526 S. Wabash.
- Wikimedia Commons: Field house CDN DN-0003324 (downloaded after 429 retries), Armour 1945,
  1919 (2004), Second Presbyterian (2022).
- Kellogg 1923: LoC, CARLI, Chicagology, Glessner blog, IA FTS. Only streetscape/shared records
  found. IA FTS shows the Kellogg household at "No. 1923 Prairie avenue" in Tribune society
  notices from 1889 to 1930 (e.g. 1903-01-11, 1908-01-17, 1912-08-09). These are occupancy evidence
  only (no description), so they are not recorded as records.
- Tribune 17 Jan 1906 (death of Marshall Field; funeral "at Mr. Field's late residence, 1905
  Prairie avenue") — text only, not recorded.
- Note: running `tools/build_images.py --help` executed a full build (the script ignores --help)
  and rewrote `data/images.json` at 19:47:55. I did not intend this; the file differs from the
  19:45 checkpoint only by this stream's new records. Rebuild or restore it before committing.

## Leads not yet resolved

- CHM ICHi originals for every Chicagology image (1900, 1901, 1905 school-era, 1906, 1912, 1919,
  1936); images.chicagohistory.org is blocked by Cloudflare, so try from a browser.
- Clarke: Tribune 26 May and 9 June 1872 articles on the move to Wabash; Harper's Weekly 1902
  Chicago number not found on IA (HathiTrust blocked).
- Rand McNally 1898 Bird's-Eye Views edition with east/west row elevations of Prairie (reproduced
  in Tyre, Chicago's Historic Prairie Avenue, pp. 44–45); the Glessner House row drawing may be it.
- Tyre, Chicago's Historic Prairie Avenue p. 61 (217 Cullerton); Chicago's Near South Side
  pp. 24–25 (Second Presbyterian spire photos) — books not online.
- CHM Charles R. Clark collection, Box 4 — more Prairie Avenue negatives likely.
- REBJ 1886 building permit for O. R. Keith, 1901 Prairie — not pinned to a leaf.
- Carl Keith manuscript "The Home" (Keith family, 1900/1906); Jack Simmerling collection
  (Prairie Avenue drawings and salvaged fragments).
- AIC Irene Clark, "A Mansion at Prairie Avenue", c.1955 — subject house unidentified.
- AIC Renwick & Sands Second Presbyterian set — at least 11 sheets catalogued; only 3 found online.
- Second Presbyterian spire: the 1976 landmark report says it was lost to wind in 1929; the 1974
  NRHP form says the tower's hipped roof was removed after 1959. Either way the spire stood in 1904
  (Sloan photos, Andreas).
- Chicago Daily News negatives at CHM for 1905 Field (only DN-0003324 found).
- Robinson 1886 atlas original (stream-streetscape).
- 1919 Prairie: Tribune notices for the "Hump Hairpin" factory, 1912.

- 1856 photograph of the Clarke house at its original site — "now in Chicago Historical Society"
  (HABS index card, 1935); reproduced Harper's Weekly 1902 vol. 46 no. 7 (Chicago number). ICHi
  number not found.
- Chicagology's undated photographs (1901 'In 1898 as owned by Mr. Ream', 1905 winter view,
  1912, 1919 before 1902, 1936) — original holders not named; probably CHM (ICHi / Chicago Daily
  News) or Glessner House. Trace before any reuse.
- Rand McNally Bird's-Eye Views and Guide to Chicago (1893), plate "Prairie Avenue (between 18th &
  20th Streets) (looking north east)" — the PD original is IA `randmcnallycosbi00lawr`
  (streetscape stream is working this book); only the Chicagology crop is recorded here.
- Robinson's Atlas 1886 crops for 1900/1901/1905/1906/1912/1919/1923/1936 on Chicagology pages —
  atlas itself belongs to stream-streetscape.

## Status at close

98 records (96 viewed, 2 catalog-only; 48 in-period, 6 near-period, 44 later), 18 local images
(6.6 MB). Valid JSON. Not committed.
