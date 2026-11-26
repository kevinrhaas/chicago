#!/usr/bin/env node
// T-3553: sweep every person for torn cloth. A QA tool, not a gate step (it renders).
//
// Each body is walked on tools/human_walk_strip.html at every level of detail and drawn from
// five sides, whole and from the chest up, standing and mid-stride. Each frame is drawn twice:
// shaded, as the town draws it, and flat, one colour per mesh with no light and no smoothing of
// edges. The flat frame says which piece of cloth each pixel shows, and three things are read
// from it:
//   speck  a small island of one piece inside another (a waistcoat corner through a coat, the
//          body through a sleeve, two layers fighting over one place): patches of the wrong cloth;
//   fray   a piece's outline that saws back and forth across another's, pixel by pixel: the
//          "ragged edges" (counted as one-pixel teeth along the meeting line);
//   hole   a small see-through gap inside the figure: the "holes";
//   jag    a piece's own outline sawing in and out, teeth and notches narrower than a few
//          pixels along a collar, a hem or a lapel: the "ragged collars".
// Findings are summed per body, level and pair of pieces, and the shaded frames with findings
// are saved with each one ringed (red speck, yellow fray, cyan hole, magenta jag).
//
//   node tools/qa_cloth_sweep.mjs [--assets a,b] [--lods 0,1,2,3] [--out DIR] [--port 8810]
//        [--jobs 3] [--before]       (--before: draw with the load-time cloth passes off)
// Needs the 4d folder served at http://127.0.0.1:<port>/ (python3 -m http.server <port>).
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i < 0 ? d : process.argv[i + 1]; };
const HERE = path.dirname(new URL(import.meta.url).pathname);
const ALL = (await fs.readdir(path.join(HERE, '../assets/humans'))).filter((f) => f.endsWith('.lod0.glb')).map((f) => f.slice(0, -9)).filter((a) => a !== 'c4d_fixture').sort();
const assets = arg('assets', '') ? arg('assets').split(',') : ALL;
const lods = arg('lods', '0,1,2,3').split(',').map(Number);
const out = arg('out', '/tmp/cloth-sweep');
const port = arg('port', '8810');
const jobs = Number(arg('jobs', 1));
const before = process.argv.includes('--before');
const SIZE = 640;
await fs.mkdir(out, { recursive: true });

// Runs in the page: draw the flat frames and read them.
async function sweep({ SIZE, frames }) {
  const s = window.__strip, THREE = s.THREE, R = s.renderer, scene = s.scene, cam = s.camera;
  const root = s.actor.root;
  const meshes = []; root.traverse((o) => { if (o.isMesh && o.visible) meshes.push(o); });
  // 7 levels a channel, never black: up to 342 pieces, read back exactly from a byte target.
  const L = 7, code = (i) => { const n = i + 1; return [n % L, Math.floor(n / L) % L, Math.floor(n / L / L) % L]; };
  const flat = meshes.map((m, i) => {
    const o = m.material, [r, g, b] = code(i);
    const mat = new THREE.MeshBasicMaterial({ side: o.side, toneMapped: false, alphaTest: o.alphaTest || (o.transparent ? 0.5 : 0), map: o.alphaTest || o.transparent ? o.map : null, transparent: false });
    mat.color.setRGB(r / (L - 1), g / (L - 1), b / (L - 1), THREE.LinearSRGBColorSpace);
    return mat;
  });
  const shaded = meshes.map((m) => m.material);
  const rt = new THREE.WebGLRenderTarget(SIZE, SIZE, { samples: 0, colorSpace: THREE.LinearSRGBColorSpace });
  const px = new Uint8Array(SIZE * SIZE * 4);
  const others = []; scene.traverse((o) => { if (o !== scene && o.visible && !o.isLight && !o.isCamera && !isIn(o) && !holds(o)) others.push(o); });
  function holds(o) { for (let p = root.parent; p; p = p.parent) if (p === o) return true; return false; }
  function isIn(o) { for (let p = o; p; p = p.parent) if (p === root) return true; return false; }
  const results = [];
  let clock = 0;
  for (const f of frames) {
    if (f.t > clock) { s.step(f.t - clock, { render: false }); clock = f.t; }
    s.setView(f.view);
    cam.zoom = f.zoom; cam.updateProjectionMatrix();
    cam.position.y += f.aimy - 0.93; cam.updateMatrixWorld(true);
    // flat
    const bg = scene.background; scene.background = null;
    for (const o of others) o.visible = false;
    meshes.forEach((m, i) => { m.material = flat[i]; });
    R.setRenderTarget(rt); R.setClearColor(0x000000, 1); R.clear(); R.render(scene, cam);
    R.readRenderTargetPixels(rt, 0, 0, SIZE, SIZE, px); R.setRenderTarget(null);
    meshes.forEach((m, i) => { m.material = shaded[i]; });
    for (const o of others) o.visible = true;
    scene.background = bg;
    // ids, flipped to image rows (top first)
    const id = new Int16Array(SIZE * SIZE).fill(-1);
    const step = 255 / (L - 1);
    for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) {
      const k = ((SIZE - 1 - y) * SIZE + x) * 4;
      const r = Math.round(px[k] / step), g = Math.round(px[k + 1] / step), b = Math.round(px[k + 2] / step);
      const n = r + g * L + b * L * L; if (n > 0 && n <= meshes.length) id[y * SIZE + x] = n - 1;
    }
    // components (4-connected)
    const comp = new Int32Array(SIZE * SIZE).fill(-1), comps = [];
    const stack = new Int32Array(SIZE * SIZE);
    for (let p0 = 0; p0 < id.length; p0++) {
      if (comp[p0] >= 0) continue;
      const v = id[p0], c = comps.length; let sp = 0, area = 0, sx = 0, sy = 0, border = false;
      const around = new Map();
      stack[sp++] = p0; comp[p0] = c;
      while (sp) {
        const p = stack[--sp], x = p % SIZE, y = (p / SIZE) | 0; area++; sx += x; sy += y;
        if (x === 0 || y === 0 || x === SIZE - 1 || y === SIZE - 1) border = true;
        for (const q of [x > 0 ? p - 1 : -1, x < SIZE - 1 ? p + 1 : -1, y > 0 ? p - SIZE : -1, y < SIZE - 1 ? p + SIZE : -1]) {
          if (q < 0) continue;
          if (id[q] === v) { if (comp[q] < 0) { comp[q] = c; stack[sp++] = q; } } else around.set(id[q], (around.get(id[q]) ?? 0) + 1);
        }
      }
      comps.push({ v, area, x: sx / area, y: sy / area, border, around });
    }
    const scale = (SIZE / 640) ** 2 * f.zoom * f.zoom;   // px per cm² grows with zoom
    const SPECK = Math.max(6, 0.9 * scale), HOLE = Math.max(6, 1.2 * scale);
    // Hair cards, eyes and the mouth are cut-outs and small parts by design: not cloth.
    const NOT = /hair|eye|brow|lash|teeth|tongue|beard|moustache|mustache|spectacle|lens|glasses/i;
    const skip = (i) => i >= 0 && NOT.test(meshes[i].name);
    const finds = [];
    for (const c of comps) {
      if (c.border) continue;
      if (c.v < 0) {
        if ([...c.around.keys()].some(skip)) continue;
        // a small see-through gap with figure all round it
        // (a gap with only skin about it is a mouth, an ear or between the fingers)
        if (c.area <= HOLE && !c.around.has(-1) && [...c.around.keys()].some((i) => shaded[i]?.name !== 'skin')) finds.push({ kind: 'hole', a: [...c.around.keys()].map((i) => meshes[i]?.name).join('+'), px: c.area, x: c.x, y: c.y });
        continue;
      }
      if (c.area > SPECK || c.around.has(-1) || skip(c.v)) continue;
      let host = -1, most = 0; for (const [k, n] of c.around) if (n > most) { most = n; host = k; }
      if (skip(host)) continue;
      finds.push({ kind: 'speck', a: meshes[c.v].name, b: meshes[host]?.name ?? '?', px: c.area, x: c.x, y: c.y });
    }
    // fray: one-pixel teeth along a meeting of two pieces (a pixel of A with B on both sides
    // across one axis, A on both sides along the other, i.e. a single-pixel spur)
    const fray = new Map();
    for (let y = 1; y < SIZE - 1; y++) for (let x = 1; x < SIZE - 1; x++) {
      const p = y * SIZE + x, v = id[p]; if (v < 0) continue;
      const l = id[p - 1], r = id[p + 1], u = id[p - SIZE], d = id[p + SIZE];
      let b = -2;
      if (l === r && l !== v && l >= 0 && (u === v || d === v)) b = l;
      else if (u === d && u !== v && u >= 0 && (l === v || r === v)) b = u;
      if (b < 0) continue;
      const key = `${v}|${b}`; const e = fray.get(key) ?? { n: 0, x: 0, y: 0 }; e.n++; e.x += x; e.y += y; fray.set(key, e);
    }
    for (const [key, e] of fray) {
      const [a, b] = key.split('|').map(Number);
      if (e.n < 4 || skip(a) || skip(b)) continue;
      finds.push({ kind: 'fray', a: meshes[a].name, b: meshes[b].name, px: e.n, x: e.x / e.n, y: e.y / e.n });
    }
    // jag: a piece's own outline sawing in and out (a jagged collar, a torn hem). The piece's
    // mask is opened and closed with a square r px across; a straight or gently curved edge
    // comes back unchanged, a tooth or notch narrower than r does not. Teeth are counted where
    // they hang off the piece (not a whole loose speck) and are short (not a thin strap).
    const r = f.zoom > 1.5 ? 4 : 2, area = new Int32Array(meshes.length);
    for (const v of id) if (v >= 0) area[v]++;
    const mk = new Uint8Array(SIZE * SIZE), t1 = new Uint8Array(SIZE * SIZE), t2 = new Uint8Array(SIZE * SIZE);
    let X0 = 0, X1 = SIZE - 1, Y0 = 0, Y1 = SIZE - 1;   // the piece's box, padded
    const morph = (src, dst, tmp, grow) => {   // separable square min/max filter
      for (let y = Y0; y <= Y1; y++) for (let x = X0; x <= X1; x++) {
        let v = grow ? 0 : 1; for (let k = -r; k <= r; k++) { const xx = x + k; const s = xx < 0 || xx >= SIZE ? (grow ? 0 : 1) : src[y * SIZE + xx]; v = grow ? (v | s) : (v & s); }
        tmp[y * SIZE + x] = v;
      }
      for (let y = Y0; y <= Y1; y++) for (let x = X0; x <= X1; x++) {
        let v = grow ? 0 : 1; for (let k = -r; k <= r; k++) { const yy = y + k; const s = yy < 0 || yy >= SIZE ? (grow ? 0 : 1) : tmp[yy * SIZE + x]; v = grow ? (v | s) : (v & s); }
        dst[y * SIZE + x] = v;
      }
    };
    const t3 = new Uint8Array(SIZE * SIZE), seen = new Uint8Array(SIZE * SIZE);
    for (let k = 0; k < meshes.length; k++) {
      if (skip(k) || shaded[k]?.name === 'skin' || area[k] < 400) continue;
      let bx0 = SIZE, bx1 = -1, by0 = SIZE, by1 = -1;
      for (let p = 0; p < mk.length; p++) { const on = id[p] === k ? 1 : 0; mk[p] = on; t2[p] = on; if (on) { const x = p % SIZE, y = (p / SIZE) | 0; if (x < bx0) bx0 = x; if (x > bx1) bx1 = x; if (y < by0) by0 = y; if (y > by1) by1 = y; } }
      X0 = Math.max(0, bx0 - 3 * r); X1 = Math.min(SIZE - 1, bx1 + 3 * r); Y0 = Math.max(0, by0 - 3 * r); Y1 = Math.min(SIZE - 1, by1 + 3 * r);
      t1.fill(0); t3.fill(0);
      morph(mk, t1, t3, false); morph(t1, t2, t3, true);   // open
      morph(t2, t1, t3, true); morph(t1, t2, t3, false);   // close → t2 smooth
      seen.fill(0);
      for (let y = Y0; y <= Y1; y++) for (let x = X0; x <= X1; x++) {
        const p0 = y * SIZE + x;
        if (seen[p0] || mk[p0] === t2[p0]) continue;
        let sp = 0, n = 0, sx = 0, sy = 0, x0 = SIZE, x1 = 0, y0 = SIZE, y1 = 0, attached = false; const other = new Map();
        stack[sp++] = p0; seen[p0] = 1;
        while (sp) {
          const p = stack[--sp], x = p % SIZE, y = (p / SIZE) | 0; n++; sx += x; sy += y;
          if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
          if (!mk[p]) other.set(id[p], (other.get(id[p]) ?? 0) + 1);
          for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
            const xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= SIZE || yy >= SIZE) continue;
            const q = yy * SIZE + xx;
            if (mk[q] !== t2[q]) { if (!seen[q]) { seen[q] = 1; stack[sp++] = q; } } else if (mk[q] && t2[q]) attached = true;
          }
        }
        if (!attached || n < 1.5 * r * r || Math.max(x1 - x0, y1 - y0) > 6 * r) continue;
        let b = -1, most = 0; for (const [kk, c] of other) if (c > most) { most = c; b = kk; }
        if (skip(b)) continue;
        finds.push({ kind: 'jag', a: meshes[k].name, b: b >= 0 ? meshes[b].name : 'background', px: n, x: sx / n, y: sy / n });
      }
    }
    let image = null;
    if (finds.length) {
      s.render(); cam.zoom = f.zoom; cam.updateProjectionMatrix(); cam.position.y += f.aimy - 0.93; cam.updateMatrixWorld(true);
      R.render(scene, cam);
      const c2 = document.createElement('canvas'); c2.width = c2.height = SIZE;
      const g = c2.getContext('2d'); g.drawImage(R.domElement, 0, 0, R.domElement.width, R.domElement.height, 0, 0, SIZE, SIZE);
      g.lineWidth = 2;
      for (const d of finds) { g.strokeStyle = d.kind === 'speck' ? '#ff2020' : d.kind === 'fray' ? '#ffd000' : d.kind === 'jag' ? '#ff40ff' : '#00e0ff'; g.beginPath(); g.arc(d.x, d.y, d.kind === 'fray' ? 10 : 6, 0, 7); g.stroke(); }
      g.fillStyle = '#000a'; g.fillRect(0, 0, SIZE, 18); g.fillStyle = '#fff'; g.font = '12px sans-serif';
      g.fillText(`${f.view} ${f.zoom > 1.5 ? 'chest' : 'whole'} t${f.t}`, 6, 13);
      image = c2.toDataURL('image/jpeg', 0.85);
    }
    let cover = 0; for (const v of id) if (v >= 0) cover++;
    results.push({ ...f, cover, finds, image });
  }
  rt.dispose(); flat.forEach((m) => m.dispose());
  return { meshes: meshes.map((m) => m.name), results };
}

const VIEWS = ['front', 'three-quarter', 'side', 'rear-three-quarter', 'rear'];
const frames = [];
for (const t of [0.05, 0.45]) for (const view of VIEWS) for (const [zoom, aimy] of [[1, 0.93], [2.4, 1.32]]) frames.push({ t, view, zoom, aimy });

const launch = () => chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const todo = []; for (const a of assets) for (const l of lods) todo.push([a, l]);
const summary = {};
async function one([asset, lod], browser) {
  const page = await browser.newPage({ viewport: { width: SIZE, height: SIZE } });
  const errors = []; page.on('pageerror', (e) => errors.push(e.message));
  if (before) await page.addInitScript('globalThis.CHICAGO_NO_DRAPE = true');
  try {
    await page.goto(`http://127.0.0.1:${port}/tools/human_walk_strip.html?asset=${asset}&lod=${lod}&view=side&w=${SIZE}&h=${SIZE}&prints=0&manual=1`);
    await page.evaluate(() => window.__strip.ready, { timeout: 180000 });
    const r = await page.evaluate(sweep, { SIZE, frames });
    const key = `${asset}.lod${lod}`;
    const pairs = {};
    let n = 0;
    for (const [i, f] of r.results.entries()) {
      for (const d of f.finds) { const k = `${d.kind} ${d.a} / ${d.b ?? ''}`; pairs[k] = (pairs[k] ?? 0) + 1; n++; }
      if (f.image) await fs.writeFile(path.join(out, `${key}.${String(i).padStart(2, '0')}.jpg`), Buffer.from(f.image.split(',')[1], 'base64'));
      delete f.image;
    }
    summary[key] = { finds: n, cover: r.results.map((f) => f.cover), meshes: r.meshes, pairs, errors, frames: r.results.map((f) => ({ view: f.view, zoom: f.zoom, t: f.t, finds: f.finds })) };
    console.log(`${key.padEnd(48)} ${String(n).padStart(4)}  ${Object.entries(pairs).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => `${k} ×${v}`).join(' · ')}${errors.length ? `  ERR ${errors[0]}` : ''}`);
  } catch (e) {
    summary[`${asset}.lod${lod}`] = { error: String(e.message ?? e) };
    console.log(`${asset}.lod${lod} FAILED ${e.message}`);
  } finally { await page.close(); }
  await fs.writeFile(path.join(out, 'summary.json'), JSON.stringify(summary, null, 1));   // as it goes
}
const queue = todo.slice();
await Promise.all(Array.from({ length: jobs }, async () => { const b = await launch(); while (queue.length) await one(queue.shift(), b); await b.close(); }));
await fs.writeFile(path.join(out, 'summary.json'), JSON.stringify(summary, null, 1));
const total = Object.values(summary).reduce((s, v) => s + (v.finds ?? 0), 0);
console.log(`\n${Object.keys(summary).length} bodies × levels, ${total} findings → ${out}/summary.json`);
