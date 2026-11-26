#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * check_fire_jaunt.mjs — T-3751. Does each Great Fire stop show what its words say?
 *
 * The owner, 2026-11-26, walking The Great Chicago Fire: "Stop 3: Verify the location. The
 * narration says the user is on Jackson Street, but the scene appears to be elsewhere"; "The
 * jaunt stops at the Field Building, but the building does not burn"; "Stop 11: The narration
 * describes a burned park, but the park appears undamaged and the referenced furniture is
 * missing"; "Ensure the visual state of the environment corresponds to the chronology and
 * events described in the narration."
 *
 * A stop's `date` + `hour` is the fire's clock (city-fire.js, T-3687), and the fire map
 * (data/fire/1871.json through renderers/web/js/fire-map.js, the renderer's own module) says
 * what is burning then. EXPECT below is what each stop's words say is in front of the visitor:
 * the landmark it names burning, burnt or standing, the goods it names heaped and burnt, and the
 * corner or street it says the visitor is on. This reads the jaunt and its every telling (the
 * grade bands and the 18+), the fire map, the scene's viewpoints and the 1871 street plan, and
 * fails a stop whose scene would not show what it tells, so a moved control, a new hour or a
 * moved stand that breaks a stop is red here and not found on a walk.
 *
 * States, read RIDE minutes after the stop's hour (the drawn fire runs on at twelve fire
 * seconds to the second while the stop is read, so a stop is read over about seven minutes):
 *   burning   heat ≥ 0.5 by then: flames at its windows and over its roof
 *   catches   alight by the end of the reading (heat ≥ 0.3 within READ minutes), not before the hour
 *   burnt     blackened (char ≥ 0.8), its flames down (heat ≤ 0.35)
 *   caught    alight or burnt, whichever: caught at least `min` minutes before the hour
 *   standing  not reached by the end of the reading, or spared
 * A goods entry reads its heaps: `burnt` (every heap charred), `some_burning` (some alight).
 *
 *   node tools/check_fire_jaunt.mjs              gate: every stop of every telling
 *   node tools/check_fire_jaunt.mjs --report     each stop's reading, passing or not
 *   node tools/check_fire_jaunt.mjs --self-test  the rule must refuse the faults it was made for
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createFireMap, burnState, minutesOf, hash01 } from '../renderers/web/js/fire-map.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
export const RIDE = 2, READ = 7;
const JAUNT = 'the-great-fire';

/** What each stop's words put in front of the visitor. Stop ids are the base jaunt's. */
export const EXPECT = {
  'oleary-barn': { street: 'DeKoven Street', see: [{ structure: 'oleary_barn_1871', state: 'burning', words: '"saw the flames"' }] },
  'st-pauls': { street: 'Clinton Street', see: [{ control: 'st_pauls_church', kind: 'frame', state: 'burnt', words: '"The church is down."' }, { control: 'batehams_mills', kind: 'frame', state: 'burning', words: '"Bateham\'s mills ... are going too"' }] },
  parmelee: { corner: ['Jackson Street', 'Franklin Street'], within_m: 20, see: [{ control: 'parmelee_stables', kind: 'masonry', state: 'catches', words: '"now one has caught"' }] },
  'court-house': { corner: ['Clark Street', 'Washington Street'], within_m: 20, see: [{ structure: 'cook_county_court_house_1871', state: 'burning', words: '"Now the tower is alight."' }] },
  'sherman-house': { corner: ['Clark Street', 'Randolph Street'], within_m: 40, see: [{ structure: 'sherman_house_1871', state: 'burning', words: '"a spirit of flame came from a window"' }, { structure: 'cook_county_court_house_1871', state: 'caught', min: 20, words: '"the Court House bell comes crashing"' }] },
  crosbys: { street: 'Washington Street', see: [{ structure: 'crosbys_opera_house_1871', state: 'burning', words: '"Now the roof catches."' }] },
  'north-side': { street: 'State Street', see: [{ control: 'wrights_stable', kind: 'frame', state: 'catches', words: '"Wright\'s stable on this corner is burning"' }] },
  'water-works': { see: [{ structure: 'chicago_pumping_station_1871', state: 'burning', words: '"In an instant, the roof was aflame."' }, { structure: 'chicago_water_tower_1871', state: 'standing', words: '"The tower will stand"' }] },
  tribune: { corner: ['Dearborn Street', 'Madison Street'], within_m: 45, see: [{ structure: 'tribune_building_1871', state: 'burning', words: '"The Tribune goes"' }] },
  'state-street': { corner: ['State Street', 'Washington Street'], within_m: 20, see: [{ structure: 'field_leiter_1871', state: 'burning', words: '"The fire comes at it ... it soon yielded."' }, { structure: 'palmer_house_1871', state: 'caught', min: 30, words: '"the Palmer House is already a ruin"' }, { structure: 'crosbys_opera_house_1871', state: 'burnt', words: 'Crosby\'s, burnt at 2:20, across the way' }] },
  'ogden-house': { see: [{ structure: 'ogden_house_1871', state: 'standing', words: '"it is standing"' }, { goods: 'washington_square_goods', state: 'burnt', words: '"burned the accumulated furniture of fifty families"' }, { structure: 'washington_square_1871', state: 'burnt', words: '"until the fire came through"' }, { structure: 'st_michaels_church_1871', state: 'standing', words: '"the fire is nearing St. Michael\'s"' }] },
  'old-cemetery': { see: [{ goods: 'old_cemetery_goods', state: 'some_burning', words: '"many have watched them burn up before their eyes"' }, { structure: 'old_city_cemetery_1871', state: 'standing', words: 'the cemetery the families shelter in' }] },
};

function centreOf(id) {
  const file = path.join(ROOT, 'data/sidecars/1871', `${id}.json`);
  if (!fs.existsSync(file)) return null;
  const s = JSON.parse(fs.readFileSync(file, 'utf8')), p = s.placement ?? {}, poly = s.footprint?.polygon ?? [[0, 0]];
  const th = (p.rotation_deg ?? 0) * Math.PI / 180, c = Math.cos(th), sn = Math.sin(th);
  const u = poly.reduce((a, q) => a + q[0], 0) / poly.length, v = poly.reduce((a, q) => a + q[1], 0) / poly.length;
  return [(p.local_e ?? 0) + u * c + v * sn, (p.local_n ?? 0) - u * sn + v * c];
}

/** The goods' heaps as fire-goods.js burns them: their catch minute, or Infinity. */
function heapTimes(doc, map, id) {
  const g = (doc.goods ?? []).find((x) => x.id === id);
  if (!g) return null;
  const from = minutesOf(g.window?.from), to = minutesOf(g.window?.to);
  return (g.local_heaps ?? []).map(([e, n, , seed]) => {
    const key = `goods:${g.id}:${seed}`;
    if (g.window) return hash01(`${key}:burns`) < (g.window.share ?? 1) ? from + (to - from) * hash01(`${key}:when`) : Infinity;
    const z = map.zoneAt(e, n), h = z ? map.hourAt(e, n, z) : null;
    return h === null ? Infinity : h + (map.model.jitter_min ?? 6) * (hash01(key) - 0.5) * 2;
  });
}

function stateOf(kind, tc, t, model, rain) {
  if (tc === null || !Number.isFinite(tc)) return { heat: 0, char: 0, never: true };
  return burnState(kind, t - tc, model, { rainAfter: Number.isFinite(rain) ? t - rain : null });
}

/** Does `want` hold for a place that catches at `tc` (minutes), seen from a stop at `t0`? */
export function judge(want, kind, tc, t0, model, rain, min = 0) {
  const at = stateOf(kind, tc, t0 + RIDE, model, rain), end = stateOf(kind, tc, t0 + READ, model, rain);
  const never = tc === null || !Number.isFinite(tc);
  switch (want) {
    case 'burning': return at.heat >= 0.5;
    case 'catches': return !never && tc >= t0 - 3 && end.heat >= 0.3;
    case 'burnt': return at.char >= 0.8 && at.heat <= 0.35;
    case 'caught': return !never && tc <= t0 - min;
    case 'standing': return never || tc > t0 + READ;
    default: throw Error(`unknown state ${want}`);
  }
}

function streetsNamed(ctx, name) {
  return ctx.streets.filter((s) => s.name && (s.name === name || s.name.replace(/^(North|South|West|East) /, '') === name));
}
function crossing(a, b, c, d) {
  const den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0]);
  if (Math.abs(den) < 1e-9) return null;
  const t = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / den, u = -((a[0] - b[0]) * (a[1] - c[1]) - (a[1] - b[1]) * (a[0] - c[0])) / den;
  return t >= -0.01 && t <= 1.01 && u >= -0.01 && u <= 1.01 ? [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])] : null;
}
function cornerOf(ctx, A, B) {
  const out = [];
  for (const s of streetsNamed(ctx, A)) for (const r of streetsNamed(ctx, B)) { const p = crossing(s.a, s.b, r.a, r.b); if (p) out.push(p); }
  return out;
}
function segDist(p, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy, t = L ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) : 0;
  return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
}
/** On the street: inside its carriageway and walks. */
function onStreet(ctx, name, p) {
  return streetsNamed(ctx, name).some((s) => segDist(p, s.a, s.b) <= s.width_m / 2 + (s.walk_m ?? 0) + 1.5);
}

export function check({ fire, scene, ctx, jaunts, expect = EXPECT }) {
  const map = createFireMap(fire), rows = [], fails = [];
  const anchors = new Map(scene.anchors.map((a) => [a.id, a]));
  const controls = new Map(fire.controls.map((c) => [c.id, c]));
  const base = jaunts.find((j) => j.id === JAUNT);
  if (!base) return { rows, fails: [`${JAUNT}: not found`] };
  for (const j of jaunts) {
    if (j.id !== JAUNT && j.version_of !== JAUNT) continue;
    const ids = j.stops.map((s) => s.id).join(' '), want = base.stops.map((s) => s.id).join(' ');
    if (ids !== want) fails.push(`${j.id}: its stops (${ids}) are not the base jaunt's (${want})`);
    for (const s of j.stops) {
      const b = base.stops.find((x) => x.id === s.id);
      if (b && (s.date !== b.date || s.hour !== b.hour || s.destination?.id !== b.destination?.id)) fails.push(`${j.id} ${s.id}: its hour or place is not the base jaunt's (${s.date} ${s.hour} ${s.destination?.id})`);
    }
  }
  for (const s of base.stops) {
    const ex = expect[s.id];
    if (!ex) { fails.push(`${s.id}: no expectation written for this stop (add it to EXPECT)`); continue; }
    const t0 = minutesOf(`${s.date}T${s.hour}`), a = anchors.get(s.destination?.id);
    if (!a) { fails.push(`${s.id}: viewpoint ${s.destination?.id} is not in the scene`); continue; }
    const at = [a.local_e, a.local_n];
    if (ex.corner) {
      const cs = cornerOf(ctx, ...ex.corner), d = cs.length ? Math.min(...cs.map((c) => Math.hypot(c[0] - at[0], c[1] - at[1]))) : Infinity;
      const ok = d <= ex.within_m;
      rows.push({ stop: s.id, what: `stands at ${ex.corner.join(' and ')}`, ok, reading: `${Number.isFinite(d) ? d.toFixed(1) : 'no such corner'} m (≤ ${ex.within_m})` });
      if (!ok) fails.push(`${s.id}: the words put you at ${ex.corner.join(' and ')}, but the stand is ${Number.isFinite(d) ? `${d.toFixed(1)} m` : 'nowhere near'} from that corner of the plan`);
    }
    if (ex.street) {
      const ok = onStreet(ctx, ex.street, at);
      rows.push({ stop: s.id, what: `stands on ${ex.street}`, ok, reading: ok ? 'on it' : 'off it' });
      if (!ok) fails.push(`${s.id}: the words put you on ${ex.street}, but the stand is not on it`);
    }
    for (const w of ex.see) {
      let ok, reading;
      if (w.goods) {
        const times = heapTimes(fire, map, w.goods);
        if (!times?.length) { fails.push(`${s.id}: goods ${w.goods} are not in the fire map`); continue; }
        const g = fire.goods.find((x) => x.id === w.goods), appear = minutesOf(g.appear) ?? -Infinity;
        const sts = times.map((tc) => stateOf('frame', tc, t0 + RIDE, map.model, map.rain));
        const burning = sts.filter((x) => x.heat >= 0.3).length, charred = sts.filter((x) => x.char >= 0.8).length;
        ok = appear <= t0 && (w.state === 'burnt' ? charred === times.length : burning > 0);
        reading = `${times.length} heaps on the ground ${appear <= t0 ? 'by then' : 'NOT YET'}: ${burning} alight, ${charred} charred`;
      } else {
        let tc, kind = w.kind ?? 'masonry';
        if (w.structure) {
          if (map.fateOf(w.structure) === 'survives') tc = null;
          else {
            const c = centreOf(w.structure);
            if (!c) { fails.push(`${s.id}: structure ${w.structure} has no 1871 sidecar`); continue; }
            tc = map.catchAt(c[0], c[1], w.structure);
            kind = map.fateOf(w.structure) === 'collapses' ? 'frame' : 'masonry';
          }
        } else {
          const c = controls.get(w.control);
          if (!c) { fails.push(`${s.id}: timed place ${w.control} is not in the fire map`); continue; }
          tc = map.catchAt(c.local[0], c.local[1], null);
        }
        ok = judge(w.state, kind, tc, t0, map.model, map.rain, w.min ?? 0);
        const st = stateOf(kind, tc, t0 + RIDE, map.model, map.rain);
        reading = tc === null || !Number.isFinite(tc) ? 'never burns' : `catches ${Math.round(tc - t0)} min from the hour; heat ${st.heat.toFixed(2)} char ${st.char.toFixed(2)}`;
      }
      const what = `${w.structure ?? w.control ?? w.goods} ${w.state}`;
      rows.push({ stop: s.id, what, ok, reading });
      if (!ok) fails.push(`${s.id} (${s.date} ${s.hour}): ${w.words} — but ${what.replace(/ \w+$/, '')} is not ${w.state} (${reading})`);
    }
  }
  return { rows, fails };
}

function load() {
  const dir = path.join(ROOT, 'data/jaunts');
  const jaunts = fs.readdirSync(dir).filter((f) => f.startsWith(JAUNT) && f.endsWith('.json')).map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
  return { fire: read('data/fire/1871.json'), scene: read('data/scenes/1871.json'), ctx: read('data/context/1871.json'), jaunts };
}

function selfTest() {
  const real = load(), clone = (x) => JSON.parse(JSON.stringify(x));
  assert.deepEqual(check(real).fails, [], 'the committed jaunt passes');
  // The stand of stop 3 back where the owner found it, on Quincy Street.
  const moved = clone(real); moved.scene.anchors.find((a) => a.id === 'fire_parmelee_stables').local_e = 192; moved.scene.anchors.find((a) => a.id === 'fire_parmelee_stables').local_n = -902;
  assert.ok(check(moved).fails.some((f) => f.startsWith('parmelee: the words put you at Jackson Street and Franklin Street')), 'a stand off its corner is refused');
  // Field, Leiter & Co. burnt out at 3:45, as the fire map had it.
  const early = clone(real); delete early.fire.structures.field_leiter_1871.burning_by;
  assert.ok(check(early).fails.some((f) => f.startsWith('state-street') && f.includes('field_leiter_1871 is not burning')), 'a landmark burnt hours before its stop is refused');
  // No goods in Washington Square.
  const bare = clone(real); bare.fire.goods = bare.fire.goods.filter((g) => g.id !== 'washington_square_goods');
  assert.ok(check(bare).fails.some((f) => f.includes('washington_square_goods are not in the fire map')), 'a park with no furniture is refused');
  // A telling that moves a stop's hour.
  const drift = clone(real); drift.jaunts.find((j) => j.version_of === JAUNT).stops[9].hour = '03:45';
  assert.ok(check(drift).fails.some((f) => f.includes('its hour or place is not the base jaunt')), 'a telling whose hour drifts is refused');
  // A stop nobody wrote down.
  const noted = clone(real); noted.jaunts.find((j) => j.id === JAUNT).stops[0].id = 'somewhere-else';
  assert.ok(check(noted).fails.some((f) => f.startsWith('somewhere-else: no expectation')), 'an unexamined stop is refused');
  assert.equal(judge('burning', 'masonry', null, 600, {}, null), false);
  assert.equal(judge('standing', 'masonry', null, 600, {}, null), true);
  console.log('FIRE JAUNT SELF-TEST PASS — a stand off its corner, a landmark burnt before its stop, a park without its furniture, a telling with another hour and a stop with no expectation are each refused');
}

if (process.argv.includes('--self-test')) selfTest();
else {
  const { rows, fails } = check(load());
  if (process.argv.includes('--report')) for (const r of rows) console.log(`${r.ok ? 'ok  ' : 'FAIL'} ${r.stop.padEnd(14)} ${r.what.padEnd(44)} ${r.reading}`);
  for (const f of fails) console.log(`FAIL ${f}`);
  if (fails.length) { console.log(`FIRE JAUNT FAIL — ${fails.length} stop reading(s) do not show what their words say`); process.exit(1); }
  console.log(`FIRE JAUNT PASS — ${rows.length} readings over ${Object.keys(EXPECT).length} stops: every Great Fire stop shows what it tells, in every telling`);
}
