#!/usr/bin/env node
/**
 * today_registration.mjs — the control points that line the Today window up with the
 * scene's own ground, year by year (Kevin, 2026-11-16).
 *
 * The owner: "Google Maps and the land we have may need some repositioning like in today
 * we are in the middle of the river near the north bank but in 1812 we are on the south
 * bank, can you match things up more accurately across the board?"
 *
 * WHY THE TWO DISAGREE. today-geo.js turns the scene's local metres into latitude and
 * longitude exactly (UTM 16N less the datum origin). The frame is right; what sits in it
 * is not everywhere where today's map has it. The 1835 town's streets were laid on
 * OpenStreetMap's own corners and agree with today's to a few metres; the 1904 Prairie
 * Avenue grid, georeferenced from the Sanborn sheets, to one or two. But the fort and
 * the river beside it were traced off the 1834 surveys, whose affine fit carries 17 to
 * 58 m (data/datum.json § derivation.residual_note), and the north-side tracts were
 * ruled off the same sheets: there the scene stands tens of metres north of today's
 * ground. So a spot by the fort asked Google for a spot in the river.
 *
 * WHAT THIS DERIVES. Pairs of points, each a place that is the same place in the scene
 * and today: the scene's position of it and today's, both in local metres.
 *   - Street crossings. Every crossing of two 1835 streets that today's City centreline
 *     file (data/modern/streets.json) also has, under the street's 2026 name the 1835
 *     record carries (`name_2026`), and every crossing of the 1904 grid's carriageways
 *     with their 2026 names. Streets are the survey that survives: the plats' lines are
 *     today's lines. A street the record grades `reconstructed` is not a survey and is
 *     left out, and so is a crossing more than MAX_MISS_M from today's.
 *   - The fort. The City's landmark site of Fort Dearborn (data/modern/landmark_sites.json),
 *     the intersection of Michigan Avenue and Wacker Drive, which marks the fort's southern
 *     perimeter, against the middle of the scene's south curtain: the first fort's outer
 *     pickets in 1812, the 1816 fort's palisade in 1835. The river is NOT a control: its banks moved (the 1833 cut, the wharfing,
 *     and the widening the fort itself was pulled down for in 1856, docs/research/
 *     04-structures-south.md), and the point is to stand at the same PLACE. So the
 *     1812 south bank, north of the fort, lands in today's river: the channel of about
 *     90 ft that ran past the fort is today's north half, and the fort's own north end
 *     lies under the south half and the bridge.
 * Each year takes the crossings (its ground and the town's plat are one frame) and its
 * own fort; 1904 has no fort. The renderer interpolates between them
 * (renderers/web/js/today-register.js), and that table is this tool's output, checked by
 * tools/test_today_view.mjs.
 *
 *   node tools/today_registration.mjs           print the table today-register.js holds
 *   node tools/today_registration.mjs --report  and each control's miss, for a reader
 *
 * It writes nothing. Today's view is a navigation aid: no period layer moves because of it.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { latLngToLocal } from '../renderers/web/js/today-geo.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const readJson = (p) => JSON.parse(readFileSync(path.join(APP, p), 'utf8'));

/** A crossing further than this from today's is a different crossing, not an error. */
export const MAX_MISS_M = 60;
/** 1871: the river's middle is paired every this many metres along the scene's channel. */
export const RIVER_STEP_M = 100;
/** 1871: today's channel further than this from the scene's is not the same reach. */
export const RIVER_MAX_M = 90;
/** 1871: today's channel must be one plain channel across, not a junction or a turning basin. */
export const RIVER_WIDTH_M = [20, 110];
/** 1871: the reaches paired (the forks' outer channels, the canal and the editorial extensions are not). */
const RIVERS_1871 = ['main_stem', 'north_branch', 'north_branch_canal', 'south_branch'];
/** A street's line is carried this far past its end, so a T-junction is a crossing. */
const REACH_M = 12;

/** "N/S Canal Street" -> "CANAL"; "E 18th St" -> "18TH". */
export function streetCore(name) {
  let n = String(name ?? '').split(/[,(]/)[0].trim().toUpperCase();
  n = n.replace(/^(NORTH|SOUTH|EAST|WEST) /, '');
  n = n.replace(/^(N|S|E|W)(\/(N|S|E|W))? /, '');
  n = n.replace(/ (ST|STREET|AVE|AVENUE|DR|DRIVE|BLVD|BOULEVARD|PL|PLACE|CT|COURT|RD|ROAD)$/, '');
  return n.trim();
}

function segX(a, b, c, d, reach = 0) {
  const r = [b[0] - a[0], b[1] - a[1]], s = [d[0] - c[0], d[1] - c[1]];
  const den = r[0] * s[1] - r[1] * s[0];
  if (Math.abs(den) < 1e-9) return null;
  const t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den;
  const u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den;
  const lr = Math.hypot(...r), ls = Math.hypot(...s);
  const ta = reach / lr, ua = reach / ls;
  if (t < -ta || t > 1 + ta || u < -ua || u > 1 + ua) return null;
  // Crossings at a shallow angle are not points: two lines 15° apart wander a long way.
  const sin = Math.abs(den) / (lr * ls);
  if (sin < Math.sin(35 * Math.PI / 180)) return null;
  return [a[0] + t * r[0], a[1] + t * r[1]];
}

/** Where segment ab meets segment cd at any angle (a bank against a line across the river). */
function segHit(a, b, c, d) {
  const r = [b[0] - a[0], b[1] - a[1]], s = [d[0] - c[0], d[1] - c[1]];
  const den = r[0] * s[1] - r[1] * s[0];
  if (Math.abs(den) < 1e-12) return null;
  const t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den;
  const u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den;
  return t >= 0 && t <= 1 && u >= 0 && u < 1 ? [a[0] + t * r[0], a[1] + t * r[1]] : null;
}

/** Every crossing of polyline set A with polyline set B. */
function crossings(linesA, linesB, reach) {
  const out = [];
  for (const la of linesA) for (const lb of linesB) {
    for (let i = 0; i + 1 < la.length; i++) for (let j = 0; j + 1 < lb.length; j++) {
      // Reach only past a line's own ends, never inside it.
      const ra = (i === 0 || i + 2 === la.length) ? reach : 0;
      const rb = (j === 0 || j + 2 === lb.length) ? reach : 0;
      const p = segX(la[i], la[i + 1], lb[j], lb[j + 1], Math.max(ra, rb));
      if (p && !out.some((q) => Math.hypot(q[0] - p[0], q[1] - p[1]) < 3)) out.push(p);
    }
  }
  return out;
}

function modernIndex(doc) {
  const by = new Map();
  for (const s of doc.segments) {
    const core = streetCore(doc.names[s[0]]);
    const flat = s[9];
    const line = [];
    for (let i = 0; i + 1 < flat.length; i += 2) line.push([flat[i], flat[i + 1]]);
    if (!by.has(core)) by.set(core, []);
    by.get(core).push(line);
  }
  return by;
}

/** Area centroid of a closed ring. */
function centroid(ring) {
  let a = 0, x = 0, y = 0;
  for (let i = 0; i + 1 < ring.length; i++) {
    const [x0, y0] = ring[i], [x1, y1] = ring[i + 1];
    const c = x0 * y1 - x1 * y0;
    a += c; x += (x0 + x1) * c; y += (y0 + y1) * c;
  }
  return [x / (3 * a), y / (3 * a)];
}

/** A structure phase's footprint in local metres (the renderer's own placement). */
function footprintRing(file, phaseId, origin) {
  const rec = readJson(`data/structures/${file}.json`);
  const ph = rec.phases.find((p) => p.id === phaseId);
  const e0 = ph.position.utm_e - origin.e, n0 = ph.position.utm_n - origin.n;
  const th = (ph.position.rotation_deg ?? 0) * Math.PI / 180;
  const ring = ph.footprint.polygon.map(([u, v]) => [e0 + u * Math.cos(th) + v * Math.sin(th), n0 - u * Math.sin(th) + v * Math.cos(th)]);
  return ring;
}

/** The middle of a footprint's south side: its two southernmost corners' midpoint. */
function southSideMiddle(ring) {
  const [a, b] = ring.slice().sort((p, q) => p[1] - q[1]);
  return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
}

const r1 = (v) => Math.round(v * 10) / 10;

export function deriveControls() {
  const datum = readJson('data/datum.json');
  const origin = { e: datum.origin_utm_e, n: datum.origin_utm_n };
  const modern = modernIndex(readJson('data/modern/streets.json'));
  const controls = [];
  const dropped = [];
  const take = (id, years, scene, today, kind) => {
    // One crossing reached from two carriageways (or two blocks of one street) is one control.
    if (controls.some((c) => c.years.join() === years.join()
      && Math.hypot(c.scene[0] - scene[0], c.scene[1] - scene[1]) < 4)) return;
    const miss = Math.hypot(today[0] - scene[0], today[1] - scene[1]);
    controls.push({ id, kind, years, scene: scene.map(r1), today: today.map(r1), miss_m: r1(miss) });
  };

  const pairUp = (streets, years, label) => {
    for (let i = 0; i < streets.length; i++) for (let j = i + 1; j < streets.length; j++) {
      const A = streets[i], B = streets[j];
      if (A.core === B.core) continue;
      const ma = modern.get(A.core), mb = modern.get(B.core);
      if (!ma || !mb) continue;
      const here = crossings([A.line], [B.line], REACH_M);
      if (!here.length) continue;
      const today = crossings(ma, mb, REACH_M);
      for (const p of here) {
        let best = null, bd = Infinity;
        for (const q of today) { const d = Math.hypot(q[0] - p[0], q[1] - p[1]); if (d < bd) { bd = d; best = q; } }
        const id = `${label}:${A.id}x${B.id}`;
        if (!best || bd > MAX_MISS_M) { dropped.push({ id, why: best ? `today's crossing ${r1(bd)} m off` : 'no crossing today' }); continue; }
        take(id, years, p, best, 'street_crossing');
      }
    }
  };

  // The 1835 plat's streets, with the 2026 names their records carry.
  const s1835 = readJson('data/streets/1835.json').streets
    .filter((s) => s.geometry_confidence !== 'reconstructed' && s.name_2026)
    .map((s) => ({ id: s.id, core: streetCore(s.name_2026), line: s.path_local_enu_m }))
    .filter((s) => modern.has(s.core));
  pairUp(s1835, ['1812', '1835', '1904'], '1835');

  // The 1904 grid: each carriageway's centreline, end to end, under its 2026 name.
  const grid = readJson('data/street_grid/1904.json');
  const lines = new Map();
  for (const cw of grid.carriageways) {
    const st = grid.streets[cw.street];
    const core = streetCore(st?.name_2026);
    if (!modern.has(core) || /re-laid|vacated/i.test(st?.name_2026 ?? '')) continue;
    const q = cw.polygon_local_m;
    const a = [(q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2];
    const b = [(q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2];
    lines.set(cw.id, { id: cw.id, core, line: [a, b] });
  }
  pairUp([...lines.values()], ['1812', '1835', '1904'], '1904');

  // The fort: the City's landmark site, which marks its southern perimeter, against the
  // middle of each fort's south curtain.
  const sites = readJson('data/modern/landmark_sites.json').sites;
  const fortSite = sites.find((s) => s.id === 'site_of_fort_dearborn');
  const fortToday = centroid(fortSite.polygon_lnglat.map(([lng, lat]) => latLngToLocal(lat, lng)));
  take('fort:first_fort_1803', ['1812'], southSideMiddle(footprintRing('first_fort_dearborn_pickets_outer', 'first_fort_1803', origin)), fortToday, 'landmark_site');
  take('fort:picket_1816', ['1835'], southSideMiddle(footprintRing('fort_dearborn_palisade', 'picket_1816', origin)), fortToday, 'landmark_site');

  // 1871 (Kevin, 2026-11-19: "from the today view in 1871 it seems like the today view sits
  // further west where i am standing ... like we are standing on the shore and in today
  // view we are in the river"). The 1871 city is not laid on the 1835 plat: its named
  // streets, its river and its shore were all read off Mitchell's 1870 map through one
  // affine fit (data/context/1871/plan.json map_control, 18.7 m RMS, 40 m at worst), and
  // the river's line wanders 20 to 80 m from today's channel. So 1871 takes its own
  // controls and none of the 1835 plat's.
  //   - The fit's own corners: each named crossing the fit and its checks hold, where the
  //     fit puts it in the scene (its pixel through the affine) against where OpenStreetMap
  //     puts it today (the control's modern_control).
  //   - The river. By 1871 the Chicago River ran between dock lines, and in most reaches
  //     today's banks are those docks (the channel since is the same water, give or take
  //     a widening): the 1871 river's distance from today's is the map reading, not the
  //     river moving. So every RIVER_STEP_M along the scene's main stem, Branches and North
  //     Branch Canal, the middle of the scene's channel is paired with the middle of
  //     today's (data/modern/chicago_river.json, the City's own water polygons) across it,
  //     where today's is one plain channel (RIVER_WIDTH_M) no more than RIVER_MAX_M off.
  //     Left out where the river DID move: the South Branch between Polk and Eighteenth
  //     Streets, straightened about a quarter mile west in 1928-30 (the scene's channel
  //     there is the old bend, and standing on it is standing on today's dry ground), and
  //     the mouth east of the 1871 shore, since rebuilt as harbour and lock.
  const plan = readJson('data/context/1871/plan.json');
  const fit = plan.map_control.coefficients;
  const affine = ([px, py]) => [fit.a * px + fit.b * py + fit.c, fit.d * px + fit.e * py + fit.f];
  for (const c of plan.map_control.controls) {
    // Today's corner: OpenStreetMap's intersection the control was read against.
    const today = latLngToLocal(c.modern_control.lat, c.modern_control.lon);
    take(`1871:map_${c.id}`, ['1871'], affine(c.pixel), today, 'map_fit_corner');
  }
  const water = readJson('data/modern/chicago_river.json').polygons
    .map((p) => p.rings.map((r) => r.map(([lng, lat]) => latLngToLocal(lat, lng))));
  const inWater = (q) => {
    let k = false;
    for (const poly of water) for (const r of poly) {
      for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
        const [xi, yi] = r[i], [xj, yj] = r[j];
        if ((yi > q[1]) !== (yj > q[1]) && q[0] < (xj - xi) * (q[1] - yi) / (yj - yi) + xi) k = !k;
      }
    }
    return k;
  };
  // Today's channel across the scene's at c (unit normal nv): the water interval nearest
  // the scene's middle, as offsets along nv, or null.
  const across = (c, nv) => {
    const a = [c[0] - nv[0] * 200, c[1] - nv[1] * 200], b = [c[0] + nv[0] * 200, c[1] + nv[1] * 200];
    const ts = [];
    for (const poly of water) for (const r of poly) for (let i = 0; i + 1 < r.length; i++) {
      const p = segHit(a, b, r[i], r[i + 1]);
      if (p) ts.push(Math.hypot(p[0] - a[0], p[1] - a[1]) - 200);
    }
    ts.sort((x, y) => x - y);
    let best = null;
    for (let k = 0; k + 1 < ts.length; k++) {
      const m = (ts[k] + ts[k + 1]) / 2;
      if (ts[k + 1] - ts[k] < 0.5 || !inWater([c[0] + nv[0] * m, c[1] + nv[1] * m])) continue;
      if (!best || Math.abs(m) < Math.abs(best.m)) best = { m, width: ts[k + 1] - ts[k] };
    }
    return best;
  };
  const insideBoundary = (q) => {
    let k = false;
    const r = plan.boundary;
    for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      const [xi, yi] = r[i], [xj, yj] = r[j];
      if ((yi > q[1]) !== (yj > q[1]) && q[0] < (xj - xi) * (q[1] - yi) / (yj - yi) + xi) k = !k;
    }
    return k;
  };
  const streetN = (id) => {
    const pts = plan.streets.find((s) => s.id === id).points;
    return pts.reduce((acc, p) => acc + p[1], 0) / pts.length;
  };
  const straightened = [streetN('eighteenth_street'), streetN('polk_street')];
  for (const id of RIVERS_1871) {
    const pts = plan.rivers.find((r) => r.id === id).points;
    let carry = 0, k = 0;
    for (let i = 0; i + 1 < pts.length; i++) {
      const a = pts[i], b = pts[i + 1];
      const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      if (L < 1) continue;
      const u = [(b[0] - a[0]) / L, (b[1] - a[1]) / L], nv = [-u[1], u[0]];
      for (let s = carry; s < L; s += RIVER_STEP_M) {
        const c = [a[0] + u[0] * s, a[1] + u[1] * s];
        const rid = `1871:river_${id}_${String(k++).padStart(3, '0')}`;
        if (id === 'south_branch' && c[1] > straightened[0] && c[1] < straightened[1]) {
          dropped.push({ id: rid, why: 'straightened 1928-30' }); continue;
        }
        if (!insideBoundary(c)) { dropped.push({ id: rid, why: 'past the 1871 shore or limits' }); continue; }
        const t = across(c, nv);
        if (!t) { dropped.push({ id: rid, why: 'no channel today' }); continue; }
        if (Math.abs(t.m) > RIVER_MAX_M || t.width < RIVER_WIDTH_M[0] || t.width > RIVER_WIDTH_M[1]) {
          dropped.push({ id: rid, why: `today's channel ${r1(t.m)} m off, ${r1(t.width)} m wide` }); continue;
        }
        take(rid, ['1871'], c, [c[0] + nv[0] * t.m, c[1] + nv[1] * t.m], 'river_middle');
      }
      carry = ((carry - L) % RIVER_STEP_M + RIVER_STEP_M) % RIVER_STEP_M;
    }
  }

  controls.sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  return { controls, dropped };
}

/** The table as today-register.js holds it: [id, years, sceneE, sceneN, todayE, todayN]. */
export function controlTable(controls) {
  return controls.map((c) => [c.id, c.years.join(' '), ...c.scene, ...c.today]);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const { controls, dropped } = deriveControls();
  if (process.argv.includes('--report')) {
    for (const c of controls) console.log(`${c.id.padEnd(48)} ${c.years.join(',').padEnd(15)} miss ${String(c.miss_m).padStart(5)} m  scene ${c.scene}  today ${c.today}`);
    for (const d of dropped) console.log(`dropped ${d.id}: ${d.why}`);
    console.log(`${controls.length} controls, ${dropped.length} dropped`);
  } else {
    console.log(controlTable(controls).map((r) => `  ${JSON.stringify(r)},`).join('\n'));
  }
}
