# The 1904 Prairie Avenue street surfaces (T-1728)

What the roadways, alleys, walks, curbs and parkways of T-0474's grid were made of on
**1 July 1904**, and how sure we are. The answer lives in `data/street_surfaces/1904.json`
(authored; held by `tools/check_street_surfaces.py`), is drawn by
`renderers/web/js/street-grid.js`, and is textured from `assets/textures/prairie_1904_pbr/`.
`python3 tools/check_street_surfaces.py --table` prints every surface.

## 1. The evidence rule

The owner's ask (2026-09-28): *"make sure we have the street and materials and how the road and
sidewalks were laid out"*. The ticket's rule, from the Prairie library's own warning, is that **a
citywide paving report does not identify a particular block's surface**: it bounds, it cannot assert.
So a block's surface here is

- **attested** only where a city record names it for that block on both sides of the scene date, or
  names it worn and out of its guaranty after it;
- **inferred** where a record orders it or lets its contract and nothing read confirms it was laid;
- **reconstructed** otherwise, with a liberty (L296, L297).

The checker makes the library's warning a rule: `bounding_only_sources` (the 1904 paving report and
the 1905 code) can never attest a block, and cannot carry an inferred one alone.

## 2. Sources read

| id | what it gives here |
|---|---|
| `chicago_council_proceedings_1902_v49` | 28 Apr 1902: ordinance for asphalt on Prairie 16th–22nd (superseded); 22 Sep 1902: asphalt ordinance for Indiana 18th–39th; the Board of Local Improvements' 1902 curbing vocabulary (sandstone curbstones; a combined curb and gutter named in titles) |
| `chicago_council_proceedings_1903_v50` | 9 Feb 1903: ordinance for **curbing, grading and paving with asphalt Prairie avenue, from 16th street to 20th street** (p. 2067) |
| `chicago_council_proceedings_1904_v52` | 2 Nov 1903: the Board's report on every street it had paved since 1901 — **"Prairie avenue from 16th street to 20th street. Good condition"** (p. 1390) — and, by omission, that nothing else in the grid was a Board paving of 1901–03 |
| `chicago_council_proceedings_1905_v54` | 1 Dec 1904: the Superintendent of Streets' ward survey of worn pavements out of guaranty — **18th (Indiana–Calumet), 20th (Indiana–Calumet), 21st (Michigan–Calumet), Prairie 20th–22nd and Calumet (21st to 403 ft N of 20th), all macadam** (p. 1699) |
| `chicago_council_proceedings_1907_v58` | 7 Nov 1906: the Board's three-year condition report — Prairie 16th–20th asphalt (R. F. Conway Co.), Prairie 20th–22nd asphalt (Barber), Indiana 18th–39th asphalt, the alley west of Prairie 20th–21st rock asphalt |
| `chicago_council_proceedings_1899_v43` | 1899: asphalt contract for 16th St (Michigan–Prairie) to J. H. Covode; asphalt for Calumet 21st–31st to the Standard Paving Co.; brick ordinance for Indiana 16th–18th; asphalt roll for 22nd St (Indiana–IC) filed |
| `chicago_council_proceedings_1903_v51` | 11 May 1903: rock asphalt ordered for the alley west of Prairie, 20th–21st; 28 Sep 1903: the Council presses for Indiana's east side |
| `chicago_council_proceedings_1904_v53` | 28 May 1904: the city consents to the South Park Commissioners taking Prairie 16th–23rd and 16th St as a boulevard |
| `south_park_commissioners_statutes_1908` | the effective consent (30 Oct 1905) and the Commissioners' taking (24 Oct 1906) |
| `south_park_commissioners_municipal_code_1897` | no Prairie Avenue boulevard in 1897; the Chicago City Railway's double track on Indiana and 18th St (horse cars, 1896) |
| `alvord_street_paving_report_1904` | the library's `civic-paving-1904`: Chicago's 1,371 miles of improved way at 1 Jan 1904 (52 % cedar block, 31 % macadam, 10 % asphalt, 5 % brick, 2 % stone block) and which pavement suited which street — a bound only |
| `chicago_revised_municipal_code_1905` | the materials a walk, curb or roadway could legally be (secs. 1944, 2062, 2066, 2068, 2070, 2072, 2077, 2079) — a bound only |
| `habs_glessner_house_il_1015_photographs` | nos. 2 and 3 (c. 1923): both Glessner frontages — jointed pale walk, grass parkway, pale jointed curb; a later bound only |

All the Proceedings were read in the Internet Archive's OCR of the Newberry Library's copies, found
through the Archive's full-text search. The Glessner House's own records were not reachable.

## 3. Which authority kept a "boulevard" in 1904 — the city

The 1911 Sanborn sheets print **"Prairie Av. Blvd."** and **"E. 16th St. (Boulevard)"**, and the
ticket asked who paved and kept a boulevard in 1904. **Prairie Avenue was not one yet.** The South
Park Commissioners' 1897 code lists no Prairie Avenue boulevard; the city
consented on 28 May 1904 and again, effectively, on 30 October 1905; and the Commissioners **selected
and took** Prairie Avenue from 16th to 29th Street and 16th Street from Michigan to Prairie on **24
October 1906**, to connect Michigan Boulevard with the South Park. On the scene date both were city
streets: paved by special assessment through the Board of Local Improvements and repaired by the
Department of Public Works — which is exactly who reports them in 1903, 1904 and 1906. The 1911
designation is therefore a later fact, and L293's caveat that "a boulevard ordinance could have fixed
a different section" does not reach 1904.

## 4. What each surface is, and why

**Prairie Avenue, 16th–20th — sheet asphalt, ATTESTED.** Ordered 9 February 1903; down and "Good
condition" on 2 November 1903; "asphalt. R. F. Conway Co., contractor. In good condition" on 7
November 1906. Two records either side of the scene date. This is the roadway the /1904/ door looks
across.

**Prairie Avenue, 20th–22nd — macadam, ATTESTED.** The 1902 asphalt ordinance ran to 22nd Street but
was superseded by the 1903 one stopping at 20th. On 1 December 1904 the block is macadam in need of
repair with its guaranty expired, and it is absent from the Board's 1901–03 list, so it predates 1901.
It was repaved in asphalt (Barber) before November 1906 — after the scene.

**E. 18th, 20th and 21st Streets — macadam, ATTESTED** (the same December 1904 survey, the same
omission from the 1901–03 list). **Calumet Avenue** 20th–21st: macadam, attested; 21st–22nd: the
asphalt let in 1899, inferred; 18th–20th: macadam carried round the curve from the attested south
403 ft, reconstructed (L297).

**E. 16th Street, E. 22nd Street, Indiana 16th–18th — INFERRED** from 1899 contracts and ordinances
(asphalt, asphalt, brick) whose completion is not read.

**Indiana Avenue 18th–22nd — sheet asphalt, RECONSTRUCTED as finished** (L297): ordered 1902, pressed in
September 1903, finished somewhere between November 1903 and November 1906.

**Alleys — graded earth and cinders, RECONSTRUCTED** (L297). Only one has a record: the alley west of
Prairie between 20th and 21st was ordered paved with rock asphalt in May 1903 and was paved between
November 1903 and November 1906; it is drawn as it stood before.

**Walks — Portland cement concrete in 5 × 6 ft blocks; curbs — sandstone curbstones; parkways and the
foot inside the walk — mown turf. All RECONSTRUCTED** (L296), on all 31 block faces, both sides of
Prairie from 16th to 22nd and every cross-street face. The code allows cement, limestone or cinder
walks and no new wooden one; stone or white-oak curbs (concrete with a concrete walk); grass plats.
The Council's own sidewalk business turns from plank to cement between 1899 and 1902. The 1903
Prairie title names curbing and no combined curb and gutter, which the Board's 1902 full-text
ordinances would call sandstone curbstones. The c. 1923 views show a jointed pale walk, turf and a
pale jointed curb on both Glessner frontages. The walk block is 5 ft along a 6-ft walk and 6 ft along
16th Street's 5-ft walk (sec. 2062).

## 5. What the c. 1923 photographs add, and do not

HABS no. 2 (Prairie Avenue, c. 1923) shows from the house outward: a pale walk laid in jointed slabs,
a paved crossing from the front door over the grass to the curb, turf with a young tree, a pale curb
in straight jointed lengths, and a smooth pale roadway. No. 3 (18th Street) shows turf at the wall,
the same walk, turf, and the same curb. They fix the ARRANGEMENT (walk – parkway – curb) T-0474
reconstructed and are consistent with the materials chosen; they cannot separate a stone curb from a
concrete one at this resolution, and they are nineteen years late. The door-to-curb crossing is not
drawn: nothing dates it to 1904. No. 1 (1963) shows 18th Street as patched asphalt.

## 6. The look

Every map is procedural (`tools/generate_prairie_1904_pbr.py`, no photograph sampled) and its look is
reconstructed (L296) — a record that says "asphalt" says nothing of its grey. Tiles are metric: asphalt
4 m, macadam 6 m, brick 2.12 m (20 courses of a 4 × 8.5 in brick with its joint), turf 3 m; the walk
tile is two blocks along and one across its own band, the curb two 6-ft stones along and one across. A
square tile is laid on the world axis nearest its street, so two segments overlapping through an
intersection draw the same texel; a jointed one follows the record's own frame. Where roadways cross,
the avenue is drawn over the cross street.

## 7. Frame budget

Measured at the /1904/ spawn on the published tree (SwiftShader), before → after: **16 → 20 draw
calls** desktop and **16 → 19** mobile, against a ceiling of 215; triangles 74,049 → 72,829 desktop,
81,123 → 77,601 mobile (the grid is cut into more meshes, so more of it is culled); textures 6 → 27;
the page fetches 1.62 MB more (21 JPEG maps).

## 8. Gaps, and what would close them

- **Walk, curb and parkway materials** — a sidewalk or curbing special-assessment ordinance for these
  blocks read in FULL (the Council prints only titles), the Board of Local Improvements' ordinance
  files, a dated pre-1905 photograph, or Glessner House's own records of its frontage (the museum's
  photograph collection; its Houghton drawings are 1885–87 design drawings).
- **Indiana Avenue 18th–22nd and the 20th–21st alley** — the Board's acceptance records or the
  Department of Public Works' annual reports for 1903–1905 would date their completion.
- **Calumet Avenue north of 20th** — a Department of Public Works street-improvement register.
- **Streetcar tracks** on Indiana Avenue and 18th Street are not drawn (L297); a franchise map would
  place them.
- **No crown, gutter or curb reveal** (L293 still stands).
