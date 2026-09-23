# Cartographic sources, pipeline precedents, and renderer technology

> **Research dossier — committed verbatim as a citable input.**
> Produced by a research agent on 2026-08-09 for the 4D Chicago project.
> Claims carry their own confidence tags and sources; nothing here is authoritative
> until promoted into `data/` with a resolving `source_id`. Where a source could not
> be retrieved, the gap is stated rather than filled.

---

# Chicago 1835 — Source & Pipeline Scoping Report

---

## 1. MAPS — digital access, resolution, rights, georeferencing suitability

### Headline finding
**The best georeferencing master is not the Newberry Hathaway map.** It is the **Boston Public Library / Leventhal copy of J.S. Wright 1834**, because it is open-rights *and already published as a georeferenced GeoTIFF*. The Newberry's Hathaway digital surrogate is a single ~1.9 MB JPEG; the **Library of Congress** holds a 6536 × 9318 px copy of the same Hathaway map that is free to reuse. Plan around LOC + BPL rasters, and use the Newberry only for the Andreas cadastral layer (which *is* excellently digitized there).

---

### 1.1 Joshua Hathaway, *Chicago with the School Section, Wabansia and Kinzie's Addition* (1834)

| | |
|---|---|
| **Newberry holding** | Original at Newberry, VAULT drawer, **Graff 1817**. Catalog permalink: https://i-share-nby.primo.exlibrisgroup.com/permalink/01CARLI_NBY/i5mcb2/alma991577568805867 |
| **Newberry digital surrogate** | **Not in `collections.newberry.org`.** Newberry published it to Internet Archive instead: **https://archive.org/details/nby_157756** (uploader `dis@newberry.org`, 2020-09-04, collections `newberrymisc`/`newberry`, subject tag `DCC`) |
| **Scan resolution (Newberry/IA)** | **One file only** — `Chicago_with_School_Section_map.jpg`, **1,989,572 bytes**. No JP2, no TIFF, no IIIF. ARK `ark:/13960/t6j19788h`. Insufficient for warping |
| **LOC copy (use this)** | **https://www.loc.gov/item/2008621683/** — creator "Hathaway, Joshua, 1810-1863"; call no. `G4104.C6G4 1820 .H2`; *1 map : col., hand col. ; 73 × 51 cm* |
| **LOC resolution** | JP2 **6536 × 9318 px, 9.15 MB** (`https://tile.loc.gov/storage-services/service/gmd/gmd410/g4104/g4104c/ct007620.jp2`); master TIFF **182,730,712 bytes (~174 MB)**; IIIF `info.json`: `https://tile.loc.gov/image-services/iiif/service:gmd:gmd410:g4104:g4104c:ct007620/info.json` |
| **LOC rights** | *"The content of the Library of Congress Geography and Map Division digitized collections is free to use and reuse unless a Rights Advisory statement is present."* No advisory present. Credit line: Library of Congress, Geography and Map Division |
| **⚠ Cataloging trap** | LOC dates this **"[1820?]"** and the call number encodes 1820. This is a **cataloging error** — Hathaway was born 1810. Title, dimensions and content match the 1834 map. Record this discrepancy in your provenance sidecar rather than silently "correcting" it |
| **Other copies** | MIT DOME: https://dome.mit.edu/handle/1721.3/15641 · Encyclopedia of Chicago (flaky, 503s): http://www.encyclopedia.chicagohistory.org/pages/10634.html |
| **What it shows** | The 1834 real-estate state of the town: original plat **plus** the School Section (Sec. 16), **Wabansia**, and **Kinzie's Addition** — i.e. the five parcels that roughly doubled the platted area. This is the correct extent envelope for a **1835** model |
| **Suitability** | **Primary georeferencing raster for the full 1835 extent.** Use the LOC JP2/IIIF, not the Newberry JPEG. Warp against surviving section-line geometry (the PLSS grid is still legible in modern Chicago streets), not against buildings |

### 1.2 J.S. Wright, *Chicago, drawn by J.S. Wright according to survey* (1834) — **best master-geometry source**

| | |
|---|---|
| **URL** | **https://collections.leventhalmap.org/search/commonwealth:js9577436** · ARK: https://ark.digitalcommonwealth.org/ark:/50959/js9577436 · IIIF manifest: https://www.digitalcommonwealth.org/search/commonwealth:js9577436/manifest |
| **Record** | Manuscript map in ink and watercolour, **46 × 37 cm**, **scale ≈ 1:7,200**, publisher *New York : P.A. Mesier's Lith. 28 Wall St.*; identifier `06_01_016718`; **"Colored to indicate date surveyed"** |
| **Rights** | **"No known copyright restrictions. No known restrictions on use."** |
| **Downloads** | Primary uncompressed **TIF 62.2 MB**; full-res **JPEG 5.22 MB**; medium JPEG 213 KB; **GeoTIFF (georeferenced) TIF 69.4 MB** — plus live **Allmaps** georeferencing on the item page |
| **Other copies** | Newberry (Graff 4755), surfaced via paywalled Adam Matthew *American West*: https://www.americanwest.amdigital.co.uk/Documents/Details/Chicago--drawn-by-J--S--Wright-according-to-survey/Graff_4755 · UWM AGDM: https://collections.lib.uwm.edu/digital/collection/agdm/id/5958/ · chicagology scan: https://chicagology.com/wp-content/themes/revolution-20/PreFire2/1834chicagowright.jpg · Encyclopedia of Chicago: http://www.encyclopedia.chicagohistory.org/pages/10349.html |
| **What it shows** | The grid, the **cut through the sandbar** giving the river direct lake access, Fort Dearborn south/west of the cut, Kinzie's North Side property, the Public Square, South Water Street. Drawn to help J.H. Kinzie sell lots; the Newberry copy was evidence in *Bates v. Illinois Central* |
| **Suitability** | **Use as master geometry.** Open rights + existing GeoTIFF + a genuine survey at 1:7,200 with block/lot lines and survey-date colouring. Wright gives you the street centrelines and lot subdivision; Hathaway gives you the outer extent. Georeference Wright first, then rubber-sheet Hathaway to it |

### 1.3 James Thompson, canal-commissioners plat (1830)

| | |
|---|---|
| **Status** | **The original burned in the 1871 fire.** What survives is a Canal Commissioners' working copy (dated to at least 1836). Chicago History Museum holds **ICHi-34284** |
| **Accessible scans** | Wikimedia Commons (PD): https://commons.wikimedia.org/wiki/File:Thompson_plat_of_Chicago_1830.png and https://commons.wikimedia.org/wiki/File:Thompson_Chicago_plat_1830.jpg · chicagology: https://chicagology.com/wp-content/themes/revolution-20/PreFire3/1830thompsonmapofchicagotown.jpg · Encyclopedia of Chicago: http://www.encyclopedia.chicagohistory.org/pages/11175.html |
| **What it shows** | The original Town of Chicago, **≈0.375 sq mi**, **80-ft streets, 18-ft alleys**, completed **4 August 1830**, made to the order of the Illinois & Michigan Canal Commissioners |
| **Suitability** | **Parameter source, not a warping raster.** No open high-res archival scan located. Its value is the hard dimensional numbers (80 ft / 18 ft, block and lot module) that let you generate street and alley geometry *analytically* rather than tracing pixels. Cite CHM ICHi-34284; budget a rights request if you want a plate-quality scan |

### 1.4 Conley & Stelzer, *A map of Chicago: incorporated as a town August 5, 1833* (1933) — **the building inventory**

| | |
|---|---|
| **URL** | **https://collections.leventhalmap.org/search/commonwealth:0r96fm830** · ARK: https://ark.digitalcommonwealth.org/ark:/50959/0r96fm830 |
| **Record** | Artist **O.E. Stelzer**; copyright holder **Walter Conley**; historical adviser **Caroline M. McIlvaine** (Chicago Historical Society librarian). 1 map, colour, **44 × 64 cm**, **scale ≈ 1:5,450**, **oriented north to the right**, relief shown pictorially, "Compiled from original 'Map of Chicago about 1833.'" Call no. `G4104.C6A5 1833 .S94`; identifier `06_01_014768` |
| **Rights (BPL)** | **"No known copyright restrictions. No known restrictions on use."** |
| **Downloads** | TIF **92.6 MB**; JPEG **7.77 MB**; medium JPEG 426 KB; **GeoTIFF (georeferenced) 124 MB** + Allmaps |
| **⚠ Rights caveat** | Geographicus reports the LOC copy stamped **© CIF 5380, Mar-7 1933**. A 1933 US publication is *not* automatically PD until 2029 — it is PD only if the 1961 renewal lapsed (most pictorial maps were never renewed). chicagology reproduces the Tribune version noting it was *"here reprinted by their permission."* **Recommendation:** BPL's assertion is good cover, but run a Stanford Copyright Renewal Database check before shipping large derivative textures, and record the outcome in the sidecar |
| **Production provenance** | Conley (1893–1936), a Chicago architect, spent ~2 years in libraries and archives; McIlvaine had thirty years earlier collected data from the last surviving pioneers. 100 signed/numbered large prints at \$100; 500 smaller simplified copies omitting the horizon, border and several scenes. Reproduced in the *Chicago Sunday Tribune*, Aug 1933. Dealer descriptions: https://www.geographicus.com/P/AntiqueMap/mapofchicago-conley-1933 and https://www.geographicus.com/P/AntiqueMap/mapofchicagosundaytribune-conley-1933 (both 403 to bots; readable in a browser) |
| **Suitability** | **The single most valuable building-level source you have** — pictorial elevations of individual 1833 structures with street names identical to today's Loop. Use for (a) the building inventory and massing/roof-form reference, (b) a secondary georeference layer via its GeoTIFF. **But it is itself a 1933 reconstruction.** Tag every geometry derived from it as *tertiary / interpretive*, never primary. This is exactly the class of source the London Charter requires you to disclose |

### 1.5 Andreas, *Map of Chicago, 1830* (landownership)

| | |
|---|---|
| **URL** | **https://collections.newberry.org/archive/Map-of-Chicago--1830-2KXJ8ZSSRP29B.html** |
| **Record** | A.T. Andreas (1839–1900); published **1884**, depicting 1830; detached from *History of Chicago*; **Edward E. Ayer Collection**; call no. `G4104.C6G46 1830 .A5`; 44 × 31 cm |
| **Rights** | **"No Copyright – United States"** (open access, no licensing fees) |
| **Resolution** | **9182 × 13140 px**, **IIIF-enabled**, direct download. Platform is Newberry Digital Collections (Orange Logic Cortex) |
| **Legend (verbatim)** | *"The names given on various tracts of land are those of the primary patentees, or persons by whom entry was made, entered or patented between the years of 1828 and 1836. The information is taken from 'Book of Original Entry.' Streets as shown were laid out subsequent to 1830."* |
| **Also** | chicagology copy: https://chicagology.com/wp-content/themes/revolution-20/PreFire3/1830mapatandreas.jpg · full text of Andreas vol. 1: https://archive.org/details/historyofchicago01inandr |
| **Suitability** | **Attribution layer, not geometry.** It's an 1884 redrawing, so don't warp to it. Its value: it binds parcels to *named people*, which is the natural key for the "who owned/occupied this" field in your provenance sidecar. Note the legend's own warning that the streets are anachronistic to 1830 |

### Cross-cutting notes
- **Newberry DCC is broken/reorganised**: `dcc.newberry.org` root returns 200 but the *Mapping Chicago and the Midwest, 1688–1906* item `https://dcc.newberry.org/?p=14414` returns **404**. Verify manually before citing.
- **Newberry high-res orders**: no central image database; use the catalog + "Order Digital Files" (https://www.newberry.org/collection/research-guide/image-research).
- **`encyclopedia.chicagohistory.org` is unreliable** — intermittent 503s. Archive any page you cite.
- **Shoreline is a moving target.** The 1834 harbour cut through the sandbar means the Wright 1834 shoreline ≠ the Thompson 1830 shoreline. Model the 1835 shoreline from Wright/Hathaway, and record the choice.
- **Georeferencing tooling**: both BPL maps are already in **Allmaps** (https://allmaps.org/, editor at https://editor.allmaps.org/), which produces **W3C Georeference Annotations** — an approved IIIF Presentation API extension (https://iiif.io/news/2023/05/15/georef-extension-published/). Store the annotation JSON in your repo as the citable georeferencing record; Allmaps warps on the fly from IIIF without you generating derivatives.

---

## 2. chicagology.com/prefire — what it actually hosts

**Root**: https://chicagology.com/prefire/ — self-described as *"the largest on-line collection of Pre-Chicago Fire images in the world."*

**Structure**
- Year-by-year **"new buildings"** lists: 1846–49, 1855–57, 1859, 1861, 1864–70. Subpage pattern `chicagology.com/prefire/prefireNNN/`.
- An **alphabetical directory of 500+ named pre-fire structures** (banks, theatres, hotels, churches, breweries, foundries, mansions), each entry giving street location with cross-streets.
- **Fort Dearborn** section at `chicagology.com/fortdearborn/NNN/`.
- **Prominent Events 1804–1926** chronology.

**Pages directly relevant to 1830–35**
- **https://chicagology.com/prefire/prefire275/** — *Early Street Maps of Chicago*. Inventory in page order: Thompson 1830 plat; *Mouth of Chicago River*, 24 Feb 1830; *The Land Owner* (Aug 1869) engraved recreation of Chicago **1835** from a map found among J.H. Kinzie's papers; the **original Kinzie manuscript map**, hand-dated **1833**, described as *"probably the first ever made in Chicago"*, showing school reservations and an intact Fort Dearborn; **Wright 1834**; *Wabonsia*, James Kinzie, **1835**; **Andreas 1830** landownership; Wolf's Point 1853; **Conley/Stelzer** — both the Tribune (11 Aug 1933) reproduction and the original Conley map. Plus a text addendum on South Water St., Lake St., the Milwaukee Trace / Northwest Plank Road, Barry Point Trail and the Nine-mile Swamp crossing — **useful for the road network beyond the platted grid**.
- **https://chicagology.com/prefire/prefire273/** — *Wolf's Point and the Town of Chicago*. Carries the **Geo. Davis 1832 drawing** of Wolf's Point (engraved in *Chicago Magazine*, 15 May 1857) with a detailed prose description of the two principal buildings — **Elijah Wentworth's tavern** (part log, part frame, north of the Lake St. bridge site) and the **Miller House** (log, partly sided, on the point between the North Branch and the Main Channel), plus Blanchard's 1892 *"Chicago in 1832"*, *The Point 1833* (Justin Herriott), Wolf's Point 1830 (Andreas), and *1833 South Water*. **This is your best textual evidence for specific 1832–33 building construction and materials.**
- **https://chicagology.com/prefire/prefire127/** — Green Tree Tavern, built 1833, NE corner N. Canal & W. Lake.

**Building key / numbered map: ❌ not present.** There is **no numbered or keyed 1833–35 map** anywhere on chicagology. The closest substitutes are (a) the Conley/Stelzer pictorial, which labels landmarks in situ but has **no numeric key**, and (b) the alphabetical directory, which functions as a de-facto key by *name + cross-streets*. **You will have to construct the 1835 building key yourself** from Andreas vol. 1, the Fergus-reprinted early Chicago directories, and Conley's pictorial labels.

**Rights**: chicagology carries no license statement. Its images are hot-linkable JPEGs under `/wp-content/themes/revolution-20/PreFire*/` but **treat the site as a finding aid only** — re-source every image from the holding institution before it enters the model or the citation graph.

---

## 3. Precedent pipelines

### 3.1 `CamilleMorlighem/histo3d` — https://github.com/CamilleMorlighem/histo3d

*"Automatic reconstruction of historical 3D city models from historical maps."* MIT licensed. Paper: **Morlighem et al., "Reconstructing historical 3D city models," *Urban Informatics* 1, 11 (2022)**, https://doi.org/10.1007/s44212-022-00011-3 (open access: https://ncbi.nlm.nih.gov/pmc/articles/PMC9587120). MSc thesis: https://repository.tudelft.nl/islandora/object/uuid:0889e498-cdd6-4a19-bbcb-d3fb189560e1

**Four stages**
1. **Prepare** georeferenced historical maps (TIF, projected CRS).
2. **Process raster → extract building plots** (supervised, using a training shapefile of classified points: buildings / text / symbols).
3. **Subdivide plots → individual building footprints** (two alternative algorithms).
4. **Reconstruct 3D buildings** from footprints.

**Inputs** — mandatory: georeferenced TIF; training shapefile; ground point cloud (LAS or SHP). Optional: current footprints with construction dates + roof heights; existing 3D models (CityJSON); ground-truth plot points for validation.
**Outputs**: `final_plots_*.shp` (with generalisation metrics), `final_all_footprints.shp`, `histo_model_*.json` (CityJSON), plus **val3dity** and **cjio** validation reports.
**Dependencies**: Python 3.5+; **Blender 2.83+** with **BlenderGIS**, **Up3date**, **BCGA**; **GRASS GIS 7.8+**; **cjio**; **val3dity**.
**Variants**: *complete* (uses current footprints + existing 3D models + ground truth) vs *shortened* (mandatory inputs only).
**Reported accuracy**: >84% of ground-truth building plots identified, >89% correctly classified — *for maps with good scan resolution and strict symbology*.
**Data repo**: https://github.com/CamilleMorlighem/histo3d-data — Delft 1880/1915/1961/1982 and Brussels 1700/1890/1924 as SHP + GeoTIFF + CityJSON, MIT.

**What to reuse conceptually**
- ✅ **The stage separation** (raster → plots → footprints → solids) as your directory and provenance structure — each stage's output is a citable artefact.
- ✅ **The explicit "educated guesses and assumptions" framing** — histo3d states up front that it produces *plausible* models. Adopt the same honesty as a first-class data field.
- ✅ **A hard validation gate**: run `val3dity` on the CityJSON before any release. Nothing ships that isn't a valid solid.
- ✅ **CityJSON as the archival intermediate**, glTF as the delivery format.

**What NOT to reuse**
- ❌ **Point-cloud / LiDAR height recovery and current-footprint matching.** Nothing of 1835 Chicago survives, so heights cannot be derived — they must be **authored** from documentary evidence (storey counts in Andreas, directory entries, Conley's elevations). Your height field is an *interpretation* and must be typed as such.
- ❌ **The two-alternative plot-subdivision machinery.** Thompson's plat gives you a regular, dimensioned grid (80-ft streets, 18-ft alleys) and Wright gives you surveyed lots — subdivide analytically, don't infer from pixels.
- ❌ **Full automation.** histo3d targets hundreds/thousands of buildings from symbol-strict survey maps. At ~150 buildings from *pictorial* sources, hand-authoring in Blender with a scripted export is cheaper and far more defensible.

### 3.2 chicago00.org — what it is

**The Chicago 00 Project**, https://chicago00.org/ — a free AR/VR series developed and managed by **John Russick** (then SVP, Chicago History Museum) and **Geoffrey Alan Rhodes**, **2014–2021**, built to surface CHM's film/photo/sound archive as site-specific immersive experiences. Episodes: **Eastland Disaster 1915** (AR along the river), **St. Valentine's Day Massacre 1929** (VR, Feb 2017), **Century of Progress 1933** (VR, 2018), **1968 DNC protests** (360 video, https://1968.chicago00.org/), **1893 World's Columbian Exposition** (web portal, https://1893.chicago00.org/), **Great Chicago Fire 1871** (https://1871.chicago00.org/, krpano-delivered WebXR/gigapixel). AAM Award for Excellence, 2018.

**Relevance to you**: it is a **media-anchored AR overlay on real sites**, not a modelled walkable city — so it is *not* a pipeline precedent. It is valuable as (a) evidence that CHM will partner on this kind of work and is the natural rights counterparty for ICHi-34284 and the Conley original, and (b) a model for the *interpretive* layer — anchoring archival media to coordinates.

### 3.3 Other walkthrough precedents (3, one line each)

- **Virtual St Paul's Cathedral Project** (NC State / John Wall, with MOLA) — https://vpcathedral.chass.ncsu.edu/ — 1620s London cathedral modelled visually *and acoustically*; the exemplary precedent is its published **"Constructing the Visual Model"** page (https://vpcathedral.chass.ncsu.edu/?page_id=122), which documents modelling rationale alongside the model — do exactly this.
- **Virtual Angkor** (Monash SensiLab / Flinders / UT Austin) — https://www.virtualangkor.com/ and https://www.virtualangkor.com/technology — a decade-long, city-scale, *populated* reconstruction delivered as 360° video + VR teaching modules; the precedent for scoping a whole living city and for packaging it pedagogically.
- **Rosewood Heritage & VR / "Rosewood: An Interactive History"** — https://virtualrosewood.com/raih/ — a small vanished American town rebuilt for the browser with oral histories and background data surfaced as interactive overlays; **the closest analogue to Chicago 1835** in scale, delivery medium and provenance-surfacing ambition.
- *(Commercial-scholarly extreme, for calibration: Rome Reborn / Flyover Zone — https://en.wikipedia.org/wiki/Rome_Reborn.)*

---

## 4. three.js walkthrough tech — 2025/2026 state

### 4.1 Version and module resolution

**Current: `three@0.185.1` (r185), published 2026-07-01.** Recent cadence: 0.183.0 (2026-02-18), 0.184.0 (2026-04-16), 0.185.0 (2026-06-25). three ships ~6–8 releases/yr and **routinely breaks addon APIs between them** — **pin an exact version**, never `@latest`.

Import map, exactly mirroring three.js's own examples (which use `"three": "../build/three.module.js", "three/addons/": "./jsm/"` — see https://github.com/mrdoob/three.js/blob/dev/examples/misc_controls_pointerlock.html):

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.185.1/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.185.1/examples/jsm/"
  }
}
</script>
```
unpkg equivalent: `https://unpkg.com/three@0.185.1/build/three.module.js` + `https://unpkg.com/three@0.185.1/examples/jsm/`.

**CDN vs vendored → vendor it.** Copy `build/three.module.js` plus only the `examples/jsm/**` files you import into `/vendor/three-0.185.1/` and point the import map at repo-relative paths. Rationale for a provenance project: GitHub Pages is already a static host so there is no bandwidth argument; a CDN outage or an unpinned tag breaks a *citable* artefact; and the old cross-site cache-sharing benefit no longer exists (browsers have partitioned the HTTP cache per top-level site since ~2020). **Keep the import map either way** — it is the mechanism that makes bare `three/addons/...` specifiers work with zero build.

**Minimal-build alternative**: Vite + `vite build --base=/<repo>/` + a GH Actions Pages deploy. Only worth it if you want tree-shaking and content-hashed filenames. Not needed at this scale.

**GitHub Pages specifics**: add a `.nojekyll` file at repo root (Jekyll otherwise drops `_`-prefixed dirs). All asset paths must be relative (`./assets/…`) or use `<base>`, since the site lives under `/<repo>/`. GH Pages does **not** send COOP/COEP, so no `SharedArrayBuffer` → use single-threaded Draco/Basis decoders (they work fine).

### 4.2 Controls

```js
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
const controls = new PointerLockControls(camera, document.body);
```
API (https://threejs.org/docs/pages/PointerLockControls.html): `lock(unadjustedMovement)`, `unlock()`, readonly `isLocked`, `pointerSpeed` (default 1), `minPolarAngle`/`maxPolarAngle`, `moveForward(d)`, `moveRight(d)`, `getDirection(v)`; events `lock`, `unlock`, `change`. Reference implementation with WASD + jump + raycast floor collision: the official `misc_controls_pointerlock` example above.

**Mobile fallback is mandatory — Pointer Lock is unavailable on iOS Safari.** Feature-detect and branch:
- Left thumb virtual stick → translate; right-half screen drag → look. **nipplejs** (https://github.com/yoannmoinet/nipplejs) is the de facto joystick lib and integrates cleanly with three.
- **Architect the input layer as a single intent object** — `{forward, strafe, yawDelta, pitchDelta, jump}` — written by either the pointer-lock handler or the touch handler, and read by one shared character controller. This keeps the walk physics identical across platforms.
- Handle `visualViewport` resize for the iOS URL bar; add an explicit "tap to start" gate (needed anyway for audio autoplay policy).

### 4.3 glTF loading and compression

```js
import { GLTFLoader }   from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader }  from 'three/addons/loaders/DRACOLoader.js';
import { KTX2Loader }   from 'three/addons/loaders/KTX2Loader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
```
- **Meshopt over Draco for this project.** `loader.setMeshoptDecoder(MeshoptDecoder)`. `EXT_meshopt_compression` + `KHR_mesh_quantization` decodes dramatically faster than Draco with no per-file WASM worker cold start — the right trade for ~150 small low-poly meshes. Reported reductions of 29 MB → 2.5 MB on comparable content; three.js supports both.
- **Draco** if you need it: `dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/')` (the Draco team's recommended hosting; see three.js issue https://github.com/mrdoob/three.js/issues/27263), or vendor `examples/jsm/libs/draco/gltf/` (`draco_decoder.js`, `draco_decoder.wasm`, `draco_wasm_wrapper.js`). Then `gltfLoader.setDRACOLoader(dracoLoader)`.
- **Textures: KTX2 + Basis.** `ktx2Loader.setTranscoderPath('<vendored>/examples/jsm/libs/basis/').detectSupport(renderer)`, then `gltfLoader.setKTX2Loader(ktx2Loader)`. This is the mobile-critical one — KTX2 stays compressed *on the GPU*, roughly 10× VRAM saving, which matters more than download size. ETC1S for albedo, UASTC for normals.
- **Authoring pipeline** — **glTF Transform** (https://gltf-transform.dev/, `@gltf-transform/cli`):
  ```
  npx @gltf-transform/cli optimize in.glb out.glb --compress meshopt --texture-compress ktx2
  ```
  Also run `dedup`, `weld`, `join`, `simplify`, and especially **`palette`** — which converts per-building flat colours into a shared atlas so every building can share one material (a prerequisite for BatchedMesh).

### 4.4 Instancing, batching, terrain, sky

**Instancing/batching**
- **`InstancedMesh`** for identical repeated geometry — prairie grass cards, fence posts, trees, chimneys, window frames, hitching posts. 1 draw call for N instances; the commonly cited figure is ~200 draw calls / 20 ms collapsing to 1 call / 0.1 ms.
- **`BatchedMesh`** (https://threejs.org/docs/pages/BatchedMesh.html) for *different* geometries sharing one material while remaining **individually addressable** — this is precisely your buildings case, because you need per-building raycast picking to open the provenance popup. Combine with array textures if you need per-building texture variation in one draw call.
- Instrument with `renderer.info.render.calls`; target **< 50** on mobile.
- Grass: instanced alpha-tested cross-quads, per-instance scale/rotation jitter, distance fade, `castShadow = false`, and cull the instance ring aggressively.

**Terrain — do not do runtime displacement.** 1835 Chicago is a near-flat sand/prairie plain; the only relief is river banks, the sandbar and the lake shore. Bake the terrain once in Blender/QGIS as a decimated glTF mesh with baked vertex colours or a single low-res albedo. Runtime `PlaneGeometry` + displacement map costs vertices you don't need (displacement requires high tessellation to avoid blockiness) and complicates collision. Keep a **separate simplified collision mesh** — or just a sampled heightfield array at ~1 m — for the walk controller, so rendering LOD and physics stay decoupled.

**Sky and period lighting**
```js
import { Sky } from 'three/addons/objects/Sky.js';
```
Preetham analytic skydome (https://threejs.org/docs/pages/Sky.html; example https://threejs.org/examples/webgl_shaders_sky.html). Uniforms: `turbidity`, `rayleigh`, `mieCoefficient`, `mieDirectionalG`, `sunPosition`, `showSunDisc`. **Set `sky.material.uniforms.showSunDisc.value = false` before generating the environment map, and restore it before rendering the skybox** — the docs call this out explicitly as an artefact fix.
- Pick and *document* a specific moment (e.g. August 1835, 10:00 local, 41.88 °N / 87.63 °W), compute the real sun elevation/azimuth, and drive both `sunPosition` and a matching `DirectionalLight` from it. Feed the sky into `PMREMGenerator.fromScene(sky)` for IBL ambient.
- Raise `turbidity` slightly for prairie haze and woodsmoke. `renderer.toneMapping = THREE.ACESFilmicToneMapping`; `renderer.outputColorSpace = THREE.SRGBColorSpace`.
- Shadows: **one** directional shadow, frustum tightly fitted around the player (±60 m), 2048² desktop / 1024² mobile, tuned `shadow.bias`/`normalBias`. Bake AO into the building textures rather than paying for SSAO.

### 4.5 Performance budget — ~150 low-poly buildings + prairie, mid-range mobile

Target 60 fps, accept a 30 fps floor.

| Budget item | Target |
|---|---|
| Total download | **15–20 MB** (buildings 6–8 MB, terrain 1–2 MB, KTX2 textures 4–6 MB, three.module.js ~1.2 MB) |
| Triangles per building | 1.5–3k avg → **225k–450k** for the town |
| Vegetation + props | ≤ 150k tris |
| **Total visible tris** | **≤ 600k** |
| **Draw calls** | **≤ 50–80** — 1 BatchedMesh (buildings, atlased), 2–4 InstancedMesh (vegetation/props), 1 terrain, 1 water, 1 sky |
| Unique materials | ≤ 5 |
| Textures | ≤ 8 KTX2, none above 1024² |
| GPU memory | ≤ 150 MB |
| JS heap | ≤ 200 MB |
| Pixel ratio | `Math.min(devicePixelRatio, 2)` desktop, cap at **1.5** mobile; add dynamic resolution scaling driven by frame time |
| LOD | Frustum culling is on by default. Add `THREE.LOD` only if profiling demands it — at 150 buildings it usually won't |

General references: https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/ · https://discoverthreejs.com/tips-and-tricks/ · https://www.utsubo.com/blog/threejs-best-practices-100-tips

---

## 5. Renderer-agnostic layer

### 5.1 glTF + JSON sidecar — confirmed, this is the right contract

glTF 2.0 is by definition *"a JSON-based, rendering-API-agnostic runtime asset delivery format"* (https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html), with first-class importers in **Godot 4** (native, best-in-class), **Unity** (glTFast / UnityGLTF) and **Unreal** (Interchange / glTF importer). Meshopt and Draco are both supported by Godot and glTFast; Draco is the safer lowest common denominator for Unreal, meshopt the better one for web. **Ship an uncompressed `.glb` as the archival master and generate compressed web derivatives from it** — one master, many deliveries.

**Keep provenance out of the binary and in the sidecar.** One JSON record per structure, keyed by a stable ID that *also* appears as the glTF **node name** and in **`node.extras`** (`extras` survives round-trips through Blender, Godot and glTFast, and is trivially diffable in git).

Suggested sidecar record:
```
id, name(s), function, 
location: { lat, lon, crs, local_x, local_z, street, block, lot },
extant: { from, to },
evidence: [ { source_url, iiif_region, page_or_plate, quotation, holding_institution, rights } ],
confidence: attested | inferred | conjectural,     ← the London Charter "paradata" requirement
assumptions: [ free text — height, roof form, materials, siting ],
author, license, revision, last_modified
```
Serve the *same* JSON to the three.js popup UI so the walkthrough and the archival record can never drift apart.

**Options considered and rejected (for now):**
- `KHR_xmp_json_ld` — asset-level, awkward for 150 per-node records.
- **`EXT_structural_metadata` + `EXT_mesh_features`** (https://github.com/CesiumGS/glTF/tree/3d-tiles-next/extensions/2.0/Vendor/EXT_structural_metadata) — the correct long-term answer *if* you ever move to 3D Tiles, but it is binary-packed, thinly supported outside Cesium, and not human-diffable — the opposite of what a provenance project wants. Adopt only at the point you export 3D Tiles.

**Georeference contract.** Declare one projected CRS everywhere: **EPSG:3435** (NAD83 / Illinois East, ftUS — the local standard) or **EPSG:26971** if you want metres. Put a single scene origin (lat/lon + CRS + rotation) in the sidecar header so any engine can place the model absolutely, and keep three.js scene coordinates as **metres relative to that origin** to avoid float32 precision loss.

### 5.2 CityJSON as optional archival export — yes, worth it, low cost

CityJSON is at **v2.0** (upgrade guides at https://www.cityjson.org/). It gives you what glTF structurally cannot: **semantic surfaces** (`WallSurface` / `RoofSurface` / `GroundSurface`), **explicit LOD tagging**, a **real CRS**, and arbitrary per-object attributes — meaning it can carry your provenance attributes *natively* rather than in a sidecar.

Toolchain (all catalogued at https://www.cityjson.org/software/):
- **Up3date** — https://github.com/cityjson/Up3date — Blender add-on to import/export CityJSON preserving geometries, attributes and semantics, with LODs accessible via the Blender UI. **⚠ README states CityJSON v1.0**, and the author notes it is a free-time project with no development guarantees — verify against v2.0 or normalise with `cjio upgrade`. Alternative if it bit-rots: **CityJSONEditor** (https://github.com/rostock/CityJSONEditor).
- **cjio / cjval** — CLI processing, version upgrade, and the official CityJSON validation.
- **val3dity** — https://val3dity.readthedocs.io/ — ISO-19107 geometric-validity checking of solids. Use as the release gate, exactly as histo3d does.
- **ninja** (web viewer) for spot checks; **tyler** if you ever want CityJSON → 3D Tiles.

**Recommended flow:** Blender is the single source of truth →
1. `.glb` for web + game engines (meshopt/KTX2 derivatives from an uncompressed master),
2. **CityJSON** via Up3date for the archive/GIS,
3. the **sidecar JSON** generated from the same Blender custom properties,

so all three artefacts are provably consistent. Gate every release on `val3dity` passing and on a script that asserts the node names in the `.glb`, the object IDs in the CityJSON, and the keys in the sidecar are the same set.

---

### Sources

[Newberry — Hathaway 1834 on Internet Archive](https://archive.org/details/nby_157756) · [Newberry catalog permalink](https://i-share-nby.primo.exlibrisgroup.com/permalink/01CARLI_NBY/i5mcb2/alma991577568805867) · [LOC — Hathaway map item](https://www.loc.gov/item/2008621683/) · [LOC IIIF info.json](https://tile.loc.gov/image-services/iiif/service:gmd:gmd410:g4104:g4104c:ct007620/info.json) · [MIT DOME copy](https://dome.mit.edu/handle/1721.3/15641) · [Leventhal — Wright 1834](https://collections.leventhalmap.org/search/commonwealth:js9577436) · [Digital Commonwealth ARK — Wright](https://ark.digitalcommonwealth.org/ark:/50959/js9577436) · [Adam Matthew — Newberry Graff 4755](https://www.americanwest.amdigital.co.uk/Documents/Details/Chicago--drawn-by-J--S--Wright-according-to-survey/Graff_4755) · [UWM AGDM — Wright 1834](https://collections.lib.uwm.edu/digital/collection/agdm/id/5958/) · [Encyclopedia of Chicago — Wright's Survey Map](http://www.encyclopedia.chicagohistory.org/pages/10349.html) · [Encyclopedia of Chicago — Hathaway](http://www.encyclopedia.chicagohistory.org/pages/10634.html) · [Encyclopedia of Chicago — Thompson's Plat of 1830](http://www.encyclopedia.chicagohistory.org/pages/11175.html) · [Wikimedia — Thompson plat PNG](https://commons.wikimedia.org/wiki/File:Thompson_plat_of_Chicago_1830.png) · [Wikimedia — Thompson plat JPG](https://commons.wikimedia.org/wiki/File:Thompson_Chicago_plat_1830.jpg) · [Leventhal — Conley/Stelzer 1933](https://collections.leventhalmap.org/search/commonwealth:0r96fm830) · [Geographicus — Conley/Stelzer](https://www.geographicus.com/P/AntiqueMap/mapofchicago-conley-1933) · [Geographicus — Sunday Tribune edition](https://www.geographicus.com/P/AntiqueMap/mapofchicagosundaytribune-conley-1933) · [Newberry Digital Collections — Andreas Map of Chicago, 1830](https://collections.newberry.org/archive/Map-of-Chicago--1830-2KXJ8ZSSRP29B.html) · [Andreas, History of Chicago vol. 1 (IA)](https://archive.org/details/historyofchicago01inandr) · [Newberry — Image Research guide](https://www.newberry.org/collection/research-guide/image-research) · [Newberry — Chicago History guide](https://www.newberry.org/collection/research-guide/chicago-history) · [Allmaps](https://allmaps.org/) · [Allmaps Editor](https://editor.allmaps.org/) · [IIIF Georeference Extension announcement](https://iiif.io/news/2023/05/15/georef-extension-published/) · [chicagology — Pre-Fire index](https://chicagology.com/prefire/) · [chicagology — Early Street Maps of Chicago](https://chicagology.com/prefire/prefire275/) · [chicagology — Wolf's Point and the Town of Chicago](https://chicagology.com/prefire/prefire273/) · [chicagology — Green Tree Tavern](https://chicagology.com/prefire/prefire127/) · [histo3d](https://github.com/CamilleMorlighem/histo3d) · [histo3d-data](https://github.com/CamilleMorlighem/histo3d-data) · [Reconstructing historical 3D city models (Urban Informatics 2022)](https://link.springer.com/article/10.1007/s44212-022-00011-3) · [PMC open-access copy](https://ncbi.nlm.nih.gov/pmc/articles/PMC9587120) · [TU Delft thesis](https://repository.tudelft.nl/islandora/object/uuid:0889e498-cdd6-4a19-bbcb-d3fb189560e1) · [Chicago 00 Project](https://chicago00.org/) · [Chicago 00 — 1871](https://1871.chicago00.org/) · [Chicago 00 — 1893](https://1893.chicago00.org/) · [Virtual St Paul's Cathedral Project](https://vpcathedral.chass.ncsu.edu/) · [VSPC — Constructing the Visual Model](https://vpcathedral.chass.ncsu.edu/?page_id=122) · [Virtual Angkor](https://www.virtualangkor.com/) · [Virtual Angkor — Technology](https://www.virtualangkor.com/technology) · [Rosewood: An Interactive History](https://virtualrosewood.com/raih/) · [Rome Reborn](https://en.wikipedia.org/wiki/Rome_Reborn) · [three.js PointerLockControls docs](https://threejs.org/docs/pages/PointerLockControls.html) · [three.js pointerlock example source](https://github.com/mrdoob/three.js/blob/dev/examples/misc_controls_pointerlock.html) · [three.js Sky docs](https://threejs.org/docs/pages/Sky.html) · [three.js sky shader example](https://threejs.org/examples/webgl_shaders_sky.html) · [three.js BatchedMesh docs](https://threejs.org/docs/pages/BatchedMesh.html) · [three.js GLTFLoader docs](https://threejs.org/docs/pages/GLTFLoader.html) · [three.js DRACOLoader docs](https://threejs.org/docs/pages/DRACOLoader.html) · [three.js issue #27263 — gstatic Draco default](https://github.com/mrdoob/three.js/issues/27263) · [glTF Transform](https://gltf-transform.dev/) · [@gltf-transform/cli on npm](https://www.npmjs.com/package/@gltf-transform/cli) · [Codrops — Building Efficient Three.js Scenes (2025)](https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/) · [Discover three.js — Tips and Tricks](https://discoverthreejs.com/tips-and-tricks/) · [100 Three.js Performance Tips (2026)](https://www.utsubo.com/blog/threejs-best-practices-100-tips) · [nipplejs](https://github.com/yoannmoinet/nipplejs) · [glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html) · [EXT_structural_metadata](https://github.com/CesiumGS/glTF/tree/3d-tiles-next/extensions/2.0/Vendor/EXT_structural_metadata) · [CityJSON](https://www.cityjson.org/) · [CityJSON software list](https://www.cityjson.org/software/) · [Up3date](https://github.com/cityjson/Up3date) · [CityJSONEditor](https://github.com/rostock/CityJSONEditor) · [val3dity docs](https://val3dity.readthedocs.io/)
