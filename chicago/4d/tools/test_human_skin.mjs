// SPDX-License-Identifier: GPL-3.0-or-later
// T-3400: skin, hair and eyes for every portable human (renderers/web/js/human-skin.js).
// It must: dress exactly the skin, hair and eyes of every real export (never a garment
// or a shoe); add no texture; splice into three's own standard shader at every anchor it
// names, light wrapper included; chain beneath another hook (confidence.js) with a program
// key that names the chain; share one skin and one hair program across bodies; read each
// body's bind pose in metres however it was quantised; and be wired into humans.js's build.
// T-3553: the one texture it reads is a person's own skin sheet, as uniforms of that same
// program, on that person's material alone; or, for a person with none, the library's sheet
// of faces (FACE_LIBRARY), one face of it inside the face's part of the body's map.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
// human-skin.js imports its sibling human-hair-styles.js (T-3493), so it is loaded from its own
// file with 'three' resolved to the vendored copy, not from a data: URL.
registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const { surfaceFor, dressSkin, restMatrix, SKIN, EYES, AGE, restingLid, likenessLayout, likenessSheetsReady, LIKENESS, MOUTH_SHADE, DRAWN_TEETH, FRONT_VIEW, HAIR_UNDER, frontPicture, FACE_LIBRARY, libraryFaceLayout, SHEET_FETCH } = await import(new URL('renderers/web/js/human-skin.js', here));

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
assert.deepEqual(Object.keys(s.uniforms).sort(), ['chiBrowTint', 'chiFace', 'chiFaceLib', 'chiFaceLibAt', 'chiFaceLibGain', 'chiFaceLook', 'chiFaceMarks', 'chiLike', 'chiLikeAxis', 'chiLikeBack', 'chiLikeFront', 'chiLikeFrontAt', 'chiLikeFrontTo', 'chiLikeFrontU', 'chiLikeFrontV',
  'chiLikeGrow', 'chiLikeHat', 'chiLikeMap', 'chiLikeMask', 'chiLikeTeeth', 'chiLikeTint', 'chiLikeUv', 'chiSkin', 'chiSkinEven', 'chiSkinLipTone', 'chiSkinRest', 'chiSkinSheen']);
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

// T-3553: a face from the library (FACE_LIBRARY; tools/face_library.py builds the sheet). One
// face of the sheet is laid inside a rounded rectangle of the body's map, in the body's skin
// tone and under the person's complexion, before the lips, the age and the brows are worked.
// The same in the shader's text and here.
const faceMask = (u, v) => {
  const L = FACE_LIBRARY, qx = Math.abs(u - L.centre[0]) - (L.half[0] - L.round), qy = Math.abs(v - L.centre[1]) - (L.half[1] - L.round);
  const d = Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - L.round, t = Math.min(1, Math.max(0, (d + L.feather) / L.feather));
  return 1 - t * t * (3 - 2 * t);
};
{
  const L = FACE_LIBRARY, fl = x => (Number.isInteger(x) ? x.toFixed(1) : String(x));
  assert.equal(s.uniforms.chiFaceLib.value, null, 'a plain skin reads no sheet of faces');
  assert.deepEqual(s.uniforms.chiFaceLibGain.value.toArray(), [1, 1, 1, 0], 'and wears none');
  assert.deepEqual(s.uniforms.chiFaceLibAt.value.toArray(), [0, 0, 0, 0]);
  for (const marker of ['if ( chiFaceLibGain.w > 0.5 ) {',
    `vec2 fq = abs( vMapUv - vec2( ${fl(L.centre[0])}, ${fl(L.centre[1])} ) ) - vec2( ${fl(L.half[0] - L.round)}, ${fl(L.half[1] - L.round)} );`,
    `float fd = length( max( fq, 0.0 ) ) + min( max( fq.x, fq.y ), 0.0 ) - ${fl(L.round)};`,
    `float fa = 1.0 - smoothstep( ${fl(-L.feather)}, 0.0, fd );`,
    `vec3 fc = texture2D( chiFaceLib, chiFaceLibAt.xy + ( vMapUv - vec2( ${fl(L.box[0])}, ${fl(L.box[1])} ) ) * chiFaceLibAt.zw ).rgb;`,
    'c = mix( c, fc * chiFaceLibGain.rgb * diffuse, fa );'])
    assert.equal(s.fragmentShader.split(marker).length, 2, `the library's face, once: ${marker}`);
  const at = marker => s.fragmentShader.indexOf(marker);
  assert.deepEqual(s.uniforms.chiSkinEven.value.toArray(), [1, 1, 1], 'a plain skin is its body\'s own');
  assert(at('vec3 c = diffuseColor.rgb * chiSkinEven;') < at('c = mix( c, fc * chiFaceLibGain.rgb * diffuse, fa );') && at('c = mix( c, fc * chiFaceLibGain.rgb * diffuse, fa );') < at('vec3 tex = c / max( diffuse, vec3( 1e-3 ) );'),
    'laid on the body\'s colour first, so the lips, the age and the brows work on the face it gave');
  // The mask: whole over the face, nothing at the ears or past the box a face of the sheet covers.
  const [u0, v0, u1, v1] = L.box;
  assert(Math.abs((u1 - u0) - (v1 - v0)) < 1e-12 && u0 >= 0 && v0 >= 0 && u1 <= 1 && v1 <= 1, 'a face of the sheet is a square of the map');
  assert(L.centre[0] - L.half[0] >= u0 && L.centre[0] + L.half[0] <= u1 && L.centre[1] - L.half[1] >= v0 && L.centre[1] + L.half[1] <= v1, 'the mask lies within the square the sheet holds');
  assert(L.round > L.feather && L.feather > 0 && L.round <= Math.min(...L.half), 'a rounded rectangle with a soft rim inside it');
  // Measured on the bodies' map (T-3553): the midline, the eyes, the brow's top, the chin's point, the temples.
  for (const [what, u, v] of [['between the eyes', 0.838, 0.5167], ['an eye', 0.838, 0.47], ['the other eye', 0.838, 0.565], ['the mouth', 0.92, 0.5167], ['the chin', 0.9595, 0.5167], ['a temple', 0.838, 0.442], ['the other temple', 0.838, 0.591]])
    assert(faceMask(u, v) > 0.999, `${what} wears the library's face whole (${faceMask(u, v)})`);
  for (const [what, u, v] of [['an ear', 0.86, 0.36], ['the other ear', 0.86, 0.67], ['the crown', 0.7526, 0.5167], ['under the jaw', 0.99, 0.5167], ['a hand', 0.3, 0.3]])
    assert.equal(faceMask(u, v), 0, `${what} keeps the body's own skin`);
  assert(faceMask(L.centre[0] - L.half[0] + L.feather / 2, L.centre[1]) > 0.4 && faceMask(L.centre[0] - L.half[0] + L.feather / 2, L.centre[1]) < 0.6, 'and gives way across its rim');
  // What human-variation.js leaves on a figure, as the shader's uniforms.
  const face = { url: 'http://example.invalid/faces.jpg', index: 7, cols: 5, size_px: [1280, 1280], tile_px: 256, gain: [1.25, 1.3, 1.4], lines: 0.6 };
  const lay = libraryFaceLayout(face);
  assert.deepEqual(lay.at.map(x => +x.toFixed(9)), [2 * 256 / 1280, 1 * 256 / 1280, +(256 / 1280 / (u1 - u0)).toFixed(9), +(256 / 1280 / (v1 - v0)).toFixed(9)], 'the eighth face is the third of the second row');
  // The box's corner reads the tile's corner, the box's far corner the tile's far corner.
  assert(Math.abs(lay.at[0] + (u1 - u0) * lay.at[2] - 3 * 256 / 1280) < 1e-12 && Math.abs(lay.at[1] + (v1 - v0) * lay.at[3] - 2 * 256 / 1280) < 1e-12);
  assert.deepEqual([lay.url, lay.gain, lay.lines], [face.url, face.gain, 0.6]);
  assert.notEqual(lay.gain, face.gain, 'its own copy of the gain');
  assert.notEqual(libraryFaceLayout({ ...face, index: 8 }).key, lay.key, 'another face is another look');
  assert.notEqual(libraryFaceLayout({ ...face, url: `${face.url}?2` }).key, lay.key, 'and so is the same place on another sheet');
  assert.notEqual(libraryFaceLayout({ ...face, gain: [1.25, 1.3, 1.5] }).key, lay.key, 'and so is another body\'s gain');
  assert.notEqual(libraryFaceLayout({ ...face, lines: 0.3 }).key, lay.key);
  assert.equal(libraryFaceLayout({ ...face, lines: undefined }).lines, 1, 'a face that says nothing of its lines keeps the drawn ones');
  assert.equal(libraryFaceLayout({ ...face, lines: 7 }).lines, 1);
  for (const [why, bad] of [['none', null], ['none', undefined], ['no sheet', { ...face, url: '' }], ['the body\'s own (-1)', { ...face, index: -1 }], ['a face past the sheet', { ...face, index: 25 }],
    ['half a face', { ...face, index: 1.5 }], ['no columns', { ...face, cols: 0 }], ['no size', { ...face, size_px: null }], ['no tile', { ...face, tile_px: 0 }], ['a gain of two', { ...face, gain: [1, 1] }],
    ['a gain of nothing', { ...face, gain: [1, 0, 1] }], ['a gain that is no number', { ...face, gain: [1, NaN, 1] }]])
    assert.equal(libraryFaceLayout(bad), null, `${why}: no face is laid`);
  assert.notEqual(libraryFaceLayout({ ...face, index: 24 }), null, 'the last face of a five by five sheet is on it');
}

// T-3553: a person's own skin sheet (tools/bake_likeness_skin.py). Its layout is uniforms of
// the one skin program; a body with none reads no sheet; and a person who wears one never
// puts it on the material their body's export shares with everyone else.
{
  assert.equal(s.uniforms.chiLike.value, null, 'a plain skin reads no sheet');
  assert.equal(s.uniforms.chiLikeMask.value.w, 0, 'a plain skin wears no sheet');
  assert.deepEqual(s.uniforms.chiLikeTeeth.value.toArray(), [2, 2, -1, -1], 'and has no mouth to shade: its teeth\'s rect is empty');
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
  // The hair that stands out from the skin (T-3553): the vertex step moves the skin out, away
  // from the head's upright middle line, by the mask's red, never past the hat's band; the
  // fragment step lights it by the sheet's own facing and takes the pores, oil and scatter off it.
  for (const marker of ['if ( chiLikeGrow.w > 0.0 ) {', 'textureLod( chiLike, chiLikeMask.xy + st * chiLikeMask.z, 0.0 ).r * chiLikeGrow.w',
    'stand = min( stand, mix( 1.0, chiLikeHat.y, smoothstep( chiLikeHat.x - 0.02, chiLikeHat.x, vChiSkinP.y ) ) );', 'away *= stand / max( length( away ), 1e-5 );', 'transformed += chiLikeBack * away;',
    'from.y = clamp( vChiSkinP.y, from.y - chiLikeAxis, from.y );', 'vec3 away = vChiSkinP - from;'])
    assert.equal(s.vertexShader.split(marker).length, 2, `grown hair spliced once: ${marker}`);
  assert.equal(s.uniforms.chiLikeAxis.value, 0, 'a plain skin has no line to stand out from');
  for (const marker of ['chiLikeHair = a * mask.b;', 'chiLikeStand = a * mask.r * chiLikeGrow.w;', 'roughnessFactor = mix( roughnessFactor, max( roughnessFactor, 0.8 ), chiLikeHair );'])
    assert.equal(s.fragmentShader.split(marker).length, 2, `grown hair spliced once: ${marker}`);
  // ...and the cells of the sheet the hair stands out in: the head rect's upper half (48 x 64 cells of 16).
  const hairCells = Buffer.from(Uint8Array.from({ length: 384 }, (_, i) => (i < 192 && i % 6 < 4 ? 255 : 0))).toString('base64');
  const grownSheet = { ...sheet, grow: { reach_m: 0.05, from_m: [0, 1.64, 0.03], normal_px: [528, 566], axis_m: 0.07, fine: { cell_px: 16, edge_m: 0.008, cells: hairCells } },
    eyes: { px: [528, 838], size: 96, white_srgb: [0.42, 0.36, 0.34] } };
  const grownLay = likenessLayout(grownSheet);
  assert.deepEqual(grownLay.grow, [0, 1.64, 0.03, 0.05]);
  assert.equal(grownLay.axis, 0.07, 'the upright line the hair stands out from');
  assert.deepEqual([grownLay.fine.cols, grownLay.fine.rows, grownLay.fine.edge_m], [48, 64, 0.008], 'and the cells it stands out in');
  const oldSheet = likenessLayout({ ...sheet, grow: { reach_m: 0.05, from_m: [0, 1.64, 0.03], normal_px: [528, 566] } });
  assert.deepEqual([oldSheet.axis, oldSheet.fine], [0, null], 'a record with neither stands out from one point, on the body\'s own triangles');
  assert.deepEqual([lay.axis, lay.fine], [0, null]);
  assert.deepEqual(grownLay.facing, [528 / 768, 566 / 1024]);
  assert.deepEqual(grownLay.eyes, { rect: [528 / 768, 838 / 1024, 192 / 768, 96 / 1024], white: [0.42, 0.36, 0.34] });
  for (const bad of [{ reach_m: 0, from_m: [0, 1, 0], normal_px: [1, 1] }, { reach_m: 0.05, from_m: [0, 1], normal_px: [1, 1] }, { reach_m: 0.05, from_m: [0, 1, 0] }])
    assert.deepEqual(likenessLayout({ ...sheet, grow: bad }).grow, [0, 0, 0, 0], 'a grow block that does not parse grows nothing');
  for (const bad of [{ px: [1, 1], size: 0, white_srgb: [1, 1, 1] }, { px: [1], size: 96, white_srgb: [1, 1, 1] }, { px: [1, 1], size: 96, white_srgb: [1, 1] }])
    assert.equal(likenessLayout({ ...sheet, eyes: bad }).eyes, null, 'an eyes block that does not parse is none');
  for (const bad of [null, {}, { ...sheet, url: '' }, { ...sheet, rects: [] }, { ...sheet, rects: Array(LIKENESS.rects + 1).fill(sheet.rects[0]) },
    { ...sheet, rects: [{ uv: [1, 0, 0, 1], px: [0, 0, 1, 1] }] }, { ...sheet, mask: null }]) assert.equal(likenessLayout(bad), null, 'a sheet that does not parse is no sheet');
  // The front picture, shown from the front (T-3553, FRONT_VIEW): a picture of its own beside
  // the sheet, laid on the grown skin by where each place stands at rest, for an eye near the
  // line it was taken along, on what faces it, where the sheet took another picture, and only
  // its hair on hair and its skin on skin.
  const picture = { url: 'http://example.invalid/likeness/p_front.jpg', size_px: [640, 512], colour_px: [0, 0, 512, 512], shown_px: [512, 0, 640, 128], kind_px: [512, 128, 640, 256],
    u: [3.5, 0.2, 0.8, 0.2], v: [0.3, -3.6, -0.6, 6.3], toward: [0, 0, 1] };
  const shownLay = likenessLayout({ ...grownSheet, front: picture });
  assert.deepEqual(shownLay.front, { url: picture.url, u: picture.u, v: picture.v, to: [0, 0, 1], at: [[0, 0, 0.8, 1], [0.8, 0, 0.2, 0.25], [0.8, 0.25, 0.2, 0.25]] }, 'its camera, and its three rectangles as shares of the file');
  assert.equal(grownLay.front, null, 'a sheet with no front picture has none');
  assert.equal(likenessLayout({ ...sheet, front: picture }).front, null, 'and a sheet whose hair does not stand out is not given one (it is laid on the grown skin)');
  for (const bad of [{ ...picture, url: '' }, { ...picture, toward: [0, 0, 2] }, { ...picture, u: [1, 2, 3] }, { ...picture, kind_px: undefined }, { ...picture, shown_px: [640, 0, 512, 128] }, { ...picture, size_px: [0, 512] }])
    assert.equal(frontPicture(bad), null, 'a front picture that does not parse is none');
  assert.equal(s.uniforms.chiLikeFront.value, null, 'a plain skin reads no front picture');
  assert.equal(s.uniforms.chiLikeFrontTo.value.w, 0, 'and is told so');
  assert.equal(s.uniforms.chiLikeFrontAt.value.length, 3);
  for (const marker of ['vec3 chiGrown = vChiSkinP;', 'chiGrown += away;',
    'vChiLikeFront = vec2( dot( chiLikeFrontU.xyz, chiGrown ) + chiLikeFrontU.w, dot( chiLikeFrontV.xyz, chiGrown ) + chiLikeFrontV.w );'])
    assert.equal(s.vertexShader.split(marker).length, 2, `the front picture's place, once: ${marker}`);
  for (const marker of ['if ( chiLikeFrontTo.w > 0.5 ) {', `float shown = smoothstep( ${FRONT_VIEW.from}, ${FRONT_VIEW.full}, dot( normalize( vViewPosition ), to ) )`,
    `* smoothstep( 0.0, ${FRONT_VIEW.faces}, dot( facing, chiLikeFrontTo.xyz ) );`, `vec2 q = clamp( vChiLikeFront, ${FRONT_VIEW.inset}, 1.0 - ${FRONT_VIEW.inset} );`,
    'shown *= texture2D( chiLikeFront, chiLikeFrontAt[ 1 ].xy + q * chiLikeFrontAt[ 1 ].zw ).g;',
    `shown *= 1.0 - smoothstep( ${FRONT_VIEW.kind}, ${FRONT_VIEW.other}, abs( texture2D( chiLikeFront, chiLikeFrontAt[ 2 ].xy + q * chiLikeFrontAt[ 2 ].zw ).g - mask.b ) );`,
    'like = mix( like, texture2D( chiLikeFront, chiLikeFrontAt[ 0 ].xy + q * chiLikeFrontAt[ 0 ].zw ).rgb * chiLikeTint.w, shown );'])
    assert.equal(s.fragmentShader.split(marker).length, 2, `the front picture, once: ${marker}`);
  assert(s.fragmentShader.indexOf('like = mix( like, texture2D( chiLikeFront,') < s.fragmentShader.indexOf('c = mix( c / max( diffuse, vec3( 1e-3 ) ) * chiLikeTint.rgb, like, a );'), 'it is the sheet\'s colour before the sheet is laid on the body\'s');
  assert(FRONT_VIEW.from > 0.5 && FRONT_VIEW.from < FRONT_VIEW.full && FRONT_VIEW.full < 1, 'all of it from in front, none of it from the side (a side picture\'s own view is past 60 degrees)');
  assert(FRONT_VIEW.faces > 0 && FRONT_VIEW.faces < 0.5 && FRONT_VIEW.kind < FRONT_VIEW.other && FRONT_VIEW.inset > 0 && FRONT_VIEW.inset < 0.02);
  // The small blocks stand edge to edge on the file: read two of their texels in, a filtered
  // read at a block's rim stays the block's own on a phone's half-size copy too.
  assert(FRONT_VIEW.inset * (picture.shown_px[2] - picture.shown_px[0]) >= 2, 'the blocks beside the picture are read at least two texels in from their rims');
  // Hair that hangs is not lit as a ceiling (HAIR_UNDER): where hair's grown surface faces down
  // it takes the light as its side does.
  for (const marker of ['vec2 out2 = vChiSkinP.xz - chiLikeGrow.xz;', `vec3 side = vec3( out2.x, 0.0, out2.y ) / max( length( out2 ), 1e-4 ) + vec3( 0.0, - ${HAIR_UNDER.down}, 0.0 );`,
    `vec3 n = mix( chiLikeN, normalize( side ), chiLikeHair * smoothstep( ${HAIR_UNDER.from}, ${HAIR_UNDER.full}, - chiLikeN.y ) );`, 'vec3 grown = normalize( gx * n.x + gy * n.y + cross( gx, gy ) * n.z );'])
    assert.equal(s.fragmentShader.split(marker).length, 2, `the underside of hair, once: ${marker}`);
  assert(HAIR_UNDER.from > 0 && HAIR_UNDER.from < HAIR_UNDER.full && HAIR_UNDER.full < 1 && HAIR_UNDER.down >= 0 && HAIR_UNDER.down < 0.5, 'hair that faces out or up is lit as it faces');
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
  assert.equal(gs.uniforms.chiLikeAxis.value, 0.07);
  assert.deepEqual(gs.uniforms.chiLikeHat.value.toArray().slice(1), [LIKENESS.under_hat_m, 528 / 768, 566 / 1024]);
  assert(gs.uniforms.chiLikeHat.value.x > 1e5, 'bareheaded until a hat is seen on it');
  assert.equal(typeof grownBody.onBeforeRender, 'function');
  // Where the hair stands out the near levels' skin is drawn finer (human-fine.js): the person's
  // own geometry, the body's vertices first; the far levels, a phone and everyone else keep the body's.
  {
    const head = () => {
      const g = new THREE.SphereGeometry(.1, 12, 8), n = g.attributes.position.count, uv = g.attributes.uv;
      // The ball's own texture coordinates, laid inside the sheet's head rect.
      for (let i = 0; i < n; i++) uv.setXY(i, 0.635 + uv.getX(i) * 0.365, 0.175 + uv.getY(i) * 0.685);
      g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Array(n * 4).fill(0), 4));
      g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(Array.from({ length: n * 4 }, (_, i) => (i % 4 ? 0 : 1)), 4));
      return g;
    };
    const wear = (geo, name, like) => {
      const bone = new THREE.Bone(), mesh = Object.assign(new THREE.SkinnedMesh(geo, Object.assign(new THREE.MeshStandardMaterial(), { name: 'skin' })), { name });
      const root = new THREE.Group(); root.add(bone, mesh); root.updateMatrixWorld(true);
      mesh.bind(new THREE.Skeleton([bone]), mesh.matrixWorld);
      if (like) root.userData.chiLikenessSkin = like;
      dressSkin(root); dressSkin(root);
      return mesh;
    };
    const near = head(), n0 = near.attributes.position.count;
    const one = wear(near, 'stand_in_body_0_lod0', grownSheet), two = wear(near, 'stand_in_body_0_lod0', grownSheet);
    assert.notEqual(one.geometry, near, 'the near level\'s skin is split under the hair');
    assert.deepEqual(one.geometry.userData.chiFine.of, n0);
    assert(one.geometry.attributes.position.count > n0 * 2 && one.geometry.attributes.skinWeight.count === one.geometry.attributes.position.count);
    assert.deepEqual(Array.from(one.geometry.attributes.position.array.subarray(0, n0 * 3)), Array.from(near.attributes.position.array), 'the body\'s vertices first, as they were');
    assert.equal(two.geometry, one.geometry, 'one fine geometry for every rebuild of the person at that level');
    assert.equal(wear(near, 'stand_in_body_0_lod1', grownSheet).geometry, one.geometry, 'the second level too');
    assert.equal(wear(near, 'stand_in_body_0_lod2', grownSheet).geometry, near, 'a far level keeps the body\'s triangles');
    assert.equal(wear(near, 'stand_in_body_0', grownSheet).geometry, near, 'and a mesh of no level');
    assert.equal(wear(near, 'stand_in_body_0_lod0', sheet).geometry, near, 'a sheet with no hair standing out splits nothing');
    assert.equal(wear(near, 'stand_in_body_0_lod0', null).geometry, near, 'nor does a plain body');
    assert.equal(LIKENESS.fine_lods, 2);
    // A phone (a touch screen under LIKENESS.small_px on its short side) keeps the body's own.
    const had = { screen: Object.getOwnPropertyDescriptor(globalThis, 'screen'), navigator: Object.getOwnPropertyDescriptor(globalThis, 'navigator') };
    Object.defineProperty(globalThis, 'screen', { value: { width: 390, height: 780 }, configurable: true });
    Object.defineProperty(globalThis, 'navigator', { value: { maxTouchPoints: 5 }, configurable: true });
    try { assert.equal(wear(head(), 'stand_in_body_0_lod0', grownSheet).geometry.userData.chiFine, undefined, 'a phone keeps the body\'s triangles'); }
    finally { for (const [k, d] of Object.entries(had)) { if (d) Object.defineProperty(globalThis, k, d); else delete globalThis[k]; } }
    assert(wear(head(), 'stand_in_body_0_lod0', grownSheet).geometry.userData.chiFine, 'and a computer does not');
  }
  // A mouth that opens (T-3553, human-mouth.js): a sheet with teeth adds their strip to the skin's
  // own geometry at every level, after the finer head's rows, carried by the bone it names; a
  // figure whose face has the smile, or who has a jaw, is given its mouth's play, left on the
  // figure; one with neither has none.
  {
    const teeth = { grid: [3, 2], bone: 'head', at_m: [[-.01, .005, .09], [0, .005, .091], [.01, .005, .09], [-.01, -.005, .09], [0, -.005, .091], [.01, -.005, .09]],
      uv: [[.76, .87], [.8, .87], [.84, .87], [.76, .9], [.8, .9], [.84, .9]] };
    const toothed = { ...grownSheet, url: grownSheet.url + '?teeth', teeth, smile: { file: 'x.json', vertices: [0], delta: [0, 0, 1] } };
    const head = () => {
      const g = new THREE.SphereGeometry(.1, 12, 8), n = g.attributes.position.count, uv = g.attributes.uv;
      for (let i = 0; i < n; i++) uv.setXY(i, 0.635 + uv.getX(i) * 0.365, 0.175 + uv.getY(i) * 0.685);
      g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Array(n * 4).fill(0), 4));
      g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(Array.from({ length: n * 4 }, (_, i) => (i % 4 ? 0 : 1)), 4));
      return g;
    };
    const wear = (geo, name, like, smiling = true) => {
      const spine = new THREE.Bone(), skull = Object.assign(new THREE.Bone(), { name: 'head' });
      const mesh = Object.assign(new THREE.SkinnedMesh(geo, Object.assign(new THREE.MeshStandardMaterial(), { name: 'skin' })), { name });
      const root = new THREE.Group(); spine.add(skull); root.add(spine, mesh); root.updateMatrixWorld(true);
      mesh.bind(new THREE.Skeleton([spine, skull]), mesh.matrixWorld);
      // human-variation.js names the smile on a mesh whose face moves.
      if (smiling) { mesh.morphTargetDictionary = { eyeBlinkLeft: 0, jawOpen: 1, chiSmile: 2 }; mesh.morphTargetInfluences = [0, 0, 0]; }
      if (like) root.userData.chiLikenessSkin = like;
      dressSkin(root, { person: 'stand_in' }); dressSkin(root, { person: 'stand_in' });
      return { mesh, root };
    };
    for (const [name, fine] of [['stand_in_body_0_lod0', true], ['stand_in_body_0_lod3', false]]) {
      const src = head(), n0 = src.attributes.position.count, { mesh, root } = wear(src, name, toothed);
      const g = mesh.geometry, t = g.userData.chiTeeth;
      assert(t && t.added === 6, `${name}: the strip is added`);
      assert.equal(!!g.userData.chiFine, fine, `${name}: on the ${fine ? 'finer' : "body's own"} head`);
      assert.equal(t.of + 6, g.attributes.position.count, 'its rows are the last');
      assert(fine ? t.of > n0 : t.of === n0);
      assert.deepEqual([0, 1, 2, 3].map(c => g.attributes.skinIndex.getComponent(t.of, c)), [1, 0, 0, 0], 'carried by the bone the record names');
      assert.equal(src.attributes.position.count, n0, 'the body\'s own geometry is not touched');
      const mouth = root.userData.chiMouth;
      assert(mouth?.bound, `${name}: the figure is given its mouth`);
      const first = mouth;
      dressSkin(root, { person: 'stand_in' });
      assert.equal(root.userData.chiMouth, first, 'the same one at every rebuild');
      for (let k = 0; k < 90; k++) mouth.apply(1 / 30, { facing: true });
      assert.equal(mesh.morphTargetInfluences[2], 1, 'and it plays the smile');
    }
    assert.equal(wear(head(), 'stand_in_body_0_lod0', toothed, false).root.userData.chiMouth, undefined, 'a level with no face that moves and no jaw has no mouth to play');
    const plainHead = head(), plain = wear(plainHead, 'stand_in_body_0_lod3', sheet, false);
    assert.equal(plain.mesh.geometry, plainHead, 'a sheet with no teeth adds none');
    assert.equal(plain.root.userData.chiMouth, undefined, 'and no mouth');
    // A figure with a jaw and no smile has a mouth all the same (it talks); and a ball of a
    // head, with no lips' edge to find, is given no drawn teeth.
    { const spine = new THREE.Bone(), skull = Object.assign(new THREE.Bone(), { name: 'head' }), jaw = Object.assign(new THREE.Bone(), { name: 'jaw' });
      const mesh = Object.assign(new THREE.SkinnedMesh(head(), Object.assign(new THREE.MeshStandardMaterial(), { name: 'skin' })), { name: 'talker_body_0_lod2' });
      const root = new THREE.Group(); spine.add(skull); skull.add(jaw); root.add(spine, mesh); root.updateMatrixWorld(true);
      mesh.bind(new THREE.Skeleton([spine, skull, jaw]), mesh.matrixWorld);
      dressSkin(root, { person: 'talker' });
      const mouth = root.userData.chiMouth;
      assert(mouth?.bound, 'a jaw alone is given a mouth');
      dressSkin(root, { person: 'talker' });
      assert.equal(root.userData.chiMouth, mouth, 'the same one at every rebuild');
      assert.equal(root.children.filter(o => o.userData.chiTeeth === true).length, 0, 'and a head with no lips has no drawn teeth'); }
    // The inside of the mouth is shaded for everyone; the pictured teeth of a face that has
    // them lie in the same shade until the face moves into its smile (its last shape).
    const shadeOf = m => compile(m.material).uniforms.chiLikeTeeth.value.toArray();
    const rect = shadeOf(wear(head(), 'stand_in_body_0_lod0', toothed).mesh);
    assert(rect[0] < .76 && rect[2] > .84 && rect[1] < .87 && rect[3] > .9 && rect[2] - rect[0] < .081 && rect[3] - rect[1] < .031, `a sheet with teeth names their part of the map (${rect})`);
    assert.deepEqual(shadeOf(plain.mesh), [2, 2, -1, -1], 'a sheet with none names no part of the map');
    const { u0, u1, v0, hand_u, hand_v, dark, lit_by } = MOUTH_SHADE;
    for (const line of [`float bag = step( ${u0}, vMapUv.x ) * step( vMapUv.x, ${u1} ) * step( ${v0}, vMapUv.y )`, `* max( step( ${hand_u}, vMapUv.x ), step( ${hand_v}, vMapUv.y ) );`,
      `c *= 1.0 - ${dark} * bag;`, `c *= 1.0 - ${dark} * teeth * ( 1.0 - smoothstep( 0.0, ${lit_by}, vChiSmile ) );`])
      assert.equal(s.fragmentShader.split(line).length, 2, `the mouth's shade, once: ${line}`);
    // Everyone's: the mouth's own shade stands outside the block a person's sheet is read in.
    const blockEnd = s.fragmentShader.indexOf('chiLikeN = facing;'), bagAt = s.fragmentShader.indexOf(`c *= 1.0 - ${dark} * bag;`), sheetAt = s.fragmentShader.indexOf('if ( chiLikeMask.w > 0.5 ) {');
    assert(sheetAt > 0 && blockEnd > sheetAt && bagAt > blockEnd && bagAt < s.fragmentShader.indexOf('diffuseColor.rgb = c;', bagAt), "the inside of the mouth is shaded after a sheet's pictures are laid, whoever wears the skin");
    // Drawn teeth (everyone with no picture of theirs): drawn by the one skin program from their
    // place outside the map, where no sheet and no body has anything; no pores, no blood, wet.
    const { TEETH_DRAWN } = await import(new URL('renderers/web/js/human-mouth.js', here));
    const fl = x => (Number.isInteger(x) ? x.toFixed(1) : String(x)), T = TEETH_DRAWN;
    assert.deepEqual([T.u0, T.v0, T.set_u, T.tone_v, T.row_v, T.pad], [2, 2, 2, 4, 2, 0.05], 'the layout of a tooth\'s place on the map (tools/test_human_mouth.mjs reads it back the same way)');
    assert(T.set_u >= 2 && T.row_v >= 1 + 2 * T.pad && T.tone_v >= 2 * T.row_v, 'a set, a row and a tone each have room');
    for (const line of [
      // ...its place read back: which set (a hair inside it, so a place on a set's first edge is that set's), tone and row,
      `float su = vMapUv.x - ${fl(T.u0)}, set = floor( ( su + 1e-4 ) / ${fl(T.set_u)} );`,
      `float sv = vMapUv.y - ${fl(T.v0)}, tone = floor( sv / ${fl(T.tone_v)} ), row = sv - ${fl(T.tone_v)} * tone, lower = step( ${fl(T.row_v)}, row );`,
      // ...how far across and from gum to edge, and the tooth drawn there over whatever the map gave;
      `c = chiDrawnTeeth( clamp( su - ${fl(T.set_u)} * set, 0.0, 1.0 ), clamp( ( row - ${fl(T.row_v)} * lower - ${T.pad} ) / ${1 - 2 * T.pad}, 0.0, 1.0 ), lower, set, tone );`,
      'chiSkinLip = 0.0; chiSkinCrease = 0.0; ageH = 0.0; pore = 0.0; lines = 0.0; grain = 0.0;',
      // ...the drawing itself: a tooth to its edge and its sides, gum to ivory, and the mouth's dark past it.
      `float tooth = ( 1.0 - smoothstep( longs - 0.03, longs, along ) ) * smoothstep( 0.0, ${DRAWN_TEETH.gap}, side );`,
      `vec3 c = mix( vec3( ${DRAWN_TEETH.gums.join(', ')} ), ivory, smoothstep( ${DRAWN_TEETH.gum[0]}, ${DRAWN_TEETH.gum[1]}, along ) );`,
      `return mix( vec3( ${DRAWN_TEETH.dark.join(', ')} ), c, tooth );`,
      'vec3 chiDrawnTeeth( float across, float along, float lower, float set, float tone ) {', `if ( vMapUv.x > ${TEETH_DRAWN.u0 - 0.5} ) {`, 
      `roughnessFactor = mix( roughnessFactor, ${DRAWN_TEETH.gloss}, chiSkinTooth );`, 'vec3 soft = vec3( 0.6, 0.38, 0.25 ) * chiSkin.w * ( 1.0 - chiLikeHair ) * ( 1.0 - chiSkinIn );', '* vec3( 0.24, 0.07, 0.035 ) * chiSkin.w * ( 1.0 - chiLikeHair ) * ( 1.0 - chiSkinIn );', 'chiRim * 3.0 * ( 1.0 - chiSkinIn );', 'chiSkinIn = bag;', `float inMouth = chiSkinIn * ( 1.0 - ${DRAWN_TEETH.shine} * chiSkinTooth );`, 'reflectedLight.indirectSpecular *= 1.0 - inMouth;', 'reflectedLight.directSpecular *= 1.0 - inMouth;', 'pore *= 1.0 - bag; lines *= 1.0 - bag; grain *= 1.0 - bag; ageH *= 1.0 - bag;', 'chiSkinTooth = 1.0; chiSkinIn = 1.0;'])
      assert.equal(s.fragmentShader.split(line).length, 2, `drawn teeth, once: ${line}`);
    assert(s.fragmentShader.indexOf('c = chiDrawnTeeth(') > bagAt, 'drawn over whatever the map gave that place');
    assert(TEETH_DRAWN.u0 - 0.5 > 1 && TEETH_DRAWN.v0 > 1, 'their place lies outside the map');
    const D = DRAWN_TEETH;
    for (const edges of [D.upper, D.lower]) assert(edges.length === 4 && edges.every((e, i) => e > (edges[i - 1] ?? 0)) && edges[2] * (1 + 1.5 * D.size) < 1, `three teeth and part of a fourth show on a side (${edges})`);
    assert(D.lower[0] < D.upper[0], 'a lower incisor is narrower than an upper');
    assert(D.long.length === 5 && D.long.every(l => l > .7 && l <= 1) && D.long[1] < D.long[0], 'the side incisors are shorter');
    assert(D.ivory.every((c, i) => c * Math.max(...D.lit) < .6 && c >= (D.ivory[i + 1] ?? 0)) && D.stain.every(x => x > .6 && x < 1), 'ivory in the mouth, never white; a tone further is duller and yellower');
    assert(D.dark.every(c => c < .1) && D.gloss < .5 && D.shine > 0 && D.shine < .5 && D.gum[0] < D.gum[1] && D.gum[1] < .3);
    assert.equal(s.vertexShader.split('vChiSmile = morphTargetInfluences[ MORPHTARGETS_COUNT - 1 ];').length, 2, 'the smile is read as the last shape of a face that moves');
    assert(s.vertexShader.indexOf('vChiSmile = 0.0;') < s.vertexShader.indexOf('#ifdef USE_MORPHTARGETS\n    vChiSmile ='), 'and is none on a face that does not');
    assert(dark > .5 && dark < 1 && lit_by > 0 && lit_by <= .4, 'lit before the smile kept while talking is reached');
    assert.equal(wear(head(), 'stand_in_body_0_lod3', { ...toothed, teeth: { ...teeth, bone: 'jawbone' } }).mesh.geometry.userData.chiTeeth, undefined, 'a bone the body has not, no strip');
  }
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

// T-3553: the shaded part of the map (MOUTH_SHADE) holds the inside of the mouth and nothing else, on
// every real body, at every level: a triangle that reaches into it is carried by the head or
// the jaw (the left hand's island lies against it; a fingertip was shaded once).
{
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
  // The area of a triangle inside a rectangle of the map.
  const within = (tri, [x0, y0, x1, y1]) => {
    const cut = (poly, inside, meet) => { const out = []; for (let i = 0; i < poly.length; i++) { const a = poly[i], b = poly[(i + 1) % poly.length]; if (inside(a)) out.push(a); if (inside(a) !== inside(b)) out.push(meet(a, b)); } return out; };
    const atX = x => (a, b) => [x, a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1])], atY = y => (a, b) => [a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]), y];
    let poly = cut(tri, p => p[0] >= x0, atX(x0)); poly = cut(poly, p => p[0] <= x1, atX(x1)); poly = cut(poly, p => p[1] >= y0, atY(y0)); poly = cut(poly, p => p[1] <= y1, atY(y1));
    let area = 0; for (let i = 0; i < poly.length; i++) { const p = poly[i], q = poly[(i + 1) % poly.length]; area += p[0] * q[1] - q[0] * p[1]; }
    return Math.abs(area) / 2;
  };
  const { u0, u1, v0, hand_u, hand_v } = MOUTH_SHADE, shaded = [[hand_u, v0, u1, 2], [u0, hand_v, hand_u, 2]], corner = [u0, v0, hand_u, hand_v];
  // The mouth's own island: the head's and the jaw's triangles in this part of the map (the
  // hand's fingertip lies against it). All of it is to be shaded, not most of it.
  const island = [0.75, v0, u1, 1], whole = tri => Math.abs((tri[1][0] - tri[0][0]) * (tri[2][1] - tri[0][1]) - (tri[2][0] - tri[0][0]) * (tri[1][1] - tri[0][1])) / 2;
  // ...and the teeth's own part of the map (the strip's, from the record) holds nothing of the
  // body at all: what is shaded there with the mouth shut is the strip and only the strip.
  const persons = JSON.parse(await fs.readFile(new URL('assets/humans/web/hm08_variation_persons.json', here), 'utf8')).persons;
  const toothRect = likenessLayout({ ...persons.pa1904_grey_w_l.skin, url: 'http://example.invalid/w_skin.jpg' })?.teeth?.rect;
  assert(toothRect && toothRect[2] > toothRect[0] && toothRect[3] > toothRect[1], 'William Grey\'s record has teeth, and their part of the map');
  // Sarah Grey's are her own photograph of the smile's, in the same part of her sheet; a record
  // without teeth has none.
  const herRect = likenessLayout({ ...persons.pa1904_grey_mrs_w_l.skin, url: 'http://example.invalid/s_skin.jpg' })?.teeth?.rect;
  assert(herRect && herRect[2] > herRect[0] && herRect[3] > herRect[1], 'Sarah Grey\'s record has teeth, and their part of the map');
  assert.equal(likenessLayout({ ...persons.pa1904_grey_mrs_w_l.skin, teeth: undefined, url: 'http://example.invalid/s_bare.jpg' }).teeth, null, 'a record with no teeth has none');
  // T-3553: and the library's face (FACE_LIBRARY) lies over the head and nothing else: every
  // triangle that reaches into its rectangle of the map is carried by the head or the jaw, and
  // the face fills that rectangle but for its rounded corners.
  const faceRect = [FACE_LIBRARY.centre[0] - FACE_LIBRARY.half[0], FACE_LIBRARY.centre[1] - FACE_LIBRARY.half[1], FACE_LIBRARY.centre[0] + FACE_LIBRARY.half[0], FACE_LIBRARY.centre[1] + FACE_LIBRARY.half[1]];
  const faceArea = (faceRect[2] - faceRect[0]) * (faceRect[3] - faceRect[1]);
  let cornered = 0;
  const bodies = (await fs.readdir(new URL('assets/humans/web/', here))).filter(f => /\.lod0\.glb$/.test(f) && !/^c4d_fixture\./.test(f)).map(f => f.replace(/\.lod0\.glb$/, '')).sort();
  assert(bodies.length >= 35 && bodies.includes('glessner_john_j_1904') && bodies.includes('glessner_frances_m_1904'), `${bodies.length} bodies`);
  for (const asset of bodies) for (const lod of [0, 1, 2, 3]) {
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bare(await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here))), '');
    let skins = 0, inMouth = 0, lined = 0, faced = 0;
    gltf.scene.traverse((o) => {
      if (!o.isSkinnedMesh || surfaceFor(o.material) !== 'skin') return;
      skins++;
      const g = o.geometry, uv = g.attributes.uv, at = g.index, si = g.attributes.skinIndex, sw = g.attributes.skinWeight, bones = o.skeleton.bones;
      const bone = (i) => { let b = 0, w = -1; for (let c = 0; c < 4; c++) if (sw.getComponent(i, c) > w) { w = sw.getComponent(i, c); b = si.getComponent(i, c); } return bones[b].name; };
      for (let t = 0; t < at.count; t += 3) {
        const v = [at.getX(t), at.getX(t + 1), at.getX(t + 2)], tri = v.map(i => [uv.getX(i), uv.getY(i)]), names = v.map(bone);
        const head = names.every(n => n === 'head' || n === 'jaw');
        const area = shaded.reduce((a, r) => a + within(tri, r), 0);
        if (area > 0) { assert(head, `${asset} lod${lod}: a triangle of ${names.join(', ')} lies in the mouth's shade`); inMouth += area; }
        if (head && tri.every(([u, w]) => u >= island[0] && u <= island[2] && w >= island[1] && w <= island[3])) {
          assert(Math.abs(whole(tri) - area) < 1e-9, `${asset} lod${lod}: a triangle of the mouth's inside lies partly out of its shade (${tri.map(q => q.map(x => x.toFixed(4)).join(' ')).join(' | ')}: ${((1 - area / whole(tri)) * 100).toFixed(1)} percent of it)`);
          lined++;
        }
        if (!head && within(tri, corner) > 0) cornered++;
        const onFace = within(tri, faceRect);
        if (onFace > 0) { assert(head, `${asset} lod${lod}: a triangle of ${names.join(', ')} lies under the library's face`); faced += onFace; }
        for (const rect of [toothRect, herRect]) assert.equal(within(tri, rect), 0, `${asset} lod${lod}: a triangle of ${names.join(', ')} lies in the teeth's part of the map`);
      }
    });
    assert(skins > 0 && inMouth > 0.01 && lined >= 8, `${asset} lod${lod}: the inside of the mouth is in its shade (${inMouth.toFixed(4)} of the map, ${lined} triangles)`);
    assert(faced > 0.9 * faceArea && faced <= faceArea + 1e-9, `${asset} lod${lod}: the face fills the library's rectangle (${(faced / faceArea * 100).toFixed(1)} percent of it)`);
  }
  assert(cornered > 0, 'the corner left out is the one the hand reaches into');

  // Everyone's drawn teeth: a real body with no sheet is given a small mesh of two rows beside
  // its skin, in the skin's own material and on its skeleton, made hidden; its mouth shows it.
  const { TEETH_DRAWN: T } = await import(new URL('renderers/web/js/human-mouth.js', here));
  for (const [asset, lod] of [['glessner_john_j_1904', 0], ['woman_working_1812', 1], ['child_toddler_1904', 3]]) {
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bare(await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here))), '');
    const root = gltf.scene, what = `${asset} lod${lod}`;
    root.updateMatrixWorld(true);
    const all = () => { const out = []; root.traverse(o => { if (o.isMesh) out.push(o); }); return out; };
    const before = all(), skin = before.find(o => o.isSkinnedMesh && surfaceFor(o.material) === 'skin'), body = skin.geometry;
    const dressed = dressSkin(root, { age: 40, person: 'someone' });
    const teeth = all().filter(o => o.userData.chiTeeth === true);
    assert.equal(teeth.length, 1, `${what}: one mesh of teeth`);
    const t = teeth[0];
    assert(t.isSkinnedMesh && t.name === 'teeth' && t.parent === skin.parent && all().length === before.length + 1, `${what}: beside the skin`);
    assert(t.material === skin.material && t.skeleton === skin.skeleton && t.bindMatrix.equals(skin.bindMatrix), `${what}: in the skin's material, on its skeleton`);
    assert(t.matrixWorld.equals(skin.matrixWorld) || (root.updateMatrixWorld(true), t.matrixWorld.equals(skin.matrixWorld)), `${what}: standing where the skin stands`);
    assert(t.visible === false && t.frustumCulled === false && !t.castShadow, `${what}: made hidden, and never dropped for its rest pose's bound`);
    assert.equal(t.geometry.attributes.position.count, 36, `${what}: two rows of nine points, twice`);
    // The upper rows on the head's bone and the lower on the jaw's, their place on the map outside it.
    { const names = j => skin.skeleton.bones[t.geometry.attributes.skinIndex.getX(j)].name, tuv = t.geometry.attributes.uv;
      assert.deepEqual([names(0), names(17), names(18), names(35)], ['head', 'head', 'jaw', 'jaw'], `${what}: the upper teeth go with the head and the lower with the jaw`);
      for (let j = 0; j < 36; j++) assert(tuv.getX(j) >= T.u0 && tuv.getY(j) >= T.v0, `${what}: drawn from a place outside the map`); }
    // The skin's own count of morph targets, so the one program draws both; and its shadows.
    assert.deepEqual(Object.fromEntries(Object.entries(t.geometry.morphAttributes).map(([k, l]) => [k, l.length])), Object.fromEntries(Object.entries(body.morphAttributes).map(([k, l]) => [k, l.length])), `${what}: as many morph targets as the skin has`);
    assert.equal(t.morphTargetInfluences?.length, skin.morphTargetInfluences?.length, `${what}: and as many weights`);
    for (const lit of [true, false]) { skin.receiveShadow = lit; t.onBeforeRender(); assert.equal(t.receiveShadow, lit, `${what}: in the skin's shade as it is drawn`); }
    assert.equal(skin.geometry, body, `${what}: the body's own geometry is the skin's still`);
    assert.equal(dressed.skin, 'skin');
    // Shown by the mouth's play to a visitor near, and for a still.
    const mouth = root.userData.chiMouth;
    assert(mouth?.bound, `${what}: the figure has its mouth`);
    mouth.pose({ jaw: 4 });
    assert.equal(t.visible, true, `${what}: a still shows them`);
    // Dressed again: the same mesh and the same rows; another age, the same mesh with that age's rows.
    const g0 = t.geometry;
    dressSkin(root, { age: 40, person: 'someone' });
    assert.deepEqual([all().filter(o => o.userData.chiTeeth === true), t.geometry === g0, root.userData.chiMouth === mouth], [[t], true, true], `${what}: dressed again, nothing is added`);
    // An old face shows less of its upper teeth and more of its lower: both rows' edges stand higher.
    const metres = restMatrix(skin, root), edges = g => [T.cols + 4, 2 * T.cols + 4].map(j => new THREE.Vector3().fromBufferAttribute(g.attributes.position, j).applyMatrix4(metres).y);
    const mid = edges(g0);
    dressSkin(root, { age: 80, person: 'someone' });
    assert(all().filter(o => o.userData.chiTeeth === true).length === 1 && t.geometry !== g0 && t.geometry.attributes.position.count === 36, `${what}: an old face has rows of its own`);
    const aged = edges(t.geometry);
    assert(aged[0] > mid[0] + 2e-4 && aged[1] > mid[1] + 2e-4, `${what}: an old face's rows stand higher, upper and lower (${aged.map((y, k) => ((y - mid[k]) * 1000).toFixed(2))} mm)`);
    assert(t.material === skin.material, `${what}: and its material is the skin's as it is now`);
    // Whose teeth: the person's own set, by their id; an unnamed figure's by the key its
    // variation was drawn by (human-variation.js leaves it on the root), so two strangers differ.
    { const { drawnLook } = await import(new URL('renderers/web/js/human-mouth.js', here));
      const ids = Array.from({ length: 40 }, (_, k) => `stranger_${k}`), a = ids[0], b = ids.find(id => drawnLook({ id, age: 40 }).set !== drawnLook({ id: a, age: 40 }).set);
      const us = () => Array.from({ length: 36 }, (_, j) => t.geometry.attributes.uv.getX(j));
      dressSkin(root, { age: 40, person: a }); const ua = us();
      dressSkin(root, { age: 40, person: b }); const ub = us();
      assert.notDeepEqual(ua, ub, `${what}: another person, another set of teeth`);
      root.userData.chiVariationKey = a; dressSkin(root, { age: 40 });
      assert.deepEqual(us(), ua, `${what}: an unnamed figure's are by its own key`);
      root.userData.chiVariationKey = b; dressSkin(root, { age: 40 });
      assert.deepEqual(us(), ub);
      delete root.userData.chiVariationKey; }
    // A copy of a dressed figure carries a plain record where the mouth was: it is made again, not called.
    { root.userData.chiMouth = JSON.parse(JSON.stringify(root.userData.chiMouth));
      dressSkin(root, { age: 40, person: 'someone' });
      assert(typeof root.userData.chiMouth?.bind === 'function' && root.userData.chiMouth.bound && all().filter(o => o.userData.chiTeeth === true).length === 1, `${what}: a copied figure is given a mouth of its own`); }
    // T-3553: a face from the library on a real body is a look of its own: its material's
    // uniforms carry the face and the body's gain, and the age's drawn lines are scaled by
    // what the face keeps of them (an older atlas has painted its own).
    const face = { url: 'http://example.invalid/faces.jpg', index: 12, cols: 5, size_px: [1280, 1280], tile_px: 256, gain: [1.39, 1.86, 2.43], lines: 0.3 };
    {
      dressSkin(root, { age: 70, person: 'someone' });
      const plainSkin = skin.material, drawn = compile(plainSkin).uniforms.chiFaceLook.value.x;
      const a0 = Math.min(1, Math.max(0, (70 - AGE.from) / (AGE.full - AGE.from)));
      assert(drawn > 0 && drawn === Math.round(a0 * 20) / 20, `${what}: a face of seventy has drawn lines`);
      assert.equal(compile(plainSkin).uniforms.chiFaceLibGain.value.w, 0, `${what}: with no face from the library it wears none`);
      root.userData.chiFaceSkin = face;
      dressSkin(root, { age: 70, person: 'someone' });
      const u = compile(skin.material).uniforms;
      assert.notEqual(skin.material, plainSkin, `${what}: a face from the library is a look of its own`);
      assert.deepEqual(u.chiFaceLibGain.value.toArray(), [1.39, 1.86, 2.43, 1], `${what}: the body's gain, and the face is worn`);
      assert.deepEqual(u.chiFaceLibAt.value.toArray().map(x => +x.toFixed(9)), [0.4, 0.4, 0.8, 0.8], `${what}: the thirteenth face's place on the sheet`);
      assert.equal(u.chiFaceLib.value, null, 'with no page there is no image to fetch');
      assert(u.chiFaceLook.value.x === Math.round(a0 * face.lines * 20) / 20 && u.chiFaceLook.value.x < drawn, `${what}: an old face from the library keeps a part of the drawn lines (${u.chiFaceLook.value.x} of ${drawn})`);
      assert.equal(all().find(o => o.userData.chiTeeth === true)?.material, skin.material, `${what}: its teeth are in its skin's material still`);
      const worn = skin.material;
      root.userData.chiFaceSkin = { ...face, index: 13 };
      dressSkin(root, { age: 70, person: 'someone' });
      assert.notEqual(skin.material, worn, `${what}: another face, another material`);
      root.userData.chiFaceSkin = { ...face, index: 99 };
      dressSkin(root, { age: 70, person: 'someone' });
      assert.equal(compile(skin.material).uniforms.chiFaceLibGain.value.w, 0, `${what}: a face the sheet has not is not worn`);
      assert.equal(compile(skin.material).uniforms.chiFaceLook.value.x, drawn, `${what}: and the drawn lines are whole again`);
      root.userData.chiFaceSkin = face;
      // T-3553 (Kevin, 2026-11-15): a coachman wears the box's skin at his door too: the
      // body's skin is brought to it, a look of its own; a ratio that is not one is none.
      dressSkin(root, { age: 70, person: 'someone' });
      const faced = skin.material;
      root.userData.chiSkinEven = [0.9, 0.67, 0.52];
      dressSkin(root, { age: 70, person: 'someone' });
      assert.notEqual(skin.material, faced, `${what}: another body's skin, another material`);
      assert.deepEqual(compile(skin.material).uniforms.chiSkinEven.value.toArray().map(x => +x.toFixed(6)), [0.9, 0.67, 0.52], `${what}: the skin brought to the one he wears`);
      assert.deepEqual(compile(skin.material).uniforms.chiFaceLibGain.value.toArray(), [1.39, 1.86, 2.43, 1], `${what}: the face as before`);
      for (const bad of [[1, 1, 1], [0.9, 0.67], [0.9, -1, 0.5], 'abc']) {
        root.userData.chiSkinEven = bad;
        dressSkin(root, { age: 70, person: 'someone' });
        assert.deepEqual(compile(skin.material).uniforms.chiSkinEven.value.toArray(), [1, 1, 1], `${what}: ${JSON.stringify(bad)} brings nothing`);
      }
      delete root.userData.chiSkinEven;
    }
    // A sheet with its own teeth takes the drawn ones away.
    if (lod === 0) {
      root.userData.chiLikenessSkin = { ...persons.pa1904_grey_w_l.skin, url: 'http://example.invalid/w_skin.jpg' };
      dressSkin(root, { age: 61, person: 'pictured' });
      assert.equal(compile(skin.material).uniforms.chiFaceLibGain.value.w, 0, `${what}: a person's own sheet is worn, not a face from the library`);
      assert.equal(all().filter(o => o.userData.chiTeeth === true).length, 0, `${what}: a face with pictured teeth has no drawn ones`);
      assert(skin.geometry.userData.chiTeeth?.added > 0, 'its strip is in the skin itself');
    }
  }

  // T-3553: on a page the sheet is fetched, and a fetch that fails is tried again
  // (SHEET_FETCH). A stand-in page, image loader and timer: every request and every wait is
  // held here, to answer as a network might. One texture for an address, for good; one run of
  // tries at a time; everybody waiting wears their face the moment the sheet is here.
  {
    const SK = await import(new URL('addons/utils/SkeletonUtils.js', vendor));
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bare(await fs.readFile(new URL('assets/humans/web/bardwell_otis_1835.lod2.glb', here))), '');
    const calls = [], timers = [], real = { load: THREE.ImageLoader.prototype.load, setTimeout: globalThis.setTimeout };
    const settle = () => new Promise(r => setImmediate(r));
    assert.equal(typeof document, 'undefined');
    globalThis.document = { createElement: () => { throw new Error('no canvas here'); } };
    THREE.ImageLoader.prototype.load = function (url, onLoad, onProgress, onError) { calls.push({ url, ok: () => onLoad({ width: 1280, height: 1280 }), fail: () => onError(new Error('dropped')) }); return {}; };
    globalThis.setTimeout = (fn, ms) => { timers.push({ fn, ms }); return timers.length; };
    try {
      const person = (url, i, gain = [1.25, 1.25, 1.26]) => {
        const root = SK.clone(gltf.scene);
        root.userData.chiFaceSkin = { url, index: i, cols: 5, size_px: [1280, 1280], tile_px: 256, gain, lines: 1 };
        root.updateMatrixWorld(true);
        dressSkin(root, { age: 30, person: `sheet ${url} ${i}` });
        let skin; root.traverse(o => { if (o.isSkinnedMesh && surfaceFor(o.material) === 'skin' && !o.userData.chiTeeth) skin ??= o; });
        return compile(skin.material).uniforms;
      };
      const worn = us => us.map(u => u.chiFaceLibGain.value.w), sheetOf = u => u.chiFaceLib.value;
      const of = url => calls.filter(c => c.url === url);
      assert.deepEqual([SHEET_FETCH.wait_s, SHEET_FETCH.ready_tries], [[2, 8, 30, 60, 60, 60, 60, 60], 3]);

      // The sheet arrives late: asked for once, worn by all once it is here, and by those built after.
      const late = 'http://example.invalid/faces/late.jpg', a = [person(late, 7), person(late, 8), person(late, 9)];
      assert.deepEqual([of(late).length, worn(a)], [1, [0, 0, 0]], 'three people built before the sheet is here: one request, the body\'s own face showing');
      assert(sheetOf(a[0]).isTexture && !sheetOf(a[0]).image && a.every(u => sheetOf(u) === sheetOf(a[0])), 'one texture for the three');
      of(late)[0].ok(); await settle();
      assert.deepEqual(worn(a), [1, 1, 1], 'the sheet arrives: all three wear their faces');
      assert(sheetOf(a[0]).image?.width === 1280 && sheetOf(a[0]).version > 0);
      const after = person(late, 10);
      assert.deepEqual([of(late).length, worn([after]), sheetOf(after) === sheetOf(a[0]), timers.length], [1, [1], true, 0], 'one built afterwards wears it at once, with no other request');

      // An arrival switches a face on only for a material that still holds that sheet. Nothing
      // in the app points a material's uniforms at another sheet today (setLibraryFace sets them
      // once, on new uniforms); the guard is for the day something does: such a material would
      // show the wrong picture, or the face's gain over no picture at all.
      { const first = 'http://example.invalid/faces/first.jpg', other = 'http://example.invalid/faces/other.jpg';
        const moved = person(first, 3), bare = person(first, 4), stays = person(first, 5), there = person(other, 6);
        moved.chiFaceLib.value = sheetOf(there);
        bare.chiFaceLib.value = null;
        of(first)[0].ok(); await settle();
        assert.deepEqual(worn([moved, bare, stays, there]), [0, 0, 1, 0], 'the first sheet arrives: only the one still holding it wears a face');
        of(other)[0].ok(); await settle();
        assert.deepEqual(worn([moved, bare, stays, there]), [0, 0, 1, 1], 'the other arrives: its own waiter wears it'); }

      // The first try is dropped, the second brings it: those built before the failure, during
      // the wait and after it all wear their faces, on the one texture they were given.
      const drop = 'http://example.invalid/faces/dropped.jpg', b = [person(drop, 11), person(drop, 12)];
      of(drop)[0].fail(); await settle();
      assert.deepEqual([of(drop).length, timers.map(x => x.ms), worn(b)], [1, [2000], [0, 0]], 'a dropped request is asked again in two seconds, not at once');
      b.push(person(drop, 13));
      assert.deepEqual([of(drop).length, timers.length], [1, 1], 'a person built during the wait starts no request of their own');
      timers.shift().fn();
      assert.equal(of(drop).length, 2, 'the second try');
      of(drop)[1].ok(); await settle();
      assert.deepEqual(worn(b), [1, 1, 1], 'it arrives: everyone who was waiting wears their face');
      assert(b.every(u => sheetOf(u) === sheetOf(b[0]) && sheetOf(u).image), 'on the texture they were given before it failed');
      assert.deepEqual([worn([person(drop, 11)]), of(drop).length, timers.length], [[1], 2, 0], 'the same person built again wears it, and nothing more is asked');

      // An address that never answers: nine tries, each after its wait; a still waits for the
      // first three only; then nothing, until a body asks again, which begins a new run.
      const gone = 'http://example.invalid/faces/gone.jpg', c = [person(gone, 1)];
      let ready = false;
      likenessSheetsReady().then(() => { ready = true; });
      const waits = [];
      for (let k = 0; k < SHEET_FETCH.wait_s.length + 1; k++) {
        assert.equal(of(gone).length, k + 1, `try ${k + 1}`);
        await settle();
        assert.equal(ready, k >= SHEET_FETCH.ready_tries, `after ${k} failures a still ${k >= SHEET_FETCH.ready_tries ? 'goes on' : 'still waits'}`);
        of(gone)[k].fail(); await settle();
        if (timers.length) { const w = timers.shift(); waits.push(w.ms / 1000); c.push(person(gone, 2 + k)); assert.equal(of(gone).length, k + 1, 'nobody built meanwhile asks'); w.fn(); }
      }
      assert.deepEqual([waits, of(gone).length, timers.length, ready], [[...SHEET_FETCH.wait_s], 9, 0, true], 'nine tries, at the waits named, then no more');
      assert(worn(c).every(w => w === 0), 'nobody wears a face that never came');
      await likenessSheetsReady();   // nothing is under way: it resolves
      c.push(person(gone, 20));
      assert.equal(of(gone).length, 10, 'the next body to ask begins again');
      of(gone)[9].ok(); await settle();
      assert(worn(c).every(w => w === 1) && c.every(u => sheetOf(u) === sheetOf(c[0])), 'and when it comes at last, everyone built since the first wears their face');

      // A crowd built before the sheet is here (some six hundred people wear a library face
      // in 1812): past the 256 at which the waiting list is swept of materials since let go,
      // everyone still wears their face when it comes, here after a dropped try.
      const many = 'http://example.invalid/faces/crowd.jpg';
      const crowd = Array.from({ length: 300 }, (_, k) => person(many, k % 22, [1.2 + k * 0.001, 1.25, 1.26]));
      const sum = us => worn(us).reduce((a, b) => a + b, 0);
      assert.deepEqual([new Set(crowd.map(u => u.chiFaceLibGain.value)).size, of(many).length, sum(crowd)], [300, 1, 0], 'three hundred people, each their own material, one request, nobody wearing a face yet');
      of(many)[0].fail(); await settle(); timers.shift().fn(); of(many)[1].ok(); await settle();
      assert.deepEqual([sum(crowd), new Set(crowd.map(sheetOf)).size, of(many).length, timers.length], [300, 1, 2, 0], 'the sheet comes on the second try: all three hundred wear their faces');

      // A person's own sheet (the Greys') goes through the same loader: the skin sheet, the
      // front picture, and the eyes' part of the sheet. Each dropped once; a second body of
      // the same person built meanwhile asks nothing; then both arrive.
      { const grey = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bare(await fs.readFile(new URL('assets/humans/web/glessner_john_j_1904.lod0.glb', here))), '');
        const skinUrl = 'http://example.invalid/likeness/w_skin.jpg', frontUrl = 'http://example.invalid/likeness/w_front.jpg', s = persons.pa1904_grey_w_l.skin;
        assert(s?.front && s?.eyes, 'the Greys\' sheet has a front picture and eyes');
        const dressed = () => {
          const root = SK.clone(grey.scene);
          root.userData.chiLikenessSkin = { ...s, url: skinUrl, front: { ...s.front, url: frontUrl } };
          root.updateMatrixWorld(true);
          dressSkin(root, { age: 61, person: 'pa1904_grey_w_l' });
          let skin; const eyes = [];
          root.traverse(o => { if (o.isSkinnedMesh && surfaceFor(o.material) === 'skin' && !o.userData.chiTeeth) skin ??= o; if (o.isMesh && /__(iris|pupil)$/.test(o.material?.name ?? '') && o.material.map) eyes.push(o.material.map); });
          return { u: compile(skin.material).uniforms, part: eyes[0] };
        };
        const { u, part } = dressed();
        assert(u.chiLike.value?.isTexture && !u.chiLike.value.image && u.chiLikeFront.value?.isTexture && !u.chiLikeFront.value.image && u.chiLike.value !== u.chiLikeFront.value, 'the skin sheet and the front picture are each asked for');
        assert(part?.isTexture && part !== u.chiLike.value && u.chiFaceLibGain.value.w === 0, 'the eyes read a part of the sheet; no face of the library is worn');
        assert.deepEqual([of(skinUrl).length, of(frontUrl).length], [1, 1]);
        const before = [u.chiLike.value.version, u.chiLikeFront.value.version, part.version];
        of(skinUrl)[0].fail(); of(frontUrl)[0].fail(); await settle();
        const second = dressed();
        assert(second.u.chiLike.value === u.chiLike.value && second.u.chiLikeFront.value === u.chiLikeFront.value, 'another body of the same person holds the same two textures');
        assert.deepEqual([of(skinUrl).length, of(frontUrl).length, timers.length], [1, 1, 2], 'and asks for nothing while the first run waits');
        while (timers.length) timers.shift().fn();
        assert.deepEqual([of(skinUrl).length, of(frontUrl).length], [2, 2]);
        of(skinUrl)[1].ok(); of(frontUrl)[1].ok(); await settle();
        assert(u.chiLike.value.image && u.chiLikeFront.value.image, 'both arrive on the second try, on the textures the materials already hold');
        assert(u.chiLike.value.version > before[0] && u.chiLikeFront.value.version > before[1] && part.version > before[2] && part.image === u.chiLike.value.image, 'each is flagged to be sent to the card, and the eyes\' part with its sheet');
        await likenessSheetsReady(); }
    } finally {
      THREE.ImageLoader.prototype.load = real.load; globalThis.setTimeout = real.setTimeout; delete globalThis.document;
    }
  }
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
console.log('human-skin: skin, hair and eyes only, no texture but a person\'s own sheet or a face of the library\'s, spliced at every anchor, chained key, rest pose in metres, every body: PASS');
