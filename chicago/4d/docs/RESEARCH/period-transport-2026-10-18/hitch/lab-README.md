# Coupled C01 / horse / breastcollar geometric study

This fixture loads the existing exported sibling assets directly: `../carriage/carriage-c01.glb`, `../horse/equine_light_harness_reconstructed_01.glb`, and `../harness/light_breastcollar_harness_reconstructed_01.glb`. It does not duplicate or regenerate their geometry. Its original coupling code is GPL-3.0-or-later; existing asset licenses remain in their respective manifests. It uses the application Three vendor in place.

Serve `/workspace` on port8784 and visit `/shared/period-transport-lab/hitch/`. Run `python verify.py` with Python Playwright and installed `/usr/bin/chromium` for screenshots and measurements.

## What is implemented

The live single-horse hitch locates the horse root using the1m shaft/horse socket datum; each asset retains unit scale. Front steering rotates the front wheels, shaft frame and horse heading. The shafts are pitched upward about their existing front-gear origin by approximately6.5° so their forward ends reach the horse's1m shaft datum. This pitch is a reconstructed runtime fitting choice; no artifact or source was altered to imply historical fit.

Carriage rear-axle distance defines a constant-steering arc. Four wheel angles use their separate turn radii. The horse-root arc length is calculated from its actual current offset to the rear-axle trajectory, then converted to walk phase using the horse fixture's reconstructed stride0.72/0.62m. This is geometric synchronization, not sourced or physically validated gait. Changing steering instantly changes path state; there is no smooth start/stop/turn dynamics.

The harness head follows the animated horse head in world position and orientation. Original static reins/traces/check reins are hidden. Four replacement tube curves are rebuilt from live bit/breastcollar sockets to empty driver-hand/vehicle targets. Trace sag is12mm; rein sag100mm. These are visual taut/slack curves with no tension, mouth pressure, force, skin friction or vehicle acceleration model. The driver's seat and horse rider seat remain empty.

## Measurements and open gates

`validation.json` contains21 sampled states at each desktop1280×800 and mobile390×780 viewport, using distances0–5m and steering0/±8°. Screenshots show rest and turning configurations. The tests inspect the actually loaded GLB nodes and generated curve vertices; they do not certify historical accuracy.

The initial measurement found approximately59mm conservative shaft-to-torso lateral envelope separation and785mm horse-to-carriage-body longitudinal separation. The torso measurement projects actual loaded horse vertices in the region0.65–1.20m high and−1.1–0.05m fore/aft; it excludes lower limbs and harness. The longitudinal measurement projects all loaded horse vertices into vehicle coordinates. These envelope checks are useful partial clearance measurements, **not** full swept triangle-collision tests. Shafts and shaft-loop sockets remain approximately45mm apart: they are not mechanically connected, and this remaining fit gap is visible and recorded. Hoof contact samples reach about−0.2mm below the ground and140mm above it in swing; stance foot sliding is not closed.

Remaining gates include exact shaft-loop coupling, full limb/shaft/body swept collision, source-verified harness plates and vehicle subtype, photographic comparisons, continuous anatomical topology and skin, sourced gait/stance contacts, forces and suspension, brakes/reins controls, start/stop/turn/trot transitions, LODs, occupied driver/rider seats, boarding and safe interaction. This is partial T2794/T2801 coupling engineering evidence; it does not close T2795 or any production/photographic-quality acceptance.
