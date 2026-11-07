// SPDX-License-Identifier: GPL-3.0-or-later
// T-3491: each man of Heald's company looks like himself. It must: give every 1812 private a
// looks row (complexion, hair, eyes, stature, a stand-in portrait that exists), graded, with
// his own seed; spread them (no colouring held by most of the company; heights about the
// period's 68.1 in with its spread; Grummo tall); draw them (human-looks.js tints a CLONE of
// the skin and the iris, leaving the shared material alone, and gives up nothing unknown); and
// put them on his card (person-card.js `looksOf`: the register's words, height, a stand-in
// portrait labelled as one).
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const three = new URL('three.core.js', vendor).href;
const THREE = await import(three);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const js = async (name) => (await fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8')).replace("from 'three'", `from '${three}'`);
const { dressLooks, disposeLooks, looksHairStyle, COMPLEXION_TINT, EYE_COLOUR } = await import(data(await js('human-looks.js')));
const { HAIR_COLOURS, HAIR_CUTS, FACIAL_HAIR } = await import('../renderers/web/js/human-hair-styles.js');
const { looksOf } = await import('../renderers/web/js/person-card.js');

const persons = JSON.parse(await fs.readFile(new URL('assets/humans/web/hm08_variation_persons.json', here), 'utf8')).persons;
const dir = new URL('data/humans/instances/1812/', here);
const index = JSON.parse(await fs.readFile(new URL('index.json', dir), 'utf8'));
const privates = [];
for (const id of index.instances) {
  const r = JSON.parse(await fs.readFile(new URL(`${id}.json`, dir), 'utf8'));
  if (r.appearance.asset_id === 'private_first_infantry_1812') privates.push(r.person_id);
}
assert(privates.length >= 51, `the company stands (${privates.length})`);
const combos = new Map(), heights = [];
for (const pid of privates) {
  const L = persons[pid]?.looks;
  assert(L, `${pid} has looks`);
  assert(COMPLEXION_TINT[L.complexion.drawn] && EYE_COLOUR[L.eyes.drawn] && HAIR_COLOURS[L.hair.drawn], `${pid}: every drawn word is drawable`);
  assert(HAIR_CUTS[L.hair.cut] && L.hair.facial.every((f) => FACIAL_HAIR[f]), `${pid}: his cut and whiskers exist`);
  assert(['attested', 'inferred', 'reconstructed'].includes(L.grade) && L.liberty === 'L-1812-garrison-looks-3491' && L.basis, `${pid}: graded, with its liberty and basis`);
  await fs.access(new URL(`assets/${L.reference.image}`, here));
  assert(/stand-in/i.test(L.reference.why) && /not his likeness/.test(L.reference.why), `${pid}: the portrait is labelled a stand-in`);
  const key = `${L.complexion.value}|${L.hair.value}|${L.eyes.value}`;
  combos.set(key, (combos.get(key) ?? 0) + 1);
  heights.push(L.stature.inches);
}
const most = Math.max(...combos.values());
assert(combos.size >= 25 && most <= 6, `the company is varied: ${combos.size} colourings, the commonest worn by ${most}`);
for (const field of ['complexion', 'hair', 'eyes']) {
  const vals = new Set(privates.map((p) => persons[p].looks[field].value));
  assert(vals.size >= 4, `${field}: ${[...vals]}`);
}
const mean = heights.reduce((a, b) => a + b, 0) / heights.length;
const sd = Math.sqrt(heights.reduce((a, b) => a + (b - mean) ** 2, 0) / heights.length);
assert(Math.abs(mean - 68.4) < 1.2 && sd > 1.8 && sd < 3.4, `heights about the period's (mean ${mean.toFixed(1)} in, sd ${sd.toFixed(2)})`);
assert(persons.grummo_paul.looks.stature.inches >= 71 && persons.grummo_paul.looks.stature.grade === 'inferred' && persons.grummo_paul.looks.build, 'Grummo is tall and well built (inferred)');
assert.equal(persons.kennison_david.looks.stature.inches, 70, 'Kennison at about five feet ten');

// Drawing: a clone is tinted, the shared material is left alone.
const skin = new THREE.MeshStandardMaterial({ name: 'skin', color: 0xffffff });
const iris = new THREE.MeshStandardMaterial({ name: 'eyes__iris', color: 0xffffff, map: new THREE.Texture() });
const coat = new THREE.MeshStandardMaterial({ name: 'garment_upper__coat_blue_1812' });
const root = new THREE.Group();
for (const m of [skin, iris, coat]) root.add(new THREE.Mesh(new THREE.BufferGeometry(), m));
root.add(new THREE.Mesh(new THREE.BufferGeometry(), [skin, coat]));
const looks = persons.grummo_paul.looks;
const made = dressLooks(root, looks);
assert.equal(made.length, 2, 'one skin clone and one iris clone, shared across the meshes that wore them');
const meshes = root.children;
assert(meshes[0].material !== skin && meshes[0].material === meshes[3].material[0], 'the skin is a clone, one per body');
assert(meshes[2].material === coat && meshes[3].material[1] === coat, 'clothes are untouched');
assert.deepEqual(skin.color.toArray(), [1, 1, 1], 'the shared skin keeps its colour');
const t = COMPLEXION_TINT[looks.complexion.drawn];
assert(meshes[0].material.color.toArray().every((v, i) => Math.abs(v - t[i]) < 1e-6), 'the clone carries his complexion');
assert(meshes[1].material.map === null && iris.map !== null, 'his iris is drawn in his own colour, the shared one keeps its picture');
assert.deepEqual(dressLooks(root, { complexion: { drawn: 'unknown' } }), [], 'nothing unknown is drawn');
disposeLooks(made);
const style = looksHairStyle(looks, { cut: 'brushed_forward_1835', facial: ['brows_fine'], colour: 'mid_brown' });
assert(style.colour === looks.hair.drawn && style.cut === 'cropped_1812' && style.facial.includes('brows_fine'), 'his hair: his colour and crop, the brows kept');

// The card.
const card = looksOf(looks, 'https://example.org/data/');
const rows = Object.fromEntries(card.rows);
assert(rows.Complexion === looks.complexion.value && rows.Eyes === looks.eyes.value && /^about \d ft \d+ in$/.test(rows.Height), `card rows: ${JSON.stringify(rows)}`);
assert(card.reference.image.startsWith('https://example.org/data/humans/web/portraits/') && card.reference.caption.includes(looks.reference.artist), 'the stand-in portrait, by its artist');
assert.equal(looksOf(null), null, 'no looks, no section');
console.log(`human looks: ${privates.length} men, ${combos.size} colourings (commonest ${most}), heights ${mean.toFixed(1)} ± ${sd.toFixed(1)} in, Grummo ${persons.grummo_paul.looks.stature.inches} in: PASS`);
