#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * test_visitor_person.mjs — the visitor's own person (T-3644).
 *
 * Holds data/humans/visitor_person.json to the tables the renderer draws with (every body
 * published at every level, every cut, whisker, hair colour, complexion and eye colour one the
 * people layer knows, every outfit's body one test_riding seats), and visitor-person.js to its
 * contract: a stored choice is brought to one the catalog can draw, each year's dress is kept
 * per sex, the record carries what humans.js and human-variation.js read, a chosen library
 * face is the face drawn (libraryFace `pick`), the Firestore write names only the fields
 * docs/SIGN-IN.md's rule allows, and the newer of the device's and the account's choice wins.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { registerHooks } from 'node:module';

const here = new URL('../', import.meta.url);
const read = (rel) => fs.readFileSync(new URL(rel, here), 'utf8');
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here).href;
const hooks = registerHooks({ resolve: (s, c, next) => s === 'three' ? { url: vendor + 'three.module.js', shortCircuit: true }
  : s.startsWith('three/addons/') ? { url: vendor + 'addons/' + s.slice(13), shortCircuit: true } : next(s, c) });
const P = await import('../renderers/web/js/visitor-person.js');
const { HAIR_CUTS, FACIAL_HAIR, HAIR_COLOURS } = await import('../renderers/web/js/human-hair-styles.js');
const { COMPLEXION_TINT, EYE_COLOUR } = await import('../renderers/web/js/human-looks.js');
const V = await import('../renderers/web/js/human-variation.js');
const { SETTINGS_TABS } = await import('../renderers/web/js/settings-app.js');
const { facesFor, swatchColour } = await import('../renderers/web/js/person-settings.js');
hooks.deregister();

let n = 0;
const ok = (c, m) => { assert.ok(c, m); n++; };
const catalog = JSON.parse(read('data/humans/visitor_person.json'));
const kit = JSON.parse(read('assets/humans/web/hm08_variation_kit.json'));
catalog.faces = { ...kit.faces, base: 'https://example.invalid/humans/web/' };
const riding = JSON.parse(read('data/transport/riding/saddle_horses.json'));

// --- the catalog against the renderer's own tables
ok(catalog.format === 'chicago4d_visitor_person_v1' && catalog.liberty && catalog.grade === 'reconstructed', 'the catalog says what it is and its liberty');
ok(read('docs/LIBERTIES.md').includes(catalog.liberty), `${catalog.liberty} is in docs/LIBERTIES.md`);
for (const c of catalog.complexions) ok(COMPLEXION_TINT[c.id], `complexion ${c.id} is one human-looks.js tints`);
for (const e of catalog.eyes) ok(EYE_COLOUR[e.id], `eyes ${e.id} are a colour human-looks.js draws`);
for (const h of catalog.hair_colours) ok(HAIR_COLOURS[h.id], `hair colour ${h.id} is one human-hair-styles.js draws`);
for (const s of catalog.sexes.map((x) => x.id)) {
  for (const f of catalog.facial[s] ?? []) for (const w of f.wears) ok(FACIAL_HAIR[w], `${s} ${f.id}: ${w} is grown by human-hair.js`);
  for (const b of catalog.brows[s] ?? []) ok(FACIAL_HAIR[b], `${s} brows ${b}`);
}
// test_riding seats every body the visitor may choose (its assetsOf reads this catalog).
ok(read('tools/test_riding.mjs').includes('data/humans/visitor_person.json'), 'test_riding seats the visitor\'s own bodies');
for (const y of catalog.years) {
  for (const s of catalog.sexes.map((x) => x.id)) {
    const cuts = catalog.cuts[y]?.[s] ?? [], outfits = catalog.outfits[y]?.[s] ?? [];
    ok(cuts.length && outfits.length, `${y} ${s}: at least one cut and one dress`);
    for (const c of cuts) ok(HAIR_CUTS[c.id], `${y} ${s}: cut ${c.id} is one human-hair-styles.js grows`);
    for (const o of outfits) {
      for (const l of [0, 1, 2, 3]) ok(fs.existsSync(new URL(`assets/humans/web/${o.asset}.lod${l}.glb`, here)), `${y} ${s} ${o.id}: ${o.asset} at level ${l}`);
      const a = kit.assets[o.asset];
      ok(a && (a.sex === s), `${y} ${s} ${o.id}: ${o.asset} is a ${s} body the variation kit knows`);
      ok(kit.faces.bodies[o.asset], `${y} ${s} ${o.id}: the face library fits ${o.asset}`);
      ok(o.worn && o.label, `${y} ${s} ${o.id}: says what is worn`);
    }
  }
}

// --- a choice
const d = P.normalChoice(null, catalog);
ok(d.sex === 'male' && d.complexion === catalog.defaults.complexion && d.face === 'auto' && d.v === P.CHOICE_VERSION, 'nothing stored: the default person');
ok(P.personAsset(d, '1812', catalog) === riding.rider.assets['1812'] && P.personAsset(d, '1904', catalog) === riding.rider.assets['1904'],
  'the default person wears the figure that rode before the choice existed');
const junk = P.normalChoice({ sex: 'robot', complexion: 'green', face: 'nobody', years: { 1812: { male: { outfit: 'tuxedo' } } }, builder: { hat: 'x' } }, catalog);
ok(junk.sex === 'male' && junk.complexion === catalog.defaults.complexion && junk.face === 'auto' && junk.years['1812'].male.outfit === catalog.outfits['1812'].male[0].id,
  'a stored choice the catalog cannot draw is brought to one it can');
ok(junk.builder?.hat === 'x', 'a later builder\'s own fields are carried through');

// The store, on a pretend device.
const box = new Map();
const storage = { getItem: (k) => box.get(k) ?? null, setItem: (k, v) => box.set(k, v) };
let t = 0;
const person = P.createVisitorPerson({ catalog, storage, now: () => `2026-11-17T00:00:${String(t++).padStart(2, '0')}Z` });
let told = 0; person.onChange(() => told++);
person.set({ sex: 'female' });
person.set({ outfit: 'country' }, '1812');
person.set({ sex: 'male' });
ok(person.choice.sex === 'male' && person.asset('1812') === 'settler_1812', 'back to a man: his own clothes');
person.set({ sex: 'female' });
ok(person.asset('1812') === 'woman_country_1812' && person.asset('1904') === catalog.outfits['1904'].female[0].asset, 'each year\'s dress is kept per sex');
ok(told === 4 && JSON.parse(box.get(catalog.storage_key)).years['1812'].female.outfit === 'country', 'every change is told and kept on the device');
const again = P.createVisitorPerson({ catalog, storage });
ok(again.choice.sex === 'female' && again.asset('1812') === 'woman_country_1812', 'the next visit is the same person');

// --- the record the people layer reads
person.set({ complexion: 'deep_brown', hair_colour: 'black', age: 'young', eyes: 'dark_brown' });
const rec = person.record('1812');
ok(rec.sex === 'female' && rec.age.years === 25 && rec.looks.complexion.drawn === 'deep_brown' && rec.looks.eyes.drawn === 'dark_brown', 'the record carries sex, age, complexion and eyes');
ok(rec.looks.hair.drawn === 'black' && HAIR_CUTS[rec.looks.hair.cut] && rec.looks.hair.facial.includes('brows_fine'), 'and the hair: colour, the year\'s cut and her brows');
ok(rec.looks.grade === 'reconstructed' && rec.looks.liberty === catalog.liberty, 'graded reconstructed, with its liberty');
const faces = facesFor(catalog, 'female', 'deep_brown');
ok(faces.length >= 4 && faces.every((f) => f.sex === 'female' && !f.light_only), 'her faces: the library\'s women\'s, no freckled face for a dark complexion');
ok(facesFor(catalog, 'male', 'fair').some((f) => f.light_only), 'a fair man may choose a freckled face');
person.set({ face: faces[2].id });
ok(person.choice.face === faces[2].id, 'a face of hers is kept');
person.set({ complexion: 'deep_brown', face: 'toigo_freckles_female' });
ok(person.choice.face === 'auto', 'a freckled face is refused on a dark complexion (the library\'s own rule)');
person.set({ face: faces[2].id });

// --- the chosen face is the face drawn
const binBytes = fs.readFileSync(new URL(`assets/humans/web/${kit.bin}`, here));
const based = { ...V.parseVariationKit(kit, binBytes.buffer.slice(binBytes.byteOffset, binBytes.byteOffset + binBytes.byteLength)), base: 'https://example.invalid/humans/web/' };
const asset = person.asset('1812');
const pv = V.personVariation({ kit: based, key: P.VISITOR_PERSON_ID, record: person.record('1812'), assetId: asset, sceneYear: 1812 });
ok(pv.lib?.id === faces[2].id && pv.sex === 'female' && pv.age === 25, 'personVariation wears the face she chose, her sex and her age');
ok(V.libraryFace(based, { key: 'k', assetId: asset, sex: 'female', age: 30, pick: 'body' }) === null, 'pick "body": the body\'s own skin');
const seeded = V.libraryFace(based, { key: 'someone', assetId: asset, sex: 'female', age: 30, complexion: 'light' });
ok(V.libraryFace(based, { key: 'someone', assetId: asset, sex: 'female', age: 30, complexion: 'light', pick: null })?.id === seeded?.id, 'no pick: everyone else\'s face is drawn as before');

// --- keeping it with the account
const w = P.personWrite({ projectId: 'p', uid: 'u1', choice: person.choice })[0];
const fields = [...Object.keys(w.update.fields), ...w.updateTransforms.map((x) => x.fieldPath)];
const rules = read('docs/SIGN-IN.md');
const m = rules.match(/match \/people\/\{uid\}[\s\S]*?hasOnly\(\[([^\]]*)\]\)/);
ok(m, 'docs/SIGN-IN.md carries the people/<uid> rule');
const allowed = m[1].split(',').map((s) => s.trim().replace(/'/g, ''));
ok(fields.every((f) => allowed.includes(f)) && w.update.name.endsWith('/documents/people/u1'), `the write names only the rule's fields (${fields})`);
ok(JSON.stringify(person.choice).length < 4000, 'a choice fits the rule\'s 4000 characters');
ok(P.newer({ saved: '2026-11-17T01:00:00Z', a: 1 }, { saved: '2026-11-17T02:00:00Z', a: 2 }).a === 2 && P.newer({ saved: 'x', a: 1 }, { saved: '' }).a === 1, 'the newer choice wins');

// The account round trip, against a pretend Firestore.
const cloud = {};
const fetchFn = async (url, init = {}) => {
  if (init.method === 'POST') { const body = JSON.parse(init.body); cloud.doc = body.writes[0].update.fields; return { ok: true, status: 200 }; }
  return cloud.doc ? { ok: true, status: 200, json: async () => ({ fields: cloud.doc }) } : { ok: false, status: 404 };
};
const account = { uid: 'u1', idToken: async () => 'tok' };
const home = P.createVisitorPerson({ catalog, storage, account, fetchFn, projectId: 'p', now: () => '2026-11-17T05:00:00Z' });
home.set({ sex: 'male', complexion: 'brown' });
await new Promise((r) => setTimeout(r, 0));
ok(cloud.doc && JSON.parse(cloud.doc.person.stringValue).complexion === 'brown', 'a signed-in visitor\'s choice goes to their account');
const box2 = new Map();
const phone = P.createVisitorPerson({ catalog, storage: { getItem: (k) => box2.get(k) ?? null, setItem: (k, v) => box2.set(k, v) }, account, fetchFn, projectId: 'p' });
await phone.sync();
ok(phone.choice.complexion === 'brown' && phone.choice.sex === 'male', 'and comes back on another device');

// --- the Settings card
ok(SETTINGS_TABS.includes('you') && SETTINGS_TABS.indexOf('you') === 1, 'the Settings card has a You tab, second');
const html = read('renderers/web/index.html');
ok(/id="s-you" data-set-pane="you"/.test(html) && html.includes('id="s-person"'), 'its group is in the page');
ok(/^rgb\(\d+, \d+, \d+\)$/.test(swatchColour(COMPLEXION_TINT.deep_brown)), 'complexion swatches are drawn colours');
const main = read('renderers/web/js/main.js');
ok(main.includes("import('./visitor-person.js')") && main.includes('wirePersonSettings('), 'main.js mounts the person and its tab');

console.log(`visitor person (T-3644): ${n} checks PASS`);
