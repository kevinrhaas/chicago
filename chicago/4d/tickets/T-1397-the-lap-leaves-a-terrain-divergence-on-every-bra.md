---
id: T-1397
title: The lap leaves a terrain divergence on every branch it laps: two unrelated PRs carry a byte-identical river, hydrology and landings diff against dev and fail the same four terrain gates, and neither side re-derives back to the other
state: done
epic: META
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-19
pr: 1530
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T17:42:42.270Z
claimed_run: null
---

The lap leaves a terrain divergence on every branch it laps: two unrelated PRs carry a byte-identical river, hydrology and landings diff against dev and fail the same four terrain gates, and neither side re-derives back to the other.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**THE MEASUREMENT (2026-09-19).**

Two pull requests that share NO commits — #1518 (`steward/t-1372-hulls-in-port`) and #1521
(`steward/t-1377-free-black-1835`) — carry a BYTE-IDENTICAL diff against `dev` over
`chicago/4d/data/terrain/` and `chicago/4d/data/wharves/`. The sha256 of
`git diff origin/dev...<branch>` over those paths is `4637a39c77c10865` on both.

On each branch the commit that introduces it is the lap's:

```
#1518   15d4a9222  Lap onto dev: generated files regenerated, not merged
#1521   52b9939e4  Lap onto dev: generated files regenerated, not merged
```

It is a real geometry change and not a formatting or precision artefact —
`data/wharves/river_landings.json` moves `vertices` 88 -> 92 and `length_m` 2932.6 -> 2952.0,
and `river.geojson` moves 694 lines.

**IT BREAKS FOUR GATES ON EVERY BRANCH THE LAP TOUCHES.** #1518 and #1521 fail the identical
four, neither of them anything to do with the ticket being worked:

```
* dataset (schema, provenance, date gates, licenses, staleness, publish)
* the NA re-read of the north-side slough still lands on the committed centreline
* the frontage works re-derive from the rule that chose their walls
* West Water still stands one half-corridor off the bank, and the two refusals still hold
```

`dev` itself is green — gate `success` on `3845cb41c`, `a2afbecae` and `08d8cf094`.

**THE THREE DIRECT GENERATORS REPRODUCE `dev` EXACTLY.** `generate_frontage_works.py`,
`generate_river_wharves.py` and `derive_north_water.py`, run against a clean `dev` checkout,
change ZERO files. So the committed terrain is reproducible from its own generators and `dev` is
not carrying a stale artefact.

**WHY THIS MATTERS MORE THAN THE TWO PRs.** The lap runs on every open pull request. Any branch
it laps acquires this diff and fails these four gates, regardless of what the branch is for. It
manufactures red gates across the whole queue, and each one costs a human the work of deciding
whether the failure is the branch's own — which is exactly the misattribution this ticket's
filer made on #1518 before checking `git log` on the file (corrected at
https://github.com/kevinrhaas/custom/pull/1518#issuecomment-5743234204).


**WHAT IS ESTABLISHED, AND WHAT IS NOT.** Stated separately on purpose, because the filer got
this wrong once already by inferring a cause from partial evidence.

ESTABLISHED, each by a command run today:

1. The two branches' terrain diffs against `dev` are BYTE-IDENTICAL (sha256 `4637a39c77c10865`
   over `data/terrain` + `data/wharves`), and the branches share no commits.
2. On each branch the introducing commit is `Lap onto dev: generated files regenerated, not
   merged` — `15d4a9222` on #1518, `52b9939e4` on #1521.
3. `dev` REPRODUCES ITSELF. `node tools/rederive.mjs --run` over all 151 steps on a clean `dev`
   checkout changes ZERO files under `data/terrain` or `data/wharves`. So do
   `generate_frontage_works.py`, `generate_river_wharves.py` and `derive_north_water.py` run
   directly, and so do `compile_scene.py --all` and `resolve_id_collisions.mjs`.
4. THE BRANCH ALSO REPRODUCES ITSELF. Running those same three generators on #1518's branch
   changes ZERO files, and the branch still differs from `dev` by the same three afterwards.
5. So both trees are self-consistent and disagree with each other, and nothing in the manifest
   moves either one toward the other. This is a committed divergence that no re-derive corrects.
6. `dev`'s gate is green (`3845cb41c`, `a2afbecae`, `08d8cf094`); the lapped branches fail four
   terrain gates that `dev` passes.

NOT ESTABLISHED, and this ticket's first job:

- **WHICH tree is right.** The gates pass on `dev`'s terrain and fail on the branches', which is
  evidence for `dev` but is not proof — the gates' own committed references could be the stale
  thing. Decide it on the sources, not on which one is greener.
- **HOW the lap produced a terrain change that nothing reproduces today.** The regeneration must
  have run against inputs that no longer exist in that state. Until that is known, the same lap
  can mint the same fossil again on the next branch.

**A SEPARATE FINDING FROM THE SAME RUN, worth its own attention:** the clean-`dev` re-derive
changed exactly one file — `data/reconstruction/1835_reconstruction_order_book.json`. `dev` is
therefore carrying an order book that does not re-derive from its own inputs. It is not what
breaks the terrain gates and it is not this ticket, but it is a committed derived file out of
step with its generator on the integration branch, and somebody should look at it.

1. The question "which terrain is correct" is answered from the sources and WRITTEN DOWN, and
   the losing tree is corrected — either `dev`'s terrain is rebuilt and the gates' references move
   with it, or the branches' fossil is reverted and the lap is stopped from re-minting it.
2. The mechanism is found and closed. A lap that can commit generator output which no later
   re-derive reproduces will do it again; naming the trigger is what makes this ticket stay
   closed. If the trigger cannot be reproduced, say so in writing and gate against the SHAPE
   instead — see 3.
3. **The lap does not commit regenerated files that the gate has not passed.** Its own note says
   "gating is CI's — every push above re-runs the gate", and that is what leaves a red branch
   behind with nothing to roll it back. Whatever this unit does, a regeneration that breaks a gate
   must not survive as a commit on the branch.
4. Demonstrated on a reconstruction, not asserted: a branch lapped after the fix does not acquire
   a terrain diff, and #1518 and #1521 go green on those four gates without their own work being
   touched.
5. The cost is stated. Every branch the lap touches inherits four red gates that have nothing to
   do with its ticket, and each one costs a person the work of deciding whether the failure is the
   branch's own. On 2026-09-19 that cost this filer a wrong public attribution on #1518 before
   `git log` on the file corrected it.

---

## WORKED 2026-09-19. The answer to both open questions, and the fix.

### A CORRECTION FIRST — two of the ESTABLISHED items above are wrong

Item 3 said `dev` reproduces itself and item 4 said the branch does too, each from
running `generate_frontage_works.py`, `generate_river_wharves.py` and
`derive_north_water.py`. **None of those three owns `river.geojson`.** All three READ
it, so of course each tree is a fixed point for them — a fossil river yields fossil
landings, consistently. The tool that owns the file is `tools/trace_river.py`, and it
was never run. Run now, it settles the question in one command:

```
dev     python3 tools/trace_river.py --check   ->  OK   river.geojson   OK   hydrology.geojson
branch  python3 tools/trace_river.py --check   ->  DIFF river.geojson            (rc 1)
```

Same inputs on both — same 8-GCP affine, same 17.5 m RMS, same 68-vertex water ring,
same 45-point slough. The generator produces ONE answer and it is dev's.

### 1. WHICH TREE IS RIGHT — dev's, and it is decided on the source

`river.geojson` records the sha256 of the image region it was traced from, and the two
trees name different images:

```
dev      3eae241663a2f25276bee8b7bb20235c9ade43b93da3180f2094304c34d3376d   263,865 B
branches 23e14995db4925d9b4dbbd98b8531d77195e18b05a30bb65ae78e1d140e18563   231,112 B
```

The file had been saying this all along. Nothing read it.

Both are the same IIIF region — `commonwealth:js957744g`, box `868,1252,1120,1120`.
**The Boston Public Library re-encoded it** between 2026-09-18 17:43 (the timestamp on
a surviving `/tmp` copy of the old bytes) and 2026-09-19. Five consecutive fetches
today returned `23e14995` byte for byte, so this is a re-encode upstream and not a
flapping edge cache.

Dev's reading is the right one, on four grounds, none of which is "it is greener":

1. **It is the less lossy scan** — 33k more JPEG for the same 1120×1120 box. A grey
   bank-wash segmentation is exactly the kind of read that compression artefacts move.
2. **It reads cleaner.** The pinned bytes give a 69-vertex water ring; the re-encode
   gives 100 for the same bank, and shifts `south_branch` drafted width 57.3 → 57.4 m.
3. **It is the encoding the rest of the sheet is still served at.** Four other regions
   of the same image are read by this project, and all four still match their committed
   readings byte for byte (checked live today): the north branch reach `109d0a8b`, the
   south branch reach `2f542115`, the east edge `4a69980d`, the legend `49004ba3`.
   Only the forks moved.
4. **The splice.** `branches.geojson` joins `river.geojson` at BPL master rows 1252 and
   2372, and the branch windows are still on the old encoding. Re-tracing the forks
   alone puts the two sides of that join on different scans — which is precisely what
   the gates said: *the NA re-read of the north-side slough still lands on the committed
   centreline*, *the frontage works re-derive from the rule that chose their walls*,
   *West Water still stands one half-corridor off the bank*.

### 2. HOW THE LAP DID IT — an unpinned network read inside a manifest step

`tools/trace_river.py` is one of the 152 steps in `tools/derived_manifest.json`.
`.github/steward/pr-lap.sh` runs `node tools/rederive.mjs --run` **on every merge**, and
`.github/workflows/chicago-4d-pr-lap.yml` line 65 `pip install`s numpy, scipy and
Pillow — so the trace runs live on the lap runner, every time.

And `fetch_region` was this:

```python
if cache.exists():
    raw = cache.read_bytes()
else:
    raw = urllib.request.urlopen(url, timeout=180).read()
    cache.write_bytes(raw)
return raw, hashlib.sha256(raw).hexdigest()
```

The sha256 was computed, written into provenance — and **never compared to anything**.
It was a label, not a gate. So on the first lap after the re-encode the tool re-traced
the Chicago River from different bytes, `rederive.mjs --run` reported success, and the
lap committed it. Every branch lapped since inherited it.

**Seven manifest steps reach the network.** Any of them could have done this.

This also explains the thing that looked impossible — two self-consistent trees. My own
local runs agreed with dev because this box had a `/tmp/wright_1834_forks_region.jpg`
cached on 2026-09-18, and `fetch_region` preferred the cache unconditionally. The
sandbox was reading yesterday's internet.

### 3. THE FIX — a trace may not read bytes it was not made from

- **`data/traces/pinned_sources.json`** (new, authored). The five remote regions this
  project traces, each pinned by the sha256 and byte count of the bytes its committed
  reading was made from, with its readers, what stands under it, and whether upstream
  still serves it.
- **`tools/pinned_sources.py`** (new). The one fetch the pinned traces share. Cache
  and network are both held to the pin — the cache too, deliberately, because a stale
  `/tmp` file is what made dev look self-reproducing.
- **Two kinds of move, two exit codes.** A move *nobody has ruled on* is RED: the tool
  refuses, `rederive.mjs --run` fails, and the lap aborts and leaves the branch alone
  instead of committing a re-trace. That is acceptance 3, at the root — the lap cannot
  commit an ungated regeneration if the generator will not produce one. A move the
  register *has* ruled on DECLINES: writes nothing, says so, exits 0. Without that
  second case this fix would stop every lap in the queue over a fact already written
  down.
- **`trace_river.py`, `trace_shoreline.py`, `read_north_branch_bank_wash.py`** fetch
  through it. `trace_north_branch.py`, `trace_south_branch.py` and
  `measure_north_branch_banks.py` are pinned by the same change without a line of their
  own: they set `tr.REGION` and call `tr.fetch_region`, which is the shared
  implementation.
- **Gated offline**, like `refetch_control.py` and for the same stated reason — a commit
  gate may not need the network. `--check` holds the register to the shas the committed
  readings record in their own provenance (the assertion that would have caught this on
  the commit that made it), and holds every manifest step that can reach the network
  either to fetching through the module or to an enumerated offline command. The two
  exempt steps read an Internet Archive `djvu.xml` behind `--fetch`/`--map` and are run
  by the manifest as `--build`, which rebuilds offline from committed text; the
  exemption is written down and the manifest is held to it, so a third tool joining
  them is red. `--verify-upstream` is the online half, by hand.

### 4. DEMONSTRATED, NOT ASSERTED

With the pinned bytes removed from the cache, so the tool fetches what the server
actually serves today:

```
REFUSING / DECLINING ... pinned 3eae2416... (263,865 bytes)
                         received 23e14995... (231,112 bytes)
  NOT re-tracing and NOT writing.
git status -- data/terrain   ->  (empty)
```

Before this change, that same run rewrote `river.geojson`. With the pinned bytes
restored at the cache path, `trace_river.py --check` returns **OK** on both files — so
the pin does not cost the reading its reproducibility, it costs it only the ability to
be rewritten by bytes nobody chose.

**#1518 and #1521 are clear.** Six files restored on #1518 (two lap commits: `15d4a9222`
and `78ea18fff` — the earlier one had also taken `data/frontage/river_walk_frontage.json`,
`data/traces/north_side_slough_na_reread.json` and
`data/traces/wright_1834_watercourse_audit.json`, which the measurement above missed
because it only looked at `data/terrain` and `data/wharves`), three on #1521. All four
named gates pass on both, run directly, with neither PR's own work touched.

### 5. WHAT THIS COSTS, STATED

**The forks reading is no longer re-derivable from the live source.** The bytes it was
made from exist, today, only as a `/tmp` cache on one sandbox that will be reclaimed.
This project commits no copies of the BPL rasters — `data/sources/wright_1834.json`
declares `asset_use: geometry`, a deriving use, not a licence to redistribute the scan —
so restoring re-derivability is a decision for the owner, not something to take here.
The pin makes the remedy cheap and safe whenever it is taken: drop a recovered copy at
`/tmp/wright_1834_forks_region.jpg` and the reader proves it is the right bytes before
it reads one pixel. Until then `--check` prints the NOTE on every gate run, so the fact
is stated rather than forgotten.

### A STANDING FINDING, unchanged by this work

The clean-`dev` re-derive still moves exactly one file,
`data/reconstruction/1835_reconstruction_order_book.json` (336 lines on the lap
commits). It is not terrain, it is not what broke these gates, and it is not this
ticket — but `dev` is carrying an order book that does not re-derive from its own
inputs, and somebody should look at it.
