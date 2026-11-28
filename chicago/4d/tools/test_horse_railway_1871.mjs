#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/** T-3806: the 1871 horse railways (renderers/web/js/horse-railway-1871.js and
 * data/transport/horse_railways_1871.json, written by tools/lay_horse_railways_1871.py).
 *
 * Holds: the file is what its tool writes; every source a section cites resolves; the four car
 * lines are the double-track ones and their runs are closed with a crossover at each stub; the
 * timetable keeps each line's cars a headway apart and stops them at the stubs; no car runs out of
 * hours, nor on the fire night from ten o'clock, nor on the Monday; the track draws as decals in
 * few cells; the car is the declared size; and a mounted railway builds nothing far from the eye. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { registerHooks } from 'node:module';

const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here).href;
registerHooks({ resolve: (s, c, next) => s === 'three' ? { url: vendor + 'three.module.js', shortCircuit: true }
  : s.startsWith('three/addons/') ? { url: vendor + 'addons/' + s.slice(13), shortCircuit: true } : next(s, c) });
const THREE = await import(vendor + 'three.module.js');
const R = await import(new URL('renderers/web/js/horse-railway-1871.js', here).href);

// the laid data is current: check.sh's step before this one runs lay_horse_railways_1871.py in its checking mode
const doc = JSON.parse(fs.readFileSync(new URL('data/transport/horse_railways_1871.json', here), 'utf8'));

// sources resolve
for (const s of doc.sections) for (const src of s.sources) assert.ok(fs.existsSync(new URL(`data/sources/${src.id}.json`, here)), `${s.id}: ${src.id}`);
for (const src of doc.hours.fire_sources) assert.ok(fs.existsSync(new URL(`data/sources/${src.id}.json`, here)), src.id);
const liberties = fs.readFileSync(new URL('docs/LIBERTIES.md', here), 'utf8');
assert.ok(liberties.includes(doc.liberty), `${doc.liberty} is in docs/LIBERTIES.md`);

// the car lines are the double ones
const ids = doc.services.map(s => s.id).sort();
assert.deepEqual(ids, ['clark_street', 'madison_street', 'randolph_street', 'state_street']);
for (const sv of doc.services) {
  const sec = doc.sections.find(s => s.id === sv.section);
  assert.equal(sec.track, 'double', sv.id);
  const p = R.pathOf(sv.loop, true);
  assert.ok(Math.abs(p.length - sv.length_m) < 1, `${sv.id} loop length`);
  // the stubs: the run turns back on itself at 0 and at the cusp
  const a = p.at(.5), b = p.at(p.length - .5);
  assert.ok(a.de * b.de + a.dn * b.dn < -.9, `${sv.id}: the run reverses at its first stub`);
  const c = p.at(sv.cusp_m[1] - .5), d = p.at(sv.cusp_m[1] + .5);
  assert.ok(c.de * d.de + c.dn * d.dn < -.9, `${sv.id}: the run reverses at its far stub`);
  // out and back are on two tracks, the right-hand one each way
  const mid = p.at(sv.cusp_m[1] / 2), back = p.at(sv.cusp_m[1] + (p.length - sv.cusp_m[1]) / 2);
  const off = Math.hypot(mid.e - back.e, mid.n - back.n);
  assert.ok(off < 400, `${sv.id}: halfway out and halfway back are near (${off.toFixed(0)} m)`);
}
// State Street runs Lake Street to Twenty-second; North Clark crosses the river
const st = doc.services.find(s => s.id === 'state_street');
const ns = st.loop.map(p => p[1]);
assert.ok(Math.max(...ns) > -130 && Math.min(...ns) < -3740, 'State Street from Lake to Twenty-second');
assert.ok(doc.services.find(s => s.id === 'clark_street').loop.some(p => p[1] > 1800), 'Clark Street to Division');
assert.ok(!doc.sections.some(s => /wells/i.test(s.id)), 'no Wells Street line in 1871 (built 1875)');

// timetable
const car = doc.car;
for (const sv of doc.services) {
  const path = R.pathOf(sv.loop, true);
  const tt = R.createTimetable({ ...sv, length_m: path.length }, car);
  const t = 1234.5;
  const places = Array.from({ length: tt.count }, (_, k) => tt.place(t + k * sv.headway_s));
  const moving = places.filter(p => !p.dwell);
  assert.ok(moving.length >= 1, sv.id);
  // two cars running the same way are at least nearly a headway's run apart
  const outs = moving.filter(p => p.leg === 'out').map(p => p.s).sort((x, y) => x - y);
  for (let i = 1; i < outs.length; i++) assert.ok(outs[i] - outs[i - 1] > 40, `${sv.id}: cars bunched (${(outs[i] - outs[i - 1]).toFixed(1)} m)`);
  for (const p of places) assert.ok(p.speed <= car.speed_m_s + 1e-6 && p.s >= 0 && p.s <= path.length + 1e-6);
}
assert.equal(R.runDistance(0, 100, 2), 0);
assert.ok(Math.abs(R.runDistance(R.runTime(100, 2), 100, 2) - 100) < 1e-6);

// hours and the fire
const H = doc.hours;
// the horses' gait clips bind as loadGaitClip checks them (a walk bound to the wrong cycle left every car without horses)
{
  const spec = JSON.parse(fs.readFileSync('data/transport/driven/loops.json', 'utf8')).horse_models.current26_walk_v2;
  for (const g of ['walk', 'trot']) {
    const b = R.gaitBinding(spec, g);
    assert.ok(b, `the ${g} clip is bound`);
    const clip = JSON.parse(fs.readFileSync(`renderers/web/${b.file}`, 'utf8'));
    assert.equal(clip.name, b.name, `${g}: clip name`);
    assert.equal(clip.model_sha256, b.modelSha256, `${g}: model`);
    assert.equal(clip.cycle_m, b.cycle_m, `${g}: cycle (the gait refuses a clip whose cycle differs)`);
  }
}
assert.ok(R.inService(H, 15.66, '1871-10-08'), 'Sunday afternoon');
assert.ok(R.inService(H, 21, '1871-10-08'), 'Sunday at nine');
assert.ok(!R.inService(H, 22.5, '1871-10-08'), 'the fire night from ten');
assert.ok(!R.inService(H, 1.5, '1871-10-09') && !R.inService(H, 8, '1871-10-09'), 'the Monday');
assert.ok(!R.inService(H, 3, '1871-10-07') && R.inService(H, 12, '1871-10-07'), 'hours of service');

// track
const cells = R.trackGeometries(doc, () => 3.23);
const tris = cells.reduce((a, c) => a + c.triangles, 0);
assert.ok(cells.length > 40 && cells.length < 400, `cells ${cells.length}`);
assert.ok(tris < 120000, `track triangles ${tris}`);
for (const c of cells) assert.ok(c.geometry.getAttribute('_confidence'), 'track grade channel');
// every rail strip faces the sky: a strip wound face-down is culled and the track is not drawn at all
for (const c of cells) {
  const p = c.geometry.getAttribute('position').array;
  for (let t = 0; t < p.length; t += 9) {
    const ux = p[t + 3] - p[t], uz = p[t + 5] - p[t + 2], vx = p[t + 6] - p[t], vz = p[t + 8] - p[t + 2];
    assert.ok(uz * vx - ux * vz > 0, `track cell ${c.key}: a strip faces down`);
  }
}

// car
const g = R.carGeometry(car, doc.companies.ccr.livery, doc.gauge_m);
g.computeBoundingBox();
const bb = g.boundingBox;
const len = bb.max.z - bb.min.z, wid = bb.max.x - bb.min.x, hi = bb.max.y;
assert.ok(len > 6.6 && len < 7.6, `car length ${len.toFixed(2)}`);
assert.ok(wid > 2.0 && wid < 2.6, `car width ${wid.toFixed(2)}`);
assert.ok(hi > 3.0 && hi < 3.5, `car height ${hi.toFixed(2)}`);
assert.ok(bb.min.y >= -0.01, 'the wheels stand on the rail');
assert.ok(g.getAttribute('position').count / 3 < 6000, 'the car is cheap');

// mount: far from every line, nothing is built
const rail = await R.mountHorseRailway1871({ dataBase: here, doc, height: () => 3.23, hour: () => 15, date: () => '1871-10-08' });
rail.update(.016, new THREE.Vector3(-6000, 0, 6000));
let snap = rail.snapshot();
assert.equal(snap.built.length, 0);
assert.equal(snap.cellsShown, 0);
assert.ok(snap.running);
rail.update(.016, new THREE.Vector3(830, 4, 300));   // State and Washington
snap = rail.snapshot();
assert.ok(snap.cellsShown > 0, 'the track near State and Washington is drawn');
const near = rail.nearest(830, -300);
assert.ok(near && near.d < 160, `a State Street car is within reach (${near?.d?.toFixed(0)} m)`);
const night = await R.mountHorseRailway1871({ dataBase: here, doc, height: () => 3.23, hour: () => 1.5, date: () => '1871-10-09' });
night.update(.016, new THREE.Vector3(830, 4, 300));
assert.equal(night.running, false);
assert.equal(night.snapshot().built.length, 0);
rail.dispose(); night.dispose();
console.log(`test_horse_railway_1871: ok (${doc.sections.length} sections, ${doc.services.length} car lines, ${cells.length} track cells, ${tris} triangles)`);
