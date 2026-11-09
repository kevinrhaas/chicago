// SPDX-License-Identifier: GPL-3.0-or-later
// T-3522: every 1812 townsperson dressed as their own (docs/RESEARCH/town-dress-1812-3522/dress.py,
// data/humans/variation/dress_1812_town.json), with a hat made for their head (human-hats.js).
// It must: dress every drawn settler, trader, engagé and townswoman who is not a soldier, and
// no two of one body alike in hat, upper and lower garment; carry each record whole into the
// persons file humans.js reads; lay a hat on the head bone a few millimetres out from the head,
// above the brow, rigid, its outline the spec's own (a taller crown stands taller, a wider brim
// reaches further), with the band as its own mesh; give a piece its own colour where pieces share
// a material; put the dress on the card; and be wired into humans.js's build().
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
const hooks = registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const { dressHat, hatSpec } = await import(new URL('renderers/web/js/human-hats.js', here));
const { dressCloth } = await import(new URL('renderers/web/js/human-looks.js', here));
const { looksOf } = await import(new URL('renderers/web/js/person-card.js', here));
const read = async (p) => JSON.parse(await fs.readFile(new URL(p, here), 'utf8'));

// 1. Who is dressed, and that no two of one body are alike.
const town = await read('data/humans/variation/dress_1812_town.json');
const persons = (await read('assets/humans/web/hm08_variation_persons.json')).persons;
const bodies = new Set(['settler_1812', 'trader_1812', 'engage_1812', 'woman_working_1812', 'lady_1812']);
const index = await read('data/humans/instances/1812/index.json');
const rows = Array.isArray(index) ? index : index.instances ?? index.records ?? [];
let drawn = 0;
for (const row of rows) {
  const file = typeof row === 'string' ? row : row.file ?? row.path;
  if (!file) continue;
  const inst = await read(`data/humans/instances/1812/${file.split('/').pop().replace(/(\.json)?$/, '.json')}`);
  if (!bodies.has(inst.appearance?.asset_id) || !inst.person_id) continue;
  drawn++;
  if (!town.persons[inst.person_id]) {
    // A soldier moved onto a town body for chores is dressed by the garrison's file, not this one.
    assert(Object.values(persons[inst.person_id]?.dress ?? {}).length, `${inst.person_id} (${inst.appearance.asset_id}) has no dress`);
  }
}
assert(Object.keys(town.persons).length >= 35, `townspeople dressed: ${Object.keys(town.persons).length}`);
const seen = new Map();
for (const [pid, rec] of Object.entries(town.persons)) {
  assert(bodies.has(rec.asset), `${pid}: ${rec.asset}`);
  assert(rec.grade === 'reconstructed' && rec.sources.length && rec.reading && rec.worn, `${pid}: graded, sourced, read and worded`);
  const key = JSON.stringify([rec.asset, rec.colours, rec.hide, rec.hat ?? null, rec.headcloth ?? null]);
  assert(!seen.has(key), `${pid} is dressed exactly as ${seen.get(key)}`);
  seen.set(key, pid);
  const p = persons[pid]?.dress;
  assert(p, `${pid}: the persons file carries the dress`);
  assert.deepEqual(p.colours ?? {}, rec.colours, `${pid}: colours carried`);
  assert.deepEqual(p.hide ?? [], rec.hide, `${pid}: pieces left off carried`);
  assert.deepEqual(p.hat ?? null, rec.hat ?? null, `${pid}: hat carried`);
  assert.deepEqual(p.headcloth ?? null, rec.headcloth ?? null, `${pid}: headcloth carried`);
  if (rec.hat) assert(rec.hide.some((h) => /^headwear_/.test(h)), `${pid}: the body's own hat is off under the made one`);
}
// The hats differ in outline, not only colour: kinds, and crowns spread over a few centimetres.
const hats = Object.values(town.persons).map((r) => r.hat).filter(Boolean);
assert(new Set(hats.map((h) => h.kind)).size >= 3, 'round, straw and knitted hats');
const crowns = hats.filter((h) => h.kind !== 'knit').map((h) => h.crown_m);
assert(Math.max(...crowns) - Math.min(...crowns) > .05, 'crowns from low to tall');
const bare = Object.values(town.persons).filter((r) => !r.hat && !r.headcloth && r.hide.some((h) => /^headwear_/.test(h)));
assert(bare.length >= 1, 'someone bareheaded');
assert(Object.values(town.persons).filter((r) => r.headcloth).length >= 4, 'the women of the country in their head handkerchiefs');

// 2. A hat on a synthetic head (the contract's bones; a cap and a skin quantised as exports are).
const C = new THREE.Vector3(0, 1.66, .02), FACE = new THREE.Vector3(0, 1.62, .06), R_HEAD = .095, UNIT = .9;
function figure() {
  const root = new THREE.Group(); root.position.set(30, 1, -12);
  const names = ['root', 'head', 'jaw', 'eye_l', 'eye_r'];
  const at = { root: [0, 0, 0], head: [0, 1.6, .03], jaw: [0, 1.61, .045], eye_l: [.03, 1.64, .114], eye_r: [-.03, 1.64, .114] };
  const bones = names.map((n) => Object.assign(new THREE.Bone(), { name: n }));
  for (const b of bones.slice(1)) bones[0].add(b);
  for (const b of bones) { b.position.fromArray(at[b.name]); if (b !== bones[0]) b.position.sub(bones[0].position); }
  root.add(bones[0]); root.updateMatrixWorld(true);
  const toRoot = new THREE.Matrix4().copy(root.matrixWorld), unit = new THREE.Matrix4().makeScale(UNIT, UNIT, UNIT);
  const skeleton = new THREE.Skeleton(bones, bones.map((b) => new THREE.Matrix4().copy(b.matrixWorld).invert().multiply(toRoot).multiply(unit)));
  const sphere = (keep, material, centre) => {
    const g = new THREE.SphereGeometry(R_HEAD, 48, 32), pos = g.attributes.position, q = [], j = [], w = [];
    for (let i = 0; i < pos.count; i++) { const p = new THREE.Vector3().fromBufferAttribute(pos, i).add(centre); q.push(p.x / UNIT, p.y / UNIT, p.z / UNIT); j.push(1, 0, 0, 0); w.push(1, 0, 0, 0); }
    g.setAttribute('position', new THREE.Float32BufferAttribute(q, 3));
    g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(j, 4));
    g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(w, 4));
    if (keep) { const idx = g.index.array, kept = []; for (let t = 0; t < idx.length; t += 3) if (Math.min(...[0, 1, 2].map((k) => pos.getY(idx[t + k]) / UNIT * UNIT - centre.y)) > .01) kept.push(idx[t], idx[t + 1], idx[t + 2]); g.setIndex(kept); }
    const m = new THREE.SkinnedMesh(g, new THREE.MeshStandardMaterial({ name: material }));
    root.add(m); m.bind(skeleton, new THREE.Matrix4());
    return m;
  };
  const cap = sphere(true, 'hair__makehuman_short04', C);
  sphere(false, 'skin', FACE);
  root.updateMatrixWorld(true);
  return { root, cap };
}
const worldBox = (mesh) => {
  const box = new THREE.Box3(), v = new THREE.Vector3();
  mesh.updateMatrixWorld(true); mesh.skeleton.update();
  for (let i = 0; i < mesh.geometry.attributes.position.count; i++) box.expandByPoint(mesh.getVertexPosition(i, v).applyMatrix4(mesh.matrixWorld));
  return box;
};
const put = (hat, person = 'x') => { const f = figure(); const done = dressHat(f.root, hat, { person, lod: 0 }); return { ...f, done }; };
{
  const tall = put({ kind: 'round', rgb: [.02, .02, .02], band: [.01, .01, .01], crown_m: .15, brim_m: .05 });
  const low = put({ kind: 'round', rgb: [.02, .02, .02], crown_m: .09, brim_m: .1 });
  assert(tall.done && low.done, 'hats made');
  const t = worldBox(tall.done.mesh), l = worldBox(low.done.mesh);
  const eye = 1 + 1.64, head = 1 + C.y + R_HEAD;
  assert(t.min.y > eye + .005 && t.min.y < eye + .05, `the brim sits above the brow: ${(t.min.y - eye).toFixed(3)}`);
  assert(t.max.y > head && l.max.y > head - .01, 'the crown rises over the head');
  assert(t.max.y - l.max.y > .045, `a taller crown stands taller: ${(t.max.y - l.max.y).toFixed(3)}`);
  assert((l.max.x - l.min.x) - (t.max.x - t.min.x) > .08, 'a wider brim reaches further');
  assert(/^headwear__round_hat_t3522$/.test(tall.done.mesh.material.name), 'named as headwear, so the hair is cut under it');
  const band = tall.cap.parent.children.find((o) => /band/.test(o.material?.name ?? ''));
  assert(band && band.isSkinnedMesh && !Array.isArray(band.material), 'the band is its own mesh, one material');
  const si = tall.done.mesh.geometry.attributes.skinIndex, sw = tall.done.mesh.geometry.attributes.skinWeight;
  for (let i = 0; i < si.count; i++) assert(si.getX(i) === 1 && sw.getX(i) === 1, 'rigid on the head bone');
  // Out from the head everywhere: no point of the hat inside the cap's sphere.
  const v = new THREE.Vector3(), centre = new THREE.Vector3(30, 1 + C.y, -12 + C.z);
  for (let i = 0; i < si.count; i++) assert(tall.done.mesh.getVertexPosition(i, v).applyMatrix4(tall.done.mesh.matrixWorld).distanceTo(centre) > R_HEAD + .003, 'never inside the head');
  // It moves with the head.
  const before = worldBox(tall.done.mesh).getCenter(new THREE.Vector3());
  tall.cap.skeleton.bones[1].rotation.x = .4; tall.root.updateMatrixWorld(true);
  assert(worldBox(tall.done.mesh).getCenter(new THREE.Vector3()).distanceTo(before) > .01, 'nods with the head');
  const knit = put({ kind: 'knit', rgb: [.3, .04, .03], tail_m: .1 });
  const k = worldBox(knit.done.mesh);
  assert(k.min.z < -12 + C.z - R_HEAD, 'a knitted cap falls back behind the head');
  assert.equal(dressHat(figure().root, { kind: 'mitre', rgb: [1, 1, 1] }), null, 'an unknown kind is drawn as nothing');
  assert.equal(hatSpec({ kind: 'round', rgb: [0, 0, 0], crown_m: 2 }).crown, .19, 'numbers held to a hat of 1812');
  // At a far level, fewer bearings.
  const far = dressHat(figure().root, { kind: 'straw', rgb: [.5, .4, .2] }, { person: 'x', lod: 3 });
  assert(far.mesh.geometry.attributes.position.count < tall.done.mesh.geometry.attributes.position.count, 'lighter far off');
}

// 3. A piece's own colour where pieces share a material; pieces left off.
{
  const root = new THREE.Group(), shared = new THREE.MeshStandardMaterial({ name: 'garment_upper__gown_blue_print_1812' });
  const bodice = new THREE.Mesh(new THREE.BufferGeometry(), shared), band = new THREE.Mesh(new THREE.BufferGeometry(), shared), apron = new THREE.Mesh(new THREE.BufferGeometry(), shared);
  bodice.name = 'lady_1812_gown_bodice_lod0'; band.name = 'lady_1812_gown_waist_band_lod0'; apron.name = 'lady_1812_apron_lod2';
  root.add(bodice, band, apron);
  const made = dressCloth(root, { colours: { garment_upper__gown_blue_print_1812: [.5, .5, .5] }, pieces: { gown_waist_band: [.3, .05, .04] }, hide: ['apron'] });
  assert(Math.abs(band.material.color.r - new THREE.Color().setRGB(.3, .05, .04, THREE.LinearSRGBColorSpace).r) < 1e-6 && band.material !== bodice.material, 'the band its own colour');
  assert(!apron.visible && bodice.visible, 'the apron left off');
  assert(made.length === 2, 'two clones to free');
}

// 4. The card says what they wear; humans.js puts the hat on.
const card = looksOf({ complexion: { value: 'fair' }, hair: { value: 'brown' }, worn: 'a straw hat; a tow shirt' });
assert.equal(Object.fromEntries(card.rows).Dress, 'A straw hat; a tow shirt', 'the card\'s Dress row');
const humans = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
assert(/import \{ dressHat \} from '\.\/human-hats\.js';/.test(humans) && /dressHat\(scene, dress\.hat, \{ person: this\.personId, lod \}\)/.test(humans), 'humans.js builds the hat');
const mainJs = await fs.readFile(new URL('renderers/web/js/main.js', here), 'utf8');
assert(/worn: r\?\.dress\?\.worn/.test(mainJs), 'the card reads the dress');
hooks.deregister();
console.log(`town dress: ${Object.keys(town.persons).length} townspeople, ${drawn} drawn on town bodies, ${hats.length} hats made, none alike: PASS`);
