/**
 * people-directory.js — the Navigator's People screen as a directory (T-3430).
 *
 * The owner, 2026-11-06, on the 1904 People screen (a long list of every household's
 * people, nothing else): "this should have some search to it to be able to find a person or
 * household and then click and get details on that person and household the way we have it
 * with their full story and overview and be able to go to that person and or their house".
 *
 * This is the pure half: the scene's directory (`sidecars/<scene>/people.json`) read into
 * households and people, and a search over both. No DOM; tools/test_people_directory.mjs
 * reads it against the real 1904 and 1812 directories. apps/people-view.js draws it.
 *
 * NOTHING HERE IS COMPOSED BEYOND THE DIRECTORY. A household's address is the part of its
 * own name after "at"; its house is where its people live (`lives_at`); its family, staff
 * and children of other years are its rows by their own `relationship` and `lived_here`.
 */

// The family before its staff (T-3258): head, spouse, children, kin, then the servants.
const RANK = { head: 0, wife: 1, husband: 1, son: 2, daughter: 2, child: 2, servant: 4 };
const PLACE = { head: 'Head of the household', wife: 'Wife', husband: 'Husband', son: 'Son', daughter: 'Daughter',
  servant: 'Live-in staff', household_member: 'In the household' };

/** Diacritics folded, lower-cased, one space between words: what a query and a row are compared as. */
export function fold(s) {
  return String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/[^a-z0-9' ]+/g, ' ').replace(/\s+/g, ' ').trim();
}

const words = (s) => String(s ?? '').replace(/_/g, ' ').trim();
const capital = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);

/** "Head of the household", "Son", "Live-in staff": a row's place in its household. */
export function placeIn(relationship) {
  const r = String(relationship ?? '');
  return PLACE[r] ?? capital(words(r));
}

/** A row's work, where the record states one ("none" is not work). */
export function workOf(row) {
  const o = words(row?.occupation);
  return o && !/^none\b/i.test(o) ? capital(o) : '';
}

/** "1883–1899": a child of the house's years, with an en dash. */
export function yearsWords(lived) {
  return lived?.years ? String(lived.years).replace(/([\ds])-(\d|about)/g, '$1–$2') : '';
}

/** Not in the house on the scene date: a child carded for the years they lived there (T-3382). */
export const away = (row) => row?.lived_here?.on_scene_date === 'no';

/** "The Roloson household at 2109 Prairie Avenue" → { short, address, number, street }. */
export function splitHouseholdName(name) {
  const s = String(name ?? '').trim();
  const m = s.match(/^(.*?)\s+at\s+(.+)$/);
  const short = (m ? m[1] : s) || 'A household';
  const address = m ? m[2] : '';
  const num = address.match(/^(\d+)\s+(.+)$/);
  return { short, address, number: num ? Number(num[1]) : null, street: num ? num[2] : address };
}

const order = (r) => RANK[r.relationship] ?? 3;
const byPlace = (a, b) => order(a) - order(b) || String(a.name).localeCompare(String(b.name));

/** The surname a row sorts by: the last word of the name, "jr." and the like set aside. */
export function surnameOf(name) {
  const parts = String(name ?? '').replace(/\([^)]*\)/g, ' ').split(/\s+/)
    .filter((w) => w && !/^(jr|sr|ii|iii|iv)\.?$/i.test(w));
  return fold(parts[parts.length - 1] ?? '');
}

/**
 * The directory, read: `{ households, people, byId, householdById }`. A household carries
 * its rows in their household order, split into `family`, `staff` and `away`, the house its
 * people live at, and the text a search reads. A person carries the same row plus its
 * household's short name and the text a search reads.
 */
export function directoryModel(dir) {
  const rows = Array.isArray(dir?.people) ? dir.people.filter((r) => r && r.id && r.name) : [];
  const groups = new Map();
  for (const r of rows) {
    const key = r.household || r.household_name || r.id;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(r);
  }
  const households = [];
  for (const [id, members] of groups) {
    const sorted = [...members].sort(byPlace);
    const head = sorted.find((r) => r.relationship === 'head') ?? sorted[0];
    const name = head.household_name || 'A household';
    const parts = splitHouseholdName(name);
    // The house is where its people live on the scene date: the head's, else the most named.
    const homes = new Map();
    for (const r of sorted) if (r.lives_at && !away(r)) homes.set(r.lives_at, (homes.get(r.lives_at) ?? 0) + 1);
    const lives_at = (head.lives_at && !away(head) ? head.lives_at : null)
      ?? [...homes].sort((a, b) => b[1] - a[1])[0]?.[0] ?? head.lives_at ?? null;
    const here = sorted.filter((r) => !away(r));
    households.push({
      id,
      name,
      ...parts,
      file: head.file ?? null,
      head: head.id,
      lives_at,
      members: sorted,
      family: here.filter((r) => r.relationship !== 'servant'),
      staff: here.filter((r) => r.relationship === 'servant'),
      away: sorted.filter(away),
      hay: fold([name, ...sorted.map((r) => `${r.name} ${words(r.occupation)}`)].join(' ')),
    });
  }
  households.sort((a, b) => fold(a.street).localeCompare(fold(b.street))
    || (a.number ?? Infinity) - (b.number ?? Infinity) || a.name.localeCompare(b.name));
  const householdById = new Map(households.map((h) => [h.id, h]));
  const people = rows.map((r) => {
    const h = householdById.get(r.household || r.household_name || r.id);
    return { ...r, short: h?.short ?? '', address: h?.address ?? '', surname: surnameOf(r.name),
      hay: fold([r.name, words(r.occupation), placeIn(r.relationship), r.household_name].join(' ')) };
  }).sort((a, b) => a.surname.localeCompare(b.surname) || a.name.localeCompare(b.name));
  return { households, people, byId: new Map(people.map((p) => [p.id, p])), householdById };
}

/** The household a person belongs to. */
export function householdOf(model, personId) {
  const p = model?.byId?.get(personId);
  return p ? model.householdById.get(p.household || p.household_name || p.id) ?? null : null;
}

/** The household that lives at a building, for "In view" (the building Inspect or the tag holds). */
export function householdAt(model, structureId) {
  if (!structureId) return null;
  return model?.households?.find((h) => h.lives_at === structureId) ?? null;
}

/**
 * Every word of the query in a row's text, in any order: "roloson coach" finds the Rolosons'
 * coachman, "2109" the house, "cook" every cook. An empty query matches everything.
 */
export function search(model, query) {
  const q = fold(query).split(' ').filter(Boolean);
  const hit = (hay) => q.every((w) => hay.includes(w));
  if (!q.length) return { query: '', households: model?.households ?? [], people: model?.people ?? [] };
  return {
    query: q.join(' '),
    households: (model?.households ?? []).filter((h) => hit(h.hay)),
    people: (model?.people ?? []).filter((p) => hit(p.hay)),
  };
}

/** A household's one-line count: "5 people · 3 staff". */
export function householdCount(h) {
  const here = h.family.length + h.staff.length;
  return [`${here} ${here === 1 ? 'person' : 'people'}`, h.staff.length ? `${h.staff.length} staff` : ''].filter(Boolean).join(' · ');
}
