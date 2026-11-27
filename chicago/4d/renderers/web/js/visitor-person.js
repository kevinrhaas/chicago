// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * visitor-person.js — the visitor's own person (T-3644).
 *
 * Kevin, 2026-11-17: "the body you have riding the horse is a white man you will need to provide
 * options for users in settings to change the gender appearance dress, etc. this becomes a person
 * builder eventually but the foundation starts with customizing the default person".
 *
 * The visitor is drawn wherever the town sees them: in the saddle now (riding.js), and later at
 * the reins, at the oars and, as first-person hands, holding a torch or a paddle. Every one of
 * those builds the same figure from here, so it is one person everywhere:
 *
 *   asset(year)    the body (and so the dress) the visitor wears in that year
 *   record(year)   their row for the people layer's variation table: sex, age, complexion,
 *                  eyes, hair colour and cut, whiskers, and the face they chose from the library
 *                  (human-variation.js libraryFace `pick`). It is laid in under VISITOR_PERSON_ID,
 *                  so humans.js dresses the figure exactly as it dresses a townsperson
 *   actor(...)     a people-layer actor already wearing the person (visitorActor)
 *   onChange(fn)   told whenever the choice changes, so a seated figure can be re-made
 *
 * The choice is data/humans/visitor_person.json's lists, and nothing else: a year offers only the
 * dress its own townspeople already wear, so a visitor cannot be put in another time's clothes.
 * It is kept on the device (`storage_key`), and, for a visitor who signed in (sign-in.js), in
 * Firestore at people/<uid> (docs/SIGN-IN.md has the rule), so it follows them to another
 * device; the newer of the two wins. A refused or failed write keeps the device's copy and
 * says so once in the console: the person is never lost to a network.
 *
 * The shape grows: `v` is the record's version, each year's dress is kept per body type (so
 * changing it and back gives the same clothes again), and fields a later builder adds (colours,
 * a hat, build) are carried through untouched by normalChoice.
 *
 * Body types (Kevin, 2026-11-19: a third one, and the control named for the person's style, not
 * their gender). The choice's `sex` field keeps its name (stored choices, the account's copy) but
 * holds a body type: the catalog's `sexes`, shown as "Body style" (Style 1, 2, 3). One with `of` (Style 3)
 * wears any outfit and cut of the types it names, any library face, and its own `build` on each
 * body; its record's `sex` is the body's (the outfit's), so the people layer, the face library
 * and the side saddle read it as they read anyone's.
 */
import { SIGN_IN } from './sign-in-config.js';

export const VISITOR_PERSON_ID = 'visitor:you';
export const CHOICE_VERSION = 1;
const PERSON_BASIS = 'The visitor\'s own person, chosen in Settings: nobody of the town (liberty L-visitor-person-3644).';

const byId = (list, id) => (Array.isArray(list) ? list.find((x) => x.id === id) : null) ?? null;
const first = (list) => (Array.isArray(list) && list.length ? list[0] : null);
const yearKey = (year, catalog) => {
  const y = String(year ?? '');
  return (catalog.years ?? []).includes(y) ? y : null;
};

/** A body type of the catalog (`sexes`) by id. */
export const bodyType = (catalog, id) => byId(catalog.sexes, id);
/** The bodies a body type wears: its own id, or those it names in `of`. */
export const bodiesOf = (catalog, id) => bodyType(catalog, id)?.of ?? [id];
/** A year's list (`outfits` or `cuts`) for a body type, each entry with the body it is worn on. */
export function wardrobe(catalog, kind, year, id) {
  const seen = new Set(), out = [];
  for (const body of bodiesOf(catalog, id)) {
    for (const o of catalog[kind]?.[year]?.[body] ?? []) if (!seen.has(o.id)) { seen.add(o.id); out.push({ ...o, body }); }
  }
  return out;
}

/**
 * A stored or typed choice brought to one the catalog can draw: every field one of its own ids,
 * the default where it is not. Pure. Unknown extra fields are kept (a later builder's).
 */
export function normalChoice(raw, catalog) {
  const d = catalog.defaults ?? {};
  const r = raw && typeof raw === 'object' ? raw : {};
  const pickId = (list, id, fallback) => (byId(list, id) ? id : (byId(list, fallback) ? fallback : first(list)?.id ?? null));
  const sex = pickId(catalog.sexes, r.sex, d.sex);
  const out = {
    ...r,
    v: CHOICE_VERSION,
    sex,
    age: pickId(catalog.ages, r.age, d.age),
    complexion: pickId(catalog.complexions, r.complexion, d.complexion),
    eyes: pickId(catalog.eyes, r.eyes, d.eyes),
    hair_colour: pickId(catalog.hair_colours, r.hair_colour, d.hair_colour),
    facial: pickId(catalog.facial?.[sex], r.facial, d.facial),
    face: faceOk(r.face, sex, r.complexion, catalog) ? r.face : 'auto',
    hands: typeof r.hands === 'boolean' ? r.hands : !!d.hands,
    years: {},
    saved: typeof r.saved === 'string' ? r.saved : '',
  };
  // Each year's dress and cut, kept per body type.
  for (const y of catalog.years ?? []) {
    const had = r.years?.[y] && typeof r.years[y] === 'object' ? r.years[y] : {};
    out.years[y] = {};
    for (const s of (catalog.sexes ?? []).map((x) => x.id)) {
      const h = had[s] && typeof had[s] === 'object' ? had[s] : {};
      // A type's own first look in this year (`start`), so Style 3 does not open as Style 1 (T-3756).
      const start = bodyType(catalog, s)?.start?.[y] ?? {};
      out.years[y][s] = {
        ...h,
        outfit: pickId(wardrobe(catalog, 'outfits', y, s), h.outfit, start.outfit ?? null),
        cut: pickId(wardrobe(catalog, 'cuts', y, s), h.cut, start.cut ?? null),
      };
    }
  }
  return out;
}

/** Faces a person of body type `sex` and `complexion` may choose: the library's of that body
 * (both, for a type with `of`; `catalog` tells which), the freckled ones only for a light
 * complexion (the library's own rule, face_library.json `light_only_for`). */
export function faceChoices(faces, sex, complexion, catalog = null) {
  const F = faces?.faces;
  if (!Array.isArray(F)) return [];
  const light = Array.isArray(faces.light_only_for) ? faces.light_only_for : [];
  const wears = catalog ? bodiesOf(catalog, sex) : [sex === 'male' ? 'male' : 'female'];
  const original=F.map((f, index) => ({ ...f, index }))
    .filter((f) => wears.includes(f.sex) && (!f.light_only || light.includes(complexion)));
  // The full fictional photo catalog is available here. Historical NPC pools
  // never limit a visitor's choices, and no photo is hidden by complexion.
  const photos=(catalog?.photo_faces?.faces??[]).filter(f=>wears.includes(f.sex))
    .map(f=>({...f,photographic:true}));
  return [...original,...photos];
}

function faceOk(face, sex, complexion, catalog) {
  if (face === 'auto' || face === 'body') return true;
  if (typeof face !== 'string' || !catalog.faces) return false;
  return faceChoices(catalog.faces, sex, complexion, catalog).some((f) => f.id === face);
}

/** The year's own entry of the choice: { sex (the body type), body (the outfit's), outfit, cut }
 * with the catalog's records. */
export function yearChoice(choice, year, catalog) {
  const y = yearKey(year, catalog) ?? (catalog.years ?? [])[0];
  const sex = choice.sex;
  const mine = choice.years?.[y]?.[sex] ?? {};
  const outfits = wardrobe(catalog, 'outfits', y, sex);
  const cuts = wardrobe(catalog, 'cuts', y, sex);
  const start = bodyType(catalog, sex)?.start?.[y] ?? {};
  const outfit = byId(outfits, mine.outfit) ?? byId(outfits, start.outfit) ?? first(outfits);
  return { year: y, sex, body: outfit?.body ?? sex, outfit, cut: byId(cuts, mine.cut) ?? byId(cuts, start.cut) ?? first(cuts) };
}

/** The body the visitor wears in `year`. */
export function personAsset(choice, year, catalog) {
  return yearChoice(choice, year, catalog).outfit?.asset ?? null;
}

/**
 * Their row for the people layer's variation table (humans.js reads `looks`, `sex`, `age`;
 * human-variation.js reads `looks.face_pick`). Pure.
 */
export function personRecord(choice, year, catalog) {
  const { sex: type, body: sex, cut, outfit, year: y } = yearChoice(choice, year, catalog);
  const age = byId(catalog.ages, choice.age)?.years ?? 35;
  const facial = [...(byId(catalog.facial?.[type], choice.facial)?.wears ?? []), ...(catalog.brows?.[type] ?? [])];
  const graded = (value) => ({ value, drawn: value, grade: 'reconstructed' });
  // A body type's own build on this body (human-variation.js looks.build), when it has one.
  const build = bodyType(catalog, type)?.build?.[sex] ?? null;
  // ...and the faces an Auto face is drawn from on it (`face_of`, T-3756): the other body's.
  const faceOf = choice.face === 'auto' ? bodyType(catalog, type)?.face_of?.[sex] ?? null : null;
  return {
    sex, visitor: true, scene: y, ...(type !== sex ? { body_type: type } : {}),
    age: { years: age, grade: 'reconstructed' },
    looks: {
      complexion: graded(choice.complexion),
      eyes: graded(choice.eyes),
      hair: { value: choice.hair_colour, drawn: choice.hair_colour, cut: cut?.id ?? null, facial, grade: 'reconstructed' },
      face_pick: choice.face === 'auto' ? null : choice.face,
      ...(faceOf ? { face_of: faceOf } : {}),
      ...(build ? { build: { ...build } } : {}),
      grade: 'reconstructed', basis: PERSON_BASIS, liberty: catalog.liberty,
    },
    // A dress worn on its body in other colours, pieces set aside, a hat of its own (human-looks.js
    // dressCloth, human-hats.js): the riding habits.
    ...(outfit?.dress ? { dress: outfit.dress } : {}),
  };
}

/** Lay the visitor's row into a people layer's variation table (once it has loaded). */
export async function layPersonRow(humans, record) {
  const v = await humans?.assets?.variation?.();
  if (!v?.persons) return false;
  v.persons[VISITOR_PERSON_ID] = record;
  return true;
}

/**
 * A people-layer actor wearing the visitor's person in `year`: their body, dress, face and hair.
 * Not stood in the layer (createActor): the caller places, poses and disposes it. `state` is
 * the behaviour state it starts in ('seated' in the saddle, 'standing' for the portrait).
 */
export async function visitorActor(humans, person, year, { id = `visitor:${year}`, state = 'standing', lod = 1, why = PERSON_BASIS, liberty = null } = {}) {
  if (!humans?.createActor || !person) return null;
  const record = person.record(year);
  await layPersonRow(humans, record);
  const instance = { id, contract_version: 1, display: 'shown', scene: String(year), appearance: { asset_id: person.asset(year) },
    placement: { local_e: 0, local_n: 0, heading_deg: 180, anchor: 'terrain' }, behaviour: { state },
    animation: { clip: 'idle', loop: true, phase: 0 }, lod: { policy: 'fixed', fixed: lod },
    interaction: { opens: 'none', selectable: false },
    provenance: { grade: 'reconstructed', basis: why, liberty: liberty ?? person.catalog.liberty } };
  const actor = humans.createActor(instance, { identity: { kind: 'anonymous', personId: VISITOR_PERSON_ID, person: null, profile: null, role: null } });
  // The visitor is the nearest figure there is: built first in the people layer's turn (T-3572).
  actor.distance = 0;
  return actor;
}

/* ------------------------------------------------------------- keeping it */

const docsBase = (projectId) => `https://firestore.googleapis.com/v1/projects/${encodeURIComponent(projectId)}/databases/(default)/documents`;

/** The Firestore commit that keeps a choice at people/<uid>. Exported for the self-test, which
 * holds its fields to docs/SIGN-IN.md's rule. */
export function personWrite({ projectId, uid, choice }) {
  return [{
    update: { name: `projects/${projectId}/databases/(default)/documents/people/${uid}`,
      fields: { person: { stringValue: JSON.stringify(choice) } } },
    updateMask: { fieldPaths: ['person'] },
    updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }],
  }];
}

/** The newer of two choices by their `saved` stamp (the device's when they tie). */
export function newer(a, b) {
  if (!b?.saved) return a;
  if (!a?.saved) return b;
  return b.saved > a.saved ? b : a;
}

/**
 * The visitor's person: the catalog, the choice and its keeping.
 * @param {object} o  catalog (visitor_person.json, with `faces` the kit's face library header
 *   when known) · storage (localStorage or null) · account (sign-in.js: uid, idToken()) ·
 *   fetchFn · now () => ISO time
 */
export function createVisitorPerson({ catalog, storage = null, account = null, fetchFn = globalThis.fetch?.bind(globalThis),
  now = () => new Date().toISOString(), projectId = SIGN_IN?.firebase?.projectId ?? '' } = {}) {
  const key = catalog.storage_key ?? 'chicago4d.person';
  const read = () => { try { return JSON.parse(storage?.getItem(key) ?? 'null'); } catch { return null; } };
  const keep = (c) => { try { storage?.setItem(key, JSON.stringify(c)); } catch { /* a refused storage keeps it for this visit */ } };
  let choice = normalChoice(read(), catalog);
  const listeners = new Set();
  const tell = () => { for (const fn of listeners) { try { fn(choice); } catch (e) { console.warn('[4D Chicago] person:', e); } } };
  let warned = false;
  const remote = account?.uid && typeof account.idToken === 'function' && projectId && fetchFn;

  async function push() {
    if (!remote) return false;
    try {
      const token = await account.idToken();
      const res = await fetchFn(`${docsBase(projectId)}:commit`, { method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ writes: personWrite({ projectId, uid: account.uid, choice }) }) });
      if (!res.ok) throw Error(`HTTP ${res.status}`);
      return true;
    } catch (e) {
      if (!warned) console.warn('[4D Chicago] person: kept on this device only', e?.message ?? e);
      warned = true;
      return false;
    }
  }

  const api = {
    catalog,
    get choice() { return choice; },
    /** Change the choice. Fields of the year's dress (`outfit`, `cut`) need `year`. `sex` is the body type. */
    set(patch = {}, year = null) {
      const next = structuredClone(choice);
      for (const [k, v] of Object.entries(patch)) {
        if (k === 'outfit' || k === 'cut') {
          const y = yearKey(year, catalog);
          if (y) next.years[y][next.sex] = { ...next.years[y][next.sex], [k]: v };
        } else next[k] = v;
      }
      next.saved = now();
      choice = normalChoice(next, catalog);
      keep(choice);
      tell();
      void push();
      return choice;
    },
    /** Back to the person every visitor starts as. */
    reset() { choice = normalChoice({ saved: now() }, catalog); keep(choice); tell(); void push(); return choice; },
    asset: (year) => personAsset(choice, year, catalog),
    record: (year) => personRecord(choice, year, catalog),
    year: (year) => yearChoice(choice, year, catalog),
    onChange(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    /** Read the signed-in visitor's kept choice; the newer of it and the device's wins. */
    async sync() {
      if (!remote) return choice;
      try {
        const token = await account.idToken();
        const res = await fetchFn(`${docsBase(projectId)}/people/${encodeURIComponent(account.uid)}`, { headers: { Authorization: `Bearer ${token}` } });
        if (res.status === 404) { if (choice.saved) await push(); return choice; }
        if (!res.ok) throw Error(`HTTP ${res.status}`);
        const doc = await res.json();
        const theirs = normalChoice(JSON.parse(doc?.fields?.person?.stringValue ?? 'null'), catalog);
        const pick = newer(choice, theirs);
        if (pick !== choice) { choice = pick; keep(choice); tell(); } else if (choice.saved && choice.saved !== theirs.saved) await push();
      } catch (e) {
        if (!warned) console.warn('[4D Chicago] person: not read from the account', e?.message ?? e);
        warned = true;
      }
      return choice;
    },
  };
  return api;
}

/** Fetch the catalog (and the face library's header from the people kit). */
export async function loadVisitorPerson({ dataBase, assetBase = null, storage = null, account = null, fetchFn = globalThis.fetch?.bind(globalThis) }) {
  const res = await fetchFn(new URL('humans/visitor_person.json', dataBase));
  if (!res.ok) throw Error(`visitor person: HTTP ${res.status}`);
  const catalog = await res.json();
  if (assetBase) {
    try {
      const kit = await (await fetchFn(new URL('humans/web/hm08_variation_kit.json', assetBase))).json();
      if (kit?.faces) catalog.faces = { ...kit.faces, base: new URL('humans/web/', assetBase).href };
    } catch { /* no faces to choose among: Auto only */ }
    try {
      const url=new URL('humans/web/photo_faces/pilot/runtime.json',assetBase);
      const r=await fetchFn(url);
      if(r.ok){const p=await r.json();if(Array.isArray(p.faces)&&p.faces.length<=512&&p.textures?.light)
        catalog.photo_faces={...p,base:url.href,map:p.textures.light.file};}
    }catch{/* Existing saved settings and the original faces remain usable. */}
  }
  const person = createVisitorPerson({ catalog, storage, account, fetchFn });
  void person.sync();
  return person;
}
