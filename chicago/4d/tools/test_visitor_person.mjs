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
const { facesFor, swatchColour, personHost, FACE_TURNS } = await import('../renderers/web/js/person-settings.js');
const ridingCode = await import('../renderers/web/js/riding.js');
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
// Body types (Kevin, 2026-11-19): named for the person's style, not their gender, and a third.
ok(catalog.body_label && !/gender|sex/i.test(catalog.body_label) && !/'Gender'/.test(read('renderers/web/js/person-settings.js')), `the control is "${catalog.body_label}", not "Gender"`);
ok(catalog.sexes.length >= 3 && catalog.sexes.every((t) => !/^(man|woman|male|female)$/i.test(t.label)), `three body types: ${catalog.sexes.map((t) => t.label).join(', ')}`);
const bodies = ['male', 'female'];
for (const t of catalog.sexes) {
  ok(P.bodiesOf(catalog, t.id).every((b) => bodies.includes(b)), `${t.id}: worn on the bodies the town draws`);
  for (const [b, build] of Object.entries(t.build ?? {})) {
    ok(bodies.includes(b) && Object.entries(build).every(([k, v]) => kit.axes.some((a) => a.id === k && a.scope === 'full') && Math.abs(v) <= kit.limit),
      `${t.id} on a ${b} body: its build is the kit's own axes, within its limit`);
  }
}
for (const y of catalog.years) {
  for (const s of catalog.sexes.map((x) => x.id)) {
    const cuts = P.wardrobe(catalog, 'cuts', y, s), outfits = P.wardrobe(catalog, 'outfits', y, s);
    ok(cuts.length && outfits.length, `${y} ${s}: at least one cut and one dress`);
    ok(new Set(outfits.map((o) => o.id)).size === outfits.length && new Set(cuts.map((o) => o.id)).size === cuts.length, `${y} ${s}: no two dresses or cuts share an id`);
    for (const c of cuts) ok(HAIR_CUTS[c.id], `${y} ${s}: cut ${c.id} is one human-hair-styles.js grows`);
    for (const o of outfits) {
      for (const l of [0, 1, 2, 3]) ok(fs.existsSync(new URL(`assets/humans/web/${o.asset}.lod${l}.glb`, here)), `${y} ${s} ${o.id}: ${o.asset} at level ${l}`);
      const a = kit.assets[o.asset];
      ok(a && (a.sex === o.body), `${y} ${s} ${o.id}: ${o.asset} is a ${o.body} body the variation kit knows`);
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
// A riding habit (Kevin, 2026-11-18): a dress worn on its body, carried in the record for humans.js.
ok(!rec.dress, 'a dress worn as drawn carries no dress of its own');
person.set({ outfit: 'riding_habit' }, '1835');
ok(person.record('1835').dress?.hat && person.asset('1835') === 'flynn_mary_1835_dress_study' && person.record('1835').dress.hide.includes('separate_plain_apron'),
  'the 1835 riding habit: her dress in its own cloth, the apron set aside, a hat of its own');
ok(catalog.outfits['1904'].female.some((o) => o.id === 'riding_habit' && o.dress?.hat) && !catalog.outfits['1812'].female.some((o) => o.id === 'riding_habit'),
  'a riding habit in 1835 and 1904 (1812 rides astride in her own dress)');
person.set({ outfit: 'plain' }, '1835');
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

// --- the third body type (Kevin, 2026-11-19): either body's dress and hair, any face, its own build
{
  const box3 = new Map();
  const them = P.createVisitorPerson({ catalog, storage: { getItem: (k) => box3.get(k) ?? null, setItem: (k, v) => box3.set(k, v) } });
  them.set({ sex: 'neutral' });
  const dress = P.wardrobe(catalog, 'outfits', '1904', 'neutral');
  ok(['male', 'female'].every((b) => dress.some((o) => o.body === b)), 'Androgynous: the year\'s dresses of both bodies to choose among');
  them.set({ outfit: 'riding_habit' }, '1904');
  const r1 = them.record('1904');
  ok(r1.sex === 'female' && r1.body_type === 'neutral' && them.asset('1904') === 'nelson_christine_1904_errand' && r1.looks.build?.muscle > 0,
    'in the riding habit: drawn on its body, with the type\'s own build');
  ok(ridingCode.sideSaddleFor(riding, '1904', r1) === riding.side_saddle.tack['1904'], 'and rides aside, as a skirt does');
  them.set({ outfit: 'working' }, '1904');
  const r2 = them.record('1904');
  ok(r2.sex === 'male' && them.asset('1904') === 'anonymous_working_driver_1904' && r2.looks.build?.muscle < 0, 'in working clothes: a man\'s frame, drawn leaner');
  ok(ridingCode.sideSaddleFor(riding, '1904', r2) === null, 'and rides astride');
  const theirFaces = facesFor(catalog, 'neutral', 'light');
  ok(['male', 'female'].every((b) => theirFaces.some((f) => f.sex === b)), 'any of the library\'s faces');
  them.set({ face: theirFaces.find((f) => f.sex === 'female').id });
  const pv2 = V.personVariation({ kit: based, key: P.VISITOR_PERSON_ID, record: them.record('1904'), assetId: them.asset('1904'), sceneYear: 1904 });
  ok(pv2.lib?.id === them.choice.face && pv2.sex === 'male', 'a woman\'s face of the library on a man\'s frame, as chosen');
  them.set({ sex: 'female' });
  ok(them.asset('1904') === catalog.outfits['1904'].female[0].asset && !them.record('1904').body_type && !them.record('1904').looks.build, 'Feminine keeps its own dress, and no build of the third type');
  them.set({ sex: 'neutral' });
  ok(them.asset('1904') === 'anonymous_working_driver_1904', 'and back: the third type\'s own dress again');
}

// --- T-3756 (Kevin, 2026-11-26): Style 1/2/3, and Style 3 not the same as Style 1
{
  ok(catalog.sexes.map((x) => x.label).join() === 'Style 1,Style 2,Style 3' && catalog.body_label === 'Body style',
    'the body types read Style 1, Style 2 and Style 3, under "Body style"');
  ok(!/masculine|feminine|androgynous|gender/i.test(JSON.stringify(catalog.sexes.map((x) => x.label)) + catalog.body_label), 'no gendered word on the control');
  const fresh = (sex) => {
    const box = new Map();
    const p = P.createVisitorPerson({ catalog, storage: { getItem: (k) => box.get(k) ?? null, setItem: (k, v) => box.set(k, v) } });
    p.set({ sex });
    return p;
  };
  const one = fresh('male'), three = fresh('neutral');
  for (const y of catalog.years) {
    const a = P.yearChoice(one.choice, y, catalog), b = P.yearChoice(three.choice, y, catalog);
    const start = catalog.sexes.find((x) => x.id === 'neutral').start?.[y];
    ok(start && b.outfit?.id === start.outfit && b.cut?.id === start.cut, `${y}: Style 3 opens in its own start look`);
    ok(a.outfit?.id !== b.outfit?.id && a.cut?.id !== b.cut?.id, `${y}: Style 3's first dress and hair are not Style 1's`);
  }
  const r3 = three.record('1835'), r1 = one.record('1835');
  ok(r3.looks.face_of === 'female' && !r1.looks.face_of, 'an Auto face for Style 3 on a man\'s frame is drawn from the other faces; Style 1 has no such field');
  const auto3 = V.personVariation({ kit: based, key: P.VISITOR_PERSON_ID, record: r3, assetId: three.asset('1835'), sceneYear: 1835 });
  const auto1 = V.personVariation({ kit: based, key: P.VISITOR_PERSON_ID, record: r1, assetId: one.asset('1835'), sceneYear: 1835 });
  const sexOf = (id) => based.header.faces.faces.find((f) => f.id === id)?.sex;
  ok(auto3.lib && sexOf(auto3.lib.id) === 'female', 'Style 3\'s Auto face is one of the other body\'s faces, never the body\'s own (Style 1\'s)');
  ok(!auto1.lib || sexOf(auto1.lib.id) === 'male', 'Style 1\'s Auto face is drawn as before');
  three.set({ face: facesFor(catalog, 'neutral', 'light').find((f) => f.sex === 'male').id });
  ok(!three.record('1835').looks.face_of, 'a face chosen by hand is worn as chosen');
}

// --- T-3553 (Kevin, 2026-11-27): the face library by type, the photographed faces the town wears
{
  const runtimeURL = new URL('assets/humans/web/photo_faces/pilot/runtime.json', here);
  const runtime = JSON.parse(read('assets/humans/web/photo_faces/pilot/runtime.json'));
  const lib = { ...catalog, photoFaces: P.photoCatalog(runtime, new URL('https://example.invalid/humans/web/photo_faces/pilot/runtime.json')) };
  ok(lib.photoFaces.faces.length === runtime.faces.length && lib.photoFaces.thumbs.url.endsWith('/photo_faces/pilot/thumbs.jpg'), 'the You tab keeps every photographed face and its picture sheet');
  // The sheet tools/photo_face_thumbs.py writes is the size photoCatalog lays it out at.
  const jpg = fs.readFileSync(new URL('assets/humans/web/photo_faces/pilot/thumbs.jpg', here));
  let at = 2, size = null;
  while (at < jpg.length && !size) { const mark = jpg[at + 1], len = jpg.readUInt16BE(at + 2); if (mark >= 0xc0 && mark <= 0xc2) size = [jpg.readUInt16BE(at + 7), jpg.readUInt16BE(at + 5)]; at += 2 + len; }
  ok(size && size.join() === lib.photoFaces.thumbs.size_px.join(), `thumbs.jpg is ${size} as laid out`);
  for (const type of ['male', 'female', 'neutral']) {
    const groups = P.faceGroups(lib, type, 'light');
    const photo = groups.filter((g) => g.kind === 'photo'), ids = groups.flatMap((g) => g.bands.flatMap((b) => b.faces.map((f) => f.id)));
    ok(photo.map((g) => g.id).join() === catalog.ages.map((a) => a.id).join() && groups.at(-1).id === 'painted', `${type}: a type for each age (${photo.map((g) => `${g.label} ${g.count}`).join(', ')}), then the painted faces`);
    ok(new Set(ids).size === ids.length && photo.reduce((a, g) => a + g.count, 0) === P.photoFaceChoices(lib, type).length, `${type}: every face once`);
    ok(groups.every((g) => !/\b(men|women|man|woman|male|female|masculine|feminine)\b/i.test(g.label + g.bands.map((b) => b.label).join())), `${type}: no type named for a sex`);
    ok(photo.every((g) => g.bands.every((b) => b.faces.every((f, k, a) => !k || P.faceTone(a[k - 1]) >= P.faceTone(f)))), `${type}: lighter to deeper within each band`);
    const wears = P.bodiesOf(catalog, type);
    ok(P.photoFaceChoices(lib, type).every((f) => wears.includes(f.sex) && f.age >= 18), `${type}: the adults of the bodies it wears`);
  }
  ok(P.faceGroupOf(P.faceGroups(lib, 'male', 'light'), 'auto', 'older') === 'older', 'on Auto the library opens at the person\'s own age');
  // A photographed face chosen is kept, and is the face drawn (human-variation.js photoFaceFor `pick`).
  const box4 = new Map();
  const me = P.createVisitorPerson({ catalog: lib, storage: { getItem: (k) => box4.get(k) ?? null, setItem: (k, v) => box4.set(k, v) } });
  me.set({ sex: 'female', eyes: 'blue', age: 'young' });
  const hers = P.faceGroups(lib, 'female', 'light')[2].bands[0].faces[0];
  me.set({ face: hers.id });
  ok(me.choice.face === hers.id, 'a photographed face of hers is kept');
  me.set({ face: P.photoFaceChoices(lib, 'male')[0].id });
  ok(me.choice.face === 'auto', 'one of the other body\'s faces is not hers to keep (Style 2)');
  me.set({ face: hers.id });
  const photoKit = { ...based };
  ok(V.attachPhotoLibrary(photoKit, runtime, runtimeURL), 'the library attaches as the walk attaches it');
  const rec4 = me.record('1904');
  ok(rec4.looks.eyes.chosen === true && rec4.looks.face_pick === hers.id, 'the record carries the chosen face, and eyes marked chosen');
  const pv4 = V.personVariation({ kit: photoKit, key: P.VISITOR_PERSON_ID, record: rec4, assetId: me.asset('1904'), sceneYear: 1904 });
  ok(pv4.photoFace?.id === hers.id && pv4.lib?.id === hers.id, 'personVariation wears the photographed face she chose, though she is young and it is older');
  ok(read('renderers/web/js/humans.js').includes('looks?.eyes?.chosen === true'), 'a chosen eye colour is worn over the photograph\'s own iris (humans.js, after dressPhotoLooks)');
  // A painted face chosen keeps the photographs off her; Auto draws one as for anyone.
  me.set({ face: P.faceGroups(lib, 'female', 'light').at(-1).bands[0].faces[0].id });
  const pv5 = V.personVariation({ kit: photoKit, key: P.VISITOR_PERSON_ID, record: me.record('1904'), assetId: me.asset('1904'), sceneYear: 1904 });
  ok(!pv5.photoFace && pv5.lib?.id === me.choice.face, 'a painted face chosen is the painted face');
  me.set({ face: 'auto' });
  const pv6 = V.personVariation({ kit: photoKit, key: P.VISITOR_PERSON_ID, record: me.record('1904'), assetId: me.asset('1904'), sceneYear: 1904 });
  ok(pv6.photoFace && pv6.photoFace.sex === 'female', 'Auto: a photographed face drawn for her, as for anyone of the town');
  // Style 3 on Auto: the other body's photographed faces too (T-3756's rule, kept under the photographs).
  me.set({ sex: 'neutral' });
  const r7 = me.record('1835');
  const pv7 = V.personVariation({ kit: photoKit, key: P.VISITOR_PERSON_ID, record: r7, assetId: me.asset('1835'), sceneYear: 1835 });
  ok(pv7.photoFace && pv7.photoFace.sex !== r7.sex, `Style 3's Auto photographed face is the other body's (${pv7.photoFace?.sex} on ${r7.sex})`);
  // Auto follows the complexion and the age (before, every complexion gave the same face).
  me.set({ sex: 'male', age: 'middle' });
  const autoFor = (complexion) => { me.set({ complexion }); return me.record('1835').looks.face_pick; };
  const pale = autoFor('fair'), deep = autoFor('deep_brown');
  const byId = (id) => lib.photoFaces.faces.find((f) => f.id === id);
  ok(pale && deep && P.faceTone(byId(pale)) > 2 * P.faceTone(byId(deep)), `Auto: a fair complexion a lighter face (${pale}), a deep brown one a deeper (${deep})`);
  ok([pale, deep].every((id) => byId(id).sex === 'male' && byId(id).age >= 35 && byId(id).age < 55), 'Auto: a face of the body\'s own faces and the person\'s age group');
  me.set({ age: 'older' });
  ok(byId(me.record('1835').looks.face_pick).age >= 55, 'an older person, an older face');
  // Nobody of the town draws differently: no pick, no faceOf, the same face as before.
  const town = V.photoFaceFor(photoKit, { key: 'someone:1904', sex: 'male', age: 40, complexion: 'light' });
  ok(town && V.photoFaceFor(photoKit, { key: 'someone:1904', sex: 'male', age: 40, complexion: 'light', faceOf: null, pick: null })?.id === town.id, 'everyone else\'s photographed face is drawn as before');
  const ps = read('renderers/web/js/person-settings.js');
  ok(ps.includes('faceGroups(') && ps.includes("role: 'tablist'") && ps.includes('person-face-band'), 'the You tab shows the library by type, in bands');
}

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
ok(!/data-set-pane="you"/.test(html) && !html.includes('id="s-person"'), 'its group is not in the page (person-settings.js personHost makes it: the page is at the 64 KB duplicate floor)');
{
  // personHost on a small stand-in page: the group goes before Show's first, hidden unless You is open.
  const made = [];
  const node = (tag) => { const n = { tag, kids: [], attrs: {}, hidden: false, className: '', id: '', textContent: '',
    setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k] ?? null; },
    append(...k) { this.kids.push(...k); }, before(k) { made.push(['before', k, this]); } }; return n; };
  const show = node('div'), tab = node('button'); tab.attrs['aria-selected'] = 'false';
  const byId = {};
  const doc = { createElement: (t) => node(t),
    getElementById: (id) => byId[id] ?? null,
    querySelector: (q) => (q.includes('data-set-pane="show"') ? show : q.includes('data-set-tab="you"') ? tab : null) };
  const host = personHost(doc);
  const group = made[0]?.[1];
  ok(made.length === 1 && made[0][2] === show && group?.attrs['data-set-pane'] === 'you' && group.className === 'settings-group',
    'personHost puts the You group before Show\'s first group');
  ok(group.hidden === true && host?.id === 's-person' && group.kids[0]?.textContent === 'Your person' && group.kids[1] === host,
    'hidden while another tab is open, headed "Your person", holding #s-person');
}
// The face up close beside the figure (Kevin, 2026-11-19), from the same figure (no second build).
{
  const ps = read('renderers/web/js/person-settings.js'), pp = read('renderers/web/js/person-portrait.js');
  ok(FACE_TURNS[0] === 0 && ps.includes("frame: 'face'") && /person-face-close/.test(read('renderers/web/css/navigator.css')), 'the You tab draws the face up close beside the figure');
  ok(/frame === 'face'/.test(pp) && /eye_l/.test(pp) && (pp.match(/visitorActor\(/g) ?? []).length === 1, 'person-portrait.js frames the face on the eyes of the one figure it builds');
}
ok(/^rgb\(\d+, \d+, \d+\)$/.test(swatchColour(COMPLEXION_TINT.deep_brown)), 'complexion swatches are drawn colours');
const main = read('renderers/web/js/main.js');
ok(main.includes("import('./visitor-person.js')") && main.includes('wirePersonSettings('), 'main.js mounts the person and its tab');

console.log(`visitor person (T-3644): ${n} checks PASS`);
