// SPDX-License-Identifier: GPL-3.0-or-later
// T-3553: the women's finery. The owner, 2026-11-14: "when i see shows like gilded age they are
// very fancy and lots of details and you don't have that ... Give the women some variation in
// their clothing appearance". It must:
//  1. hold a dress's finery to what the cloth shader draws (human-finery.js), lay its trims at
//     their heights from the garment's own hem, top or sleeve end, on the person's own material
//     (a clone where it was shared), and hand fabric.js its numbers, in the one cloth program;
//  2. dress a record for the visitor's season (human-looks.js dressInSeason), and humans.js
//     redress on a change of season;
//  3. make the ladies' hats (picture, sailor, toque) on the head with their plumes, flowers and bow;
//  4. dress every Prairie Avenue lady as her own for summer, spring/fall and winter, no two alike,
//     each from the finery sources, her body's own hat left off under the made one; the cooks'
//     print and checked aprons drawn as print and check;
//  5. draw the 1812 records' calico, check and stripes as figures whose mean is the record's colour.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
const hooks = registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const { finerySpec, dressFinery, PATTERNS, TRIMS } = await import(new URL('renderers/web/js/human-finery.js', here));
const { patchFabric, clothHuman } = await import(new URL('renderers/web/js/fabric.js', here));
const { dressInSeason } = await import(new URL('renderers/web/js/human-looks.js', here));
const { dressHat, hatSpec, LADY_HATS } = await import(new URL('renderers/web/js/human-hats.js', here));
const read = async (p) => JSON.parse(await fs.readFile(new URL(p, here), 'utf8'));

// 1. The spec, and the numbers on a garment.
assert.equal(finerySpec(null), null);
assert.equal(finerySpec({ pattern: { kind: 'tartan-ish', rgb: [1, 1, 1] } }), null, 'an unknown figure draws nothing');
const big = finerySpec({ silk: 3, trims: Array.from({ length: 6 }, () => ({ kind: 'lace', rgb: [1, 1, 1], width_m: 9 })) });
assert.equal(big.trims.length, 4, 'at most four trims');
assert.equal(big.silk, 1, 'silk held to 1');
assert.equal(big.trims[0].width_m, .5, 'a trim held to half a metre');
{
  // A skirt 0..2 units tall at 2 units a metre (a quantised export's positions are not metres),
  // its waist band 0.25 units out; a jacket whose sleeves reach 0.8 units out.
  const root = new THREE.Group();
  root.scale.set(.5, .5, .5);   // so restMatrix (mesh to root) is a scale of 0.5: 2 units a metre
  const box = (w, h, y) => { const g = new THREE.BoxGeometry(w, h, .3); g.translate(0, y, 0); return g; };
  const shared = new THREE.MeshStandardMaterial({ name: 'garment_lower__lady_skirt_black' });
  const skirt = new THREE.Mesh(box(.5, 2, 1), shared); skirt.name = 'x_gored_skirt_lod0';
  const jacketMat = new THREE.MeshStandardMaterial({ name: 'garment_outer__lady_jacket_black' });
  const jacket = new THREE.Mesh(box(1.6, 1, 2.5), jacketMat); jacket.name = 'x_lady_jacket_body_lod0';
  const inner = new THREE.Group(); inner.add(skirt, jacket);
  const holder = new THREE.Group(); holder.add(inner);
  // restMatrix measures the mesh against `root`: give it the scaled group as root.
  const made = dressFinery(inner, {
    garment_lower__lady_skirt_black: { pattern: { kind: 'stripe', rgb: [.5, .5, .5], repeat_m: .02 },
      trims: [{ kind: 'flounce', from: 'hem', at_m: .1, width_m: .2, rgb: [.3, .3, .3] }, { kind: 'lace', from: 'top', at_m: .05, width_m: .1, rgb: [.6, .6, .6] }] },
    garment_outer__lady_jacket_black: { velvet: 1, trims: [{ kind: 'lace', from: 'cuff', at_m: .05, width_m: .1, rgb: [.6, .6, .6] }], ground: [.1, .2, .3] },
  }, []);
  assert.equal(made.length, 2, 'a clone for each garment not already the person\'s own');
  assert(skirt.material !== shared && skirt.material.userData.chiFinery, 'the skirt wears its own clone with its numbers');
  const f = skirt.material.userData.chiFinery;
  assert.deepEqual(f.fin.slice(0, 2), [0, 2], 'the skirt\'s own span');
  assert(Math.abs(f.fin[2] - 1) < 1e-9, 'units a metre measured through the mesh (identity here)');
  assert.equal(f.pat[0], PATTERNS.stripe);
  assert(Math.abs(f.bands[0][0] - .1) < 1e-6 && Math.abs(f.bands[0][1] - .1) < 1e-9, 'a hem flounce centred 0.1 up, 0.1 each way');
  assert.equal(f.bands[0][2], TRIMS.flounce, 'round the garment');
  assert(Math.abs(f.bands[1][0] - 1.95) < 1e-6 && f.bands[1][2] === TRIMS.lace + 16, 'a top trim from the top edge, on the body only');
  const j = jacket.material.userData.chiFinery;
  assert(Math.abs(j.bands[0][0] - .75) < 1e-6 && j.bands[0][2] === TRIMS.lace + 32, 'a cuff measured in from the sleeve end');
  assert.equal(j.pat[3], 1, 'velvet');
  assert(Math.abs(jacket.material.color.r - new THREE.Color().setRGB(.1, .2, .3, THREE.LinearSRGBColorSpace).r) < 1e-6, 'a ground colour under the figure');
  // An owned material takes the numbers in place.
  const own = jacket.material;
  assert.equal(dressFinery(inner, { garment_outer__lady_jacket_black: { silk: .5 } }, [own]).length, 0, 'no second clone of the person\'s own');
  // fabric.js reads them; plain and fine share one program.
  clothHuman(inner);
  const compile = (m) => { const sh = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader, fragmentShader: THREE.ShaderLib.standard.fragmentShader }; m.onBeforeCompile(sh, null); return sh; };
  const fine = compile(skirt.material), plain = new THREE.MeshStandardMaterial({ name: 'garment_lower__lady_skirt_black' });
  patchFabric(plain);
  const p = compile(plain);
  assert.equal(fine.vertexShader + fine.fragmentShader, p.vertexShader + p.fragmentShader, 'one program text');
  assert.equal(skirt.material.customProgramCacheKey(), plain.customProgramCacheKey(), 'one program key');
  assert.equal(fine.uniforms.chiFinPat.value.x, PATTERNS.stripe, 'the stripe reaches the shader');
  assert.equal(fine.uniforms.chiFinBand.value[0].z, TRIMS.flounce, 'the flounce reaches the shader');
  assert.equal(p.uniforms.chiFinPat.value.x, 0, 'a plain cloth draws no figure');
  for (const k of ['chiFinStripe', 'chiFinFlower', 'chiFinDamask', 'chiFinBand[ i ]']) assert(fine.fragmentShader.includes(k), k);
}

// 2. Seasons.
{
  const rec = { colours: { a: [1, 0, 0] }, worn: 'summer', hat: { kind: 'sailor' }, seasons: { winter: { colours: { a: [0, 0, 1] }, worn: 'winter', hat: { kind: 'toque' } } } };
  assert.equal(dressInSeason(rec, 'summer'), rec, 'summer is the record itself');
  assert.equal(dressInSeason(rec, 'spring'), rec, 'a season it does not name is the record');
  const w = dressInSeason(rec, 'winter');
  assert.deepEqual([w.colours.a, w.worn, w.hat.kind], [[0, 0, 1], 'winter', 'toque'], 'winter laid over the record');
  const humans = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/dressInSeason\(recorded, dressSeason\)/.test(humans) && /dressFinery\(scene, dress\.finery, looked\)/.test(humans), 'build() dresses for the season, with finery');
  assert(/setSeason\(season\)/.test(humans) && /a\.redress\(\)/.test(humans), 'the layer redresses on a change of season');
  const main = await fs.readFile(new URL('renderers/web/js/main.js', here), 'utf8');
  assert(/api\.humans\?\.setSeason\?\.\(s\)/.test(main) && /api\.humans\.setSeason\?\.\(api\.season/.test(main), 'main.js hands the layer the season');
}

// 3. The ladies' hats, on test_human_town_dress's synthetic head.
{
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
    return root;
  }
  assert.deepEqual([...LADY_HATS], ['picture', 'sailor', 'toque']);
  const trim = { plumes: { n: 2, rgb: [.6, .6, .6] }, flowers: { n: 6, rgb: [.6, .3, .3] }, bow: { rgb: [.1, .1, .3] } };
  const sizes = {};
  for (const kind of LADY_HATS) {
    const root = figure();
    const done = dressHat(root, { kind, rgb: [.5, .4, .25], band: [.02, .02, .02], trim }, { person: kind, lod: 0 });
    assert(done, `${kind} made`);
    const box = new THREE.Box3().setFromObject(done.mesh);
    sizes[kind] = box.max.x - box.min.x;
    const trims = done.mesh.parent.children.filter((o) => /^accessory__.*_hat_trim_t3553$/.test(o.material?.name ?? ''));
    assert.equal(trims.length, 1, `${kind}: one trimming mesh`);
    assert(trims[0].geometry.attributes.color && trims[0].material.vertexColors, `${kind}: plumes, flowers and bow in their own colours`);
    assert(trims[0].geometry.attributes.position.count > 300, `${kind}: plumes and flowers drawn`);
    assert(box.min.y - root.position.y > 1.6, `${kind}: above the brow (${(box.min.y - root.position.y).toFixed(3)})`);
  }
  assert(sizes.picture > sizes.sailor + .05 && sizes.sailor > sizes.toque, `a picture hat is the widest, a toque has no brim: ${JSON.stringify(sizes)}`);
  assert.equal(hatSpec({ kind: 'toque', rgb: [0, 0, 0], brim_m: .2 }).brim, 0, 'a toque has no brim');
  assert.equal(hatSpec({ kind: 'picture', rgb: [0, 0, 0], brim_m: .9 }).brim, .17, 'a picture hat held to 17 cm of brim');
  assert.equal(hatSpec({ kind: 'round', rgb: [0, 0, 0] }).trim, null, 'a man\'s hat of 1812 takes no trimming');
}

// 4. The Prairie Avenue women.
const prairie = (await read('data/humans/variation/dress_1904_prairie.json')).persons;
const persons = (await read('assets/humans/web/hm08_variation_persons.json')).persons;
const sources = new Set((await fs.readdir(new URL('data/sources/', here))).map((f) => f.replace(/\.json$/, '')));
// A stand-in portrait's own dress (the Greys, T-3553) is hers all year, without dealt finery.
const own = Object.entries(prairie).filter(([, r]) => r.asset === 'glessner_frances_m_1904' && /stand-in portrait/.test(r.worn));
assert(own.length >= 1 && own.every(([, r]) => !r.finery && !r.seasons && r.hat), 'a stand-in wears her portrait\'s dress all year, in a made hat');
const ladies = Object.entries(prairie).filter(([, r]) => r.asset === 'glessner_frances_m_1904' && !/stand-in portrait/.test(r.worn));
assert(ladies.length >= 90, `ladies: ${ladies.length}`);
const seen = new Map(), kinds = new Set(), hats = new Set(), figures = new Set(), trimsSeen = new Set();
for (const [pid, rec] of ladies) {
  assert(rec.grade === 'reconstructed' && rec.liberty === 'L-finery-3553' && rec.sources.length, `${pid}: graded and sourced`);
  for (const s of rec.sources) assert(sources.has(s), `${pid}: ${s} is a source record`);
  for (const season of [null, 'spring', 'fall', 'winter']) {
    const d = season ? rec.seasons[season] : rec;
    assert(d && d.finery && d.hat && d.worn, `${pid} ${season ?? 'summer'}: finery, hat and words`);
    assert(LADY_HATS.includes(d.hat.kind), `${pid}: a lady's hat`);
    assert(['headwear_lady_hat', 'lady_hat_plumes'].every((h) => d.hide.includes(h)), `${pid}: the body's own hat off under the made one`);
    hats.add(d.hat.kind);
    for (const f of Object.values(d.finery)) {
      if (f.pattern) figures.add(f.pattern.kind);
      for (const t of f.trims ?? []) trimsSeen.add(t.kind);
      assert(finerySpec(f), `${pid}: every garment's finery draws`);
    }
    kinds.add(d.worn.split(';')[0].replace(/^an? [a-z-]+ /, '').split(',')[0]);
  }
  const key = JSON.stringify([rec.colours, rec.finery, rec.hat]);
  assert(!seen.has(key), `${pid} is dressed exactly as ${seen.get(key)}`);
  seen.set(key, pid);
  const p = persons[pid]?.dress;
  assert(p && JSON.stringify(p.finery) === JSON.stringify(rec.finery) && JSON.stringify(p.seasons) === JSON.stringify(rec.seasons), `${pid}: the persons file carries the dress`);
}
assert.deepEqual([...hats].sort(), ['picture', 'sailor', 'toque'], 'every kind of hat is worn');
for (const t of ['lace', 'ribbon', 'braid', 'tucks', 'flounce', 'jet']) assert(trimsSeen.has(t), `someone's dress is trimmed with ${t}`);
assert(figures.size >= 4, `figured cloths: ${[...figures]}`);
const summers = new Set(ladies.map(([, r]) => r.colours['garment_outer__lady_jacket_black'].join()));
assert(summers.size >= 15, `summer colours: ${summers.size}`);
const cooks = Object.values(prairie).filter((r) => r.asset === 'ryan_kate_1904_cook');
assert(cooks.length && cooks.every((r) => r.finery.garment_upper__cook_print_dress.pattern && r.finery.garment_outer__cook_apron_check.pattern.kind === 'check'), 'the cook\'s print is a print, her checked apron a check');

// 5. 1812: the records' own words, drawn.
let drawn1812 = 0;
for (const f of ['dress_1812_town', 'dress_1812_native', 'dress_1812_children', 'dress_1812_garrison']) {
  for (const [pid, rec] of Object.entries((await read(`data/humans/variation/${f}.json`)).persons)) {
    const fin = persons[pid]?.dress?.finery;
    const says = /\b(calico|print|sprigged|check(ed)?|strip(ed|e)|ticking)\b/.test((rec.worn ?? '').split('; ').filter((w) => !/handkerchief/.test(w)).join('; '));
    if (!fin) continue;
    assert(says, `${pid}: a figure only where the words name one`);
    drawn1812++;
    for (const [mat, g] of Object.entries(fin)) {
      const c = rec.colours[mat];
      assert(c, `${pid}: ${mat} is a garment the record colours`);
      const mean = { check: .5, stripe: .5, pinstripe: .12, sprig: .16 }[g.pattern.kind];
      const m = g.ground.map((x, i) => x * (1 - mean) + g.pattern.rgb[i] * mean);
      assert(m.every((x, i) => Math.abs(x - c[i]) < .06), `${pid} ${mat}: the figure's mean is the record's colour (${m.map((x) => x.toFixed(2))} vs ${c})`);
    }
  }
}
assert(drawn1812 >= 500, `1812 people whose calico, check or stripes are drawn: ${drawn1812}`);
hooks.deregister();
console.log(`finery: ${ladies.length} Prairie ladies each her own in three seasons (${[...hats].join(', ')} hats; ${[...figures].join(', ')}), cooks in print, ${drawn1812} people of 1812 in their recorded figures: PASS`);
