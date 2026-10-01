# Worklog — Chicagology follow-up, south half (`stream-chicagology-south.json`, ids `cgs-`)

Session 2026-10-01. Scope: every Chicagology Prairie Avenue address page from 1834 to the end of the
index (39 pages: 1834 1900 1901 1905 1906 1912 1919 1923 1936 1945 2000 2001 2003 2009 2010 2011 2013
2017 2018 2021 2026 2027 2031 2033 2035 2036 2100 2101 2108 2109 2110 2112 2115 2120 2123 2125 2126 2130
2140 — the index lists nothing after 2140). Then a second-source pass for the thin buildings.

Result: **75 records** (35 Robinson 1886 address crops, 27 newspaper items, 9 page-text documents,
3 photographs, 1 publication plate). 53 public domain (dated pre-1929 publications), 22 link-only.
**No local files**: the coordinator stopped new `fetch_image.py` downloads mid-session (site over its
size budget), so every record is link-only with its full-size `image_url`.

## Method notes

- Sucuri challenges ~1 in 5 requests; plain `curl -sL -A 'Mozilla/5.0'` with 15–20 s retries got every
  page. Some responses come gzip-encoded: use `--compressed`.
- Images live under `wp-content/themes/revolution-20/chicagoimages{5,8,9}/`, `postfire2/`, `PreFire2/`,
  `goldenage2/` — not `wp-content/uploads`. No `-NNNxNNN` variants: the `src` file IS the full-size file
  (the HTML `width` attribute only scales it; the Robinson crops are 3841×1482 or 3698×1400).
- Duplicates were checked by `image_url` against every `stream-*.json` (including the parallel
  `stream-chicagology-north.json`), then by page + title.
- Robinson crops: the first pass kept two aggregate records. Here each address crop is its own record
  (distinct `image_url`; the arrow is Chicagology's lot identification). The arrow tip in each crop was
  located by differencing the crop against the median of its group, then checked by eye against the
  printed house numbers. Several arrows are wrong (see conflicts).

## Per page — images found / recorded / skipped

| page | images | new records | skipped (already in collection) | text document |
|---|---|---|---|---|
| 1834 | 4 | 4 (photo, Tribune 1911 headline, Inter Ocean 1911 portraits, Robinson) | — | cgs-1834-text |
| 1900 | 4 | 2 (Tribune 1871 Keith Bros. ads, Robinson) | 1900sprairieelbridgekeith, 1900prairie2024gregory | — (facts already held) |
| 1901 | 3 | 1 (Robinson) | 1901prairie, 1901prairieream | — |
| 1905 | 12 | 5 (library, hallway, Tribune 1937 Mikado, Tribune 1955 headline, Tribune 1955 remnants) | 923prairiefieldhome, 1905prairieC, 1905prairieA, 1905prairieave1955, 1893marshallfieldhouse, Tribune 28 Feb 1955 strip, 1905prairie1886map (a19 aggregate) | — |
| 1906 | 6 | 4 (Tribune 1898 five-house strip, 1896 headline, 1896 suicide scene, Robinson) | 1906prairie, 1906prairieB | cgs-1906-text |
| 1912 | 2 | 1 (Robinson) | 1912prairie | cgs-1912-text |
| 1919 | 11 (1919prairie.jpg shown twice) | 8 (Inter Ocean 1905 headline + portrait, 1919 Gatlin programme ad, 4 Tribune 2004 images, Robinson) | 1919sprairiebeforealterations, 1919prairie | cgs-1919-text |
| 1923 | 3 | 1 (Robinson) | 1923prairie1893randmcnally; Evening Post 1868 Kellogg notice = cgn-1709-evening-post-1868-kellogg-notice | — |
| 1936 | 4 | 1 (Robinson) | Tribune 1869, 1936prairie, 1936prairieetching | — (1869/1912/1915 facts already held) |
| 1945 | 2 | 1 (Robinson) | 1945sprairie | — |
| 2000 | 1 | 1 (Robinson) | — | — |
| 2001 | 2 | 1 (Robinson) | 2001prairie1915 | — |
| 2003 | 1 | 1 (Robinson) | — | — |
| 2009 | 2 | 1 (Robinson) | 2009sprairie | — (Price permit already in a20 note) |
| 2010 | 1 | 1 (Robinson) | — | — |
| 2011 | 3 | 2 (Tribune 1882 auction ad, Robinson) | 2009sprairie | — |
| 2013 | 2 | 1 (Robinson) | williamhreid1895 | — |
| 2017 | 3 | 2 (Tribune 1900 Cobb headline → 2027, Robinson) | 2017prairiearmour | — |
| 2018 | 3 | 0 images (see note) | Herrick 1905 headline = cgn-1635-tribune-1905-herrick-headline; 2108prairie1886map recorded under 2108 | cgs-2018-prairie-page |
| 2021 | 2 | 1 (Robinson) | 2021prairie1930 | — (1887 addition already held) |
| 2026 | 4 | 3 (Tribune 1876 headline + dance programme, Robinson) | landowner 1874 | cgs-2026-text |
| 2027 | 1 | 1 (Robinson) | — | — (a20-chicagology-2027-text exists) |
| 2031 | 2 | 1 (Robinson, shared with 2035) | 2031and2035prairie | — (Dewey 1887 already held) |
| 2033 | 2 | 1 (Robinson) | 2033 Walker Evans | — (1869 marble-front note already held) |
| 2035 | 3 | 0 (all shared) | 2031and2035prairie; the 1898 strip and 2031 map recorded under 1906 / 2031 | — |
| 2036 | 3 | 2 (Tribune 1937 Kate Buckingham headline, Robinson) | 2000blockprairieave1880 | cgs-2036-text |
| 2100 | 4 | 2 (Tribune 1902 headline + portrait) | 2100prairie, 2100prairie1886map (a20 aggregate) | — |
| 2101 | 2 | 2 (Tribune 1916 Pike headline, Robinson) | — | cgs-2101-text |
| 2108 | 1 | 1 (Robinson; also on the 2018 page) | — | — (a20-chicagology-2108-text exists) |
| 2109 | 2 | 2 (Tribune 1899 Roloson headline, Robinson) | — | — (a20-chicagology-2109-text exists) |
| 2110 | 4 | 3 (Tribune 2014 headline + move photo, Robinson) | reeshouse1895 | — |
| 2112 | 2 | 2 (Tribune 1893 Rothschild headline, Robinson) | — | — (a20-chicagology-2112-text exists) |
| 2115 | 2 | 1 (Robinson) | 2115prairiearmourmansion | — (1937 razing etc. already held) |
| 2120 | 2 | 1 (Robinson) | 2120sprairie | — |
| 2123 | 1 | 1 (Robinson) | — | cgs-2123-text |
| 2125 | 1 | 1 (Robinson) | — | — |
| 2126 | 1 | 1 (Robinson) | — | — |
| 2130 | 1 | 1 (Robinson) | — | — (the page's Murdoch description repeats the AIC Cobb catalogue text already in a20-aic-cobb-catalogue-residential) |
| 2140 | 4 | 1 (Robinson) | 2140prairie1880, postfire2/2140prairie, byronlsmithdiningroom | — |

`chicagoimages9/2018prairie1940.jpg` ("2018 S. Prairie / About 1940") still returns HTTP 404 — logged in
cgs-2018-prairie-page, not recorded as an image.

## Best finds

- **Chicago Tribune, 9 Jan 1898, five-house entrance strip** (cgs-tribune-1898-01-09-death-strip, PD):
  pen vignettes of the fronts of 1905, 1906, **1923, 2035 and 2108**. It is the first individual depiction
  of 1923 Kellogg and 2108 Kimball, and it shows 2035 as a detached house with a broad columned veranda.
  It also shows the scroll iron fence at 1905 Field in 1898. Companion of the 1600–1812 strip already held
  (a16-cgy-tribune-1898-prairie-widows).
- **1919 Gatlin Institute programme advertisement, 1919** (PD). This is a third near-period exterior of
  the enlarged Field Jr. house: the same viewpoint as the 1913 almanac advertisement, but a different
  exposure with a 1910s car.
- **2027**: its Robinson 1886 crop is the only image of the house. It shows a brick house with a stepped
  rear on lot 15, with frontage figure "60" printed there. This fits the Tribune's "wide, rambling, red
  brick house".
- **Robinson per-address crops for 2108, 2109, 2112, 2126, 2130.** These give the 1886 footprints, or
  show the lot vacant, for the thin buildings. The arrow analysis below corrects two of the first pass's
  "empty lot" readings.
- **Page text documents:**
  - 1906 Keith: lot 59 × 176 ft (1868). The house was split into two residences in 1898 and a second
    ground-level entrance was added at its north end. It was later the Esther Club and was razed in 1942.
  - 1912: the 1908 sale notice gives a "three story brown stone" house on a lot 56 × 176 ft, 190 ft north
    of 20th Street. The house was razed in 1939.
  - 1834 Jones: there was a third floor by 1942, when the house was in apartments; it was wrecked in
    February 1942.
  - 2036 Buckingham: the family lived there until 1923. Interiors were then rebuilt in Kate Buckingham's
    Lake View Avenue co-op and the house was razed.
  - 2026 Wahl: a brownstone mansion with a ballroom on the whole top floor.
  - 2101 and 2123: permit dimensions for later additions.

## Conflicts / mislabels found (flagged in the records)

- **2108 "Empty lot" (Chicagology caption, repeated in a20-chicagology-robinson-1886-crops) is wrong.**
  - The arrow points at the vacant lot that the 2110 page also arrows. That lot is the later Rees lot,
    built on in 1888.
  - The plate prints 2108 and "25.8" over the next lot north, a narrow brick house with a stone front.
  - The 1887 directory and the 1898 Tribune vignette also show 2108 standing.
- **2125 "Empty lot"**: the arrowed lot, printed 2125, carries a small frame footprint.
- **2109**: the arrow ends on a lot with no footprint (printed 2107, 30 ft). Roloson is listed at 2109
  in 1880–85, so the 2109 footprint is unresolved from this plate.
- **2021**: the arrow is misplaced on lot 11, which the plate prints as 2017 and which the 2017 crop also
  arrows. The plate puts 2021 on lot 14, a narrow brick house with a stone front.
- **1919 and 1923** arrows end at almost the same spot. Use the printed numbers instead: 1919 is the
  narrow lot 4, and 1923 is lot 5 with its 100 ft frontage.
- **2001 and 2003** both point at the 20th Street corner lot. **2009 and 2011** both point at lots 7–8.
- **2031 and 2035 share one crop**, and Chicagology captions it with both addresses.
- **The 1898 vignette of 1906** shows a tall side bay and portico, not a mansard. This supports the 1900
  stream's reading that the mansard photo Chicagology labels 1906 (a19-cgy-1906-keith-photo) actually
  shows 1900.
- **1905 "The Hallway"** is the Artistic Houses hall photograph *mirrored* left to right. Do not use it
  for orientation. "The Library" is the Artistic Houses library, the right way round.
- **1919 page:** the Inter Ocean of 10 Jul 1903 quoted there ("1817 Prairie … 20×177 feet") cannot be
  the 1919 house.
- **Tribune 2004 article on 1919** gives 1902 completion, about 30,000 sq ft, 43 rooms and $65,000 in
  1890. The page itself gives 21,000 sq ft and 15 bedrooms.
- **2018 Prairie** is the Herrick house on the west side. It is distinct from 2018 S. Calumet (Wheeler–Kohn).
  The Robinson crop on its page is the 2108 file.

## Thin buildings — second-source pass

| building | what was searched | result |
|---|---|---|
| all thin ones | Glessner House blog, Blogger JSON feed `q=` for 40 terms: Roloson, 2109, Kellogg, 1923, 2027, Silas Cobb, 2035, Horatio Stone, 2031, Tolman, Dewey, 2033, Otis, Murdoch, 2130, 2021, James High, Philip Armour, 2115, Rothschild, 2112, Mark Kimball, 2108, Robbins, 2126, Edson Keith, 1906, Moulton, 1912, Lowden, Blackstone, Hanford, Cullerton, Calumet Avenue, Wahl, Buckingham, Esther Club, Pike, Gorton, Papin. Every hit was compared with the catalog URLs already in the collection, and the unused posts that name these houses or streets were read for images and text | no new image of any thin building. "Prairie Avenue and Louis Sullivan I" (2020) names Max M. Rothschild of 2112 as an Adler & Sullivan client, but only for commercial work. "Woman's Athletic Club" (2013) has social history at 2115 and no house image. "A landmarked White Castle…" (2021) has a 1923 photo of 22nd Street looking west at Prairie: the south side of 22nd, with 2206–08 Prairie at left. That is out of this scope and is left as a lead for the streetscape stream |
| 2027, 2109, 1923, 2035, 2031, 2033, 2130, 2021, 2115, 2112, 2108, 2126, 1906, 1912 | Internet Archive full text (djvu.txt), grepped for owner names and numbers in: Picturesque Chicago 1882 (`picturesquechica00chic`), Picturesque Chicago (`picturesquechic00unkngoog`), Chicago and Its Environs 1891/1893 (`chicagoitsenviro00schi`/`01schi`), Andreas *History of Chicago* vol. 3 (`historyofchicago03andruoft`), *Chicago and Its Distinguished Citizens* 1881 (`chicagoitsdistin00wood`) | no residence plates or addresses for these houses. Andreas vol. 3 has only biographical index entries (Murdoch, Kellogg firm). Inland Architect 1883–1911 and Industrial Chicago were already grepped in full by the first pass and were not repeated |
| 2130, 2109, 2112, 2027, 1923, 2035, 2031, 1906, 1912 | AIC Ryerson & Burnham CONTENTdm API (mqc): Murdoch, Roloson, Rothschild, Kellogg, Cullerton, "2027/2031/2035/2109/2112/1923/1906/1912 Prairie", Tolman, Lowden, Blackstone | nothing for these houses. The "Roloson" hits are the FLW Calumet rowhouses and an Evanston house of 1909; the "Lowden" hits are Sinnissippi Farm, Oregon IL |
| all | LoC (loc.gov/pictures and loc.gov/search JSON) | **blocked**: HTTP 403 Cloudflare "Just a moment" on every request this session |
| all | Wikimedia Commons API | rate-limited after one call; nothing relevant in the one result |
| 2008 & 2018 S. Calumet, 213–217 E. Cullerton | Chicagology streets index (no Calumet Avenue or Cullerton Street section exists); Glessner blog (Hanford, Calumet Avenue, Cullerton); AIC (Cullerton) | nothing new beyond the posts already used by the first pass (Unearthing Hanford, Simmerling tribute) |

## Leads for the next pass

- **ProQuest Historical Newspapers: Chicago Tribune, 9 Jan 1898.** The article "Four blocks on Prairie
  Avenue peopled by widows and widowers…" may carry more vignette strips than the two Chicagology shows,
  and a clean scan would help.
- **Chicagology `2018prairie1940.jpg`** (404). Ask the site, or check the Wayback Machine, for the c.1940
  photograph of 2018 S. Prairie.
- **2109 footprint:** check the 1891 Greeley-Carlson atlas (st-greeley-carlson-1891-prairie-environs) and
  the 1911 Sanborn. Decide whether Roloson's house is the narrow stone-fronted house on the 25.8 ft lot.
- **2036 Buckingham interiors** are said to have been rebuilt at 2450 Lake View Avenue in 1923–24. A
  building record of that co-op may preserve them.
- **1906 "second entrance 1898"**: find the permit (UIC permit ledgers) behind Chicagology's statement.
- **Glessner blog, 2021-07 White Castle post**: the 1923 photo of 22nd Street at Prairie, south side, for
  the streetscape stream.
