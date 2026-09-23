# Terrain, elevation and hydrology of the Chicago town site, summer 1835

> **Research dossier — committed verbatim as a citable input.**
> Produced by a research agent on 2026-08-09 for the 4D Chicago project.
> Claims carry their own confidence tags and sources; nothing here is authoritative
> until promoted into `data/` with a resolving `source_id`. Where a source could not
> be retrieved, the gap is stated rather than filled.

---

# The Natural Landscape of Downtown Chicago, Summer 1835
### A source-anchored briefing for 3D terrain reconstruction

**Scope:** Chicago River main stem + forks, from the lake shore west to about Halsted, north to Chicago Ave, south to about Van Buren/Madison. Corporate limits at the time (Town of Chicago, extended 11 Feb 1835) ran to the lakeshore east of State St, from Chicago Ave to 12th St ([chicagology, *Wolf's Point and the Town of Chicago*](https://chicagology.com/prefire/prefire273/)).

**Critical caveat up front:** *No contour survey of the 1835 town site exists.* The earliest systematic levels are the 1850s street-grade and Chesbrough sewerage surveys, and the earliest published surficial-geology reconstruction is Alden's 1902 USGS Chicago Folio. Every elevation below is either (a) a period narrative statement in feet, (b) back-calculated from grade-raising records, or (c) inferred from geology. Tags in the final section reflect this.

---

## 1. Ground elevation and datum

### 1.1 Chicago City Datum (CCD)
- **CCD 0.00 = 579.88 ft above mean tide, New York**, established as the **low-water mark of Lake Michigan at Chicago in 1847**. All City benchmarks are referenced to it.
  - [City of Chicago, Elevation Benchmarks dataset](https://data.cityofchicago.org/Buildings/Elevation-Benchmarks/zgvr-7yfd) · [chicago.gov Elevation Benchmarks](https://www.chicago.gov/city/en/depts/water/dataset/elevation_benchmarks.html) · [HMdb "Number One City Datum" marker](https://www.hmdb.org/m.asp?m=248526)
- Worked example: the Northern Trust benchmark = **597.52 ft ASL = 17.64 ft CCD** ([Chicago Public Library, *The Elevation of Chicago: A Statistical Mystery*](https://www.chipublib.org/blogs/post/the-elevation-of-chicago-a-statistical-mystery/)).
- **Datum-conversion warning for the model:** CPL's own worked conversion states that a lake stage of 580.0 ft IGLD85 ≈ 580.5 ft NAVD88 ≈ **1.3 ft CCD** — which implies CCD 0 ≈ 579.2 ft NAVD88, *not* 579.88. The 579.88 figure is on the obsolete "mean tide New York" datum. **Do not mix the two.** For a heightmap, pick one internal datum (recommend: *feet above the 1835 lake surface*) and convert once at export.

### 1.2 Lake level
- Modern Lake Michigan surface: **~578.5 ft ASL** typical, historic range **576–582 ft ASL** (CPL, above). Britannica gives the Chicago plain as **579–600 ft ASL** ([Britannica, *Chicago: Landscape*](https://www.britannica.com/place/Chicago/Landscape)).
- **1835 stage is not directly recorded.** The mid-1830s fall within a high-water phase. Treat the 1835 lake surface as **580 ± 1.5 ft ASL** — *conjectural*.

### 1.3 Original ground relative to the lake — the key numbers
The single most usable pair of figures found:

> "the elevation of the original topography **east of State Street lay from nine to ten feet above the surface of the lake**, whereas to the **west of State Street, it sloped down to the river in a level plain elevated only two to three feet above the river**"
> — [Chicago Architecture History, §1.15 *Improving the Mouth of the River*](https://chicagoarchitecturehistory.com/2022/02/09/1-15-improving-the-mouth-of-the-river/)

That is the crux of the whole terrain: **a low sandy ridge belt along the lake (~+9 to +10 ft), dropping west of State Street onto a near-dead-flat wet plain only ~+2 to +3 ft above river/lake.**

Corroborating statements:
- Riverbanks at Fort Dearborn (Lt. James Strode Swearingen, 1803): **8 ft high on the south side, 6 ft on the north** ([Wikipedia, *Chicago River*, note 54](https://en.wikipedia.org/wiki/Chicago_River)).
- "The level of Lake Michigan was only **two feet below the river banks**" ([chicagoriverstories, *Chicago's Monumental Sewer System*](https://chicagoriverstories.wordpress.com/2016/04/10/chicagos-monumental-sewer-system/)).
- "the elevation of the Chicago area was only a little higher than the shoreline of Lake Michigan"; drainage inadequate, standing water citywide ([Wikipedia, *Raising of Chicago*](https://en.wikipedia.org/wiki/Raising_of_Chicago)).
- "Much of the site remained swampy, **only a few feet above the lake level**, before the central part of the city was filled in" (Britannica, above).

### 1.4 Why the city was later raised (back-calculating original grade)
- Early streets were "simply thrown up as country roads"; the Common Council eventually established grades **"two to six or eight feet above the natural level of the soil"** ([chicagology, *Early Chicago Streets*](https://chicagology.com/prefire/prefire233/)).
- Lake Street was first *lowered* nearly to water level and planked so sewage would run in the gutters — "the stench at once became intolerable" — then filled back in (same source). This is direct evidence the natural surface was within ~1–2 ft of standing water.
- By 1857 the (already partly raised) **grade of Lake Street was "about ten feet above low water,"** with a proposed new grade of **13–14 ft above low water** ([chicagology, *1855—Raising Chicago*](https://chicagology.com/prefire/prefire165/)).
- Chesbrough's Dec 31 1855 sewerage plan set the crown of the South Division at **State & Madison at 14 ft above datum**, streets falling toward the river at **6 in per block**; sewers laid *above* the old ground and buried under new fill ([chicagology 1855—Raising Chicago](https://chicagology.com/prefire/prefire165/); [Encyclopedia of Chicago, *Street Grades, Raising*](http://www.encyclopedia.chicagohistory.org/pages/1202.html)).
- 1855–56 ordinances raised grades **4 to 14 ft**; individual documented lifts: Tremont House 6 ft (1861), Lake St row 4 ft 8 in (1860), Newhall block 7 ft (1858), Briggs House 4 ft 2 in (1866) ([chicagology 1855—Raising Chicago](https://chicagology.com/prefire/prefire165/); [Wikipedia, *Raising of Chicago*](https://en.wikipedia.org/wiki/Raising_of_Chicago); [Gapers Block, *How Chicago Raised Itself Out of the Mud*](http://www.gapersblock.com/airbags/archives/city_streets_how_chicago_raised_itself_out_of_the_mud_and_astonished_the_world/)).

**Back-calculation:** modern Loop street grade ≈ 14 ft CCD; documented raises of 4–8 ft in the core → **original South Division surface ≈ 4–8 ft CCD ≈ 584–588 ft ASL**, consistent with the "+2 to +3 above the river" / "+9 to +10 near the lake" pair.

### 1.5 Soils
- Original profile, business district: **1 ft black loam → 3–4 ft "quicksand" (saturated fine silty sand) → 8–12 ft impervious blue clay** ([Chicago Architecture History §1.15](https://chicagoarchitecturehistory.com/2022/02/09/1-15-improving-the-mouth-of-the-river/)).
- The blue clay (Wadsworth Fm, "Chicago Blue Clay") can exceed 50 ft; underlain by Chicago Hardpan (Haeger Mbr, Lemont Fm), then Silurian dolomite bedrock at ~60–110 ft ([AEG, *Chicago Geology*](https://www.aegannualmeeting.org/chicago-geology-map); [Informed Infrastructure, *Building Skyscrapers on Chicago's Swampy Soil*](https://informedinfrastructure.com/post/building-skyscrapers-on-chicagos-swampy-soil)).
- Stratigraphic units mappable at the surface in 1835: **Equality Fm** (lacustrine silt/clay — the wet-prairie plain), **Henry Fm** littoral sand (beach ridges, spit, dunes), **Grayslake Peat** (sloughs, ponds, swales), **Cahokia alluvium** (river margins). The impervious clay just below the loam is *why* the site could not drain.

---

## 2. Micro-topography

### 2.1 High ground
- **Fort Dearborn mound** (south bank, at the river's bend — modern Michigan Ave & Wacker Dr): the fort "stood upon a **flattened mound**, formed by the curve of the river at its base on its three sides," buildings on the apex; it "was **as high as any other point**, overlooking the surface of the lake, commanding the prairie extending to the south, the belt of timber along the South Branch and on the North Side, and **the white sand hills both to the north and south**" ([chicagology, *Fort Dearborn I*](https://chicagology.com/prefire/prefire274/); [drloihjournal, *Complete History of the First and Second Fort Dearborn*](https://drloihjournal.blogspot.com/2018/06/history-of-the-first-and-second-fort-dearborn-in-Chicago.html)). Modern site elevation cited as **591 ft ASL** ([Wikipedia, *Fort Dearborn*](https://en.wikipedia.org/wiki/Fort_Dearborn)).
- **The lakeshore sand-ridge / spit belt.** On the left (south/east) bank of the deflected river channel: "a **long low strip of land, a sandy beach and drifting sand bars**" forming "the **barrier or dividing ridge**" between lake and river, running south **nearly half a mile** toward present Michigan Avenue ([chicagology, *Fort Dearborn I*](https://chicagology.com/prefire/prefire274/)).
- **"White sand hills both to the north and south"** of the fort — the only explicit dune reference (same source). The 1839 Fort Dearborn Addition plat shows Michigan Ave 66 ft wide with only 73 ft of land beyond it; "at best the area was probably a **low sandbar**" ([CPL, *History of Grant Park, 1830–1871*](https://www.chipublib.org/blogs/post/history-of-grant-park-1830-1871/)).
- **Regional context:** downtown sits on the Chicago Lake Plain — the floor of ancestral Lake Chicago. The nearest genuine relief is the relict Toleston beach (**18–25 ft above Lake Michigan**), the Graceland/Rose Hill spits (**600–610 ft ASL**, ~4 mi north), Calumet beach (~+35 ft), Glenwood beach (~640 ft ASL) — *all outside downtown*. ([Toleston Shoreline](https://en.wikipedia.org/wiki/Toleston_Shoreline); [Robert Loerzel, *Topography, Tombs, and Tolls*](https://www.robertloerzel.com/2023/04/06/topography-tombs-and-tolls/); [INHS, *Chicago Lake Plain*](https://beaches.inhs.illinois.edu/chicago-lake-plain/))
- The **continental divide** at the Chicago Portage was "often **less than 15 feet above the level of Lake Michigan**" — in flood the watersheds merged ([Wikipedia, *Chicago Portage*](https://en.wikipedia.org/wiki/Chicago_Portage)). Downtown had *no* watershed edge at all.

### 2.2 Low/wet ground, sloughs, ponds
- **South Division:** "generally **low and marshy ground**," with "a strip along the river shore that was **still more marshy, where land and water mingled, covered with tall grass, reeds and rushes**" ([chicagology, *Wolf's Point and the Town of Chicago*](https://chicagology.com/prefire/prefire273/)).
- **The public-square pond** (block bounded by Randolph/Washington/Clark/LaSalle — later Court House / City Hall): "was then a **pond** where Indians had trapped muskrat and settlers hunted ducks" (same source).
- **The slough** (the principal natural drain of the South Division): "a little stream they called a '**slough**,' which drained the pond and **the marsh extending up Wells Street**, and in a winding course **passed over the site of the Tremont House** [NW corner Lake & Dearborn] **and entered the river at the end of State Street**." Where Water Street crossed it, a **log bridge** was needed until after 1840 (same source). *Note: the user's "slough at State/Lake" is approximately right — the slough's mouth was at the foot of State St, and its course passed Lake & Dearborn.*
- **"Frog Pond"** at **Lake Street & LaSalle**: still standing water as late as **9 July 1836**, "inhabited by frogs… smells strong now, and in a few days will send out a horrible stench" ([chicagology, *Early Chicago Streets*](https://chicagology.com/prefire/prefire233/)).
- **Drainage:** plank sluices later built across Clark Street to carry drainage to the South Branch (same source) — indicating the natural surface flow was westward/southwestward off the State St ridge to the river.
- **Vegetation zoning at the forks:** West Side = "an **open prairie, entirely free from timber**"; South Side = "a body of **timber grew along the river, extending east as far as Wells street**"; North Side = "a body of **thrifty heavy growth of timber**"; along the river banks, sedgy grass and abundant wild onions ([chicagology, *Wolf's Point*](https://chicagology.com/prefire/prefire273/)).
- Streets "impassable" for weeks each spring; empty wagons and drays mired on Lake and Water Streets ([chicagology, *Early Chicago Streets*](https://chicagology.com/prefire/prefire233/)).

---

## 3. The Chicago River in 1835

### 3.1 Natural channel geometry
- At Fort Dearborn (Swearingen, 1803): **~30 yards (≈90 ft) wide, "upwards of 18 feet" deep**; banks 8 ft (S) / 6 ft (N) ([Wikipedia, *Chicago River*](https://en.wikipedia.org/wiki/Chicago_River)).
- Natural average depth of the river commonly given as **~12 ft** (secondary synthesis — treat as approximate).
- Flow: **sluggish, outward into Lake Michigan** — pre-reversal, pre-1900. Near-zero surface gradient; water surface effectively at lake level throughout the downtown reach ([Wikipedia, *Chicago River*](https://en.wikipedia.org/wiki/Chicago_River); [WTTW, *History of the Chicago River*](https://www.wttw.com/chicago-river-tour/history-chicago-river)).
- Early log bridges were ~10 ft wide and cleared the river by ~6 ft — a useful proxy for bank freeboard.

### 3.2 The sandbar and the natural mouth
- A **baymouth bar** built by south-flowing littoral drift deflected the river **southward, parallel to the shore, "for nearly half a mile"** before it "lost itself in the lake"; the deflection is elsewhere described as **"the equivalent of five city blocks."** The natural outlet was at **about present-day Madison Street & Michigan Avenue**.
  - [Wikipedia, *Chicago River*](https://en.wikipedia.org/wiki/Chicago_River) · [chicagology, *Fort Dearborn I*](https://chicagology.com/prefire/prefire274/) · [Chicago Architecture History §1.15](https://chicagoarchitecturehistory.com/2022/02/09/1-15-improving-the-mouth-of-the-river/)
- The bar admitted "only… boats… to pass over" — lake vessels anchored **half a mile offshore** and lightered cargo (§1.15). The schooner *Tracy* (1803) had to anchor half a mile out for the same reason ([drloihjournal](https://drloihjournal.blogspot.com/2018/06/history-of-the-first-and-second-fort-dearborn-in-Chicago.html)).
- Soldiers from Fort Dearborn cut ditches through the bar repeatedly **between 1816 and 1828**; each closed again ([Bridgehouse Museum, *Boomtown*](https://www.bridgehousemuseum.org/museum-exhibits-2); [WTTW](https://www.wttw.com/chicago-river-tour/history-chicago-river)).
- Prior engineering proposals: **Maj. Stephen H. Long, 1816** (two piers, then cut the bar); **William Howard, USACE, 1830** (close the old outlet, cut a direct channel northeast/east to the lake, pier the new outlet) (§1.15).

### 3.3 The 1833 cut and harbor works — status in summer 1835
| Date | Event | Figures |
|---|---|---|
| 2 Mar 1833 | Congress appropriates **$25,000** for Chicago harbor | — |
| Jun 1833 | Work begins under **Maj. George Bender**, Fort Dearborn commandant | — |
| Jan 1834 | **Lt. James Allen** takes over supervision | — |
| Feb 1834 | Storm **breaches the bar**, scouring the new cut | — |
| 12 Jul 1834 | Schooner ***Illinois*** (100 tons) enters and reaches **Wolf Point**, docking at Newberry & Dole | first vessel through |
| 1834 (as built) | **Entrance cut 200 ft wide, 3–7 ft deep**; **south pier 200 ft**, **north pier 700 ft** | — |
| 1835 | Piers and lighthouse further built out; Chicago is the leading port in the West | — |
| Oct 1837 | Piers extended to **1,850 ft (N)** and **1,200 ft (S)** | — |

Sources: [Wikipedia, *Chicago River*, notes 55, 57–59](https://en.wikipedia.org/wiki/Chicago_River); [Encyclopedia of Chicago, *Chicago River as Harbor*](http://www.encyclopedia.chicagohistory.org/pages/300043.html); [Chicago Architecture History §1.15](https://chicagoarchitecturehistory.com/2022/02/09/1-15-improving-the-mouth-of-the-river/); [Illinois SOS, *Communication Regarding the Chicago Harbor*](https://www.ilsos.gov/departments/archives/teaching-packages/early-chicago/doc16.html).

**For summer 1835 specifically:** the cut was open and working but shoaling was chronic; the **north pier length was between 700 ft (1834) and 1,850 ft (Oct 1837)** — no 1835 figure was found here. Interpolate **~1,000–1,300 ft**, flagged *inferred*. **⚠ CORRECTED 2026-09-12 (T-1065): that band is a YEAR-END 1835 figure, not a summer one, and reading it at the scene date is a mistake this page caused twice.** The two endpoints above are 1,019 days and 1,150 ft apart — 1.13 ft a day — and 1 July 1835 is 182 days along, which is **905 ft**, not 1,000–1,300. The band is what the same line reaches at the END of 1835 (1,112 ft) and it is where dossier 04's figure lands too. **Dossier 04 § 3 has since found the intermediate this page lacked** — Andreas: the north pier 'had been extended to 1,260 ft into the lake, to 12 ft of water' by the close of the 1835 season — and, season-weighted, reaches ~800–1,000 ft for midsummer. `data/structures/north_pier.json` records **900 ft / 274.32 m** for the scene, and all three readings agree on it once this one is read at the right date. Use 04 § 3 for any scene-date length; use this band only for the year's end. The **old southward channel** behind the sand tongue was being abandoned but was still a mapped feature for decades: S. S. Greely's 1854–58 charts still show "the former position of Fort Dearborn, **the ancient river bed, the sandbar at its mouth**" ([chicagology, *Fort Dearborn I*](https://chicagology.com/prefire/prefire274/)). Alden's 1902 USGS folio maps the **"sand bar in 1830–1833"** ([Whose Lakefront, *Lakefill*](https://www.whoselakefront.com/lakefill)).

---

## 4. Shoreline position, 1835 vs today

- **The original (pre-fill) Lake Michigan shoreline ran approximately along modern Michigan Avenue.** ([CPL, *History of Grant Park 1830–1871*](https://www.chipublib.org/blogs/post/history-of-grant-park-1830-1871/); [Whose Lakefront, *Lakefill*](https://www.whoselakefront.com/lakefill), using Dennis McClendon's shoreline map, 1821–1864 positions.)
- The **1836 Illinois & Michigan Canal Commissioners map** shows the lakeshore **~400 ft east of Michigan Avenue** — CPL notes it is "not entirely clear if, or how, 400 feet of the lake got filled," i.e. it may be either genuine post-pier accretion or a speculative paper beach. By the **1850s the shore had eroded back to within ~50 ft of Michigan Avenue**, waves lapping at lakefront mansions; the Illinois Central's 1852 trestle then fixed the line.
- **Littoral mechanics (essential for the model):** net drift is southward. Once the piers were built, **sand accreted on the north side and eroded on the south.** The accretion north of the north pier eventually became **Streeterville**. Erosion south of the cut was severe enough to wash out the old Fort Dearborn burying ground, "exposing coffins and their contents."
  - [CPL Grant Park](https://www.chipublib.org/blogs/post/history-of-grant-park-1830-1871/) · [Whose Lakefront](https://www.whoselakefront.com/lakefill) · [drloihjournal](https://drloihjournal.blogspot.com/2018/06/history-of-the-first-and-second-fort-dearborn-in-Chicago.html) · [Encyclopedia of Chicago, *Shoreline Erosion*](http://www.encyclopedia.chicagohistory.org/pages/1142.html)
- **In summer 1835 the model should show accretion only just beginning** north of the ~1-year-old pier — a widening beach wedge, not yet the Streeterville landmass.
- 1839 Fort Dearborn Addition plat: Michigan Ave 66 ft wide, **73 ft of land east of it** to the water — a useful hard constraint on the 1830s beach width.

---

## 5. Wolf Point and the forks

- Wolf Point = the **point of land at the junction of the North and South Branches, "looking directly down the main channel"**; originally the term applied to the **west bank** at the fork ([chicagology, *Wolf's Point and the Town of Chicago*](https://chicagology.com/prefire/prefire273/); [Wikipedia, *Wolf Point, Chicago*](https://en.wikipedia.org/wiki/Wolf_Point,_Chicago)).
- **Bank heights at the forks are not directly documented.** The only measured banks are Swearingen's **8 ft (south) / 6 ft (north)** near the fort, ~1.2 mi downstream. The "west of State Street… only two to three feet above the river" statement applies to the plain that includes the forks. **Reconcile as: a low bank of ~2–4 ft at the point itself**, rising slightly on the timbered north side.
- Marshiness: the forks area is repeatedly described as marshy — "farms and homesteads peppering the **marshy forks of the North Branch**"; the branches' upper forks "called **sloughs**, were marshy, wet areas with little current" ([Bridgehouse Museum](https://www.bridgehousemuseum.org/museum-exhibits-2); [TCLF, *Chicago's Landscape Legacy*](https://www.tclf.org/places/view-cultural-landscape-guides/chicago/chicagos-landscape-legacy)).
- The 1830 Thompson plat area shows **three sloughs off the Main Branch** and a "bayou" near Wolf Point ([Chicago Architecture History §1.16, *Platting the Town of Chicago*](https://chicagoarchitecturehistory.com/2022/02/11/1-16-platting-the-town-of-chicago-in-the-prairie-wilderness/)).
- Contemporary visual: the 1867 Blanchard/Shober chromolithograph **"Wolf's Point in 1833"** — a retrospective view but the standard iconographic reference for bank profile and vegetation ([Geographicus](https://www.geographicus.com/P/AntiqueMap/wolfspointchicago-blanchard-1867); [chicagology, *The Chicago River Near Wolf Point, 1833*](https://chicagology.com/goldenage/goldenage105/earle/earle4/)).

---

## 6. Citable reconstructions, maps, and datasets

**Primary maps / surveys**
| Source | Date | What it shows |
|---|---|---|
| **James Thompson plat of the Town of Chicago** | 1830 | Original 0.375 sq mi plat, 80-ft streets, river mouth, sloughs; east boundary at State St ([Encyclopedia of Chicago](http://www.encyclopedia.chicagohistory.org/pages/11175.html); [chicagology, *Early Street Maps*](https://chicagology.com/prefire/prefire275/); [Illinois SOS](https://www.ilsos.gov/departments/archives/online-exhibits/100-documents/1833-land-plat-chicago.html)) |
| **John H. Kinzie map** | 1833 | Town + school reservations, Fort Dearborn intact ([chicagology prefire275](https://chicagology.com/prefire/prefire275/)) |
| **J. S. Wright, "Chicago… According to Survey"** | 1834 | Standard 1834 town survey ([Encyclopedia of Chicago](http://www.encyclopedia.chicagohistory.org/pages/10349.html); [Allan Berry digital copy](https://allanberry.omeka.net/items/show/4)) |
| **"Map of Chicago, 1835"** | 1835 | 1835 additions south of Kinzie St ([Encyclopedia of Chicago](http://www.encyclopedia.chicagohistory.org/pages/3298.html)) |
| **Illinois & Michigan Canal Commissioners map** | 1836 | Shore ~400 ft east of Michigan Ave; piers at river mouth ([CPL Grant Park](https://www.chipublib.org/blogs/post/history-of-grant-park-1830-1871/)) |
| **U.S. Surveyor General township plat** | 1821 | GLO land-cover: swampy prairie, swamp, marshy ground ([Loerzel](https://www.robertloerzel.com/2023/04/06/topography-tombs-and-tolls/)) |
| **S. S. Greely charts** | 1854–58 | Former Fort Dearborn position, **ancient river bed**, sandbar at its mouth ([chicagology, *Fort Dearborn I*](https://chicagology.com/prefire/prefire274/)) |
| **J. D. Graham, "Chicago Harbor & Bar, Illinois"** | Apr 1857; Aug–Sep 1858 | US Topographical Engineers hydrographic surveys of the bar ([UM Clark Library](https://quod.lib.umich.edu/c/clark1ic/x-001291870/39015091899396_02); [Ruderman](https://www.raremaps.com/gallery/detail/53333)) |
| **A. F. Scharf, map of 1804 Indian trails** | pub. 1900 | Trails following ridges and sand beaches ([Loerzel](https://www.robertloerzel.com/2023/04/06/topography-tombs-and-tolls/)) |

**Geologic / topographic reconstructions**
- **Alden, W. C., 1902, *Geologic Atlas of the United States, Chicago Folio No. 81*** (Riverside, Chicago, Desplaines, Calumet quadrangles), USGS, 1:62,500, 10-ft contours, 15 pp. text + 12 maps. Includes the **"sand bar in 1830–1833"** and old river bed. [USGS GF-81](https://pubs.usgs.gov/publication/gf81) · [NGMDB](https://ngmdb.usgs.gov/Prodesc/proddesc_2488.htm) · transcribed topography text at [ebeltz.net/folio/cfol-1.html](http://ebeltz.net/folio/cfol-1.html) *(503 at time of research)*
- **Bretz, J H, 1939 & 1955, *Geology of the Chicago Region*, ISGS Bulletin 65, Parts I & II.** Part II contains 24 surficial-geology maps at 1:24,000, including **Map 08 — Chicago Loop Quadrangle**. [ISGS Bulletin 65](https://resources.isgs.illinois.edu/publications/b065) · [Chicago Loop Quad map page](http://resources.isgs.illinois.edu/maps/surficial-geology-chicago-region-chicago-loop-quadrangle) · [Bulletin 65 Pt. II PDF](https://library.isgs.illinois.edu/Pubs/pdfs/bulletins/bul065pt2.pdf)
- **ISGS surficial-geology quadrangle series & Illinois Landcover in the Early 1800s** (digitized GLO plat land-cover, 42 categories) — [ISGS Clearinghouse](https://clearinghouse.isgs.illinois.edu/data/landcover/illinois-landcover-early-1800s)
- **AEG 2026 Chicago Geology map** — modern subsurface stratigraphy of the Loop (Chicago Hardpan / Blue Clay / Lake Chicago sands / anthropogenic fill): [aegannualmeeting.org/chicago-geology-map](https://www.aegannualmeeting.org/chicago-geology-map)

**Narrative / secondary**
- A. T. Andreas, ***History of Chicago***, vol. 1 (1884): [archive.org/details/historyofchicago01andr](https://archive.org/details/historyofchicago01andr) (also `historyofchicago01inandr`, 1,340 pp.). Widely excerpted on chicagology.
- Libby Hill, ***The Chicago River: A Natural and Unnatural History*** (2000; SIU Press eds. 2019) — the standard hydrologic history. [Google Books](https://books.google.com/books/about/The_Chicago_River.html?id=GOeLDwAAQBAJ)
- **chicagology.com**: [Wolf's Point and the Town of Chicago](https://chicagology.com/prefire/prefire273/) · [Fort Dearborn I](https://chicagology.com/prefire/prefire274/) · [Early Chicago Streets](https://chicagology.com/prefire/prefire233/) · [Early Street Maps of Chicago](https://chicagology.com/prefire/prefire275/) · [1855—Raising Chicago](https://chicagology.com/prefire/prefire165/)
- **Encyclopedia of Chicago** (encyclopedia.chicagohistory.org): [Chicago River as Harbor](http://www.encyclopedia.chicagohistory.org/pages/300043.html) · [Street Grades, Raising](http://www.encyclopedia.chicagohistory.org/pages/1202.html) · [Shoreline Erosion](http://www.encyclopedia.chicagohistory.org/pages/1142.html) · [Early Lakeshore Development](http://www.encyclopedia.chicagohistory.org/pages/300062.html) · [Fort Dearborn](http://www.encyclopedia.chicagohistory.org/pages/477.html) · [Infrastructure](http://www.encyclopedia.chicagohistory.org/pages/641.html). ⚠️ **The entire encyclopedia.chicagohistory.org host returned HTTP 503 throughout this research session** — content above attributed to it comes from search-index snippets, not direct retrieval. Verify before locking into a provenance dataset.
- Chicago Architecture History (Ken Schroeder): [§1.15 Improving the Mouth of the River](https://chicagoarchitecturehistory.com/2022/02/09/1-15-improving-the-mouth-of-the-river/) · [§1.16 Platting the Town of Chicago](https://chicagoarchitecturehistory.com/2022/02/11/1-16-platting-the-town-of-chicago-in-the-prairie-wilderness/) — **source of the best two elevation figures in this report.**
- [City of Chicago, Shoreline History](https://www.chicago.gov/city/en/depts/cdot/supp_info/shoreline_history.html) *(403 to automated fetch; open in browser)*
- [Whose Lakefront — Lakefill](https://www.whoselakefront.com/lakefill) (Dennis McClendon shoreline map) · [CPL, History of Grant Park 1830–1871](https://www.chipublib.org/blogs/post/history-of-grant-park-1830-1871/)

---

# TERRAIN MODEL RECOMMENDATIONS

**Internal datum:** define **Z = 0.0 ft at the summer-1835 lake/river water surface**. Export offset: `ASL = Z + 580.0` (or `CCD = Z + 0.1` if using 579.88; see §1.1 datum warning). Total natural relief across the entire modeled area is **under 15 ft** — apply 4–8× vertical exaggeration for legibility, and quantize the heightmap at **≤0.25 ft** or the whole site will render as a plane. Recommended horizontal cell size **5–10 ft**.

| # | Zone | Extent | Z (ft above lake) | ASL @ lake=580 | Tag |
|---|---|---|---|---|---|
| 1 | **Lake / river water surface** | everywhere wet | 0.00 (flat; treat river gradient as 0) | 580.0 | documented (flow sluggish, outward) |
| 2 | **1835 lake stage itself** | — | — | 580.0 ± 1.5 | **conjectural** |
| 3 | **Lakeshore sand-ridge belt** (≈ Michigan Ave line, Chicago Ave → 12th St) | 150–400 ft wide | **+9.0 to +10.0** crest | 589–590 | **documented** (§1.15) |
| 4 | **Beach face** seaward of ridge crest | 60–100 ft wide | +9 → 0, slope ≈ 1:10 | 589 → 580 | inferred |
| 5 | **Dune hummocks** ("white sand hills" N and S of fort) | scattered, 50–150 ft across | +10 to +14 local peaks | 590–594 | inferred (documented existence, no heights) |
| 6 | **Fort Dearborn mound** (Michigan Ave & Wacker, S bank) | ~300 × 300 ft, flat-topped | **+10 to +12**, apex +12 | 590–592 | inferred (documented as "flattened mound," "as high as any other point"; 591 ASL modern) |
| 7 | **Sand tongue / spit** between old river channel and lake, fort → Madison St | length **~2,600 ft** (½ mi), width 100–300 ft | **+4 to +8** crest | 584–588 | documented extent; heights inferred |
| 8 | **South Division plain, east of State St** | State→ridge, Kinzie→Madison | +7 to +9, gently falling west | 587–589 | documented (§1.15) |
| 9 | **South Division plain, west of State St** | State→river, Kinzie→Van Buren | **+2 to +3 above river** → +2.0 to +3.5 | 582–583.5 | **documented** (§1.15) |
| 10 | Break-of-slope at **State Street** | a 200–400 ft transition band | drop ~5–6 ft over 300 ft (≈2% grade) | 588 → 583 | inferred from #8/#9 |
| 11 | **River-margin marsh strip** ("land and water mingled," reeds/rushes) | 40–120 ft back from both banks, S side esp. | **+0.5 to +2.0** | 580.5–582 | documented qualitatively |
| 12 | **Natural bank crest, main stem near fort** | S bank / N bank | **+8.0 / +6.0** | 588 / 586 | **documented** (Swearingen 1803) |
| 13 | **Natural bank crest, forks / Wolf Point** | S & W branches | **+2 to +4** | 582–584 | inferred (reconciling #9 with #12) |
| 14 | **The slough** — public square → Tremont House site (Lake & Dearborn) → river at foot of State St | length ~2,400 ft, width 15–40 ft | thalweg **−1.5 to −3.0 below adjacent plain** → +0.5 to +1.5 | 580.5–581.5 | route documented; depth/width **conjectural** |
| 15 | **Public-square pond** (Randolph–Washington, Clark–LaSalle) | ~1 city block, seasonal | bed **+1.0 to +2.0**; water 0.5–2 ft deep in spring | 581–582 | existence documented; geometry conjectural |
| 16 | **"Frog Pond," Lake St @ LaSalle** | ~100–200 ft across | bed +1.5 to +2.5, shallow (<1.5 ft) | 581.5–582.5 | existence documented (Jul 1836); geometry conjectural |
| 17 | **Wells Street marsh** (drained by the slough) | broad, ill-defined | +1.0 to +2.5, saturated | 581–582.5 | documented qualitatively |
| 18 | **West Division wet prairie** (west of South Branch) | treeless, open | **+3 to +6**, with 1–2 ft slough swales | 583–586 | inferred |
| 19 | **North Division** (N of main stem) — timbered, better-drained sandy ground | Kinzie → Chicago Ave | **+4 to +7**, rising to +9 near the lake | 584–589 | inferred |
| 20 | **Main-stem channel bed**, forks → fort | thalweg | **−12 to −18** (deepest pool at the fort bend: −18) | 562–568 | documented (Swearingen 18 ft) / inferred |
| 21 | **South & North Branch beds** | above the forks | **−6 to −10** | 570–574 | inferred |
| 22 | **Channel width, main stem** | fort reach | **~90 ft** (30 yd), widening to 150–200 ft at the forks | — | 90 ft documented; forks width inferred |
| 23 | **1834 cut through the bar** (open in 1835) | E–W, N of fort | **200 ft wide**, bed **−3 to −7** | 573–577 | **documented** |
| 24 | **North pier** (timber crib) | from shore E into lake | length **~900 ft at 1 Jul 1835** (~1,000–1,300 ft is this row's old figure and is a YEAR-END 1835 band — see § 3.3, corrected T-1065); deck ~+4 to +6 | — | length **inferred**; committed on `north_pier.crib_1835.form.length_m`, argued from dossier 04 § 3's end-of-1835 1,260 ft |
| 25 | **South pier** | " | **200 ft** (1834) to a few hundred ft | — | documented (1834) |
| 26 | **Abandoned old channel** (behind the spit, fort → Madison St) | ~2,600 ft long, 80–150 ft wide | water −1 to −4; silting into a lagoon/slough | 576–579 | **conjectural** for 1835 state |
| 27 | **Residual bar shoals** flanking the cut | 200–600 ft offshore | **−1 to −4** (breaking in storms) | 576–579 | inferred |
| 28 | **Fresh accretion wedge, N of north pier** | triangular, ~1 yr of drift | +0 to +3, 100–300 ft wide, tapering N | 580–583 | inferred (mechanism documented) |
| 29 | **Erosional scarp, S of the cut** (Fort Dearborn burying-ground reach) | along shore S of pier | 1–3 ft cut bank | — | documented qualitatively |
| 30 | **Offshore lake bed** | E of shoreline | slope ~1:60 to 1:100; −10 ft at 600–1,000 ft offshore | — | **conjectural** |

### Surface-material / texture layers (for shading & hydrology)
| Material | Where | Tag |
|---|---|---|
| Beach & dune sand (Henry Fm) | zones 3–7, 27, 28 | documented |
| Black loam ~1 ft over "quicksand" 3–4 ft over blue clay 8–12 ft | zones 8, 9, 18, 19 | **documented** (§1.15) |
| Peat/muck (Grayslake Peat) | zones 11, 14–17 | inferred |
| Alluvium/silt (Cahokia) | zones 20–21, 26 | inferred |
| Timber belt: S bank of main stem east to Wells St; whole North Division | zones 8/9 fringe, 19 | documented |
| Treeless open prairie | zone 18 (West Division) | documented |
| Sedge, tall grass, reeds, rushes, wild onion | zone 11 | documented |

### Modeling rules of thumb
1. **Flatness is the story.** Outside zones 3–7 and the fort mound, hold local gradients under **0.5 ft per 300-ft block** (Chesbrough later engineered 6 in/block *artificially*).
2. **Water table at or within ~1 ft of the surface** across zones 9, 11, 14–18. Impervious blue clay at 4–5 ft depth means **no vertical drainage** — ponding is the default state, worst in spring. Model seasonal: summer 1835 = drier than the spring "impassable" condition, but ponds 15 and 16 were still wet in July 1836.
3. **State Street is the drainage divide** of the South Division: east of it, surface water sheds to the lake over the sand ridge; west of it, everything creeps to the river via the slough (zone 14).
4. **The river mouth in summer 1835 is a hybrid**: the artificial east-trending cut (zone 23) is the working channel, the natural southward channel (zone 26) is a decaying backwater behind the spit, and the bar is actively trying to re-form. Do not render either the pre-1833 or the post-1840 configuration.
5. Do **not** place any relief greater than ~+14 ft above lake anywhere inside downtown. The nearest true topographic high ground (Graceland/Rose Hill spits, +20–30 ft) is ~4 miles north and outside the frame.

---

### Verification gaps worth closing before publishing the dataset
- **encyclopedia.chicagohistory.org was 503 for the entire session** — all EOC citations above are snippet-derived and must be re-fetched.
- **chicago.gov CDOT Shoreline History** and **ebeltz.net USGS folio transcription** blocked automated fetch (403/503); retrieve manually.
- **No 1835-specific north-pier length** was found; the 700 ft → 1,850 ft interpolation should be replaced with the figure from the Chief Engineer's annual reports (1835/1836) or House Doc. series if precision matters.
- **No 1835 lake-stage record** was located; check NOAA/GLERL historical Lake Michigan-Huron reconstructions.
- **Wolf Point bank heights** are inferred, not measured. Andreas vol. 1 and Hill's *The Chicago River* are the best places to look for a primary figure.
