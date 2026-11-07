// SPDX-License-Identifier: GPL-3.0-or-later
// T-3414: strand-card hair, beards and whiskers (renderers/web/js/human-hair.js, the table in
// human-hair-styles.js) and the eyes' cornea (human-skin.js). It must: grow cards over a
// body's own cap, a few millimetres off it, skinned to the cap's bones so they move as it does,
// however the export is quantised; grow the same hair for the same person every time and
// another for another; grow none at the far levels; put facial hair where its region says;
// add no texture and splice its shader once at every anchor; cut strands above a hat put on
// later; read every person's row as sourced or reconstructed, for a person who exists; dome
// the iris and pupil; and be wired into humans.js's build.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
const hooks = registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const { dressHair, growHair, CARDS, headFrame, keepsHair } = await import(new URL('renderers/web/js/human-hair.js', here));
const { dressSpectacles, fitSpectacles, PEOPLE_SPECTACLES, spectaclesFor } = await import(new URL('renderers/web/js/human-spectacles.js', here));
const { HAIR_CUTS, FACIAL_HAIR, HAIR_COLOURS, PEOPLE_HAIR, ERA_DEFAULT, hairFor } = await import(new URL('renderers/web/js/human-hair-styles.js', here));
const { dressSkin, domeCornea } = await import(new URL('renderers/web/js/human-skin.js', here));

// A synthetic head on the contract's bones: a cap (the top of a sphere) and a skin (all of
// it), both quantised as the exports are, the unit folded into the inverse bind matrices.
const C = new THREE.Vector3(0, 1.66, .02), FACE = new THREE.Vector3(0, 1.62, .06), R_HEAD = .095, UNIT = .9;
function figure() {
  const root = new THREE.Group(); root.position.set(30, 1, -12);
  const names = ['root', 'head', 'jaw', 'eye_l', 'eye_r'];
  const at = { root: [0, 0, 0], head: [0, 1.6, .03], jaw: [0, 1.61, .045], eye_l: [.03, 1.64, .114], eye_r: [-.03, 1.64, .114] };
  const bones = names.map(n => Object.assign(new THREE.Bone(), { name: n }));
  for (const b of bones.slice(1)) bones[0].add(b);
  for (const b of bones) { b.position.fromArray(at[b.name]); if (b !== bones[0]) b.position.sub(bones[0].position); }
  root.add(bones[0]); root.updateMatrixWorld(true);
  const toRoot = new THREE.Matrix4().copy(root.matrixWorld);
  // geometry space q -> metres: x = q * UNIT; bone i's inverse bind maps it into the bone's frame.
  const unit = new THREE.Matrix4().makeScale(UNIT, UNIT, UNIT);
  const inverses = bones.map(b => new THREE.Matrix4().copy(b.matrixWorld).invert().multiply(toRoot).multiply(unit));
  const skeleton = new THREE.Skeleton(bones, inverses);
  const sphere = (keep, material, centre = C) => {
    const g = new THREE.SphereGeometry(R_HEAD, 48, 32);
    const pos = g.attributes.position, nor = g.attributes.normal, joints = [], weights = [], q = [];
    for (let i = 0; i < pos.count; i++) {
      const p = new THREE.Vector3().fromBufferAttribute(pos, i).add(centre);
      q.push(p.x / UNIT, p.y / UNIT, p.z / UNIT);
      joints.push(1, 0, 0, 0); weights.push(1, 0, 0, 0);
    }
    g.setAttribute('position', new THREE.Float32BufferAttribute(q, 3));
    g.setAttribute('normal', nor);
    g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(joints, 4));
    g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(weights, 4));
    if (keep) {   // the cap: triangles above the brow line only
      const idx = g.index.array, kept = [];
      for (let t = 0; t < idx.length; t += 3) {
        const ys = [idx[t], idx[t + 1], idx[t + 2]].map(i => pos.getY(i));
        if (Math.min(...ys) > .01) kept.push(idx[t], idx[t + 1], idx[t + 2]);
      }
      g.setIndex(kept);
    }
    const m = new THREE.SkinnedMesh(g, new THREE.MeshStandardMaterial({ name: material }));
    root.add(m);
    m.bind(skeleton, new THREE.Matrix4());
    return m;
  };
  const cap = sphere(true, 'hair__makehuman_short04');
  cap.material.alphaTest = .4;
  const skin = sphere(false, 'skin', FACE);   // the face sits forward of the cap's sphere
  root.updateMatrixWorld(true);
  return { root, cap, skin, skeleton };
}

// 1. The cards lie over the cap, a few millimetres off it, and are skinned exactly as the cap.
{
  const { root, cap } = figure();
  const style = PEOPLE_HAIR.pa1904_otis_f_r_c1900_hans_johnson;
  const g = growHair({ hair: cap, skin: null, root, style: { ...style, facial: [] }, lod: 0, seed: 'a' });
  assert(g && g.grown.scalp > 100, `cards grown: ${g?.grown.scalp}`);
  assert(g.grown.scalp <= CARDS.lods[0].scalp);
  const n = g.position.length / 3;
  assert.equal(g.normal.length, 3 * n); assert.equal(g.strand.length, 3 * n); assert.equal(g.card.length, 4 * n);
  assert(g.index.every(i => i >= 0 && i < n), 'indices in range');
  let off = [Infinity, -Infinity];
  for (let i = 0; i < n; i++) {
    const d = Math.hypot(g.position[3 * i] - C.x, g.position[3 * i + 1] - C.y, g.position[3 * i + 2] - C.z) - R_HEAD;
    off = [Math.min(off[0], d), Math.max(off[1], d)];
  }
  // Chords of a curved scalp dip a little inside; a lifted tip stands a few millimetres out.
  assert(off[0] > -.004 && off[1] < .012, `cards hug the cap: ${off.map(x => (x * 1000).toFixed(1)).join('..')} mm`);
  for (let i = 0; i < n; i++) assert.equal(g.skinIndex[4 * i], 1, 'skinned to the head as the cap is');
  // Same person, same hair; another person, other hair.
  const again = growHair({ hair: cap, root, style: { ...style, facial: [] }, lod: 0, seed: 'a' });
  assert.deepEqual(again.position, g.position, 'seeded: the same every load');
  const other = growHair({ hair: cap, root, style: { ...style, facial: [] }, lod: 0, seed: 'b' });
  assert.notDeepEqual(other.position.slice(0, 30), g.position.slice(0, 30), 'another person, another head of hair');
  const near1 = growHair({ hair: cap, root, style: { ...style, facial: [] }, lod: 1, seed: 'a' });
  assert(near1.position.length < g.position.length, 'LOD1 grows less than LOD0');
  assert.equal(growHair({ hair: cap, root, style, lod: 2, seed: 'a' }), null, 'LOD2 grows none');
}

// 2. dressHair: one skinned sibling of the cap, no texture, its card vertices skinned to the
//    same world points the cap's own would be, the cap made solid beneath them.
{
  const { root, cap, skin, skeleton } = figure();
  // Hans is clean-shaven; a moustache is grown here through a style of the same table.
  const done = dressHair(root, { lod: 0, person: 'pa1904_otis_f_r_c1900_hans_johnson', year: 1904, style: { ...PEOPLE_HAIR.pa1904_otis_f_r_c1900_hans_johnson, facial: ['moustache'] } });
  assert(done?.mesh?.isSkinnedMesh, 'a skinned card mesh');
  const mesh = done.mesh;
  assert.equal(mesh.parent, cap.parent, 'beside the cap');
  assert.equal(mesh.skeleton, cap.skeleton, 'on the cap\'s own skeleton');
  assert.equal(mesh.castShadow, false);
  assert.equal(mesh.material.map, null, 'no texture');
  assert.equal(mesh.material.name, 'hair_cards');
  assert.equal(cap.material.alphaTest, CARDS.cap_alpha_test, 'the cap is solid beneath the cards');
  assert(done.grown.facial.moustache > 0, 'a moustache is grown');
  // Pose the head; a card vertex moves exactly as a cap point there would.
  skeleton.bones[1].rotation.set(.3, -.4, .1); root.updateMatrixWorld(true); skeleton.update();
  const pos = mesh.geometry.attributes.position, v = new THREE.Vector3();
  for (const i of [0, Math.floor(pos.count / 2), pos.count - 1]) {
    const metric = v.fromBufferAttribute(pos, i).clone();
    const card = mesh.applyBoneTransform(i, v.clone()).applyMatrix4(mesh.matrixWorld);
    // The cap's geometry for that metric point is metric / UNIT; skin it as the cap would be.
    const q = metric.clone().sub(new THREE.Vector3()).divideScalar(UNIT);
    const capWorld = q.applyMatrix4(cap.bindMatrix).applyMatrix4(new THREE.Matrix4().multiplyMatrices(skeleton.bones[1].matrixWorld, skeleton.boneInverses[1]));
    assert(card.distanceTo(capWorld) < 1e-5, `card vertex ${i} skins with the cap: ${card.distanceTo(capWorld)}`);
  }
  // The moustache sits below the eyes, in front, within its region (and the length it falls).
  const f = headFrame(cap, root), r = FACIAL_HAIR.moustache.region_cm;
  const cards = mesh.geometry.attributes.chiCard;
  let roots = 0;
  for (let i = 0; i < pos.count; i++) {
    if (cards.getY(i) !== 0) continue;
    const l = v.fromBufferAttribute(pos, i).clone().sub(f.o);
    const y = l.dot(f.y) * 100, z = l.dot(f.z) * 100;
    if (z > 1 && y < -3) { roots++; assert(y > r.y[0] - 1 && y < r.y[1] + 1, `a moustache root at ${y.toFixed(2)} cm`); }
  }
  assert(roots > 0, 'moustache roots found in front of the face');
  // Shader: spliced once at each anchor, a key of its own, under any prior hook.
  const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader, fragmentShader: THREE.ShaderLib.standard.fragmentShader };
  mesh.material.onBeforeCompile(shader, null);
  for (const marker of ['if ( vChiSkinP.y > chiCards.z ) discard;', 'void chiHairDirect(', 'normal = normalize( normal * faceDirection );', 'float tipAt = 1.0 - h * 0.45;'])
    assert.equal(shader.fragmentShader.split(marker).length, 2, `once: ${marker}`);
  assert(shader.vertexShader.includes('attribute vec3 chiStrandT;') && shader.vertexShader.includes('tObj = ( skinMatrix * vec4( tObj, 0.0 ) ).xyz;'));
  assert.deepEqual(Object.keys(shader.uniforms).sort(), ['chiCards', 'chiHair', 'chiSkinRest']);
  assert.equal(mesh.material.customProgramCacheKey(), '|chicago-strands-v1');
  // A hat put on later: strands above its band are cut; taken off, none are.
  skeleton.bones[1].rotation.set(0, 0, 0); root.updateMatrixWorld(true);
  const hatGeo = new THREE.CylinderGeometry(.1, .1, .15, 24, 1, true);
  hatGeo.translate(C.x, 1.69 + .075, C.z);
  hatGeo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Array(hatGeo.attributes.position.count * 4).fill(0).map((_, k) => (k % 4 === 0 ? 1 : 0)), 4));
  hatGeo.setAttribute('skinWeight', new THREE.Float32BufferAttribute(new Array(hatGeo.attributes.position.count * 4).fill(0).map((_, k) => (k % 4 === 0 ? 1 : 0)), 4));
  const hatBones = skeleton.bones, hatInv = hatBones.map(b => new THREE.Matrix4().copy(b.matrixWorld).invert());
  const hat = new THREE.SkinnedMesh(hatGeo, new THREE.MeshStandardMaterial({ name: 'headwear__silk_top_hat' }));
  hat.name = 'livery:top_hat';
  cap.parent.add(hat); hat.bind(new THREE.Skeleton(hatBones, hatInv), new THREE.Matrix4().copy(root.matrixWorld));   // its own binds, in metres from the root, as a livery file
  for (let k = 0; k < 30; k++) mesh.onBeforeRender();
  mesh.onBeforeRender();
  const band = mesh.material.userData.chiCards.value.z;
  assert(Math.abs(band - 1.69) < 1e-3, `the hat's band cuts the strands at 1.69 m: ${band}`);
  hat.removeFromParent();
  for (let k = 0; k < 31; k++) mesh.onBeforeRender();
  assert(mesh.material.userData.chiCards.value.z > 100, 'no hat, no cut');
  // The far levels keep the cap alone.
  assert.equal(dressHair(figure().root, { lod: 2, person: 'pa1904_otis_f_r_c1900_hans_johnson', year: 1904 }), null);
}

// 3. The table: every row's cut, pieces and colour exist; every choice is graded and said why;
//    every person named is a person of that year.
const people = {};
for (const year of [1835, 1904]) {
  const doc = JSON.parse(await fs.readFile(new URL(`data/sidecars/${year}/people.json`, here), 'utf8'));
  for (const p of doc.people ?? doc) people[p.id] = year;
}
for (const [id, row] of Object.entries(PEOPLE_HAIR)) {
  assert(HAIR_CUTS[row.cut], `${id}: cut ${row.cut}`);
  assert(HAIR_COLOURS[row.colour], `${id}: colour ${row.colour}`);
  for (const piece of row.facial) assert(FACIAL_HAIR[piece], `${id}: ${piece}`);
  assert(['reconstructed', 'inferred', 'attested'].includes(row.grade), `${id}: grade`);
  assert(row.grade === 'reconstructed' || row.source_id, `${id}: a sourced grade names its source`);
  assert(row.basis.length >= 60, `${id}: basis`);
  assert(people[id], `${id} is a person in the people sidecars`);
}
for (const [year, row] of Object.entries(ERA_DEFAULT)) assert(HAIR_CUTS[row.cut] && HAIR_COLOURS[row.colour], `era ${year}`);
assert.equal(hairFor('rc_bardwell_otis', 1835).cut, 'brushed_forward_1835');
assert.equal(hairFor('someone_else', 1904).cut, ERA_DEFAULT[1904].cut);
assert.equal(hairFor(null, 1600), null, 'no era, no hair grown');
// T-3452: the era defaults are men's cuts, so every woman a standing figure draws has her own
// row; and the 1812 private (anonymous, no person id) grows no strands under his felt cap,
// because no era cut is set for 1812 — the cleared short04 cap he was dressed over shows instead.
{
  const sexOf = JSON.parse(await fs.readFile(new URL('data/humans/variation/axes.json', here), 'utf8')).assets;
  for (const year of ['1812', '1835', '1904']) {
    let index;
    try { index = JSON.parse(await fs.readFile(new URL(`data/humans/instances/${year}/index.json`, here), 'utf8')); } catch { continue; }
    for (const id of index.instances) {
      const rec = JSON.parse(await fs.readFile(new URL(`data/humans/instances/${year}/${id}.json`, here), 'utf8'));
      if (sexOf[rec.appearance.asset_id]?.sex === 'female') assert(rec.person_id && PEOPLE_HAIR[rec.person_id], `${id}: a woman drawn in the town has her own hair row`);
    }
  }
}
assert.equal(hairFor(null, 1812), null, 'the 1812 private grows no strand hair under his cap');

// 4. Eyes: the iris and pupil take a cornea's dome, each eye about its own disc, once.
{
  const g = new THREE.BufferGeometry(), p = [], n = [];
  for (const side of [-1, 1]) for (let k = 0; k < 12; k++) {
    const a = k / 12 * Math.PI * 2, r = k % 2 ? .006 : .002;
    p.push(side * .03 + Math.cos(a) * r, 1.64 + Math.sin(a) * r, .125); n.push(0, 0, 1);
  }
  g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(n, 3));
  const iris = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ name: 'eyes__iris', roughness: .4 }));
  const root = new THREE.Group(); root.add(iris);
  assert(domeCornea(iris, root), 'domed');
  assert(!domeCornea(iris, root), 'once per geometry');
  const nn = g.attributes.normal;
  for (let i = 0; i < nn.count; i++) {
    const px = g.attributes.position.getX(i) - Math.sign(g.attributes.position.getX(i)) * .03, py = g.attributes.position.getY(i) - 1.64;
    const r = Math.hypot(px, py), tilt = Math.hypot(nn.getX(i), nn.getY(i));
    assert(nn.getZ(i) > .5, 'still facing out');
    if (r > .004) assert(tilt > .4 && (nn.getX(i) * px + nn.getY(i) * py) > 0, `the rim tilts outward: ${tilt}`);
  }
  dressSkin(root);
  assert(iris.material.roughness <= .1 && iris.material.envMapIntensity > 1, 'the cornea is glossy and mirrors the sky');
}

// 4b. A worn-up bun shares the cap's material and comes first in the file (T-3423): the
//     strands still grow from the scalp cap, the largest hair mesh, never from the bun.
{
  const { root, cap } = figure();
  const bunGeom = new THREE.SphereGeometry(.035, 8, 6);
  const n = bunGeom.attributes.position.count;
  bunGeom.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Array(4 * n).fill(0).map((_, i) => (i % 4 ? 0 : 1)), 4));
  bunGeom.setAttribute('skinWeight', new THREE.Float32BufferAttribute(new Array(4 * n).fill(0).map((_, i) => (i % 4 ? 0 : 1)), 4));
  const bun = new THREE.SkinnedMesh(bunGeom, new THREE.MeshStandardMaterial({ name: 'hair__makehuman_short04' }));
  cap.parent.add(bun); cap.parent.children.splice(cap.parent.children.indexOf(bun), 1); cap.parent.children.unshift(bun);
  bun.bind(cap.skeleton, new THREE.Matrix4());
  const mary = dressHair(root, { lod: 0, person: 'rc_flynn_mary', year: 1835 });
  assert(mary?.grown.scalp > 100, 'Mary\'s hair grows over her cap');
  assert.equal(mary.mesh.skeleton, cap.skeleton);
  assert.equal(cap.material.alphaTest, CARDS.cap_alpha_test, 'the cap, not the bun, is made solid beneath the cards');
  assert.equal(hairFor('rc_flynn_mary', 1835).cut, 'centre_part_knot_1835', 'a woman\'s cut, not the era\'s man\'s');
}

// 4c. A cap that is a cleared woman's hairstyle with its own strands (Mattie's bun, T-3434)
//     grows no scalp cards, keeps its own alpha cut, and still grows brows and lashes.
{
  const { root, cap } = figure();
  const before = cap.material.alphaTest;
  const mattie = dressHair(root, { lod: 0, person: 'glessner_williamson_martha_l', year: 1904 });
  assert.equal(hairFor('glessner_williamson_martha_l', 1904).cut, 'drawn_back_bun_1904');
  assert.equal(HAIR_CUTS.drawn_back_bun_1904.scalp_cards, false);
  assert(mattie === null || mattie.grown.scalp === 0, `no scalp cards over her bun: ${mattie?.grown.scalp}`);
  assert.equal(cap.material.alphaTest, before, 'her cap keeps its own alpha cut');
  assert(FACIAL_HAIR.lashes_upper && hairFor('rc_flynn_mary', 1835).facial.includes('lashes_upper'), 'both women grow lashes');
  // T-3456 (owner: brows "super clumpy bunchy"): the fine brow is rooted point by point and
  // evenly spaced, its hairs rising at the nose and falling at the tail.
  const brow = FACIAL_HAIR.brows_fine;
  assert(brow.exact && brow.even > 0, 'fine brows are rooted point by point, evenly');
  assert(brow.fall_ends[0] < 0 && brow.fall_ends[1] > 0, 'fine brow hairs rise at the nose, fall at the tail');
}

// 4d. A bald crown (T-3440, Glessner): cards root only below the bald line, the cap (a full
//     head of hair in its texture) is never drawn, near or far, and an undercoat in the hair's
//     colour lies on the cap's own triangles where the fringe grows, skinned with the cap.
{
  // A cap that comes down the sides and back, as a real one does, below the bald line.
  const lowCap = () => {
    const fig = figure(), g = fig.cap.geometry, pos = g.attributes.position, kept = [];
    const full = new THREE.SphereGeometry(R_HEAD, 48, 32).index.array;
    for (let t = 0; t < full.length; t += 3) {
      const ys = [full[t], full[t + 1], full[t + 2]].map(i => pos.getY(i) * UNIT - C.y), zs = [full[t], full[t + 1], full[t + 2]].map(i => pos.getZ(i) * UNIT - C.z);
      if (Math.min(...ys) > -.06 && Math.max(...zs) < .06) kept.push(full[t], full[t + 1], full[t + 2]);
    }
    g.setIndex(kept);
    return fig;
  };
  const { root, cap, skin } = lowCap();
  const row = hairFor('glessner_john_j', 1904), cut = HAIR_CUTS[row.cut];
  assert(cut.bald && row.grade === 'attested' && row.source_id, 'his fringe is read from his portrait');
  const g = growHair({ hair: cap, skin, root, style: { ...row, facial: [] }, lod: 0, seed: 'glessner_john_j' });
  assert(g.grown.scalp > 100, `a fringe grows: ${g.grown.scalp}`);
  const f = headFrame(cap, root), v = new THREE.Vector3();
  // Every card's root (its first two vertices) is on the fringe.
  for (let i = 0; i < g.card.length / 4; i++) {
    if (g.card[4 * i + 1] !== 0) continue;
    assert(keepsHair(cut, f, v.fromArray(g.position, 3 * i).addScaledVector(f.y, -.003)), 'no card roots on the bald crown');
  }
  assert(g.undercoat?.length > 30, 'an undercoat where the fringe grows');
  for (const i of g.undercoat) assert(!g.scalp.bare?.[i], 'the undercoat is never on the bald crown');
  const done = dressHair(root, { lod: 0, person: 'glessner_john_j', year: 1904 });
  assert(done && cap.visible === false, 'the cap is not drawn over a bald crown');
  const under = cap.parent.children.find(o => o.name === 'hair_undercoat');
  assert(under?.isSkinnedMesh && under.skeleton === cap.skeleton && !under.material.map, 'the undercoat is skinned with the cap, no texture');
  const far = lowCap();
  assert.equal(dressHair(far.root, { lod: 2, person: 'glessner_john_j', year: 1904 }), null);
  assert.equal(far.cap.visible, false, 'far off, the head reads bare, not capped in dark hair');
  for (const piece of row.facial) assert(FACIAL_HAIR[piece], piece);
}

// 4e. Spectacles (T-3440): only for a person whose portrait shows them, with its source;
//     round rims centred in front of each eye, a bridge, temples back to the ears, all skinned
//     to the head bone; none at the far levels.
{
  for (const [id, sp] of Object.entries(PEOPLE_SPECTACLES)) {
    assert(sp.grade === 'attested' && sp.sources.length && sp.basis.length >= 60, `${id}: spectacles sourced`);
    assert(people[id], `${id} is a person`);
  }
  assert.equal(spectaclesFor('pa1904_otis_f_r_c1900_hans_johnson'), null);
  const { root, skin } = figure();
  const fit = fitSpectacles(skin, root, PEOPLE_SPECTACLES.glessner_john_j);
  assert(fit, 'fitted');
  const f = fit.frame, P = fit.lens.position;
  // The two lens centres: in front of the eyes, one either side of the nose.
  const c1 = new THREE.Vector3().fromArray(P, 0), c2 = new THREE.Vector3().fromArray(P, 3 * (P.length / 6));
  for (const c of [c1, c2]) {
    const l = c.clone().sub(f.o);
    assert(l.dot(f.z) > .005 && Math.abs(l.dot(f.y)) < .01, `a lens in front of an eye: ${l.toArray().map(x => x.toFixed(3))}`);
  }
  assert(Math.sign(c1.clone().sub(f.o).dot(f.x)) !== Math.sign(c2.clone().sub(f.o).dot(f.x)), 'one lens either side');
  const done = dressSpectacles(root, { lod: 0, person: 'glessner_john_j' });
  assert.equal(done?.meshes.length, 2, 'wire and lenses');
  const head = skin.skeleton.bones.findIndex(b => b.name === 'head');
  for (const m of done.meshes) {
    assert(m.isSkinnedMesh && m.skeleton === skin.skeleton, 'skinned to the face\'s skeleton');
    const si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight;
    for (let i = 0; i < si.count; i++) assert(si.getX(i) === head && sw.getX(i) === 1, 'wholly on the head bone');
  }
  assert.equal(dressSpectacles(figure().root, { lod: 2, person: 'glessner_john_j' }), null, 'none far off');
  assert.equal(dressSpectacles(figure().root, { lod: 0, person: 'rc_flynn_mary' }), null, 'none for someone without');
}

// 5. Every person: humans.js grows each near body's hair after it measures its height.
const humans = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
assert(/import \{ dressHair \} from '\.\/human-hair\.js';/.test(humans));
assert(/this\.proxy\.scale\.y = [^\n]*\n[\s\S]{0,400}dressHair\(scene, \{ lod,/.test(humans), 'build() grows the hair, after the height is measured');
assert(/dressHair\(scene[^\n]*\n[\s\S]{0,200}dressSpectacles\(scene, \{ lod,/.test(humans), 'build() puts on spectacles after the hair (T-3440)');
// Liberty: the hair supplement under L418 names this ticket.
const liberties = await fs.readFile(new URL('docs/LIBERTIES.md', here), 'utf8');
assert(/\*\*Strand hair, beards and eyes \(2026-11-06, T-3414\):\*\*/.test(liberties), 'L418 carries the hair supplement');
hooks.deregister();
console.log('human-hair: cards hug the cap and skin with it, seeded per person, near levels only, facial hair in its region, no texture, spliced once, cut under a hat, table graded, cornea domed, bald crown and spectacles (T-3440), every body: PASS');
