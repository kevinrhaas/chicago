#!/usr/bin/env node
/**
 * check_upload_release.mjs — T-2158: a phone keeps the town on the GPU, not
 * twice, and still answers a tap and walks.
 *
 * The smoke reads vertices back to check what was laid, so it boots with
 * `?keep-geometry=1` (upload-release.js). This is the run without it, on the
 * PUBLISHED mirror, and it asks what the release could break:
 *
 *  1. a phone (390x780, touch) boots 1835 with no page error and actually lets
 *     go of the page arrays: the census counts them, and a released attribute
 *     of a drawn chunk has no array left while its position is kept;
 *  2. a tap still resolves on every pickable layer — buildings, fences, yard
 *     goods and the plank walks — through the same `pickAt` the walk calls; none
 *     of them keeps its triangles on a phone (they are picked by the one-pixel
 *     id pass, gpu-pick.js: T-2572 for the last three, T-2573 for the buildings'
 *     batches, which keep neither position nor index), so they are aimed at by
 *     their kept bounding spheres — a building by its instance's;
 *  3. a chunk the reach held back at boot still has its arrays, and walking up
 *     to it uploads it and lets them go, without an error;
 *  4. a desktop (1280x800, mouse) releases nothing, and there, where the
 *     triangles still exist, the GPU pick answers a fixed list of taps on the
 *     plank walks, fences, yard goods and buildings exactly as the old raycast
 *     does (`pickAtRaycast`, the oracle): the same id, at the same distance
 *     (T-2572, T-2573), and the gaze target's read-later pick (`pickAtAsync`)
 *     answers each of those taps exactly as the tap's own read does (T-2723);
 *  5. a phone boots the /1904/ door too, and its far ground is batched. 1835
 *     hides a re-read of released arrays that 1904 does not: the frontage there
 *     hands the far base a fresh geometry before `batchDistantGround()` cuts it,
 *     and 1904 has nothing to protect, so the base it cut was the one already
 *     uploaded and let go (T-2180);
 *  6. on that /1904/ phone, what nothing reads again is let go (T-2548): no GLB is
 *     banked for a detail switch, every building's source geometry goes once its
 *     batch holds a copy, and a building's decoded images close once uploaded —
 *     and a switch to `full` and back still rebuilds the town, re-reading the
 *     GLBs, draws the frame it drew before, and still answers a tap.
 *
 *   node tools/check_upload_release.mjs [siteRoot]    (default ../../site/4d)
 *   CHECK_ONLY=1835|desktop|1904   one part, each inside a 600 s foreground call
 *                                  (the whole check runs longer; CI runs it all)
 *   PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome
 */
import { createServer } from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = execSync('npm root -g').toString().trim();
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(process.argv[2] ?? path.join(HERE, '..', '..', '..', 'site', '4d'));
if (!existsSync(path.join(ROOT, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.css': 'text/css', '.glb': 'model/gltf-binary', '.bin': 'application/octet-stream',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml' };
const server = createServer((req, res) => {
  const url = decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/^\/4d\//, '/');
  let file = path.join(ROOT, url);
  if (existsSync(file) && statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  createReadStream(file).pipe(res);
});
const PORT = Number(process.env.CHECK_PORT || 4387);
await new Promise((r) => server.listen(PORT, r));

const ONLY = process.env.CHECK_ONLY || '';
const part = (name) => !ONLY || ONLY === name;
const results = [];
const check = (name, ok, detail = '') => {
  results.push(ok);
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`);
};

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});

async function boot(profile, door = '/walk/?year=1835') {
  const ctx = await browser.newContext(profile);
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(`http://127.0.0.1:${PORT}${door}${process.env.CHECK_QUERY || ""}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error,
    null, { timeout: 600000 });
  await page.waitForTimeout(1500);
  return { ctx, page, errors };
}

/**
 * Page-side: stand off a chunk's kept bounding sphere, look at its centre and
 * scan a small grid of taps until the layer answers. For layers that keep no
 * triangles on a phone (T-2572), where the old face-centroid aim cannot read one.
 */
async function aimBySphere({ layer, api }) {
  const a = window.__chicago4d;
  const frame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const meshes = [];
  a.scene3d.getObjectByName(layer)?.traverse((o) => {
    // Not `visible`: the reach hides a far chunk, and the walk below brings it back.
    if (o.isMesh && o.geometry?.boundingSphere && !o.userData.farMerged && !o.userData.farWalkTops
      && !o.userData.crossStreet
      && o.geometry.boundingSphere.radius < (layer === 'enclosures' ? 200 : 60)
      && (layer !== 'enclosures' || o.userData.pickId)) meshes.push(o);
  });
  for (let k = 0; k < Math.min(12, meshes.length); k += 1) {
    const m = meshes[(k * 7919) % meshes.length];
    const c = m.geometry.boundingSphere.center.clone().applyMatrix4(m.matrixWorld);
    const back = m.geometry.boundingSphere.radius + 4;
    const yaw = (k * 137 * Math.PI) / 180;
    // A camera of the tap's own, stood off the sphere and looking at its centre:
    // `pickAt` takes any camera, so no frame has to be drawn to aim.
    const cam = a.camera.clone();
    cam.position.set(c.x - Math.sin(yaw) * back, c.y + 1.5, c.z - Math.cos(yaw) * back);
    cam.lookAt(c);
    cam.updateMatrixWorld(true);
    // Walk there first, so the furniture reach draws the chunk: a tap only
    // lands on what the frame may draw (gpu-pick.js `drawable`).
    a.walker.teleport({ local_e: cam.position.x, local_n: -cam.position.z, yaw_deg: 0, pitch_deg: 0 });
    await frame();
    for (const y of [0, -0.1, 0.1, -0.2, 0.2, -0.3]) {
      for (const x of [0, -0.1, 0.1, -0.2, 0.2]) {
        const found = a[api].pickAt({ x, y }, cam);
        if (found) {
          return { tries: k + 1, id: found.id ?? found.record?.id ?? true,
            distance: Math.round(found.distance * 100) / 100,
            released: m.geometry.attributes.position.array === null };
        }
      }
    }
  }
  return null;
}

/**
 * Page-side, on the desktop (nothing released): aim at fixed face centroids,
 * as the phone's building tap does, and ask both engines. Every tap the raycast
 * answers must come back from the GPU with the same id at the same distance.
 */
async function gpuAgainstRaycast({ layer, api }) {
  const a = window.__chicago4d;
  const V3 = a.camera.position.constructor;
  const meshes = [];
  a.scene3d.getObjectByName(layer)?.traverse((o) => {
    if (o.isMesh && o.geometry?.attributes.position?.array && !o.geometry.index
      && !o.userData.farMerged && !o.userData.farWalkTops && o.visible
      && (layer !== 'enclosures' || o.userData.pickId)) meshes.push(o);
  });
  let compared = 0, laterCompared = 0;
  const differ = [], laterDiffer = [];
  for (let k = 0; k < 80 && compared < 12 && meshes.length; k += 1) {
    const m = meshes[(k * 7919) % meshes.length];
    const pos = m.geometry.attributes.position;
    const t = Math.floor(((k * 104729) % 9973) / 9973 * (pos.count / 3));
    const at = (j) => new V3().fromBufferAttribute(pos, t * 3 + j).applyMatrix4(m.matrixWorld);
    const p0 = at(0); const p1 = at(1); const p2 = at(2);
    const c = p0.clone().add(p1).add(p2).multiplyScalar(1 / 3);
    const nrm = p1.clone().sub(p0).cross(p2.clone().sub(p0));
    if (nrm.lengthSq() === 0) continue;
    nrm.normalize();
    const flat = Math.hypot(nrm.x, nrm.z) > 0.2 ? new V3(nrm.x, 0, nrm.z).normalize() : new V3(1, 0, 0);
    const stand = c.clone().addScaledVector(flat, 7);
    stand.y += 1.2;
    const cam = a.camera.clone();
    cam.position.copy(stand);
    cam.lookAt(c);
    cam.updateMatrixWorld(true);
    const ndc = c.clone().project(cam);
    if (Math.abs(ndc.x) > 0.95 || Math.abs(ndc.y) > 0.95 || ndc.z > 1) continue;
    const cast = a[api].pickAtRaycast({ x: ndc.x, y: ndc.y }, cam);
    if (!cast) continue;
    const gpu = a[api].pickAt({ x: ndc.x, y: ndc.y }, cam);
    compared += 1;
    const tolerance = Math.max(0.05, cast.distance * 0.002);
    if (!gpu || gpu.id !== cast.id || Math.abs(gpu.distance - cast.distance) > tolerance) {
      differ.push({ k, cast: [cast.id, cast.distance], gpu: gpu ? [gpu.id, gpu.distance] : null });
    }
    // T-2723: the gaze target's read, answered later, answers what the tap's did.
    if (a[api].pickAtAsync) {
      const later = await a[api].pickAtAsync({ x: ndc.x, y: ndc.y }, cam);
      laterCompared += 1;
      if ((later?.id ?? null) !== (gpu?.id ?? null) || (gpu && later.distance !== gpu.distance)) {
        laterDiffer.push({ k, gpu: gpu ? [gpu.id, gpu.distance] : null, later: later ? [later.id, later.distance] : null });
      }
    }
  }
  return { compared, differ, laterCompared, laterDiffer };
}

/**
 * Page-side: a building is one instance of a batch, so it is aimed at through
 * its instance's kept bounding sphere (T-2573) — the batch keeps no triangles
 * on a phone. Stand off the sphere, look at its centre, scan a small grid.
 */
async function aimBatchBySphere({ layer, api }) {
  const a = window.__chicago4d;
  const M4 = a.camera.matrixWorld.constructor;
  const batches = [];
  a.scene3d.getObjectByName(layer)?.traverse((o) => { if (o.isBatchedMesh) batches.push(o); });
  for (let k = 0; k < Math.min(16, batches.length * 6); k += 1) {
    const b = batches[(k * 7919) % batches.length];
    const ids = Object.keys(b.userData.batchIndex ?? {}).map(Number).filter((i) => b.getVisibleAt(i));
    if (!ids.length) continue;
    const id = ids[(k * 104729) % ids.length];
    const matrix = b.getMatrixAt(id, new M4()).premultiply(b.matrixWorld);
    // A Sphere to read into: the release computed the batch geometry's own.
    const sphere = b.getBoundingSphereAt(b.getGeometryIdAt(id), b.geometry.boundingSphere.clone());
    const c = sphere.center.clone().applyMatrix4(matrix);
    const r = sphere.radius * matrix.getMaxScaleOnAxis();
    const back = r + 6;
    const yaw = (k * 137 * Math.PI) / 180;
    const cam = a.camera.clone();
    cam.position.set(c.x - Math.sin(yaw) * back, c.y + 1.5, c.z - Math.cos(yaw) * back);
    cam.lookAt(c);
    cam.updateMatrixWorld(true);
    for (const y of [0, -0.1, 0.1, -0.2, 0.2]) {
      for (const x of [0, -0.1, 0.1, -0.2, 0.2]) {
        const found = a[api].pickAt({ x, y }, cam);
        if (found) {
          return { tries: k + 1, id: found.id ?? true,
            distance: Math.round(found.distance * 100) / 100,
            released: b.geometry.attributes.position.array === null
              && b.geometry.index.array.length === 0,
            r: Math.round(r * 10) / 10 };
        }
      }
    }
  }
  return null;
}

/**
 * Page-side, on the desktop (nothing released): aim at fixed face centroids of
 * fixed buildings, through each instance's matrix, and ask both engines — the
 * buildings' form of `gpuAgainstRaycast` (T-2573).
 */
async function batchGpuAgainstRaycast({ layer, api }) {
  const a = window.__chicago4d;
  const V3 = a.camera.position.constructor;
  const M4 = a.camera.matrixWorld.constructor;
  const batches = [];
  a.scene3d.getObjectByName(layer)?.traverse((o) => {
    if (o.isBatchedMesh && o.geometry.attributes.position.array && o.geometry.index?.array?.length) batches.push(o);
  });
  let compared = 0, laterCompared = 0;
  const differ = [], laterDiffer = [];
  for (let k = 0; k < 120 && compared < 16 && batches.length; k += 1) {
    const b = batches[(k * 7919) % batches.length];
    const ids = Object.keys(b.userData.batchIndex ?? {}).map(Number).filter((i) => b.getVisibleAt(i));
    if (!ids.length) continue;
    const id = ids[(k * 104729) % ids.length];
    const matrix = b.getMatrixAt(id, new M4()).premultiply(b.matrixWorld);
    const info = b._geometryInfo[b.getGeometryIdAt(id)];
    const pos = b.geometry.attributes.position;
    const idx = b.geometry.index;
    const t = Math.floor(((k * 104729) % 9973) / 9973 * (info.count / 3));
    const at = (j) => new V3().fromBufferAttribute(pos, idx.getX(info.start + t * 3 + j)).applyMatrix4(matrix);
    const p0 = at(0); const p1 = at(1); const p2 = at(2);
    const c = p0.clone().add(p1).add(p2).multiplyScalar(1 / 3);
    const nrm = p1.clone().sub(p0).cross(p2.clone().sub(p0));
    if (nrm.lengthSq() === 0) continue;
    nrm.normalize();
    const flat = Math.hypot(nrm.x, nrm.z) > 0.2 ? new V3(nrm.x, 0, nrm.z).normalize() : new V3(1, 0, 0);
    const stand = c.clone().addScaledVector(flat, 7);
    stand.y += 1.2;
    const cam = a.camera.clone();
    cam.position.copy(stand);
    cam.lookAt(c);
    cam.updateMatrixWorld(true);
    const ndc = c.clone().project(cam);
    if (Math.abs(ndc.x) > 0.95 || Math.abs(ndc.y) > 0.95 || ndc.z > 1) continue;
    const cast = a[api].pickAtRaycast({ x: ndc.x, y: ndc.y }, cam);
    if (!cast) continue;
    const gpu = a[api].pickAt({ x: ndc.x, y: ndc.y }, cam);
    compared += 1;
    const tolerance = Math.max(0.05, cast.distance * 0.002);
    if (!gpu || gpu.id !== cast.id || Math.abs(gpu.distance - cast.distance) > tolerance) {
      differ.push({ k, cast: [cast.id, cast.distance], gpu: gpu ? [gpu.id, gpu.distance] : null });
    }
    // T-2723: the gaze target's read, answered later, answers what the tap's did.
    if (a[api].pickAtAsync) {
      const later = await a[api].pickAtAsync({ x: ndc.x, y: ndc.y }, cam);
      laterCompared += 1;
      if ((later?.id ?? null) !== (gpu?.id ?? null) || (gpu && later.distance !== gpu.distance)) {
        laterDiffer.push({ k, gpu: gpu ? [gpu.id, gpu.distance] : null, later: later ? [later.id, later.distance] : null });
      }
    }
  }
  return { compared, differ, laterCompared, laterDiffer };
}

/* ---- 1–3: the phone ---------------------------------------------------- */
if (part('1835')) {
  const { ctx, page, errors } = await boot({ viewport: { width: 390, height: 780 },
    deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const state = await page.evaluate(() => {
    const a = window.__chicago4d;
    const s = a.scene3d;
    const drawn = (name) => {
      const out = { released: 0, kept: 0, positionKept: 0, positionReleased: 0 };
      s.getObjectByName(name)?.traverse((o) => {
        const g = o.geometry;
        if (!o.isMesh || !g?.userData.uploadReleased || o.userData.reachCulled || !o.visible) return;
        if (g.attributes.normal && g.attributes.normal.array === null) out.released += 1;
        else out.kept += 1;
        if (g.attributes.position.array) out.positionKept += 1;
        else out.positionReleased += 1;
      });
      return out;
    };
    return { error: a.error ?? null, census: a.uploadRelease,
      frontage: drawn('frontage'), enclosures: drawn('enclosures'), terrain: drawn('terrain') };
  });
  check('phone: 1835 boots with no page error', !state.error && errors.length === 0,
    state.error || errors.slice(0, 3).join(' | '));
  check('phone: the page arrays are let go once uploaded',
    state.census?.attributes > 0 && state.census.keptForHarness === false,
    JSON.stringify(state.census));
  // T-2572: picked on the GPU, so not even the position is kept for a tap.
  check('phone: a drawn plank-walk chunk has no normals and no position left in the page',
    state.frontage.released > 0 && state.frontage.positionKept === 0
    && state.frontage.positionReleased >= state.frontage.released,
    JSON.stringify(state.frontage));
  check('phone: drawn fence chunks are released the same way',
    state.enclosures.released > 0 && state.enclosures.positionKept === 0
    && state.enclosures.positionReleased >= state.enclosures.released,
    JSON.stringify(state.enclosures));
  check('phone: drawn ground tiles are released', state.terrain.released > 0,
    JSON.stringify(state.terrain));

  // 2. A tap on each layer, aimed at through the bounding spheres they keep
  // (T-2572); the buildings below (T-2573).
  for (const [layer, api] of [['enclosures', 'enclosures'], ['yard', 'yard'], ['frontage', 'frontage']]) {
    const hit = await page.evaluate(aimBySphere, { layer, api });
    check(`phone: a tap still resolves on ${layer}, with its triangles let go`,
      !!hit && hit.released, JSON.stringify(hit));
  }
  // T-2573: the buildings' batches keep neither position nor index (the index
  // keeps its element type, in an empty array, for three's multi-draw), and a
  // building is aimed at by its instance's kept bounding sphere.
  const batches = await page.evaluate(() => {
    const out = { batches: 0, positionKept: 0, indexKept: 0, released: 0 };
    window.__chicago4d.scene3d.getObjectByName('structures')?.traverse((o) => {
      if (!o.isBatchedMesh || !o.geometry.userData.uploadReleased) return;
      out.batches += 1;
      if (o.geometry.attributes.position.array) out.positionKept += 1;
      if (o.geometry.index?.array?.length) out.indexKept += 1;
      if (!o.geometry.attributes.position.array && o.geometry.index?.array?.length === 0) out.released += 1;
    });
    return out;
  });
  check('phone: the buildings\' batches keep no position and no index in the page',
    batches.batches > 0 && batches.positionKept === 0 && batches.indexKept === 0
    && batches.released === batches.batches, JSON.stringify(batches));
  {
    const hit = await page.evaluate(aimBatchBySphere, { layer: 'structures', api: 'buildings' });
    check('phone: a tap still resolves on structures, with its triangles let go',
      !!hit && hit.released, JSON.stringify(hit));
  }

  // 3. A chunk the reach held back at boot is uploaded, and let go, when reached.
  const walk = await page.evaluate(async () => {
    const a = window.__chicago4d;
    const frame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    let far = null;
    a.scene3d.getObjectByName('frontage')?.traverse((o) => {
      if (!far && o.isMesh && o.userData.reachCulled && !o.userData.crossStreet
        && o.geometry?.attributes.normal?.array) far = o;
    });
    if (!far) return { found: false };
    if (!far.geometry.boundingSphere) far.geometry.computeBoundingSphere();
    const c = far.geometry.boundingSphere.center.clone().applyMatrix4(far.matrixWorld);
    a.walker.teleport({ local_e: c.x + 3, local_n: -c.z + 3, yaw_deg: 225, pitch_deg: -10 });
    for (let i = 0; i < 30; i += 1) await frame();
    for (let yaw = 0; yaw < 360; yaw += 45) {
      a.walker.teleport({ local_e: c.x + 3, local_n: -c.z + 3, yaw_deg: yaw, pitch_deg: -20 });
      await frame();
    }
    return { found: true, name: far.name, released: far.geometry.attributes.normal.array === null,
      positionReleased: far.geometry.attributes.position.array === null };
  });
  check('phone: a held-back walk chunk is uploaded and let go when walked to',
    walk.found && walk.released && walk.positionReleased, JSON.stringify(walk));
  check('phone: no page error after the taps and the walk', errors.length === 0,
    errors.slice(0, 3).join(' | '));

  // A visitor who raises the detail on a phone: the far merge meets released
  // chunks (and must leave them chunked), the cross streets come back, and the
  // trees are rebuilt and released again.
  const raised = await page.evaluate(async () => {
    const a = window.__chicago4d;
    const frame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    await a.setDetail('full');
    a.walker.teleport({ local_e: 0, local_n: 0, yaw_deg: 90, pitch_deg: -25 });
    a.walker.setFlying?.(true);
    for (let yaw = 0; yaw < 360; yaw += 30) {
      a.walker.teleport({ local_e: 0, local_n: 0, yaw_deg: yaw, pitch_deg: -25 });
      await frame();
    }
    return { detail: a.detail ?? null, error: a.error ?? null, census: a.uploadRelease };
  });
  check('phone: raising the detail to full draws with no page error',
    errors.length === 0 && !raised.error, errors.slice(0, 3).join(' | ') || JSON.stringify(raised));
  await ctx.close();
}

/* ---- 4: the desktop ---------------------------------------------------- */
if (part('desktop')) {
  const { ctx, page, errors } = await boot({ viewport: { width: 1280, height: 800 } });
  const census = await page.evaluate(() => window.__chicago4d.uploadRelease);
  check('desktop: 1835 boots with no page error', errors.length === 0, errors.slice(0, 3).join(' | '));
  check('desktop: nothing is released', census?.attributes === 0 && census.sources === 0
    && census.images === 0, JSON.stringify(census));
  for (const [layer, api] of [['frontage', 'frontage'], ['enclosures', 'enclosures'], ['yard', 'yard']]) {
    const r = await page.evaluate(gpuAgainstRaycast, { layer, api });
    check(`desktop: the GPU pick answers ${r.compared} fixed taps on ${layer} as the raycast does`,
      r.compared >= 8 && r.differ.length === 0, JSON.stringify(r.differ.slice(0, 3)));
    if (layer !== 'yard') { // the gaze target's layers (T-2723)
      check(`desktop: the gaze target's read-later pick answers the same ${r.laterCompared} taps on ${layer} as the tap's`,
        r.laterCompared === r.compared && r.laterDiffer.length === 0, JSON.stringify(r.laterDiffer.slice(0, 3)));
    }
  }
  {
    const r = await page.evaluate(batchGpuAgainstRaycast, { layer: 'structures', api: 'buildings' });
    check(`desktop: the GPU pick answers ${r.compared} fixed taps on structures as the raycast does`,
      r.compared >= 10 && r.differ.length === 0, JSON.stringify(r.differ.slice(0, 3)));
    check(`desktop: the gaze target's read-later pick answers the same ${r.laterCompared} taps on structures as the tap's`,
      r.laterCompared === r.compared && r.laterDiffer.length === 0, JSON.stringify(r.laterDiffer.slice(0, 3)));
  }
  await ctx.close();
}

/* ---- 5–6: the phone at the 1904 door ---------------------------------- */
if (part('1904')) {
  const { ctx, page, errors } = await boot({ viewport: { width: 390, height: 780 },
    deviceScaleFactor: 2, isMobile: true, hasTouch: true }, '/1904/');
  const state = await page.evaluate(() => {
    const a = window.__chicago4d;
    let base = null;
    a.scene3d?.getObjectByName('terrain')?.traverse((o) => {
      if (o.name.startsWith('terrain_base__')) {
        base = { batched: !!o.isBatchedMesh,
          pieces: o.userData.spatialBatch?.pieces ?? 0 };
      }
    });
    return { scene: a.scene?.id ?? null, error: a.error ? String(a.error) : null,
      census: a.uploadRelease, base };
  });
  check('phone: /1904/ boots the 1904 scene with no page error',
    state.scene === '1904' && !state.error && errors.length === 0,
    state.error || errors.slice(0, 3).join(' | '));
  check('phone: /1904/ lets go of its page arrays', state.census?.attributes > 0,
    JSON.stringify(state.census));
  check('phone: /1904/ batches the far ground it has already uploaded',
    state.base?.batched && state.base.pieces > 1, JSON.stringify(state.base));

  // 6. T-2548: what a phone never reads again is let go, and a switch still works.
  const held = () => page.evaluate(() => {
    const a = window.__chicago4d;
    let rows = 0; let kept = 0;
    for (const row of a.registry.values()) {
      if (!row.gltf) continue;
      rows += 1;
      row.gltf.scene.traverse((o) => { if (o.geometry?.attributes.position) kept += 1; });
    }
    return { rows, kept, banked: a.bankedAssets, census: a.uploadRelease };
  });
  const before = await held();
  check('phone: /1904/ banks no GLB for a detail switch', before.banked === 0, JSON.stringify(before));
  check('phone: /1904/ lets go of every building\'s source geometry',
    before.rows > 0 && before.kept === 0 && before.census.sources >= before.rows
    && before.census.sourceBytes > 0, JSON.stringify(before));
  // T-2596: since Glessner v4 joined the Prairie houses in KTX2, a 1904 building may hold
  // no decoded image at all — a KTX2 texture is a compressed upload, never an ImageBitmap.
  // So the claim is that none is left OPEN: closed ones (width 0) are what this released,
  // and a town with no bitmap left to close passes on its compressed textures alone.
  const bitmaps = await page.evaluate(() => {
    let open = 0; let closed = 0; let compressed = 0; const seen = new Set();
    window.__chicago4d.buildings?.group?.traverse((o) => {
      for (const m of [].concat(o.material ?? [])) {
        for (const v of Object.values(m)) {
          if (!v?.isTexture || !v.source || seen.has(v.source)) continue;
          seen.add(v.source);
          if (v.isCompressedTexture) compressed += 1;
          else if (typeof ImageBitmap !== 'undefined' && v.source.data instanceof ImageBitmap) {
            if (v.source.data.width > 0) open += 1; else closed += 1;
          }
        }
      }
    });
    return { open, closed, compressed };
  });
  check('phone: /1904/ closes the buildings\' decoded images once uploaded',
    bitmaps.open === 0 && (before.census.images > 0 ? before.census.imageBytes > 0 : bitmaps.compressed > 0),
    JSON.stringify({ ...bitmaps, census: before.census }));
  const look = () => page.evaluate(async () => {
    const a = window.__chicago4d;
    // Past the welcome, which holds the frame while it is up (gate-frame.js).
    const deadline = Date.now() + 20000;
    while (a.welcome && a.welcome.state !== 'world' && Date.now() < deadline) {
      if (a.welcome.state === 'welcome') a.welcome.enter('spawn');
      if (a.welcome.state !== 'world') await new Promise((r) => setTimeout(r, 100));
    }
    a.setAnimationHold(true);
    const p = a.buildings.positionOf('glessner_house');
    const e = p.x + 28; const n = -p.z + 22;
    a.walker.teleport({ local_e: e, local_n: n, pitch_deg: 8,
      yaw_deg: ((Math.atan2(p.x - e, -p.z - n) * 180) / Math.PI + 360) % 360 });
    const frame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    for (let i = 0; i < 8; i += 1) await frame();
    const sig = await a.capture(96);
    let hit = null;
    for (const y of [0, 0.1, 0.2, -0.1]) {
      for (const x of [0, -0.2, 0.2]) {
        const found = hit ? null : a.buildings.pickAt({ x, y }, a.camera);
        hit = hit ?? found?.id ?? found?.record?.id ?? null;
      }
    }
    return { cells: sig.cells, hit, detail: a.detail ?? null };
  });
  const shown = await look();
  const switched = await page.evaluate(async () => {
    const a = window.__chicago4d;
    await a.setDetail('full');
    const full = a.detail;
    await a.setDetail('light');
    return { full, back: a.detail, error: a.error ? String(a.error) : null };
  });
  const after = await held();
  const again = await look();
  const moved = shown.cells.reduce((m, v, i) => Math.max(m, Math.abs(v - again.cells[i])), 0);
  check('phone: /1904/ switches to full and back with no page error',
    switched.full === 'full' && switched.back === 'light' && !switched.error && errors.length === 0,
    errors.slice(0, 3).join(' | ') || JSON.stringify(switched));
  check('phone: /1904/ after the switch banks nothing and holds no source geometry',
    after.banked === 0 && after.kept === 0 && after.census.sources > before.census.sources,
    JSON.stringify(after));
  check('phone: /1904/ draws the frame it drew before the switch', moved <= 2,
    `largest cell change ${moved} of 255`);
  check('phone: /1904/ still answers a tap on a building after the switch', !!again.hit,
    JSON.stringify({ before: shown.hit, after: again.hit }));
  await ctx.close();
}

await browser.close();
server.close();
const failed = results.filter((ok) => !ok).length;
console.log(failed ? `FAIL upload release: ${failed} of ${results.length} checks`
  : `PASS upload release: ${results.length} checks`);
process.exit(failed ? 1 : 0);
