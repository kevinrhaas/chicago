/* machine-drift.js — the time machine's telemetry numbers, defined once for the portal's
   console (portal/portal.js) and the Navigator's telemetry strip (js/nav-telemetry.js), T-2623.

   DESIGN §06 "Machine chrome": the strip "reuses portal.js telemetry and drift events". So the
   numbers the portal's console shows on its 800 ms tick — FIELD COHERENCE, INTERVAL DRIFT and
   the reactor — and the cadence of its drift events (the first 5-8 s in, then every 9-14 s,
   each about 2.9 s long) live here, and both read them. They are decorative, and say so: the
   field and the drift are fake instruments and never pretend to be research.

   A classic script with no import or export, so the portal can load it with <script> and the
   renderer can import it for its effect; both read globalThis.chicagoMachineDrift. */
(() => {
  const TICK_MS = 800;
  const rand = (a, b, random = Math.random) => a + random() * (b - a);
  /** One tick's numbers. `slipping` is true while a drift event holds. */
  function readings(slipping = false, random = Math.random) {
    return {
      coherence: slipping ? rand(0.962, 0.981, random) : rand(0.994, 0.999, random),
      drift: slipping ? rand(1.2, 2.1, random) : rand(0.3, 0.5, random),
      reactor: rand(86.4, 88.1, random),
    };
  }
  const format = Object.freeze({
    coherence: (v) => v.toFixed(3),
    drift: (v) => `±${v.toFixed(1)} d`,
    reactor: (v) => `${v.toFixed(1)}%`,
  });
  /** Milliseconds from now to the next drift event: the first, or one after another. */
  const nextDriftIn = (first = false, random = Math.random) =>
    (first ? rand(5000, 8000, random) : rand(9000, 14000, random));
  const DRIFT_MS = 2900;
  globalThis.chicagoMachineDrift = Object.freeze({ TICK_MS, DRIFT_MS, rand, readings, format, nextDriftIn });
})();
