/** One inventory for in-world search and the future arrival picker (T-1277).
 * Unknown addresses stay unknown. The public business index, when present,
 * owns firm identity and scene-date location; fallback rows are explicitly derived.
 */
import { displayName, searchTerms } from './display-name.js';
import { KINDS, placeKind, structureGrade } from './place-kinds.js';

export const normal = value => String(value ?? '').toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
const words = value => String(value ?? '').replace(/_/g, ' ').replace(/\s+/g, ' ').trim();
const idOf = field => (field && typeof field === 'object' ? field.value : field) || null;
const positioned = p => Number.isFinite(p?.e) && Number.isFinite(p?.n);
const CARDINALS = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
export const DESTINATION_GROUPS = [...KINDS.slice(0, 3), { id: 'businesses', label: 'Businesses' }, ...KINDS.slice(3)];
const labels = Object.fromEntries(DESTINATION_GROUPS.map(k => [k.id, k.label]));
const order = Object.fromEntries(DESTINATION_GROUPS.map((k, i) => [k.id, i]));
const tradeFunction = /(?:^|_)(?:store|shop|warehouse|manufactory|tannery|brickyard)(?:_|$)|tavern_inn|auction_room|printing_office|boarding_house|hotel_stable/;

/**
 * T-2740: the orders Go to offers. The owner, 2026-10-17: "order those by address number,
 * name of building, owner of building and also distance closest furthest". Each order puts
 * the rows that have nothing to sort on (a viewpoint has no address, an empty roof no owner)
 * after the ones that do, in name order, so the list never hides a row.
 */
export const SORTS = [
  { id: 'near', label: 'Nearest' }, { id: 'far', label: 'Furthest' },
  { id: 'address', label: 'Address' }, { id: 'name', label: 'Name' }, { id: 'owner', label: 'Owner' },
];
/** `1616-1620 S. Prairie Avenue` → { number: 1616, street: 'prairie avenue', text }. A record's
 *  own address line (aka, symbolic location, title); 1835 has lots and blocks, not numbers. */
const ADDRESS = /(?:^|—\s*)(\d{1,5})(?:\s*[-–]\s*\d{1,5})?\s+(?:[NSEW]\.?\s+)?((?:[A-Z][A-Za-z'’.]*\s+){0,2}?(?:Avenue|Street|Ave\.?|St\.|Place|Court|Road|Boulevard|Drive))\b/;
export function addressOf(...lines) {
  for (const line of lines.flat()) {
    const m = ADDRESS.exec(String(line ?? ''));
    if (m) return { number: Number(m[1]), street: normal(m[2]).replace(/\bave\.?$/, 'avenue').replace(/\bst\.$/, 'street'), text: m[0].replace(/^—\s*/, '').trim() };
  }
  return null;
}
/** A title's name without its article or its leading address: what "by name" reads. A title
 *  that only describes the building ("the alley building of…", "A vacant log dwelling") has
 *  no name to sort on, so it follows the named ones, in title order. */
export function nameKey(t) {
  const label = String(t?.label ?? '').trim();
  if (!label || label === t?.id) return null;
  // "[?] G. Abbot", "[Mrs.] Herman": the directory's doubt is not part of the name; a title
  // that is all doubt ("[tin, sheet iron and stove manufactory, …]") has none.
  const rest = label.replace(/^\[[^\]]*\]\s*/, '').replace(/^\d[\d\s–-]*(?:\([^)]*\)\s*)?(?:[NSEW]\.\s+)?\S+\s+(?:Avenue|Street)\s*[—:-]\s*/, '');
  // 1904's unnamed drafts carry their construction family from the district register instead.
  if (/^(?:[Aa]n?\s|[Tt]he\s+[a-z]|[a-z]|(?:Brick masonry|Frame dwelling|Stone-front masonry)\b)/.test(rest)) return null;
  return normal(rest.replace(/^the\s+/i, '')) || null;
}
/** "John J. Glessner" → "glessner john j. glessner": surname first, so the list reads A to Z by family. */
export function ownerKey(name) {
  const first = String(name ?? '').split(/\s*(?:\/|&|\band\b|,)\s*|(?<=[a-z])-(?=[A-Z])/)[0];
  const words = first.replace(/\([^)]*\)/g, ' ').split(/\s+/).filter(w => w && !/^(?:jr|sr|ii|iii)\.?$/i.test(w));
  return words.length ? normal(`${words.at(-1)} ${name}`) : null;
}
/** A name the way the town would write it: "Rufus Brown", "Pierce & French", "W. H. Stow". */
const NAMEISH = /^(?!(?:The|A|An|No|Nobody|Anonymous|To)\b)[A-Z][\w.'’&-]*(?:\s+(?:[A-Z&(][\w.'’()&-]*|and|de|du|la|le|van|von)){0,5}$/;
/** The household or person a resident line names: "The Vieaux household — …" → "Vieaux". */
function whoOf(value) {
  const text = String(value ?? '').trim();
  const family = /^The\s+(.+?)\s+(?:brothers['’]\s+)?(?:household|family)\b/.exec(text)?.[1];
  // "The Brown boarding-house household" is the Browns'; "The brickyard household" is nobody's by name.
  if (family) return /^[A-Z]/.test(family) ? family.replace(/(?:\s+[a-z][\w-]*)+$/, '') : null;
  const [head, tail] = text.split(/\s+—\s+/);
  const pick = /household$/i.test(head ?? '') && tail ? tail : head;
  return NAMEISH.test(pick ?? '') ? pick : null;
}
/** Whose building the record says it is, from what it already carries; null when it says nobody. */
function ownerOf(s, id, { title, vacant }, titleOf) {
  // Who kept or lived in it, then who worked there: boarders, lodgers and a shared roof are not.
  const households = (Array.isArray(s?.residents) ? s.residents : []).filter(h => /\b(?:lived|kept|keeps|worked)\b/.test(String(h?.relation)));
  const home = h => (/\b(?:lived|kept|keeps)\b/.test(String(h.relation)) ? 0 : 1);
  for (const h of [...households].sort((x, y) => home(x) - home(y))) {
    const name = whoOf(h?.name);
    if (name) return name;
  }
  // "Rufus Brown's Boarding House", "Clark's house at the forks", "The Burns house".
  const own = /^(?:The\s+)?([A-Z][\w.'’-]*(?:\s+(?:[A-Z][\w.'’-]*|&|and|de|du|la|le))*)(?:'s|’s|')\s/.exec(title)
    ?? /^The\s+([A-Z][\w'’-]*(?:\s+[A-Z][\w'’-]*)*?)(?:\s+family['’]s)?\s+house\b/.exec(title);
  if (own && !/\b(?:House|Hotel|Store|Factor|Tavern|Office)$/.test(own[1])) return own[1];
  // A title that says the roof stood empty or to let outranks an occupant line under it.
  const occ = vacant ? null : whoOf(String(s?.attributes?.occupants?.value ?? '').split(/,\s/)[0]);
  if (occ) return occ;
  // 1904's Prairie drafts are filed under the family the district study names them for —
  // `sherman_house_2100_prairie`, its coach house `sherman_house_2100_prairie_coach_house` —
  // and their titles carry it ("2100 Prairie Avenue — Sherman Victorian Gothic"). A name
  // is taken only where the house's own title spells it, so `stone_house_2035` (limestone)
  // is nobody's.
  const slug = /^([a-z_]+?)_house(_\d{3,5}_[a-z]+)/.exec(id);
  if (slug) {
    const main = titleOf(`${slug[1]}_house${slug[2]}`) ?? title;
    const at = slug[1].split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .map(w => new RegExp(`(?<![A-Za-z])${w}(?![a-z])`).exec(main)).filter(Boolean);
    if (at.length) {
      const span = main.slice(Math.min(...at.map(m => m.index)), Math.max(...at.map(m => m.index + m[0].length)));
      return span.includes('(') && !span.includes(')') ? `${span})` : span;
    }
  }
  return null;
}
const lastIfMissing = (a, b, key, dir = 1) => {
  const x = key(a), y = key(b);
  if (x == null || y == null) return (x == null) - (y == null);
  return dir * (typeof x === 'number' ? x - y : x.localeCompare(y));
};
/** Rows in the chosen order (T-2740), as one list: a sorted list has no kind headings to split it. */
export function sortRows(rows, sort = 'near', visitor = null) {
  const dist = t => positioned(visitor) && positioned(t) ? Math.hypot(t.e - visitor.e, t.n - visitor.n) : null;
  // A row with nowhere to stand (its card opens instead) follows every row you can go to.
  const placed = (a, b) => positioned(b) - positioned(a);
  const byName = (a, b) => lastIfMissing(a, b, nameKey) || a.label.localeCompare(b.label);
  const order = {
    near: (a, b) => lastIfMissing(a, b, dist) || byName(a, b),
    far: (a, b) => lastIfMissing(a, b, dist, -1) || byName(a, b),
    address: (a, b) => lastIfMissing(a, b, t => t.address?.street ?? null) || lastIfMissing(a, b, t => t.address?.number ?? null) || byName(a, b),
    name: byName,
    owner: (a, b) => lastIfMissing(a, b, t => ownerKey(t.owner)) || byName(a, b),
  }[sort] ?? byName;
  return [...rows].sort((a, b) => placed(a, b) || order(a, b));
}

export function createDestinations({ scene, index, registry, people, positionOf, businesses = null,
  standFor = null, router = null, terrain = null } = {}) {
  const targets = [];
  const titleOf = id => registry?.has?.(id) ? displayName(registry.get(id)?.sidecar ?? {}, id).title : null;
  const position = id => {
    const p = positionOf?.(id);
    if (positioned(p)) return p;
    const placement = registry?.get(id)?.sidecar?.placement;
    return Number.isFinite(placement?.local_e) && Number.isFinite(placement?.local_n)
      ? { e: placement.local_e, n: placement.local_n } : null;
  };
  for (const a of scene?.anchors ?? []) {
    const facing = Number.isFinite(a.yaw_deg) ? `Viewpoint · looking ${CARDINALS[Math.round(((a.yaw_deg % 360 + 360) % 360) / 22.5) % 16]}` : 'Viewpoint';
    targets.push({ ...a, kind: 'anchor', group: 'viewpoints', label: a.label || a.id, sub: facing,
      e: a.local_e, n: a.local_n, search: normal([a.id, a.label, 'viewpoint'].filter(Boolean).join(' ')) });
  }
  for (const i of index?.intersections ?? []) {
    targets.push({ ...i, kind: 'intersection', group: 'corners', label: i.label || i.id,
      sub: 'Corner · verified junction', e: i.local_e, n: i.local_n,
      search: normal([i.id, i.label, 'corner', ...(i.search_terms ?? [])].filter(Boolean).join(' ')) });
  }
  for (const [id, record] of registry?.entries?.() ?? []) {
    const s = record?.sidecar ?? {}, name = displayName(s, id), group = placeKind(s, id, name), pos = position(id);
    const fn = words(s.attributes?.function?.value).split(';')[0].trim().replace(/^tavern inn$/, 'tavern & inn');
    targets.push({ kind: 'structure', group, id, label: name.title, sub: fn || labels[group],
      address: addressOf(name.title, s.placement?.symbolic_location, s.aka ?? []), owner: ownerOf(s, id, name, titleOf), vacant: name.vacant || undefined,
      presence: structureGrade(s), position: s.placement?.position_confidence || 'reconstructed',
      e: pos?.e, n: pos?.n, limit: pos ? null : 'No known address',
      search: normal([searchTerms(s, id), fn, labels[group]].filter(Boolean).join(' ')) });
  }
  const structures = new Map(targets.filter(t => t.kind === 'structure').map(t => [t.id, t]));
  const structureAt = id => structures.get(id) ?? null;
  const peopleRows = people?.people ?? people?.persons ?? [];
  for (const p of Array.isArray(peopleRows) ? peopleRows : []) {
    const lives = idOf(p.lives_at), works = idOf(p.works_at);
    const livesOk = !!(registry?.has(lives) && position(lives)), worksOk = !!(registry?.has(works) && position(works));
    const at = livesOk ? lives : worksOk ? works : null, pos = at ? position(at) : null;
    const building = at ? displayName(registry.get(at)?.sidecar ?? {}, at).title : null;
    const occupation = words(idOf(p.occupation)), occ = occupation !== 'none recorded' ? occupation : '';
    const limit = at ? null : 'No known address';
    targets.push({ kind: 'person', group: 'people', id: p.id, label: p.name || p.id,
      sub: ['Person', occ, at ? `${livesOk ? 'lived at' : 'worked at'} ${building}` : `${limit} · open card`].filter(Boolean).join(' · '),
      lives_at: livesOk ? lives : null, works_at: worksOk ? works : null, at, limit,
      address: at ? structureAt(at)?.address ?? null : null, owner: p.name || null,
      grade: p.grade ?? null, e: pos?.e, n: pos?.n,
      search: normal([p.name, occ, p.household_name, building, 'person'].filter(Boolean).join(' ')) });
  }
  // A house with no household on its record is still the household's that lived there.
  // The head of the household that lived there: John J. Glessner's house, not his wife's
  // or a lodger's.
  for (const p of Array.isArray(peopleRows) ? peopleRows : []) {
    const home = p?.name && p.relationship === 'head' ? structureAt(idOf(p.lives_at)) : null;
    if (home && !home.owner && !home.vacant) home.owner = p.name;
  }
  const rows = businesses?.businesses ?? (Array.isArray(businesses) ? businesses : null);
  if (rows) {
    for (const b of rows) {
      const w = b.where ?? {};
      // Nearby anchors are NOT premises. The compiled scene-date decision is authoritative.
      const at = w.kind === 'premises' && b.present_at_scene_date !== false && registry?.has(w.structure_id) ? w.structure_id : null;
      const pos = at ? position(at) : null;
      const building = pos ? displayName(registry.get(at)?.sidecar ?? {}, at).title : null;
      const limit = pos ? null : b.present_at_scene_date === false ? 'Not present at this scene date' : w.limit_reason || 'No known address';
      targets.push({ kind: 'business', group: 'businesses', id: b.id, label: b.name || b.id, at: pos ? at : null,
        sub: ['Business', b.trade || words(b.occupation), building || w.street, limit && `${limit} · open card`].filter(Boolean).join(' · '),
        limit, grade: b.grade, e: pos?.e, n: pos?.n, location_from: w.from, location_to: w.to,
        address: pos ? structureAt(at)?.address ?? null : null, owner: b.people?.[0]?.name ?? null,
        search: normal([b.name, b.trade, b.occupation, building, w.street, ...(b.goods ?? []), ...(b.firm_styles ?? []), ...(b.people ?? []).map(p => p.name)].filter(Boolean).join(' ')) });
    }
  } else {
    for (const t of targets.filter(t => t.kind === 'structure')) {
      const fn = registry.get(t.id)?.sidecar?.attributes?.function?.value ?? '';
      if (tradeFunction.test(fn.split(';')[0])) targets.push({ ...t, kind: 'business', group: 'businesses', at: t.id,
        derived_from: 'structure', sub: `Business · ${t.sub} · ${t.label}${t.limit ? ` · ${t.limit} · open card` : ''}`, search: normal(`${t.search} business`) });
    }
  }
  const keyed = new Map(targets.map(t => [`${t.kind}:${t.id}`, t]));
  const byId = (kind, id) => keyed.get(`${kind}:${id}`) ?? null;
  // `sort` (T-2740) is one of SORTS: the rows come back as one list in that order. Without
  // it, the grouped order the in-town panel's kind headings read.
  function search(q = '', { kind = 'all', includeReconstructed = false, visitor = null, sort = null } = {}) {
    const terms = normal(q).trim().split(/\s+/).filter(Boolean);
    const distance = t => positioned(visitor) && positioned(t) ? Math.hypot(t.e - visitor.e, t.n - visitor.n) : Infinity;
    const found = targets.filter(t => (includeReconstructed || !['structure', 'business'].includes(t.kind) || t.presence !== 'reconstructed')
      && (kind === 'all' || t.group === kind || t.kind === kind) && terms.every(w => t.search.includes(w)));
    if (sort) return sortRows(found, sort, visitor);
    return found.sort((a, b) => order[a.group] - order[b.group] || (terms.length ? 0 : distance(a) - distance(b)) || a.label.localeCompare(b.label));
  }
  function resolve(target, { card = true } = {}) {
    const t = target && byId(target.kind, target.id);
    if (!positioned(t)) return null;
    const structureId = t.kind === 'structure' ? t.id : t.at;
    const standOff = structureId ? (standFor?.(structureId, { card }) ?? router?.standOff?.(structureId, { e: t.e, n: t.n })) : { e: t.e, n: t.n };
    if (!positioned(standOff) || (structureId && router?.blockedAt(standOff.e, standOff.n))) return null;
    const y = terrain?.surfaceHeight(standOff.e, standOff.n);
    return { ...t, standOff: { ...standOff, ...(Number.isFinite(y) ? { y } : {}) }, structureId: structureId || null, limit: t.limit ?? null };
  }
  // An order the scene has nothing to sort on is not offered: 1835 had no house numbers yet.
  const sorts = SORTS.filter(s => (s.id !== 'address' || targets.some(t => t.address)) && (s.id !== 'owner' || targets.some(t => t.owner)));
  return { sorts, targets, kinds: ['anchor', 'intersection', 'structure', 'business', 'person'], groups: DESTINATION_GROUPS,
    search, byId, resolve, get count() { return targets.length; }, peopleAvailable: people !== null && people !== undefined };
}
