# Chicago 4D → Unreal → streamed application

## Standalone updates and parity — 2026-09-20

The standalone Mac preview and downloadable prerelease now exist. Use the [build/release process](BUILD-AND-RELEASE.md) for the next update and the [parity tracker](PARITY.md) for missing web features. T-1472 through T-1475 add on-demand builds, placement repair, flora and navigation; existing T-1360 owns roads. Native parity comes before streaming. The prototype evidence below is historical, not the current build entry point.

Owner request, 18 September 2026: regularly build downloadable game assets, complete the
Unreal rendition, fix the black-bar/static corruption seen during play, and eventually
pull or push a tested build onto a server. Queue this programme after South Through Time
and before Loop Improvements. Keep work needing Unreal off the remote web worker.

## Current evidence, not a release

A local spike on the owner's Mac created `Chicago4D_UE` with Unreal 5.8. The engine log
identified 5.8.2. The source was the local `custom-t1222/chicago/4d` checkout, NOT a promise
that today's dev has identical asset counts. The generated map is
`/Game/Chicago4D/Maps/Chicago1835_Preview`.

The spike imported 382 structure GLBs plus ground and water (384 static mesh actors,
388 total actors). Sidecar placement was converted from metres to Unreal centimetres;
glTF `(x,y,z)` converts to Unreal `(x,z,y)`, so ENU becomes `(100e,-100n,100h)`.
Facade bearing maps to actor yaw; a viewer yaw clockwise from north maps to Unreal yaw
minus 90 degrees. Ground anchoring samples the scene epoch heightfield; water-anchored
structures use the datum's water plane. Check these against the engine version in use.

The saved verification found the expected collision flag on solid meshes and plausible
Sauganash dimensions. Water has NoCollision, but its import generated empty convex-hull
warnings; fix the import settings rather than suppressing these logs. A streamed image
of the Sauganash and keyboard input were observed in Chrome at `http://127.0.0.1`.
This does NOT establish complete traversal, reliable spawn, fidelity, long-session stability,
remote networking, or safe packaged-build behavior. Diagnostic `BugItGo` was used to reset
the view; it enables ghost mode, so that part of the demonstration is NOT collision proof.
A future traversal receipt must explicitly use normal walking with cheats off.

The owner subsequently reported frequent black-bar/static noise. It is OPEN. Do not
confuse dynamic corruption with stable aspect-ratio letterboxing or call it fixed because
a still frame looks clean. The local server package declared UE5.7 signalling dependencies,
while the engine is UE5.8; `endpointIdConfirm` and `layerPreference` were unsupported in
the legacy PixelStreaming log. This is a compatibility lead, not an established cause.
The browser snapshot showed roughly 60 fps at 1920×1080 and high video bitrates; it is
one observation, not a target or a stability test.

The spike has no web procedural streets, flora, props, enclosures, information cards,
confidence visualization, epoch-switching UI, or faithful material/lighting parity.
Nine imported sidecars retained `review_required`; the report identifies them. Existing
Indigenous-history/review constraints and the no-human-figures rule continue to apply.
The launch-time skeletal-mesh show flag is only a prototype expedient, not a shipped pawn.

`prototype/` preserves the small scripts and reports as **reference text**, not production
entry points. They contain original local paths, overwrite the preview map on rerun,
reuse existing imports without a source-hash check, do not remove retired assets, and
continue after some per-asset errors. They must be hardened before automation. No binary
assets, credentials, raw engine installation, server config, or private research deposit
are copied here. Source asset licenses remain authoritative.

## Deliverables and progression

1. **Scene bundle:** engine-neutral GLB, JSON sidecars, scene/epoch and terrain resources,
   referenced textures, runtime-safe provenance, license inventory, and checksums. This
   is what the existing Blender bake can publish without Unreal. Preserve master assets
   independently of web-optimized derivatives; compatibility decides which Unreal consumes.
2. **Unreal project/import:** pinned engine/plugin configuration, importer, materials,
   playable map and pawn, collision/navigation decisions, incremental update behavior.
   Generated Unreal caches and local absolute paths are not the portable source.
3. **Cooked application:** target-OS build made with the matching SDK/toolchain, carrying
   the exact accepted bundle digest. This is what a GPU streaming host runs; uploading a
   GLB archive alone cannot produce a playable server. A Mac executable is not a Linux build.
4. **Deployment release:** application plus matched signalling/frontend versions, runtime
   configuration, health checks and rollback. Engine binaries are not casually redistributed
   inside a publicly downloadable source-asset bundle.

Each immutable release records source commit, scene dates, asset hashes, generator/Blender
pin, bundle schema, Unreal version where applicable, target platform, build id, and test
receipts. Build a consistent snapshot; never mix sidecars from one commit with meshes from
another. Stage updates, validate checksums and schema, then switch the active release
atomically. Keep the last known good release. Failures leave its pointer untouched.

Start by attaching versioned bundles to the existing successful scheduled bake and a manual
build path, rather than inventing a second schedule that races it. Record actual cadence,
retention and download instructions. An expiring CI artifact needs explicit expiry and a
stable discovery mechanism; durable releases/storage must be deliberately selected. Verify
availability from a fresh consumer. No new paid storage or public deployment is authorized
merely by filing these tickets. Workflow changes need the owner-visible PR required by
AGENTS.md. Continue the dev/main promotion boundary.

## Where work can run

| Work | Eligible environment | Owner presence |
|---|---|---|
| Contracts, source changes, manifests, checksums, CI configuration and runbooks | Remote web worker | Normally unnecessary |
| Geometry generation, texture baking, reproducibility and bundle assembly | Existing pinned Blender bake runner | Normally unnecessary; web worker must not install Blender to bypass the established boundary |
| Unreal import, material/lighting review, walking, Mac encoder corruption | Owner's Mac initially; exact project/engine/GPU/browser access required | Coordinate an available session for first diagnosis, access prompts, and final visual review |
| Unreal automated import/cook/package | Qualified licensed Unreal build runner with matching SDKs and storage | Initial provisioning/authentication/terms may require owner; routine runs should not |
| Pixel Streaming runtime and corruption/network QA | Supported GPU encoder + driver + display/render context + matched signalling/frontend + real browser | Initial reproduction and external-network checks as needed |
| Host promotion and public network/security setup | Approved staging/production host with scoped credentials and cost limit | Required for unapproved costs, terms, credentials or public exposure |

A remote Unreal runner is an option, NOT assumed available. Inventory OS/architecture,
engine license/account access, installation route, SDK/toolchain, GPU and encoder access,
RAM/disk/cache budget, session/display constraints and permitted runtime. A headless CPU
machine may support some build steps while being unable to render/encode/validate a stream.
Do not assume installing the engine cures a missing GPU. Do not install it in an ephemeral
web worker merely to discover the job cannot finish. Prepare an exact provisioning proposal
and obtain any necessary license/terms, host and cost approvals, then prove import, cooking
and streaming separately. Until that evidence exists, local tickets stay held.

## Enforced execution holds

Engine and deployment tickets are `state: blocked-tech`, with explicit `blocked_on` text.
The existing `list --workable` excludes them and `claim` refuses them. Their `# HOLD`
references in QUEUE are deliberately comments: the parser reads only bare T-NNNN lines.
A heading or an invented metadata field alone would not enforce this protection.

Unblocking is an assigned coordinator action, not a web loop's workaround. Inspect every
prerequisite receipt and the CURRENT executor's capabilities. Dependency completion alone
does not prove engine access. Open an engine ticket only immediately before an eligible
worker claims it; if access is lost, restore `blocked-tech` before handing it back. Since
this scheduler has no capability-scoped claims, do not leave an unclaimed engine-only ticket
open in the general queue. Use the reserved position in this band when unblocking—the tool's
append-to-bottom default does not reflect the owner's ranking. The owner authorizes this
section order, not reordering the rest of the queue.

Remote preparation may be a bounded successor assigned to a remote worker, but it cannot
close the parent acceptance requiring engine evidence. Never substitute `needs_bake` for
Unreal eligibility: it describes the existing Blender boundary only. Report held work and
its unblocking conditions; do not repeatedly attempt it or manufacture successful receipts.

## Completing scenery parity without duplicating the web renderer

T-0252 already owns the cross-renderer export decision; this request supplies its missing
consumer and authorizes pursuing portable scene assets. Resolve the export contract there.
Inventory current layers, including streets/alleys, frontage/plank walks, wharves and bridge
approaches, flora, fauna subject to project constraints, fences/enclosures, yards/wells,
boats/wagons/camps/signage, water/terrain material detail, atmosphere/lighting, confidence
and source cards, and year/epoch behavior. Do not call the historical nine-layer list a
complete current inventory. Do not generate people or bypass review flags.

For each layer record its source, seed, ground/water dependency, portable representation,
material/textures, instancing/LOD/collision policy, unsupported features, license and parity
receipt. Terrain-dependent geometry must rebuild against the same epoch/heightfield, retaining
re-derivation gates. Avoid a second independent implementation of historical placement rules.

First demonstrate one street corridor exported, imported, and walkable. Then take one bounded
layer or corridor per successor, in this same band, recording the remaining inventory before
closing the predecessor. Do not close the epic because the first corridor works. Subsequent
slices cover material fidelity, instancing/LOD, lighting, interaction/provenance, multiple
scene dates, and measured performance as well as geometry. Newly generated assets retain
license records and the existing research confidence rules.

## Streaming defect experiment

Record hardware, macOS/browser versions, engine build, plugin choice (legacy or PS2), server
and frontend commit/lockfile, codec, resolution, fps, bitrate and launch args without secrets.
Capture a repeatable camera path and moving-video evidence. Compare the local game viewport
with the decoded stream at the same location; identify which first contains the corruption.
Compare a minimal template with Chicago, then change ONE variable at a time: supported
matched infrastructure, encoder/codec, 720p/30 versus 1080p/60, bitrate bounds, browser,
on-screen versus off-screen capture, and supported render settings. Measure fps, dropped
frames, packet loss and latency. Do not blame geometry, Mac support or the version mismatch
without the comparison. Do not blindly migrate both server and plugin during diagnosis.

Acceptance needs the formerly failing route, motion and resize/reconnect tests, at least
10 continuous minutes at the chosen supported preset, no recurring corruption, retained
before/after clips, and normal walking. Stable letterboxing is documented separately. If no
Mac configuration succeeds, report the negative matrix and create a qualified-runner handoff;
do not close as fixed or require the owner to rebake the town without evidence.

## Server handoff

Prefer a pull-by-digest staging update to broad push credentials unless the chosen host needs
push. Dry run, disk-space checks, digest/signature policy, atomic activation, health probe,
rollback, log retention and startup supervision are required. Keep tokens/TURN credentials in
secrets, not assets/logs. Decide one shared session versus per-user instances explicitly and
measure capacity before scaling. Authenticate/protect signalling as appropriate; qualify TLS,
WebSocket routing and STUN/TURN from an external client, not just localhost. Start with one
approved staging host. Production promotion is a separate owner action.

## Primary references (checked 18 September 2026)

- [Epic: Pixel Streaming reference](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-pixel-streaming-reference) — platform/encoder requirements and settings.
- [Epic: Getting started](https://dev.epicgames.com/documentation/unreal-engine/getting-started-with-pixel-streaming-in-unreal-engine) — engine-matched infrastructure branch and streaming setup.
- [Epic: official infrastructure](https://github.com/EpicGames/PixelStreamingInfrastructure) — versioned server/frontend packages.
- [Epic: containers overview](https://dev.epicgames.com/documentation/unreal-engine/overview-of-containers-in-unreal-engine) — development/runtime container options; availability is not proof of this runner's capabilities.
