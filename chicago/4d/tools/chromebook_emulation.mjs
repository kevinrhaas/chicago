/**
 * T-3675 — the low-end Chromebook of a classroom set, as Chrome on ChromeOS reports it.
 *
 * There is no Chromebook in this container, so the one measured here is EMULATED: the
 * browser is told what a school's low-end Chromebook tells a page, and the town then
 * makes its own choices from that, as it does on the real machine. Nothing in the app
 * is forced (no `?device=`): the user agent says CrOS, `navigator.deviceMemory` 4,
 * `hardwareConcurrency` 4, and WEBGL_debug_renderer_info names the Celeron N4020's
 * Intel UHD Graphics 600 the way ChromeOS's ANGLE does. The pixels are still drawn by
 * SwiftShader, so a reading here is bytes, never a timing.
 *
 * Used by tools/measure_memory.mjs (`--only chromebook`) and tools/check_chromebook.mjs.
 */

/** The class-set Chromebook: Celeron N4020 / UHD 600, 4 GB, 1366x768 at 1x, no touch. */
export const CHROMEBOOK = Object.freeze({
  id: 'chromebook',
  label: 'Chromebook 1366x768 (ChromeOS, Intel UHD 600, 4 GB, 4 threads)',
  userAgent: 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) '
    + 'Chrome/130.0.0.0 Safari/537.36',
  platform: 'Chrome OS',
  memoryGB: 4,
  cores: 4,
  vendor: 'Google Inc. (Intel)',
  renderer: 'ANGLE (Intel, Mesa Intel(R) UHD Graphics 600 (GLK 2), OpenGL ES 3.2)',
  width: 1366,
  height: 768,
  dsf: 1,
});

/**
 * Other renderer strings a classroom Chromebook gives (ChromeOS ANGLE over Mesa or the
 * vendor's driver). Every one shares the system's memory.
 */
export const CHROMEBOOK_GPUS = Object.freeze([
  CHROMEBOOK.renderer,
  'ANGLE (Intel, Mesa Intel(R) UHD Graphics 605 (GLK 3), OpenGL ES 3.2)',
  'Mesa DRI Intel(R) HD Graphics 400 (Braswell)',
  'ANGLE (Intel, Mesa Intel(R) HD Graphics 500 (APL 2), OpenGL ES 3.2)',
  'ANGLE (Intel, Mesa Intel(R) UHD Graphics (JSL), OpenGL ES 3.2)',
  'ANGLE (ARM, Mali-G72, OpenGL ES 3.2)',
  'ANGLE (ARM, Mali-G52 MC2, OpenGL ES 3.2)',
  'Mali-G57',
  'ANGLE (Imagination Technologies, PowerVR Rogue GX6250, OpenGL ES 3.2)',
  'ANGLE (Qualcomm, Adreno (TM) 618, OpenGL ES 3.2)',
  'ANGLE (AMD, AMD Radeon(TM) Graphics (radeonsi, renoir, LLVM 15.0.7), OpenGL ES 3.2)',
]);

/** Playwright context options for the emulated Chromebook (a laptop: no touch screen). */
export function chromebookContext(extra = {}) {
  return {
    viewport: { width: CHROMEBOOK.width, height: CHROMEBOOK.height },
    deviceScaleFactor: CHROMEBOOK.dsf, isMobile: false, hasTouch: false,
    userAgent: CHROMEBOOK.userAgent,
    ...extra,
  };
}

/**
 * The init script (pass with its argument: `ctx.addInitScript(spoofDevice, CHROMEBOOK)`).
 * Runs in the page before any of its scripts: the getters the device profile reads.
 */
export function spoofDevice(d) {
  const def = (proto, key, value) => {
    try { Object.defineProperty(proto, key, { get: () => value, configurable: true }); } catch { /* sealed */ }
  };
  def(Navigator.prototype, 'deviceMemory', d.memoryGB);
  def(Navigator.prototype, 'hardwareConcurrency', d.cores);
  def(Navigator.prototype, 'userAgent', d.userAgent);
  if (globalThis.NavigatorUAData) def(NavigatorUAData.prototype, 'platform', d.platform);
  for (const C of [globalThis.WebGLRenderingContext, globalThis.WebGL2RenderingContext]) {
    if (!C) continue;
    const get = C.prototype.getParameter;
    C.prototype.getParameter = function getParameter(p) {
      if (p === 0x9246) return d.renderer;   // UNMASKED_RENDERER_WEBGL
      if (p === 0x9245) return d.vendor;     // UNMASKED_VENDOR_WEBGL
      return get.call(this, p);
    };
  }
}
