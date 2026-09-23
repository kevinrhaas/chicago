# Chicago Buildings Database — Research Source Registry

**Scope:** every building ever constructed in Chicago, 1780–present, with address, architect, style, construction year, demolition year, and designation status.

**Compiled:** 2026-08-01

**Verification legend**

- **[VERIFIED]** — URL fetched successfully during compilation; described contents/fields observed directly.
- **[UNVERIFIED]** — URL could not be fetched from this environment (403 / robots.txt / rate limit / cache-only domain). The resource is believed real and correct, but confirm before relying on it.
- **[BROKEN]** — confirmed dead, hijacked, or otherwise unusable as written.

A note on why some things are unverified: several hosts (`artic.edu`, `explore.chicagocollections.org`, `skyscrapercenter.com`, `chicagotribune.newspapers.com`, `chicago.gov` main site) return 403 to automated fetchers, Wikipedia/Wikidata were cache-only in this environment, and `datacatalog.cookcountyil.gov` disallows HTML crawling in robots.txt. In the Cook County case the **API endpoints work fine even though the HTML browse pages are blocked** — that pattern recurs and is worth remembering.

---

## 0. Executive summary — the five sources that do the most work

If you build nothing else, build these five and you have ~90% of the rows:

| Rank | Source | What it gives you | Coverage |
|---|---|---|---|
| 1 | **Cook County Assessor — Single and Multi-Family Improvement Characteristics** (`x54s-btds`) | `char_yrblt` (year built) for essentially every residential parcel improvement in the county | ~1.2M+ buildings, extant only |
| 2 | **Chicago Building Permits** (`ydr8-5enu`) | New construction + wrecking/demolition permits with dates and addresses, 2006–present | 842,870 permits; 31,667 new construction, 21,844 wrecking/demolition |
| 3 | **Chicago Building Footprints** (`syp8-uezg` / `hz9b-7nh8`) | Geometry, and (in the attribute table) year built, stories, height, condition | ~800k footprints |
| 4 | **Frank A. Randall, *History of the Development of Building Construction in Chicago*** | Year-by-year, address-by-address record of significant construction 1830s–1940s including demolished buildings | The single best pre-modern source |
| 5 | **Sanborn Fire Insurance Maps** (LOC) | Building-by-building footprints, construction material, height in stories, by survey year | Reconstructs demolished blocks |

The hard problem is not extant buildings — the Assessor solves that. The hard problem is **demolished** buildings, for which there is no comprehensive dataset before 2006. Sections 1.2, 1.7, 3.5, 4.4 and 5 are the demolition-recovery toolkit.

---

## 1. OFFICIAL / GOVERNMENT

### 1.1 City of Chicago Landmarks Database (LandmarksWeb)

- **URL:** https://webapps1.chicago.gov/landmarksweb/web/home.htm **[VERIFIED]**
- **Alphabetical listing:** https://webapps1.chicago.gov/landmarksweb/web/listings.htm **[VERIFIED]**
- **Architects index:** https://webapps1.chicago.gov/landmarksweb/web/architects.htm **[VERIFIED — linked from home]**
- **Covers:** All individually designated Chicago Landmarks and all Chicago Landmark Districts, plus a front end onto the Chicago Historic Resources Survey (17,000+ properties of historical significance).
- **Fields observed on a detail page:** landmark name, street address, year built, architect, City Council designation date, a multi-paragraph significance narrative, and photographs. Cross-links to thematic "tours" (Art Deco, Boul Mich, etc.) which are a useful ready-made style tagging.
- **URL patterns (confirmed by fetching a live record):**
  - Individual landmark: `https://webapps1.chicago.gov/landmarksweb/web/landmarkdetails.htm?lanId={ID}&counter={N}`
    (working example: https://webapps1.chicago.gov/landmarksweb/web/landmarkdetails.htm?lanId=1234&counter=1 → 333 North Michigan Building, 1928, Holabird & Roche/Root, designated February 7, 1997)
  - District: `https://webapps1.chicago.gov/landmarksweb/web/districtdetails.htm?disId={ID}`
- **How to get data out:** **Scrape.** No API. `lanId` appears to be a small dense integer space — iterate `lanId` from ~1 to ~2000 and parse. The `counter` parameter is cosmetic (list position) and can be set to 1.
- **Caveat:** No designation-report PDF link was visible on the detail page HTML. Designation reports are published separately on the main city site (see below) — treat the PDF linkage as a manual join on landmark name.
- **Designation reports (PDFs):** https://www.chicago.gov/city/en/depts/dcd/supp_info/chicago_landmarks.html **[UNVERIFIED — chicago.gov returns 403 to automated fetchers]**. Reports are typically at paths like `https://www.chicago.gov/content/dam/city/depts/zlup/Historic_Preservation/Publications/{Name}.pdf`. These are the richest single-building documents the city produces: full architectural description, construction chronology, architect biography, alteration history, and a criteria-for-designation section. Harvest manually or via a headless browser.

### 1.2 Chicago Data Portal (Socrata) — data.cityofchicago.org

**API basics.** Every dataset is reachable at `https://data.cityofchicago.org/resource/{4x4}.json` with SoQL query parameters (`$select`, `$where`, `$group`, `$order`, `$limit`, `$offset`). Metadata and full column list at `https://data.cityofchicago.org/api/views/{4x4}.json`. Register a free app token and pass it as `$$app_token=` or the `X-App-Token` header to escape throttling. Bulk CSV: `https://data.cityofchicago.org/api/views/{4x4}/rows.csv?accessType=DOWNLOAD`.

**Cross-portal discovery API** (very useful, and it works when the HTML portals don't):
`https://api.us.socrata.com/api/catalog/v1?domains=data.cityofchicago.org&q={term}&limit=20` **[VERIFIED]**

#### Permits — construction and demolition

- **Building Permits** — `ydr8-5enu` **[VERIFIED]**
  - https://data.cityofchicago.org/resource/ydr8-5enu.json
  - 2006–present, permits not voided/revoked. **842,870 rows.**
  - Columns: `ID`, `PERMIT#`, `PERMIT_STATUS`, `PERMIT_MILESTONE`, `PERMIT_TYPE`, `REVIEW_TYPE`, `APPLICATION_START_DATE`, `ISSUE_DATE`, `PROCESSING_TIME`, `STREET_NUMBER`, `STREET_DIRECTION`, `STREET_NAME`, `WORK_TYPE`, `WORK_DESCRIPTION`, `PERMIT_CONDITION`, an extensive fee block, and `CONTACT_1..CONTACT_2` name/type/address fields (the contact fields are where **architect, general contractor, owner and developer names** live — this is an underused architect source for the modern era).
  - **Verified `permit_type` values and counts** (from a live `$group` query):

    | permit_type | count |
    |---|---|
    | PERMIT – EXPRESS PERMIT PROGRAM | 320,546 |
    | PERMIT - EASY PERMIT PROCESS | 207,656 |
    | PERMIT - RENOVATION/ALTERATION | 166,890 |
    | PERMIT - SIGNS | 54,769 |
    | **PERMIT - NEW CONSTRUCTION** | **31,667** |
    | PERMIT - ELEVATOR EQUIPMENT | 22,172 |
    | **PERMIT - WRECKING/DEMOLITION** | **21,844** |
    | PERMIT - SCAFFOLDING | 8,965 |
    | PERMIT - REINSTATE REVOKED PMT | 5,278 |
    | PERMIT - PORCH CONSTRUCTION | 3,096 |
    | PERMIT - FOR EXTENSION OF PMT | 58 |

  - **This is the key to demolition dates for the modern era.** Note the en-dash in "PERMIT – EXPRESS PERMIT PROGRAM" vs. hyphens elsewhere — a real gotcha when writing `$where` clauses.
  - Example demolition extract:
    ```
    https://data.cityofchicago.org/resource/ydr8-5enu.json
      ?$select=id,permit_,issue_date,street_number,street_direction,street_name,work_description
      &$where=permit_type='PERMIT - WRECKING/DEMOLITION'
      &$order=issue_date
      &$limit=50000&$offset=0
    ```
    (Socrata mangles `PERMIT#` into an API field name — check `/api/views/ydr8-5enu.json` `columns[].fieldName` for the exact token before relying on it.)
  - **Important limitation:** an issued wrecking permit is not proof of demolition, and the issue date precedes the actual teardown by weeks to months. Corroborate with 1.2/asbestos notices and footprint disappearance between vintages.

- **CDPH Environmental Asbestos and Demolition Notification** — `qhb4-qx8k` **[VERIFIED via catalog]**
  - https://data.cityofchicago.org/resource/qhb4-qx8k.json
  - Notices of Intent (NOI) for demolition and asbestos abatement under Municipal Code Ch. 11-4 Art. XVIII.
  - **Underrated.** NOIs carry a *scheduled start and end date of demolition*, which is often a tighter demolition date than the permit issue date. Cross-check against `ydr8-5enu`.

- **Sign Permits** — `yrm5-pjgu` **[VERIFIED via catalog]** — marginal for buildings, useful for identifying commercial tenancy/use changes.

#### Designation status

- **Individual Landmarks** — `uct4-hrvh` **[VERIFIED]** — **407 rows**. Columns: `name`, `id`, `address`, `date_built`, `architect`, `landmark`, `the_geom`, `valid_date`. This is the current tabular authority and it directly populates five of your target fields. `valid_date` = designation date.
- **Individual Landmarks - Map** — `bddq-yxar` **[VERIFIED via catalog]** (current map view)
- **Individual Landmarks (Deprecated January 2024)** — `tdab-kixi` **[VERIFIED via catalog]** — superseded by `uct4-hrvh`; still useful for diffing designations over time.
- **Landmark Districts** — `zidz-sdfj` **[VERIFIED via catalog]**
- **Boundaries - Landmark Districts** — `t8pq-wu86` (shapefile) and **KML** `rkur-ce6h` **[VERIFIED via catalog]** — spatially join every building footprint to its district to derive district-contributing status.
- **National Register of Historic Places** — `yw5d-szpx`; **KML** `c4vt-4uy5` **[VERIFIED via catalog]** — city-maintained list of Chicago NRHP listings and National Historic Landmarks. Easier to join than the federal files, but authoritative dates come from NPS (§1.4).
- **Chicago Historic Resources Survey — Red and Orange Buildings** — `ty7a-2bxt`; **KML** `cmb2-8jw8` **[VERIFIED]**
  - Decade-long survey completed 1995; **~9,900 pre-1940 properties** rated for historic/architectural significance. Red = most significant, Orange = significant. Red/Orange status triggers Chicago's **Demolition-Delay Ordinance** unless the building is already a landmark.
  - **Distributed as a zipped shapefile, not tabular** — the Socrata `columns` array is empty. Download the ZIP and read with GeoPandas/QGIS, or use the KML.
  - The full CHRS (17,000+ properties, including Yellow/Green ratings) is exposed only through LandmarksWeb, not as open data.

#### Geometry and the built stock

- **Building Footprints** — `syp8-uezg` (tabular-with-derived-map) and **Building Footprints - Map** — `hz9b-7nh8` **[VERIFIED via catalog]**
  - https://data.cityofchicago.org/resource/syp8-uezg.geojson
  - The current authority. Attribute table typically includes footprint ID, `bldg_id`, year built, stories above/below grade, building height, non-standard flag, condition, `bldg_status` (ACTIVE/DEMOLISHED/PROPOSED), and address components. **The `bldg_status` field and the deprecated vintages below are a poor man's time series of demolition.**
  - **Deprecated vintages are valuable, not junk** — diff them to detect demolitions between snapshots:
    - `w2v3-isjw` (deprecated Jan 2013), `6mpq-sfwi` (deprecated Dec 2013), `qv97-3bvb` (deprecated Aug 2015), plus older aliases `vmwt-djju` and `tf32-rk4u`. **[all VERIFIED via catalog]**

- **Chicago Energy Benchmarking** — `xq83-jr8c`; **Covered Buildings** — `g5i5-yz37`; **Covered Buildings - Map** — `hpv9-sp6k` **[VERIFIED via catalog]**
  - Annual reporting for buildings ≥50,000 sq ft. Contains **year built, gross floor area, property type, and a stable `Chicago Energy Benchmarking ID`** for roughly 3,500 large buildings. Excellent high-confidence ground truth for the large-commercial segment.
  - Single-year filtered views also exist (`tepd-j7h5` 2014, `j2ev-2azp` 2017, `jn94-it7m` 2019, map `hvcb-xciu`, `kj4h-bdje`).

#### Condition, vacancy, distress (demolition leading indicators)

- **Building Violations** — `22u3-xenr` **[VERIFIED via catalog]** — Department of Buildings violations 2006–present, with address and lat/long. Dangerous-and-hazardous violations frequently precede demolition by 1–3 years.
- **Vacant and Abandoned Buildings - Violations** — `kc9i-wq85` **[VERIFIED via catalog]** — since 2011, financial-institution-owned.
- **311 Service Requests - Vacant and Abandoned Buildings Reported - Historical** — `7nii-7srd` **[VERIFIED via catalog]** — since 2010-01-01.
- **Building Code Scofflaw List** — `crg5-4zyp` **[VERIFIED via catalog]** — chronic-violation priority buildings with addresses, coordinates and ownership.

#### Address reference

- There is **no dataset literally named "Address Points" on the Chicago portal** — repeated catalog queries returned none. **[VERIFIED negative]** Chicago's address point layer lives on the city's ArcGIS infrastructure (`gisapps.chicago.gov` / the Chicago GIS open data hub), which returned 403 to automated fetching **[UNVERIFIED]**. Use the Cook County layer instead (§1.3), which covers the city completely.
- **Micro-Market Recovery Program - Addresses** — `cf2f-mmzv` **[VERIFIED via catalog]** — narrow, but a clean address-with-geography crosswalk for targeted neighborhoods.

### 1.3 Cook County Assessor & Cook County Open Data — the single largest source of construction years

Portal: https://datacatalog.cookcountyil.gov/ **[HTML browse UNVERIFIED — robots.txt disallows crawling]**
**API works despite the robots block**: `https://datacatalog.cookcountyil.gov/resource/{4x4}.json` and `https://datacatalog.cookcountyil.gov/api/views/{4x4}.json` both fetched successfully. **[VERIFIED]**

- **Assessor - Single and Multi-Family Improvement Characteristics** — `x54s-btds` **[VERIFIED — full column list retrieved]**
  - **This is your year-built backbone.** Covers all of Cook County, **1999 to present**, updated **monthly**.
  - **Row grain is the improvement (building), not the parcel** — multiple rows per PIN mean multiple buildings on the parcel, disambiguated by `card`. This is exactly what you want for a buildings database.
  - Key API fields: **`char_yrblt` (year built)**, `pin`, `pin10`, `year` (tax year), `card`, `class` (property class), `char_bldg_sf`, `char_land_sf`, `char_apts` (units), `char_beds`, `char_rooms`.
  - **No stories/height field** in this dataset — get height and floors from the city footprints layer or CTBUH.
  - Example pull:
    ```
    https://datacatalog.cookcountyil.gov/resource/x54s-btds.json
      ?$select=pin,card,year,class,char_yrblt,char_bldg_sf,char_apts
      &$where=char_yrblt > 1780 AND year = 2024
      &$limit=50000&$offset=0
    ```
  - **Data-quality warning:** assessor year-built values are notoriously rounded and defaulted. Expect enormous spikes at 1900, 1910, 1920, and every decade boundary; expect post-rehab years overwriting original construction years. Treat as `confidence = medium` and let any documentary source override it.

- **Assessor - Parcel Universe** — `nj4t-kc8j` **[VERIFIED — full column list retrieved]**
  - "A complete, historic universe of Cook County parcels with attached geographic, governmental, and spatial data." Bi-weekly updates.
  - Fields: `pin` (14-digit), `pin10`, `tax_year`, `zip_code`, **`latitude`, `longitude`**, `centroid_x_crs_3435`, `centroid_y_crs_3435`, `township_name`, `township_code`, `neighborhood_code`, `municipality_name`, `municipality_num`, census block group / tract / congressional district, school districts, fire/library/park/sanitation districts, TIF district.
  - **Contains no year-built column** — its job is to give every PIN coordinates and geography. Join `x54s-btds` → `nj4t-kc8j` on `pin`.
  - **Critical gotcha, stated in the dataset's own metadata:** PINs must be zero-padded to 14 characters; CSV downloads silently strip leading zeros. Read PIN as string, always.

- **Assessor - Residential Condominium Unit Characteristics** — `3r7i-mrz4` **[VERIFIED via catalog]** — 1999–present. Needed because condo buildings appear as hundreds of unit PINs; you must collapse to one building row.
- **Assessor - Commercial Valuation Data** — `csik-bsws` **[VERIFIED via catalog]** — 2021–present. Thin on history but the only structured commercial characteristics source.
- **Assessor [Archived 05-11-2022] - Residential Property Characteristics** — `bcnq-qi2z` **[VERIFIED via catalog]** — the legacy CAMA extract; different field names, worth diffing against `x54s-btds` for year-built disagreements.
- **Assessor - Parcel Addresses** — `3723-97qp` **[VERIFIED via catalog]** — situs + mailing addresses per PIN. Your PIN↔address crosswalk.
- **Assessor - Parcel Sales** — `wvhk-k5uv` **[VERIFIED via catalog]** — 1999–present; sale immediately preceding a demolition permit is a strong developer/teardown signal.
- **Assessor - Parcel Proximity** — `ydue-e5u3` **[VERIFIED via catalog]** — distances to spatial features; useful derived covariates.
- **Cook County Address Points** — `78yw-iddh` **[VERIFIED via catalog]** — Cook County GIS, "one point for every address." Use this as the master address gazetteer since Chicago has no equivalent open dataset.
  - Historical 2016 township-level address point layers also exist: `7832-c962` (Area 03), `nkzg-ucit` (06), `rxi4-nx3v` (07), `6y64-fiuv` (13), `ai6s-9ihv` (15), `mqn9-4wmy` (22), `vhk7-x9yc` (27), `d8c2-rize` (29), `7fn9-axdp` (33). **[VERIFIED via catalog]**
- **ccgisdata parcel polygon vintages** — `77tz-riq7` (2021), `2yvh-uwrw` (2020), `a33b-b59u` (2016 historical), `nxb6-rw3s` (2015 historical) **[VERIFIED via catalog]** — annual parcel geometry; parcel consolidation between vintages is another demolition/redevelopment signal.
- **Assessor's open-source stack:** the CCAO publishes its data pipelines and an R package on GitHub (`github.com/ccao-data`) **[UNVERIFIED]** — worth checking for canonical field dictionaries.

### 1.4 National Register of Historic Places (NPS)

- **NPGallery NRHP search:** https://npgallery.nps.gov/NRHP/ **[VERIFIED]**
  - Search by resource name (any/all words/phrase), state, county, city, reference number, NPS park, and record category.
  - **Full nomination PDFs** — the single richest per-building narrative source in existence for listed properties: construction dates, architect attribution, style, alteration history, bibliography. Chicago has hundreds of individual listings plus dozens of historic districts whose nominations contain **building-by-building inventories with addresses, dates and contributing/non-contributing status**. Mining district nominations is the highest-yield manual task on this whole list.
  - No API advertised on the landing page. Asset URLs follow `https://npgallery.nps.gov/GetAsset/{uuid}` and NRHP documents are commonly reachable as `https://npgallery.nps.gov/NRHP/GetAsset/{refnum}_text` (nomination) and `_photos` **[UNVERIFIED pattern]**. Scrape the search results to harvest reference numbers, then fetch assets.

- **NPS "NRHP Data Downloads":** https://www.nps.gov/subjects/nationalregister/data-downloads.htm **[VERIFIED]**
  - Bulk Excel spreadsheets, dated (current release observed: **2026-05-22**):
    - `national-register-listed_20260522.xlsx` — all listed properties
    - `national-register-removed_20260522.xlsx` — **delistings, which usually mean demolition**
    - `national-register-mps-covers_20260522.xlsx` — Multiple Property Documentation Forms
    - `National-Historic-Landmarks_20260522.xlsx`
    - `federal-DOEs_20260522.xlsx` — Federal Determinations of Eligibility
    - `national-register-everything_20260522.xlsx` — the comprehensive file; **start here**
    - `NR-NHL-NRIS-terms_20210805.pdf` — NRIS terminology reference / data dictionary
  - **Spatial data:** unrestricted NRIS inventory as an ESRI file geodatabase, distributed through the **NPS IRMA portal** (link in the "holdings" section of the IRMA record).
  - **Fields:** reference number, resource name, address, city/county/state, listing date, architect/builder, architectural style, area of significance, period of significance, level of significance, resource type/counts.
  - **How to get it:** direct bulk download. Filter `state = Illinois AND county = Cook AND city = Chicago`. The date stamp in the filename changes with each release — scrape the page for the current filename rather than hardcoding.

- **NRHP Weekly List:** https://www.nps.gov/subjects/nationalregister/weekly-list.htm **[UNVERIFIED]** — weekly announcements of new listings, pending nominations and removals. Poll to keep designation status current.

### 1.5 HABS / HAER / HALS at the Library of Congress

- **Collection:** https://www.loc.gov/collections/historic-american-buildings-landscapes-and-engineering-records/ **[VERIFIED]**
- **JSON API confirmed working:**
  `https://www.loc.gov/collections/historic-american-buildings-landscapes-and-engineering-records/?q=Chicago&fo=json` **[VERIFIED]**
  - Add `&c=100&sp={page}` to paginate; `&at=results` to trim the payload.
- **Why it matters:** HABS documented many Chicago buildings *immediately before demolition* — often the only measured record of a lost structure. This is a primary source of demolished-building data with construction dates.
- **Per-item fields observed:** title, call number, control number, creator/contributor with roles, description with counts of photos/drawings/data pages, subject headings, place, digital access URLs and thumbnails, rights, repository, **survey number** (e.g. `HABS ILL,16-CHIG,...`), **construction dates**, and significance notes.
- **Materials:** large-format photographs, measured drawings, and **data pages** (PDF histories — read these; they contain architect, date, and demolition circumstances).
- **How to get data out:** JSON API for the index; then fetch item-level JSON at `https://www.loc.gov/item/{id}/?fo=json` and pull the PDF data pages. All public domain, no rights clearance needed.

### 1.6 Illinois SHPO (State Historic Preservation Office)

- **Agency:** https://dnrhistoric.illinois.gov/ **[VERIFIED]** — the Historic Preservation Division within Illinois DNR. Administers the National Register in Illinois and holds the statewide survey files.
- **HARGIS** (Historic Architectural Resources Geographic Information System) — the statewide GIS of surveyed and listed historic properties. **[UNVERIFIED — the guessed path `dnrhistoric.illinois.gov/preserve/architecture-history/hargis.html` returned 404, and the agency homepage does not name it]**. Navigate from the site's Preservation → Architecture & History section, or contact SHPO directly at (217) 782-4836. Access is often restricted to CRM professionals and government users; expect to request an account.
- **Survey files:** paper and digital Illinois Historic Structures Survey (1970s) and later county/municipal surveys, held in Springfield. Not online. **Manual request.**
- **Also on site:** online resources for African American History and Historic Buildings, a photo gallery, and an Illinois history timeline.

### 1.7 Sanborn Fire Insurance Maps

- **Library of Congress digital collection:** https://www.loc.gov/collections/sanborn-maps/ **[VERIFIED]**
- **JSON API confirmed working:**
  `https://www.loc.gov/collections/sanborn-maps/?q=Chicago&fa=location:illinois&fo=json` **[VERIFIED]**
  - Returns `id`, `title`, `date`, `description`, `location_city/county/state/country`, `location_secondary`, `digitized`, `access_restricted`, `image_url` (multiple resolutions), `resource` links, **`segments` (sheet count)**, `created_published`, `mime_type`, `format`, `language`, plus geographic facets.
- **Why it is essential:** each Sanborn sheet shows every structure on a block with **footprint, number of stories, construction material (brick/frame/stone), use, and street address**. Comparing Chicago volumes across survey years (roughly 1880s, 1890s, 1900s, 1910s, and continuously-updated "pasted" editions through the 1950s–70s) lets you bracket both construction and demolition to a few years for buildings that appear in no permit database.
- **Access model:**
  - LOC: free, public domain for pre-1923 volumes; **later volumes are `access_restricted` and only viewable onsite at LOC**. Check the `access_restricted` flag before building a scraper.
  - **ProQuest Digital Sanborn Maps** — the licensed product covering the full run including post-1923 editions. Access via Chicago Public Library or a university. **[UNVERIFIED URL]** typically `sanborn.umi.com`.
  - **Chicago History Museum** holds Sanborn maps in its research center (§2.1) **[VERIFIED]**.
- **How to get data out:** **Manual/georeferencing project.** There is no OCR'd structured Sanborn dataset. Realistic approach: download page images via the LOC API, georeference the sheets in QGIS, and digitize footprints for target blocks. Some volunteer georeferencing already exists (see the LOC "Sanborn Maps" georeferencer and the NYPL Building Inspector model) — check before duplicating effort.

### 1.8 Other government sources worth adding

- **Chicago Zoning / Land Use inventory (CMAP)** — https://cmap.illinois.gov/data/ **[UNVERIFIED]** — regional land use inventories from 1990 onward; useful for parcel-level use classification and change detection.
- **Sanborn-adjacent: Chicago Plat Books and Robinson's Atlas of Chicago (1886)** — on the LOC and Newberry; block-level building outlines pre-dating most Sanborn coverage. **[UNVERIFIED]**
- **US Census Bureau building permits (C-40)** — https://www.census.gov/construction/bps/ **[UNVERIFIED]** — aggregate counts only, no addresses; useful for validating annual construction totals.
- **Chicago Municipal Code / Journal of the Proceedings of the City Council** — landmark ordinances, street name and address renumbering ordinances (see §6 on the 1909 renumbering). Available through the Municipal Reference Collection (§2.3).

---

## 2. ARCHIVES / LIBRARIES / MUSEUMS

### 2.1 Chicago History Museum (Abakanowicz Research Center)

- **Research landing:** https://www.chicagohistory.org/research/ **[VERIFIED]**
- **ARCHIE online catalog:** https://i-share-chm.primo.exlibrisgroup.com/discovery/search?vid=01CARLI_CHM:CARLI_CHM **[VERIFIED — URL confirmed from CHM site]**
- **CHM Images (digital image archive):** https://images.chicagohistory.org/ **[VERIFIED — URL confirmed from CHM site]**
- **Research Center LibGuide:** http://libguides.chicagohistory.org/research **[VERIFIED — URL confirmed from CHM site]**
- **Holdings relevant to you:** printed materials, archives and manuscripts, **prints and photographs**, **architectural drawings**, ephemera, **Sanborn maps**, and **onsite access to the historical Chicago Tribune and Chicago Defender newspaper databases**.
- The **Chicago Daily News negatives collection** (~55,000 glass plate negatives, 1902–1933) is a CHM holding; much of it is digitized and also mirrored in the Library of Congress "Chicago Daily News" collection at https://www.loc.gov/collections/chicago-daily-news-negatives/ **[UNVERIFIED]** — that LOC mirror is API-accessible with `?fo=json` like other LOC collections and is a very rich source of dated exterior photographs of buildings that no longer exist.
- **How to get data out:** ARCHIE is Ex Libris Primo — it has a **Primo/PNX search API** and supports deep-linked queries, so index harvesting is feasible. CHM Images is browsable but licensing is restrictive (most images purchasable, not freely reusable). **Metadata harvest OK; image reuse requires permission.**

### 2.2 Explore Chicago Collections

- **URL:** https://explore.chicagocollections.org/ **[UNVERIFIED — returns 403 to automated fetchers]**
- **What it is:** a federated discovery layer over the finding aids and digital objects of **20+ Chicago-area archives** (Chicago History Museum, Newberry, UIC, University of Chicago, Loyola, DePaul, Northwestern, Columbia College, Art Institute, Chicago Public Library, and more), run by the Chicago Collections Consortium.
- **Why it matters:** one search across every institution's architectural drawings, photographs and organizational records, with browse-by-place and browse-by-topic that map directly onto neighborhoods and building types.
- **How to get data out:** **Scrape / manual.** No public API advertised. Because it aggregates EAD finding aids, individual member institutions may expose OAI-PMH endpoints that are easier to harvest than the portal itself.

### 2.3 Chicago Public Library

- **Archives & special collections:** https://www.chipublib.org/archives-collections/ **[VERIFIED]**
  - Named collections observed: **Vivian G. Harsh Research Collection of Afro-American History and Literature**, **Northside Neighborhood History Collection** (incl. LGBTQIA+ materials 1974–2003), **Special Collections at the Harold Washington Library Center**, plus subject-organized holdings across 20+ subjects including Government & Politics and Business & Labor.
  - An A–Z collections directory and photo-reproduction ordering service are available; `https://www.chipublib.org/a-z-resources/` returned 404 **[BROKEN as written — navigate from the archives page instead]**.
- **Digital collections:** https://www.chipublib.org/digital/ **[UNVERIFIED — referenced on the verified archives page]**
- **Municipal Reference Collection** (formerly the Municipal Reference Library) — the city's own documents: Council proceedings, department annual reports, building department records, city directories, and the Chicago Plan Commission files. Now folded into HWLC Special Collections. **[UNVERIFIED — the direct URL `chipublib.org/archival_post/municipal-reference-collection/` 404s; ask via the archives page]** This is where you find **pre-1906 building department permit ledgers** if any survive.
- **Online resources / databases with a library card:** https://www.chipublib.org/online-resources/ **[VERIFIED]** — confirmed: **Chicago Sun-Times via NewsBank** (`https://chipublib.idm.oclc.org/login?url=https://infoweb.newsbank.com/apps/news/browse-pub`) and the **New York Times**. ProQuest Historical Newspapers and Digital Sanborn were **not** visible on that page **[UNVERIFIED]** — see §5 for how to confirm.

### 2.4 Ryerson & Burnham Libraries, Art Institute of Chicago

- **URL:** https://www.artic.edu/research/ryerson-burnham-libraries **[UNVERIFIED — artic.edu returns 403 to automated fetchers]**
- **What it holds:** the premier architectural archive for Chicago. **Architectural drawings** (Burnham & Root, D.H. Burnham & Co., Holabird & Roche/Root, Adler & Sullivan material, Daniel Burnham's papers, Mies-related holdings), architectural photography, and the **Burnham Index to Architectural Literature** — a card-catalog-derived index to periodical articles about individual buildings, which is the fastest way to find contemporary trade-press coverage of a specific Chicago building.
- **Also:** the **Ryerson & Burnham Archives digital collections** and the AIC's digital publications.
- **How to get data out:** **Manual / onsite**, with a growing digitized subset. Finding aids are also surfaced through Explore Chicago Collections (§2.2). Appointment required for originals.

### 2.5 University of Illinois Chicago — Special Collections & University Archives

- **URL:** https://www.lib.uic.edu/collections/special-collections/ **[UNVERIFIED — robots/DNS failure from this environment]**
- **What it holds:** the strongest holdings on **Chicago neighborhoods, community organizations, and urban renewal** — Hull-House records, Chicago Urban League, community area social service agencies, and extensive neighborhood photographic collections. UIC's own campus construction destroyed the Near West Side Italian neighborhood, and the archive documents what was there.
- **Key digital collection:** UIC Digital Collections, including the **Chicago Neighborhood Photograph Collections**. **[UNVERIFIED]**
- **How to get data out:** manual; finding aids federated into Explore Chicago Collections.

### 2.6 University of Chicago — Special Collections Research Center

- **URL:** https://www.lib.uchicago.edu/scrc/ **[VERIFIED]**
- **Finding aids search:** https://www.lib.uchicago.edu/scrc/finding-aids/ **[VERIFIED — URL confirmed on site]**
- **Collections by subject:** https://www.lib.uchicago.edu/collex/?view=subjects **[VERIFIED — URL confirmed on site]**
- **What it holds:** rare books, manuscripts, University archives, and the **University of Chicago Photographic Archive** (strong on Hyde Park/Kenwood and South Side buildings, plus the 1893 World's Columbian Exposition). Also the Chicago Jazz Archive and significant urban sociology (Chicago School) records with neighborhood surveys.
- **Access:** open to all researchers; appointments required for the general public.
- **How to get data out:** manual; the Photographic Archive is browsable online with item-level metadata.

### 2.7 Newberry Library

- **Digital collections:** https://collections.newberry.org/ **[VERIFIED]**
- **What it holds:** manuscripts, **maps** (one of the great cartographic collections in North America), books, photographs, postcards, broadsides, and art. Chicago-relevant items observed include **Auditorium Theater programs 1888–1938**, the **John High postcard collection (ca. 1890s–1910s)**, a Chicago protest collection, and church records.
- **Map projects:** "Mapping Outside the Lines," the **Atlas of Historical County Boundaries**, "Indigenous Chicago," and "Mapping Movement."
- **Why it matters for buildings:** the Newberry holds Chicago fire insurance atlases, Rand McNally output, **city directories**, and the Pullman Company archive. Postcards are an underrated dated-photograph source for demolished commercial buildings.
- **How to get data out:** the digital collections platform supports item-level browsing and downloads; there are crowdsourced transcription projects (including a Zooniverse postcard-tagging project) whose outputs may be reusable. **Scrape / manual.**

### 2.8 Additional archives worth listing

- **Northwestern University Libraries — Charles Deering McCormick Library of Special Collections** **[UNVERIFIED]** — co-publisher of greatchicagofire.org; holds Chicago transportation and civic records.
- **Illinois Institute of Technology, Paul V. Galvin Library** **[UNVERIFIED]** — the **Mies van der Rohe Society** and IIT campus records; the definitive Mies-in-Chicago holdings alongside MoMA.
- **Loyola, DePaul, Columbia College Chicago archives** **[UNVERIFIED]** — all Chicago Collections Consortium members, reachable via §2.2.
- **Frank Lloyd Wright Trust / Wright archives (Avery Library, Columbia + MoMA)** **[UNVERIFIED]** — the Wright drawings archive is jointly held by Avery and MoMA; Oak Park/River Forest work sits just outside city limits but Chicago work (Robie House, Rookery lobby, Bach House, Emil Bach) is in scope.

---

## 3. REFERENCE WORKS / ENCYCLOPEDIAS

### 3.1 The Encyclopedia of Chicago

- **URL:** https://www.encyclopedia.chicagohistory.org/ **[UNVERIFIED — robots.txt/SSL failure from this environment; URL confirmed as live from the Chicago History Museum research page]**
- **Publisher:** Chicago History Museum, the Newberry Library, and Northwestern University (print edition, University of Chicago Press, 2004).
- **Covers:** ~1,400 entries plus biographical dictionaries, the **Dictionary of Leading Chicago Businesses**, and — most useful to you — **individual entries for all 77 community areas** with development chronologies, and thematic entries on architecture, the Chicago School, balloon-frame construction, building codes, and the fire.
- **How to get data out:** **Scrape.** Entry URLs follow `.../pages/{id}.html`. Free, no paywall. Good for community-area context and cross-referencing, not for per-building records.

### 3.2 SAH Archipedia

- **URL:** https://sah-archipedia.org/ **[UNVERIFIED — 403 to automated fetchers]**
- **Publisher:** Society of Architectural Historians, with the University of Virginia Press.
- **Covers:** the digital successor to the *Buildings of the United States* series. **Buildings of Illinois** contributes several hundred Chicago entries with scholarly, citable descriptions.
- **Fields per entry:** building name, address, coordinates, architect, date, style, a scholarly narrative, and bibliography.
- **Access model:** a free "Archipedia Classic Buildings" subset (~100 buildings/state) is open; the **full text is subscription** (institutional, or free through many libraries).
- **How to get data out:** **Scrape the free tier; manual for the rest.** URL pattern `sah-archipedia.org/buildings/{state}-{number}`. Best used as a high-confidence authority to *adjudicate* conflicting dates rather than as bulk input.

### 3.3 AIA Guide to Chicago

- **Citation:** Alice Sinkevitch and Laurie McGovern Petersen, eds., *AIA Guide to Chicago*, **3rd edition**, University of Illinois Press, 2014 (1st ed. 1993, 2nd ed. 2004). A 4th edition has been discussed. **[UNVERIFIED edition status]**
- **Covers:** ~2,000 extant Chicago buildings organized by neighborhood, each with address, architect, completion date, and a short critical description.
- **How to get data out:** **Manual (book).** No digital edition with structured data. It is nevertheless the best single printed cross-check for architect attribution and completion year on notable extant buildings, and its neighborhood organization maps cleanly onto community areas. Worth OCR-ing your own copy for internal reconciliation.

### 3.4 Chicago's Famous Buildings

- **Citation:** Franz Schulze and Kevin Harrington, eds., *Chicago's Famous Buildings*, **5th edition**, University of Chicago Press, 2003 (originally Arthur Siegel, ed., 1965).
- **Covers:** a curated canon (~200 buildings) with dates, architects, and critical commentary; the earlier editions document buildings demolished between 1965 and 2003, so **old editions are themselves a demolished-buildings source**.
- **How to get data out:** manual.

### 3.5 Frank A. Randall, *History of the Development of Building Construction in Chicago*

- **The definitive year-by-year construction record.** Originally 1949; **2nd edition revised and expanded by John D. Randall, University of Illinois Press, 1999.**
- **Archive.org identifiers (all confirmed present via the advanced-search JSON API) [VERIFIED]:**
  - `historyofdevelop00rand` — https://archive.org/details/historyofdevelop00rand
  - `historyofdevelop0000rand` — https://archive.org/details/historyofdevelop0000rand
  - `historyofdevelop0000rand_02ed` — https://archive.org/details/historyofdevelop0000rand_02ed (the 2nd edition)
  - `historyofdevelop0000fran` — https://archive.org/details/historyofdevelop0000fran
- **Also on HathiTrust** at https://catalog.hathitrust.org/ (search title) **[UNVERIFIED]**.
- **What it gives you:** a chronological listing, year by year from the 1830s to the 1940s, of substantial Chicago buildings with **address, architect, engineer, contractor, number of stories, structural system, construction date, and — crucially — demolition date where known**. Plus a technical narrative on the evolution of foundations, fireproofing and steel framing, and an index by building name and by architect.
- **How to get data out:** archive.org lending is restricted for the in-copyright editions (borrow to read); the 1949 edition may be openly readable. **Realistic approach:** OCR the chronological listing pages and parse into records — it is semi-structured and yields a few thousand high-confidence pre-1950 rows including demolished buildings. This is the highest-value single OCR project on this list.
- **Access model:** archive.org full-text search works even on lending-restricted items, so you can locate a building by address without borrowing.

### 3.6 A. T. Andreas, *History of Chicago* (3 vols., 1884–86)

- **Public domain, on archive.org. Identifiers confirmed via the advanced-search API [VERIFIED]:**
  - `historyofchicago01inandr` — Vol. 1 (to 1857) — https://archive.org/details/historyofchicago01inandr
  - `historyofchicago02andr` — Vol. 2 (1857–1871) — https://archive.org/details/historyofchicago02andr
  - `historyofchicago0000andr` — https://archive.org/details/historyofchicago0000andr
  - `historychicagoo00andrgoog` — Google-scanned copy — https://archive.org/details/historychicagoo00andrgoog
  - (Vol. 3, 1871–1885, exists under a similar identifier — search `q=creator:"Andreas, A. T."`.)
- **Why it matters:** **exhaustive on pre-Fire buildings.** Andreas lists individual structures, their builders, their costs, their occupants, and what happened to them in 1871, with a level of granularity nothing else matches for 1830–1871. Includes engravings of buildings destroyed in the fire.
- **How to get data out:** full public-domain text and DjVu/OCR available for direct download — `https://archive.org/download/{identifier}/{identifier}_djvu.txt`. **Parseable.** Expect messy 19th-century OCR.

### 3.7 City directories, atlases and Rand McNally

- **Archive.org advanced search API [VERIFIED working]:**
  ```
  https://archive.org/advancedsearch.php?q=Chicago+city+directory&fl[]=identifier&fl[]=title&fl[]=year&rows=100&output=json
  ```
- **What to look for:** Lakeside Annual Directory of the City of Chicago (the main run, 1870s–1917), Edwards' Chicago directories (1850s–60s), Rand McNally Chicago guides and bird's-eye views, and Robinson's Atlas of the City of Chicago (1886).
- **Why it matters:** directories give **occupancy by address year over year** — the single best way to establish that a building existed in year X and had ceased to exist by year Y, and to attach original use. Combined with the 1909 renumbering tables (§6), they let you carry an address forward.
- **How to get data out:** bulk download OCR text from archive.org; parse the street-address ("householders") sections, which are already tabular by street and number.
- **Also:** HathiTrust (https://babel.hathitrust.org) holds directory runs not on archive.org. **[UNVERIFIED]**

### 3.8 Other reference works

- **Carl Condit, *The Chicago School of Architecture* (1964) and *Chicago 1910–29* / *Chicago 1930–70*** — the scholarly technical history; strong on structural systems and construction dates. **[UNVERIFIED availability]**
- **Robert Bruegmann, *The Architects and the City: Holabird & Roche of Chicago, 1880–1918*** (1997) — includes a **catalog of ~1,000 Holabird & Roche commissions with dates, addresses and demolition status**. This is the model for what a firm-level catalogue raisonné gives you; several exist for other Chicago firms. **[UNVERIFIED]**
- **Rudolph Schirmer / *Industrial Chicago* (1891–96, 6 vols.)** — "The Building Interests" volumes are on archive.org and constitute a contemporaneous survey of Chicago building. **[UNVERIFIED identifier]**
- **Chicago Landmarks designation reports** (§1.1) function as reference works in their own right.

---

## 4. ENTHUSIAST / SPECIALIST SITES

### 4.1 Chicagology

- **URL:** https://chicagology.com/ **[VERIFIED — and confirmed to block plain HTTP fetching]**
- **Confirmed behavior:** returns a JavaScript-required interstitial ("You are being redirected... Javascript is required"). A plain fetcher gets nothing. **Requires a headless browser (Playwright/Puppeteer) with JS enabled**, and be polite about rate.
- **Covers:** one of the deepest amateur compilations on pre-1930 Chicago — extensive pages on the Great Fire, individual Loop buildings, hotels, theaters, breweries, railroads and the World's Fairs, heavily illustrated with period images and reprinted newspaper text.
- **Value:** excellent for **demolished commercial buildings** where it often reprints contemporary descriptions with dates. Treat as secondary — attribution and dates are inconsistent — but it frequently points to the primary source.

### 4.2 Chicago Architecture Center

- **URL:** https://www.architecture.org/ **[VERIFIED]**
- **Buildings of Chicago database:** https://www.architecture.org/buildings-of-chicago **[VERIFIED — link confirmed on site]** — searchable per-building entries with architect, year, style, address and photos.
- **Architecture Encyclopedia:** https://www.architecture.org/online-resources/architecture-encyclopedia **[VERIFIED — link confirmed on site]**
- **CAC Watch List:** https://www.architecture.org/online-resources/cac-watch-list **[VERIFIED — link confirmed on site]** — significant sites with active preservation issues; a forward-looking demolition-risk signal.
- **City planning resources:** https://www.architecture.org/online-resources/chicago-city-planning-resources **[VERIFIED]**
- **Reports:** https://www.architecture.org/reports **[VERIFIED]**
- **How to get data out:** **Scrape.** No API. The Buildings of Chicago database is well-structured and modest in size (hundreds to low thousands of entries) — a good, clean, curated seed set.

### 4.3 Landmarks Illinois

- **URL:** https://www.landmarks.org/ **[VERIFIED]**
- **What it is:** statewide preservation nonprofit, founded 1971.
- **Relevant outputs:** the annual **"Most Endangered Historic Places in Illinois"** list; the **Illinois Restoration Resource Directory**; a "Surveys & Databases" section; the Landmarks Illinois Reinvestment Program and preservation easements (easement-encumbered buildings are effectively protected — a designation-status nuance worth capturing); the Richard H. Driehaus Foundation Preservation Awards; the biannual newsletter *The Arch* and the *Preservation News* blog.
- **How to get data out:** **Scrape.** Endangered lists are per-year HTML pages; the blog carries demolition news that often predates any dataset.

### 4.4 Preservation Chicago and the "Chicago 7 Most Endangered"

- **URL:** https://preservationchicago.org/ and https://preservationchicago.org/chicago7/ **[UNVERIFIED — repeated HTTP 429 rate-limiting on three attempts; the root URL served unrelated cached content]**
- **What it is:** city-focused advocacy nonprofit. The **"Chicago 7 Most Endangered"** list has been published annually since **2003**, naming seven threatened buildings or building types each year with a detailed dossier on each (address, architect, date, threat, ownership).
- **Why it matters:** it is effectively a **hand-curated demolition-risk register with 20+ years of history**, and the retrospectives note which listed buildings were subsequently lost. Also publishes demolition alerts and testimony to the Commission on Chicago Landmarks.
- **How to get data out:** **Scrape with backoff** — the site rate-limits aggressively; use a headless browser with delays, or work from the annual PDF booklets. Year pages appear to follow `preservationchicago.org/chicago7/` with per-year subpages **[pattern UNVERIFIED]**.

### 4.5 Cinema Treasures

- **URL:** https://cinematreasures.org/ **[VERIFIED]**
- **Chicago browse:** https://cinematreasures.org/theaters/united-states/illinois/chicago **[VERIFIED]**
- **Verified counts: 643 Chicago theaters total** across all statuses (open, closed, demolished, restoring, renovating), of which **50 are currently open**.
- **URL pattern:** `https://cinematreasures.org/theaters/{numeric_id}` (e.g. https://cinematreasures.org/theaters/958).
- **Fields:** the browse table shows name, location, status and screen count; individual theater pages add **address, opened date, closed date, architect, firm, style, seating capacity, previous names, and a community-contributed history with photos**.
- **Why it matters:** the **definitive** database for the movie-palace and neighborhood-theater building type, which Chicago had in enormous numbers and demolished en masse between 1950 and 1990. It carries **opening and closing dates plus demolition notes** for hundreds of buildings that exist in no government dataset.
- **How to get data out:** **Scrape.** No public API. IDs are dense integers — crawl the Chicago index, then fetch each detail page. Respect robots.txt and rate-limit.

### 4.6 Skyscraper databases

- **CTBUH Skyscraper Center** — https://www.skyscrapercenter.com/city/chicago **[UNVERIFIED — 403 to automated fetchers]**
  - The Council on Tall Buildings and Urban Habitat's database. Per-building fields: **official name, other names, status (completed/under construction/demolished/never built), completion year, height to architectural top / tip / occupied floor, floors above and below grade, structural material, function, architect (design and architect of record), structural engineer, MEP engineer, main contractor, developer, owner.**
  - Chicago is one of its deepest cities, and it explicitly tracks **demolished tall buildings**.
  - **API:** CTBUH exposes JSON endpoints behind the site (patterns like `skyscrapercenter.com/api/...` and per-building `/building/{slug}/{id}`) **[UNVERIFIED]**; there is also a "Data Export" for members. Practically: scrape with a headless browser, or apply for research data access at https://www.ctbuh.org/ **[UNVERIFIED]**.
  - **Best-in-class for `height_ft`, `floors`, and structural material** on anything over ~12 stories.

- **SkyscraperPage** — https://skyscraperpage.com/ **[VERIFIED — site fetches fine]**
  - **Warning: `cityID=6` is Shanghai, not Chicago.** Find Chicago's `cityID` by navigating `skyscraperpage.com/cities/` → United States → Illinois → Chicago before hardcoding. **[Chicago cityID UNVERIFIED]**
  - Per-building fields observed: name, **floors**, **construction status** (built / under construction / proposed / on hold / demolished / never built), **completion year**, and count of scale drawings. Height and architect are on detail pages rather than the index.
  - URL patterns: database listing `https://skyscraperpage.com/cities/?cityID={id}` (supports status and offset pagination); diagrams `https://skyscraperpage.com/diagrams/?cityID={id}`; individual building `https://skyscraperpage.com/cities/?buildingID={id}`.
  - **How to get data out:** **Scrape.** No API. Its distinctive value is the **proposed and never-built** inventory and its coverage of mid-rise buildings CTBUH ignores.

- **Emporis — DEFUNCT.** Emporis (emporis.com), long the most comprehensive building database including thousands of Chicago mid-rises, **shut down in 2022**. **[VERIFIED: what replaced it]** — its editorial lineage continued as **Phorio**, and `https://www.phorio.com/` now issues a **302 redirect to `https://www.skydb.net/?from=phorio`**.
  - **SKYDB** — https://www.skydb.net/ **[VERIFIED]** — claims **212,085 verified tall buildings** worldwide, maintained by editors and community contributors verifying against primary sources. Tracks height, floor count, status (existing / under construction / in planning / vision / **demolished**), completion year, location, and associated companies (architect, developer, engineer), plus photos and renderings. Chicago coverage is not explicitly stated on the landing page but is near-certain given scope. **[Chicago coverage UNVERIFIED]**
  - **Also check the Wayback Machine for emporis.com** — `https://web.archive.org/web/*/emporis.com/city/101026/chicago-il-usa*` — the old Chicago building lists are partly preserved and contain data that never migrated anywhere. **[UNVERIFIED]**

### 4.7 Blogs and independent research sites

- **Chicago Patterns** — https://chicagopatterns.com/ **[VERIFIED]** — long-form documentation of Chicago's architectural heritage neighborhood by neighborhood: endangered and damaged landmarks, **recently demolished historic buildings**, post-Fire Loop commercial architecture, and churches. Contributors include Eric Allix Rogers, Gabriel X. Michael and John Morris. Functions as both archive and advocacy platform. **Scrape; excellent demolition-event coverage with dates and photographs.**
- **Forgotten Chicago** — https://forgottenchicago.com/ **[VERIFIED]** — documents modernist architecture, urban development, transportation infrastructure and vanishing streetscape details. Features: walking tours and webinars (with the Chaddick Institute and Docomomo), a **Flickr pool of historical photographs**, "Images of America" books by the editors (Logan Square, Avondale), a legacy read-only forum, and an active subreddit. **Scrape articles; the Flickr pool is separately harvestable via the Flickr API.**
- **The Architecture Professor** — https://www.thearchitectureprofessor.com/ **[VERIFIED]** — by **Jerry Larson**. Deep, well-researched chronological treatment of Chicago architecture: **pre-Fire Chicago 1803–1871 on a companion blog**, post-Fire 1874–1891 on the main blog, and the Chicago School (Root, Burnham & Root). Detailed analysis of the Masonic Temple, Monadnock, Woman's Temple and other **demolished** landmarks, with drawings, period photographs and structural analysis. **One of the best free secondary sources for demolished 1870s–1890s Loop buildings.**
- **Digital Research Library of Illinois History Journal** — https://drloihjournal.blogspot.com/ **[VERIFIED]** — by Dr. Neil Gale. **3,247+ articles**, over 112 million reads since December 2016. Covers Chicago landmarks and infrastructure, the Great Fire, Marshall Field & Co., the 1893 World's Columbian Exposition, amusement parks (Riverview), theaters, restaurants, forts and lost towns. Organized with 100+ keyword tags, monthly/yearly archives from November 2016, and full-text search. **Blogger platform — has a built-in feed API** (`/feeds/posts/default?alt=json&max-results=500`), which makes bulk harvesting easy. Secondary source; verify dates.
- **Jazz Age Chicago** (Scott Newman) — historically at `chicago.urban-history.org` **[BROKEN — DNS does not resolve]**. Covered Chicago urban leisure 1893–1945: ballrooms, movie palaces, amusement parks, department stores, and sports venues, with per-venue building histories. **Retrieve from the Wayback Machine:** `https://web.archive.org/web/*/chicago.urban-history.org/*`.
- **Chicago Detours** — chicagodetours.com **[BROKEN — the domain currently serves Indonesian online-gambling spam; the site appears hijacked or expired]**. Its architecture/history blog content, if wanted, must come from the Wayback Machine: `https://web.archive.org/web/*/chicagodetours.com/*`. **Do not link users to the live domain.**
- **The Great Chicago Fire and the Web of Memory** — https://greatchicagofire.org/ **[VERIFIED]** — a 2011 collaboration of the **Chicago Historical Society and Northwestern University**. Two halves: (1) the fire itself in five chronological sections — pre-fire Chicago, the conflagration, the destruction, the recovery, and the rebuilding; (2) cultural memory — eyewitness accounts, journalism, literature and art, the O'Leary legend, souvenirs and commemorations. Hosts photographs, illustrations, eyewitness accounts, contemporary journalism, 3-D images, an **1871 timeline**, and a touring section covering **54 historically significant landmarks connected to the fire**. Images are mostly CHM-owned and purchasable. **Scrape text; the "rebuilding" section is a good source for 1872–74 construction.**
- **Other worth adding [all UNVERIFIED]:** *Chicago Architecture Blog* (chicagoarchitecture.org) for current construction pipeline; *Curbed Chicago* archives (now folded into Chicago magazine / Block Club) for 2010s demolition news; *Block Club Chicago* (blockclubchicago.org) for current neighborhood-level demolition reporting; *Docomomo US/Chicago* for postwar modernism; *Society of Architectural Historians Chicago chapter*; the *r/chicago* and *ChicagoArchitecture* subreddits and SkyscraperCity/SkyscraperPage forums, whose Chicago development threads often record demolition dates before any official source.

### 4.8 Wikipedia and Wikidata

**[Wikipedia/Wikidata domains were cache-only in this environment — all URLs and the queries below are UNVERIFIED but follow documented, stable APIs.]**

- **Wikipedia raw wikitext** (the markdown converter strips tables, so always use `action=raw`):
  ```
  https://en.wikipedia.org/w/index.php?title=List_of_tallest_buildings_in_Chicago&action=raw
  https://en.wikipedia.org/w/index.php?title=List_of_demolished_buildings_and_structures_in_Chicago&action=raw
  https://en.wikipedia.org/w/index.php?title=Category:Buildings_and_structures_in_Chicago&action=raw
  https://en.wikipedia.org/w/index.php?title=National_Register_of_Historic_Places_listings_in_Chicago&action=raw
  https://en.wikipedia.org/w/index.php?title=List_of_Chicago_Landmarks&action=raw
  ```
  The NRHP-listings and Chicago Landmarks list articles are large sortable wikitables containing name, image, listing date, address, coordinates and a description — parse the wikitext directly.
- **MediaWiki API** for category traversal:
  ```
  https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Buildings_and_structures_in_Chicago&cmlimit=500&format=json
  ```
  Recurse subcategories (by decade of completion, by neighborhood, by type, "Demolished buildings and structures in Chicago").

- **Wikidata SPARQL** — https://query.wikidata.org/ (endpoint `https://query.wikidata.org/sparql`). Accepts GET or POST with `query=`, `Accept: application/sparql-results+json`, and a descriptive `User-Agent` (required — anonymous requests are throttled).

  **Example: every building in Chicago with coordinates, architect, inception and demolition date.**

  ```sparql
  SELECT ?building ?buildingLabel ?coord ?inception ?demolished
         ?architectLabel ?styleLabel ?heritageLabel ?floors ?height ?image
  WHERE {
    ?building wdt:P131* wd:Q1297 .            # located in administrative entity: Chicago (Q1297)
    ?building wdt:P31/wdt:P279* wd:Q41176 .   # instance of building (Q41176) or any subclass

    OPTIONAL { ?building wdt:P625  ?coord }       # coordinate location
    OPTIONAL { ?building wdt:P571  ?inception }   # inception (construction/completion)
    OPTIONAL { ?building wdt:P576  ?demolished }  # dissolved, abolished or demolished date
    OPTIONAL { ?building wdt:P84   ?architect }   # architect
    OPTIONAL { ?building wdt:P149  ?style }       # architectural style
    OPTIONAL { ?building wdt:P1435 ?heritage }    # heritage designation
    OPTIONAL { ?building wdt:P1101 ?floors }      # floors above ground
    OPTIONAL { ?building wdt:P2048 ?height }      # height
    OPTIONAL { ?building wdt:P18   ?image }       # image

    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  }
  ```

  **Variant: demolished Chicago buildings only** — replace the `OPTIONAL` on `P576` with a required triple:
  ```sparql
  SELECT ?building ?buildingLabel ?inception ?demolished ?architectLabel ?coord
  WHERE {
    ?building wdt:P131* wd:Q1297 ;
              wdt:P31/wdt:P279* wd:Q41176 ;
              wdt:P576 ?demolished .
    OPTIONAL { ?building wdt:P571 ?inception }
    OPTIONAL { ?building wdt:P84  ?architect }
    OPTIONAL { ?building wdt:P625 ?coord }
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  }
  ORDER BY ?demolished
  ```

  **Programmatic fetch:**
  ```
  https://query.wikidata.org/sparql?format=json&query={URL-encoded SPARQL}
  ```
  If the query times out (60s limit), narrow `wdt:P31/wdt:P279*` to specific classes (`wd:Q41176` building, `wd:Q811979` architectural structure, `wd:Q18142` high-rise, `wd:Q16970` church building, `wd:Q24354` theater) and union the results, or use the Wikidata Query Service's `?dump` alternatives / the weekly JSON dumps at https://dumps.wikimedia.org/wikidatawiki/entities/.

  **Useful Wikidata properties for your schema:** P31 instance of, P131 located in admin entity, P625 coordinates, P6375 street address, P571 inception, P1619 date of official opening, P576 dissolved/demolished, P84 architect, P193 main building contractor, P88 commissioned by, P149 architectural style, P1101 floors above ground, P1139 floors below ground, P2048 height, P2044 elevation, P366 use, P1435 heritage designation, P649 NRHP reference number, P1600 Chicago Landmark ID **[property ID UNVERIFIED]**, P856 official website, P18 image.

### 4.9 OpenStreetMap

- **Overpass API endpoints:** `https://overpass-api.de/api/interpreter`, `https://overpass.kumi.systems/api/interpreter`, `https://z.overpass-api.de/api/interpreter`
- **[Query UNVERIFIED — the public endpoint returned HTTP 406 to this environment's GET request; Overpass generally wants a POST with the query in the `data` form field, or a GET with `Accept: */*`. Test with `curl -d @query.overpassql` before relying on it.]**

  **Example: all Chicago buildings that carry a `start_date` tag.**
  ```overpassql
  [out:json][timeout:300];
  area["boundary"="administrative"]["admin_level"="8"]["name"="Chicago"]->.chi;
  (
    way["building"]["start_date"](area.chi);
    relation["building"]["start_date"](area.chi);
  );
  out tags center;
  ```

  **Example: all Chicago building footprints with full geometry** (large — expect a multi-GB response; prefer an extract):
  ```overpassql
  [out:json][timeout:900];
  area["boundary"="administrative"]["admin_level"="8"]["name"="Chicago"]->.chi;
  (
    way["building"](area.chi);
    relation["building"](area.chi);
  );
  out body;
  >;
  out skel qt;
  ```

  **Example: heritage/designated buildings in Chicago:**
  ```overpassql
  [out:json][timeout:300];
  area["boundary"="administrative"]["admin_level"="8"]["name"="Chicago"]->.chi;
  (
    nwr["heritage"](area.chi);
    nwr["ref:nrhp"](area.chi);
    nwr["historic"="building"](area.chi);
  );
  out tags center;
  ```

- **Useful OSM tags:** `building=*`, `building:levels`, `height`, `start_date`, `name`, `addr:housenumber`/`addr:street`, `architect`, `building:architecture`, `heritage`, `heritage:operator`, `ref:nrhp`, `wikidata`, `wikipedia`.
- **The `wikidata` tag is gold** — it gives you a free OSM↔Wikidata↔Wikipedia join key on thousands of Chicago buildings.
- **Bulk alternatives to Overpass (recommended for a full extract):**
  - Geofabrik Illinois extract — https://download.geofabrik.de/north-america/us/illinois.html **[UNVERIFIED]**
  - BBBike custom extract — https://extract.bbbike.org/ **[UNVERIFIED]**
  - OSM full history planet (for detecting when a building was *deleted* from OSM, a weak demolition signal) — https://planet.openstreetmap.org/ **[UNVERIFIED]**
- **Caveat:** Chicago's OSM building layer was largely bulk-imported from the city footprints dataset, so `start_date` coverage is thin and OSM is not an independent source for year built. Its independent value is `wikidata` linkage, current names, and current use.

---

## 5. NEWSPAPERS AND TRADE PRESS

This is where demolition dates for 1871–2005 actually live. Budget serious time here.

### 5.1 Chicago Tribune

- **ProQuest Historical Newspapers: Chicago Tribune (1849–current, with a rolling embargo)** — the fully-searchable page-image archive. **The single most productive source for demolition dates**, because the Tribune reported wrecking contracts, "Old Building to Come Down" items, and real estate transfers in detail.
- **Access:** via **Chicago Public Library card** (ProQuest is standard in CPL's A–Z database list) **[UNVERIFIED — CPL's featured online-resources page confirmed NewsBank/Sun-Times and NYT but did not list ProQuest; confirm at https://www.chipublib.org/online-resources/ or via Ask a Librarian]**. Also available at the Chicago History Museum research center **[VERIFIED — CHM lists Tribune and Defender historical newspaper databases]**, and at any Illinois academic library.
- **Newspapers.com Chicago Tribune archive** — https://chicagotribune.newspapers.com/ **[UNVERIFIED — 403 to automated fetchers]** — a consumer subscription alternative with OCR text, clipping, and a usable (unofficial) API surface for scripted search.
- **How to get data out:** **Manual, or scripted search within a licensed session.** ProQuest terms prohibit bulk scraping. Practical method: query by address string and by building name for a target list, and record citation + date.

### 5.2 Chicago Daily News

- Published 1875–1978. The **Chicago Daily News negatives collection (1902–1933)** at the Chicago History Museum is the photographic counterpart, largely digitized and mirrored at the Library of Congress (https://www.loc.gov/collections/chicago-daily-news-negatives/ **[UNVERIFIED]**, API-accessible with `?fo=json`).
- **Text archive:** less well digitized than the Tribune; check ProQuest, NewsBank, and CHM's ARCHIE (§2.1). **[UNVERIFIED]**

### 5.3 Chicago Inter Ocean

- Published 1872–1914. A major Chicago daily with strong real-estate and building coverage during the boom decades.
- **Access:** Illinois Digital Newspaper Collections (https://idnc.library.illinois.edu/) **[UNVERIFIED]** and **Chronicling America** (Library of Congress, free, full-text, API-accessible) — https://chroniclingamerica.loc.gov/search/pages/results/?state=Illinois&andtext=Chicago&format=json **[UNVERIFIED but Chronicling America's JSON API is well documented and free]**. **This is the best *free, bulk-harvestable* historical newspaper source** for Chicago; check which Chicago titles and date ranges are digitized.

### 5.4 Chicago Defender

- Published 1905–present; **ProQuest Historical Newspapers: Chicago Defender (1910–1975)**.
- **Essential and irreplaceable** for South and West Side buildings — Black-owned businesses, churches, theaters (Regal, Savoy), the Black Metropolis / Bronzeville commercial district, and the demolitions of urban renewal — almost none of which the mainstream dailies covered.
- **Access:** CPL card / CHM research center **[CHM VERIFIED]**.

### 5.5 Trade press — the near-complete permit record

These weekly and monthly trade journals **printed building permits and construction contracts issued in Chicago, essentially in full**, for decades. For the period 1880–1930 they are functionally a machine-readable permit database if you OCR them.

- **The American Contractor** (Chicago, weekly, 1879–1930s) — printed permit lists with **address, owner, architect, cost, and description**. **[UNVERIFIED — search HathiTrust and archive.org for "American Contractor" Chicago]** This is the closest thing to a comprehensive pre-1930 Chicago permit database that exists.
- **The Economist** (Chicago real estate weekly, 1888–1930s) — Chicago real estate and building news, with weekly building-permit summaries and construction cost tables. Distinct from the London *Economist*. **[UNVERIFIED]**
- **Inland Architect and News Record** (Chicago, 1883–1908) — the Chicago School's own journal; published building announcements, plates and obituaries of architects. **Digitized copies exist on archive.org and HathiTrust** — search `archive.org/advancedsearch.php?q=%22Inland+Architect%22&output=json` **[UNVERIFIED]**.
- **Construction News** (Chicago) — successor/contemporary of the above. **[UNVERIFIED]**
- **The Chicago Real Estate Index / Chicago Real Estate and Building Journal** **[UNVERIFIED]**
- **Engineering News-Record**, **The Brickbuilder**, **Architectural Record**, **Western Architect** — national/regional journals with heavy Chicago coverage; most pre-1929 volumes are public domain on archive.org and HathiTrust and **fully bulk-downloadable as OCR text**.
- **How to get data out:** for the public-domain runs, download `_djvu.txt` from archive.org and write a parser for the permit-list format (they are highly regular: `123 N. Clark st., 6-sty brk store & office bldg, $150,000; owner ...; architect ...`). **This is the second-highest-value OCR project on this list after Randall.**
- **The Ryerson & Burnham Burnham Index (§2.4)** indexes these journals by building — use it to target rather than reading everything.

### 5.6 Other newspaper access

- **Chronicling America (LOC)** — free, full-text, JSON API, covers many Illinois titles pre-1963. https://chroniclingamerica.loc.gov/ **[UNVERIFIED]**
- **Illinois Digital Newspaper Collections (UIUC)** — https://idnc.library.illinois.edu/ **[UNVERIFIED]** — free, includes Chicago-area titles.
- **NewsBank / Chicago Sun-Times via CPL** — https://chipublib.idm.oclc.org/login?url=https://infoweb.newsbank.com/apps/news/browse-pub **[VERIFIED — link confirmed on CPL's online resources page]** — covers the modern era (roughly 1985–present) where the Tribune's ProQuest coverage may be embargoed.
- **Block Club Chicago** — https://blockclubchicago.org/ **[UNVERIFIED]** — current neighborhood-level demolition reporting, 2018–present.

---

## 6. CROSS-CUTTING PITFALLS (read before ingesting anything)

1. **The 1909 street renumbering.** Chicago comprehensively renumbered and renamed streets in 1909 (Edward Brennan's grid reform, centered on State & Madison). **Any address from a pre-1909 source is not comparable to a modern address.** You need a conversion table — the standard reference is the 1909–1911 city ordinance renumbering guide, reprinted in city directories and available through the Municipal Reference Collection (§2.3) and on chicagology (§4.1). **Store `address_historical` and `address_modern` as separate columns.**
2. **Annexation.** Chicago's boundaries grew enormously (1889 annexation of Hyde Park, Lake, Lake View, Jefferson quadrupled the city's area; smaller annexations through 1920s). A building "in Chicago" in 1890 may have been in Lake View in 1885 and appear under that name in sources.
3. **The Great Fire (Oct 8–10, 1871)** destroyed ~17,500 buildings and, separately, destroyed the city's own records. There is effectively no municipal building record before 1871. Andreas (§3.6) is the substitute.
4. **Assessor year-built rounding.** Massive artificial spikes at decade boundaries; rehab years overwriting original years. Never treat `char_yrblt` as authoritative when a documentary source disagrees.
5. **Permit ≠ event.** A wrecking permit is an intent; a new-construction permit precedes completion by 1–3 years. Model `permit_date` and `event_date` separately.
6. **Condos and PINs.** One physical building can be 400 PINs. Collapse on `pin10` + building footprint before counting buildings.
7. **Multiple buildings per parcel.** The Assessor's `card` field handles this; most naive joins do not.
8. **Address point ≠ building.** A large building has many address points; a corner building has addresses on two streets. Your `address` field needs a `primary` flag and an alternates table.
9. **Socrata field-name mangling.** Display names (`PERMIT#`) differ from API field names. Always read `/api/views/{4x4}.json` → `columns[].fieldName` before writing queries.
10. **En-dash vs hyphen in `permit_type`.** Confirmed present in the live data. Use `LIKE`/`starts_with` rather than exact equality where possible.

---

## 7. SUGGESTED DATABASE SCHEMA

### 7.1 Core table: `building`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID / bigint PK | Your own surrogate key. Never reuse an external ID as the PK. |
| `name` | text | Best-known name. |
| `alternate_names` | text[] / child table | Former names, developer names, tenant names. Theaters and hotels change names constantly — make this a child table `building_name(building_id, name, name_type, valid_from, valid_to, source_id)`. |
| `address_modern` | text | Normalized post-1909 Chicago address. |
| `address_historical` | text[] | Pre-1909 and pre-annexation addresses. |
| `address_number`, `address_direction`, `address_street`, `address_suffix`, `zip` | text | Parsed components — join on these, not on the full string. |
| `latitude`, `longitude` | numeric(9,6) | WGS84. Prefer footprint centroid > address point > parcel centroid > geocode. |
| `footprint` | geometry(MultiPolygon, 4326) | Nullable — demolished buildings usually have none. |
| `community_area` | smallint + text | One of the 77; derive spatially, don't trust source-supplied values. |
| `ward_historical` | text[] | Wards are remapped every decade; store with a year. |
| `year_started` | smallint | Construction start. |
| `year_completed` | smallint | Completion/opening. **This is your primary date; index it.** |
| `date_completed_precision` | enum | `exact_date` / `year` / `decade` / `range` / `unknown`. |
| `year_demolished` | smallint | |
| `date_demolished_precision` | enum | Same enum. |
| `demolition_cause` | enum | `fire` / `great_fire_1871` / `redevelopment` / `urban_renewal` / `highway` / `public_works` / `collapse` / `condemned` / `abandonment` / `expressway` / `institutional_expansion` / `unknown`. |
| `architect` | text + child table | Make it `building_architect(building_id, person_or_firm_id, role, source_id)` with roles `design_architect`, `architect_of_record`, `associate`, `landscape`, `engineer`, `alteration`. Firms rename constantly (Burnham & Root → D.H. Burnham & Co. → Graham, Anderson, Probst & White) — keep a `firm` table with successor links. |
| `developer` | text | Also `owner_original`, `contractor`. |
| `style` | text[] | Controlled vocabulary; allow multiple (a building can be Chicago School + Sullivanesque). |
| `height_ft` | numeric | Note the measurement basis — architectural top vs. tip vs. roof. Store `height_basis`. |
| `floors` | smallint | Plus `floors_below_grade`. |
| `structural_system` | text | Load-bearing masonry / iron frame / steel frame / reinforced concrete / balloon frame / platform frame. Randall and CTBUH both supply this. |
| `original_use` | text | Controlled vocabulary. |
| `current_use` | text | Null if demolished. |
| `designation_status` | text[] / child table | `building_designation(building_id, authority, designation_type, ref_number, designated_date, removed_date)` where authority ∈ {Chicago Landmark, Chicago Landmark District (contributing), NRHP, NRHP District (contributing), National Historic Landmark, CHRS Red, CHRS Orange, Landmarks Illinois easement}. Designations accrete and get revoked — this must be a child table. |
| `status` | enum | `extant` / `demolished` / `under_construction` / `proposed` / `never_built` / `moved` / `unknown`. |
| `source_urls` | jsonb / child table | See §7.2. |
| `confidence` | enum or numeric 0–1 | Per-field, not per-row — see §7.3. |
| `created_at`, `updated_at` | timestamptz | |

### 7.2 `source` and `assertion` tables — the important part

Do **not** put `source_urls` as a flat array on the building row. Model provenance at the **field** level:

```
source(id, name, url, source_type, publisher, accessed_at, license, reliability_tier)

assertion(id, building_id, field_name, value_text, value_num, value_date,
          source_id, source_locator, extracted_at, confidence, superseded_by)
```

Every value in §7.1 is a *materialized winner* of the assertions for that `(building_id, field_name)`. This is the only structure that survives contact with sources that disagree — and they will disagree constantly about year built.

Suggested `reliability_tier` for adjudication (1 = trumps all):

1. Chicago Landmark designation report, NRHP nomination, HABS data pages
2. Randall; SAH Archipedia; Bruegmann-style firm catalogues; AIA Guide
3. Contemporary trade press (American Contractor, Inland Architect); Sanborn; city directories
4. City permits; CTBUH; Energy Benchmarking
5. Cook County Assessor `char_yrblt`; city footprints year-built
6. Wikipedia/Wikidata; Cinema Treasures; SkyscraperPage; enthusiast blogs

### 7.3 Join keys and reconciliation

**Best join keys, in order of reliability:**

1. **`pin` / `pin10` (Cook County PIN)** — the strongest key for anything extant since ~1999. Joins Assessor characteristics ↔ parcel universe ↔ parcel addresses ↔ sales ↔ parcel geometry. **Always store as a zero-padded 14-character string.** Weakness: parcels get split and consolidated, and a PIN is not a building (use `pin` + `card`).
2. **Spatial join on footprint centroid / point-in-polygon** — the only key that works across city, county, OSM and NRHP data. Buffer 10–20 m and disambiguate by address. This is how you connect the city's building footprints to Cook County parcels.
3. **Normalized address** — `{number}|{direction}|{street}|{suffix}` uppercased, with `STREET`→`ST`, `AVENUE`→`AVE` and ordinal normalization. Works for permits, violations, directories, Cinema Treasures, blogs. **Watch address ranges** (`180-200 N LaSalle`) — expand to a range and match on overlap.
4. **NRHP reference number** — a clean 8-digit integer, joins NPS bulk files ↔ NPGallery PDFs ↔ Wikipedia NRHP lists ↔ OSM `ref:nrhp` ↔ Wikidata P649. **The best cross-domain key you get for free.**
5. **Wikidata QID** — joins Wikipedia, OSM (`wikidata` tag), Wikimedia Commons, and increasingly library authority files. Adopt it as your canonical external ID for notable buildings.
6. **Chicago Landmark `lanId`** (from LandmarksWeb) and the `id` in the `uct4-hrvh` dataset — the internal city keys; join to each other by name+address, then use `lanId` thereafter.
7. **Chicago Energy Benchmarking ID** — stable across years for large buildings.
8. **Name + completion-year fuzzy match** — the fallback for pre-1950 and demolished buildings, where nothing else exists. Use trigram similarity on normalized names plus a ±3-year window on `year_completed`, and require manual review above a similarity threshold.

**Reconciliation strategy:**

- **Build the spine from the Assessor** (`x54s-btds` joined to `nj4t-kc8j` on `pin`), which gives you a row and a year for essentially every extant building. Then **spatially attach city footprints** (`syp8-uezg`) to get geometry, floors and height.
- **Overlay the authorities in reliability order.** For `year_completed`, a designation report or Randall entry overwrites the Assessor unconditionally; the Assessor's value survives only where nothing better exists. Record both as assertions, never destroy the loser.
- **Demolished buildings need a separate ingest path**, because they are absent from every parcel-based source. Build them from: Randall (§3.5), Andreas (§3.6), Cinema Treasures (§4.5), HABS (§1.5), wrecking permits + asbestos NOIs (§1.2) for 2006+, footprint-vintage diffs (§1.2) for ~2005–present, Sanborn diffs (§1.7) for pre-1970, and NRHP removals (§1.4). Then **match them against the extant spine by address and reject any match** — a demolished building whose address now hosts an extant building is expected, not an error; link them with a `successor_building_id`.
- **Flag rather than resolve** disagreements greater than 5 years on `year_completed`, or any conflict on architect attribution. A `needs_review` boolean plus an assertion-count-in-conflict integer will surface the several thousand rows worth human time.
- **Set `confidence` per field.** A reasonable formula: `confidence = f(best_source_tier, agreement_among_sources, date_precision)`. Anything resting solely on tier 5–6 with no corroboration should be ≤ 0.5.

### 7.4 Recommended child tables

```
building_name       (building_id, name, name_type, valid_from, valid_to, source_id)
building_address    (building_id, address_text, address_parsed, is_primary, era, source_id)
building_architect  (building_id, firm_id, person_id, role, work_year, source_id)
building_designation(building_id, authority, designation_type, ref_number,
                     designated_date, removed_date, contributing_flag, source_id)
building_event      (building_id, event_type, event_date, date_precision, description, source_id)
                     -- event_type: completed, opened, altered, fire, moved, condemned,
                     --             wrecking_permit_issued, demolished, rebuilt
building_media      (building_id, media_type, url, rights, date_taken, source_id)
firm                (id, name, founded, dissolved, successor_firm_id, wikidata_qid)
source              (id, name, url, source_type, publisher, accessed_at, license, reliability_tier)
assertion           (id, building_id, field_name, value, source_id, source_locator,
                     confidence, extracted_at, superseded_by)
```

`building_event` is worth calling out: modeling dates as **events with precision and provenance** rather than as bare integer columns on the building row is what lets you represent "demolished sometime between the 1938 and 1950 Sanborn surveys" honestly, which is the actual state of knowledge for a large fraction of Chicago's lost building stock.

---

## Appendix: quick-reference endpoint list

```
# Chicago Data Portal (Socrata)
https://data.cityofchicago.org/resource/ydr8-5enu.json        # Building Permits (incl. demolition)
https://data.cityofchicago.org/resource/qhb4-qx8k.json        # Asbestos/Demolition Notifications
https://data.cityofchicago.org/resource/uct4-hrvh.json        # Individual Landmarks
https://data.cityofchicago.org/resource/zidz-sdfj.json        # Landmark Districts
https://data.cityofchicago.org/resource/yw5d-szpx.json        # NRHP in Chicago
https://data.cityofchicago.org/resource/syp8-uezg.geojson     # Building Footprints
https://data.cityofchicago.org/resource/22u3-xenr.json        # Building Violations
https://data.cityofchicago.org/resource/xq83-jr8c.json        # Energy Benchmarking
https://data.cityofchicago.org/api/views/{4x4}.json           # metadata + true API field names
https://data.cityofchicago.org/api/views/{4x4}/rows.csv?accessType=DOWNLOAD

# Cook County (API works even though HTML browse is robots-blocked)
https://datacatalog.cookcountyil.gov/resource/x54s-btds.json  # year built (char_yrblt)
https://datacatalog.cookcountyil.gov/resource/nj4t-kc8j.json  # Parcel Universe (lat/long)
https://datacatalog.cookcountyil.gov/resource/3723-97qp.json  # Parcel Addresses
https://datacatalog.cookcountyil.gov/resource/78yw-iddh.json  # Cook County Address Points

# Socrata cross-portal discovery
https://api.us.socrata.com/api/catalog/v1?domains={portal}&q={term}&limit=20

# Library of Congress (JSON on any collection URL via &fo=json)
https://www.loc.gov/collections/historic-american-buildings-landscapes-and-engineering-records/?q=Chicago&fo=json
https://www.loc.gov/collections/sanborn-maps/?q=Chicago&fa=location:illinois&fo=json
https://www.loc.gov/item/{id}/?fo=json

# NPS
https://www.nps.gov/subjects/nationalregister/data-downloads.htm
https://npgallery.nps.gov/NRHP/

# Internet Archive
https://archive.org/advancedsearch.php?q={query}&fl[]=identifier&fl[]=title&fl[]=year&rows=100&output=json
https://archive.org/download/{identifier}/{identifier}_djvu.txt

# Wikidata / OSM
https://query.wikidata.org/sparql?format=json&query={urlencoded}
https://overpass-api.de/api/interpreter   (POST, data={query})

# Chicago Landmarks (scrape)
https://webapps1.chicago.gov/landmarksweb/web/landmarkdetails.htm?lanId={id}&counter=1
https://webapps1.chicago.gov/landmarksweb/web/districtdetails.htm?disId={id}
```
