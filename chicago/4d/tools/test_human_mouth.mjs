// SPDX-License-Identifier: GPL-3.0-or-later
// T-3553: a mouth that opens (renderers/web/js/human-mouth.js). The teeth: a record's strip is
// read or refused; it is added to a skin's geometry as rows of its own after the source's, where
// the record puts them, coloured from where the record says, carried whole by one bone, facing
// out of the mouth, left alone by every morph target; the source is never changed; and what
// was made is kept once for a sheet and freed with its source. The mouth's play: a face with the
// smile gives it to a visitor near in front and with a greeting, eases in and out, keeps part of
// it talking while the jaw runs in syllables, the same run for the same person; a voice takes
// the jaw; the next level's mouth carries on from the last; and a face without the smile, or a
// jaw its expression holds, is never written.
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const { teethStrip, teethGeometry, teethOf, createMouth, MOUTH } = await import(new URL('renderers/web/js/human-mouth.js', here));
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

// Kept once for a source and a sheet; a geometry with its teeth is handed back; freed with its source.
{ const s = ball(), a = teethOf(s, 'sheet-a', { metres, strip, bone: 2 });
  assert(a.userData.chiTeeth && teethOf(s, 'sheet-a', { metres, strip, bone: 2 }) === a, 'the same sheet, the same geometry');
  assert(teethOf(s, 'sheet-b', { metres, strip, bone: 2 }) !== a, "another sheet's is its own");
  assert.equal(teethOf(a, 'sheet-a', { metres, strip, bone: 2 }), a, 'teeth are not added twice');
  assert.equal(teethOf(s, 'sheet-c', { metres, strip: null, bone: 2 }), s, 'with no strip the source is drawn as it is');
  assert.equal(teethOf(null, 'x', {}), null);
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
// A face without the smile is not played and never written: not its targets, not its jaw.
{ const f = face(['eyeBlinkLeft', 'jawOpen']), m = createMouth({ id: 'x', scene: f.scene });
  f.w[1] = .4;
  assert(!m.bound);
  run(m, 3, { facing: true, talk: 1, greeting: true });
  m.say(1).pose({ smile: 1, jaw: 9 });
  assert.deepEqual([f.w, f.deg()], [[0, .4], 0]); }

console.log('human mouth OK: the teeth are a strip of their own behind the lips, and a face with a smile gives it, keeps part of it talking and moves its jaw');
