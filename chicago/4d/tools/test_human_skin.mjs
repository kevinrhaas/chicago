// SPDX-License-Identifier: GPL-3.0-or-later
// T-3400: skin, hair and eyes for every portable human (renderers/web/js/human-skin.js).
// It must: dress exactly the skin, hair and eyes of every real export (never a garment
// or a shoe); add no texture; splice into three's own standard shader at every anchor it
// names, light wrapper included; chain beneath another hook (confidence.js) with a program
// key that names the chain; share one skin and one hair program across bodies; read each
// body's bind pose in metres however it was quantised; and be wired into humans.js's build.
// T-3553: the one texture it reads is a person's own skin sheet, as uniforms of that same
// program, on that person's material alone.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
// human-skin.js imports its sibling human-hair-styles.js (T-3493), so it is loaded from its own
// file with 'three' resolved to the vendored copy, not from a data: URL.
registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const { surfaceFor, dressSkin, restMatrix, SKIN, EYES, AGE, restingLid, likenessLayout, likenessSheetsReady, LIKENESS } = await import(new URL('renderers/web/js/human-skin.js', here));

const materialNames = async asset => {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.glb`, here));
  const n = bytes.readUInt32LE(12);
  return JSON.parse(bytes.subarray(20, 20 + n)).materials.map(m => m.name);
};
const exports = (await fs.readdir(new URL('assets/humans/web/', here))).filter(f => f.endsWith('.glb')).map(f => f.slice(0, -4));
assert(exports.some(a => a.startsWith('anonymous_working_driver_1904')) && exports.some(a => a.startsWith('bardwell_otis_1835')), 'Hans and Otis are exported');
for (const asset of exports) {
  const names = await materialNames(asset);
  const root = new THREE.Group();
  for (const name of names) root.add(new THREE.Mesh(new THREE.BufferGeometry(), Object.assign(new THREE.MeshStandardMaterial(), { name })));
  const dressed = dressSkin(root);
  const want = names.filter(n => /^(skin|hair|eyes)($|__)/.test(n)).sort();   // the pupil too, under its cornea (T-3414)
  assert.deepEqual(Object.keys(dressed).sort(), want, `${asset}: exactly its skin, hair and eyes`);
  assert(Object.values(dressed).includes('skin'), `${asset}: has skin`);
  root.traverse(o => { if (o.isMesh && !/^(skin|hair|eyes)/.test(o.material.name)) assert.equal(o.material.onBeforeCompile, THREE.Material.prototype.onBeforeCompile, `${o.material.name} untouched`); });
  console.log(`${asset}: ${Object.entries(dressed).map(([k, v]) => `${k}=${v}`).join(', ')}`);
}
for (const [name, surface] of [['skin', 'skin'], ['skin__dark', 'skin'], ['hair__makehuman_short04', 'hair'], ['eyes', 'eyes'], ['eyes__sclera', 'eyes'], ['eyes__iris', 'eyes'],
  ['eyes__pupil', 'eyes'], ['eyes__lash', null], ['garment_upper__shirt_linen', null], ['footwear__closed_leather_shoes', null], ['skinny_tie', null], ['', null]]) assert.equal(surfaceFor({ name }), surface, name);
assert.deepEqual(dressSkin(new THREE.Mesh(new THREE.BufferGeometry(), Object.assign(new THREE.MeshBasicMaterial(), { name: 'skin' }))), {}, 'an unlit material is left alone');

// Eyes: wet, the sclera less paper-white, once however often a body is dressed.
const sclera = Object.assign(new THREE.MeshStandardMaterial({ color: 0xd0c8b8, roughness: .38 }), { name: 'eyes__sclera' });
const eyeRoot = new THREE.Mesh(new THREE.BufferGeometry(), sclera);
const before = sclera.color.r;
dressSkin(eyeRoot); dressSkin(eyeRoot);
assert.equal(sclera.roughness, EYES.roughness);
assert.equal(sclera.customProgramCacheKey(), '|chicago-sclera-v1', 'the white is shaded toward its corners');
assert(Math.abs(sclera.color.r - before * EYES.sclera_value) < 1e-9, 'the sclera is toned once');

// The bind pose in metres: a quantised export folds its scale into the inverse bind matrices.
{
  const bone = new THREE.Bone(); bone.position.set(0, .9, 0);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute([0, -1, 0, 0, 1, 0, .1, 1, 0], 3));
  geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 4));
  geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0], 4));
  const mesh = new THREE.SkinnedMesh(geo, new THREE.MeshStandardMaterial());
  const root = new THREE.Group(); root.add(bone, mesh); root.position.set(40, 2, -7); root.updateMatrixWorld(true);
  // Positions span ±1 for a 1.7 m body: the inverse bind matrix carries the .85 m unit.
  // (three skins a vertex to bone.matrixWorld · inverse · bindMatrix · position).
  const inverse = new THREE.Matrix4().copy(bone.matrixWorld).invert().multiply(root.matrixWorld)
    .multiply(new THREE.Matrix4().makeScale(.85, .85, .85)).multiply(new THREE.Matrix4().makeTranslation(0, 1, 0))
    .multiply(new THREE.Matrix4().copy(mesh.matrixWorld).invert());
  mesh.bind(new THREE.Skeleton([bone], [inverse]), mesh.matrixWorld);
  const m = restMatrix(mesh, root);
  const foot = new THREE.Vector3(0, -1, 0).applyMatrix4(m), top = new THREE.Vector3(0, 1, 0).applyMatrix4(m);
  assert(Math.abs(foot.y) < 1e-6 && Math.abs(top.y - 1.7) < 1e-6, `rest pose in metres from the root: ${foot.y} → ${top.y}`);
}

// Splices into three's own standard shader, after a prior hook, and is idempotent.
const compile = material => {
  const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader, fragmentShader: THREE.ShaderLib.standard.fragmentShader };
  material.onBeforeCompile(shader, null);
  return shader;
};
const dressOne = (name, hook) => {
  const m = Object.assign(new THREE.MeshStandardMaterial(), { name });
  if (hook) { m.onBeforeCompile = hook; m.customProgramCacheKey = () => 'chicago4d-confidence'; }
  const root = new THREE.Mesh(new THREE.BufferGeometry(), m);
  root.geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 1.6, 0, .1, 1.8, 0, -.1, 1.7, .1], 3));
  dressSkin(root); dressSkin(root);
  return m;
};
let priorRan = 0;
const skin = dressOne('skin', shader => { priorRan++; shader.fragmentShader = '// prior\n' + shader.fragmentShader; });
const s = compile(skin);
assert.equal(priorRan, 1, 'the prior hook runs once, first');
assert(s.fragmentShader.includes('// prior'));
assert(THREE.ShaderChunk.lights_physical_pars_fragment.includes('void RE_Direct_Physical( const in IncidentLight directLight'), "three's direct-light signature is the one wrapped");
for (const marker of ['chiSkinH = ( - chiSkin.x * pore', 'roughnessFactor = clamp( min( roughnessFactor, chiSkinSheen.z ) - chiSkinSheen.x', 'chiSkinN0 = normal;',
  'void chiSkinDirect(', '#define RE_Direct chiSkinDirect', 'reflectedLight.indirectDiffuse += diffuseColor.rgb * chiSkinSheen.y']) {
  assert.equal(s.fragmentShader.split(marker).length, 2, `skin spliced once: ${marker}`);
}
// The wrapper must follow three's own definition, and the normal step the begin step.
assert(s.fragmentShader.indexOf('#include <lights_physical_pars_fragment>') < s.fragmentShader.indexOf('void chiSkinDirect('));
assert(s.vertexShader.includes('vChiSkinP = ( chiSkinRest * vec4( position, 1.0 ) ).xyz;'));
assert.deepEqual(Object.keys(s.uniforms).sort(), ['chiBrowTint', 'chiFace', 'chiFaceLook', 'chiFaceMarks', 'chiLike', 'chiLikeBack', 'chiLikeGrow', 'chiLikeHat', 'chiLikeMap', 'chiLikeMask',
  'chiLikeTint', 'chiLikeUv', 'chiSkin', 'chiSkinLipTone', 'chiSkinRest', 'chiSkinSheen']);
// T-3553 (Kevin, 2026-11-12: "when the sun is behind people their lips have a pink line too much"):
// lips found in the map's own colour (the complexion divided out) and turned partway to the skin's
// hue; the parting shaded in the light step. Every skin, every period: one program.
assert(SKIN.lip_tone > 0 && SKIN.lip_tone < 1, 'a lip keeps some of its own colour');
assert.equal(s.uniforms.chiSkinLipTone.value, SKIN.lip_tone);
for (const marker of ['vec3 tex = c / max( diffuse, vec3( 1e-3 ) );', 'chiSkinLip = smoothstep(', 'chiSkinLip * chiSkinLipTone',
  'chiSkinCrease = chiSkinLip * face', 'reflectedLight.indirectDiffuse *= shade;'])
  assert.equal(s.fragmentShader.split(marker).length, 2, `lips spliced once: ${marker}`);
assert(s.fragmentShader.indexOf('chiSkinLip = smoothstep(') < s.fragmentShader.indexOf('chiSkinCrease = chiSkinLip'), 'the lip is found before its parting is shaded');
// T-3493: a face's look is uniforms; a body with no face frame draws no age and no brow shade.
assert.deepEqual(s.uniforms.chiFaceLook.value.toArray(), [0, 0, 0, 0]);
for (const marker of ['float ageH = 0.0;', 'c = mix( c, c * chiBrowTint,', 'chiSkinH = ( - chiSkin.x * pore * 0.000035 - chiSkin.y * lines * 0.00002 + grain * 0.00007 ) * ( 1.0 - chiLikeHair ) + ageH;'])
  assert.equal(s.fragmentShader.split(marker).length, 2, `face look spliced once: ${marker}`);
assert.equal(restingLid(null), 0);
assert.equal(restingLid(AGE.lid_from), 0, 'no resting lid before its age');
assert(Math.abs(restingLid(AGE.lid_full) - AGE.lid_most) < 1e-9 && restingLid(99) === AGE.lid_most, 'full by its age, no further');
assert.deepEqual(s.uniforms.chiSkin.value.toArray(), [SKIN.pores, SKIN.lines, SKIN.mottle, SKIN.scatter]);
assert.equal(skin.customProgramCacheKey(), 'chicago4d-confidence|chicago-skin-v1', 'the key names the chain');
assert.equal(skin.map ?? null, null, 'no texture added');

const hair = dressOne('hair__makehuman_short04');
const h = compile(hair);
for (const marker of ['void chiHairDirect(', '#define RE_Direct chiHairDirect', 'roughnessFactor = max( roughnessFactor, chiHair.w );', 'chiHairTv = dot( t, t )']) {
  assert.equal(h.fragmentShader.split(marker).length, 2, `hair spliced once: ${marker}`);
}
// The strand runs with the skinned body: it is turned by skinMatrix, which three declares before begin_vertex.
assert(h.vertexShader.indexOf('#include <skinnormal_vertex>') < h.vertexShader.indexOf('tObj = ( skinMatrix * vec4( tObj, 0.0 ) ).xyz;'));
assert.deepEqual(Object.keys(h.uniforms).sort(), ['chiHair', 'chiHairCrown', 'chiSkinRest', 'chiSkinRestInv']);
assert.equal(hair.customProgramCacheKey(), '|chicago-hair-v1');

// Bodies differ by uniforms, never code: one skin program for two bodies.
const a = compile(dressOne('skin')), b = compile(dressOne('skin__other'));
assert.equal(a.vertexShader + a.fragmentShader, b.vertexShader + b.fragmentShader, 'one skin program text');

// T-3553: a person's own skin sheet (tools/bake_likeness_skin.py). Its layout is uniforms of
// the one skin program; a body with none reads no sheet; and a person who wears one never
// puts it on the material their body's export shares with everyone else.
{
  assert.equal(s.uniforms.chiLike.value, null, 'a plain skin reads no sheet');
  assert.equal(s.uniforms.chiLikeMask.value.w, 0, 'a plain skin wears no sheet');
  for (const r of s.uniforms.chiLikeUv.value) assert(r.x > r.z && r.y > r.w, 'a plain skin\'s rects are empty');
  for (const marker of ['if ( chiLikeMask.w > 0.5 ) {', 'c = mix( c / max( diffuse, vec3( 1e-3 ) ) * chiLikeTint.rgb, like, a );', 'ageH *= 1.0 - a;'])
    assert.equal(s.fragmentShader.split(marker).length, 2, `likeness spliced once: ${marker}`);
  assert(s.fragmentShader.indexOf('ageH *= 1.0 - a;') < s.fragmentShader.indexOf('chiSkinH = ( - chiSkin.x * pore'), 'the drawn age lines give way before the relief is summed');
  assert(s.fragmentShader.indexOf('c = mix( c, c * chiBrowTint,') < s.fragmentShader.indexOf('if ( chiLikeMask.w > 0.5 ) {'), 'the pictures are laid over the drawn face, not under it');
  const sheet = { url: 'http://example.invalid/likeness/p_skin.jpg', size_px: [768, 1024],
    rects: [{ uv: [0.635, 0.175, 1.0, 0.86], px: [0, 0, 512, 1024] }, { uv: [0.24, 0.02, 0.52, 0.14], px: [520, 170, 768, 276] }],
    mask: { px: [528, 520], scale: 0.25 }, tint: [0.64, 0.67, 0.94], gain: 1.1 };
  const lay = likenessLayout(sheet);
  // A rect's corners land on its pixels: uv * scale + offset, as the shader reads it.
  lay.uv.forEach(([u0, v0, u1, v1], k) => {
    const [sx, sy, ox, oy] = lay.map[k], [x0, y0, x1, y1] = sheet.rects[k].px;
    for (const [u, v, x, y] of [[u0, v0, x0, y0], [u1, v1, x1, y1]]) assert(Math.abs(u * sx + ox - x / 768) < 1e-9 && Math.abs(v * sy + oy - y / 1024) < 1e-9, `rect ${k} corner`);
  });
  assert.deepEqual(lay.mask, [528 / 768, 520 / 1024, 0.25, 1]);
  assert.deepEqual(lay.tint, [0.64, 0.67, 0.94, 1.1]);
  // A sheet with no hair of its own to stand out, and no eyes: none of either.
  assert.deepEqual(lay.grow, [0, 0, 0, 0]);
  assert.deepEqual(lay.facing, [0, 0]);
  assert.equal(lay.eyes, null);
  assert.equal(s.uniforms.chiLikeGrow.value.w, 0, 'a plain skin grows nothing');
  assert(s.uniforms.chiLikeHat.value.x > 1e5, 'and is under no hat');
  // The hair that stands out from the skin (T-3553): the vertex step moves the skin out along
  // the line from the head's middle by the mask's red, never past the hat's band; the fragment
  // step lights it by the sheet's own facing and takes the pores, oil and scatter off it.
  for (const marker of ['if ( chiLikeGrow.w > 0.0 ) {', 'textureLod( chiLike, chiLikeMask.xy + st * chiLikeMask.z, 0.0 ).r * chiLikeGrow.w',
    'stand = min( stand, mix( 1.0, chiLikeHat.y, smoothstep( chiLikeHat.x - 0.02, chiLikeHat.x, vChiSkinP.y ) ) );', 'transformed += chiLikeBack * ( away * ( stand / max( length( away ), 1e-5 ) ) );'])
    assert.equal(s.vertexShader.split(marker).length, 2, `grown hair spliced once: ${marker}`);
  for (const marker of ['chiLikeHair = a * mask.b;', 'chiLikeStand = a * mask.r * chiLikeGrow.w;', 'roughnessFactor = mix( roughnessFactor, max( roughnessFactor, 0.8 ), chiLikeHair );'])
    assert.equal(s.fragmentShader.split(marker).length, 2, `grown hair spliced once: ${marker}`);
  const grownSheet = { ...sheet, grow: { reach_m: 0.05, from_m: [0, 1.64, 0.03], normal_px: [528, 566] },
    eyes: { px: [528, 838], size: 96, white_srgb: [0.42, 0.36, 0.34] } };
  const grownLay = likenessLayout(grownSheet);
  assert.deepEqual(grownLay.grow, [0, 1.64, 0.03, 0.05]);
  assert.deepEqual(grownLay.facing, [528 / 768, 566 / 1024]);
  assert.deepEqual(grownLay.eyes, { rect: [528 / 768, 838 / 1024, 192 / 768, 96 / 1024], white: [0.42, 0.36, 0.34] });
  for (const bad of [{ reach_m: 0, from_m: [0, 1, 0], normal_px: [1, 1] }, { reach_m: 0.05, from_m: [0, 1], normal_px: [1, 1] }, { reach_m: 0.05, from_m: [0, 1, 0] }])
    assert.deepEqual(likenessLayout({ ...sheet, grow: bad }).grow, [0, 0, 0, 0], 'a grow block that does not parse grows nothing');
  for (const bad of [{ px: [1, 1], size: 0, white_srgb: [1, 1, 1] }, { px: [1], size: 96, white_srgb: [1, 1, 1] }, { px: [1, 1], size: 96, white_srgb: [1, 1] }])
    assert.equal(likenessLayout({ ...sheet, eyes: bad }).eyes, null, 'an eyes block that does not parse is none');
  for (const bad of [null, {}, { ...sheet, url: '' }, { ...sheet, rects: [] }, { ...sheet, rects: Array(LIKENESS.rects + 1).fill(sheet.rects[0]) },
    { ...sheet, rects: [{ uv: [1, 0, 0, 1], px: [0, 0, 1, 1] }] }, { ...sheet, mask: null }]) assert.equal(likenessLayout(bad), null, 'a sheet that does not parse is no sheet');
  // Two bodies of one export share its skin material; the second wears a sheet.
  const body = (shared, like) => {
    const bone = new THREE.Bone();
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute([0, 1.6, 0, .1, 1.8, 0, -.1, 1.7, .1], 3));
    geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Array(12).fill(0), 4));
    geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0], 4));
    const mesh = new THREE.SkinnedMesh(geo, shared);
    const root = new THREE.Group(); root.add(bone, mesh); root.updateMatrixWorld(true);
    mesh.bind(new THREE.Skeleton([bone]), mesh.matrixWorld);
    if (like) root.userData.chiLikenessSkin = like;
    dressSkin(root); dressSkin(root);
    return mesh;
  };
  const shared = Object.assign(new THREE.MeshStandardMaterial(), { name: 'skin' });
  const plain = body(shared, null), pictured = body(shared, sheet), again = body(shared, sheet), other = body(shared, { ...sheet, url: sheet.url + '?2' });
  assert.equal(plain.material, shared, 'the first wearer keeps the shared material');
  assert.notEqual(pictured.material, shared, 'a pictured person takes a twin');
  assert.equal(again.material, pictured.material, 'and the same twin at every rebuild');
  assert.notEqual(other.material, pictured.material, 'another sheet is another twin');
  const ps = compile(shared), ls = compile(pictured.material);
  assert.equal(ps.uniforms.chiLikeMask.value.w, 0, 'the shared material wears no sheet');
  assert.equal(ls.uniforms.chiLikeMask.value.w, 1, 'the twin wears it');
  assert.deepEqual(ls.uniforms.chiLikeTint.value.toArray(), [0.64, 0.67, 0.94, 1.1]);
  assert.deepEqual(ls.uniforms.chiLikeUv.value[0].toArray(), sheet.rects[0].uv);
  assert(ls.uniforms.chiLikeUv.value[2].x > ls.uniforms.chiLikeUv.value[2].z, 'a rect the sheet does not use is empty');
  assert.equal(ls.uniforms.chiLike.value, null, 'with no page there is no image to fetch');
  assert.equal(ps.vertexShader + ps.fragmentShader, ls.vertexShader + ls.fragmentShader, 'one skin program text, pictured or not');
  assert.equal(pictured.material.customProgramCacheKey(), shared.customProgramCacheKey(), 'and one program key');
  assert.equal(pictured.material.map ?? null, null, 'the sheet is never the material\'s own map');
  // The pictured person is first to wear another shared material: the next, plain wearer takes a twin without it.
  const shared2 = Object.assign(new THREE.MeshStandardMaterial(), { name: 'skin' });
  const first = body(shared2, sheet), second = body(shared2, null);
  assert.equal(first.material, shared2);
  assert.notEqual(second.material, shared2, 'a plain wearer after a pictured one takes a twin');
  assert.equal(compile(second.material).uniforms.chiLikeMask.value.w, 0, 'which wears no sheet');
  // A pictured person whose sheet says how far its hair stands out: the twin's uniforms carry it.
  const tall = body(Object.assign(new THREE.MeshStandardMaterial(), { name: 'skin' }), null), grownBody = body(tall.material, grownSheet);
  const gs = compile(grownBody.material);
  assert.deepEqual(gs.uniforms.chiLikeGrow.value.toArray(), [0, 1.64, 0.03, 0.05]);
  assert.deepEqual(gs.uniforms.chiLikeHat.value.toArray().slice(1), [LIKENESS.under_hat_m, 528 / 768, 566 / 1024]);
  assert(gs.uniforms.chiLikeHat.value.x > 1e5, 'bareheaded until a hat is seen on it');
  assert.equal(typeof grownBody.onBeforeRender, 'function');
  // Its own eyes (T-3553): twins of the eyes' shared materials, the iris and the pupil reading
  // the sheet, the whites in the picture's colour; the shared ones stay everyone else's.
  {
    const eyes = like => {
      const root = new THREE.Group();
      const mats = Object.fromEntries(['sclera', 'iris', 'pupil'].map(k => [k, sharedEyes[k]]));
      for (const m of Object.values(mats)) root.add(new THREE.Mesh(new THREE.BufferGeometry(), m));
      if (like) root.userData.chiLikenessSkin = like;
      dressSkin(root); dressSkin(root);
      return Object.fromEntries(root.children.map(o => [o.material.name.split('__')[1], o.material]));
    };
    const sharedEyes = Object.fromEntries(['sclera', 'iris', 'pupil'].map(k => [k, Object.assign(new THREE.MeshStandardMaterial({ color: 0x808080 }), { name: `eyes__${k}` })]));
    const plainEyes = eyes(null), own = eyes(grownSheet), ownAgain = eyes(grownSheet), noEyes = eyes(sheet);
    for (const k of ['sclera', 'iris', 'pupil']) {
      assert.equal(plainEyes[k], sharedEyes[k], `${k}: a plain figure keeps the shared material`);
      assert.equal(noEyes[k], sharedEyes[k], `${k}: so does a sheet with no eyes on it`);
      assert.notEqual(own[k], sharedEyes[k], `${k}: a pictured figure takes a twin`);
      assert.equal(ownAgain[k], own[k], `${k}: the same twin at every rebuild`);
      assert.equal(own[k].name, `eyes__${k}`);
    }
    const lin = c => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
    for (const [k, c] of [['r', 0.42], ['g', 0.36], ['b', 0.34]]) assert(Math.abs(own.sclera.color[k] - lin(c) * 1.1) < 1e-6, 'the whites are the picture\'s colour, in the sheet\'s tone');
    assert.equal(own.sclera.customProgramCacheKey(), '|chicago-sclera-v1', 'shaded toward their corners as any');
    assert.equal(own.iris.envMapIntensity, EYES.like_sky, 'the cornea mirrors less sky over a picture');
    assert(EYES.like_sky < EYES.cornea_sky);
    assert(Math.abs(own.iris.color.r - 1.1) < 1e-9 && own.pupil.color.r === own.iris.color.r, 'the picture is the colour');
    assert.equal(own.iris.map ?? null, null, 'with no page there is no picture to read');
    assert.equal(sharedEyes.iris.envMapIntensity, EYES.cornea_sky);
  }
  await likenessSheetsReady();   // nothing is fetched here; it resolves at once
}

// T-3553: the lids of a face in its own skin rest as its front picture shows them. That much of
// the blink's own shape is the rest shape's, less what the face's age already rests them, and
// the face's blink targets keep only the rest of the way, so a full blink ends where it did.
{
  const { restedBlink } = await import(new URL('renderers/web/js/human-skin.js', here));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 1, 0, 0, 0, 1, 0], 3));
  geo.morphAttributes.position = [new THREE.Float32BufferAttribute([0, -1, 0, 0, 0, 0, 0, 0, 0], 3), new THREE.Float32BufferAttribute([0, 0, 0, 0, -2, 0, 0, 0, 0], 3),
    new THREE.Float32BufferAttribute([0, 0, 0, 0, 0, 0, 0, 0, 5], 3)];
  geo.morphTargetsRelative = true;
  const face = new THREE.Mesh(geo, new THREE.MeshStandardMaterial());
  face.morphTargetDictionary = { eyeBlinkLeft: 0, eyeBlinkRight: 1, jawOpen: 2 };
  assert.equal(restedBlink(face, face, 0, 30), null, 'no rest asked, none given');
  assert.equal(restedBlink(new THREE.Mesh(new THREE.BufferGeometry(), face.material), face, .3, 30), null, 'a body with no blink (a far level) rests nothing');
  assert.equal(restedBlink(face, face, restingLid(60), 60), null, 'a rest its age already gives adds nothing');
  const young = restedBlink(face, face, .25, 30);
  assert.equal(young.rest, .25);
  assert.deepEqual(young.targets, [geo.morphAttributes.position[0], geo.morphAttributes.position[1]], 'the blink\'s own two targets');
  assert.equal(young.morphAttributes.position[2], geo.morphAttributes.position[2], 'the jaw\'s target is the shared one');
  assert.notEqual(young.morphAttributes.position[0], geo.morphAttributes.position[0]);
  assert(Math.abs(young.morphAttributes.position[0].getY(0) + .75) < 1e-6 && Math.abs(young.morphAttributes.position[1].getY(1) + 1.5) < 1e-6, 'the blink keeps the rest of the way');
  assert.equal(geo.morphAttributes.position[0].getY(0), -1, 'the shared target is untouched');
  const old = restedBlink(face, face, .25, 60), aged = restingLid(60);
  assert(aged > 0 && Math.abs(old.rest + (1 - old.rest) * aged - .25) < 1e-9, 'with its age\'s own rest, the lids rest where the picture has them');
  const variation = await fs.readFile(new URL('renderers/web/js/human-variation.js', here), 'utf8');
  assert(variation.includes('lidRest?.(mesh, scene, like.lid, variation.age)') && variation.includes('lids?.morphAttributes'), 'human-variation.js rests the lids of a face in its own skin');
  assert(!/from '\.\/human-skin\.js'/.test(variation), 'and still reads three alone: human-skin.js hands its lid rest in');
  const skinSource = await fs.readFile(new URL('renderers/web/js/human-skin.js', here), 'utf8');
  assert(skinSource.includes('setLidRest(restedBlink);'), 'human-skin.js hands it in as it loads');
}

// Every person, not only drivers: humans.js dresses each body it builds.
const humans = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
assert(/import \{ dressSkin(, restingLid)? \} from '\.\/human-skin\.js';/.test(humans), 'humans.js imports dressSkin');
// T-3412 put per-person variation between the clone and the dressing, so the window
// allows build()'s whole preamble, not just the lines that were there first.
assert(/const scene = cloneSkinned\(gltf\.scene\);[\s\S]{0,1700}dressSkin\(scene[,)]/.test(humans), 'build() dresses the clone');
// T-3493: the person's age reaches the skin, and the face's cards join the face's morphs.
assert(/dressSkin\(scene, \{ age: this\.variation\?\.age/.test(humans), 'build() passes the person\'s age');
assert(/faces\.push\(hair\.face\)/.test(humans), 'brows and lashes move with the face');
console.log('human-skin: skin, hair and eyes only, no texture but a person\'s own sheet, spliced at every anchor, chained key, rest pose in metres, every body: PASS');
