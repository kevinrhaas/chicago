# The closing convergence rebuild

*Derived — regenerate with `python3 tools/rebuild_closing_set.py --build`; `tools/check.sh` re-derives it. T-1333, as of 2026-09-18.*

Five derived files close the resident layer. This page is the one place that says they are a set, what order they rebuild in, and — as measured deltas against a frozen baseline, never as a spot reading — what the last rebuild moved.

```
python3 tools/rebuild_closing_set.py --rebuild
```

## 1. The set, and the order it rebuilds in

The order is read out of `tools/derived_manifest.json`, which holds the whole derived layer in dependency order; the closing set is a subsequence of it. A member whose tool is not a manifest step fails `--check`.

| # | member | rebuilt by | manifest step | files the lap may rebuild |
|---|---|---|---|---|
| 1 | `data/residents/index.json` and its `merged` redirect table | `tools/rebuild_resident_index.py` | 73 | 1 |
| 2 | the 1835 sidecars, `data/sidecars/1835/` | `tools/compile_scene.py` | 122 | 1 |
| 3 | the town census, `data/town_census.json` | `tools/town_census.py` | 141 | 1 |
| 4 | the final resident audit, `chicago/reference/resident-research/final/audit/` | `tools/export_resident_audit.py` | 143 | 3 |
| 5 | the published residents, `site/chicago/4d/data/residents/` | `tools/publish.sh` | **none** — see §2 | 0 |

## 2. What the manifest does not own

Acceptance 5 of T-1333: a file in this set that `tools/derived_manifest.json` does not own is a finding, not a footnote. Two of them, both measured.

**The mirror.** The mirror is generated and untracked (T-0938), so no merge can ever conflict in it and the lap has nothing to resolve; `tools/publish.sh` writes it, `tools/check.sh` publishes it as its first step, and `tools/check_published_residents.mjs` asserts the shipped value equals its source, file for file.

That one is a property of the mirror rather than an oversight — it is the one member `tools/rederive.mjs` will never rebuild, and it has nothing to rebuild. `--check` holds the exemption to this written reason, so deleting the reason is as red as deleting the file.

**The sidecars, and it is a real gap.** A member's tool writes a footprint; the manifest claims a subset of it, and only a claimed file can have a merge conflict cleared by rebuilding. Everything else is refused to the run that owns the ticket — safe, and it is the state that leaves a PR open.

| member | tracked files written | claimed by the manifest | unowned |
|---|---:|---:|---:|
| `data/residents/index.json` and its `merged` redirect table | 1 | 1 | 0 |
| the 1835 sidecars, `data/sidecars/1835/` | 421 | 1 | 420 |
| the town census, `data/town_census.json` | 1 | 1 | 0 |
| the final resident audit, `chicago/reference/resident-research/final/audit/` | 3 | 3 | 0 |

420 tracked closing-set file(s) are written by a manifest step and not claimed by it — in `sidecars_1835`. Widening `resolves` to the whole sidecar directory is a decision about what the lap may overwrite, not a bookkeeping fix, and the manifest is explicit that "being run by the manifest and owning your outputs are separate decisions" — so this states the number rather than taking that decision. The row moves the moment the count does.

## 3. The deltas

Baseline: `07605197356ccd8d8b4f547eccb2d1dc619ef06f` on `dev`, taken 2026-09-18 — the tree T-1333 opened on. The baseline is measured once and committed; a value here that is not `0` is what the closing rebuild moved.

| measured | baseline | now | delta |
|---|---:|---:|---:|
| households in `index.json` | 1258 | 1393 | +135 |
| household cards on disk | 1258 | 1393 | +135 |
| persons in `index.json` | 1288 | 2265 | +977 |
| rows in the `merged` redirect table | 66 | 66 | 0 |
| redirects that do not arrive | 0 | 0 | 0 |
| persons graded `attested` | 410 | 410 | 0 |
| persons graded `inferred` | 875 | 875 | 0 |
| persons graded `reconstructed` | 3 | 980 | +977 |
| 1835 sidecar files | 391 | 421 | +30 |
| people in the 1835 people sidecar | 1288 | 3202 | +1914 |
| buildings standing in the town census | 371 | 401 | +30 |
| people housed in the town census | 34 | 181 | +147 |
| households housed in the town census | 20 | 31 | +11 |
| rows in the final resident audit | 1288 | 2265 | +977 |
| published resident files in the mirror | 1336 | 2152 | +816 |

## 4. T-1144's banked acceptances, as deltas

T-1144 banked acceptances 3, 5 and 9 to this pass "to state as deltas rather than claimed closed from a spot reading". Each is measured here on both trees, so a later branch that reintroduces one turns the gate red.

| measured | baseline | now | delta |
|---|---:|---:|---:|
| acc. 3 — Mary Durbin, John Simmons, John Vincent or Logdson in the layer | 0 | 0 | 0 |
| acc. 5 — standing 1835 trades cited to no 1835 source | 0 | 0 | 0 |
| acc. 9 — uncertain presences | 820 | 820 | 0 |
| acc. 9 — …of them carrying a dated evidence leg | 820 | 820 | 0 |

Acceptance 9 reads as a pair: 820 of 820 uncertain presences carry a `last_dated_appearance`, so the gap is 0.

## 5. What holds this page

`python3 tools/rebuild_closing_set.py --check` runs in `tools/check.sh` and asserts three things: every member is rebuilt by a manifest step or carries a written exemption, every member's tool is gated with `--check` by `tools/check.sh`, and this page re-renders to itself from the tree. The last of those is what stops a branch that moves the town from leaving a stale report green.
