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
 *  2. a tap still resolves on each layer that keeps its position for one —
 *     buildings, fences, yard goods and the plank walks — through the same
 *     `pickAt` the walk calls;
 *  3. a chunk the reach held back at boot still has its arrays, and walking up
 *     to it uploads it and lets them go, without an error;
 *  4. a desktop (1280x800, mouse) releases nothing;
 *  5. a phone boots the /1904/ door too, and its far ground is batched. 1835
 *     hides a re-read of released arrays that 1904 does not: the frontage there
 *     hands the far base a fresh geometry before `batchDistantGround()` cuts it,
 *     and 1904 has nothing to protect, so the base it cut was the one already
 *     uploaded and let go (T-2180).
 *
 *   node tools/check_upload_release.mjs [siteRoot]    (default ../../site/4d)
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

/* ---- 1–3: the phone ---------------------------------------------------- */
{
  const { ctx, page, errors } = await boot({ viewport: { width: 390, height: 780 },
    deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const state = await page.evaluate(() => {
    const a = window.__chicago4d;
    const s = a.scene3d;
    const drawn = (name) => {
      const out = { released: 0, kept: 0, positionKept: 0 };
      s.getObjectByName(name)?.traverse((o) => {
        const g = o.geometry;
        if (!o.isMesh || !g?.userData.uploadReleased || o.userData.reachCulled || !o.visible) return;
        if (g.attributes.normal && g.attributes.normal.array === null) out.released += 1;
        else out.kept += 1;
        if (g.attributes.position.array) out.positionKept += 1;
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
  check('phone: a drawn plank-walk chunk has no normals left in the page but keeps its position',
    state.frontage.released > 0 && state.frontage.positionKept >= state.frontage.released,
    JSON.stringify(state.frontage));
  check('phone: drawn fence chunks are released the same way',
    state.enclosures.released > 0 && state.enclosures.positionKept >= state.enclosures.released,
    JSON.stringify(state.enclosures));
  check('phone: drawn ground tiles are released', state.terrain.released > 0,
    JSON.stringify(state.terrain));

  // 2. A tap on each layer that keeps its position for one.
  for (const [layer, api] of [['structures', 'buildings'], ['enclosures', 'enclosures'],
    ['yard', 'yard'], ['frontage', 'frontage']]) {
    const hit = await page.evaluate(async ({ layer, api }) => {
      const a = window.__chicago4d;
      const THREE = { Vector3: a.camera.position.constructor };
      const meshes = [];
      a.scene3d.getObjectByName(layer)?.traverse((o) => {
        if (o.isMesh && o.geometry?.attributes.position?.array && !o.userData.farMerged
          && !o.userData.farWalkTops && o.visible
          // A fence answers a tap only where its chunk names an owner.
          && (layer !== 'enclosures' || o.userData.pickId)) meshes.push(o);
      });
      const frame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      // A building is one instance of a batch: its triangles are the batch's,
      // placed by its own matrix, so aim at it through that matrix.
      const instance = (m, k) => {
        if (!m.isBatchedMesh) return { m, idx: m.geometry.index, matrix: m.matrixWorld, start: 0, count: null };
        const ids = Object.keys(m.userData.batchIndex ?? {}).map(Number);
        const id = ids[(k * 7919) % ids.length];
        const matrix = new a.camera.matrixWorld.constructor();
        m.getMatrixAt(id, matrix);
        matrix.premultiply(m.matrixWorld);
        const info = m._geometryInfo?.[m._instanceInfo?.[id]?.geometryIndex];
        return { m, idx: m.geometry.index, matrix, start: info?.indexStart ?? 0, count: info?.indexCount ?? null };
      };
      for (let k = 0; k < Math.min(24, meshes.length * 8); k += 1) {
        const inst = instance(meshes[(k * 7919) % meshes.length], k);
        const m = inst.m;
        const pos = m.geometry.attributes.position;
        const idx = inst.idx;
        const tris = (inst.count ?? (idx ? idx.count : pos.count)) / 3;
        const t = Math.floor(((k * 104729) % 9973) / 9973 * tris);
        const at = (j) => new THREE.Vector3().fromBufferAttribute(pos,
          idx ? idx.getX(inst.start + t * 3 + j) : t * 3 + j).applyMatrix4(inst.matrix);
        const p0 = at(0); const p1 = at(1); const p2 = at(2);
        const c = p0.clone().add(p1).add(p2).multiplyScalar(1 / 3);
        const nrm = p1.clone().sub(p0).cross(p2.clone().sub(p0));
        if (nrm.lengthSq() === 0) continue;
        nrm.normalize();
        // Stand off the face along its normal (level), and look back at it.
        const flat = Math.hypot(nrm.x, nrm.z) > 0.2 ? new THREE.Vector3(nrm.x, 0, nrm.z).normalize()
          : new THREE.Vector3(1, 0, 0);
        const stand = c.clone().addScaledVector(flat, 7);
        const de = c.x - stand.x; const dn = -(c.z - stand.z);
        a.walker.teleport({ local_e: stand.x, local_n: -stand.z,
          yaw_deg: ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360, pitch_deg: 0 });
        await frame();
        const eye = a.camera.position;
        const pitch = (Math.atan2(c.y - eye.y, Math.hypot(c.x - eye.x, c.z - eye.z)) * 180) / Math.PI;
        a.walker.teleport({ local_e: stand.x, local_n: -stand.z,
          yaw_deg: ((Math.atan2(de, dn) * 180) / Math.PI + 360) % 360, pitch_deg: pitch });
        await frame();
        const ndc = c.clone().project(a.camera);
        if (Math.abs(ndc.x) > 0.95 || Math.abs(ndc.y) > 0.95 || ndc.z > 1) continue;
        const found = a[api].pickAt({ x: ndc.x, y: ndc.y }, a.camera);
        if (found) return { tries: k + 1, id: found.id ?? found.record?.id ?? true };
      }
      return null;
    }, { layer, api });
    check(`phone: a tap still resolves on ${layer}`, !!hit, JSON.stringify(hit));
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
      positionKept: !!far.geometry.attributes.position.array };
  });
  check('phone: a held-back walk chunk is uploaded and let go when walked to',
    walk.found && walk.released && walk.positionKept, JSON.stringify(walk));
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
{
  const { ctx, page, errors } = await boot({ viewport: { width: 1280, height: 800 } });
  const census = await page.evaluate(() => window.__chicago4d.uploadRelease);
  check('desktop: 1835 boots with no page error', errors.length === 0, errors.slice(0, 3).join(' | '));
  check('desktop: nothing is released', census?.attributes === 0, JSON.stringify(census));
  await ctx.close();
}

/* ---- 5: the phone at the 1904 door ------------------------------------ */
{
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
  await ctx.close();
}

await browser.close();
server.close();
const failed = results.filter((ok) => !ok).length;
console.log(failed ? `FAIL upload release: ${failed} of ${results.length} checks`
  : `PASS upload release: ${results.length} checks`);
process.exit(failed ? 1 : 0);
