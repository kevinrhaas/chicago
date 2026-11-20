/**
 * T-3672 — a teacher's route, carried whole in one link or one file (CLASSROOM-FEATURES item 11).
 *
 * A teacher strings places (buildings and viewpoints) and people of ONE year into an order,
 * may name a jaunt for the class to take, and may add a short note and a question to any
 * stop. Nothing is uploaded and nothing is sent: the route travels in the link
 * (`?route=<base64url of compact UTF-8 JSON>`) or in a downloaded file, and a student's
 * answers go to their own field notebook on their own device.
 *
 * It follows the moment link's rules (moment.js): every value is normalized and bounded, and
 * a malformed or over-long route is refused WHOLE rather than read in part. The one thing
 * read in part is a well-formed stop this town does not hold: it is left out and counted,
 * so a student is told how many were skipped. A route for another year is not an error; it
 * names that year and the link that opens it there.
 *
 * The teacher's note and question are the teacher's own words. They are shown as such, only
 * ever as text (never markup), and nothing here composes a historical claim from them.
 *
 * Pure: no DOM, no storage. tools/test_teacher_route.mjs reads it against the real scenes.
 */
export const ROUTE_YEARS = Object.freeze(['1812', '1835', '1904']);
export const ROUTE_VERSION = 1;
export const ROUTE_FORMAT = '4d-chicago-route';
export const ROUTE_LIMITS = Object.freeze({ stops: 20, title: 80, note: 280, question: 280, url: 6000, file: 65536, answer: 2000 });
// The moment link's id rule, so a route names nothing a moment could not.
const ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$/;
/** A stop is a building, a viewpoint (Go to's, as jaunts use them) or a person. */
export const STOP_KINDS = Object.freeze(['place', 'spot', 'person']);
const PACK = { place: 'b', spot: 'v', person: 'p' };
const UNPACK = { b: 'place', v: 'spot', p: 'person' };
const KIND_OF_DESTINATION = { structure: 'place', anchor: 'spot' };

const length = (s) => Array.from(s).length;
/**
 * A teacher's text: control characters out (a line break kept where it may be), line ends
 * made one kind, runs of blank lines and spaces closed up, trimmed. Over the bound is
 * refused (null), never cut, so a link cannot say less than its teacher wrote.
 */
export function cleanText(value, max, { lines = true } = {}) {
  if (value === undefined || value === null) return '';
  if (typeof value !== 'string') return null;
  let s = value.replace(/\r\n?/g, '\n').replace(/\t/g, ' ');
  s = s.replace(lines ? /[\u0000-\u0009\u000b-\u001f\u007f-\u009f\u2028\u2029]/g : /[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g, lines ? '' : ' ');
  s = s.replace(/[ \u00a0]{2,}/g, ' ').replace(/ *\n */g, '\n').replace(/\n{3,}/g, '\n\n').trim();
  return length(s) > max ? null : s;
}

/** The one route object: `{ version, year, title, jaunt, stops: [{ kind, id, note, question }] }`, or null. */
export function normalRoute(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  if (raw.version !== undefined && Number(raw.version) !== ROUTE_VERSION) return null;
  const year = String(raw.year ?? '');
  if (!ROUTE_YEARS.includes(year)) return null;
  const title = cleanText(raw.title, ROUTE_LIMITS.title, { lines: false });
  if (title === null) return null;
  const jaunt = raw.jaunt === undefined || raw.jaunt === null || raw.jaunt === '' ? null : String(raw.jaunt);
  if (jaunt !== null && (typeof raw.jaunt !== 'string' || !ID.test(jaunt))) return null;
  if (!Array.isArray(raw.stops) || raw.stops.length > ROUTE_LIMITS.stops) return null;
  const stops = [];
  for (const s of raw.stops) {
    if (!s || typeof s !== 'object' || !STOP_KINDS.includes(s.kind) || typeof s.id !== 'string' || !ID.test(s.id)) return null;
    const note = cleanText(s.note, ROUTE_LIMITS.note), question = cleanText(s.question, ROUTE_LIMITS.question);
    if (note === null || question === null) return null;
    stops.push({ kind: s.kind, id: s.id, note, question });
  }
  if (!stops.length && !jaunt) return null;
  return { version: ROUTE_VERSION, year, title, jaunt, stops };
}

// ---- the link -------------------------------------------------------------------------- //

/** The compact form a link carries: short keys, a stop as [kind, id, note?, question?]. */
export function packRoute(route) {
  const r = normalRoute(route);
  if (!r) return null;
  const packed = { v: r.version, y: r.year, t: r.title };
  if (r.jaunt) packed.j = r.jaunt;
  packed.s = r.stops.map((s) => {
    const row = [PACK[s.kind], s.id];
    if (s.note || s.question) row.push(s.note);
    if (s.question) row.push(s.question);
    return row;
  });
  return packed;
}
export function unpackRoute(packed) {
  if (!packed || typeof packed !== 'object' || Array.isArray(packed) || !Array.isArray(packed.s)) return null;
  if (packed.s.length > ROUTE_LIMITS.stops) return null;
  const stops = [];
  for (const row of packed.s) {
    if (!Array.isArray(row) || row.length < 2 || row.length > 4 || !UNPACK[row[0]]) return null;
    stops.push({ kind: UNPACK[row[0]], id: row[1], note: row[2], question: row[3] });
  }
  return normalRoute({ version: packed.v, year: packed.y, title: packed.t, jaunt: packed.j, stops });
}

const toBase64 = (bytes) => {
  let bin = '';
  for (let i = 0; i < bytes.length; i += 4096) bin += String.fromCharCode(...bytes.subarray(i, i + 4096));
  return globalThis.btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};
/** The `route` parameter's value: base64url of the compact JSON, UTF-8. */
export function encodeRoute(route) {
  const packed = packRoute(route);
  return packed ? toBase64(new TextEncoder().encode(JSON.stringify(packed))) : null;
}
/** A `route` parameter's value back to the route, or null for anything malformed or too long. */
export function decodeRoute(param) {
  if (typeof param !== 'string' || !param || param.length > ROUTE_LIMITS.url || !/^[A-Za-z0-9_-]+$/.test(param)) return null;
  try {
    const bin = globalThis.atob(param.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (param.length % 4)) % 4));
    const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
    return unpackRoute(JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)));
  } catch { return null; }
}

/** `{ route }`, `{ error: 'long' | 'malformed' }`, or null when the page has no route link. */
export function parseRouteLink(search) {
  let params;
  try { params = new URLSearchParams(search ?? ''); } catch { return null; }
  if (!params.has('route')) return null;
  const param = params.get('route') ?? '';
  if (String(search).length > ROUTE_LIMITS.url || param.length > ROUTE_LIMITS.url) return { error: 'long' };
  const route = decodeRoute(param);
  return route ? { route, param } : { error: 'malformed' };
}

const PATH_YEAR = /\/(\d{4})(\/?(?:index\.html)?)$/;
/**
 * The link that opens `route`: this page (or, given `year`, the same page for that year), its
 * query and fragment replaced by the route alone. Null when it would pass the length bound,
 * or is not an http(s) page.
 */
export function routeLink(route, href = globalThis.location?.href, { year = null } = {}) {
  const param = encodeRoute(route);
  if (!param) return null;
  let url;
  try { url = new URL(href); } catch { return null; }
  if (!['http:', 'https:'].includes(url.protocol)) return null;
  const want = year ? String(year) : null;
  const pathYear = url.pathname.match(PATH_YEAR);
  const keepYear = url.searchParams.has('year') || (want && !pathYear);
  if (want && pathYear) url.pathname = url.pathname.replace(PATH_YEAR, `/${want}$2`);
  const yearParam = want ?? url.searchParams.get('year');
  url.search = ''; url.hash = '';
  if (keepYear && yearParam) url.searchParams.set('year', yearParam);
  url.searchParams.set('route', param);
  return url.href.length > ROUTE_LIMITS.url ? null : url.href;
}

// ---- the file -------------------------------------------------------------------------- //

/** The route as a file a teacher keeps: readable JSON, the same object the link carries. */
export function routeFileText(route) {
  const r = normalRoute(route);
  return r ? `${JSON.stringify({ format: ROUTE_FORMAT, ...r }, null, 2)}\n` : null;
}
export function routeFileName(route) {
  const slug = String(route?.title ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40);
  return `4d-chicago-route-${route?.year ?? 'town'}${slug ? `-${slug}` : ''}.json`;
}
/** A route file's text back to the route, or null: too large, not JSON, not ours, malformed. */
export function readRouteFile(text) {
  if (typeof text !== 'string' || text.length > ROUTE_LIMITS.file) return null;
  try {
    const doc = JSON.parse(text);
    return doc?.format === ROUTE_FORMAT ? normalRoute(doc) : null;
  } catch { return null; }
}

// ---- what this town holds -------------------------------------------------------------- //

export const fold = (s) => String(s ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
  .replace(/[^a-z0-9' ]+/g, ' ').replace(/\s+/g, ' ').trim();
const idOf = (field) => (field && typeof field === 'object' ? field.value : field) || null;
const words = (s) => String(s ?? '').replace(/_/g, ' ').replace(/\s+/g, ' ').trim();

/**
 * What a route can name in this scene: its buildings and viewpoints (Go to's own rows, read
 * from `targets`), its people (the scene's directory rows), and its jaunts (catalog rows a
 * class may take). Each row carries the label the town already gives it — nothing new is
 * written about any of them. `has(id)` says the building is in this scene's registry.
 */
export function routeCatalog({ year, targets = [], people = [], jaunts = [], has = () => true } = {}) {
  const rows = new Map();
  const add = (row) => { if (ID.test(row.id) && !rows.has(`${row.kind}:${row.id}`)) rows.set(`${row.kind}:${row.id}`, row); };
  for (const t of Array.isArray(targets) ? targets : []) {
    if (!t?.id || !t.label) continue;
    if (t.kind === 'structure') add({ kind: 'place', id: t.id, label: t.label, sub: t.address?.text ?? '', hay: fold(`${t.label} ${t.address?.text ?? ''} ${t.owner ?? ''}`) });
    else if (t.kind === 'anchor') add({ kind: 'spot', id: t.id, label: t.label, sub: '', hay: fold(`${t.label} ${t.short ?? ''}`) });
  }
  for (const p of Array.isArray(people) ? people : []) {
    if (!p?.id || !p.name || p.lived_here?.on_scene_date === 'no') continue;
    const home = [idOf(p.lives_at), idOf(p.works_at)].find((s) => s && has(s)) ?? null;
    const occupation = words(idOf(p.occupation));
    const work = occupation && !/^none\b/i.test(occupation) ? occupation : '';
    const household = String(p.household_name ?? '').replace(/\s+at\s+.*$/, '').replace(/\s+—.*$/, '');
    add({ kind: 'person', id: p.id, label: p.name, sub: [work, household].filter(Boolean).join(' · '), home,
      hay: fold(`${p.name} ${work} ${p.household_name ?? ''}`) });
  }
  const outings = (Array.isArray(jaunts) ? jaunts : []).filter((r) => r?.id && r.title && ID.test(r.id)
    && r.availability === 'available' && r.audience !== 'adults' && !r.version_of)
    .map((r) => ({ id: r.id, title: r.title, destinations: Array.isArray(r.destinations) ? r.destinations : [], stops: r.stop_count ?? null }))
    .sort((a, b) => a.title.localeCompare(b.title, 'en'));
  const jauntById = new Map(outings.map((j) => [j.id, j]));
  return {
    year: String(year ?? ''),
    get: (kind, id) => rows.get(`${kind}:${id}`) ?? null,
    jaunt: (id) => jauntById.get(id) ?? null,
    jaunts: outings,
    get size() { return rows.size; },
    /** Every word of the query in a row, buildings first, then viewpoints, then people. */
    search(query, limit = 8) {
      const q = fold(query).split(' ').filter(Boolean);
      if (!q.length) return [];
      const order = { place: 0, spot: 1, person: 2 };
      return [...rows.values()].filter((r) => q.every((w) => r.hay.includes(w)))
        .sort((a, b) => order[a.kind] - order[b.kind] || a.label.localeCompare(b.label, 'en')).slice(0, limit);
    },
  };
}

/** A jaunt's stops as route stops: its buildings and viewpoints this town holds, in its order. */
export function jauntStops(jaunt, catalog) {
  const stops = [];
  let dropped = 0;
  for (const d of jaunt?.destinations ?? []) {
    const kind = KIND_OF_DESTINATION[d?.kind];
    const known = kind && catalog?.get(kind, d.id);
    if (!known) { dropped++; continue; }
    const last = stops[stops.length - 1];
    if (last && last.kind === kind && last.id === d.id) continue;
    if (stops.length >= ROUTE_LIMITS.stops) { dropped++; continue; }
    stops.push({ kind, id: d.id, note: '', question: '' });
  }
  return { stops, dropped };
}

/**
 * A route as a student meets it in this year: `{ state: 'ready', … }` with each stop's label
 * from the town, the stops this town does not hold left out and counted; `{ state:
 * 'wrong-year', … }` with the link for the route's own year; or null with a message when
 * nothing of it can be shown. `message` is a string-table key and its fill.
 */
export function routeSession(parsed, { year, catalog, href = globalThis.location?.href } = {}) {
  if (!parsed) return { session: null, message: null };
  if (parsed.error || !parsed.route) return { session: null, message: { key: parsed.error === 'long' ? 'route.long' : 'route.invalid' } };
  const route = parsed.route;
  if (route.year !== String(year)) {
    const link = routeLink(route, href, { year: route.year });
    return { session: { state: 'wrong-year', route, year: route.year, link }, message: { key: 'route.otherYear', params: { year: route.year } } };
  }
  const stops = [];
  let skipped = 0;
  route.stops.forEach((s) => {
    const row = catalog?.get(s.kind, s.id);
    if (!row) { skipped++; return; }
    stops.push({ ...s, n: stops.length + 1, label: row.label, sub: row.sub ?? '', home: row.home ?? null });
  });
  const known = route.jaunt ? catalog?.jaunt(route.jaunt) : null;
  const jauntMissing = !!route.jaunt && !known;
  if (!stops.length && !known) return { session: null, message: { key: 'route.nothing', params: { n: skipped } } };
  const session = { state: 'ready', route, year: route.year, title: route.title, link: routeLink(route, href),
    stops, skipped, jaunt: known ? { id: known.id, title: known.title } : null, jauntMissing };
  const key = skipped ? (skipped === 1 ? 'route.arrivedSkippedOne' : 'route.arrivedSkipped') : 'route.arrived';
  return { session, message: { key, params: { n: skipped } } };
}

// ---- a student's answer ---------------------------------------------------------------- //

const ANSWER_LEAD = 'My answer: ';
/** The notebook title a student finds an answer by: the route, then the stop. */
export function answerTitle(session, stop) {
  return `Route: ${session?.title || 'Teacher’s route'} · Stop ${stop.n}: ${stop.label}`.slice(0, 200);
}
/** A field-notebook note for one answer: the teacher's question, marked as theirs, then the answer. */
export function answerEntry(session, stop, answer) {
  const text = cleanText(String(answer ?? ''), ROUTE_LIMITS.answer);
  if (!text) return null;
  return { kind: 'note', title: answerTitle(session, stop), year: session.year, place: stop.label,
    text: `${stop.question ? `Teacher’s question: ${stop.question}\n\n` : ''}${ANSWER_LEAD}${text}` };
}
/** The answer already in the notebook for this stop, if any: `{ id, answer }`. */
export function savedAnswer(entries, session, stop) {
  const title = answerTitle(session, stop);
  const e = [...(entries ?? [])].reverse().find((x) => x?.kind === 'note' && x.title === title && x.year === session.year);
  if (!e) return null;
  const at = String(e.text ?? '').indexOf(ANSWER_LEAD);
  return { id: e.id, answer: at >= 0 ? e.text.slice(at + ANSWER_LEAD.length) : String(e.text ?? '') };
}

// ---- the route now open on this page --------------------------------------------------- //

export function createRouteStore() {
  let current = null;
  const listeners = new Set();
  return {
    get: () => current,
    set(next) {
      current = next ?? null;
      for (const fn of listeners) { try { fn(current); } catch { /* one view cannot stop another */ } }
      return current;
    },
    clear() { return this.set(null); },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}
/** The route a student has open in this page: set by a link on landing, or a teacher's Try it. */
export const activeRoute = createRouteStore();
