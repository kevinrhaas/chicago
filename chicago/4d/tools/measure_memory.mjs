/**
 * WHAT A YEAR KEEPS RESIDENT, LAYER BY LAYER, AND WHO IS HOLDING IT (T-2546).
 *
 *   node tools/measure_memory.mjs [--year 1812,1835,1904] [--only desktop|mobile|both]
 *        [--no-snapshot] [--keep-geometry] [--ktx2-off] [--json out.json]
 *   node tools/measure_memory.mjs --from reading.json
 *   node tools/measure_memory.mjs --gate [--year …] [--only …] [--json out.json]
 *   node tools/measure_memory.mjs --self-test
 *   node tools/measure_memory.mjs --walk prairie [--only …] [--residency-off] [--budget-mib N] [--json out.json]
 *   node tools/measure_memory.mjs --walk prairie --captures [--only …] [--stands id,id] [--shots dir] [--json out.json]
 *
 * The owner, 2026-10-16: "I see often that in a browser on mobile we get memory
 * crashes and it's getting jittery". Frame time has ceilings
 * (`still_frame_ceilings.json`), triangles and draws have ceilings (`DETAIL`,
 * `BUDGET`), the published bytes have a budget (`SITE-BUDGET.md`) — and the thing
 * that kills a phone tab, resident memory, was read only ad hoc in per-ticket QA
 * scripts and compared with nothing. This is the meter and the ceiling.
 *
 * WHAT IS READ, per year × viewport, from the published year door (`/1835/`, as a
 * visitor arrives), after the welcome is entered at spawn, a few frames are drawn
 * so every layer is on the GPU, texture residency is let finish its uploads
 * (T-2718: it paces them, so a reading taken before could read low), and two
 * forced GCs:
 *
 *   js heap ....... `Runtime.getHeapUsage().usedSize`: the V8 heap after GC.
 *   arraybuffers .. `Runtime.getHeapUsage().backingStorageSize`: the bytes behind
 *                   every live ArrayBuffer — geometry the page still holds, GLB
 *                   bytes, decoded tables. Outside the JS heap, inside the tab.
 *   gpu buffers ... MEASURED: every `bufferData` the page's WebGL contexts were
 *                   handed, less every `deleteBuffer`, counted by an init script
 *                   that wraps the context before the renderer exists.
 *   gpu textures .. MEASURED the same way: `texImage2D` / `texStorage2D` /
 *                   `compressedTexImage2D` level by level (×4/3 after a
 *                   `generateMipmap`), and every renderbuffer (shadow maps, MSAA).
 *                   An image texture is RGBA8 on the GPU whatever it shipped as.
 *   total ......... the sum of the four: the RESIDENT ESTIMATE the gate holds. On
 *                   iOS the GPU's share counts against the same tab's limit, so
 *                   it is one number on purpose.
 *
 * And, to say WHOSE the bytes are:
 *
 *   per layer ..... each top-level child of `scene3d`, walked: the page bytes its
 *                   attributes still hold (CPU kept) and an ESTIMATE of their GPU
 *                   bytes (an attribute `upload-release.js` let go of is priced at
 *                   the byte length it recorded as it let go — T-2569, since a
 *                   compact attribute is not float32 — or, unrecorded, at its
 *                   count × item size × 4; a released index at 4 bytes when it
 *                   needs them), and
 *                   the distinct textures its materials reach. The layer sum is
 *                   printed beside the MEASURED GL total so the estimate's error
 *                   is in plain sight; only measured figures are gated.
 *   retainers ..... the ten largest ArrayBuffer retainer paths from a heap
 *                   snapshot: every `JSArrayBufferData` (the backing store), its
 *                   shortest path from the GC roots, summed by path — so a reading
 *                   says "26 MB is `assetBytes` in scene-loader's module scope",
 *                   not just "26 MB". `--no-snapshot` skips it (a snapshot is the
 *                   slow half of a reading, and the gate does not need it).
 *
 * WHAT THE FIGURES ARE AND ARE NOT. Headless Chromium draws through SwiftShader, a
 * software rasteriser, so nothing here is a timing. Bytes are bytes: the same
 * arrays and the same textures are made on a phone. What a real GPU driver adds
 * (alignment, its own copies, compression it was not given) is not counted, so
 * the total is a FLOOR on what the tab costs a phone, not a ceiling on it.
 *
 * `--gate` HOLDS THE CEILING: `tools/memory_ceilings.json` has one total per year ×
 * viewport, set from the reading written there. Bytes do not belong to a machine
 * the way milliseconds do, so the ceilings are not per machine. `--self-test`
 * boots 1835 on the phone with `?keep-geometry=1` — every page array kept, as
 * before T-2158 — and must read OVER the ceiling: the gate is shown able to go red.
 * `.github/workflows/chicago-4d-frame-time.yml` runs both, beside the frame gate.
 *
 * `--walk prairie` (T-2598) READS ALONG A WALK instead of at spawn: /1904/, Prairie
 * Avenue's centreline from south of the 1800 block to the 1600 block, a station every
 * 40 m. At each the eye is stood there, texture residency is let finish what it is
 * uploading (texture-residency.js), and the GL meter's texture bytes and residency's
 * own resident bytes are read. It fails if residency ever holds more than its tier's
 * budget, or a page error is thrown. `--residency-off` walks with `?residency=0`: the
 * before, every house picture resident wherever the eye is.
 *
 * `--captures` stands the eye at the five Glessner stands and three street-eye stands
 * instead, and shoots each three times in one page: with residency working (A), with
 * every picture forced resident (C — the before), and with residency working again
 * (D). The page has no paused clock — leaves sway, humans walk, flags fly — so A and D
 * differ by that motion alone, across the very interval C was shot inside. It reports
 * C against the nearer of A and D beside A against D: "residency is invisible here"
 * is a reading, not a claim.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT4D = path.resolve(HERE, '..');
const CEILINGS_PATH = path.join(HERE, 'memory_ceilings.json');
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
const has = (name) => process.argv.includes(name);
const MB = (b) => (b / 1048576).toFixed(1);

const FROM = argAt('--from');
const GATE = has('--gate');
const SELF_TEST = has('--self-test');
const jsonOut = argAt('--json');
const ONLY = argAt('--only') || 'both';
const WALK = argAt('--walk');
const RESIDENCY_OFF = has('--residency-off');
const CAPTURES = has('--captures');
/** T-2598's stands: Glessner from five sides and three street eyes, on foot unless aloft. */
const STANDS = [
  { id: 'glessner-ne-corner', local_e: 1410, local_n: -3200, yaw_deg: 225 },
  { id: 'glessner-front', local_e: 1405, local_n: -3230, yaw_deg: 270 },
  { id: 'glessner-north-18th', local_e: 1360, local_n: -3205, yaw_deg: 180 },
  { id: 'glessner-se-prairie', local_e: 1408, local_n: -3262, yaw_deg: 315 },
  { id: 'glessner-aloft-ne', local_e: 1440, local_n: -3170, yaw_deg: 225, altitude_m: 60, pitch_deg: -30 },
  { id: 'street-prairie-1600-south', local_e: 1402, local_n: -3000, yaw_deg: 180 },
  { id: 'street-prairie-1800-north', local_e: 1402, local_n: -3280, yaw_deg: 0 },
  { id: 'street-18th-east', local_e: 1300, local_n: -3207, yaw_deg: 90 },
];
/**
 * The Prairie Avenue walk (T-2598): the roadway's centreline, E 1402 — Glessner's east
 * face stands at E 1387.6 with the 14.7 ft setback behind the street line, and the
 * avenue is 66 ft wide — from N -3270 (south of 1808) to N -2990 (1612), every 40 m,
 * looking north up the avenue.
 */
const WALKS = {
  prairie: { year: '1904', stations: Array.from({ length: 8 }, (_, i) => ({
    local_e: 1402, local_n: -3270 + 40 * i, yaw_deg: 0 })) },
};
if (WALK && !WALKS[WALK]) { console.error(`no walk named ${WALK}: ${Object.keys(WALKS).join(', ')}`); process.exit(2); }
const YEARS = SELF_TEST ? ['1835'] : WALK ? [WALKS[WALK].year]
  : (argAt('--year') || '1812,1835,1904').split(',').filter(Boolean);
const KEEP_GEOMETRY = SELF_TEST || has('--keep-geometry');
// T-2582: `--ktx2-off` boots with `?ktx2=0`, every library sheet on its image path —
// the before to the KTX2 after, read by the same meter in the same build.
const KTX2_OFF = has('--ktx2-off');
const SNAPSHOT = !GATE && !SELF_TEST && !WALK && !has('--no-snapshot');

const VIEWPORTS = [
  { id: 'desktop', label: 'desktop 1280x800', width: 1280, height: 800, dsf: 1, mobile: false, tier: 'full' },
  // The owner's phone: touch, coarse pointer, an iPhone's pixel ratio; the renderer
  // picks its own boot tier and Sharpness (Low on a phone) as it does there.
  { id: 'mobile', label: 'phone 390x780 dpr3', width: 390, height: 780, dsf: 3, mobile: true, tier: null },
].filter((v) => (SELF_TEST ? v.mobile : ONLY === 'both' || (ONLY === 'mobile' ? v.mobile : !v.mobile)));

// ---------------------------------------------------------------- printing

function printReading(reading) {
  console.log(`memory · ${reading.measured.on} · ${reading.measured.build}`);
  for (const row of reading.rows) {
    const t = row.totals;
    console.log(`\n/${row.year}/ ${row.viewport} · tier ${row.tier} · pixel ratio ${row.pixelRatio}`
      + `${row.keepGeometry ? ' · ?keep-geometry=1' : ''}`);
    console.log(`  total ${MB(t.total)} MB = js heap ${MB(t.jsHeap)} + arraybuffers ${MB(t.arrayBuffers)}`
      + ` + gpu buffers ${MB(t.gpuBuffers)} + gpu textures ${MB(t.gpuTextures)} MB`
      + ` (renderbuffers ${MB(t.gpuRenderbuffers)} of it; shadow maps ${MB(row.shadowMapBytes)})`);
    if (row.ktx2) {
      const k = row.ktx2;
      console.log(`  library sheets: ${k.sheets.ktx2} KTX2 + ${k.sheets.fallback} image = ${MB(k.sheets.gpuBytes)} MB on the GPU`
        + ` · KTX2 ${k.reason}${k.formats ? ` (${k.formats.join(', ')})` : ''}${k.enabled && k.dropTopMip ? ' · top mip dropped' : ''}`
        + `${k.sheets.failed.length ? ` · FAILED ${k.sheets.failed.join('; ')}` : ''}`);
    }
    console.log(`  ${row.textures.distinct} distinct textures (${row.textures.images} images);`
      + ` layer estimate gpu geometry ${MB(row.layerSum.gpuGeometry)} MB vs measured buffers ${MB(t.gpuBuffers)} MB`);
    console.log('  layer                 cpu kept   gpu geom   textures   never uploaded (MB)');
    for (const l of row.layers) {
      console.log(`  ${l.name.padEnd(20)} ${MB(l.cpuKept).padStart(9)} ${MB(l.gpuGeometry).padStart(10)}`
        + ` ${MB(l.textureBytes).padStart(10)} ${MB(l.cpuNeverUploaded ?? 0).padStart(10)}  (${l.textures} tex)`);
    }
    if (row.retainers?.length) {
      console.log(`  largest ArrayBuffer retainers (snapshot: ${MB(row.snapshot.arrayBufferBytes)} MB in`
        + ` ${row.snapshot.arrayBuffers} buffers):`);
      for (const r of row.retainers) console.log(`  ${MB(r.bytes).padStart(8)} MB  ×${r.count}  ${r.path}`);
    }
    if (row.errors?.length) console.log(`  pageerrors: ${row.errors.length} — ${row.errors[0]}`);
  }
}

if (FROM) {
  printReading(JSON.parse(fs.readFileSync(FROM, 'utf8')));
  process.exit(0);
}

// ---------------------------------------------------------------- the browser

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const root = path.resolve(ROOT4D, '../../site/4d');
if (!fs.existsSync(path.join(root, '1835', 'index.html'))) {
  console.error(`no published mirror at ${root} — run tools/publish.sh first`);
  process.exit(2);
}
let build = 'unknown';
try { const b = JSON.parse(fs.readFileSync(path.join(root, 'build.json'), 'utf8')); build = b.version || b.sha || b.build || b.commit || JSON.stringify(b).slice(0, 60); } catch { /* none */ }

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.wasm': 'application/wasm',
  '.md': 'text/markdown', '.woff2': 'font/woff2', '.ktx2': 'image/ktx2',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(root, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(root) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const PORT = server.address().port;

/**
 * THE GL METER, installed before any script on the page runs. It wraps the WebGL
 * entry points that allocate GPU memory and keeps, per buffer / texture /
 * renderbuffer object, the bytes its last allocation asked for, so a re-upload
 * replaces rather than adds and a delete takes its bytes away. Bindings are read
 * back with `getParameter` at the moment of the call, which is right through
 * vertex-array objects and texture units without shadowing either.
 */
function installGlMeter() {
  const buffers = new Map(); const textures = new Map(); const renderbuffers = new Map();
  const mipped = new WeakSet();
  const BPP = {
    0x8058: 4, 0x8C43: 4, 0x8051: 4, 0x8C41: 4, 0x881A: 8, 0x8814: 16, 0x881B: 8, 0x8815: 16,
    0x8229: 1, 0x822B: 2, 0x822D: 2, 0x822E: 4, 0x822F: 4, 0x8230: 8, 0x81A5: 2, 0x81A6: 4,
    0x8CAC: 4, 0x88F0: 4, 0x8CAD: 8, 0x8D48: 1, 0x8D62: 2, 0x8D9F: 4, 0x8C3A: 4, 0x8C3D: 4,
  };
  // Block-compressed formats (T-2582: KTX2 sheets transcode to these), bytes a texel,
  // over whole 4x4 blocks: ASTC 4x4, ETC2 RGBA and BC2/3/7 at 1; ETC1/ETC2 RGB, BC1 and
  // PVRTC 4bpp at 0.5; PVRTC 2bpp at 0.25. Without these a compressed texStorage2D
  // fell through to "unsized, four channels" and read as RGBA8.
  const BLOCK = {
    0x93B0: 1, 0x93D0: 1, 0x9278: 1, 0x9279: 1, 0x83F2: 1, 0x83F3: 1, 0x8C4E: 1, 0x8C4F: 1,
    0x8E8C: 1, 0x8E8D: 1, 0x9274: 0.5, 0x9275: 0.5, 0x8D64: 0.5, 0x83F0: 0.5, 0x83F1: 0.5,
    0x8C4C: 0.5, 0x8C4D: 0.5, 0x8C00: 0.5, 0x8C02: 0.5, 0x8C01: 0.25, 0x8C03: 0.25,
  };
  const blocks = (n) => Math.max(4, Math.ceil(n / 4) * 4);
  const TYPE_BPP = { 0x1406: 4, 0x140B: 2, 0x8D61: 2, 0x1405: 4, 0x1404: 4, 0x1403: 2, 0x1402: 2 };
  const bpp = (internal, type) => {
    if (BPP[internal]) return BPP[internal];
    // Unsized formats: four channels as the GPU lays them out, at the type's width.
    return 4 * ((TYPE_BPP[type] || 1) > 1 ? TYPE_BPP[type] : 1);
  };
  const cubeOrFace = (gl, target) => (target >= 0x8515 && target <= 0x851A ? gl.TEXTURE_BINDING_CUBE_MAP : null);
  const bound2d = (gl, target) => gl.getParameter(cubeOrFace(gl, target)
    ?? (target === gl.TEXTURE_2D ? gl.TEXTURE_BINDING_2D
      : target === gl.TEXTURE_CUBE_MAP ? gl.TEXTURE_BINDING_CUBE_MAP
        : target === 0x806F ? 0x806A : target === 0x8C1A ? 0x8C1D : gl.TEXTURE_BINDING_2D));
  const setLevel = (tex, key, bytes) => {
    if (!tex) return;
    let m = textures.get(tex);
    if (!m) { m = new Map(); textures.set(tex, m); }
    m.set(key, bytes);
  };
  const dims = (src) => [src?.videoWidth || src?.naturalWidth || src?.displayWidth || src?.width || 0,
    src?.videoHeight || src?.naturalHeight || src?.displayHeight || src?.height || 0];
  for (const Ctx of [window.WebGL2RenderingContext, window.WebGLRenderingContext]) {
    if (!Ctx) continue;
    const P = Ctx.prototype;
    const wrap = (name, after) => {
      const orig = P[name];
      if (!orig) return;
      P[name] = function wrapped(...args) {
        const out = orig.apply(this, args);
        try { after(this, args, out); } catch { /* the meter never breaks the page */ }
        return out;
      };
    };
    wrap('bufferData', (gl, [target, data, , srcOffset, length]) => {
      const buf = gl.getParameter(target === gl.ELEMENT_ARRAY_BUFFER
        ? gl.ELEMENT_ARRAY_BUFFER_BINDING : target === gl.ARRAY_BUFFER ? gl.ARRAY_BUFFER_BINDING
          : target === 0x8A11 ? 0x8A28 : gl.ARRAY_BUFFER_BINDING);
      if (!buf) return;
      let bytes = typeof data === 'number' ? data : (data?.byteLength || 0);
      if (length && data?.BYTES_PER_ELEMENT) bytes = length * data.BYTES_PER_ELEMENT;
      else if (srcOffset && data?.BYTES_PER_ELEMENT) bytes -= srcOffset * data.BYTES_PER_ELEMENT;
      buffers.set(buf, bytes);
    });
    wrap('deleteBuffer', (gl, [buf]) => buffers.delete(buf));
    wrap('texImage2D', (gl, args) => {
      const [target, level, internal] = args;
      let w; let h; let type;
      if (args.length >= 8) { [, , , w, h, , , type] = args; } else { [w, h] = dims(args[5]); type = args[4]; }
      setLevel(bound2d(gl, target), `${target}:${level}`, w * h * bpp(internal, type));
    });
    wrap('compressedTexImage2D', (gl, [target, level, , w, h, , data, srcOffset, srcLength]) => {
      const bytes = typeof data === 'number' ? (srcOffset || 0) : (srcLength || data?.byteLength || 0);
      setLevel(bound2d(gl, target), `${target}:${level}`, bytes || w * h);
    });
    wrap('texStorage2D', (gl, [target, levels, internal, w, h]) => {
      const tex = bound2d(gl, target);
      const faces = target === gl.TEXTURE_CUBE_MAP ? 6 : 1;
      for (let l = 0; l < levels; l += 1) {
        const lw = Math.max(1, w >> l); const lh = Math.max(1, h >> l);
        setLevel(tex, `${target}:${l}`, faces * (BLOCK[internal]
          ? blocks(lw) * blocks(lh) * BLOCK[internal] : lw * lh * bpp(internal)));
      }
    });
    wrap('texImage3D', (gl, args) => {
      const [target, level, internal, w, h, d, , , type] = args;
      setLevel(bound2d(gl, target), `${target}:${level}`, w * h * d * bpp(internal, type));
    });
    wrap('texStorage3D', (gl, [target, levels, internal, w, h, d]) => {
      const tex = bound2d(gl, target);
      for (let l = 0; l < levels; l += 1) {
        setLevel(tex, `${target}:${l}`, Math.max(1, w >> l) * Math.max(1, h >> l)
          * (target === 0x8C1A ? d : Math.max(1, d >> l)) * bpp(internal));
      }
    });
    wrap('generateMipmap', (gl, [target]) => { const t = bound2d(gl, target); if (t) mipped.add(t); });
    wrap('deleteTexture', (gl, [tex]) => textures.delete(tex));
    const rbStore = (gl, internal, w, h, samples) => {
      const rb = gl.getParameter(gl.RENDERBUFFER_BINDING);
      if (rb) renderbuffers.set(rb, w * h * bpp(internal) * Math.max(1, samples || 1));
    };
    wrap('renderbufferStorage', (gl, [, internal, w, h]) => rbStore(gl, internal, w, h, 1));
    wrap('renderbufferStorageMultisample', (gl, [, samples, internal, w, h]) => rbStore(gl, internal, w, h, samples));
    wrap('deleteRenderbuffer', (gl, [rb]) => renderbuffers.delete(rb));
  }
  window.__memoryMeter = () => {
    let gpuBuffers = 0; let gpuTextures = 0; let gpuRenderbuffers = 0;
    for (const b of buffers.values()) gpuBuffers += b;
    for (const [tex, levels] of textures) {
      let t = 0; let explicitMips = false;
      for (const [key, bytes] of levels) { t += bytes; if (!key.endsWith(':0')) explicitMips = true; }
      gpuTextures += mipped.has(tex) && !explicitMips ? Math.round(t * 4 / 3) : t;
    }
    for (const r of renderbuffers.values()) gpuRenderbuffers += r;
    return { gpuBuffers, gpuTextures, gpuRenderbuffers,
      liveBuffers: buffers.size, liveTextures: textures.size, liveRenderbuffers: renderbuffers.size };
  };
}

/** The page side of a reading: the scene walked layer by layer. */
function readLayers() {
  const a = window.__chicago4d;
  const scene = a.scene3d;
  const seenGeo = new Set(); const seenData = new Set(); const texOwner = new Map();
  const kept = !!a.uploadRelease?.keptForHarness;
  const attrBytes = (attr, isIndex) => {
    const data = attr.isInterleavedBufferAttribute ? attr.data : attr;
    if (seenData.has(data)) return { cpu: 0, gpu: 0, pending: 0 };
    seenData.add(data);
    const arr = data.array;
    // Marked to be let go of on upload and still holding its array: it has not
    // been uploaded (a chunk this tier hides is never drawn), so it is page bytes only.
    if (arr && data.userData?.uploadReleased && !kept) return { cpu: arr.byteLength, gpu: 0, pending: arr.byteLength };
    if (arr) return { cpu: arr.byteLength, gpu: arr.byteLength, pending: 0 };
    // Let go of after upload (T-2158): the GPU still holds it at its upload layout,
    // which upload-release.js records as it lets go (T-2569: compact attributes).
    if (data.userData?.uploadBytes) return { cpu: 0, gpu: data.userData.uploadBytes, pending: 0 };
    const count = data.count ?? attr.count ?? 0;
    const item = data.stride ?? attr.itemSize ?? 1;
    const width = isIndex ? (count > 65535 ? 4 : 2) : 4;
    return { cpu: 0, gpu: count * item * width, pending: 0 };
  };
  const texBytes = (t) => {
    // A compressed texture (a KTX2 sheet) is its transcoded blocks, every level it holds.
    if (t.isCompressedTexture && t.mipmaps?.length) {
      return t.mipmaps.reduce((sum, m) => sum + (m.data?.byteLength ?? 0), 0);
    }
    const img = t.image || t.source?.data;
    const w = img?.width || img?.videoWidth || 0; const h = img?.height || img?.videoHeight || 0;
    const mips = t.generateMipmaps && t.minFilter !== 1006 && t.minFilter !== 1003;
    return Math.round(w * h * 4 * (mips ? 4 / 3 : 1));
  };
  const layers = [];
  for (const layer of scene.children) {
    const row = { name: layer.name || `(${layer.type})`, cpuKept: 0, gpuGeometry: 0, textureBytes: 0,
      textures: 0, geometries: 0, cpuNeverUploaded: 0 };
    const add = (b) => { row.cpuKept += b.cpu; row.gpuGeometry += b.gpu; row.cpuNeverUploaded += b.pending; };
    layer.traverse((o) => {
      const geo = o.geometry;
      if (geo && !seenGeo.has(geo)) {
        seenGeo.add(geo);
        row.geometries += 1;
        for (const attr of Object.values(geo.attributes || {})) {
          add(attrBytes(attr, false));
        }
        if (geo.index) add(attrBytes(geo.index, true));
      }
      // An instanced or batched mesh's own matrices and colours are GPU buffers too.
      for (const extra of [o.instanceMatrix, o.instanceColor]) {
        if (extra?.isBufferAttribute) add(attrBytes(extra, false));
      }
      const mats = Array.isArray(o.material) ? o.material : (o.material ? [o.material] : []);
      for (const m of mats) {
        for (const v of Object.values(m)) {
          if (v?.isTexture && !texOwner.has(v) && !v.isRenderTargetTexture) {
            texOwner.set(v, row.name); row.textures += 1; row.textureBytes += texBytes(v);
          }
        }
        for (const u of Object.values(m.uniforms || {})) {
          const v = u?.value;
          if (v?.isTexture && !texOwner.has(v) && !v.isRenderTargetTexture) {
            texOwner.set(v, row.name); row.textures += 1; row.textureBytes += texBytes(v);
          }
        }
      }
    });
    layers.push(row);
  }
  let shadowMapBytes = 0;
  scene.traverse((o) => {
    if (o.isLight && o.castShadow && o.shadow?.map) {
      const { width, height } = o.shadow.map;
      shadowMapBytes += width * height * 8 * (o.isPointLight ? 6 : 1);
    }
  });
  const images = new Set();
  for (const t of texOwner.keys()) images.add(t.source || t.image);
  layers.sort((x, y) => (y.cpuKept + y.gpuGeometry + y.textureBytes) - (x.cpuKept + x.gpuGeometry + x.textureBytes));
  return { layers: layers.filter((l) => l.cpuKept + l.gpuGeometry + l.textureBytes > 0), shadowMapBytes,
    textures: { distinct: texOwner.size, images: images.size },
    tier: a.detail, pixelRatio: a.renderer.getPixelRatio(), uploadRelease: a.uploadRelease ?? null };
}

// ---------------------------------------------------------------- the heap snapshot

/**
 * Parse a V8 heap snapshot written to `file` without holding it as one string
 * (a 1835 phone's runs to hundreds of MB): the node and edge arrays are read
 * straight into typed arrays from the bytes, and only the strings are JSON.
 */
function parseSnapshot(file) {
  const buf = fs.readFileSync(file);
  const find = (needle, from = 0) => buf.indexOf(Buffer.from(needle), from);
  const nodesAt = find('"nodes":[');
  const meta = JSON.parse(`${buf.subarray(0, nodesAt).toString('utf8').replace(/,\s*$/, '')}}`).snapshot.meta;
  const ints = (start) => {
    let out = new Uint32Array(1 << 20); let n = 0; let v = 0; let inNum = false; let i = start;
    for (; i < buf.length; i += 1) {
      const c = buf[i];
      if (c >= 48 && c <= 57) { v = v * 10 + (c - 48); inNum = true; } else {
        if (inNum) {
          if (n === out.length) { const g = new Uint32Array(out.length * 2); g.set(out); out = g; }
          out[n++] = v; v = 0; inNum = false;
        }
        if (c === 93) break; // ]
      }
    }
    return { arr: out.subarray(0, n), end: i };
  };
  const nodes = ints(nodesAt + 9);
  const edgesAt = find('"edges":[', nodes.end);
  const edges = ints(edgesAt + 9);
  const stringsAt = find('"strings":[', edges.end);
  const close = buf.lastIndexOf(Buffer.from(']'));
  const strings = JSON.parse(buf.subarray(stringsAt + 10, close + 1).toString('utf8'));
  return { meta, nodes: nodes.arr, edges: edges.arr, strings };
}

function retainersFrom(snap, top = 10) {
  const { meta, nodes, edges, strings } = snap;
  const NF = meta.node_fields.length; const EF = meta.edge_fields.length;
  const nType = meta.node_fields.indexOf('type'); const nName = meta.node_fields.indexOf('name');
  const nSize = meta.node_fields.indexOf('self_size'); const nEdges = meta.node_fields.indexOf('edge_count');
  const eType = meta.edge_fields.indexOf('type'); const eName = meta.edge_fields.indexOf('name_or_index');
  const eTo = meta.edge_fields.indexOf('to_node');
  const NT = meta.node_types[0]; const ET = meta.edge_types[0];
  const count = nodes.length / NF;
  const firstEdge = new Uint32Array(count + 1);
  for (let i = 0, e = 0; i < count; i += 1) { firstEdge[i] = e; e += nodes[i * NF + nEdges] * EF; firstEdge[i + 1] = e; }
  const WEAK = ET.indexOf('weak'); const SHORTCUT = ET.indexOf('shortcut');
  const ELEMENT = ET.indexOf('element'); const HIDDEN = ET.indexOf('hidden');
  // Shortest path from the root (node 0) over strong edges, as DevTools' "distance".
  const dist = new Int32Array(count).fill(-1); const parentEdge = new Int32Array(count).fill(-1);
  const parentNode = new Int32Array(count).fill(-1);
  const queue = new Uint32Array(count); let qh = 0; let qt = 0;
  dist[0] = 0; queue[qt++] = 0;
  while (qh < qt) {
    const n = queue[qh++];
    for (let e = firstEdge[n]; e < firstEdge[n + 1]; e += EF) {
      const t = edges[e + eType];
      if (t === WEAK || t === SHORTCUT) continue;
      const to = edges[e + eTo] / NF;
      if (dist[to] !== -1) continue;
      dist[to] = dist[n] + 1; parentEdge[to] = e; parentNode[to] = n; queue[qt++] = to;
    }
  }
  const nameOf = (n) => strings[nodes[n * NF + nName]];
  // An object's own `name` property, when it is a non-empty string: a three Object3D's.
  const ownName = (n) => {
    for (let e = firstEdge[n]; e < firstEdge[n + 1]; e += EF) {
      if (edges[e + eType] === ELEMENT || edges[e + eType] === HIDDEN) continue;
      if (strings[edges[e + eName]] === 'name') {
        const to = edges[e + eTo] / NF;
        if (NT[nodes[to * NF + nType]] === 'string' || NT[nodes[to * NF + nType]] === 'concatenated string') {
          const s = nameOf(to);
          return s && s.length < 40 ? s : null;
        }
      }
    }
    return null;
  };
  const edgeLabel = (e) => {
    const t = edges[e + eType];
    if (t === ELEMENT || t === HIDDEN) return '[]';
    const s = strings[edges[e + eName]];
    return ET[t] === 'context' ? `(scope).${s}` : String(s);
  };
  const groups = new Map(); let total = 0; let buffersN = 0;
  for (let n = 0; n < count; n += 1) {
    if (nameOf(n) !== 'system / JSArrayBufferData') continue;
    const bytes = nodes[n * NF + nSize];
    total += bytes; buffersN += 1;
    if (dist[n] < 0) continue;
    // Walk up the shortest path: label each hop by the edge that holds the child,
    // the holder's constructor, and — once — the nearest named three object.
    const hops = []; let layer = null; let outer = null; let cur = n; let guard = 0;
    while (parentNode[cur] > 0 && guard < 40) {
      const p = parentNode[cur]; const e = parentEdge[cur];
      const holder = nameOf(p).split(' ')[0];
      const label = edgeLabel(e);
      if (hops.length < 6 && label !== 'backing_store' && label !== 'buffer') hops.push(`${holder}.${label}`);
      if (guard > 0 && holder !== 'Scene') {
        const nm = ownName(p);
        if (nm && /^[a-z][\w-]*$/.test(nm)) { if (!layer) layer = nm; outer = nm; }
      }
      cur = p; guard += 1;
    }
    const named = layer ? `  [in '${outer}'${outer !== layer ? ` › '${layer}'` : ''}]` : '';
    const key = `${hops.slice(0, 4).join(' ← ')}${named}`;
    const g = groups.get(key) || { path: key, bytes: 0, count: 0 };
    g.bytes += bytes; g.count += 1; groups.set(key, g);
  }
  return { arrayBufferBytes: total, arrayBuffers: buffersN,
    top: [...groups.values()].sort((x, y) => y.bytes - x.bytes).slice(0, top) };
}

async function takeSnapshot(cdp, file) {
  const out = fs.openSync(file, 'w');
  const onChunk = ({ chunk }) => fs.writeSync(out, chunk);
  cdp.on('HeapProfiler.addHeapSnapshotChunk', onChunk);
  await cdp.send('HeapProfiler.takeHeapSnapshot', { reportProgress: false, captureNumericValue: false });
  cdp.off('HeapProfiler.addHeapSnapshotChunk', onChunk);
  fs.closeSync(out);
}

// ---------------------------------------------------------------- one reading

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
const rows = [];
const started = Date.now();
for (const year of YEARS) {
  for (const vp of VIEWPORTS) {
    const t0 = Date.now();
    const ctx = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      deviceScaleFactor: vp.dsf, isMobile: vp.mobile, hasTouch: vp.mobile,
    });
    await ctx.addInitScript(installGlMeter);
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    const qs = [KEEP_GEOMETRY && 'keep-geometry=1', KTX2_OFF && 'ktx2=0',
      RESIDENCY_OFF && 'residency=0', argAt('--budget-mib') && `residency-budget=${argAt('--budget-mib')}`]
      .filter(Boolean);
    const q = qs.length ? `?${qs.join('&')}` : '';
    await page.goto(`http://127.0.0.1:${PORT}/${year}/${q}`, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 420_000 });
    if (vp.tier) {
      const now = await page.evaluate(() => window.__chicago4d.detail);
      if (now !== vp.tier) await page.evaluate((t) => window.__chicago4d.setDetail(t), vp.tier);
    }
    // Into the town at spawn, as a visitor goes in; then a few frames so every
    // layer has been drawn — and so uploaded, and so released — at least once.
    await page.evaluate(async () => {
      const w = window.__chicago4d.welcome;
      const deadline = Date.now() + 90_000;
      while (w && w.state !== 'world' && Date.now() < deadline) {
        if (w.state === 'welcome') w.enter('spawn');
        if (w.state !== 'world') await new Promise((r) => setTimeout(r, 100));
      }
      for (let i = 0; i < 3; i += 1) await new Promise((r) => requestAnimationFrame(r));
      await new Promise((r) => setTimeout(r, 1000));
    });
    if (WALK && CAPTURES) {
      const settle = () => page.evaluate(async () => {
        const api = window.__chicago4d;
        const frame = () => new Promise((r) => requestAnimationFrame(r));
        const deadline = Date.now() + 90_000;
        await frame();
        while ((api.residency?.pending ?? 0) > 0 && Date.now() < deadline) await frame();
        await frame();
        return api.residency ? { resident: api.residency.resident, sources: api.residency.sources } : null;
      });
      const shoot = async () => (await page.screenshot({ type: 'png', timeout: 180_000 })).toString('base64');
      // Compared in a blank page: a pixel differs when any channel moves by more than 8.
      const cmp = await ctx.newPage();
      const compare = (shots) => cmp.evaluate(async ({ a, c, d }) => {
        const load = async (b64) => {
          const img = new Image(); img.src = `data:image/png;base64,${b64}`; await img.decode();
          const cv = document.createElement('canvas'); cv.width = img.width; cv.height = img.height;
          const g = cv.getContext('2d'); g.drawImage(img, 0, 0);
          return g.getImageData(0, 0, img.width, img.height).data;
        };
        const [pa, pc, pd] = await Promise.all([load(a), load(c), load(d)]);
        const count = (p, q) => {
          let n = 0; let se = 0;
          for (let i = 0; i < p.length; i += 4) {
            let moved = false;
            for (let k = 0; k < 3; k += 1) { const d = p[i + k] - q[i + k]; se += d * d; if (Math.abs(d) > 8) moved = true; }
            if (moved) n += 1;
          }
          const mse = se / (p.length / 4 * 3);
          return { pixels: n, share: n / (p.length / 4), psnr: mse ? 10 * Math.log10(255 * 255 / mse) : null };
        };
        const ac = count(pa, pc); const dc = count(pd, pc);
        return { noise: count(pa, pd), residency: ac.pixels <= dc.pixels ? ac : dc };
      }, shots);
      const results = [];
      const only = argAt('--stands')?.split(',');
      for (const stand of STANDS.filter((st) => !only || only.includes(st.id))) {
        const { id, ...at } = stand;
        // T-2718: an aloft stand flies through the HUD first, as `goTo` does — a
        // walker teleported aloft with the HUD's intent still on foot is put back on
        // the ground the next frame, and the shot is of the road at -30°.
        const aloft = await page.evaluate((x) => {
          const api = window.__chicago4d;
          api.setFly(typeof x.altitude_m === 'number');
          api.walker.teleport(x);
          return { flying: api.walker.state.flying, altitude: api.walker.state.altitude };
        }, at);
        const working = await settle();
        if (typeof at.altitude_m === 'number') {
          // The walker's own state: `api.flying` / `api.altitude` are copied once
          // by Object.assign and read false / 0 whatever the eye is doing.
          const now = await page.evaluate(() => {
            const { flying, altitude } = window.__chicago4d.walker.state;
            return { flying, altitude };
          });
          if (!now.flying || now.altitude < at.altitude_m / 2) {
            console.log(`::error::${id}: asked for ${at.altitude_m} m aloft, the eye is ${now.flying ? 'flying' : 'on foot'} at ${now.altitude.toFixed(1)} m — this stand did not frame what it names`);
            process.exitCode = 1;
          }
          Object.assign(aloft, { settled: now });
        }
        const a = await shoot();
        await page.evaluate(() => window.__chicago4d.textureResidency?.everything());
        const all = await settle();
        const c = await shoot();
        await page.evaluate(() => window.__chicago4d.textureResidency?.override(null));
        await settle();
        const d = await shoot();
        const diff = await compare({ a, c, d });
        results.push({ id, working, all, ...(typeof at.altitude_m === 'number' ? { aloft } : {}), ...diff });
        // Each stand is written as it is read: a phone stand costs minutes under
        // SwiftShader, and a run cut off at its clock keeps what it finished.
        if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify({ ticket: 'T-2598', partial: true, viewport: vp.id, captures: results }, null, 2)}\n`);
        if (argAt('--shots')) {
          fs.mkdirSync(argAt('--shots'), { recursive: true });
          for (const [k, v] of Object.entries({ a, c })) {
            fs.writeFileSync(path.join(argAt('--shots'), `${vp.id}-${id}-${k}.png`), Buffer.from(v, 'base64'));
          }
        }
        const pct = (x) => `${(100 * x.share).toFixed(3)} %`;
        const db = (x) => (x.psnr === null ? 'identical' : `${x.psnr.toFixed(1)} dB`);
        console.log(`  ${id}: ${working?.resident}/${working?.sources} resident · `
          + `C↔A|D ${diff.residency.pixels} px (${pct(diff.residency)}, ${db(diff.residency)})`
          + ` against motion A↔D ${diff.noise.pixels} px (${pct(diff.noise)}, ${db(diff.noise)})`);
      }
      rows.push({ year, viewport: vp.id, label: vp.label, walk: WALK, captures: results, errors, steps: [], over: 0,
        seconds: { captures: Math.round((Date.now() - t0) / 1000) } });
      await ctx.close();
      continue;
    }
    if (WALK) {
      const steps = [];
      for (const station of WALKS[WALK].stations) {
        const step = await page.evaluate(async (at) => {
          const api = window.__chicago4d;
          api.walker.teleport(at);
          const frame = () => new Promise((r) => requestAnimationFrame(r));
          const deadline = Date.now() + 60_000;
          await frame();
          while ((api.residency?.pending ?? 0) > 0 && Date.now() < deadline) await frame();
          await frame();
          const gl = window.__memoryMeter();
          const r = api.residency;
          return { ...at, gpuTextures: gl.gpuTextures + gl.gpuRenderbuffers,
            residency: r && { resident: r.resident, sources: r.sources, residentBytes: r.residentBytes,
              budgetBytes: r.budgetBytes, wantedBytes: r.wantedBytes, pending: r.pending, uploads: r.uploads,
              evictions: r.evictions, redecodes: r.redecodes, overBudget: r.overBudget } };
        }, station);
        steps.push(step);
        console.log(`  N ${step.local_n}: gpu textures ${MB(step.gpuTextures)} MB`
          + (step.residency ? ` · resident ${step.residency.resident}/${step.residency.sources}`
            + ` = ${MB(step.residency.residentBytes)} of ${MB(step.residency.budgetBytes)} MB`
            + ` (reach asks ${MB(step.residency.wantedBytes)}, ${step.residency.overBudget} turned away)`
            + ` (pending ${step.residency.pending})` : ' · residency off'));
      }
      const residency = await page.evaluate(() => {
        const r = window.__chicago4d.residency;
        return r && { ...r, problems: [...r.problems] };
      });
      const over = steps.filter((st) => st.residency && st.residency.residentBytes > st.residency.budgetBytes);
      rows.push({ year, viewport: vp.id, label: vp.label, walk: WALK, residencyOff: RESIDENCY_OFF,
        steps, residency, errors, over: over.length,
        maxGpuTextures: Math.max(...steps.map((st) => st.gpuTextures)),
        maxResidentBytes: Math.max(...steps.map((st) => st.residency?.residentBytes ?? 0)),
        seconds: { walk: Math.round((Date.now() - t0) / 1000) } });
      console.log(`walk ${WALK} ${vp.id}: max gpu textures ${MB(rows.at(-1).maxGpuTextures)} MB, `
        + `${over.length} station(s) over budget, ${errors.length} page error(s)`);
      await ctx.close();
      continue;
    }
    // T-2718: texture residency paces its uploads (4 MiB a frame on a phone), so 3
    // frames + 1 s can read the spawn mid-upload — low, and a ceiling set on it
    // too tight. Settle it as the walk does, and record what it held.
    const spawnResidency = await page.evaluate(async () => {
      const api = window.__chicago4d;
      const frame = () => new Promise((r) => requestAnimationFrame(r));
      const t0 = Date.now();
      const before = api.residency?.pending ?? 0;
      while ((api.residency?.pending ?? 0) > 0 && Date.now() - t0 < 120_000) await frame();
      await frame();
      const r = api.residency;
      return r && { pendingAtRead: before, settleMs: Date.now() - t0, resident: r.resident, sources: r.sources,
        residentBytes: r.residentBytes, budgetBytes: r.budgetBytes, wantedBytes: r.wantedBytes,
        pending: r.pending, uploads: r.uploads, evictions: r.evictions, overBudget: r.overBudget };
    });
    if (spawnResidency) {
      console.log(`  residency at spawn: ${spawnResidency.pendingAtRead} pending after 3 frames + 1 s, settled in `
        + `${spawnResidency.settleMs} ms · resident ${spawnResidency.resident}/${spawnResidency.sources} = `
        + `${MB(spawnResidency.residentBytes)} of ${MB(spawnResidency.budgetBytes)} MB (pending ${spawnResidency.pending})`);
    }
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('HeapProfiler.enable');
    await cdp.send('HeapProfiler.collectGarbage');
    await cdp.send('HeapProfiler.collectGarbage');
    const heap = await cdp.send('Runtime.getHeapUsage');
    const gl = await page.evaluate(() => window.__memoryMeter());
    const scene = await page.evaluate(readLayers);
    const totals = {
      jsHeap: heap.usedSize, arrayBuffers: heap.backingStorageSize ?? 0,
      gpuBuffers: gl.gpuBuffers, gpuTextures: gl.gpuTextures + gl.gpuRenderbuffers,
      gpuRenderbuffers: gl.gpuRenderbuffers,
    };
    totals.total = totals.jsHeap + totals.arrayBuffers + totals.gpuBuffers + totals.gpuTextures;
    const row = { year, viewport: vp.id, label: vp.label, tier: scene.tier, pixelRatio: scene.pixelRatio,
      keepGeometry: KEEP_GEOMETRY, totals, gl, heapTotal: heap.totalSize,
      shadowMapBytes: scene.shadowMapBytes, textures: scene.textures, layers: scene.layers,
      layerSum: {
        cpuKept: scene.layers.reduce((s, l) => s + l.cpuKept, 0),
        gpuGeometry: scene.layers.reduce((s, l) => s + l.gpuGeometry, 0),
        textureBytes: scene.layers.reduce((s, l) => s + l.textureBytes, 0),
        cpuNeverUploaded: scene.layers.reduce((s, l) => s + l.cpuNeverUploaded, 0),
      },
      uploadRelease: scene.uploadRelease, residency: spawnResidency, ktx2: await page.evaluate(() => window.__chicago4d.ktx2 ?? null), errors, seconds: { boot: Math.round((Date.now() - t0) / 1000) } };
    if (heap.backingStorageSize === undefined) row.note = 'this Chromium reports no backingStorageSize; arraybuffers read 0';
    if (SNAPSHOT) {
      const ts = Date.now();
      const file = path.join(os.tmpdir(), `memory-${year}-${vp.id}-${process.pid}.heapsnapshot`);
      await takeSnapshot(cdp, file);
      const r = retainersFrom(parseSnapshot(file));
      fs.rmSync(file, { force: true });
      row.snapshot = { arrayBufferBytes: r.arrayBufferBytes, arrayBuffers: r.arrayBuffers };
      row.retainers = r.top;
      row.seconds.snapshot = Math.round((Date.now() - ts) / 1000);
    }
    rows.push(row);
    console.log(`memory /${year}/ ${vp.id}: total ${MB(totals.total)} MB (${row.seconds.boot}s`
      + `${row.seconds.snapshot ? ` + snapshot ${row.seconds.snapshot}s` : ''})`);
    await ctx.close();
  }
}
await browser.close();
server.close();

const reading = {
  ticket: 'T-2546',
  measured: {
    on: new Date().toISOString(), build,
    machine: `${os.cpus()[0]?.model?.trim()} ×${os.cpus().length}`,
    seconds: Math.round((Date.now() - started) / 1000),
    method: 'published year door, welcome entered at spawn, 3 frames + 1 s, texture residency let finish its uploads, two forced GCs; '
      + 'heap and backing store from Runtime.getHeapUsage; GPU from a WebGL allocation meter',
  },
  rows,
};
if (WALK) {
  // The walk holds residency to its budget at every station, and the page to no errors.
  reading.ticket = 'T-2598';
  reading.measured.method = `the ${WALK} walk: /${WALKS[WALK].year}/, welcome entered, the eye stood at `
    + 'each station, residency let finish its uploads, 3 frames; GPU from a WebGL allocation meter';
  if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(reading, null, 2)}\n`);
  let red = 0;
  for (const row of rows) {
    if (row.over) { red += 1; console.log(`::error::${row.viewport}: residency held more than its budget at ${row.over} station(s)`); }
    if (row.errors.length) { red += 1; console.log(`::error::${row.viewport}: ${row.errors.length} pageerror(s): ${row.errors[0]}`); }
    if (row.residency?.problems?.length) console.log(`::warning::${row.viewport}: ${row.residency.problems.join('; ')}`);
  }
  console.log(`\n${rows.length} walk(s) in ${reading.measured.seconds} s`);
  // An aloft stand that did not get aloft has already set exitCode (T-2718).
  process.exit(red ? 1 : (process.exitCode ?? 0));
}
printReading(reading);
console.log(`\n${rows.length} reading(s) in ${reading.measured.seconds} s`);
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify(reading, null, 2)}\n`);

// ---------------------------------------------------------------- the gate

if (GATE || SELF_TEST) {
  const ceilings = JSON.parse(fs.readFileSync(CEILINGS_PATH, 'utf8'));
  let red = 0;
  for (const row of rows) {
    const c = ceilings.ceilings?.[row.year]?.[row.viewport];
    if (!c) { console.log(`::warning::no memory ceiling for /${row.year}/ ${row.viewport}; read, not held`); continue; }
    const over = row.totals.total > c.total_bytes;
    const line = `/${row.year}/ ${row.viewport}: ${MB(row.totals.total)} MB against a ceiling of ${MB(c.total_bytes)} MB`;
    if (SELF_TEST) {
      if (over) console.log(`self-test ok — with every page array kept, ${line}: the gate goes red`);
      else { red += 1; console.log(`::error::self-test FAILED — ?keep-geometry=1 read ${line}, under it: the ceiling could not catch the loss of T-2158`); }
    } else if (over) {
      red += 1;
      console.log(`::error::memory over its ceiling — ${line}. Bring it down, or argue the new number in tools/memory_ceilings.json with its reading`);
    } else console.log(`ok ${line}`);
    if (row.errors.length && !SELF_TEST) { red += 1; console.log(`::error::/${row.year}/ ${row.viewport}: ${row.errors.length} pageerror(s): ${row.errors[0]}`); }
  }
  process.exit(red ? 1 : 0);
}
