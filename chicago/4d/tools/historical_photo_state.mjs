// SPDX-License-Identifier: GPL-3.0-or-later
// The existing person's values and appearance, read through the real variation code.
import fs from 'node:fs/promises';
import { registerHooks } from 'node:module';
const root = new URL('../', import.meta.url);
const three = new URL('renderers/web/vendor/three-0.185.1/three.module.js', root).href;
registerHooks({ resolve: (s, c, next) => s === 'three' ? { url: three, shortCircuit: true } : next(s, c) });
const V = await import('../renderers/web/js/human-variation.js');
const { hairFor, HAIR_COLOURS } = await import('../renderers/web/js/human-hair-styles.js');
const { looksHairStyle } = await import('../renderers/web/js/human-looks.js');
const read = async p => JSON.parse(await fs.readFile(new URL(p, root)));
const files = async url => {
  const name = String(url).split('/humans/web/')[1];
  try {
    const b = await fs.readFile(new URL('assets/humans/web/' + name, root));
    return { ok: true, json: async () => JSON.parse(b), arrayBuffer: async () => b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength) };
  } catch { return { ok: false }; }
};
const kit = await V.loadVariationKit('https://reference.invalid/humans/web/', files);
if (!kit) throw Error('Cannot read the existing variation kit');
delete kit.photoPortraits;
const people = (await read('assets/humans/web/hm08_variation_persons.json')).persons;
const named = (o, key) => {
  if (!o || typeof o !== 'object') return null;
  if ([o.id, o.person, o.person_id, o.key].includes(key)) {
    const n = o.name ?? o.label ?? o.display_name;
    if (typeof n === 'string') return n;
    if (n?.display) return n.display;
  }
  for (const child of Object.values(o)) { const n = named(child, key); if (n) return n; }
  return null;
};
const result = {};
for (const key of process.argv.slice(2)) {
  const record = people[key];
  if (!record) throw Error('Unknown person: ' + key);
  let portrait={};try{portrait=await read('data/humans/variation/portraits/'+key+'.json');}catch{}
  let assigned=null;const at=record.drawn_as?.[0];if(at){const [file,id]=at.split('#'),d=await read(file);assigned=id?d.people?.find(p=>p.person===id)?.asset_id:d.appearance?.asset_id;}
  const asset = portrait.base_body ?? portrait.card?.body ?? assigned ?? (record.sex === 'female' ? 'glessner_frances_m_1904' : 'glessner_john_j_1904');
  const v = V.personVariation({ kit, key, record, assetId: asset, sceneYear: Number(record.scene) });
  const values = { ...v.values };
  for (const [axis, option] of Object.entries(v.option)) values[axis + '.option'] = option;
  const hair = record.looks ? looksHairStyle(record.looks, hairFor(key, Number(record.scene))) : hairFor(key, Number(record.scene));
  let label = key;
  if (record.record) label = named(await read(record.record), key) ?? key;
  result[key] = { label, asset, sex: v.sex, age: v.age, height: v.height, values,
    drawn_as:record.drawn_as??[],hair_rgb: HAIR_COLOURS[hair?.colour] ?? HAIR_COLOURS.dark_brown,
    complexion: record.looks?.complexion?.drawn ?? null, eyes: record.looks?.eyes ?? null };
}
process.stdout.write(JSON.stringify(result));
