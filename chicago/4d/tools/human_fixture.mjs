#!/usr/bin/env node
/**
 * human_fixture.mjs — T-1787. THE PORTABLE-HUMAN EXPORT PATH, PROVED IN THE BROWSER.
 *
 *   node tools/human_fixture.mjs           open every human GLB under assets/humans/ (the
 *                                          Blender exports and their Meshopt derivatives)
 *                                          at 1280x800 and 390x780 and hold each to the
 *                                          acceptance below; then hold the structural
 *                                          readings to data/humans/fixture.measure.json
 *   node tools/human_fixture.mjs --write   the same, and WRITE the measure file: run it
 *                                          after tools/human_export.sh moves any byte
 *   node tools/human_fixture.mjs --check   no browser: every GLB has a measure entry whose
 *                                          sha256 is the file's, and every verdict is ok —
 *                                          so a rebuild that is not re-measured fails in
 *                                          tools/check.sh
 *
 * Serves chicago/4d on a loopback port and opens tools/human_fixture.html (never
 * published), which loads each file through the renderer's own GLTFLoader and
 * Meshopt decoder. A file passes only if, in the browser:
 *
 *   - it opens with no page error and no console error
 *   - its skin carries all 56 contract bones and the three required sockets
 *   - raising the left upper arm moves the surface (skinning deforms)
 *   - `idle` and `walk` both turn bones when played (and `walk` states its speed)
 *   - on lod0/lod1 each required morph moves the surface; lod2/lod3 may have none
 *   - the five required material slots load, and the texture decodes at its size
 *   - its rest frame is metric: 0.45-2.3 m tall, soles on y = 0
 *   - a Meshopt derivative's decoded rest frame is its master's to the millimetre,
 *     with the same triangles, joints, morphs and clips — which is what
 *     tools/human_contract.py cannot read from a quantised file's JSON
 *
 * The budgets it records are the ones docs/HUMAN-ASSET-CONTRACT.md § 8 publishes.
 * Frame times are SwiftShader's, a software rasteriser: a ratio between LODs, not a
 * phone's frame rate.
 */
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { execSync } from 'node:child_process';
import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MEASURE = path.join(ROOT, 'data/humans/fixture.measure.json');
const MODE = process.argv[2] || '';
if (!['', '--write', '--check'].includes(MODE)) {
  console.error('usage: node tools/human_fixture.mjs [--write|--check]');
  process.exit(2);
}

async function glbs() {
  const out = [];
  for (const dir of ['assets/humans', 'assets/humans/web']) {
    let names = [];
    try { names = await readdir(path.join(ROOT, dir)); } catch { /* none yet */ }
    out.push(...names.filter((n) => n.endsWith('.glb')).sort().map((n) => `${dir}/${n}`));
  }
  return out;
}
const sha256 = async (f) => createHash('sha256').update(await readFile(path.join(ROOT, f))).digest('hex');
const lodOf = (f) => Number(/\.lod([0-3])\.glb$/.exec(f)[1]);
const masterOf = (f) => (f.includes('/web/') ? f.replace('/web/', '/') : null);

const files = await glbs();
if (!files.length) { console.error('no human GLB under assets/humans/'); process.exit(1); }

if (MODE === '--check') {
  const m = JSON.parse(await readFile(MEASURE, 'utf8'));
  const bad = [];
  const byFile = new Map(m.files.map((e) => [e.file, e]));
  for (const f of files) {
    const e = byFile.get(f);
    if (!e) bad.push(`${f}: no entry in data/humans/fixture.measure.json — run node tools/human_fixture.mjs --write`);
    else if (e.sha256 !== await sha256(f)) bad.push(`${f}: its bytes moved since it was measured — re-run node tools/human_fixture.mjs --write`);
    else if (e.verdicts.some((v) => !v.ok)) bad.push(`${f}: a recorded verdict is not ok (${e.verdicts.filter((v) => !v.ok).map((v) => v.check).join(', ')})`);
  }
  for (const e of m.files) if (!files.includes(e.file)) bad.push(`${e.file}: measured, but no longer under assets/humans/`);
  for (const b of bad) console.log(`FAIL ${b}`);
  console.log(`${files.length} human GLB(s) held to their browser measure; ${bad.length ? `${bad.length} finding(s)` : 'OK'}`);
  process.exit(bad.length ? 1 : 0);
}

const contract = JSON.parse(await readFile(path.join(ROOT, 'data/humans/contract.json'), 'utf8'));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.glb': 'model/gltf-binary', '.wasm': 'application/wasm' };
const server = createServer(async (req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT)) { res.writeHead(403).end(); return; }
  try {
    const body = await readFile(p);
    res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404).end(); }
});
await new Promise((ok) => server.listen(0, '127.0.0.1', ok));
const base = `http://127.0.0.1:${server.address().port}/tools/human_fixture.html?files=${files.join(',')}`;

// Playwright is installed globally in CI, and ESM does not honour NODE_PATH, so fall
// back to the global root by absolute path (tools/smoke_renderer.mjs does the same).
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
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const viewports = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const runs = {};
const errors = [];
try {
  for (const [vp, size] of Object.entries(viewports)) {
    const page = await browser.newPage({ viewport: size });
    page.on('pageerror', (e) => errors.push(`${vp}: pageerror ${e.message}`));
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(`${vp}: console.error ${msg.text()}`); });
    await page.goto(base);
    await page.waitForFunction(() => window.__fixture?.ready || window.__failed, null, { timeout: 120000 })
      .catch((e) => errors.push(`${vp}: never ready (${e.message.split('\n')[0]})`));
    runs[vp] = (await page.evaluate(() => window.__fixture?.results)) || [];
    await page.close();
  }
} finally {
  await browser.close();
  server.close();
}

const REQ_SLOTS = contract.materials.required;
const REQ_MORPHS = contract.morphs.required;
const H = contract.frame.rest_height_m;
const entries = [];
let failed = errors.length;
for (const e of errors) console.log(`FAIL ${e}`);
const desk = new Map((runs.desktop || []).map((r) => [r.file, r]));
const mob = new Map((runs.mobile || []).map((r) => [r.file, r]));
for (const f of files) {
  const r = desk.get(f); const m = mob.get(f);
  if (!r || !m) { console.log(`FAIL ${f}: did not load at ${!r ? 'desktop' : 'mobile'}`); failed++; continue; }
  const lod = lodOf(f);
  const v = [];
  const check = (name, ok, got) => v.push({ check: name, ok: !!ok, got });
  check('one skeleton under every primitive', r.skeletons === 1, `${r.skinned_meshes} skinned primitive(s), ${r.skeletons} skeleton(s)`);
  check('the whole contract skeleton', r.contract_bones_missing.length === 0 && r.joints >= contract.skeleton.bones.length,
    r.contract_bones_missing.length ? `missing ${r.contract_bones_missing.join(', ')}` : `${r.joints} joints`);
  check('the required sockets on their bones', r.sockets.length === contract.sockets.required.length, r.sockets.join(', '));
  check('skinning deforms', r.skin_deform_m > 0.1, `${r.skin_deform_m} m at the left hand, upper arm raised 45 deg`);
  for (const c of contract.clips.required_for_actor) {
    const k = r.clips[c];
    check(`clip ${c} plays`, k && k.turns_deg > 0.5 && k.surface_m > 0.001,
      k ? `${k.most} turns ${k.turns_deg} deg; surface moves ${k.surface_m} m` : 'absent');
  }
  check('walk states its ground speed', typeof r.clips.walk?.speed_m_s === 'number', r.clips.walk?.speed_m_s);
  if (contract.morphs.required_lods.includes(lod)) {
    for (const mm of REQ_MORPHS) check(`morph ${mm} moves`, (r.morph_max_mm[mm] || 0) > 1, `${r.morph_max_mm[mm] ?? 'absent'} mm`);
  }
  check('the required material slots load', REQ_SLOTS.every((s) => r.materials.some((n) => n.split('__')[0] === s)), r.materials.join(', '));
  check('the texture decodes', r.textures.length > 0 && r.textures.every((t) => t.w > 0 && t.h > 0),
    r.textures.map((t) => `${t.slot} ${t.w}x${t.h}`).join(', '));
  check('metric rest height', r.rest_height_m >= H.min && r.rest_height_m <= H.max, `${r.rest_height_m} m`);
  check('soles on the ground', Math.abs(r.soles_y_m) <= 0.05, `${r.soles_y_m} m`);
  check('faces +Z, the glTF front', r.facing.startsWith('+Z'), r.facing);
  check('the same at 390x780', m.triangles === r.triangles && m.joints === r.joints && m.draw_calls === r.draw_calls,
    `${m.triangles} tris, ${m.draw_calls} draws`);
  const mf = masterOf(f);
  if (mf) {
    const mr = desk.get(mf);
    const d = mr ? Math.max(Math.abs(mr.rest_height_m - r.rest_height_m), Math.abs(mr.soles_y_m - r.soles_y_m), Math.abs(mr.span_m - r.span_m)) : Infinity;
    check('decoded frame matches its master', mr && d <= 0.002, mr ? `${(d * 1000).toFixed(2)} mm from ${path.basename(mf)}` : 'no master');
    check('same triangles, joints, morphs and clips as its master', mr && mr.triangles === r.triangles && mr.joints === r.joints
      && JSON.stringify(mr.morphs) === JSON.stringify(r.morphs) && JSON.stringify(Object.keys(mr.clips)) === JSON.stringify(Object.keys(r.clips)),
    mr ? `${r.triangles} tris` : 'no master');
  }
  const bad = v.filter((x) => !x.ok);
  failed += bad.length;
  console.log(`${bad.length ? 'FAIL' : 'ok  '} ${f}: ${(r.bytes / 1024).toFixed(1)} KB, ${r.triangles} tris, ${r.draw_calls} draws, `
    + `${r.joints} joints, ${r.morphs.length} morphs, load ${r.load_ms}/${m.load_ms} ms, frame ${r.frame_ms_median}/${m.frame_ms_median} ms`
    + (bad.length ? `\n       ${bad.map((x) => `${x.check}: ${x.got}`).join('\n       ')}` : ''));
  entries.push({
    file: f, sha256: await sha256(f), lod, derivative_of: mf, bytes: r.bytes, meshopt: r.meshopt,
    triangles: r.triangles, vertices: r.vertices, draw_calls: r.draw_calls, materials: r.materials.length,
    textures: r.textures, joints: r.joints, morphs: r.morphs, clips: Object.fromEntries(Object.entries(r.clips)
      .map(([k, c]) => [k, { duration_s: c.duration_s, tracks: c.tracks, speed_m_s: c.speed_m_s }])),
    rest_height_m: r.rest_height_m, soles_y_m: r.soles_y_m,
    load_ms: { desktop: r.load_ms, mobile: m.load_ms }, frame_ms_median: { desktop: r.frame_ms_median, mobile: m.frame_ms_median },
    verdicts: v,
  });
}

// The structural readings must not move without a rebuild; timings may.
const STRUCT = ['sha256', 'bytes', 'triangles', 'vertices', 'draw_calls', 'materials', 'joints'];
if (MODE !== '--write') {
  let committed = null;
  try { committed = JSON.parse(await readFile(MEASURE, 'utf8')); } catch { /* none */ }
  if (!committed) { console.log('FAIL no data/humans/fixture.measure.json — run with --write'); failed++; }
  else {
    const by = new Map(committed.files.map((e) => [e.file, e]));
    for (const e of entries) {
      const c = by.get(e.file);
      const moved = c ? STRUCT.filter((k) => JSON.stringify(c[k]) !== JSON.stringify(e[k])) : ['(no entry)'];
      if (moved.length) { console.log(`FAIL ${e.file}: ${moved.join(', ')} differ from the committed measure — re-run with --write`); failed++; }
    }
  }
}

if (MODE === '--write') {
  if (failed) { console.log(`REFUSING to write the measure: ${failed} finding(s)`); process.exit(1); }
  const tier = (lods) => lods.map((l) => entries.find((e) => e.lod === l && e.meshopt)).filter(Boolean);
  const out = {
    _doc: 'T-1787: the portable-human export path, measured in the browser by tools/human_fixture.mjs on the CI fixture '
      + 'that tools/human_export.sh builds (tools/human_fixture_blend.py -> tools/human_export.py -> gltf-transform meshopt). '
      + 'docs/HUMAN-ASSET-CONTRACT.md § 8 publishes the budgets from it. Frame times are SwiftShader (software) and '
      + 'only compare LODs with each other. tools/human_fixture.mjs --check (in tools/check.sh) holds every sha256 here '
      + 'to the committed GLB, so a rebuild that is not re-measured fails.',
    ticket: 'T-1787',
    measured: new Date().toISOString().slice(0, 10),
    viewports: viewports,
    tiers: Object.fromEntries(Object.entries(contract.lods.tiers).map(([t, lods]) => [t, {
      lods, web_bytes_if_all_fetched: tier(lods).reduce((a, e) => a + e.bytes, 0),
      nearest_lod_triangles: tier(lods)[0]?.triangles ?? null,
    }])),
    files: entries,
  };
  await writeFile(MEASURE, JSON.stringify(out, null, 2) + '\n');
  console.log(`wrote ${path.relative(ROOT, MEASURE)}`);
}
console.log(`${entries.length} human GLB(s) opened at 1280x800 and 390x780; ${failed ? `${failed} finding(s)` : 'OK'}`);
process.exit(failed ? 1 : 0);
