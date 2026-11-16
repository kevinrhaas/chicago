#!/usr/bin/env node
/**
 * test_vessels.mjs — the vessels a visitor watches working and takes the helm of (T-3612).
 *
 * Builds every vessel in data/boats/vessels_1835.json and vessels_1812.json on the committed
 * ground of its scene (the box heightfield, read the way terrain.js reads it), and drives the
 * layer and the helm without a browser:
 *
 *   - every kind builds (topsail schooner, Mackinaw boat, bateau, rowboat, bark canoe), spans
 *     its own length, sets, furls and strips its canvas, and puts the helm above its deck;
 *   - the schooner's main boom stands clear over the helmsman's head;
 *   - the helm's own rule (boat-pilot.js blockedAt) passes every afloat berth and every sample
 *     of the 1835 harbour loop, and stops a schooner at a pier, at the drawbridge and on the
 *     bank, while a rowboat passes under the draw;
 *   - the trim of the canvas follows the wind: booms to leeward, eased running, heel to leeward;
 *   - the layer mounts with no refusal; on a summer day two schooners sail and keep moving; at
 *     night out of sight they are at their resting places; in winter the lake vessels are gone
 *     and the rest laid up, and the helm is refused;
 *   - a dated berth puts the Kinzies' boat at the river mouth on 15 August 1812 (the battle
 *     jaunt's stop) and back below the house on the 14th;
 *   - taking the Hiram's helm and putting way on moves her through her own water; held toward
 *     the north pier she is stopped short of it, and going ashore lands the visitor on ground.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export async function resolve(s, c, n) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return n(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { buildVessel } = await import('../renderers/web/js/vessel-model.js');
const { createVessels, trimFor, localToEnu } = await import('../renderers/web/js/vessels.js');
const { blockedAt, createBoatPilot } = await import('../renderers/web/js/boat-pilot.js');

const ROOT = new URL('../', import.meta.url);
const read = (p) => JSON.parse(fs.readFileSync(new URL(p, ROOT), 'utf8'));
const EPOCH = { 1835: 'e1834_harbor_cut', 1812: 'e1830_natural' };

// --- the ground, as terrain.js samples it: the box, bilinear, the edge carried out ---------
function groundOf(scene) {
  const meta = read(`data/terrain/epochs/${EPOCH[scene]}/heightfield.json`);
  const buf = fs.readFileSync(new URL(`data/terrain/epochs/${EPOCH[scene]}/${meta.bin}`, ROOT));
  const vals = new Int16Array(buf.buffer, buf.byteOffset, meta.rows * meta.cols);
  return (e, n) => {
    let c = (e - meta.origin_e) / meta.cell_m, r = (n - meta.origin_n) / meta.cell_m;
    c = Math.min(Math.max(c, 0), meta.cols - 1.0001); r = Math.min(Math.max(r, 0), meta.rows - 1.0001);
    const c0 = Math.floor(c), r0 = Math.floor(r), fc = c - c0, fr = r - r0, C = meta.cols;
    const v = (rr, cc) => vals[rr * C + cc];
    return ((v(r0, c0) * (1 - fc) + v(r0, c0 + 1) * fc) * (1 - fr)
      + (v(r0 + 1, c0) * (1 - fc) + v(r0 + 1, c0 + 1) * fc) * fr) * meta.scale + meta.offset;
  };
}
// The browser's terrain answers a flat 0 past the box (no apron in the harbour), which is why
// the layer's bed() carries the box's edge out for the helm; the test terrain does the same.
const terrainOf = (scene) => {
  const h = groundOf(scene);
  const meta = read(`data/terrain/epochs/${EPOCH[scene]}/heightfield.json`);
  const inBounds = (e, n) => e >= meta.origin_e && n >= meta.origin_n
    && e <= meta.origin_e + (meta.cols - 1) * meta.cell_m && n <= meta.origin_n + (meta.rows - 1) * meta.cell_m;
  const raw = (e, n) => (inBounds(e, n) ? h(e, n) : 0);
  return { groundHeight: raw, inBounds, surfaceHeight: (e, n) => Math.max(raw(e, n), 0), walkHeight: (e, n) => Math.max(raw(e, n), 0), isWater: (e, n) => raw(e, n) < 0 };
};

let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks += 1; };

// --- 1. every kind builds --------------------------------------------------------------------
const docs = { 1835: read('data/boats/vessels_1835.json'), 1812: read('data/boats/vessels_1812.json') };
const kinds = new Set();
for (const scene of ['1835', '1812']) {
  for (const rec of docs[scene].vessels) {
    if (kinds.has(rec.kind)) continue;
    kinds.add(rec.kind);
    const m = buildVessel(rec);
    let meshes = 0;
    m.group.traverse((o) => { if (o.isMesh) meshes += 1; });
    ok(meshes > 0, `${rec.kind}: built no mesh`);
    const box = new THREE.Box3().setFromObject(m.group);
    // The hull itself, without the bowsprit: the deck's own run.
    ok(m.dims && Math.abs(m.dims.length - rec.hull.length_m) < 0.12 * rec.hull.length_m,
      `${rec.kind}: the hull runs ${m.dims?.length} m, not its ${rec.hull.length_m} m`);
    ok(box.max.x - box.min.x >= rec.hull.length_m * 0.9, `${rec.kind}: drawn shorter than its hull`);
    ok(m.helm.y > m.deckY(m.helm.x) + 0.8, `${rec.kind}: the helm's eye is not above the deck`);
    for (const s of ['set', 'furled', 'bare', 'set']) m.setSails(s, -1, 30, 20);
    if (m.stroke) { m.stroke(0.3, true); m.stroke(0, false); }
    m.setDetail(false); m.setDetail(true);
    if (rec.kind === 'topsail_schooner') {
      // The main boom over the helmsman: its lowest point aft of the mainmast stands clear
      // of a head 1.8 m above the deck at the helm.
      const rig = m.group.getObjectByName('main-rig');
      ok(rig, 'the schooner has no main rig');
      m.setSails('furled');
      m.group.updateMatrixWorld(true);
      let low = Infinity;
      rig.traverse((o) => {
        if (!o.isMesh || !o.parent.visible) return;
        const p = o.geometry.getAttribute('position'), v = new THREE.Vector3();
        for (let i = 0; i < p.count; i++) {
          v.fromBufferAttribute(p, i).applyMatrix4(o.matrixWorld);
          if (Math.abs(v.x - m.helm.x) < 1.5 && Math.abs(v.z) < 1) low = Math.min(low, v.y);
        }
      });
      if (process.env.VESSEL_DEBUG) console.log("boom over the helm", low - m.deckY(m.helm.x));
      ok(low !== Infinity && low > m.deckY(m.helm.x) + 1.8, `the main boom hangs ${(low - m.deckY(m.helm.x)).toFixed(2)} m over the deck at the helm`);
    }
    m.dispose?.();
  }
}
for (const k of ['topsail_schooner', 'mackinaw_boat', 'bateau', 'rowboat', 'bark_canoe']) ok(kinds.has(k), `no ${k} in the records`);

// --- 2. the helm's rule against the record --------------------------------------------------
const nav35 = docs[1835].navigation, g35 = groundOf('1835');
const craftRec = (rec) => ({ id: rec.id, kind: rec.kind, masted: nav35.kinds[rec.kind]?.masted, length: rec.hull.length_m, beam: rec.hull.beam_m, draft: rec.hull.draft_m });
for (const scene of ['1835', '1812']) {
  const doc = docs[scene], g = groundOf(scene);
  for (const rec of doc.vessels) {
    if (rec.mode === 'beached' || rec.mode === 'circuit') continue;
    for (const b of [rec.berth, rec.winter_berth, ...(rec.dated ?? []).map((d) => d.berth)].filter(Boolean)) {
      const why = blockedAt(doc.navigation, { ...craftRec(rec), masted: doc.navigation.kinds[rec.kind]?.masted }, b.e, b.n, b.bearing, { ground: g });
      ok(why === null, `${rec.id} at (${b.e}, ${b.n}): ${why}`);
    }
  }
}
const schooner = craftRec(docs[1835].vessels.find((v) => v.id === 'vessel_schr_hiram'));
const loop = docs[1835].routes.harbour_loop;
let loopBad = null;
for (const [e, n, b] of loop.points) {
  const why = blockedAt(nav35, schooner, e, n, b, { ground: g35 });
  if (why) { loopBad = `(${e}, ${n}) ${why}`; break; }
}
ok(loopBad === null, `the harbour loop is blocked for a schooner at ${loopBad}`);
const centroid = (pts) => pts.reduce((a, p) => [a[0] + p[0] / pts.length, a[1] + p[1] / pts.length], [0, 0]);
const obstacle = (id) => nav35.obstacles.find((o) => o.id === id);
ok(obstacle('north_pier') && obstacle('dearborn_street_drawbridge'), 'the piers and the draw are not in the navigation rules');
{
  const [pe, pn] = centroid(obstacle('north_pier').pts);
  ok(blockedAt(nav35, schooner, pe, pn, 90, { ground: g35, depth: false }) === 'the pier', 'a schooner is not stopped by the north pier');
  const [de, dn] = centroid(obstacle('dearborn_street_drawbridge').pts);
  ok(blockedAt(nav35, schooner, de, dn, 90, { ground: g35, depth: false }) === 'the draw is down', 'a schooner passes the drawbridge with the draw down');
  const row = { id: 'r', kind: 'rowboat', masted: false, length: 5, beam: 1.5, draft: 0.25 };
  ok(blockedAt(nav35, row, de, dn, 90, { ground: g35, depth: false }) === null, 'a rowboat cannot pass under the draw');
  ok(/aground|shallow/.test(String(blockedAt(nav35, schooner, 765, -40, 90, { ground: g35 }))), 'a schooner sails over the south bank');
}

// --- 3. the trim follows the wind ------------------------------------------------------------
{
  const wind = docs[1835].wind.from_bearing;
  const reach = trimFor((wind + 90) % 360, wind), other = trimFor((wind + 270) % 360, wind), run = trimFor((wind + 180) % 360, wind), close = trimFor((wind + 50) % 360, wind);
  ok(reach.side === -other.side, 'the booms do not change sides on the other tack');
  ok(Math.sign(reach.heel) === reach.side, 'she heels to windward');
  ok(run.boom > reach.boom && reach.boom > close.boom, 'the sheets are not eased as the wind comes aft');
}

// --- 4. the layer: day, night, winter --------------------------------------------------------
function fetchFor(scene) {
  return async (url) => {
    const u = String(url);
    if (u.endsWith(`boats/vessels_${scene}.json`)) return { ok: true, status: 200, json: async () => docs[scene] };
    return { ok: false, status: 404, json: async () => ({}) };
  };
}
const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 3000);
const camAt = (e, n, yawDeg = 0) => { camera.position.set(e, 2, -n); camera.rotation.set(0, -yawDeg * Math.PI / 180, 0, 'YXZ'); camera.updateMatrixWorld(true); camera.matrixWorldInverse.copy(camera.matrixWorld).invert(); };
let hour = 9, season = 'summer', date = '1835-07-01';
let pilotRef = null;
globalThis.fetch = fetchFor('1835');
const problems = [];
const t35 = terrainOf('1835');
const v35 = await createVessels({ dataBase: 'http://x/data/', sceneId: '1835', terrain: t35, problems, hour: () => hour, season: () => season, date: () => date, pilot: () => pilotRef });
ok(problems.length === 0, `problems: ${problems.join('; ')}`);
ok(v35.census.vessels === docs[1835].vessels.length && v35.census.refused === 0, `census ${JSON.stringify(v35.census)}`);
ok(v35.things.length === v35.census.vessels, 'not every vessel can be taken');
for (const [e, n] of [[1790, 360], [1895, 271], [2600, -400], [765, 58]]) {
  ok(Math.abs(v35.bed(e, n) - g35(e, n)) < 0.01, `the helm reads the bed at (${e}, ${n}) as ${v35.bed(e, n)}, the berths were laid on ${g35(e, n)}`);
}
camAt(765, 15, 353);
v35.update(0.1, camera);
// The layer looks round twice a second (its dt is held to a quarter second a frame).
const tick = (layer) => { for (let i = 0; i < 3; i++) layer.update(0.25, camera); };
const sailors = () => v35.vessels.filter((v) => v.state === 'sailing');
ok(sailors().length === 2, `${sailors().length} sailing on a summer morning`);
const at0 = sailors().map((v) => [v.pose.e, v.pose.n]);
for (let i = 0; i < 300; i++) v35.update(0.1, camera);
ok(sailors().every((v, i) => Math.hypot(v.pose.e - at0[i][0], v.pose.n - at0[i][1]) > 10), 'the sailing schooners stand still');
for (const v of sailors()) ok(blockedAt(nav35, schooner, v.pose.e, v.pose.n, v.pose.bearing, { ground: g35 }) === null, `${v.id} sails out of her water`);
hour = 23;
camAt(-500, -2000, 180);
tick(v35);
const rested = v35.vessels.filter((v) => v.rec.mode === 'circuit');
ok(rested.every((v) => v.state === 'resting'), `at night: ${rested.map((v) => v.state).join(', ')}`);
ok(v35.census.sailing === 0 || sailors().length === 0, 'still sailing in the dark');
hour = 9; season = 'winter';
tick(v35);
const absent = v35.vessels.filter((v) => v.rec.winter === 'absent');
ok(absent.length >= 3 && absent.every((v) => !v.model.group.visible && v.state === 'absent'), 'a lake vessel winters in the river');
ok(v35.vessels.filter((v) => v.rec.winter === 'laid_up').every((v) => v.state === 'laid_up'), 'a vessel is not laid up in winter');
{
  const thing = v35.things.find((t) => t.id === 'vessel:vessel_schr_hiram');
  const refuse = thing.actions[thing.state][0].refuse?.();
  ok(/frozen|Laid up/.test(String(refuse)), `taking a laid-up schooner in winter: ${refuse}`);
}
season = 'summer';
tick(v35);
ok(v35.vessels.find((v) => v.id === 'vessel_schr_philips').state === 'moored', 'the Philips does not come back in summer');

// --- 5. the 1812 boats on the battle jaunt's days ----------------------------------------------
globalThis.fetch = fetchFor('1812');
date = '1812-08-14';
const v12 = await createVessels({ dataBase: 'http://x/data/', sceneId: '1812', terrain: terrainOf('1812'), problems, hour: () => hour, season: () => season, date: () => date });
ok(problems.length === 0 && v12.census.vessels === 2, `1812: ${problems.join('; ')} ${JSON.stringify(v12.census)}`);
const kinzie = v12.vessels.find((v) => v.id === 'vessel_kinzie_boat_1812');
tick(v12);
const home = [kinzie.pose.e, kinzie.pose.n];
date = '1812-08-15';
tick(v12);
ok(kinzie.pose.n < -300, `on 15 August the Kinzies' boat is not at the river mouth (${kinzie.pose.e}, ${kinzie.pose.n})`);
date = '1812-08-14';
tick(v12);
ok(kinzie.pose.e === home[0] && kinzie.pose.n === home[1], 'the Kinzies\' boat is not back below the house');

// --- 6. the helm --------------------------------------------------------------------------------
const said = [];
const standable = (e, n) => g35(e, n) > 0.15;
const pilot = createBoatPilot({ nav: () => v35.nav, ground: v35.bed, hulls: () => v35.hulls(), standable, say: (t) => said.push(t) });
pilotRef = pilot;
{
  const hiram = v35.vessels.find((v) => v.id === 'vessel_schr_hiram');
  const craft = v35.craftOf('vessel_schr_hiram');
  ok(pilot.take(craft) && pilot.active && hiram.state === 'piloted', 'the Hiram\'s helm does not take');
  ok(pilot.take(v35.craftOf('vessel_schr_whig')) === false, 'two helms at once');
  const p0 = { ...craft.pose };
  pilot.drive({ forward: 1, strafe: 0 });
  for (let i = 0; i < 150; i++) { pilot.update(0.1); v35.update(0.1, camera); }
  const p1 = { ...craft.pose };
  ok(Math.hypot(p1.e - p0.e, p1.n - p0.n) > 5, `the Hiram moved ${Math.hypot(p1.e - p0.e, p1.n - p0.n).toFixed(1)} m under way`);
  ok(blockedAt(v35.nav, craft, p1.e, p1.n, p1.bearing, { ground: g35 }) === null, 'the Hiram left her water');
  // Run her on toward the lake; whatever stops her, she is never inside a pier or ashore.
  for (let i = 0; i < 1500 && !pilot.blocked; i++) { pilot.update(0.1); v35.update(0.1, camera); }
  const p2 = craft.pose;
  ok(blockedAt(v35.nav, craft, p2.e, p2.n, p2.bearing, { ground: g35 }) === null, `the Hiram ran into something (${p2.e.toFixed(0)}, ${p2.n.toFixed(0)})`);
  const words = pilot.leave();
  ok(!pilot.active && /Ashore|rows you ashore/.test(String(words)), `going ashore said ${words}`);
  ok(hiram.state === 'left', `the Hiram is ${hiram.state} after you go ashore`);
  const land = localToEnu(hiram.pose, 0, 0);
  ok(Number.isFinite(land.e), 'no pose after going ashore');
}

// Out in the lake, past the measured box: the Jesse Smith, at her resting place in the offing,
// takes way and sails on with the lake's own depth under her, not aground on the box's edge.
{
  hour = 23; tick(v35);
  const js = v35.vessels.find((v) => v.id === 'vessel_schr_jesse_smith');
  ok(js.state === 'resting' && js.pose.e > 1700, `the Jesse Smith rests at (${js.pose.e}, ${js.pose.n}), ${js.state}`);
  const craft = v35.craftOf(js.id);
  ok(pilot.take(craft), 'the Jesse Smith\'s helm does not take');
  const p0 = { ...craft.pose };
  pilot.drive({ forward: 1, strafe: 0 });
  for (let i = 0; i < 200; i++) { pilot.update(0.1); v35.update(0.1, camera); }
  ok(!pilot.blocked && Math.hypot(craft.pose.e - p0.e, craft.pose.n - p0.n) > 8, `in the lake she ${pilot.blocked ? `is held: ${pilot.blocked}` : 'did not move'}`);
  ok(pilot.leave() === 'A boat rows you ashore' || said.at(-1) === 'A boat rows you ashore', `from the offing: ${said.at(-1)}`);
}

console.log(`test_vessels: ${checks} checks passed (${kinds.size} kinds, ${v35.census.vessels} vessels in 1835, ${v12.census.vessels} in 1812)`);
