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
PUBLISHED TREE  site/chicago/4d
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

**The boot payload budget is 12 MB.** That is 1.66× the measured 7.223 MB:
tight enough that a careless import into `walk/js/` or an unmetered new boot
fetches cannot accumulate silently (each is visible against 60 % spent), and
loose enough that the growing town — South Through Time is ahead, and every
new 1835 structure adds boot GLBs — does not force a re-budget every quarter.
Re-measure and check with:

```
bash tools/publish.sh                      # build the mirror the visitor gets
node tools/measure_boot_payload.mjs        # the report above
node tools/measure_boot_payload.mjs --check  # exit 1 past the 12 MB budget
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

**What the whole-tree cap is now for:** repository hygiene, not visitor cost.
The gate's `SITE_BUDGET_MB` moved 40 → **256 MB** on the same commit — a
quarter of GitHub Pages' documented 1 GB site limit, six and a half times the
38.87 MB the tree carries today — so the tree cannot approach the platform
wall by drift and no one has to buy headroom out of the honesty of the record
again (32 → 36 → 40 were three such purchases). The household cards can grow
tenfold without costing a first visit a byte; the thing that costs every
visitor immediately is the boot payload, and that is what the 12 MB defends.

## 5. What the gate does now

- **Refuses** over 256 MB — the repository-hygiene guard, not the visitor-cost
  budget; the visitor-cost budget is the 12 MB boot payload budget in § 4,
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
