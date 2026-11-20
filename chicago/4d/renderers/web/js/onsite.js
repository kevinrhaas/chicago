/**
 * onsite.js — the on-site tour (T-3674): a walk you take on the real Prairie Avenue,
 * holding a phone or tablet in Window mode (controls/window.js), from stop to stop to
 * the Glessner House.
 *
 * The owner, 2026-11-19, gap-analysis item 16 ("On-site mode"; docs/CLASSROOM-FEATURES.md).
 * The tour is data (data/onsite/prairie_1904.json): an ordered list of stops, each with
 * where you stand today (latitude and longitude, derived from the 1904 parcel's street
 * front and checked against the City's landmark lot by tools/check_onsite_tour.mjs) and
 * a short card citing existing source records.
 *
 * What a fix does, here:
 *  - DISTANCE and DIRECTION to the stop you are walking to, from the fix itself (today's
 *    latitude and longitude against the stop's), never from where the scene put you.
 *  - ARRIVAL only at the stop in hand, in order, when the fix is inside a radius scaled
 *    to the accuracy the device reports (ARRIVE_MIN_M plus the accuracy, at most
 *    ARRIVE_MAX_M). A fix rougher than ROUGH_FIX_M calls no arrival at all and says so;
 *    "I'm here" is always there for the visitor to say it instead.
 *  - OFF THE GROUND: a fix more than GROUND_MARGIN_M outside the stops' own box is "off
 *    the tour's ground". The tour says how far the next stop is, and Window mode is asked
 *    to hold the visitor where they are (`hold`), so a fix at home never walks anybody
 *    to Prairie Avenue.
 *
 * Arrival does not move the tour on: the card shows the stop you reached and the way to
 * the next, and "Next stop" takes it there, so a stop 17 m from the last is not skipped
 * because one fix covers both. Pure: no DOM, no THREE, no fetch.
 */
import { distanceM, trueBearing } from './today-geo.js';

/** The one year the tour is offered in. */
export const ONSITE_YEAR = '1904';
/** The smallest arrival radius, metres (a fix reporting ±0 m, or ?window-at=). */
export const ARRIVE_MIN_M = 10;
/** The largest arrival radius, metres: past this the stops would swallow their neighbours. */
export const ARRIVE_MAX_M = 35;
/** A fix reporting worse than this calls no arrival; the visitor says "I'm here". */
export const ROUGH_FIX_M = 35;
/** How far outside the stops' own box the tour's ground reaches, metres. */
export const GROUND_MARGIN_M = 150;

/** The arrival radius for a fix of this reported accuracy (metres). */
export function arrivalRadius(accuracy) {
  const a = Math.max(0, Number(accuracy) || 0);
  return Math.min(ARRIVE_MAX_M, ARRIVE_MIN_M + a);
}

const POINTS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
/** A bearing (degrees clockwise from north) as one of eight compass points. */
export function compassPoint(deg) {
  const d = ((Number(deg) % 360) + 360) % 360;
  return POINTS[Math.round(d / 45) % 8];
}

/** The smallest signed turn from `from` to `to`, degrees, -180..180 (+ is to the right). */
export function turnDeg(to, from) {
  let d = (Number(to) - Number(from)) % 360;
  if (d > 180) d -= 360;
  if (d < -180) d += 360;
  return d;
}

/** A distance said plainly: "8 m", "140 m", "2.4 km". */
export function sayDistance(m) {
  const v = Math.max(0, Number(m) || 0);
  if (v >= 1000) return `${(Math.round(v / 100) / 10).toFixed(1)} km`;
  return `${Math.round(v)} m`;
}

/**
 * What is wrong with a tour document, as lines (none when it is sound): an id, a scene, at
 * least two stops, unique ids, a finite latitude and longitude, a title, text and at least
 * one source for each stop, and each source's citation carried.
 */
export function tourProblems(doc) {
  const out = [];
  if (!doc || typeof doc !== 'object') return ['no tour document'];
  if (!doc.id) out.push('the tour has no id');
  if (String(doc.scene) !== ONSITE_YEAR) out.push(`the tour's scene is ${doc.scene}, not ${ONSITE_YEAR}`);
  const stops = Array.isArray(doc.stops) ? doc.stops : [];
  if (stops.length < 2) out.push('a tour needs at least two stops');
  const seen = new Set();
  for (const s of stops) {
    const at = s?.id || '(no id)';
    if (!s?.id) out.push('a stop has no id');
    else if (seen.has(s.id)) out.push(`stop ${s.id} appears twice`);
    seen.add(s?.id);
    if (!Number.isFinite(s?.lat) || !Number.isFinite(s?.lon) || Math.abs(s.lat) > 90 || Math.abs(s.lon) > 180) out.push(`stop ${at} has no position`);
    if (!s?.title) out.push(`stop ${at} has no title`);
    if (!s?.text) out.push(`stop ${at} has no text`);
    if (!Array.isArray(s?.sources) || !s.sources.length) out.push(`stop ${at} cites no source`);
    for (const id of s?.sources || []) if (!doc.citations?.[id]) out.push(`stop ${at} cites ${id}, whose citation the tour does not carry`);
  }
  return out;
}

/** The tour's ground: the stops' box in the scene's metres, widened by GROUND_MARGIN_M. */
export function tourGround(doc, toLocal, margin = GROUND_MARGIN_M) {
  const pts = (doc?.stops || []).map((s) => toLocal(s.lat, s.lon));
  const e = pts.map((p) => p.e), n = pts.map((p) => p.n);
  const box = { minE: Math.min(...e) - margin, maxE: Math.max(...e) + margin, minN: Math.min(...n) - margin, maxN: Math.max(...n) + margin };
  return { ...box, has: (pe, pn) => pe >= box.minE && pe <= box.maxE && pn >= box.minN && pn <= box.maxN };
}

/**
 * One visitor's walk of a tour.
 * @param {object} o
 * @param {object} o.doc       the tour (data/onsite/*.json), sound by tourProblems
 * @param {Function} o.toLocal (lat, lon) => { e, n }, the scene's metres (window.js toLocal with the datum)
 * @returns the session: `state`, `update(fix)`, `here()`, `next()`, `back()`, `hold(at)`.
 */
export function createOnsiteTour({ doc, toLocal }) {
  const stops = doc.stops;
  const ground = tourGround(doc, toLocal);
  const state = {
    cursor: 0,              // the stop in hand: walking to it, or reached it
    arrived: false,         // whether the stop in hand is reached
    reached: stops.map(() => false),
    complete: false,        // the last stop reached
    fix: null,              // { lat, lon, accuracy } as last given
    off: false,             // the last fix is off the tour's ground
    rough: false,           // the last fix is too rough to call arrival
    radius: null,           // the arrival radius for the last fix
    toward: null,           // { index, distance, bearing, point } to the stop walked to next
    how: null,              // how the stop in hand was reached: 'gps' or 'visitor'
  };

  /** The stop the visitor walks to next: the one in hand, or after it once reached. */
  const walkingTo = () => (state.arrived ? (state.cursor + 1 < stops.length ? state.cursor + 1 : null) : state.cursor);

  function measure() {
    const i = walkingTo();
    if (!state.fix || i === null) { state.toward = null; return; }
    const from = { lat: state.fix.lat, lng: state.fix.lon };
    const to = { lat: stops[i].lat, lng: stops[i].lon };
    const bearing = trueBearing(from, to);
    state.toward = { index: i, distance: distanceM(from, to), bearing, point: compassPoint(bearing) };
  }

  function arrive(how) {
    state.arrived = true;
    state.reached[state.cursor] = true;
    state.how = how;
    if (state.cursor === stops.length - 1) state.complete = true;
  }

  return {
    state,
    stops,
    ground,
    get stop() { return stops[state.cursor]; },

    /** Whether Window mode should hold the visitor where they are for this fix (scene metres). */
    hold: (at) => !ground.has(at.e, at.n),

    /** A fix, as Window mode gives it: `{ lat, lon, accuracy }`. Returns the state. */
    update(fix) {
      if (!fix || !Number.isFinite(fix.lat) || !Number.isFinite(fix.lon)) return state;
      state.fix = { lat: fix.lat, lon: fix.lon, accuracy: Math.max(0, Number(fix.accuracy) || 0) };
      const at = toLocal(fix.lat, fix.lon);
      state.off = !ground.has(at.e, at.n);
      state.radius = arrivalRadius(state.fix.accuracy);
      state.rough = state.fix.accuracy > ROUGH_FIX_M;
      if (!state.off && !state.rough && !state.arrived) {
        const s = stops[state.cursor];
        if (distanceM({ lat: fix.lat, lng: fix.lon }, { lat: s.lat, lng: s.lon }) <= state.radius) arrive('gps');
      }
      measure();
      return state;
    },

    /** The visitor says they are at the stop in hand. */
    here() {
      if (!state.arrived) arrive('visitor');
      measure();
      return state;
    },

    /** On to the next stop (a reached stop's card stays until this is asked). */
    next() {
      if (state.cursor >= stops.length - 1) return state;
      state.cursor += 1;
      state.arrived = state.reached[state.cursor];
      state.how = state.arrived ? state.how : null;
      if (state.fix) this.update(state.fix); else measure();
      return state;
    },

    /** Back to the stop before. */
    back() {
      if (state.cursor <= 0) return state;
      state.cursor -= 1;
      state.arrived = state.reached[state.cursor];
      measure();
      return state;
    },
  };
}
