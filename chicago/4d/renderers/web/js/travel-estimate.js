import { PACES, paceSpeed, FLY, ARRIVAL_SETTLE_S } from './travel-settings.js';

const point = p => p && Number.isFinite(p.e) && Number.isFinite(p.n);
const seconds = v => Number.isFinite(v) && v >= 0 ? v : 0;

/** Pure prediction; routing and coordinates are supplied by the same scene as travel. */
export function estimateLeg({ from, to, mode, settings = {}, router }) {
  if (!point(from) || !point(to) || !Object.hasOwn(PACES, mode)) return null;
  const direct = Math.hypot(to.e - from.e, to.n - from.n);
  if (!Number.isFinite(direct)) return null;
  if (mode === 'instantly') return { seconds: ARRIVAL_SETTLE_S, length_m: direct, approx: false };
  if (mode === 'fly') {
    const height = PACES.fly.cruise(direct), altitude = Math.min(FLY.maxAltitude, seconds(from.altitude));
    // Integrate the controller's height-dependent vertical speed, in metre bands.
    const vertical = (lo, hi) => {
      let time = 0;
      for (let h = lo; h < hi; h += 1) {
        const step = Math.min(1, hi - h);
        time += step / (FLY.riseSpeed * FLY.altitudeGain(h + step / 2));
      }
      return time;
    };
    const ascent = vertical(Math.min(altitude, height), height);
    const descent = vertical(0, Math.max(height, altitude));
    const cruise = direct / (FLY.speed * FLY.altitudeGain(height));
    return { seconds: ascent + cruise + descent + ARRIVAL_SETTLE_S, length_m: direct, approx: false };
  }
  const route = router?.plan?.(from, to);
  const routed = route?.points?.length && Number.isFinite(route.length_m) && route.length_m >= 0;
  const length_m = routed ? route.length_m : direct * 1.3;
  return { seconds: length_m / paceSpeed(mode, settings) + ARRIVAL_SETTLE_S, length_m, approx: !routed };
}

/** Catalog timing and full story documents share the same primary-path estimate.
 * `from` prices an in-progress leg from the visitor's current position. */
export function estimateJaunt(jaunt, mode, { resolve = d => d, settings = {}, router,
  startIndex = 0, from = null, includeOpening = true } = {}) {
  const stops = jaunt.stops || jaunt.destinations?.map((destination, i) => ({ destination, ...jaunt.timing?.stops?.[i] }));
  if (!stops?.length || !Object.hasOwn(PACES, mode)) return null;
  let total = includeOpening ? seconds(jaunt.opening?.read_s ?? jaunt.timing?.opening_read_s) : 0;
  let approx = false;
  const legs = [], first = Math.max(0, Math.min(startIndex, stops.length - 1));
  let previous = from || resolve(stops[first].destination);
  if (!point(previous)) return null;
  for (let i = first; i < stops.length; i++) {
    const stop = stops[i], target = resolve(stop.destination);
    if (!point(target)) return null;
    if (i > first || from) {
      const leg = estimateLeg({ from: previous, to: target, mode, settings, router });
      if (!leg) return null;
      legs.push(leg); total += leg.seconds; approx ||= leg.approx;
    }
    total += seconds(stop.read_s) + seconds(stop.action_s);
    previous = target;
  }
  return { seconds: total, approx, legs };
}

export function formatEstimate(estimate) {
  if (!estimate || !Number.isFinite(estimate.seconds)) return 'No estimate';
  const minutes = Math.round(estimate.seconds / 30) / 2;
  return `about ${minutes} min${estimate.approx ? ' (approximate route)' : ''}`;
}
