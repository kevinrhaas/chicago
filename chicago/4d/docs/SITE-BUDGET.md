# The published tree's byte budget — where the 32 MB is, and what it defends

**T-0722.** On 2026-09-05 `dev` reached **31.999 MB** of a 32 MB budget on its own, and
every open PR on the queue stopped being mergeable: `tools/validate.py` refuses the
dataset step over budget, and a changelog entry alone is a few KB. The PR that hit it
(T-0693, #834) filed the ticket rather than trimming its own provenance notes to buy
60 KB, which was the right call — a budget paid for out of the honesty of the record is
a budget that has stopped defending anything.

The ticket's first ask was the one nothing here had ever answered: **say where the bytes
are.** This file is that answer, and `python3 tools/site_budget.py` re-prints it from the
tree at any commit, so it does not go stale as prose.

## 1. Where the 32 MB is

Printed at the fix commit, after the de-duplication in § 3:

```
PUBLISHED TREE  site/4d
   30.690 MB in 2273 files — 95.9 % of the 32 MB budget,   1.310 MB of headroom

BY DIRECTORY (two levels)
    8.768 MB   1385  data/residents
    6.752 MB    379  data/sidecars
    6.192 MB    372  data/gltf
    2.198 MB     10  walk/vendor
    1.419 MB     45  walk/js
    1.311 MB      1  js
    1.161 MB      3  data
    0.618 MB      7  data/terrain
    0.544 MB      9  data/enclosures
    0.364 MB      6  data/frontage
    0.348 MB      3  (root)
    0.291 MB     24  data/flora
    0.218 MB      3  data/yard
    0.203 MB     11  data/fauna
    0.129 MB      2  data/signage
    0.090 MB      7  walk/css
    0.034 MB      1  walk
    0.029 MB      2  data/wharves
    0.018 MB      2  data/boats
    0.005 MB      1  data/scenes

BY FILE TYPE
   18.899 MB   1831  .json
    6.192 MB    372  .glb
    4.925 MB     54  .js
    0.495 MB      1  .bin
    0.090 MB      7  .css
    0.048 MB      3  .geojson
    0.034 MB      2  .html
    0.004 MB      1  .md
    0.002 MB      1  (none)
    0.001 MB      1  .sha256

THE 20 LARGEST FILES
    1.376 MB  walk/vendor/three-0.185.1/three.core.js
    1.311 MB  js/changelog.js
    1.155 MB  data/liberties.json
    0.952 MB  data/residents/directories.json
    0.666 MB  data/sidecars/1835/people.json
    0.665 MB  data/gltf/terrain__e1834_harbor_cut.glb
    0.620 MB  walk/vendor/three-0.185.1/three.module.js
    0.495 MB  data/terrain/epochs/e1834_harbor_cut/heightfield.bin
    0.489 MB  data/residents/index.json
    0.362 MB  data/residents/research_pilot.json
    0.347 MB  tickets.json
    0.316 MB  data/frontage/town_street_edge.json
    0.223 MB  data/enclosures/town_lot_line_rails.json
    0.214 MB  walk/js/flora.js
    0.194 MB  data/yard/town_trade_goods.json
    0.190 MB  data/sidecars/1835/index.json
    0.162 MB  walk/js/trees.js
    0.137 MB  data/enclosures/town_lot_line_boards.json
    0.127 MB  data/signage/town_business_signboards.json
    0.118 MB  walk/js/main.js

IDENTICAL CONTENT, SHIPPED MORE THAN ONCE (groups over 64 KB)
  none — every file over the floor is the only copy of itself
```

Read plainly: **the tree is the record.** 25.3 MB of the 30.7 MB is `data/` — 1,385
resident files, 379 sidecars, 372 baked GLBs — and every one of those directories has a
named reader in `tools/publish.sh` and a fetch site in `renderers/web/js/`. The 6.2 MB of
GLB is the town itself. There is no staging area here, no build intermediate, no
forgotten export.

## 2. What the mirror owes a visitor

The ticket's second ask allowed for a whole category to be free to drop: "published
research JSON the walkthrough does not read at runtime". **That category is empty, and it
was checked by name rather than assumed.** The three files that look most like research
spill are all fetched:

| file | size | read by |
|---|---|---|
| `data/residents/directories.json` | 0.95 MB | `renderers/web/js/residents.js:803, :998` |
| `data/residents/index.json` | 0.49 MB | `residents.js:423`, `census.js:7` |
| `data/residents/research_pilot.json` | 0.36 MB | `residents.js:786, :994` |

The rest of `data/` is the same story, and `tools/publish.sh` argues it directory by
directory, each comment written by the run that found the layer 404ing on the deployed
site while the dev tree rendered it perfectly. So the honest report is that **nothing in
this tree is spare except a copy**, which is § 3.

## 3. The one byte that was not the record

`tools/site_budget.py` groups the tree by content hash, because a total cannot tell the
difference between a byte that IS the record and a byte that is a COPY of one. It found
exactly one group over 64 KB:

```
1.311 MB wasted — 2 x 1.311 MB
    js/changelog.js
    walk/js/changelog.js
```

The changelog is authored at `renderers/web/js/changelog.js` — inside the app, because
the What's-new tab imports it and a page cannot import from its own publish mirror.
`publish.sh` then did two things with it: `cp -a renderers/web "$SITE/walk"` carried it to
`walk/js/changelog.js`, and an explicit copy put it at `js/changelog.js`, the fleet-parsed
path Manager and the polecat.live launcher read. Both paths are contracts. Neither was
wrong. Together they shipped the same 1.31 MB twice — **4.1 % of the whole budget**,
growing at **twice** the rate of the record itself, since every new entry cost the payload
double.

The fix keeps both URLs and ships one file: `publish.sh` writes the real changelog to the
fleet path and overwrites the mirror's `walk/js/changelog.js` with a nine-line re-export
of it. `whatsnew.js` imports `./changelog.js` and asks only for `CHANGELOG` and
`LATEST_VERSION`; inside the mirror, `../../js/changelog.js` resolves. **Nothing under
`renderers/web/` changes** — the dev tree still holds the authored file at the path the
app imports, which is the entire reason the changelog lives inside the app.

Measured: **31.999 MB → 30.69 MB**, and the growth rate of the changelog on the payload is
halved.

## 4. The boot payload, measured — and what the whole-tree cap is now for

The recommendation at the foot of the old §4 was: measure what a visitor
actually downloads, budget THAT tightly, and let the whole-tree cap relax into
the repository-hygiene guard it always was. **T-0727 is that measurement, made
2026-09-16 on build `62ee9f88d`:**

```
BOOT PAYLOAD — first visit stands in the 1835 street
  7.223 MB across 915 request(s), gzip on the wire, fresh browser context,
  counted from the server side until the app's own ready flag
  (window.__chicago4d.ready) plus a 3 s settle.

  BY TYPE          2.583 MB .json · 2.515 MB .glb · 1.716 MB .js
                   0.368 MB .bin · 0.031 MB .css
  LARGEST          1.099 MB terrain__e1834_harbor_cut.glb
                   0.713 MB js/changelog.js
                   0.368 MB the 16-bit heightfield
                   0.348 MB data/liberties.json
                   0.272 MB three.core.js
```

Three consecutive runs produced byte-identical totals — the measurement is a
property of the tree, not of the run.

**The boot payload budget is 29 MB**, re-set on 2026-10-17 by T-2693 for the prebuilt
ground (§ 4g). T-2677 had set it at 20 MB on 2026-10-16 for the prebuilt frontage timber
(§ 4f). T-1973 had set it at 13 MB on 2026-10-02 for the reasons in
§ 4a. It was set at 12 MB, 1.66× the measured 7.223 MB:
tight enough that a careless import into `walk/js/` or an unmetered new boot
fetches cannot accumulate silently (each is visible against 60 % spent), and
loose enough that the growing town — South Through Time is ahead, and every
new 1835 structure adds boot GLBs — does not force a re-budget every quarter.
Re-measure and check with:

```
bash tools/publish.sh                      # build the mirror the visitor gets
node tools/measure_boot_payload.mjs        # the report above
node tools/measure_boot_payload.mjs --check  # exit 1 past the 29 MB budget
```

The nightly `chicago-4d-bake.yml` enforces this with `--check` in the desktop
`1-2` smoke leg (T-1156), after downloading the bake's `published-mirror`
artifact. A breach fails the smoke dependency and prevents the bake PR from
opening. It runs once per bake, before that leg's renderer smoke, with a
three-minute step timeout; the eight smoke legs and their ceilings stay intact.
GitHub schedules use the default branch's workflow definition, so this change
reaches the scheduled nightly through the normal owner-controlled promotion to
`main`; a push or dispatch using the updated workflow exercises it earlier.

The method, stated because the number is only as good as it: a real headless
Chromium boots the published mirror over a local origin that gzips every
response — the live origin was verified to serve `content-encoding: gzip` for
`.js`, `.json`, `.html` **and** `.glb` alike — from a fresh context (no cache,
no cookies), counting every byte the server writes per request until the same
ready flag the smoke gates on. No hand-declared file list anywhere in it.

### 4a. Re-measured 2026-10-02: 14.27 MB, and 2.28 MB of it was not the town (T-1973)

Dev @ `c86459b5` measured **14.269 MB across 1,286 requests**, 2.27 MB over. The
growth since 2026-09-16 was not one careless import. Two things had grown by design:
the PBR relief maps (T-1488, T-1815, T-1836, T-1963) put **3.95 MB of PNG** on the
boot path, and the scene's own records grew (`.json` 2.58 → 4.27 MB, `.glb` 2.52 →
3.41 MB) as the town filled in. The third was a cost that grew with every release:
**`js/changelog.js`, 1.03 MB on the wire**, imported at boot so the What's-new dot
could count unread releases.

Two of those were bytes a visitor did not need in order to stand in the street,
and T-1973 removed them without touching what the scene shows:

| cut | before | after | how |
|---|---|---|---|
| relief maps | 3.947 MB PNG | 2.649 MB WebP | lossless WebP beside each PNG master, held **pixel-identical** by `tools/web_textures.py --check` in the gate; the four modules ask for `.webp` |
| changelog at boot | 1.028 MB | 0 | `publish.sh` writes the release numbers into the page (`<meta name="c4d-releases" content="1-1307">`); `whatsnew.js` imports the changelog only when the tab opens |

```
BOOT PAYLOAD — first visit stands in the 1835 street, with T-1973's cuts
  on c86459b5                       11.989 MB across 1284 request(s) — two runs, byte-identical
  on 652ca8ea (+ T-1960)            12.000 MB across 1285 request(s) — 107 bytes inside 12 MB
  on d8c6b562 (+ T-1971, T-1804)    12.575 MB across 1289 request(s) — 13,185,448 bytes
```

### 4b. Why the budget is 13 MB now (T-1973)

The cuts above held: the same day, on dev @ `d8c6b562`, the maps and the changelog
weighed what they did on `c86459b5`. **What moved was the town.** T-1971 seated the
1,003 households present on the scene date under standing dwellings (L354), and the
seats live in the per-structure sidecars every first visit loads: `data/sidecars/1835/`
grew **+0.546 MB on the wire** in that one merge. T-1804's two camps added 26 KB more.
That is the 1835 completion programme (T-1215) doing what the owner asked of it, and
its remaining pieces (T-1972's uncertain households, T-1966's workplaces) write into the
same records.

The 12 MB was chosen to be "loose enough that the growing town does not force a
re-budget every quarter". It lasted sixteen days, because the town grew faster than the
quarter it was sized for. The budget was not raised to fit the waste: the 2.28 MB that
was not the town came out first, in the same change. **13 MB is 1.03× the 12.575 MB
measured with the cuts**, 0.425 MB of room. That is deliberately tight. A careless import
the size of the old changelog (1 MB) still breaches it. The programme's remaining household and workplace
records will press on it. The run they press on has a measured lever ready:
`liberties.json` (0.555 MB, below), then the panel files behind it. If the town outgrows
13 MB on scene records alone, the next re-set should first ask whether the
household seats belong in the boot sidecars at all. A card reads them; the scene draws
nothing from them.


**The next cut, named and measured** so the run that meets the next refusal knows where to
look: `data/liberties.json` is **0.555 MB** on the wire and awaited at boot
(`main.js`, `mountLiberties`), although only the Evidence panel and an open provenance
card read it, and the card already redraws when the list arrives late
(`popup.setLiberties`). Loading it on first need is a change to how provenance reaches
the card, and three smoke parts read it synchronously, so it is its own piece of work,
not a rider on this one. **Taken by T-2058 (2026-10-06):** the list is fetched on first need now — Evidence
opened, its liberties topic shown, or a building card drawn (`main.js`
`ensureLiberties`, through `createPopup`'s `onShow`) — and the card redraws when it
lands. The smoke asserts at ready that the handle is still empty. Measured on the
branch, on the steward runner: **13.488 MB across 1446 requests, with no request for
`liberties.json`**. The cut was real; the budget is still breached, because the town
grew about 0.97 MB and 140 requests between T-2047's reading (`cb56e2e4`) and this one.
That remainder is its own ticket, and the budget was not raised to fit it.
**Taken by T-2151 (2026-10-06): the household notes are off the boot path.** Dev @
`08cf2391` measured **13.652 MB across 1474 requests** (the town had grown again since
T-2058's reading). `measure_boot_payload.mjs` now prints a BY FOLDER table beside the type
split, and it answered §4b's question at once: `data/sidecars/1835/` was **4.132 MB** of it,
and the households' `residents[]` were **1.07 MB** of that on the wire. The seat belongs in
the sidecar; the paragraphs do not. A household's `name` and `relation` title the building and
feed the Go-to search, and the card draws its people, roles, grades and basis the moment it
opens, so those stay. The reasoning behind each `why` toggle (each person's `note`, the
household's `why`, and its `research_note`, which no renderer reads) is 0.87 MB that only
an open card ever shows. `publish.sh` now runs `tools/defer_household_notes.mjs`, which ships
each of the 314 seated records slim and writes its households whole to
`sidecars/<scene>/households/<id>.json`. The card fetches that file when it opens
(`main.js` `ensureHouseholdNotes`, through `createPopup`'s `onShow`), hands it to the popup,
which holds it beside the record (the record stays as shipped) and redraws. The source tree is untouched, because two dozen tools read `data/sidecars/` whole.
`defer_household_notes.mjs --check` (in check.sh) holds the shipped form to the source, and
`check_published.mjs` declares exactly the seated records as transformed. Measured on the
branch, on the steward runner: **12.780 MB across 1474 requests**, 0.22 MB inside 13 MB, with
no household file requested at boot; and **12.887 MB across 1500** once T-2148's West blocks
merged beneath it the same hour, 0.11 MB inside. The town is still growing into this budget
faster than its cuts come out of it. The panel files named above are the next lever.
**Taken by T-2315 (2026-10-10): the boot sidecars travel packed.** Dev @ `031535d99`
measured **14.513 MB across 1615 requests**, 1.51 MB over. Bisected on the steward runner,
first-parent over dev: T-2146 (`64e14c76d`, thirteen School Section houses) is the merge that
crossed the line, 12.978 → 13.096 MB. The largest single step since was T-2278 (`ecf8a0195`,
doors and windows on every 1835 building, every structure rebaked): +0.759 MB of `.glb`,
13.535 → 14.294 MB. Neither was waste; the town grew. The waste was in how the records
travelled. Every one of the 686 sidecars was its own request and its own gzip stream, so a
value the town repeats was paid for once per record. And it repeats a lot: 1,505 citations
across 689 records are 58 distinct sources, and the reconstructed roofs share their
attribute reasoning family by family. Nothing could come off the boot path instead: a card
draws its citations and its `why` toggles the moment it opens, and the smoke reads them in
the same tick. So `publish.sh` now runs `tools/pack_boot_sidecars.mjs`. It ships every
string or object of 60+ characters that 3+ records carry once, in
`sidecars/<scene>/boot/shared.json`, and the records fifty to a file in `boot/part-<n>.json`
by index row, each shared value replaced by `{ "$shared": n }`. The shipped `index.json`
gains `boot: { shared, dir, per_part }`, so the loader never probes. `scene-loader.js`
rehydrates each record before anything else sees it, so the registry holds what the record's
own URL holds, key for key. That URL is untouched and still readable (§6). A version-pointed
structure (T-1727) loads its file whole. `pack_boot_sidecars.mjs --check` (in check.sh)
rehydrates every boot copy with the loader's function and compares it to the record. The
sidecar folder went **3.739 MB / 694 requests → 1.269 MB / 23**. Measured on the branch:
**12.044 MB across 944 requests**, 0.96 MB inside 13 MB. The panel files named above are
still the next lever after this one.
Behind it are the other panel files a first visit fetches before
any panel is opened: `reconstruction/1835_address_book.json` (0.161 MB),
`residents/employment_coverage.json`, `reconstruction/1835_population_profile.json`,
`residents/research_pilot.json` (about 0.04 MB each). Minifying the 547 boot sidecars was
measured and is not worth it: gzip already takes the whitespace, and it saves 0.07 MB.

**What the whole-tree cap is now for:** repository hygiene, not visitor cost.
The gate's `SITE_BUDGET_MB` moved 40 → **256 MB** on the same commit — a
quarter of GitHub Pages' documented 1 GB site limit, six and a half times the
38.87 MB the tree carries today — so the tree cannot approach the platform
wall by drift and no one has to buy headroom out of the honesty of the record
again (32 → 36 → 40 were three such purchases). The household cards can grow
tenfold without costing a first visit a byte; the thing that costs every
visitor immediately is the boot payload, and that is what the 13 MB defends.

### 4c. The KTX2 sheets and their transcoder, re-measured 2026-10-16 (T-2582)

T-2582 ships the roof relief maps, the 1904 street surfaces and the ground strip's muck as
GPU-compressed KTX2 (`js/ktx2.js`, `tools/ktx2_sheets.py`). The point is GPU memory, not
wire bytes, and the wire pays for it. Measured with `tools/measure_boot_payload.mjs --check`
on the T-2582 branch: **12.858 MB of 13.000 MB**, 0.142 MB of room. The cost over the image
path, per request, in that reading:

| what | wire | why it is there |
|---|---:|---|
| the four roof sheets as `.ktx2` over their `.webp` | +0.403 MB | UASTC data maps keep 8 bits a texel before Zstandard, where the WebPs were lossless-compressed images (1.139 MB against 0.736 MB) |
| `basis_transcoder.wasm` + `.js` | 0.251 MB | the transcoder, fetched once, the first time a `.ktx2` is asked for |
| `KTX2Loader`, `ktx-parse`, `zstddec`, `WorkerPool`, `ColorSpaces`, `js/ktx2.js` | 0.035 MB | the loader and its imports, gzip |
| **total** | **+0.689 MB** | |

What it buys, from `tools/measure_memory.mjs` with and without `--ktx2-off` on the same
build: the 1835 sheets fall from 21.3 MB to 5.3 MB of GPU memory on a desktop and to
1.3 MB on a phone; 1904's twenty-five fall from 49.3 MB to 3.1 MB on a phone.

**The room this leaves is the tightest the budget has stood.** ETC1S would halve the roof
sheets' bytes, but measured on the shingle ORM it reads 28-32 dB per channel against the
master where UASTC reads 41 dB and up (`tools/ktx2_sheets.py`), and a roof's relief is
what those maps are for. T-2583 (the wall, frontage and signboard sheets) adds more KTX2 to
the 1835 boot and will not fit beside this without a lever: the household seats in the
boot sidecars (§ 4b) are the one already named.

**The walls, re-measured 2026-10-16 (T-2588, the first piece of T-2583): 12.906 MiB of
13.000, +48 KB.** The wall relief's pair ships as KTX2 — the normal on UASTC, and the `orl`
the page used to pack from the `orm` and the basecolor, packed at convert time and put on
ETC1S at its top quality (`tools/ktx2_sheets.py` gives the measurement: 35.5-40.6 dB per
channel, where UASTC would have shipped 1.193 MB for the pair against ETC1S's 0.253 MB). A
KTX2 GPU now fetches three files a substrate in place of three WebPs:

| | before (WebP) | after (KTX2) |
|---|---:|---:|
| hewn log: normal, orm, basecolor → normal, orl | 0.968 MB | 0.644 MB |
| clapboard: the same | 0.433 MB | 0.372 MB, **and the 0.433 MB stays** |
| boot total (`measure_boot_payload.mjs`, same machine, same hour) | 13,484,866 B | 13,532,986 B |

The clapboard's three WebPs stay in the boot because `frontage.js` binds the same sheet
and still packs its grain from them. That is the lever for the next piece: frontage can
bind this KTX2 pair (its grain is a function of the `orl`'s B) and the 0.433 MB leaves the
boot (T-2589). On the phone the walls' maps fall from 5.4 MB of GPU memory to 1.4 MB
(`measure_memory.mjs`, structures' textures 6.7 → 2.7 MB with the roofs' 1.3 MB in both).

### 4d. The frontage timber's KTX2, measured 2026-10-16 (T-2589) — it fits once the walls left the WebPs

T-2589 ships the board face `frontage.js` binds (and the yard goods share) as KTX2: the
`normal_gl` the wall relief already ships (T-2588, one file that both layers bind), and two of
its own, the `orm` (ETC1S, 56 KB) and the grain the layer used to pack on the CPU (ETC1S,
89 KB). The codecs are `tools/ktx2_sheets.py` § THE FRONTAGE TIMBER.

**It did not fit while the walls stayed on their images.** `wall-relief.js` read the same
three clapboard WebPs, so they were fetched anyway and the frontage KTX2s were pure addition.
Measured then with `tools/measure_boot_payload.mjs --check` on one published tree, the
frontage `.ktx2` removed for the before: 12.861 MB before, **13.273 MB after, 0.273 over**.
The budget was not raised for it, because the bytes over were a duplicate and not the town,
and the piece waited for T-2588.

**With T-2588 merged, the frontage was the last layer reading those WebPs.** Once frontage
moves to KTX2 they leave the boot. Re-measured on the merge of this branch with `dev` at
d7dd58ce9:

| reading | boot payload |
|---|---:|
| `dev` (walls on KTX2, frontage on the clapboard WebPs; § 4c above) | 12.906 MB |
| this branch (frontage on the wall's normal plus its own `orm` and grain) | **12.639 MB, within 13.000** |

That is 0.433 MB of WebPs out and 0.144 MB of `orm` and grain in. The shared normal is
fetched once.

What it buys, from `tools/measure_memory.mjs --year 1835 --only mobile` (the before/after on
one tree, taken before the merge): total resident **628.4 → 610.3 MB**; GPU textures 100.9 →
85.9 MB; the frontage layer's textures 16.0 → 1.0 MB and the yard's 14.8 → 4.8 MB;
ArrayBuffers 241.3 → 238.3 MB, because the grain's CPU copy is no longer kept.

A further lever, not taken here: the wall's `orl` already carries what the frontage's two
own sheets do (AO and roughness in R and G, and L / mean in B, from which the grain is
1 + GRAIN_STRENGTH x (2B - 1), over GRAIN_HEADROOM). A frontage shader that read the grain
from the `orl` would fetch no clapboard file of its own and save another 0.144 MB.

### 4e. Signage's wood prepared at convert time, and the sand as KTX2, re-measured 2026-10-16 (T-2590)

`renderers/web/js/signage.js` fetched two 1024² library maps per wood sheet (the signboard
and the heavy timber: basecolor and normal, 612 KB of WebP) only to read each one down to
512², turn it a quarter and, for the basecolor, normalise its grain — on the main thread,
at every boot. `tools/web_textures.py` now writes those four results as DERIVED tiles
(`_grain.webp`, `_normal_turned.webp`, 244 KB together) and holds each pixel-identical to
the transform of its master; the four plain WebPs nothing else loaded are gone. Read in
Chromium against the old in-browser derivation: the normals within one level, the grain
within one level on average (eight at most, of 255) — the area mean of an exact halving
reads the same texels a canvas's half-size draw does.

Measured with `tools/measure_boot_payload.mjs --json`, dev and this branch each published
and read on the same runner: **13,484,865 B (12.860 MB) → 13,120,204 B (12.512 MB)**, the
same 971 requests; WebP 2.010 → 1.646 MB. That is **0.488 MB of room** where § 4c left
0.142 MB, and it is the room the wall sheets' KTX2 (T-2588) was named as lacking.
T-2588 landed first, so the two were measured together after `dev` was merged in:
`measure_boot_payload.mjs --check` reads **12.567 MB of 13.000** across 976 requests, WebP
0.646 MB and KTX2 2.107 MB. That leaves 0.433 MB of room, where T-2588 alone left 0.094 MB.
With T-2589 (§ 4d) merged in as well, re-measured on that merge with `--check`: **12.292 MB
of 13.000** across 975 requests, WebP 0.233 MB and KTX2 2.243 MB, which leaves 0.708 MB of
room where § 4d left 0.361 MB.

The sand's mean luma, which `ground-strip.js` read from the image's pixels, is derived by
`tools/ktx2_sheets.py` into `lake_michigan_dune_sand_basecolor.luma.json` (0.256117, from
every texel of the master; the old 256² canvas read was within 0.3 % of it), and the sand
ships as KTX2 beside the muck. The strip draws only under `?proof=ground`, so neither the
boot payload nor the memory meter's 1835 boot sees it.

**What this piece does NOT move: GPU memory at a normal boot.** The signage library maps
were never uploaded — they are painted into the sign atlas, a canvas built from the town's
own records, and that atlas is the layer's GPU cost before and after. No sheet's GPU
bytes fell, so `tools/memory_ceilings.json` is left where it stands; its lowering is the
wall-relief and frontage pieces' (T-2588, T-2589), which do upload their sheets.

### 4f. The frontage timber ships prebuilt, re-measured 2026-10-16 (T-2677) — and the budget is 20 MB

The owner, on T-2560: *"a big package app download that happens up front so the app is
lightning fast rendering when you are walking or flying"*; that ticket's acceptance asks for
this budget re-measured with the prebuilt files counted. Laying the frontage's boards (1.95 million vertices)
over the terrain was one main-thread task at every boot, the same for every visitor.
`tools/publish.sh` now runs the page's own `createFrontage` in Node
(`tools/prebuild_layers.mjs`, byte-equal to the page since T-2676) and writes
`data/prebuilt/1835/frontage.json` (the index: 0.28 MB) and `frontage.bin.gz`; the page
uploads those buffers instead of building them (frontage.js § THE TOWN'S TIMBER, PREBUILT).

**What the visitor downloads.** Measured with `tools/measure_boot_payload.mjs` on this
branch and on `dev` @ `2bcd059fe`, the same runner: **12.311 MB → 19.010 MB**, 981 → 984
requests; the prebuilt folder is 6.695 MB of it. The buffer is 74.5 MiB raw. It is
gzipped TWICE on disk, because deflate's 32 KB window is far shorter than the runs the timber
repeats over: one pass is 10.76 MB, the second 6.93 MB, a third no smaller. GitHub Pages
serves `.gz` as it is, so 6.65 MB is also what the live origin sends. That is half again what
a first visit carried, on purpose. On the measure tools' slow-phone network (1.6 Mbit/s) it
is about 35 s more download, started as the scene phase ends so it runs under terrain and
buildings, which take 15 s at the phone profile's CPU.

**What it buys**, `tools/measure_boot_phases.mjs --quick --phone` (4x CPU throttle, network
unthrottled, steward runner, one reading per cell; `--no-prebuilt` is the before):

| mobile · light | frontage | longest task in it | boot's longest task | ready |
|---|---|---|---|---|
| cold, built in the browser | 3,209 ms | 3,318 ms | 16,187 ms | 84.3 s |
| cold, prebuilt | 796 ms | 914 ms | 15,816 ms | 80.2 s |
| warm, built in the browser | 3,318 ms | 3,360 ms | 15,805 ms | 85.8 s |
| warm, prebuilt | 753 ms | 884 ms | 15,421 ms | 82.0 s |

The boot's longest task is not frontage's and did not move (it is in `ground`, about
16 s here). The frontage's share is now 0.9 s where it was 3.3 s. The first cut inflated
the buffer on the main thread and gave about a second of that back to `terrain`;
it inflates on a job-pool worker now (`jobs/inflate-kernel.js`).

**The tree.** 74.5 MiB raw would have taken the published tree to 373.7 MiB of its 320.
Gzipped twice it is 6.65 MiB, and the tree reads 305.9 MiB of 320.

**Why 20 MB.** 19.010 MB measured plus about the 0.7 MB of room the 13 MB budget left over
12.3 MB. The rule § 4b set still holds for everything else: a careless import or an
unmetered boot fetch still shows against under 1 MB of room. The next prebuilt layer
(T-2678, the spatial-batch chunks) has to measure its own bytes against this number and
argue its own re-set.

### 4g. The ground ships prebuilt, re-measured 2026-10-17 (T-2693) — and the budget is 29 MB

T-2678's second piece. The 1835 ground was loaded, conformed to the heightfield, cut into
223 tiles and partitioned into 9,405 pieces at every boot. That came to 3.0 s of the
terrain phase at the phone profile (T-2692's reading). `tools/publish.sh` now runs those
same functions in Node (`tools/prebuild_layers.mjs --layer ground`) and writes
`data/prebuilt/1835/ground.json` (the index, 0.80 MB) and `ground.bin.gz` (27.6 MB raw,
10.63 MB gzipped twice). The page batches the pieces and does **not** fetch the ground GLB
(terrain.js § THE GROUND, PREBUILT). Read on the published page, 669 of 669 ground
attributes over 223 tiles are byte-equal to the Node build
(`prebuild_layers.mjs --layer ground --parity --root ../../site/4d`), with zero page errors.

**What it buys**, `tools/measure_boot_phases.mjs --published --quick --phone` (4x CPU
throttle, network unthrottled, steward runner, one reading per cell).
`--no-prebuilt-ground` is the before: the frontage still comes prebuilt and the page cuts
its own ground, which is what dev did.

| mobile · light | terrain | longest task in it | boot's longest task |
|---|---|---|---|
| cold, ground cut in the browser | 8,760 ms | 4,100 ms | 16,504 ms |
| cold, ground prebuilt | 6,172 ms | 4,021 ms | 17,229 ms |
| warm, ground cut in the browser | 8,812 ms | 3,946 ms | 15,775 ms |
| warm, ground prebuilt | 6,050 ms | 4,038 ms | 16,690 ms |

The terrain phase is **2.6 s shorter cold and 2.8 s shorter warm**. Its longest task did not
move: that task is not the ground's cut, which mostly ran on the job pool already (T-2599).
The boot's longest task is not terrain's at all. Its spread between rows (15.8 to 17.2 s)
is the runner's noise on a single reading.

**What the visitor downloads.** `tools/measure_boot_payload.mjs`, the same published tree,
with and without `--no-prebuilt-ground`: **19.109 MB → 28.195 MB**, 992 → 993 requests.
The `.gz` files go 6.694 → 16.831 MB and the `.json` files gain the 0.21 MB index on the
wire. The `.glb` files go 4.885 → 3.628 MB: the published ground GLB is meshopt-packed and
costs only **1.26 MB** on the wire. (T-2692's reading guessed the prebuild could replace a
30.5 MB GLB. That figure was the source GLB in `assets/`, and the page never fetches it.)
So this is a trade of about **9.1 MB more on a first visit for 2.6 s less CPU** at the phone
profile. On the measure tools' slow-phone network (1.6 Mbit/s) that is about 48 s more
download. The download starts before the scene phase, so it runs under scene and buildings.
A warm visit, or a kept year (T-2561's pack holds `data/prebuilt/1835/`), pays nothing.

**Where the trade is refused.** A visitor who has asked to save data, or whose browser rates
the connection 3G or slower (`navigator.connection`), is never offered the prebuild. The
page fetches the 1.3 MB GLB and cuts the ground itself.

**The tree.** `tools/site_budget.py`: 289.730 MB of 320, 30.270 MB of headroom, with the
ground's 11.42 MB in it.

**Why 29 MB.** The owner, on T-2560, asked for *"a big package app download that happens
up front so the app is lightning fast rendering when you are walking or flying"*. The
ground was the next 3 s of that boot (T-2692). The number is the 28.195 MB measured plus
about the 0.8 MB of room the 20 MB budget left. § 4b's rule still holds for everything
else: a careless import or an unmetered boot fetch shows against under 1 MB of room.
**The next lever is bytes, not CPU.** The prebuild ships every vertex as float32 because
batching copies them as they are. A format that ships only the partition and lets the page
gather from the 1.26 MB GLB it already conforms would give most of the 9.1 MB back. That is
written up on T-2694, the town's other spatial-batch callers, which has to measure its own
bytes against this number and argue its own re-set.

## 5. What the gate does now

- **Refuses** over 320 MiB (T-2595; measured re-budgets in §8 and §9) — the repository-hygiene guard, not the visitor-cost
  budget; the visitor-cost budget is the 29 MB boot payload budget in § 4,
  enforced by `tools/measure_boot_payload.mjs --check`. The gate names
  `tools/site_budget.py` in the message so the next run does not have to invent
  the report again.
- **Warns at 90 %**, with the headroom in MB. Until T-0722 nothing said a word until the
  tree was already a wall, and the run that discovered it was a run whose finished work
  could not merge. The warning is advisory by design: it is meant to reach the queue while
  there is still room to answer it. It fires today, at 95.9 %, and it should.
- **Refuses any two files in the mirror with identical content over 64 KB.** A duplicate is
  not a judgement call the way a large file is — one of the two is the file and the other
  is waste, and the answer is always a re-export, a redirect or a deletion. This class of
  waste cost 4.1 % of the budget silently for as long as both paths existed; it cannot come
  back the same way.

## 6. The next lever, measured but not pulled

Minifying the mirror's JSON — the published copies only, which are generated rather than
authored — was measured at **1.99 MB** across 1,831 files. It is not done here: it would
make the published record unreadable at its own URL, and this project publishes records
people are meant to be able to open. It is a decision about what the mirror is for, which
is the owner's, so it is a ticket and not a quiet optimisation.

## 7. The same bytes across the tree's edge — T-1828

On 2026-10-01 T-1821's Prairie Avenue image collection took the tree to **287.0 MB** of
256, and dev's gate went red with every PR behind it. `site_budget.py --dupes` saw
nothing, because it walks `site/4d/` only — and the duplicate was across that edge:
publish.sh copies the two reference browsers (`prairie-1904/`, `pre-fire/`) into the
mirror for the dev preview, while the site root already publishes their production
copies from the tracked `site/prairie-1904/` and `site/pre-fire/`. **91.7 MB** of the
mirror was byte-identical to a file at the same path under the root.

`tools/serve_from_root.py` (run by publish.sh, self-tested in check.sh) removes an asset
directory from the mirror only when **every** file in it is identical at the root, and
writes `viewer/root-served.js` so the viewer reads that directory from `/<app>/`. A
directory holding anything the root lacks stays whole — T-1821's
`research/images/files/` stays today, and moves by itself once the production copy is
refreshed to hold it. Result: **196.3 MB**, 76.7 % of budget, 59.7 MB of headroom.

The cost, stated: the root is deployed from `main`, so `/4d/dev/` previews a moved
directory at main's bytes until the next promotion. Viewer code and data never move.

## 8. Detailed Glessner surfaces — measured storage allowance, T-2226

The first full preflight refused the new surface pass at **262.262 MiB** against
256 MiB. The original 1024-pixel joint maps add **7,413,840 bytes** across the
Full and Light assets; their geometry counts remain unchanged. The complete gate
reported this as its sole failure in 890 steps. This failure is retained in the
T-2226 evidence and is not described as an initial green run.

`site_budget.py` finds no identical-file waste over 64 KiB. A read-only price of
minifying every published JSON file saves **5.435 MiB**, insufficient to cover the
6.262 MiB overrun; the readable-record decision in §6 remains untouched. The
reviewed material maps and all public research records are preserved.

The whole-tree **repository-hygiene** allowance is now **288 MiB**, with
**25.738 MiB** of measured headroom. The 90% warning still fires on this tree, and
the duplicate-content guard is unchanged. This is a declared storage re-budget,
not a change to the visitor boot allowance, Full/Balanced/Light scene limits or
the 200,000-triangle Light house ceiling. T-2227 still owns the recorded scene
performance failures and the added asset-transfer cost.

This checkout carries 129.136 MiB outside `site/4d/`; two full 288 MiB app
allowances plus that measured content total **705.136 MiB**, below the 1 GiB
platform limit recorded in §4. That is a capacity calculation using the current
checkout, not a claim that both deployment branches were rebuilt here. Future
changes still need their own gate and measured visitor costs. Exact byte counts,
alternatives and limitations are in
`docs/RESEARCH/glessner-finish-T-2226/site-budget-reprice.json`.

## 9. The Prairie houses in KTX2 — measured storage allowance, T-2595

T-2595 re-encodes the images in the 20 textured Prairie house web GLBs from JPEG to
KTX2 (`tools/ktx2_glb.py`, run by `tools/web_derivatives.sh`): UASTC level 2 with RDO
and zstd 18 for normal maps, ETC1S for colour, the recipe `tools/ktx2_sheets.py` uses for
the library sheets. The point is the phone's GPU memory, and the wire pays for it.

| | before (JPEG) | after (KTX2) |
|---|---:|---:|
| the 20 derivatives on the wire | 28,806,824 B | 53,759,924 B (+23.797 MiB) |
| their textures on a phone's GPU, by format (RGBA8 + mips → ETC2/ASTC + mips) | 1,074.6 MiB | 159.3 MiB (6.7×) |
| the published tree | ≈ 274.2 MiB | 297.968 MiB |
| `/1904/` on the phone at spawn, GPU textures, `tools/measure_memory.mjs` with and without `--ktx2-off` on one build | 510.2 MB | 384.0 MB |
| the same, whole resident estimate | 1,329.4 MB | 1,105.6 MB |

The by-format figure counts every texture of every house; the meter counts only what the
GPU was asked to upload, which at spawn on Prairie and 18th is the houses in view. Of the
126.2 MB the meter sees fall, 46.2 MB is the library sheets `--ktx2-off` also turns back
into images (T-2582's, already shipped), so about 80 MB is these houses. The 1904 phone
ceiling in `tools/memory_ceilings.json` comes down 1,450 → 1,225 MiB by its own rule,
and the desktop one 2,175 → 1,750 MiB (desktop reads 1,587.5 MB, zero page errors).

Every derivative is still smaller than its master (assertion 6 of
`tools/measure_web_derivatives.py`). Rendered at each house's reference camera from
the old and the new derivative, the ten houses that have one read 41.7-51.9 dB PSNR, the
difference visible only at 8× gain on the brick colour.

**Why not ETC1S for the normal maps too.** On one 1024² sandstone normal map (463 KB as
JPEG): UASTC with RDO is 1.14 MB at 39.2 dB, UASTC at RDO λ 4 is 919 KB at 37.1 dB, and
ETC1S at qlevel 255 is 218 KB at 31.4 dB. ETC1S would pay for itself on the wire and cost
the relief the maps exist for; the roof sheets were refused ETC1S on the same reading
(§4c). gltf-transform's own `uastc` command never applies RDO to a normal map, which is
why the encode is a tool of ours: through the CLI the same 20 houses came to 67.9 MB.

The whole-tree **repository-hygiene** allowance is now **320 MiB**, with **22.032 MiB**
of headroom. Two 320 MiB app allowances plus the 129.136 MiB of other site content total
**769.136 MiB**, below the 1 GiB platform limit. The 13 MB boot payload is untouched: no
textured house is in the 1835 boot. T-2596 (the Glessner v4 set in KTX2) has handed
some of it back, measured: the full derivative 59,126,156 → 43,829,952 B and the light
32,534,812 → 15,521,960 B (its 37 textures capped at 1024), 32,309,056 B (30.81 MiB) off
the published tree, which then read 268.87 MiB of 320 (51.13 MiB headroom). The
three-file recovery package went 152,421,884 → 120,457,725 B (25 parts → 20). Rendered
from the five reference cameras, old files against new, the re-encode reads 36.7–45.4 dB
PSNR, texture grain only (docs/RESEARCH/ktx2-v4/glessner-v4-ktx2.json).

## 10. Texture residency — T-2598

The bytes above are what a visitor downloads; this is what a phone keeps on its GPU
once they are open. Each house picture a GLB brings in is resident only within its
tier's reach of the eye and under its tier's budget, nearest first
(`renderers/web/js/texture-residency.js`, `RESIDENCY`); farther off it draws a
64-texel stand-in of itself in the same slot, so no shader recompiles.

| tier | enter | leave | budget | uploads a frame |
|---|---|---|---|---|
| full, balanced | 160 m | 200 m | 512 MiB | 16 MiB |
| light (a phone) | 70 m | 90 m | 256 MiB | 4 MiB |

The budgets come from the Prairie Avenue walk
(`node tools/measure_memory.mjs --walk prairie`, eight stations, N -3270 to N -2990):

- **phone, at the figures above** (`docs/measurements/T-2598-walk-mobile.json`):
  residency held 90.5–256.0 MiB, never over; the GL meter's textures peaked at
  **316.1 MB**, against **456.0 MB** at spawn before residency (T-2546) and 414.0 MB
  with the budget lifted at a 90/120 m reach (`T-2598-walk-mobile-reach.json`).
  At the 1800 block the reach asks about 352 MB, so the budget turns the farthest
  pictures in reach away there.
- **desktop, budget lifted** (`T-2598-walk-desktop-reach.json`): every one of the 61
  house pictures (477.2 MB) is within 200 m of the walk's middle, so 512 MiB keeps all
  of today's houses resident there and holds the line as more are refined. 384 MiB was
  tried first and turned near houses away; it was raised rather than shipped.

Captures (`--captures`, `T-2598-captures-mobile.json`): at four Glessner stands on
the phone, the frame with every picture forced resident differs from the working
frames by less than the scene's own motion between them (2.8 / 21.1 / 11.8 / 17.5 %
of pixels against 3.7 / 30.4 / 17.5 / 22.3 %). The aerial stand, the street-eye
stands and the moving p95 frame time are not yet read; the steward runner's
SwiftShader draws one frame in seconds, so the p95 needs a GPU.
