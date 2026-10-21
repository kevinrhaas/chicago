/**
 * T-2970 — THE DRAWS THE DRIVER RECEIVES, COUNTED WHERE `renderer.info` CANNOT SEE THEM.
 *
 * three's `renderer.info.render.calls` goes up once per object it renders. A
 * BatchedMesh is one object, so three counts it as ONE call, but it submits it as a
 * multi-draw with one entry per instance it kept (`_multiDrawCount`), and each entry
 * is a draw to the driver: ANGLE loops them where the GPU has no native multi-draw,
 * and a phone pays for every one. At Read frame pacing's 1904 flight pose the page
 * said 339 calls while the GL received 27,895 draws (T-2927,
 * docs/measurements/T-2927-flight-draws.json), and every draw budget the project had
 * — `BUDGET` in main.js, light's floor in the smoke, the detail ceilings — read the
 * 339. No gate saw that frame's cost.
 *
 * The count here is three's own plus what three's own leaves out: each call to the
 * WEBGL_multi_draw extension adds its `drawcount - 1`, the entries past the one
 * `info.update` already took. Where the extension is missing three draws a BatchedMesh
 * entry by entry and counts each, so nothing is added and the figure is still the
 * driver's. The tally resets when `renderer.info` resets, so it means what
 * `info.render.calls` means — the last `render()`, or more where a caller holds
 * `autoReset` off (gpu-pick.js, confidence.js) — and the two cannot drift.
 *
 * It wraps the extension's four entry points, which are called once per BatchedMesh
 * drawn (hundreds a frame, not the thousands of draws inside them).
 *
 * It NEVER ENABLES the extension itself: it waits for three to ask the context for
 * it, and wraps what three is handed. three enables `WEBGL_multi_draw` lazily, at the
 * first BatchedMesh it draws, and the first version of this asked for it at boot
 * (`extensions.has`) — which on its own, nothing wrapped, put one 52-57 ms flora pass
 * on the first walk after a tier change (frame 8 of the moving-frames gate's balanced
 * and light walks, on CI and locally; the gate's ceilings are 32 and 21 ms). So the
 * one thing it puts on the GL context is a pass-through `getExtension` that notices
 * that name go by.
 */

/** Each entry point, and where its `drawcount` sits (the WEBGL_multi_draw spec). */
const MULTI_DRAW = { multiDrawArraysWEBGL: 5, multiDrawElementsWEBGL: 6,
  multiDrawArraysInstancedWEBGL: 7, multiDrawElementsInstancedWEBGL: 8 };

/**
 * Count the driver's draws on `renderer`. Returns `{ draws, multiDrawExtra, native }`
 * as live readings: `draws` is the figure every draw budget is held to, and
 * `native` says whether three has taken the extension and it is being counted.
 * Call it before the first BatchedMesh is drawn (main.js does, at boot), or the
 * extension three already holds goes uncounted.
 */
export function countDriverDraws(renderer) {
  // One tally per renderer: a second caller reads the first's rather than wrapping twice.
  if (renderer.__driverDraws) return renderer.__driverDraws;
  const info = renderer.info;
  let extra = 0;
  let native = false;
  const wrap = (ext) => {
    if (!ext || native) return ext;
    native = true;
    for (const [name, at] of Object.entries(MULTI_DRAW)) {
      const fn = ext[name];
      if (typeof fn !== 'function') continue;
      ext[name] = function countedMultiDraw() {
        const n = arguments[at];
        if (n > 1) extra += n - 1;
        return fn.apply(ext, arguments);
      };
    }
    return ext;
  };
  // Wrapped when three (or upload-release.js's hold) asks for it, never asked for here.
  const gl = renderer.getContext();
  const getExtension = gl.getExtension;
  gl.getExtension = function getExtensionNoticed(name) {
    const ext = getExtension.call(this, name);
    return name === 'WEBGL_multi_draw' ? wrap(ext) : ext;
  };
  const reset = info.reset;
  info.reset = function resetWithDriverDraws() { extra = 0; return reset.call(this); };
  return (renderer.__driverDraws = {
    get draws() { return info.render.calls + extra; },
    get multiDrawExtra() { return extra; },
    get native() { return native; },
  });
}
