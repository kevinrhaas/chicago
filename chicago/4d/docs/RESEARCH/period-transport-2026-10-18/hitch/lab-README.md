# Coupled C01 / horse / breastcollar geometric study

This fixture loads the existing exported sibling assets directly: `../carriage/carriage-c01.glb`, `../horse/equine_light_harness_reconstructed_01.glb`, and `../harness/light_breastcollar_harness_reconstructed_01.glb`. It does not duplicate or regenerate their geometry. Its original coupling code is GPL-3.0-or-later; existing asset licenses remain in their respective manifests. It uses the application Three vendor in place.

Serve `/workspace` on port8784 and visit `/shared/period-transport-lab/hitch/`. Run `python verify.py` with Python Playwright and installed `/usr/bin/chromium` for screenshots and measurements.

## What is implemented

The live single-horse hitch locates the horse root using the1m shaft/horse socket datum; each asset retains unit scale. Front steering rotates the front wheels, shaft frame and horse heading. The shafts are pitched upward about their existing front-gear origin by approximately6.5° so their forward ends reach the horse's1m shaft datum. This pitch is a reconstructed runtime fitting choice; no artifact or source was altered to imply historical fit.

Carriage rear-axle distance defines a constant-steering arc. Four wheel angles use their separate turn radii. The horse-root arc length is calculated from its actual current offset to the rear-axle trajectory, then converted to walk phase using the horse fixture's reconstructed stride0.72/0.62m. This is geometric synchronization, not sourced or physically validated gait. Changing steering instantly changes path state; there is no smooth start/stop/turn dynamics.

The harness head follows the animated horse head in world position and orientation. Original static reins/traces/check reins are hidden. Four replacement tube curves are rebuilt from live bit/breastcollar sockets to empty driver-hand/vehicle targets. Trace sag is12mm; rein sag100mm. These are visual taut/slack curves with no tension, mouth pressure, force, skin friction or vehicle acceleration model. The driver's seat and horse rider seat remain empty.

## Measurements and open gates

`validation.json` contains35 sampled states at each desktop1280×800 and mobile390×780 viewport, using distances0–5m and steering0/±8°/±12°. Screenshots show rest and turning configurations. The tests inspect the actually loaded GLB nodes and generated curve vertices; they do not certify historical accuracy.

The initial measurement found approximately59mm conservative shaft-to-torso lateral envelope separation and785mm horse-to-carriage-body longitudinal separation. The torso measurement projects actual loaded horse vertices in the region0.65–1.20m high and−1.1–0.05m fore/aft; it excludes lower limbs and harness. The longitudinal measurement projects all loaded horse vertices into vehicle coordinates. These envelope checks are useful partial clearance measurements, **not** full swept triangle-collision tests. Shafts and shaft-loop sockets remain approximately45mm apart in the initial checkpoint. The T2795 follow-up below supersedes that gap with authored tugs and measured section fit. Hoof contact samples reach about−0.2mm below the ground and140mm above it in swing; stance foot sliding is not closed.

Remaining gates include exact shaft-loop coupling, full limb/shaft/body swept collision, source-verified harness plates and vehicle subtype, photographic comparisons, continuous anatomical topology and skin, sourced gait/stance contacts, forces and suspension, brakes/reins controls, start/stop/turn/trot transitions, LODs, occupied driver/rider seats, boarding and safe interaction. This is partial T2794/T2801 coupling engineering evidence; it does not close T2795 or any production/photographic-quality acceptance.


## T2795 follow-up: metadata and shaft fit

The app fixture now consumes the carriage export's wheelbase, track and front/rear wheel radii, and the horse manifest's reconstructed `locomotion.walk.stride_m`. No vehicle dimensions or gait stride are duplicated in the two carriage/coupling viewers. Actual exported shaft-end vertices determine tip centers and cross-section envelope. A pitch solve aligns the midpoint to the harness shaft socket height while keeping the horse ground root and unit scale.

The earlier45mm gap was lateral: the original provisional socket centers were±0.36m, while actual authored shaft centers are±0.405m. New reconstructed shaft tugs and support webbing are authored at±0.405m,1m,0.05m; this is an explicit adjustable engineering fit, not historical measurement. In the loaded geometry the loop bore is36.99994mm. Shaft corners projected along the actual shaft axis into the tug plane occupy30.50646mm radius; resulting radial clearance is6.49348mm. Endpoint residual is below0.00001mm. This is a local static section check, not evidence of contact-force behavior or a full swept collision gate.

Shaft plane is geometrically plausible for this unscaled study: its forward ends are1m above ground beside the torso, and the shaft-to-torso lateral envelope remains positive in sampled poses. Breeching is present around the hindquarters, but no validated holdback connection routes its loads to the shafts; a visible breeching strap alone does not provide braking or reverse restraint. Its height and force path remain engineering/period-source gates.

## Front turntable rolling correction

The complete front axle swivels about its kingpin. Its wheel-center position relative to the rear axle is `(x cos δ, wheelbase − x sin δ)` in the ground plane, rather than the unsteered `(x, wheelbase)`. For curvature `k=tan δ/wheelbase`, its distance multiplier is therefore `sec δ − kx`; the rear multiplier remains `1−kx`. Both carriage and coupled viewers use this turntable formula. The metadata sensitivity check independently calculates those expected angles. A separate finite-difference check observes actual loaded world wheel centers over rear-axle distances1m to1.01m at0/±8/±12° and compares their chord length against roll-angle change times exported wheel radius. This is a kinematic rolling check, not steering-force, tire-slip or dynamic suspension validation.
