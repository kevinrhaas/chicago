// SPDX-License-Identifier: GPL-3.0-or-later
// T-3553: a mouth that opens (renderers/web/js/human-mouth.js). The teeth: a record's strip is
// read or refused; it is added to a skin's geometry as rows of its own after the source's, where
// the record puts them, coloured from where the record says, carried whole by one bone, facing
// out of the mouth, left alone by every morph target; the source is never changed; and what
// was made is kept once for a sheet and freed with its source. The mouth's play: a face with the
// smile gives it to a visitor near in front and with a greeting, eases in and out, keeps part of
// it talking while the jaw runs in syllables, the same run for the same person; a voice takes
// the jaw; the next level's mouth carries on from the last; a face without the smile talks with
// its jaw alone and no target of it is written; and one with neither is not a mouth.
// Everyone's drawn teeth: the lips' inner edge is found on every body by its place on the map
// (all of it at the nearest level, less of it further off: every body at every level is read
// here, and the three that have too little of it left for rows are named); two rows stand
// behind it, the upper on the head and the lower on the jaw, bowed forward to the middle, from
// a little past one corner of the mouth to a little past the other, each by its own lip's
// edge, their place on the map saying which row, set and tone as the skin's shader reads it
// back; they are made as rows apart, of the source's own kind, with its count of morph
// targets; and the mouth shows them to a visitor who stands near the figure, and to nobody else.
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const { teethStrip, teethGeometry, teethOf, createMouth, MOUTH, LIP_RIM, LIP_ARCS, TEETH_DRAWN, lipRim, drawnLook, drawnTeeth } = await import(new URL('renderers/web/js/human-mouth.js', here));
const { SMILE } = await import(new URL('renderers/web/js/human-variation.js', here));

// A strip of 3 across by 2 down, 1 cm a step, standing 2 cm in front of the origin; its colour
// from a patch off the head's own island.
const record = () => ({ grid: [3, 2], bone: 'head',
  at_m: [[-.01, .005, .02], [0, .005, .021], [.01, .005, .02], [-.01, -.005, .02], [0, -.005, .021], [.01, -.005, .02]],
  uv: [[.6, .1], [.65, .1], [.7, .1], [.6, .15], [.65, .15], [.7, .15]] });
const strip = teethStrip(record());
assert.deepEqual([strip.cols, strip.rows, strip.bone, strip.at.length, strip.uv.length], [3, 2, 'head', 18, 12]);
for (const bad of [null, {}, { ...record(), grid: [1, 2] }, { ...record(), grid: [3, 3] }, { ...record(), bone: 7 }, { ...record(), uv: record().uv.slice(1) },
  { ...record(), at_m: record().at_m.map(p => p.slice(0, 2)) }, { ...record(), at_m: record().at_m.map(() => [0, NaN, 0]) }]) {
  assert.equal(teethStrip(bad), null, JSON.stringify(bad)?.slice(0, 70));
}

// A head: a ball of 10 cm in the file's own numbers (centimetres, so the matrix to metres is a
// scale), with bones, a blink that moves and a quantised normal.
const ball = () => {
  const g = new THREE.SphereGeometry(10, 12, 8);
  const n = g.attributes.position.count, ji = new Uint16Array(n * 4), jw = new Uint8Array(n * 4), blink = new Float32Array(n * 3), nq = new Int8Array(n * 3);
  for (let i = 0; i < n; i++) {
    ji.set([0, 1, 2, 0], i * 4); jw.set([128, 100, 27, 0], i * 4);
    blink.set([0, g.attributes.position.getY(i) * .1, 0], i * 3);
    for (let c = 0; c < 3; c++) nq[i * 3 + c] = Math.round(g.attributes.normal.getComponent(i, c) * 127);
  }
  g.setAttribute('normal', new THREE.BufferAttribute(nq, 3, true));
  g.setAttribute('skinIndex', new THREE.BufferAttribute(ji, 4));
  g.setAttribute('skinWeight', new THREE.BufferAttribute(jw, 4, true));
  g.morphAttributes.position = [Object.assign(new THREE.BufferAttribute(blink, 3), { name: 'eyeBlinkLeft' })];
  g.morphAttributes.normal = [Object.assign(new THREE.BufferAttribute(new Float32Array(n * 3), 3), { name: 'eyeBlinkLeft' })];
  g.morphTargetsRelative = true;
  g.computeBoundingSphere();
  return g;
};
const metres = new THREE.Matrix4().makeScale(.01, .01, .01);
const src = ball(), n0 = src.attributes.position.count, tri0 = src.index.count;
const before = JSON.stringify([...Object.values(src.attributes).map(a => Array.from(a.array)), Array.from(src.index.array)]);
const g = teethGeometry(src, { metres, strip, bone: 2 });
assert(g && g !== src, 'a geometry of its own');
assert.equal(JSON.stringify([...Object.values(src.attributes).map(a => Array.from(a.array)), Array.from(src.index.array)]), before, 'the source is not changed');
assert.deepEqual(g.userData.chiTeeth, { of: n0, added: 6 });
for (const [name, a] of Object.entries(src.attributes)) {
  const b = g.attributes[name];
  assert.equal(b.count, n0 + 6, `${name}: six rows more`);
  assert.equal(b.array.constructor, a.array.constructor, `${name}: kept in the source's own numbers`);
  assert.equal(b.normalized, a.normalized, `${name}: read as the source's is`);
  assert.deepEqual(Array.from(b.array.slice(0, n0 * a.itemSize)), Array.from(a.array), `${name}: the source's rows first, in order`);
}
const v = new THREE.Vector3();
for (let j = 0; j < 6; j++) {
  const i = n0 + j;
  v.fromBufferAttribute(g.attributes.position, i).applyMatrix4(metres);
  assert(v.distanceTo(new THREE.Vector3(...record().at_m[j])) < 1e-6, `point ${j} stands where the record puts it`);
  assert(Math.hypot(g.attributes.uv.getX(i) - record().uv[j][0], g.attributes.uv.getY(i) - record().uv[j][1]) < 1e-6, `point ${j} takes its colour from where the record says`);
  assert.deepEqual([0, 1, 2, 3].map(c => g.attributes.skinIndex.getComponent(i, c)), [2, 0, 0, 0], 'carried by the one bone');
  assert.deepEqual([0, 1, 2, 3].map(c => g.attributes.skinWeight.getComponent(i, c)), [1, 0, 0, 0], 'and wholly by it');
  v.fromBufferAttribute(g.attributes.normal, i);
  assert(v.z > .9 && Math.abs(v.length() - 1) < .02, `point ${j} faces out of the mouth (${v.toArray().map(x => x.toFixed(2))})`);
  for (const list of Object.values(g.morphAttributes)) for (const t of list) assert.deepEqual([t.getX(i), t.getY(i), t.getZ(i)], [0, 0, 0], 'a morph target leaves the strip where it stands');
}
for (const [name, list] of Object.entries(src.morphAttributes)) {
  assert.equal(g.morphAttributes[name].length, list.length);
  list.forEach((t, k) => {
    assert.equal(g.morphAttributes[name][k].name, t.name, 'a target keeps its name');
    assert.deepEqual(Array.from(g.morphAttributes[name][k].array.slice(0, n0 * 3)), Array.from(t.array), 'and its moves');
  });
}
assert.equal(g.morphTargetsRelative, true);
// Two cells, two triangles each, after the source's own, each wound to face out of the mouth (+z).
assert.equal(g.index.count, tri0 + 12);
assert.deepEqual(Array.from(g.index.array.slice(0, tri0)), Array.from(src.index.array), "the source's triangles first");
const P = i => new THREE.Vector3().fromBufferAttribute(g.attributes.position, i);
for (let t = tri0; t < g.index.count; t += 3) {
  const [a, b, c] = [0, 1, 2].map(k => g.index.getX(t + k));
  assert(a >= n0 && b >= n0 && c >= n0, "the strip's triangles join only its own points");
  assert(new THREE.Vector3().crossVectors(P(b).sub(P(a)), P(c).sub(P(a))).z > 0, 'and face out of the mouth');
}
assert.equal(g.boundingSphere, src.boundingSphere, "the source's bounds hold");

// What cannot take a strip is refused, not guessed at.
const grouped = ball(); grouped.addGroup(0, 6, 0);
const loose = ball().toNonIndexed();
const bare = ball(); bare.deleteAttribute('uv');
for (const [what, geo, opts] of [['no strip', src, { metres, strip: null, bone: 2 }], ['no bone', src, { metres, strip, bone: -1 }], ['no matrix', src, { strip, bone: 2 }],
  ['drawn in groups', grouped, { metres, strip, bone: 2 }], ['no index', loose, { metres, strip, bone: 2 }], ['no texture coordinates', bare, { metres, strip, bone: 2 }]]) {
  assert.equal(teethGeometry(geo, opts), null, what);
}

// Several strips, each carried by its own bone; and the rows alone, as a geometry of the source's kind.
{ const lower = teethStrip({ ...record(), bone: 'jaw', at_m: record().at_m.map(q => [q[0], q[1] - .02, q[2]]) });
  const two = teethGeometry(src, { metres, strips: [{ strip, bone: 2 }, { strip: lower, bone: 1 }] });
  assert.deepEqual(two.userData.chiTeeth, { of: n0, added: 12 });
  assert.equal(two.index.count, tri0 + 24);
  for (let j = 0; j < 12; j++) assert.equal(two.attributes.skinIndex.getComponent(n0 + j, 0), j < 6 ? 2 : 1, 'each strip by its own bone');
  for (let t = tri0; t < two.index.count; t += 3) {
    const ids = [0, 1, 2].map(k => two.index.getX(t + k) - n0);
    assert(ids.every(i => i >= 0 && i < 6) || ids.every(i => i >= 6 && i < 12), 'no triangle joins two strips');
  }
  v.fromBufferAttribute(two.attributes.position, n0 + 6).applyMatrix4(metres);
  assert(v.distanceTo(new THREE.Vector3(-.01, -.015, .02)) < 1e-6, "the second strip's points follow the first's");
  assert.equal(teethGeometry(src, { metres, strips: [{ strip, bone: 2 }, { strip: lower, bone: -1 }] }), null, 'a strip with no bone refuses them all');
  assert.equal(teethGeometry(src, { metres, strips: [] }), null, 'no strips at all');
  const apart = teethGeometry(src, { metres, apart: true, strips: [{ strip, bone: 2 }, { strip: lower, bone: 1 }] });
  assert.deepEqual(apart.userData.chiTeeth, { of: 0, added: 12 });
  assert.deepEqual(Object.keys(apart.attributes).sort(), Object.keys(src.attributes).sort(), "rows apart have the source's attributes, all of them");
  for (const [name, a] of Object.entries(src.attributes)) {
    const b = apart.attributes[name];
    assert(b.count === 12 && b.itemSize === a.itemSize, `${name}: twelve rows`);
    if (name === 'uv') assert(b.array instanceof Float32Array && !b.normalized, 'their place on the map is kept as plain numbers');
    else assert(b.array.constructor === a.array.constructor && b.normalized === a.normalized, `${name}: kept as the source's are`);
  }
  assert(apart.index.count === 24 && Array.from(apart.index.array).every(i => i < 12), 'and only their own triangles');
  // ...and its count of morph targets (the one program draws both), none of which moves them.
  assert.deepEqual(Object.keys(apart.morphAttributes).sort(), Object.keys(src.morphAttributes).sort(), "the source's kinds of morph target");
  for (const [name, list] of Object.entries(src.morphAttributes)) {
    assert.equal(apart.morphAttributes[name].length, list.length, `${name}: as many as the source has`);
    list.forEach((t, k) => {
      const b = apart.morphAttributes[name][k];
      assert(b.count === 12 && b.name === t.name && b.array.constructor === t.array.constructor && Array.from(b.array).every(x => x === 0), `${name} ${k}: a target that leaves the rows where they stand`);
    });
  }
  assert.equal(apart.morphTargetsRelative, src.morphTargetsRelative);
  assert(apart.boundingSphere !== src.boundingSphere && apart.boundingSphere.equals(src.boundingSphere), "bounds of their own, the source's to begin with");
  apart.computeBoundingSphere();
  assert(src.boundingSphere.radius > 9, "measuring the rows does not move the source's bounds");
  v.fromBufferAttribute(apart.attributes.position, 0).applyMatrix4(metres);
  assert(v.distanceTo(new THREE.Vector3(...record().at_m[0])) < 1e-6, 'standing where the record puts them');
  assert.deepEqual([0, 1, 2, 3].map(c => apart.attributes.skinIndex.getComponent(11, c)), [1, 0, 0, 0]);
  assert.equal(JSON.stringify([...Object.values(src.attributes).map(a => Array.from(a.array)), Array.from(src.index.array)]), before, 'the source is not changed'); }

// Kept once for a source and a sheet; a geometry with its teeth is handed back; freed with its source.
{ const s = ball(), a = teethOf(s, 'sheet-a', { metres, strip, bone: 2 });
  assert(a.userData.chiTeeth && teethOf(s, 'sheet-a', { metres, strip, bone: 2 }) === a, 'the same sheet, the same geometry');
  assert(teethOf(s, 'sheet-b', { metres, strip, bone: 2 }) !== a, "another sheet's is its own");
  assert.equal(teethOf(a, 'sheet-a', { metres, strip, bone: 2 }), a, 'teeth are not added twice');
  assert.equal(teethOf(s, 'sheet-c', { metres, strip: null, bone: 2 }), s, 'with no strip the source is drawn as it is');
  assert.equal(teethOf(null, 'x', {}), null);
  // Options that are worked out only when the geometry has to be made, and once.
  let asked = 0;
  const make = () => { asked++; return { metres, strip, bone: 2 }; };
  const c = teethOf(s, 'sheet-d', make);
  assert(c.userData.chiTeeth && teethOf(s, 'sheet-d', make) === c && asked === 1, 'worked out once');
  assert.equal(teethOf(s, 'sheet-e', () => null), s, 'none worked out: the source as it is');
  let freed = 0; a.addEventListener('dispose', () => freed++);
  s.dispose();
  assert.equal(freed, 1, 'freed with its source'); }

// The mouth's play. A face: a skinned mesh whose body has the blink, the exported jaw target and
// the smile, on a skeleton whose head (turned, as a clip holds it) carries a jaw bone.
const DEG = Math.PI / 180;
const face = (names = ['eyeBlinkLeft', 'jawOpen', SMILE], { jawBone = true } = {}) => {
  const scene = new THREE.Group(), head = Object.assign(new THREE.Bone(), { name: 'head' }), jaw = Object.assign(new THREE.Bone(), { name: 'jaw' });
  head.position.set(0, 1.6, 0); jaw.position.set(0, -.02, .03); jaw.rotation.set(.4, 0, 0);
  if (jawBone) head.add(jaw);
  const mesh = new THREE.SkinnedMesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial());
  scene.add(head, mesh); scene.updateMatrixWorld(true);
  mesh.bind(new THREE.Skeleton(jawBone ? [head, jaw] : [head]), mesh.matrixWorld);
  mesh.morphTargetDictionary = Object.fromEntries(names.map((k, i) => [k, i]));
  mesh.morphTargetInfluences = names.map(() => 0);
  const rest = jaw.quaternion.clone(), chin = new THREE.Vector3(0, -.06, .07);
  return { scene, head, jaw, w: mesh.morphTargetInfluences, at: mesh.morphTargetDictionary,
    // How far the jaw is turned from where the clip holds it, degrees; and where the chin is, in the figure's frame.
    deg: () => 2 * Math.acos(Math.min(1, Math.abs(jaw.quaternion.dot(rest)))) / DEG,
    chin: () => { scene.updateMatrixWorld(true); return jaw.localToWorld(chin.clone()); } };
};
const run = (m, seconds, state, each) => { for (let t = 0; t < seconds; t += 1 / 30) { m.apply(1 / 30, state); each?.(); } };
{ const f = face(), m = createMouth({ id: 'pa1904_grey_w_l', scene: f.scene });
  assert(m.bound, 'a face with the smile is played');
  run(m, 3, {});
  assert.deepEqual([f.w, f.deg()], [[0, 0, 0], 0], 'at rest nothing is moved');
  // A visitor in front: the smile comes, never past the whole of it, and stays while they stand there.
  let last = 0, rose = true;
  run(m, 2.5, { facing: true }, () => { rose &&= f.w[f.at[SMILE]] >= last - 1e-9; last = f.w[f.at[SMILE]]; });
  assert(rose && last === 1, `the smile eases in to the whole of it (${last})`);
  assert.equal(f.deg(), 0, 'and the jaw is still');
  m.apply(1 / 30, {});
  assert(f.w[f.at[SMILE]] < 1 && f.w[f.at[SMILE]] > .9, 'it does not snap off');
  run(m, 6, {});
  assert.equal(f.w[f.at[SMILE]], 0, 'and goes when they have gone');
  // A greeting brings it, and it outlasts the greeting by after_s.
  run(m, 1.7, { greeting: true });
  run(m, MOUTH.after_s * .8, {});
  assert(f.w[f.at[SMILE]] > .95, `it stays after a greeting (${f.w[f.at[SMILE]]})`);
  run(m, 6, {});
  assert.equal(f.w[f.at[SMILE]], 0);
  // Talking: part of the smile, and the jaw opens and shuts about the body's own left-to-right,
  // the chin going down and not aside, never past its height.
  const shutChin = f.chin();
  let hi = 0, lo = 99, shut = 0, low = shutChin.clone();
  run(m, 20, { talk: 1 }, () => { const d = f.deg(); hi = Math.max(hi, d); lo = Math.min(lo, d); if (d < .2) shut++; const c = f.chin(); if (c.y < low.y) low = c; });
  assert(Math.abs(f.w[f.at[SMILE]] - MOUTH.talk) < 1e-6, `talking keeps part of the smile (${f.w[f.at[SMILE]]})`);
  assert(hi > MOUTH.jaw_deg * .5 && hi <= MOUTH.jaw_deg + 1e-6 && lo < .2 && shut > 30, `the jaw runs in syllables (${lo.toFixed(2)}..${hi.toFixed(2)} degrees, shut ${shut} frames)`);
  assert(low.y < shutChin.y - .003 && Math.abs(low.x - shutChin.x) < 1e-6, `the chin goes down, not aside (${low.toArray().map(x => x.toFixed(4))} from ${shutChin.toArray().map(x => x.toFixed(4))})`);
  assert.deepEqual(f.w.slice(0, 2), [0, 0], 'the blink and the exported jaw target are not its to write');
  run(m, 6, {});
  assert.deepEqual([f.w[f.at[SMILE]], f.deg()], [0, 0], 'and both come to rest');
  assert(f.chin().distanceTo(shutChin) < 1e-9, 'the jaw is back where the clip holds it');
  // A voice takes the jaw outright, and gives it back.
  m.say(.5); run(m, 1, {});
  assert(Math.abs(f.deg() - MOUTH.say_deg * .5) < .01 && Math.abs(f.w[f.at[SMILE]] - MOUTH.talk) < .05, `a voice opens the jaw to its level (${f.deg()})`);
  m.say(2); run(m, 1, {});
  assert(Math.abs(f.deg() - MOUTH.say_deg) < .01, 'a level is held to one');
  m.say(null); run(m, 6, {});
  assert.deepEqual([f.w[f.at[SMILE]], f.deg()], [0, 0]);
  assert.deepEqual(m.snapshot(), { smile: 0, jaw_deg: 0, faces: 1, said: null });
  // A clip that moves the jaw itself is followed: the opening is turned on over what it holds now.
  const held = new THREE.Quaternion().setFromEuler(new THREE.Euler(.1, .2, 0));
  f.jaw.quaternion.copy(held);
  m.say(1); run(m, 1, {});
  const over = 2 * Math.acos(Math.min(1, Math.abs(f.jaw.quaternion.dot(held)))) / DEG;
  assert(Math.abs(over - MOUTH.say_deg) < .01, `the opening is over the clip's own pose (${over})`);
  m.say(null); run(m, 6, {});
  assert(f.jaw.quaternion.equals(held), "and the clip's pose is left as it was");
  // A still: held where it is asked.
  m.pose({ smile: .5, jaw: 5 });
  assert(f.w[f.at[SMILE]] === .5 && Math.abs(2 * Math.acos(Math.min(1, Math.abs(f.jaw.quaternion.dot(held)))) / DEG - 5) < .01, 'a still holds the smile and the jaw it is given');
  // Bound again while the jaw is turned (a level set aside mid-word and taken up again): the
  // turn is not taken for the clip's own pose.
  m.bind(f.scene); m.pose({ smile: 0, jaw: 0 });
  assert(f.jaw.quaternion.equals(held), 'binding again does not keep an old opening'); }
// The same person talks the same way; another, another.
{ const jaws = id => { const f = face(), m = createMouth({ id, scene: f.scene }), out = []; run(m, 8, { talk: 1 }, () => out.push(+f.deg().toFixed(4))); return out; };
  assert.deepEqual(jaws('a'), jaws('a'));
  assert.notDeepEqual(jaws('a'), jaws('b')); }
// Where the visitor stands: near and in front is smiled at; far, beside or behind is not. The
// figure faces its own +Z, turned by its heading.
{ const at = (x, z, heading = 0) => { const f = face(), m = createMouth({ id: 'x', scene: f.scene }), root = new THREE.Group();
    root.position.set(10, 0, -4); root.rotation.y = heading;
    run(m, 3, { viewer: new THREE.Vector3(10 + x, 1.6, -4 + z), root }); return f.w[f.at[SMILE]]; };
  assert.equal(at(0, 2), 1, 'two metres in front');
  assert.equal(at(1, 2), 1, 'a little to one side');
  assert.equal(at(0, MOUTH.within_m + .5), 0, 'too far');
  assert.equal(at(2, 0), 0, 'beside');
  assert.equal(at(0, -2), 0, 'behind');
  assert.equal(at(2, 0, Math.PI / 2), 1, 'turned to face them');
  assert.equal(at(0, 2, Math.PI / 2), 0, 'turned away'); }
// The next level's mouth carries on from this one's.
{ const a = face(), m = createMouth({ id: 'x', scene: a.scene });
  run(m, 3, { facing: true });
  const b = face(), next = createMouth({ id: 'x', scene: b.scene }).follow(m);
  assert.equal(b.w[b.at[SMILE]], 1, 'the smile is where the last level left it');
  assert.deepEqual(next.state(), m.state());
  assert.equal(createMouth({ id: 'x', scene: face().scene }).follow(null).snapshot().smile, 0, 'with no last level it starts at rest'); }
// A level with the smile and no jaw bone smiles and talks with its lips still; nothing is thrown.
{ const f = face(['eyeBlinkLeft', SMILE], { jawBone: false }), m = createMouth({ id: 'x', scene: f.scene });
  run(m, 5, { talk: 1 });
  assert(m.bound && Math.abs(f.w[f.at[SMILE]] - MOUTH.talk) < 1e-6); }
// A face without the smile has a mouth all the same: it talks with its jaw and smiles at nobody,
// and none of its targets is ever written.
{ const f = face(['eyeBlinkLeft', 'jawOpen']), m = createMouth({ id: 'x', scene: f.scene });
  f.w[1] = .4;
  assert(m.bound, 'a jaw alone is a mouth');
  run(m, 3, { facing: true, greeting: true });
  assert.deepEqual([f.w, f.deg(), m.snapshot().smile], [[0, .4], 0, 0], 'with no smile to give, a visitor and a greeting move nothing');
  let hi = 0, shut = 0;
  run(m, 20, { talk: 1 }, () => { const d = f.deg(); hi = Math.max(hi, d); if (d < .2) shut++; });
  assert(hi > MOUTH.jaw_deg * .5 && hi <= MOUTH.jaw_deg + 1e-6 && shut > 30, `it talks with its jaw (to ${hi.toFixed(2)} degrees)`);
  assert.deepEqual([f.w, m.snapshot().smile, m.snapshot().faces], [[0, .4], 0, 0], 'and writes no target');
  run(m, 6, {});
  assert.equal(f.deg(), 0, 'and its jaw comes to rest');
  m.say(1); run(m, 1, {});
  assert(Math.abs(f.deg() - MOUTH.say_deg) < .01, 'a voice opens its jaw');
  m.say(null); run(m, 6, {});
  m.pose({ smile: 1, jaw: 9 });
  assert(Math.abs(f.deg() - 9) < .01 && f.w[0] === 0 && f.w[1] === .4, 'a still opens its jaw and writes no target'); }
// A face with neither the smile nor a jaw is not a mouth, and is never written.
{ const f = face(['eyeBlinkLeft'], { jawBone: false }), m = createMouth({ id: 'x', scene: f.scene });
  assert(!m.bound);
  run(m, 3, { facing: true, talk: 1, greeting: true });
  m.say(1).pose({ smile: 1, jaw: 9 });
  assert.deepEqual(f.w, [0]); }
// A figure's drawn teeth (a mesh of their own, made hidden) are drawn for a visitor who stands
// near while the jaw is open, and for a still; the next level's mouth carries that on.
{ const f = face(['eyeBlinkLeft', 'jawOpen']), teeth = new THREE.Mesh(), root = new THREE.Group();
  teeth.userData.chiTeeth = true; teeth.visible = false; f.scene.add(teeth);
  // The figure stands well away from the middle of the world: the distance is the visitor's from it.
  root.position.set(40, 0, -25);
  const from = (x, z) => new THREE.Vector3(root.position.x + x, 1.6, root.position.z + z), d = (MOUTH.teeth_m - .5) / Math.SQRT2;
  const m = createMouth({ id: 'x', scene: f.scene }), near = from(d, -d), far = from(0, MOUTH.teeth_m + .5), aside = from(-MOUTH.teeth_m - .5, 0);
  let seen = 0, hidden = 0;
  run(m, 6, { talk: 1 }, () => { if (teeth.visible) seen++; });
  assert.equal(seen, 0, 'with no visitor they are not drawn');
  run(m, 2, { viewer: near, root }, () => { if (teeth.visible) seen++; });
  assert.equal(seen, 0, 'nor behind shut lips, however near the visitor');
  run(m, 6, { talk: 1, viewer: near, root }, () => { const open = m.snapshot().jaw_deg > MOUTH.teeth_deg; assert.equal(teeth.visible, open, 'drawn exactly while the jaw is open'); if (open) seen++; else hidden++; });
  assert(seen > 30 && hidden > 10, `a visitor near sees them as the person talks (${seen} frames of ${seen + hidden})`);
  m.say(1); run(m, 1, { viewer: near, root });
  assert.equal(teeth.visible, true);
  const g2 = face(['eyeBlinkLeft', 'jawOpen']), t2 = new THREE.Mesh();
  t2.userData.chiTeeth = true; t2.visible = false; g2.scene.add(t2);
  createMouth({ id: 'x', scene: g2.scene }).follow(m);
  assert.equal(t2.visible, true, "the next level's are in view at once");
  for (const [where, viewer] of [['ahead', far], ['aside', aside], ['at the middle of the world', new THREE.Vector3(0, 1.6, 0)]]) {
    run(m, 1, { viewer: near, root });
    assert.equal(teeth.visible, true);
    run(m, 1, { viewer, root });
    assert.equal(teeth.visible, false, `a visitor further off, ${where}, does not see them`);
  }
  m.say(null); run(m, 3, {});
  m.pose({ jaw: 3 });
  assert.equal(teeth.visible, true, 'a still with its jaw open has them in view');
  m.pose({ jaw: 0 });
  assert.equal(teeth.visible, false, 'and one with its mouth shut does not');
  // A still is for its picture: the next frame with nobody near does not leave them drawn.
  m.pose({ jaw: 3 }); m.say(1);
  m.apply(1 / 30, {});
  assert(m.snapshot().jaw_deg > MOUTH.teeth_deg && teeth.visible === false, 'after a still, a frame with no visitor draws none'); }
// A mesh of drawn teeth has its face's count of morph targets (one program draws both) and is
// no face: the smile is written to the face alone.
{ const f = face(), teeth = new THREE.Mesh();
  teeth.userData.chiTeeth = true; teeth.visible = false;
  teeth.morphTargetDictionary = { ...f.at }; teeth.morphTargetInfluences = f.w.map(() => 0);
  f.scene.add(teeth);
  const m = createMouth({ id: 'x', scene: f.scene });
  run(m, 3, { facing: true });
  assert.deepEqual([f.w[f.at[SMILE]], teeth.morphTargetInfluences, m.snapshot().faces], [1, [0, 0, 0], 1], 'the teeth are not counted as a face'); }

// Everyone's drawn teeth, on the bodies themselves.
{ const fs = await import('node:fs/promises');
  const { surfaceFor, restMatrix } = await import(new URL('renderers/web/js/human-skin.js', here));
  const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
  const { GLTFLoader } = await import(new URL('addons/loaders/GLTFLoader.js', vendor));
  const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
  await MeshoptDecoder.ready;
  globalThis.self ??= globalThis;
  const bare = bytes => {   // the export without its pictures, which node cannot decode
    const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20 + n));
    for (const m of doc.materials ?? []) {
      delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
      if (m.pbrMetallicRoughness) { delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; }
    }
    const json0 = Buffer.from(JSON.stringify(doc)), json = Buffer.concat([json0, Buffer.alloc(-json0.length & 3, 32)]);
    const bin = bytes.subarray(28 + n), out = Buffer.alloc(28 + json.length + bin.length);
    out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
    out.writeUInt32LE(json.length, 12); out.writeUInt32LE(0x4e4f534a, 16); json.copy(out, 20);
    out.writeUInt32LE(bin.length, 20 + json.length); out.writeUInt32LE(0x004e4942, 24 + json.length); bin.copy(out, 28 + json.length);
    return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
  };
  const skinOf = async (asset, lod) => {
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bare(await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here))), '');
    gltf.scene.updateMatrixWorld(true);
    let mesh = null;
    gltf.scene.traverse((o) => { if (!mesh && o.isSkinnedMesh && surfaceFor(o.material) === 'skin') mesh = o; });
    return { mesh, root: gltf.scene };
  };
  // The same person, the same teeth; the young show their upper teeth and the old their lower.
  const D = TEETH_DRAWN;
  // A place on the map as the skin's shader reads it back (human-skin.js: the lines
  // tools/test_human_skin.mjs holds it to), in the card's own single-precision numbers.
  const f32 = Math.fround, clamp01 = x => Math.min(1, Math.max(0, x));
  const read = (u, w) => {
    const su = f32(f32(u) - D.u0), set = Math.floor(f32(f32(su + 1e-4) / D.set_u));
    const sv = f32(f32(w) - D.v0), tone = Math.floor(f32(sv / D.tone_v)), row = f32(sv - D.tone_v * tone), lower = row >= D.row_v ? 1 : 0;
    return [set, tone, lower, clamp01(f32(su - D.set_u * set)), clamp01(f32(f32(row - D.row_v * lower - D.pad) / f32(1 - 2 * D.pad)))];
  };
  const step = (x, by) => { const f = new Float32Array([x]), i = new Uint32Array(f.buffer); i[0] += by; return f[0]; };
  const below = x => step(x, -1), above = x => step(x, 1);
  assert.deepEqual(drawnLook({ id: 'pa1904_field_marshall', age: 69 }), drawnLook({ id: 'pa1904_field_marshall', age: 69 }));
  const young = drawnLook({ id: 'a', age: 18 }), old = drawnLook({ id: 'a', age: 80 }), unknown = drawnLook({ id: 'a' });
  assert.deepEqual([young.upper, young.lower, old.upper, old.lower], [D.upper_m[0], D.lower_m[0], D.upper_m[1], D.lower_m[1]]);
  assert(unknown.upper < young.upper && unknown.upper > old.upper, 'an age not known is a middle one');
  assert(young.tone <= old.tone && old.tone >= 1, `older teeth are no whiter (${young.tone}, ${old.tone})`);
  const looks = Array.from({ length: 400 }, (_, i) => drawnLook({ id: `crowd_${i}`, age: 20 + (i % 60) }));
  assert(looks.every(l => Number.isInteger(l.set) && l.set >= 0 && l.set < D.sets && Number.isInteger(l.tone) && l.tone >= 0 && l.tone < D.tones));
  assert.equal(new Set(looks.map(l => l.set)).size, D.sets, 'every set is somebody\'s');
  assert.equal(new Set(looks.map(l => l.tone)).size, D.tones, 'and every tone');
  assert.equal(new Set(looks.map(l => l.key)).size, new Set(looks.map(l => `${l.set}|${l.tone}|${l.upper}|${l.lower}`)).size, 'a key for each kind of teeth');
  const bodies = (await fs.readdir(new URL('assets/humans/web/', here))).filter(f => /\.lod0\.glb$/.test(f) && !/^c4d_fixture\./.test(f)).map(f => f.replace(/\.lod0\.glb$/, '')).sort();
  assert(bodies.length >= 35, `${bodies.length} bodies`);
  // Too little of the lips' edge is left on these, the furthest level of three girls' bodies
  // (no vertex of the lower lip's own): they have no rows. The level is never drawn within MOUTH.teeth_m.
  const none = new Set(['child_girl_1812 lod3', 'child_girl_1904 lod3', 'potawatomi_girl_1812 lod3']), found = [[], [], [], []], bow = [[], [], [], []], parted = [[], [], [], []];
  let drawn = 0, without = 0;
  for (const asset of bodies) for (const lod of [0, 1, 2, 3]) {
    const { mesh, root } = await skinOf(asset, lod), g = mesh.geometry, what = `${asset} lod${lod}`;
    const ids = lipRim(g.attributes.uv);
    assert.equal(lipRim(g.attributes.uv), ids, 'found once for a map');
    found[lod].push(ids.length);
    if (lod === 0) {
      assert.equal(ids.length, LIP_RIM.length, `${what}: every vertex of the lips' edge is found (${ids.length})`);
      // Whose each is (LIP_ARCS): the jaw carries the lower lip's and none of the upper lip's.
      const uv = g.attributes.uv, jaw = mesh.skeleton.bones.findIndex(b => b.name === 'jaw'), last = LIP_RIM.length - 1;
      LIP_RIM.forEach(([u, w], k) => {
        const i = Array.from(ids).find(j => Math.hypot(uv.getX(j) - u, uv.getY(j) - w) < D.within);
        let byJaw = 0;
        for (let c = 0; c < 4; c++) if (g.attributes.skinIndex.getComponent(i, c) === jaw) byJaw += g.attributes.skinWeight.getComponent(i, c);
        if (k >= LIP_ARCS.lower[0] && k <= LIP_ARCS.lower[1]) assert(byJaw > .5, `${what}: the jaw carries the lower lip's edge (${k}: ${byJaw.toFixed(2)})`);
        else if (k <= LIP_ARCS.upper || k >= last - LIP_ARCS.upper) assert(byJaw < .1, `${what}: and not the upper lip's (${k}: ${byJaw.toFixed(2)})`);
        else assert(byJaw >= .05 && byJaw <= .5, `${what}: a corner is both lips' (${k}: ${byJaw.toFixed(2)})`);
      });
    }
    else assert(ids.length >= D.least && ids.length <= LIP_RIM.length, `${what}: enough of the lips' edge is found (${ids.length})`);
    const metres = restMatrix(mesh, root), look = drawnLook({ id: asset, age: 45 }), strips = drawnTeeth(g, { metres, look });
    if (none.has(what)) { assert.equal(strips, null, `${what}: too little of the lips' edge for rows`); without++; continue; }
    assert(strips?.length === 2 && strips[0].bone === 'head' && strips[1].bone === 'jaw', `${what}: an upper row on the head and a lower on the jaw`);
    // The edge itself, metres.
    const rim = Array.from(ids, (i) => v.fromBufferAttribute(g.attributes.position, i).applyMatrix4(metres).toArray());
    const xa = Math.min(...rim.map(q => q[0])), xb = Math.max(...rim.map(q => q[0])), ya = Math.min(...rim.map(q => q[1])), yb = Math.max(...rim.map(q => q[1]));
    strips.forEach(({ strip }, lower) => {
      assert.deepEqual([strip.cols, strip.rows, strip.at.length, strip.uv.length], [D.cols, 2, D.cols * 6, D.cols * 4]);
      const at = (r, c) => Array.from(strip.at.subarray(3 * (r * D.cols + c), 3 * (r * D.cols + c) + 3));
      assert(Math.abs(at(0, 0)[0] - (xa - D.past_m)) < 1e-6 && Math.abs(at(0, D.cols - 1)[0] - (xb + D.past_m)) < 1e-6, `${what}: from past one corner of the mouth to past the other`);
      for (let c = 0; c < D.cols; c++) {
        const top = at(0, c), bottom = at(1, c);
        assert(top[0] === bottom[0] && top[2] === bottom[2] && top[1] > bottom[1] + .004, `${what}: a row stands upright, its top first`);
        // The lips' line there lies within the edge's own heights; the row's hidden side is in its lip, its edge by the line.
        const line = lower ? top[1] - look.lower - D.lip_m[1] : bottom[1] + look.upper + D.lip_m[0];
        assert(line > ya - 1e-6 && line < yb + 1e-6, `${what}: the rows stand by the lips' line (${line.toFixed(4)} in ${ya.toFixed(4)}..${yb.toFixed(4)})`);
        assert(Math.abs((lower ? line - bottom[1] : top[1] - line) - D.gum_m) < 1e-6);
        if (c && c < D.cols - 1) assert(top[2] < at(0, 0)[2] + .03 && top[2] > at(0, 0)[2] - 1e-9, `${what}: the row bows forward to the middle`);
      }
      // The dental arch: the middle stands well ahead of the ends (a flat row would cut through the lips' corners).
      { const mid = (D.cols - 1) / 2, ahead = at(0, mid)[2] - Math.max(at(0, 0)[2], at(0, D.cols - 1)[2]);
        if (!lower) bow[lod].push(ahead);
        assert(ahead > .005, `${what}: the ${lower ? 'lower' : 'upper'} row's middle stands ahead of its ends (${(ahead * 1000).toFixed(1)} mm)`); }
      // Behind every point of the edge, by the least it may be: the row between two of its points is a chord, further back still.
      for (const q of rim) {
        const t = (q[0] - at(0, 0)[0]) / (at(0, D.cols - 1)[0] - at(0, 0)[0]) * (D.cols - 1), c = Math.min(D.cols - 2, Math.max(0, Math.floor(t)));
        const z = at(0, c)[2] + (at(0, c + 1)[2] - at(0, c)[2]) * (t - c);
        assert(z <= q[2] - D.back_m - (lower ? D.bite_m : 0) + 1e-6, `${what}: the ${lower ? 'lower' : 'upper'} row stands behind the lips' edge (${((q[2] - z) * 1000).toFixed(2)} mm)`);
        assert(z > q[2] - .02, `${what}: and not far behind it (${((q[2] - z) * 1000).toFixed(2)} mm)`);
      }
      // Its place on the map lies outside it, and reads back as the skin's shader reads it.
      for (let r = 0; r < 2; r++) for (let c = 0; c < D.cols; c++) {
        const u = strip.uv[2 * (r * D.cols + c)], w = strip.uv[2 * (r * D.cols + c) + 1];
        assert(u >= D.u0 && w >= D.v0, 'outside the map');
        for (const x of [u, below(u), above(u)]) {
          const [set, tone, low, across, along] = read(x, w);
          assert.deepEqual([set, tone, low], [look.set, look.tone, lower], `${what}: its set, tone and row (u ${x})`);
          // (single precision: a place at u 17 is known to about two millionths)
          assert(Math.abs(across - c / (D.cols - 1)) < 1e-5, `how far across (${across} for ${c / (D.cols - 1)})`);
          assert(Math.abs(along - (lower ? 1 - r : r)) < 1e-5, 'and from gum to edge: the edge is the side toward the other lip');
        }
      }
    });
    assert(strips[1].strip.at[2] < strips[0].strip.at[2], `${what}: the upper teeth close over the lower`);
    // Each row by its own lip: at the middle the upper lip's edge stands over the lower lip's at
    // the near levels (the lips of a face at rest do not seal), and within a millimetre of it far off.
    { const mid = (D.cols - 1) / 2, yOf = (k, r) => strips[k].strip.at[3 * (r * D.cols + mid) + 1];
      const upperLip = yOf(0, 1) + look.upper + D.lip_m[0], lowerLip = yOf(1, 0) - look.lower - D.lip_m[1];
      parted[lod].push(upperLip - lowerLip);
      // (Each row is set by its own lip: were both set by one lip's edge, the two would be the same height.)
      assert(upperLip >= lowerLip + (lod < 2 ? .0005 : -.001) && upperLip - lowerLip < .006, `${what}: the lips' two edges at the middle (${((upperLip - lowerLip) * 1000).toFixed(2)} mm apart)`); }
    // As rows apart: of the body's own kind, on the head's bone and the jaw's.
    const bones = mesh.skeleton.bones, apart = teethGeometry(g, { metres, apart: true, strips: strips.map(s => ({ strip: s.strip, bone: bones.findIndex(b => b.name === s.bone) })) });
    assert(apart && apart.attributes.position.count === D.cols * 4 && apart.index.count === (D.cols - 1) * 12, `${what}: ${D.cols * 4} points, drawn apart`);
    assert.deepEqual(Object.keys(apart.attributes).sort(), Object.keys(g.attributes).sort());
    assert.deepEqual([bones[apart.attributes.skinIndex.getX(0)].name, bones[apart.attributes.skinIndex.getX(D.cols * 4 - 1)].name], ['head', 'jaw']);
    v.fromBufferAttribute(apart.attributes.position, 0).applyMatrix4(metres);
    assert(v.distanceTo(new THREE.Vector3(...strips[0].strip.at.subarray(0, 3))) < 2e-4, `${what}: kept in the body's own numbers, it stands where it was put (${v.toArray().map(x => x.toFixed(5))})`);
    // A body packs its place on the map into whole numbers of 0..1; the rows' own, outside the map, is kept whole.
    assert(g.attributes.uv.normalized && !(g.attributes.uv.array instanceof Float32Array), `${what}: the body's own place on the map is packed`);
    for (let j = 0; j < D.cols * 4; j++) {
      const s = strips[j < D.cols * 2 ? 0 : 1].strip, jj = j % (D.cols * 2);
      assert(Math.abs(apart.attributes.uv.getX(j) - s.uv[2 * jj]) < 1e-6 && Math.abs(apart.attributes.uv.getY(j) - s.uv[2 * jj + 1]) < 1e-6 && apart.attributes.uv.getX(j) >= D.u0, `${what}: the rows' place outside the map is kept`);
    }
    drawn++;
  }
  assert(drawn >= 35 * 4 - 3 && without === none.size, `${drawn} body levels with rows, ${without} without`);
  // What the record says of it (docs/LIBERTIES.md, L-everyone-teeth-3553).
  const span = list => [Math.min(...list), Math.max(...list)];
  assert.deepEqual(found.map(span), [[39, 39], [31, 39], [17, 23], [8, 13]], `how much of the lips' edge each level finds (${JSON.stringify(found.map(span))})`);
  assert(Math.min(...bow.flat()) > .005 && Math.min(...parted[0], ...parted[1]) > .0005, `rows bowed ${(Math.min(...bow.flat()) * 1000).toFixed(1)} mm at least; lips ${(Math.min(...parted[0], ...parted[1]) * 1000).toFixed(2)} mm apart at least, near`);
  // Too little of the edge, or a mouth of no human width: no rows. A made-up edge of eight
  // vertices (three of the upper lip's, two corners, three of the lower lip's), 5 cm across.
  { const made = (picks, wide = .05) => {
      const g = new THREE.BufferGeometry(), n = picks.length, pos = new Float32Array(n * 3), uv = new Float32Array(n * 2), last = LIP_RIM.length - 1;
      const us = picks.map(k => LIP_RIM[k][0]), ua = Math.min(...us), ub = Math.max(...us);
      picks.forEach((k, i) => {
        const upper = k <= LIP_ARCS.upper || k >= last - LIP_ARCS.upper, lower = k >= LIP_ARCS.lower[0] && k <= LIP_ARCS.lower[1];
        const x = ((LIP_RIM[k][0] - ua) / (ub - ua) - .5) * wide;   // `wide` from the first of them to the last
        pos.set([x, 1.5 + (upper ? .001 : lower ? -.001 : 0), .1 - 8 * x * x], i * 3); uv.set(LIP_RIM[k], i * 2);
      });
      g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
      return g; };
    const same = new THREE.Matrix4(), look = drawnLook({ id: 'made', age: 40 }), eight = [0, 5, 33, 12, 26, 16, 19, 22];
    assert.equal(eight.length, D.least);
    assert.equal(drawnTeeth(made(eight), { metres: same, look })?.length, 2, 'eight of the edge, of both lips, are enough');
    assert.equal(drawnTeeth(made(eight.slice(1)), { metres: same, look }), null, 'one fewer is too few');
    assert.equal(drawnTeeth(made(eight, D.wide_m[0] * .9), { metres: same, look }), null, 'a mouth too narrow to be one');
    assert.equal(drawnTeeth(made(eight, D.wide_m[1] * 1.1), { metres: same, look }), null, 'or too wide');
    assert.equal(drawnTeeth(made([0, 3, 5, 7, 31, 33, 35, 37, 12, 26]), { metres: same, look }), null, "none of the lower lip's own: no rows"); }
  // What has no lips' edge has no drawn teeth.
  assert.equal(drawnTeeth(ball(), { metres, look: drawnLook({}) }), null, 'a ball has no lips');
  assert.equal(drawnTeeth(null, { metres, look: drawnLook({}) }), null);
  assert.equal(lipRim(null).length, 0); }

console.log('human mouth OK: pictured teeth are a strip behind the lips and a face with a smile gives it; everyone else has drawn teeth behind their own lips and talks with their jaw');
