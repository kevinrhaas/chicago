---
id: T-0015
title: Does the AO bake earn its nightly
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: M
legacy_id: B-A1
parent: null
opened: 2026-08-17
closed: 2026-08-23
pr: 327
claimed_by: run 8/23/2026, 8:12:16 AM CT
blocked_on: null
needs_bake: false
---

Does the AO bake earn its nightly? Measure what AO actually contributes to the shipped
frame vs what the nightly costs. Deep history: § B-A1 (~8434).

**Acceptance:** a measured yes (keep, with numbers) or no (retire the step, with numbers).

---

## MEASURED 2026-08-23 — the answer is NO, and the question had a false premise

**There is no nightly AO cost to earn.** `--ao` is opt-in on `generators/build.py`
and *nothing passes it*: not `tools/bake.sh` (which forwards `"$@"`), not
`chicago-4d-bake.yml` (`./tools/bake.sh` and `./tools/bake.sh --only …`), not
anything else in the repo. The flag has been opt-in-and-never-opted-in.

| the ticket asks | measured |
|---|---|
| what AO contributes to the shipped frame | **nothing** — 0 of 345 master GLBs carry an `occlusionTexture`; every manifest entry that records the field says `baked_ao: false` (251 false, 94 absent, 0 true) |
| what the nightly costs for it | **nothing** — the nightly never bakes AO |
| what it *would* cost | **+137 %** build time on one asset: 1,457 ms → 3,454 ms (`sauganash_hotel`, direct Blender, 512×512, 48 samples), and **+4.4 %** file size, 94,420 → 98,580 bytes. Across 345 assets that is roughly **+11 minutes** of nightly |
| what it *would* contribute | **less than nothing today** — see below |

**And it has broken while nobody was running it.** The bake itself still works —
in memory the AO reads min 0.000, max 1.000, **mean 0.2158** over 262,144 texels,
which *corroborates* the docstring's long-standing "mean 0.265, too dark, it is a
geometry problem" rather than contradicting it. But the texture that reaches the
GLB is **entirely black, min 0 and max 0**, confirmed with two independent PNG
decoders. Switching `--ao` on today would not ship the too-dark AO the docstring
warns about; it would ship a fully-occluded one, and `assets/manifest.json` would
record `baked_ao: true` for it.

### What was done about it

Nothing was retired. Deleting `--ao` would foreclose the low-poly AO cage the
docstring describes as the real fix, and that is a direction call rather than a
measurement.

**Shipped here:** this measurement; **T-0158** for the export loss, carrying the
eliminations already done so nobody repeats them (it is not the object's
selection state); and a correction to `tools/bake.sh`'s header, which said
`--no-bake` skips "AO baking" and so read as though AO were on by default.

### What was written, demonstrated, and then deliberately NOT shipped

`assert_ao_survived_export()` — a guard that refuses a GLB whose occlusion
texture carries no occlusion, checked on the **exported bytes** rather than on
the in-memory image, because memory is not where this breaks. It was written,
and demonstrated firing (`rc=1`) on the real asset with the default path
untouched (`rc=0`). It is not in this change, and the reason is **T-0139**:

`generators/mesh_inputs.py` hashes `build.py`'s BYTES into every asset's
`inputs_sha256`, so editing it — even a comment — stales the whole town. The
full rebake was run (343 assets, 95 changed bytes, the rest byte-identical) and
it healed everything **except** `cook_county_courthouse_1835__wood_1835.glb`,
which the bake cannot reach because its only phase runs 1835-10-01 to 12-31 and
the scene targets 1835-07-01. That is precisely T-0139, whose own text says the
previous run got past it "with a throwaway script that monkey-patched
`resolve_phase` — which is exactly the shape of thing that should not be needed
twice."

This is the second run to hit it. Using the workaround again would have made the
thing T-0139 warns about routine, and fixing T-0139 is a different ticket with
its own acceptance. So the guard and the docstring correction wait for T-0139,
and belong naturally to whoever takes **T-0158** — fixing the export means
touching `build.py` and rebaking anyway.

**Evidence for T-0139's priority:** it has now blocked two separate runs, and it
blocks *any* edit to `build.py`, including a one-line comment.

### The decision left to the owner

Retire-or-fix is genuinely open and is not the loop's call: **T-0158** fixes the
export, and the AO cage remains the documented plan for making AO worth having
at all. What is now settled is that the current path earns nothing, costs nothing
because it never runs, and can no longer fail quietly.
