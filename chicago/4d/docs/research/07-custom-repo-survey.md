# Survey of the custom repo: pre_fire_v1, reference material, and joliet

> **Research dossier — committed verbatim as a citable input.**
> Produced by a research agent on 2026-08-09 for the 4D Chicago project.
> Claims carry their own confidence tags and sources; nothing here is authoritative
> until promoted into `data/` with a resolving `source_id`. Where a source could not
> be retrieved, the gap is stated rather than filled.

---

# Briefing: `/home/user/custom` — Chicago + Joliet

## 0. Repo & git situation

- Repo root: `/home/user/custom`, remote `https://github.com/kevinrhaas/custom`.
- **Current branch: `claude/chicago-1835-walkthrough-plan-01hz6t`** (exists on origin). Other branch: `main` (+ `origin/main`). No worktrees, no stash inspection done.
- `git log --oneline -15` (tip first):
  ```
  f55b4a5 Remove outdated Chicago historical photos and add a new complete map
  3101148 Add new historical photos of Chicago
  7aaf312 Merge pull request #28 — Baseline faceted knight for the chess set
  25012c9 Close the three claims the third review found still untrue
  73a85d8 Remove outline knots that turn by less than six degrees
  26d0f22 Second review: the jowl step was still absent, and the check could not see it
  5e7af13 Fix what the design review found, and make the build assert it from now on
  b7a3271 Check the knight by slicing it, not just by measuring overhang angles
  773a5b8 Refine the knight: one sloped plane for the lip line and jaw taper
  3073e6e Add baseline faceted knight: STL, geometry kernel, reference harness
  fd5b90a Merge branch 'main' of https://github.com/kevinrhaas/custom
  a3a59fb Add new document list-2-gemini.docx to reference materials
  5dbbb9d Add sourced pre-fire building images
  5d4620f Fix hidden years in pre-fire Chicago viewer
  4561cb3 Add Chicago atlas to hosted site
  ```
  The two tip commits (photos) are the only work on this branch beyond the chess merge — i.e. the 1835 walkthrough branch is currently *just* reference-material staging.
- Repo is a mixed workshop: 3D-print CAD projects (alligator-chess, bamboo-vase, chicago-star, garage, ordovician-sandstone, pentaho, …), plus `chicago/`, `joliet/`, `site/`.

---

## 1. `/home/user/custom/chicago/pre_fire_v1`

### What it is
A **research dataset with a static viewer bolted on** — "Chicago Before the Fire — research database v1", covering 1674 → 9 Oct 1871. Explicitly *not* a fabricated parcel census: named/source-identifiable structures only; anonymous totals live separately in `stock_estimates.csv`. Zero dependencies, zero build step, designed from the start to be droppable onto GitHub Pages.

### Full file layout
```
chicago/pre_fire_v1/
├── README.md
├── data/
│   ├── buildings.csv              324 rows, 24 cols
│   ├── building_names.csv         596 rows (canonical + aliases)
│   ├── building_events.csv
│   ├── building_sources.csv       385 links
│   ├── sources.csv                92 source records
│   ├── assertions.csv             1,563 field-level claims
│   ├── stock_estimates.csv        aggregate counts w/o identities
│   ├── media.csv, media_buildings.csv, media_checksums.csv
│   ├── statistics.json
│   └── validation_report.json
├── maps/
│   ├── map_references.csv         14 dated maps w/ provenance
│   ├── city_extent_events.csv     6 effective-dated legal extents
│   ├── landform_events.csv        6 effective-dated landscape events
│   ├── image_checksums.csv
│   └── images/                    14 JPG/PNG (list below)
├── media/images/buildings/        6 building images
├── docs/
│   ├── methodology.md, statistics.md, quality_report.md,
│   │   research_gaps.md, source_acquisition.md, building_image_audit.md
│   └── period_notes/  decade_pre1830_notes.md, pre1830_audit_applied.md,
│                      decade_1830s_notes.md, decade_1840s/1850s/1860s_notes.md,
│                      decade_1870_1871_notes.md
├── schema/  import_order.md, data_dictionary.csv
└── viewer/  index.html (4.0 KB) · app.js (8.6 KB) · style.css (4.9 KB) · data.json (245 KB)
```

### How it works
- **`viewer/index.html`** — hand-written, no framework, no build. Header, a `<input type=range min=1674 max=1871>` year slider + exact-year number input + 14 quick-year buttons (1674, 1779, 1803, 1830, 1831, 1833, 1836, 1840, 1848, 1851, 1853, 1860, 1868, 1871), a map card, four metric/context cards, and a records table (Name / Images / Known span / Type / Historical address / 1871 fire fate / Confidence / Timeline). Assets cache-busted with `?v=4`.
- **`viewer/app.js`** (~140 lines, plain DOM, no deps). Single `fetch('data.json')` → builds two indexes (`namesByBuilding`, `mediaByBuilding`) → `render()` on every input event. Key logic:
  - `cleanYear()` regex-extracts the first `\d{4}` from messy date strings.
  - `activeInYear(row, year)`: built = `year_completed ?? year_started`; active if `built <= year && (demolished == null || demolished >= year)`. **Undated losses stay visible** — deliberate.
  - `closestMap(year)`: sorts all 14 maps by `|reference_year − year|`, ties broken toward the later map; then a `<select>` lets you switch between variants sharing that reference year (1871 has four).
  - `currentEvent()`: picks the latest effective-dated `cityExtentEvents` / `landformEvents` row covering the year.
  - Search is **global across all years**, matching name + aliases + media title/creator/repository + address + type + all three year fields; a "View 1835"-style jump button per row sets the slider to the building's known start year.
  - `escapeHtml()` on everything; images `loading="lazy"`; media paths resolved as `../` + `local_path` (so the viewer lives one level below `maps/` and `media/`).
- **`viewer/data.json`** is a pre-flattened join of the CSVs. Top-level keys and shapes:
  | key | len | fields |
  |---|---|---|
  | `buildings` | 324 | building_id, canonical_name, year_started, year_completed, year_demolished, status, address_historical, latitude, longitude, building_type, fire_fate_1871, confidence, needs_review |
  | `maps` | 14 | map_id, reference_year, map_date, date_precision, title, creator, publisher, map_type, coverage, shows_building_footprints, georeference_status, source_url, local_image_path, width_px, height_px, rights_statement, credit_line, reliability, notes |
  | `cityExtentEvents` | 6 | effective_start/end, event_type, name, legal_or_source_description, approx_area_sq_mi, geometry_status, source_url, confidence, needs_review, notes |
  | `landformEvents` | 6 | effective_start/end, event_type, feature, description, spatial_status, source_url, confidence, needs_review, modeling_instruction |
  | `names` | 596 | building_name_id, building_id, name, name_type, sequence |
  | `media` | 20 | media_id, media_type, title, depicted_year, source_url, local_path, rights_statement, credit_line, created_date, creator, repository, representation_type, accuracy_note |
  | `mediaBuildings` | 9 | media_id, building_id, relationship, confidence, notes |
  | `statistics` | dict | see below |

- **`statistics`**: 324 building records · 92 sources · 385 building↔source links · 1,563 assertions · 14 map refs · 20 media records (14 maps + 6 building images) · 9 media↔building links · 5 buildings with media · **only 15 geocoded records** · 214 `needs_review` · 54 documented 1871 fire losses / 10 probable / 95 unresolved. By period: pre-1830 = 40, 1830s = 55, 1840s = 60, 1850s = 68, 1860s = 59, 1870s = 42. By confidence: high 214, medium 99, low 11.

### Data/images displayed and how organised
**14 maps** (`maps/images/`, referenced by `reference_year`):

| ref yr | file | type | georef | footprints |
|---|---|---|---|---|
| 1830 | `1830_thompson_plat.png` | plat | not_georeferenced | no |
| 1833 | `1833_conley_stelzer_map.jpg` | historical_reconstruction | not_georef | pictorial_only |
| **1834** | `1834_hathaway_map.jpg` | cadastral map | **georeferenced_external** | no |
| 1836 | `1836_mesier_map.jpg` | cadastral_map | not_georef | no |
| 1839 | `1839_chicago_harbor_plan.jpg` | engineering_plan | not_georef | limited |
| 1849 | `1849_rees_rucker_map.jpg` | city_and_vicinity | needs_georeferencing | limited |
| 1853 | `1853_henry_hart_map.jpg` | cadastral_wall_map | georeferenced_external | **yes** |
| 1857 | `1857_palmatary_view.jpg` | birds_eye | not_georef | pictorial |
| 1868 | `1868_ruger_view.jpg` | birds_eye | not_georef | pictorial |
| 1870 | `1870_mitchell_map.jpg` | city_map | not_georef | no |
| 1871 | `1871_pre_fire_view.jpg`, `1871_pre_fire_birds_eye.jpg`, `1871_city_map.jpg`, `1871_burnt_district_relief_map.jpg` | 3 views + fire footprint | mostly not_georef; burnt-district = needs_georeferencing | pictorial/limited |

**6 building images** (`media/images/buildings/`), each with a `representation_type` and `accuracy_note` that the viewer renders as a caution label:
`wolf_point_1833_nypl.jpg` (retrospective lithograph, NYPL) · `wolf_point_1830_andreas.jpg` (retrospective reconstruction, Andreas 1884) · `chicago_1833_newberry.jpg` (retrospective postcard, Newberry/CARLI) · `sauganash_hotel_andreas.jpg` (retrospective lithograph, c.1831–33, Digital Chicago/CHM) · `green_tree_tavern_1859.jpg` (**actual historical photograph**, 1859, Illinois Digital Archives) · `kinzie_house_1857.png` (retrospective illustration).

**City extent events** (6): 1830-08-04→1833-08-04 Thompson's 58-block plat · 1833-08-05→1837-03-03 Town of Chicago · 1837-03-04→1847-02-15 City original limits (lake→Wood St, 22nd→North Ave) · 1847 · 1853 · 1869→1871-10-09.
**Landform events** (6): 1674 portage wetlands · 1830 river mouth/shoreline · 1839 harbor works · 1850–1870 street & building raising · 1852–1871 IC lakefront fill · 1871-10-08→10 burnt district (explicitly "an event layer affecting intersecting properties, not a citywide demolition rule").

### How it is published
- **Workflow:** `.github/workflows/deploy.yml` — `actions/upload-pages-artifact@v3` with **`path: site`**, triggered on push to `main` touching `site/**` or the workflow itself, plus `workflow_dispatch`. It runs one sanity step: parse every `git ls-files 'site/**/*.js'` with `node --input-type=module --check`, falling back to script parsing. Concurrency group `pages`.
- **No CNAME anywhere.** Only Pages marker file is **`site/.nojekyll`**. No `_config.yml`.
- **No symlinks anywhere in the repo.** The published tree is a **byte-identical copy**: `diff -rq chicago/pre_fire_v1/{viewer,maps,media} site/chicago/pre-fire/{viewer,maps,media}` is clean (all four viewer files identical sizes/content).
- **URL mapping:** `kevinrhaas.github.io/custom/` → `site/`. So:
  - `…/custom/chicago/` → `site/chicago/index.html` (a themed landing page with two app cards, aurora backdrop, light/dark toggle persisted to `localStorage['custom.theme']`).
  - `…/custom/chicago/pre-fire/viewer/` → `site/chicago/pre-fire/viewer/index.html` ← **this is the working viewer URL**, and it's the one in `site/sitemap.xml`.
  - ⚠️ **`…/custom/chicago/pre-fire` (no `/viewer/`) has no `index.html`** — `site/chicago/pre-fire/` contains only `viewer/`, `maps/`, `media/`. That bare path will 404 on Pages. If the user is quoting `kevinrhaas.github.io/custom/chicago/pre-fire` as the live URL, either they mean the `/viewer/` child or a redirect stub needs adding.
  - The published copy **omits** `data/`, `docs/`, `schema/`, `README.md` — only the three asset dirs the viewer reads are mirrored. The landing page links back to GitHub for "Research files".
- Root `README.md` documents the "publish only `site/`, keep ~2 GB of CAD out of the artifact" rule and calls it the Polecat platform deploy pattern.

---

## 2. `/home/user/custom/chicago/postfire_1870s_v1` (brief)

"Chicago Rebuilds — 1872–1879 database v1". Same architecture as `pre_fire_v1`, extended into eight **independently researched annual tranches**. Contains: `data/` (buildings, building_events, **building_relationships** predecessor/rebuild links, **potential_cross_year_matches** for entity-resolution review, sources, building_sources, assertions, annual_stock_estimates, media, statistics.json, validation_report.json); `maps/` with 9 images (1872 Mayer, 1873/1875/1876 Warner-Beers, 1874 & 1877 Mitchell, 1874 fire burnt district, 1878 railway guide, 1879 bird's-eye) plus `annual_city_model.csv` and `city_and_land_events.csv`; `research/annual_tranches/year_18XX_{buildings,sources}.csv` for 1872–1879; `research/source_scans/` (two Andreas v3 page JPEGs: rebuilding totals p60, permit table p67); `research/excerpts/` (YEAR_SCHEMA.md, city_landmarks.json, Andreas stats excerpt); `docs/annual_notes/year_18XX_notes.md` ×8 plus methodology/statistics/quality/gaps/cross_year_audit/map_media_audit/aggregate_statistics_audit; an `.xlsx` companion + `.inspect.ndjson`; and a `viewer/` (same 4-file static pattern). Published as `site/chicago/rebuilding-1870s/viewer/` — 312 records, 9 maps per the landing page. Key scope rule: each year is a research tranche, not a completion-year filter; starts/completions/openings are separate events.

---

## 3. `/home/user/custom/chicago/reference`

Files: `chicago_buildings_chronology_1674_2026.{md,csv,xlsx}`, `chicagobuildingssources.md`, `chicagobuildingstimeline.md`, `4d_chicago_schema_spec_comprehensive.pdf`, `list-1-gemini.numbers`, `list-2-gemini.docx`, `claude-tech-guidance-1/`, `photos/`.

### 3a. `chicago_buildings_chronology_1674_2026.md` (4,202 lines)
**Header:** "**4,009 entries.** Loss notation is included where documented; otherwise status reflects the source inventory."
**Schema (md):** `## <year>` sections, each a bullet list of `- <Name> — <Address> — lost <year>`.
**Schema (the CSV twin, 4,009 rows, 12 columns):** `Construction Year` (BOM-prefixed), `Building / Identifying Name`, `Address`, `Torn Down / Destroyed`, `Status / Outcome`, `Construction Date Text`, `Architect`, `Source Class`, `Source As Of`, `Source URL`, `Notes`, `Confidence` (High/Medium/…).

**Counts:** 1830–1837 inclusive = **19 entries** (1830:1, 1831:2, 1832:2, 1833:6, 1834:1, 1835:1, 1836:5, 1837:1). Everything with a construction year **≤1835 = 30 entries**. Surrounding years for context: 1829:2, 1838:2, 1839:2, 1840–42:0, 1843:1, 1844:4, 1845:2. **The 1830s coverage here is thin** — 19 rows against `pre_fire_v1`'s 55 records for the same decade.

**ALL pre-1836 entries, verbatim key fields:**

| Yr | Name | Address | Lost | Status / Outcome | Date text | Source class | Conf |
|---|---|---|---|---|---|---|---|
| 1674 | Jacques Marquette winter shelter / encampment | Chicago River area | 1675 | Temporary shelter abandoned after winter | Winter 1674–75 | Early settlement research | High |
| 1780 | Du Sable estate — **Bakehouse** | N bank of Chicago R. nr present-day Pioneer Court | — | No longer extant; precise loss date not established | c. 1780s | Early settlement research (nps.gov) | Medium |
| 1780 | Du Sable estate — **Barn no. 1** | ditto | — | ditto | c. 1780s | ditto | Medium |
| 1780 | Du Sable estate — **Barn no. 2** | ditto | — | ditto | c. 1780s | ditto | Medium |
| 1780 | Du Sable estate — **Dairy** | ditto | — | ditto | c. 1780s | ditto | Medium |
| 1780 | Du Sable estate — **Horse-powered mill** | ditto | — | ditto | c. 1780s | ditto | Medium |
| 1780 | Du Sable estate — **Main dwelling / trading house** | ditto | — | ditto | c. 1780s | ditto | Medium |
| 1780 | Du Sable estate — **Poultry house** | ditto | — | ditto | c. 1780s | ditto | Medium |
| 1780 | Du Sable estate — **Smokehouse** | ditto | — | ditto | c. 1780s | ditto | Medium |
| 1780 | Du Sable estate — **Stable** | ditto | — | ditto | c. 1780s | ditto | Medium |
| 1780 | Du Sable estate — **Workshop** | ditto | — | ditto | c. 1780s | ditto | Medium |
| 1803 | Fort Dearborn — first fort | Chicago River at Lake Michigan | 1812 | Burned and destroyed after evacuation | 1803 | encyclopedia.chicagohistory.org/pages/477 | High |
| 1803 | Site of Fort Dearborn (landmark record) | Michigan Av & Wacker Dr | 1812 / 1857 | Historic site; first fort burned 1812, second demolished 1857 | 1803-37 | City individual landmark (`uct4-hrvh`, as-of 2026-04-17), designated 09/15/1971 | High |
| 1804 | United States Factory / trading house at Fort Dearborn | Fort Dearborn vicinity | — | No longer extant; loss date not established | c. 1804 | Early settlement research | Medium |
| 1816 | Fort Dearborn — second fort | Chicago River at Lake Michigan | 1857 | Demolished | 1816 | Early settlement research | High |
| 1829 | **Caldwell's Tavern** | Wolf Point | — | No longer extant; loss date not established | 1829 | encyclopedia…/pages/603 | High |
| 1829 | **Miller House tavern** | Wolf Point | — | No longer extant; loss date not established | 1829 | …/603 | High |
| 1830 | **Mark Beaubien's Sauganash Tavern / Hotel** | Lake Street near Market Street | 1851 | Destroyed by fire | **1830–31** | …/603 | High |
| 1831 | **Methodist log meetinghouse** | Opposite Wolf Point | — | No longer extant; loss date not established | 1831 | encyclopedia.chicagohistory.org | Medium — *"Earliest probable purpose-built Christian worship building in Chicago."* |
| 1831 | Site of the Sauganash Hotel/Wigwam (landmark record) | SE corner of Lake St & Wacker Dr | 1851 | Historic site; hotel destroyed by fire | 1831,1860 | City individual landmark, designated 11/06/2002 | High |
| 1832 | **Chicago Harbor Lighthouse — first lighthouse** | Fort Dearborn / river mouth | 1852 | Replaced by second lighthouse | 1832 | Early settlement research | High |
| 1832 | **Chicago River fixed-span bridge — first bridge** | Chicago River | — | No longer extant; loss date not established | 1832 | Early settlement research | High |
| 1833 | **First Cook County Jail — log blockhouse** | Chicago | — | No longer extant | 1833 | Early settlement research | High |
| 1833 | **First St. Mary's Catholic Church** | Lake Street west of State Street | — | Replaced / no longer extant | 1833 | Early settlement research | High |
| 1833 | **Green Tree Tavern** | Lake and Canal Streets | 1902 | **Collapsed before planned preservation move** | 1833 | …/pages/1110 | High |
| 1833 | **Miltimore's Folly — first public schoolhouse** | State and Madison vicinity | — | No longer extant | 1833 | Early settlement research | High |
| 1833 | **Noble-Seymour-Crippen House** | 5624 N Newark Av | — | Current City landmark (2026); no loss year | 1833 (addn 1863, architect Unknown) | City individual landmark, designated 05/11/1988 | High |
| 1833 | **Tremont House I** | Lake and Dearborn Streets | 1839 | Destroyed by fire | 1833 | …/603 | High |
| 1834 | **First Presbyterian Church building** | Chicago | — | Replaced / no longer extant | 1834 | Early settlement research | High |
| 1835 | **First Cook County Courthouse** | Clark and Randolph Streets | 1853 | Replaced by courthouse and city hall | 1835 | Early settlement research | High |

*(1836–1837 for completeness: Clarke House Museum — Chicago Women's Park & Gardens, Park District inventory, at 41.857067/-87.62188; First Baptist Church building; Henry B Clarke House — 1855 S Indiana Av, landmark 10/14/1970; Lake House hotel — Rush & Kinzie, †1871 Great Fire; Saloon Building — Lake & Clark, †1871 Great Fire; First St. James Episcopal Church — †1857.)*

**Note the internal disagreements** you will have to adjudicate for 1835: the chronology dates Sauganash to **1830** while `pre_fire_v1` and the timeline say **1831**; the chronology puts First Presbyterian at **1834** while `pre_fire_v1` says **1833**; Clarke House appears **three times** across sources (1836 chronology ×3 rows, and `pre_fire_v1` once).

### 3b. `chicagobuildingstimeline.md` (2,868 lines)
"**2,135 named buildings and structures, 1803–2030**, ordered by year of completion. 549 of them are gone." Loss marked with a dagger after the name — `†1931` — with cause when non-ordinary; a bare `†` means gone, year unpinned. Alternate names in parentheses. Organised `## 1780s … ## 2030s` + `## Undated`, with `### <year>` subsections and a decade jump-nav. **Stated coverage policy: "through the 1860s it names essentially every structure documented in the historical record, down to individual taverns, cabins, and frame churches"**, then shifts to named landmarks from the 1870s. Both world's fairs included in full. Companions: the CSV and the source registry.

Its 1830s section is materially richer than the chronology's — for the 1835 project this is the better name list:
- **1830:** Heacock's Point Tavern †; Mann's Tavern (Calumet River) †
- **1831:** Chicago Harbor Lighthouse (Fort Dearborn Light) †1831 — **collapsed**; Mansion House †; Sauganash Hotel †1851 — fire; Site of the Sauganash Hotel/Wigwam
- **1832:** *(none)*
- **1833:** Brown's Boarding House †; Dexter Graves' Boarding House †; First Baptist Church (first meeting house) †; Green Tree Tavern (Chicago Hotel / Lake Street House) †1902 — collapsed; Haas and Sulzer Brewery †1871 — Great Fire; Noble-Seymour-Crippen House; St. Mary's Catholic Church (first church building) †1871 — Great Fire; Tremont House I †1839 — fire; Walker's House (Wolf Point) †
- **1834:** Chicago Harbor North Pier †; Dearborn Street Drawbridge (first drawbridge) †1839; Exchange Coffee House †; First Methodist Episcopal Church (first meeting house) †; First Presbyterian Church (first frame church) †; Stiles' Tavern †
- **1835:** Cook County Courthouse (first courthouse) †1853; Cook County Jail (first jail) †; Lake House Hotel †1871 — Great Fire; Steamboat Hotel (American Hotel) †; Western Hotel †
- **1836:** Clarke House; Ellis Inn †; Fay's Boarding House †; Henry B. Clarke House (Widow Clarke House); Ike Cook's Saloon (Cook's Coffee House) †; Kelsey's Boarding House †; New York House †; Prairie Avenue District; Rice's Coffee House †; Saloon Building †1871 — Great Fire
- **1837:** Chicago Theatre (Sauganash dining room) †1851 — fire; City Hotel (Sherman House I) †1861; St. James Episcopal Church †c.1855; United States Hotel †; William B. Ogden House †1871 — Great Fire
- Earlier, relevant to a 1835 scene: **1820** Indian Agency House (Cobweb Castle) †; **1823** Wolf Point Tavern (Rat Castle / Wolf Tavern) †c.1850; **1825** Robinson's Tavern and Store †; **1827** Miller House (Miller's Tavern) †; **1829** Eagle Exchange Tavern †1851 — fire; **1804** Kinzie House (Kinzie Mansion) †1832.

### 3c. `chicagobuildingssources.md` (774 lines) — research source registry
Scope: every Chicago building 1780–present. Compiled 2026-08-01. Uses a **[VERIFIED] / [UNVERIFIED] / [BROKEN]** legend per URL, with an honest note that `artic.edu`, `explore.chicagocollections.org`, `skyscrapercenter.com`, `chicago.gov`, newspapers.com return 403 to fetchers and Cook County's HTML is robots-blocked *while its APIs work fine*.

**§0 the five sources that do 90% of the work:** Cook County Assessor improvement characteristics (`x54s-btds`, `char_yrblt`, ~1.2M, extant only) · Chicago Building Permits (`ydr8-5enu`, 842,870 rows; 31,667 new construction, 21,844 wrecking/demolition, 2006+) · Chicago Building Footprints (`syp8-uezg`/`hz9b-7nh8`, ~800k) · **Frank A. Randall, *History of the Development of Building Construction in Chicago*** ("the single best pre-modern source") · Sanborn Fire Insurance Maps (LOC). The stated hard problem: **demolished** buildings, with no comprehensive dataset before 2006.

Sections: 1 Official/Government (Landmarks LandmarksWeb scrape via `lanId`, Socrata, Cook County, NRHP, HABS/HAER, SHPO, Sanborn) · 2 Archives (CHM Abakanowicz, Explore Chicago Collections, CPL, Ryerson & Burnham, UIC, UChicago, **Newberry**) · 3 Reference works (Encyclopedia of Chicago, SAH Archipedia, AIA Guide, Randall, **Andreas 1884–86 3 vols**, directories/atlases) · 4 Enthusiast (Chicagology, CAC, Landmarks Illinois, Preservation Chicago, Cinema Treasures, skyscraper DBs, Wikipedia/Wikidata, OSM) · 5 Newspapers & trade press · 6 Pitfalls · 7 Suggested schema · Appendix endpoint list.

**§6 pitfalls that bear directly on an 1835 project:** (1) the **1909 Brennan street renumbering** — no pre-1909 address is comparable to a modern one; store `address_historical` and `address_modern` separately. (2) Annexation. (3) **The Great Fire destroyed the city's own records — there is effectively no municipal building record before 1871; Andreas is the substitute.** (4) Assessor year-built decade rounding. (5) permit ≠ event. (6–8) PIN/condo/address-point joins. (9–10) Socrata field mangling and an en-dash in `permit_type`.

**§7 schema recommendation:** a `building` spine (with `year_started`, `year_completed` + `date_completed_precision` enum `exact_date|year|decade|range|unknown`, `year_demolished` + precision, `demolition_cause` enum incl. `great_fire_1871`, `structural_system` incl. **balloon frame**, `status` enum) — but the load-bearing recommendation is **field-level provenance**: `source(id,…,reliability_tier)` + `assertion(building_id, field_name, value, source_id, source_locator, confidence, superseded_by)`, with every column on the building row a "materialized winner" of its assertions. Reliability tiers 1–6 (1 = designation report/NRHP/HABS … 6 = Wikipedia/enthusiast). Child tables `building_name`, `building_address`, `building_architect`, `building_designation`, **`building_event`** (completed/opened/altered/fire/moved/condemned/wrecking_permit_issued/demolished/rebuilt), `building_media`, `firm`. Join-key ranking: PIN → spatial centroid → normalized address → NRHP ref → Wikidata QID → `lanId` → name+year fuzzy. Reconcile in reliability order, never destroy the loser, flag >5-year disagreements. **`pre_fire_v1` visibly implements this schema** (buildings/sources/assertions/building_names/building_events/media + confidence + needs_review).

### 3d. `claude-tech-guidance-1/` — **the earlier 1835 analysis to honour**
`files/BRIEF.md` (13.5 KB) + a working skeleton: `structures.json`, `structures.schema.json`, `sources.json`, `validate_structures.py`, `check.sh`. Full summary of its recommendations:

1. **Framing.** "Chicago 1835 — Development Brief… Handoff document for Claude Code. Read this in full before writing any code." It is **"not primarily a game project. It is a research dataset with renderers attached."** The durable artifact is georeferenced structure data with source provenance; **renderers are disposable and plural**.
2. **Target:** `1835-07-01`, configurable but *enforced*. Scope ≈ half a square mile — river forks east to the lake, Kinzie St south to Madison, State St west to Des Plaines. **~150 structures, population ~3,300.** First milestone: one building (Sauganash) end to end.
3. **Anti-goals (§2):** no hand-modelling into a renderer (every mesh regenerable from `data/` by a command, or it doesn't belong in the repo); **never invent sources** — mark `conjectural` rather than fabricate a citation to pass a validator; never silently fill gaps; **never drift past the target date** (most vivid published description of early Chicago is 1837–1845 and describes a bigger town); no assets without license provenance (CC0/CC-BY only); renderers consume glTF + JSON and never reach into `generators/`.
4. **Repo layout (§3):** `data/{sources.json,structures.json,traces/,terrain/}` · `generators/{common/,archetypes/,build.py}` · `assets/{gltf/,textures/,audio/,LICENSES.md}` · `renderers/web/` (three.js, ships first, maintained permanently) + later `godot/` · `tools/{validate_structures.py,check.sh}` · `docs/{RESEARCH.md,PROVENANCE.md}` · `AGENTS.md`.
5. **Provenance model (§4) — the heart of it.** Confidence is **per attribute, not per building** ("you will routinely know a footprint precisely while knowing nothing about the roof pitch"). Levels: `documented` (primary source attests at target date; requires ≥1 resolving `source_id`), `inferred` (from typology/adjacent evidence/period practice; **requires a non-empty `note` stating the reasoning**), `conjectural` (no evidence, visual completeness only; surfaced in the build report). **Every renderer must implement a "confidence view"** toggle recolouring the scene by evidence quality — documented renders normally, inferred tinted, conjectural as translucent massing. "This is not a debug feature… it is what separates this from a themed environment."
6. **Date enforcement (§5):** every structure carries `documented_range {from,to}`; **the validator fails the build if TARGET_DATE falls outside it** — "the most important check in the suite." Do not widen a range to pass; narrow it and mark conjectural.
7. **Coordinates (§6):** working CRS **EPSG:26916** (UTM 16N NAD83, metres); scene frame local ENU metres with a fixed datum origin; structures store UTM *and* derived local (local is computed, never hand-entered). **Datum origin = the river forks at Wolf Point, ~41.8885 N / −87.6385 W — flagged PLACEHOLDER, must be verified against the georeferenced Hathaway (1834) and Wright (1834) surveys before any geometry is generated.** Author to glTF **Y-up, right-handed, metres**. Convert period feet/chains/links at ingest and record the original figure in `note`.
8. **Archetypes (§7):** buildings generated from a small parameterized set, not modelled individually — `frame_tavern` (Sauganash), `frame_storefront` (South Water), `log_dwelling`, `plank_walk` (raised board sidewalk over mud), `ground_prairie` (wet prairie, mud, ruts). **Balloon-frame construction was invented in Chicago in 1832–33 and is the defining local technology of this exact moment — get stud spacing, sheathing and proportions right, "because it is the thing a knowledgeable viewer will check first."** Each archetype exposes `build(params: dict) -> bpy.types.Object`; no archetype reads `structures.json`.
9. **Milestone 0 (§8) — the Sauganash end to end**, 7-point definition of done: real `sources.json` entries → one schema-valid `structures.json` record with per-attribute confidence and a defensible range → `frame_tavern.py` mesh from that record alone → headless `build.py` emitting `assets/gltf/sauganash.glb` → `renderers/web/` walkaround → **working confidence-view toggle** → `check.sh` clean. Explicitly warns: *the surviving Sauganash images are later reconstructions that disagree with each other*, and that is the right problem to hit on building one. **Milestone 1 = one South Water Street block** (repeatable storefront archetypes; watch date drift).
10. **Sources (§9):** *Primary cartography* — **Hathaway 1834 (Newberry) = "the master geometry source"**, commissioned by John H. Kinzie for lot sales, small rectangles denote individual buildings; **Wright 1834 (Newberry)** = best for shoreline, river mouth, sandbar, river's outward flow; **Conley/Stelzer 1833 reconstruction** via chicagology.com/prefire. *Textual* — Andreas 1884 3 vols (incl. the 1830 landownership map); ***Chicago Democrat* from 1833** — period ads naming businesses block by block, "the best street-level source that exists", suited to bulk processing once OCR'd; Newberry pioneer reminiscences; Encyclopedia of Chicago. *Methodological precedent* — **`CamilleMorlighem/histo3d`** (GRASS GIS digitization → BlenderGIS → BCGA procedural modelling → CityJSON via Up3date → val3dity validation; "closest existing pipeline… read the paper before designing the trace-to-footprint step"); **chicago00.org** (CHM / Geoffrey Alan Rhodes). *Agent tooling* — `Unity-Technologies/skills`, `duolahypercho/GT-caliber` (for the `AGENTS.md` + headless-CI-gate pattern).
11. **1835 context (§10) — standing constraint.** The final removal of the Potawatomi from Chicago occurred **August 1835, inside the target window**. Do not let an agent improvise Native presence, representation, dialogue or depiction; this is not a gap to fill by inference. Newberry's Indigenous Chicago curriculum is the starting point; seek review from Native scholars/community organisations before shipping any depiction. **Until then, leave human depiction out of scope entirely — "An empty, accurate town is honest. A populated, invented one is not."** Record in `AGENTS.md`, not just the brief.
12. **CI gate (§11):** `tools/check.sh` before any commit — (1) `validate_structures.py` schema → semantic → referential; (2) every file under `assets/` has a `LICENSES.md` entry; (3) headless `generators/build.py --dry-run` per structure; (4) `renderers/web` compiles. "Keep it fast. A gate that takes four minutes gets skipped."
13. **First actions (§12):** read brief + schema → scaffold layout → write `AGENTS.md` from §2 and §10 → **verify the datum origin against Hathaway/Wright before anything else** → begin Milestone 0 at sources. "Do not skip ahead to geometry. The dataset is the project."

**The shipped skeleton matches:** `structures.schema.json` (draft 2020-12, `additionalProperties:false`, `$defs.attested {value, confidence, sources[], note}`, `date_range`, archetype enum `frame_tavern|frame_storefront|log_dwelling|frame_dwelling|institutional|fort_structure|outbuilding`, footprint polygon in local ENU metres CCW, `position.rotation_deg` = facade bearing CW from grid north, `review_required` blocking release "for anything touching Indigenous history or depiction"). `validate_structures.py` implements: schema pass → referential (`source_id` resolves) → semantic (documented needs sources; inferred needs note; conjectural-with-sources warns; **`datum.verified:false` is a hard error**; target-date-outside-range is a hard error; `documented_range` span >12 years warns "Chicago changed fast between 1833 and 1837"; required generator params `stories, wall_height_m, roof_type, construction`; a warning when >60% of a structure's attributes are conjectural), prints a documented/inferred/conjectural percentage table, `--strict` promotes warnings. `structures.json` ships one deliberately-almost-entirely-`conjectural` Sauganash template (`sauganash_hotel`, aka Eagle Exchange Tavern / Beaubien's tavern, archetype `frame_tavern`, placeholder range 1831-01-01→1837-12-31, placeholder 12×8 m rectangle, `construction: balloon_frame` marked `inferred` with a real note) plus the unverified datum — **so the validator fails out of the box, by design**. `sources.json` has four entries, all `verified: false`: `hathaway_1834`, `wright_1834`, `andreas_1884_v1` ("treat as secondary… cite the page for every claim"), `conley_stelzer_1833` ("Reproduction rights unclear — CHECK BEFORE USE… a modern reconstruction, never sole evidence").

### 3e. `reference/photos/` — every file
| File | Size / dims | What it is |
|---|---|---|
| `IMG_5379.jpeg.pdf` | 149 KB, 2-page PDF | A PDF wrapper around a JPEG (iOS "save photo as PDF"). Same camera-roll series as 5380–5382. **Content not extracted** — no `pdftotext`, `pypdf`, `pdfminer` or PyMuPDF in this environment, and no PIL. Worth opening manually. |
| `IMG_5380.png` | 848×612, 0.9 MB | Hand-coloured lithograph, **early Chicago from the lake looking west**: the palisaded Fort Dearborn compound (white buildings, flagstaff) on the south bank; the river deflected south behind a long **sandbar**; a small house group with people on the north bank (Kinzie side); tipis at far left; birchbark canoes with Native paddlers in the foreground. Iconographically the standard "Chicago in 1820 / 1831" retrospective view. **Directly useful: shoreline, sandbar, river mouth geometry, ground condition.** |
| `IMG_5381.png` | 650×368, 0.4 MB | Engraved **"CHICAGO IN 1812"** map. Labels: *Prairie*, *S. Branch*, *N. Branch*, *Ind. Trail*, *Agency House*, *Burns*, *Ouilmette*, *Kinzie*, *Fort D.*, *Sand Hills*, *Lake Michigan*, the river mouth turning south along the bar. Classic Andreas/Kirkland plate. Pre-dates the target window but fixes trail + house positions. |
| `IMG_5382.png` | 2048×1624, 5.9 MB | **"Chicago In Early Days. 1779–1857."** — a Kurz & Allison chromolithograph (copyright notice bottom right, Wabash Ave, Chicago), **15 numbered vignettes with a printed key**: 1 Old Fort Dearborn, erected 1803 · 2 The First Cabin, built 1779 by Jean Baptiste Point de Saible, the first settler · 3 Chicago in 1845, pop. 12,088 · 4 First Rush Medical College, inc. 1837, city pop. 4,170 · 5 Fort Dearborn as rebuilt, 1835, pop. 3,265 · 6 The First Court House · 7 Water Works, erected 1853, pop. 60,662 · **8 Chicago in 1830 — from the lake, pop. 96** (the large central panel: fort compound, river, north-bank houses, tipi, canoes) · **9 Wolf Point in 1830** · 10 The Clybourne House · **11 The Green Tree Hotel, cor. West Lake and Canal St., built 1833** · **12 The Old Kinzie Mansion, built 1832, pop. 310** · 13 Chicago in 1853, pop. 60,662 (large bird's-eye with piers and shipping) · **14 The Sauganash Hotel, built 1831** · 15 The Old Block House and Light House in 1857, the last of Fort Dearborn, pop. 93,000. **This is the single richest 1830s pictorial reference in the repo** — it depicts Sauganash, Green Tree, Wolf Point, Kinzie Mansion and the 1830 river-mouth view on one sheet. Caveat: it is an 1890s retrospective, exactly the "later reconstruction that disagrees with itself" the BRIEF warns about. |
| `old-chicago-complete-map.png` | 2936×2431, 11.1 MB | **"OLD CHICAGO by Jean Sterling Nelson, drawing by John Winters"**, © 1940, Kroch's/Chicago lithographer — a decorative **pictorial map**, borders reading *ITS RIVER AND TRAILS · ITS PERSONS AND PLACES · SOME FAMOUS HISTORICAL SITES · OLD FACES*, with corner portrait medallions (John H. Kinzie 1803–65, Gen. Dearborn 1775–1828, Wm. B. Ogden first mayor 1837, and two others). Labels the whole 1830s settlement: **Fort Dearborn, John Kinzie's House, Ouilmette's Cabin, Miller House, Green Tree Tavern, Mark Beaubien's Sauganash Tavern, Pottawatomie Village, Wolf Point, Tremont House, First Presbyterian Church, First Baptist Church, Calhoun's print shop, Kinzie's Addition**, plus the trails (**Northwest Trail, Green Bay Road, Hubbard's Trace, Whiskey Point Road**), the street grid (So. Water, Lake, Randolph, Washington, Madison; Wells, La Salle, Clark, Dearborn, State), North/South Branch, the sandbar and river mouth, Fort Dearborn Massacre site, "Harbor cut by Engineers 1833". Added in the tip commit as "a new complete map". **Orientation and toponym aid only — a 1940 cartoon map, tier-6 evidence, must not drive geometry.** |

### 3f. `4d_chicago_schema_spec_comprehensive.pdf`
Exists, 60 KB, generated by **WeasyPrint 62.3** (i.e. produced from HTML). Fonts are subset-embedded so raw stream scraping yields garbage, and no PDF text tooling is installed here — but the **document outline/bookmark tree extracted cleanly**, giving the full section structure:

> **4D Historical Building Database Specification — Downtown Chicago**
> 1. Architectural Strategy & Temporal Modeling Framework
>  B. Chronology & Temporal State Control
>  C. Physical & Architectural Specs
>  D. People, Organizations & Legal Attributes
>  E. 3D Spatial Assets & Visual Environment
>  F. Archival Media & Data Quality Governance
> 3. Supporting Normalized Relational Tables
> 4. Primary Data Ingestion Sources for Researchers — Geographic & Physical Records; Architectural & Photographic Archives
> 5. Implementation Stack & Architectural Pipeline
> 6. Mandatory Chicago-Specific Research Directives

Body text needs `pip install pypdf` / poppler, or opening it directly, to read.

Also present, unread: `list-1-gemini.numbers` (169 KB, Apple Numbers), `list-2-gemini.docx` (3.0 MB, added in commit a3a59fb) — two Gemini-produced building lists.

---

## 4. `/home/user/custom/joliet`

### What it is
**"Joliet: Midnight Infiltration"** — a browser first-person **urban-exploration** game set in the Old Joliet Prison (1125 Collins St, Gothic Revival limestone, Boyington & Wheelock 1857–68, closed 2002), rendered in its present decayed state. **No combat, no weapons.** Traversal + observation at night with a headlamp on a finite battery. Babylon.js + TypeScript + Vite; no runtime deps beyond Babylon.

### Layout
```
joliet/
├── index.html · vite.config.ts · tsconfig.json · package.json · README.md · STATUS.md · ASSETS.md
├── src/
│   ├── main.ts (343)              Boot + the SCENES registry (?scene=<id>)
│   ├── core/  Renderer(537) Player(656) Input(331) Settings(269) Palette(113)
│   │          Noise(197) Bakery(701) Materials(411) Kit(632) Audio(443) TouchControls(343)
│   ├── scenes/ SceneBase(77) PerimeterApproach(587) Powerhouse(3306)
│   │           Cellblocks(2112) TheVoid(2031)
│   └── ui/    Hud, Hints, Objective, PauseMenu, TitleScreen, ControlsHelp, ui.css, touch.css
├── tools/  shots.mjs · stage.mjs · probe-build.mjs · traverse-probe.mjs
│           light-calibrate.mjs · title-check.mjs · touch-probe.mjs
├── docs/   RESEARCH.md (996) DESIGN.md (101) ART-BIBLE.md (174)
│           HISTORICAL-LIBERTIES.md (82) QUALITY-LOG.md (142) QUALITY-BACKLOG.md (232)
├── public/assets/  textures/ (16 CC0 PBR sets: limestone-ashlar, limestone-roughface,
│                   brick, concrete-block, concrete-floor, grass, ground-dirt-gravel,
│                   asphalt, diamond-plate, metal-grate, painted-metal-chipped,
│                   rusted-metal-pitted, rusted-metal-sheet, water, wood-planks-rotten)
│                   env/ (2 HDRIs: dusk-overcast, night-moonlit)
└── artifacts/  shots/{1.1-perimeter,2.1-powerhouse}/iter-NN/*.png + report.json · touch/
```
~15,800 lines of TypeScript. Scripts: `dev`, `build`, `preview`, `shots`, `check` (tsc --noEmit), `stage`, `probe`, `calibrate`.

### How it was built
- **Research first, modelling second.** `docs/RESEARCH.md` is 996 lines with an explicit "⚠️ Read this before anything else", a **§0.1 primary sources actually used**, a **§0.2 "What does NOT exist (negative findings)"**, and a **§0.3 master list of source conflicts**. It corrected four errors in the original brief (e.g. perimeter wall: 25 ft is the *1857 design spec* that every secondary source repeats; as-built is 32–35 ft — the game uses as-built). Colour palette was derived numerically by sampling 41 NRHP survey photographs (§5.1 documents the method; §5.3 is the master hex table).
- **Append-only `HISTORICAL-LIBERTIES.md`** with a stated standard: *"a visitor who has taken the Old Joliet Prison tour should recognise every room, and should be able to tell you which parts we made up."* Every compression (site scaled from ~72 acres to ~400×300 m, simplified interiors, approximate tower positions, simultaneous decay states from different years) and every invention (the sealed sub-level, the Yard Tower interior) is listed with reasoning.
- **A screenshot/critic loop** (`tools/shots.mjs`): 5 fixed camera anchors per scene, 1080p, per-anchor FPS / mesh count / triangle count / page-error capture, output to `artifacts/shots/<scene>/iter-NN/`. `QUALITY-LOG.md` records 9 iterations with root causes; `STATUS.md` states bluntly that the formal 8-axis scoring protocol **was not** followed and scene 1.1 "must not be described as having passed it."
- **`STATUS.md` is deliberately unflattering** — per-area honest scores, including "Accessibility was scored 5/10 for three days and was really 0/10" and "Audio: built, never heard." It also documents refusing an unsatisfiable exit condition (a blind quality comparison against Call of Duty frames) on the grounds that any agent reporting it complete would be fabricating evidence.

### Data model and rendering approach
- **`SceneBase.ts`** defines the contract: a `SceneManifest {id, title, spawn:{position,yaw}, anchors: ShotAnchor[]}` — **the shot/critic harness reads the same manifest the game does**, so camera anchors are data, not test fixtures. `GameScene.build()` is called once; `kit()` returns a `KitContext` whose `register(mesh, opts)` centrally applies **world-space UVs** (`worldUV(mesh, 1/3)` — constant texel density regardless of object size), `checkCollisions`, `receiveShadows`, shadow casting, a `metadata.surface` tag (drives footstep audio), and `freezeWorldMatrix()` (static architecture → large draw-call win).
- **`Kit.ts`** is a **parametric architecture library**, not hand-modelled geometry: `buildWall`, `buildTower`, `buildCrenellation`, `buildBarredWindow`, `buildBarbedWireLine` (catenary), `buildGround` (with `GroundAperture` rectangles cut out for the trench). Scenes *compose* from the kit; core is never edited by scene code.
- **`Bakery.ts` + `Noise.ts`**: every material is **procedurally synthesised at load time** from seeded tileable value/fBm/Worley/ashlar noise into a frozen 18-preset named library (`Materials.ts`). Rationale from the README: *"A photo scan puts the weathering wherever the photographer's wall had it; generated maps let runoff start at the cap rail and biological blotching sit in the sheltered courses, which is what the reference actually shows."* Also a few hundred KB of code instead of tens of MB of downloads. The CC0 sets in `public/assets/` are detail overlays only, all logged in `ASSETS.md` with source URL + licence.
- **Renderer:** PBR + IBL, cascaded shadow maps with PCF contact hardening, SSAO2, ACES tonemap, restrained bloom, TAA, grain, motion blur, **4 quality tiers**; touch devices forced to `low` at ~1.8× hardware scaling.
- **Player:** not a rigid body — swept-ellipsoid collide-and-slide plus an explicit step-up probe ("more predictable and cheaper than a physics capsule… this building is almost entirely stairs, thresholds and doorways").
- **Scene registry in `main.ts`:** a plain `Record<string, {title, ambience, loadingLine, make}>`; **`?scene=<id>` is the only navigation** because no transition system exists — the harness and landing-page deep links use it too. `window.__joliet = {ready, scene, player, renderer}` is the harness handle.
- **Roles are data, not four campaigns:** one level geometry, `RoleConfig` objects drive ability flags, stamina curves, highlight filters, barks, and spawn point.
- **Publishing:** `vite.config.ts` uses `base: './'` (relative) so the same bundle works from `vite preview`, from `artifacts/`, and from Pages. The **built bundle is committed to `site/joliet/app/`** (`assets/babylon-*.js`, `index-*.js`, `index-*.css`, one HDRI) with a hand-written `site/joliet/index.html` wrapper — because the Pages workflow only publishes `site/`. Same publish pattern as the Chicago viewers.

### Lessons/patterns that transfer to a Chicago 1835 walkthrough
1. **Research dossier first, geometry second** — and make the dossier state its *negative* findings and its *source conflicts* explicitly. `RESEARCH.md` §0.2/§0.3 is exactly the discipline `BRIEF.md` §4 asks for, already proven at scale in this repo.
2. **An append-only liberties ledger** is the practical sibling of the BRIEF's confidence model. Joliet's "a tour visitor should be able to tell you which parts we made up" ≈ the BRIEF's confidence-view toggle. Chicago 1835 should have both: per-attribute confidence in data *and* a human-readable liberties doc.
3. **Parametric kit + procedural materials beat hand-modelling** — and it is the same instruction as BRIEF §2 ("all meshes are generated from data via scripts"). `Kit.ts`'s `build*()` functions are a working precedent for `generators/archetypes/{frame_tavern, frame_storefront, log_dwelling, plank_walk, ground_prairie}.py`.
4. **World-space UVs and a centralised `register()` hook** — one place that enforces texel density, collision, shadows and surface tagging. The 1835 equivalent: one loader that applies confidence-tinting shaders centrally, so the confidence view can never be forgotten per-building.
5. **Manifest-driven camera anchors + a headless screenshot/perf harness** (`tools/shots.mjs` → `artifacts/shots/iter-NN/report.json`) gives an agent loop objective evidence. Directly reusable for an 1835 walkthrough: anchors at the forks, South Water, Fort Dearborn, the Sauganash.
6. **A fast CI gate that fails loudly** — Joliet has `npm run check` + the shot harness + page-error capture; the BRIEF specifies `check.sh` with 4 steps. The `validate_structures.py` that ships in `claude-tech-guidance-1/files/` is ready to drop in as step 1.
7. **`?scene=`-style URL-addressable entry points** before a transition system exists — ship one walkable block early, reachable by URL, rather than blocking on a level flow.
8. **The static-`site/`-only publish convention** already governs this repo: an 1835 renderer must build to a committed bundle under `site/chicago/1835/` (relative `base`), with sources living in `chicago/`. And add an `index.html` at any directory a URL will point at — the existing `site/chicago/pre-fire/` has none.
9. **Honest status reporting.** Joliet's `STATUS.md` refusing an unverifiable exit condition is the model for how to handle the BRIEF §10 constraint on Indigenous depiction: state the limit, don't paper over it.
10. **Watch the mismatch in kind:** Joliet is one building at high fidelity from an NRHP nomination with measured dimensions; Chicago 1835 is ~150 buildings whose geometry comes from a single lot-sale map (Hathaway 1834) and pioneer recollection. The BRIEF's answer — archetypes + per-attribute confidence + translucent conjectural massing — is the right adaptation, and nothing in `pre_fire_v1` currently supplies footprints (**only 15 of 324 records are geocoded, and no map is internally georeferenced except two marked `georeferenced_external`**). Georeferencing Hathaway 1834 and verifying the Wolf Point datum is the true critical path.
