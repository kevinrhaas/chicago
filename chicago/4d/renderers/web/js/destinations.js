/** One inventory for in-world search and the future arrival picker (T-1277).
 * Unknown addresses stay unknown. The public business index, when present,
 * owns firm identity and scene-date location; fallback rows are explicitly derived.
 */
import { displayName, searchTerms } from './display-name.js';
import { KINDS, placeKind, presenceGrade } from './place-kinds.js';

export const normal = value => String(value ?? '').toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
const words = value => String(value ?? '').replace(/_/g, ' ').replace(/\s+/g, ' ').trim();
const idOf = field => (field && typeof field === 'object' ? field.value : field) || null;
const positioned = p => Number.isFinite(p?.e) && Number.isFinite(p?.n);
const CARDINALS = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
export const DESTINATION_GROUPS = [...KINDS.slice(0, 3), { id: 'businesses', label: 'Businesses' }, ...KINDS.slice(3)];
const labels = Object.fromEntries(DESTINATION_GROUPS.map(k => [k.id, k.label]));
const order = Object.fromEntries(DESTINATION_GROUPS.map((k, i) => [k.id, i]));
const tradeFunction = /(?:^|_)(?:store|shop|warehouse|manufactory|tannery|brickyard)(?:_|$)|tavern_inn|auction_room|printing_office|boarding_house|hotel_stable/;

export function createDestinations({ scene, index, registry, people, positionOf, businesses = null,
  standFor = null, router = null, terrain = null } = {}) {
  const targets = [];
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
      presence: presenceGrade(s), position: s.placement?.position_confidence || 'reconstructed',
      e: pos?.e, n: pos?.n, limit: pos ? null : 'No known address',
      search: normal([searchTerms(s, id), fn, labels[group]].filter(Boolean).join(' ')) });
  }
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
      grade: p.grade ?? null, e: pos?.e, n: pos?.n,
      search: normal([p.name, occ, p.household_name, building, 'person'].filter(Boolean).join(' ')) });
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
  function search(q = '', { kind = 'all', includeReconstructed = false, visitor = null } = {}) {
    const terms = normal(q).trim().split(/\s+/).filter(Boolean);
    const distance = t => positioned(visitor) && positioned(t) ? Math.hypot(t.e - visitor.e, t.n - visitor.n) : Infinity;
    return targets.filter(t => (includeReconstructed || !['structure', 'business'].includes(t.kind) || t.presence !== 'reconstructed')
      && (kind === 'all' || t.group === kind || t.kind === kind) && terms.every(w => t.search.includes(w)))
      .sort((a, b) => order[a.group] - order[b.group] || (terms.length ? 0 : distance(a) - distance(b)) || a.label.localeCompare(b.label));
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
  return { targets, kinds: ['anchor', 'intersection', 'structure', 'business', 'person'], groups: DESTINATION_GROUPS,
    search, byId, resolve, get count() { return targets.length; }, peopleAvailable: people !== null && people !== undefined };
}
