/**
 * device-profile.js — read what the device offers, then choose per device.
 *
 * T-2559. The owner, 2026-10-16: *"if there is a way to tap into local
 * computing resources for rendering based on the browser and platform"*. Until
 * this the renderer knew one thing about the device — whether it has a touch
 * screen — so a 2026 iPad Pro and a five-year-old Android phone both booted
 * `light` at Sharpness Low, and a weak laptop booted `full`.
 *
 * Run once at boot, before the scene is fetched:
 *
 *  1. READ what the platform says: WebGPU (`navigator.gpu`, its adapter's info
 *     and limits), the WebGL2 renderer string, MAX_TEXTURE_SIZE, the
 *     compressed formats (ASTC / ETC2 / BC7 — T-2551 needs the same answer),
 *     `hardwareConcurrency`, `deviceMemory` (Chromium only, a hint), screen
 *     pixels and `devicePixelRatio`.
 *  2. MEASURE for at most a second: a fill and a vertex pass on an offscreen
 *     target, timed with EXT_disjoint_timer_query_webgl2 where the browser
 *     exposes it and by the wall clock across a pixel read otherwise.
 *  3. DECIDE a class — weak, standard or strong — and from the class and the
 *     platform the boot detail tier, Sharpness, texture tier (T-2551/T-2553),
 *     worker count (T-2556) and whether WebGPU is there for a later renderer
 *     (T-2558).
 *
 * The result is cached in localStorage keyed by the renderer string and the
 * build, so a repeat visit skips the benchmark. A forced profile is never
 * cached.
 *
 * THE VISITOR KEEPS THE LAST WORD. These are the defaults for a visitor who
 * never chose; a stored Scene detail or Image sharpness always wins (main.js
 * reads it first, as it did before), and Settings says what was chosen and why.
 *
 * DOCTRINE 5 HOLDS: a class moves flora, shadows, resolution and texture tier —
 * the existing detail ladder and the Sharpness stops — and never what is
 * reconstructed.
 *
 * WHAT IS NOT YET KNOWN, SAID PLAINLY. The benchmark's thresholds below are a
 * first setting, not a calibration: no reading from real phone or laptop
 * silicon was taken to set them, and they are to be moved when T-2546's meter
 * reports what the classes actually cost. The raw readings are kept on the
 * profile (`api.device.bench`) so that can be done from the field.
 *
 * A SOFTWARE RASTERISER IS NOT BENCHMARKED. SwiftShader and llvmpipe measure
 * the CPU, not a GPU, and they are the machine every one of this project's
 * frame and triangle ceilings is gated on: the platform default is, by that
 * gate, the one the budgets were set for there. So a software renderer keeps
 * the platform default as `standard`, with that reason written on the profile,
 * and pays no benchmark. `?device=weak` is the visitor's way down.
 */

/** The classes, weakest first. */
export const DEVICE_CLASSES = Object.freeze(['weak', 'standard', 'strong']);

/** localStorage key for the cached profile. */
export const PROFILE_KEY = 'chicago4d.device';

/** The benchmark's ceiling, and the measured passes' share of it. */
export const BENCH_BUDGET_MS = 1000;

/**
 * Thresholds on the measured rates. A FIRST SETTING (see the header): weak is
 * below the slower of the two floors, strong above both ceilings.
 *   fill: megapixels shaded per millisecond (1 Mpx/ms = 1 Gpx/s)
 *   verts: million vertices transformed per millisecond (Mvert/ms)
 */
export const THRESHOLDS = Object.freeze({
  fill: { weak: 0.6, strong: 4 },
  verts: { weak: 0.05, strong: 0.4 },
});

const SOFTWARE = /swiftshader|llvmpipe|softpipe|software|basic render|microsoft basic|mesa offscreen/i;

/** True when the renderer string names a software rasteriser. */
export function isSoftwareRenderer(renderer) {
  return SOFTWARE.test(String(renderer || ''));
}

/** `?device=weak|standard|strong` — HARNESS ONLY: forces the class, never cached. */
export function forcedClass(search) {
  try {
    const v = new URLSearchParams(search || '').get('device');
    return DEVICE_CLASSES.includes(v) ? v : null;
  } catch { return null; }
}

/**
 * The class from what was read and measured. Pure, so it is tested in node.
 * Returns { cls, why }.
 */
export function classify(signals, bench, { forced = null, stepDown = 0 } = {}) {
  let cls;
  let why;
  if (forced) {
    cls = forced; why = `forced by ?device=${forced}`;
  } else if (!signals.webgl2) {
    cls = 'weak'; why = 'no WebGL2 context could be read';
  } else if (isSoftwareRenderer(signals.renderer)) {
    cls = 'standard'; why = 'a software rasteriser: the platform default, not benchmarked';
  } else if ((signals.cores && signals.cores <= 2) || (signals.memoryGB && signals.memoryGB <= 2)
    || (signals.maxTexture && signals.maxTexture < 4096)) {
    cls = 'weak';
    why = `few resources (${signals.cores ?? '?'} cores, ${signals.memoryGB ?? '?'} GB, `
      + `${signals.maxTexture ?? '?'} px textures)`;
  } else if (!bench || !Number.isFinite(bench.fill) || !Number.isFinite(bench.verts)) {
    cls = 'standard'; why = 'the benchmark gave no reading';
  } else if (bench.fill < THRESHOLDS.fill.weak || bench.verts < THRESHOLDS.verts.weak) {
    cls = 'weak'; why = `benchmark below the floor (${fmt(bench.fill)} Mpx/ms, ${fmt(bench.verts)} Mvert/ms)`;
  } else if (bench.fill >= THRESHOLDS.fill.strong && bench.verts >= THRESHOLDS.verts.strong
    && (signals.cores ?? 8) >= 6) {
    cls = 'strong'; why = `benchmark above the ceiling (${fmt(bench.fill)} Mpx/ms, ${fmt(bench.verts)} Mvert/ms)`;
  } else {
    cls = 'standard'; why = `benchmark between the bounds (${fmt(bench.fill)} Mpx/ms, ${fmt(bench.verts)} Mvert/ms)`;
  }
  // T-2547's crash marker: a device that ran out of memory last session steps down.
  const steps = Math.max(0, Math.floor(stepDown) || 0);
  if (steps) {
    const at = Math.max(0, DEVICE_CLASSES.indexOf(cls) - steps);
    if (DEVICE_CLASSES[at] !== cls) { cls = DEVICE_CLASSES[at]; why += `; stepped down ${steps} after a crash`; }
  }
  return { cls, why };
}

function fmt(n) { return Number.isFinite(n) ? n.toFixed(2) : '?'; }

/**
 * What a class chooses, on a touch device or not. Pure.
 *
 * A phone or tablet keeps `light` detail at every class: the owner's phone
 * memory crashes (T-2546) are about geometry held, and until that meter reads
 * what `balanced` costs on a phone a stronger phone earns Sharpness, not
 * geometry. A weak desktop steps to `balanced` at Low; a strong one is drawn
 * at High.
 */
export function decide(cls, { touch = false, cores = null, webgpu = false } = {}) {
  const c = DEVICE_CLASSES.includes(cls) ? cls : 'standard';
  const table = touch
    ? { weak: ['light', 1], standard: ['light', 1], strong: ['light', 1.5] }
    : { weak: ['balanced', 1], standard: ['full', 1.5], strong: ['full', 2] };
  const [detail, sharpness] = table[c];
  const textures = touch || c === 'weak' ? 'light' : 'full';
  const n = Number.isFinite(cores) && cores > 0 ? cores : 4;
  const workers = c === 'weak' ? 1 : Math.max(1, Math.min(c === 'strong' ? 6 : 4, n - 1));
  return { detail, sharpness, textures, workers, webgpu: !!webgpu };
}

/** The words Settings shows. */
export const CLASS_LABEL = Object.freeze({ weak: 'modest', standard: 'standard', strong: 'strong' });
const DETAIL_LABEL = { full: 'Full', balanced: 'Balanced', light: 'Light' };
const SHARP_LABEL = { 1: 'Low', 1.5: 'Medium', 2: 'High' };

/** "Your device: strong desktop, chosen Full detail at High sharpness." */
export function describeProfile(profile) {
  if (!profile) return '';
  const kind = profile.touch ? 'phone or tablet' : 'computer';
  const d = DETAIL_LABEL[profile.choice.detail] ?? profile.choice.detail;
  const s = SHARP_LABEL[profile.choice.sharpness] ?? String(profile.choice.sharpness);
  return `Your device: ${CLASS_LABEL[profile.cls] ?? profile.cls} ${kind}, chosen ${d} detail at ${s} sharpness.`;
}

/** The cache key: renderer string and build, so a new GPU or a new build re-measures. */
export function cacheKey(renderer, build) {
  return `${String(renderer || '?')}|${String(build || '?')}`;
}

/** The cached profile if it was measured on this renderer and build, else null. */
export function readCached(storage, key) {
  try {
    const raw = storage?.getItem(PROFILE_KEY);
    if (!raw) return null;
    const hit = JSON.parse(raw);
    return hit && (key == null || hit.key === key) && DEVICE_CLASSES.includes(hit.cls) ? hit : null;
  } catch { return null; }
}

// ---- reading the platform ---------------------------------------------------

function readGl(doc) {
  const out = { webgl2: false, renderer: '', vendor: '', maxTexture: null, formats: [], timer: false };
  let canvas;
  let gl;
  try {
    canvas = doc.createElement('canvas');
    canvas.width = 256; canvas.height = 256;
    gl = canvas.getContext('webgl2', { antialias: false, depth: false, stencil: false,
      preserveDrawingBuffer: false, powerPreference: 'high-performance' });
  } catch { gl = null; }
  if (!gl) return { signals: out, gl: null };
  out.webgl2 = true;
  const dbg = gl.getExtension('WEBGL_debug_renderer_info');
  out.renderer = String((dbg && gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)) || gl.getParameter(gl.RENDERER) || '');
  out.vendor = String((dbg && gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL)) || gl.getParameter(gl.VENDOR) || '');
  out.maxTexture = Number(gl.getParameter(gl.MAX_TEXTURE_SIZE)) || null;
  const exts = gl.getSupportedExtensions() || [];
  const has = (re) => exts.some((e) => re.test(e));
  if (has(/compressed_texture_astc/)) out.formats.push('astc');
  if (has(/compressed_texture_etc$/) || has(/compressed_texture_etc\b/)) out.formats.push('etc2');
  if (has(/compressed_texture_bptc/)) out.formats.push('bc7');
  if (has(/compressed_texture_s3tc/)) out.formats.push('s3tc');
  out.timer = exts.includes('EXT_disjoint_timer_query_webgl2');
  return { signals: out, gl };
}

async function readWebGpu(nav, timeoutMs = 250) {
  if (!nav?.gpu?.requestAdapter) return { present: false };
  try {
    const adapter = await Promise.race([
      nav.gpu.requestAdapter(),
      new Promise((r) => setTimeout(() => r(undefined), timeoutMs)),
    ]);
    if (adapter === undefined) return { present: true, adapter: false, note: 'adapter request timed out' };
    if (!adapter) return { present: true, adapter: false };
    const info = adapter.info || {};
    return {
      present: true, adapter: true,
      vendor: info.vendor || '', architecture: info.architecture || '',
      maxTexture: adapter.limits?.maxTextureDimension2D ?? null,
      maxBufferMB: adapter.limits?.maxBufferSize ? Math.round(adapter.limits.maxBufferSize / 2 ** 20) : null,
    };
  } catch (err) {
    return { present: true, adapter: false, note: String(err?.message || err) };
  }
}

// ---- the benchmark ----------------------------------------------------------

const VS = `#version 300 es
in vec2 p; uniform float k;
void main(){ vec2 q = p; for (int i = 0; i < 4; i++) q = q * 0.999 + sin(q.yx * k + float(i)) * 1e-4;
  gl_Position = vec4(q, 0.0, 1.0); }`;
const FS = `#version 300 es
precision highp float; uniform float k; out vec4 o;
void main(){ vec2 u = gl_FragCoord.xy * 0.01; float a = 0.0;
  for (int i = 0; i < 8; i++) a += sin(u.x * k + float(i)) * cos(u.y * k - float(i));
  o = vec4(fract(a), 0.5, 0.5, 1.0); }`;

function program(gl) {
  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
  const p = gl.createProgram();
  gl.attachShader(p, sh(gl.VERTEX_SHADER, VS));
  gl.attachShader(p, sh(gl.FRAGMENT_SHADER, FS));
  gl.linkProgram(p);
  return gl.getProgramParameter(p, gl.LINK_STATUS) ? p : null;
}

const frame = () => new Promise((r) => (typeof requestAnimationFrame === 'function'
  ? requestAnimationFrame(() => r()) : setTimeout(r, 16)));

/**
 * Time `draw` on the GPU: the timer query where there is one (polled over the
 * following frames), else the wall clock across a 1-pixel read, which waits for
 * the GPU. Null once `deadline` has passed: the budget is a ceiling, not a hope.
 */
async function timeDraw(gl, timerExt, draw, now, deadline) {
  if (now() >= deadline) return null;
  const px = new Uint8Array(4);
  if (timerExt) {
    const q = gl.createQuery();
    gl.beginQuery(timerExt.TIME_ELAPSED_EXT, q);
    draw();
    gl.endQuery(timerExt.TIME_ELAPSED_EXT);
    while (now() < deadline) {
      await frame();
      if (gl.getQueryParameter(q, gl.QUERY_RESULT_AVAILABLE)) {
        const disjoint = gl.getParameter(timerExt.GPU_DISJOINT_EXT);
        const ns = gl.getQueryParameter(q, gl.QUERY_RESULT);
        gl.deleteQuery(q);
        return !disjoint && ns > 0 ? { ms: ns / 1e6, method: 'timer-query' } : null;
      }
    }
    gl.deleteQuery(q);
    return null;
  }
  gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
  const t0 = now();
  draw();
  gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
  return { ms: now() - t0, method: 'wall-clock' };
}

/**
 * A fill pass (full-target quads, an 8-term shader) and a vertex pass (a list
 * of zero-area triangles, so vertices dominate), each grown fourfold from a
 * small first draw until one pass takes long enough to read (>= 8 ms), all
 * inside BENCH_BUDGET_MS — the fill pass may spend up to half of it.
 * Returns { fill: Mpx/ms, verts: Mvert/ms, ms, method }.
 */
export async function benchmark(gl, { now = () => performance.now(), budgetMs = BENCH_BUDGET_MS } = {}) {
  const start = now();
  const deadline = start + budgetMs * 0.9;
  const prog = program(gl);
  if (!prog) return { fill: NaN, verts: NaN, ms: now() - start, method: 'no-program' };
  const W = 512;
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texStorage2D(gl.TEXTURE_2D, 1, gl.RGBA8, W, W);
  const fb = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
  gl.viewport(0, 0, W, W);
  gl.useProgram(prog);
  gl.uniform1f(gl.getUniformLocation(prog, 'k'), 3.1);
  const loc = gl.getAttribLocation(prog, 'p');
  const quad = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, quad);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const timerExt = gl.getExtension('EXT_disjoint_timer_query_webgl2');
  let method = timerExt ? 'timer-query' : 'wall-clock';

  // Fill: n full-target quads, n x4 until a pass reads >= 8 ms.
  let fill = NaN;
  const fillDeadline = start + budgetMs * 0.5;
  for (let n = 1; n <= 1024; n *= 4) {
    const t = await timeDraw(gl, timerExt, () => { for (let i = 0; i < n; i++) gl.drawArrays(gl.TRIANGLES, 0, 6); },
      now, fillDeadline);
    if (!t) break;
    method = t.method;
    if (t.ms > 0) fill = (n * W * W / 1e6) / t.ms;
    if (t.ms >= 8) break;
  }

  // Vertices: zero-area triangles on one diagonal, so the fragment stage does no work.
  let verts = NaN;
  const count = 3 * 2 ** 15;
  const vb = new Float32Array(count * 2);
  for (let i = 0; i < count; i++) { vb[2 * i] = (i % 997) / 997 * 2 - 1; vb[2 * i + 1] = vb[2 * i]; }
  const vbuf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, vbuf);
  gl.bufferData(gl.ARRAY_BUFFER, vb, gl.STATIC_DRAW);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  for (let n = 1; n <= 256; n *= 4) {
    const t = await timeDraw(gl, timerExt, () => { for (let i = 0; i < n; i++) gl.drawArrays(gl.TRIANGLES, 0, count); },
      now, deadline);
    if (!t) break;
    if (t.ms > 0) verts = (n * count / 1e6) / t.ms;
    if (t.ms >= 8) break;
  }
  gl.deleteBuffer(quad); gl.deleteBuffer(vbuf); gl.deleteFramebuffer(fb); gl.deleteTexture(tex); gl.deleteProgram(prog);
  return { fill, verts, ms: now() - start, method };
}

// ---- the profile -------------------------------------------------------------

/**
 * Profile this device once. Never throws: any failure reads as `standard` with
 * the reason, so a browser that refuses a probe boots exactly as it did before.
 *
 * Returns { cls, why, touch, choice: {detail, sharpness, textures, workers,
 * webgpu}, signals, bench, cached, forced, costMs, key }.
 */
export async function profileDevice({
  touch = false, build = '', storage = null, search = '', stepDown = 0,
  doc = globalThis.document, nav = globalThis.navigator, win = globalThis.window,
  now = () => performance.now(), forceBench = false,
} = {}) {
  const t0 = now();
  const forced = forcedClass(search);
  let gl = null;
  try {
    const read = readGl(doc);
    gl = read.gl;
    const signals = {
      ...read.signals,
      cores: Number(nav?.hardwareConcurrency) || null,
      memoryGB: Number(nav?.deviceMemory) || null,
      screen: win?.screen ? [win.screen.width, win.screen.height] : null,
      dpr: Number(win?.devicePixelRatio) || 1,
    };
    const key = cacheKey(signals.renderer, build);
    const hit = !forced && !forceBench && !stepDown ? readCached(storage, key) : null;
    if (hit) {
      return { ...hit, touch, choice: decide(hit.cls, { touch, cores: signals.cores, webgpu: hit.choice?.webgpu }),
        cached: true, forced: null, costMs: now() - t0 };
    }
    const gpu = await readWebGpu(nav);
    signals.webgpu = gpu;
    const software = isSoftwareRenderer(signals.renderer);
    const bench = gl && !forced && (!software || forceBench) ? await benchmark(gl, { now }) : null;
    const { cls, why } = classify(signals, bench, { forced, stepDown });
    const profile = {
      key, cls, why, touch,
      choice: decide(cls, { touch, cores: signals.cores, webgpu: !!gpu.adapter }),
      signals, bench, cached: false, forced, costMs: now() - t0,
    };
    // A forced or crash-stepped profile is a one-off; only a measured one is kept.
    if (!forced && !stepDown) {
      try { storage?.setItem(PROFILE_KEY, JSON.stringify({ key, cls, why, signals, bench, choice: profile.choice })); } catch { /* full or private */ }
    }
    return profile;
  } catch (err) {
    return { key: null, cls: forced || 'standard', why: `the profile failed: ${err?.message || err}`, touch,
      choice: decide(forced || 'standard', { touch }), signals: {}, bench: null, cached: false, forced,
      costMs: now() - t0 };
  } finally {
    try { gl?.getExtension('WEBGL_lose_context')?.loseContext(); } catch { /* best effort */ }
  }
}
