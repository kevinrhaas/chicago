/**
 * today-geo.js — the scene's local metres back to latitude and longitude (T-3601).
 *
 * The scene's frame is EPSG:26916 (UTM zone 16N, NAD83) less the origin in
 * data/datum.json, east and north in metres; a bearing in it is measured from GRID
 * north. The Today window asks Google Street View for the same spot and the same
 * direction, and Street View speaks WGS84 latitude/longitude and TRUE-north headings.
 *
 * NAD83 and WGS84 differ by about a metre here, under a Street View panorama's own
 * spacing, so the GRS80 ellipsoid stands for both. The inverse is the standard
 * transverse Mercator series (Snyder, Map Projections — A Working Manual, USGS PP 1395,
 * 1987, eqs. 8-18 to 8-25), good to well under a centimetre inside one zone.
 *
 * Grid north and true north part by the meridian convergence, about -0.4° at Prairie
 * Avenue (zone 16's central meridian is 87° W; the town is 0.6° east of it). It is
 * measured, not assumed: the true azimuth of a short step due grid-north.
 *
 * Today's view is a navigation aid like today's streets (modern-streets.js): nothing
 * in a period layer is read off it. Pure: no DOM, no THREE.
 */

const A = 6378137.0;
const F = 1 / 298.257222101;
const E2 = F * (2 - F);
const EP2 = E2 / (1 - E2);
const K0 = 0.9996;
const FALSE_E = 500000;
const DEG = Math.PI / 180;

/** The datum's own origin (data/datum.json), so the module needs no fetch. */
export const DATUM = Object.freeze({
  zone: 16, origin_utm_e: 447072.7, origin_utm_n: 4637395.8,
  origin_lat: 41.886721, origin_lon: -87.637951,
});

/** UTM (northern hemisphere) easting/northing in metres to { lat, lng } in degrees. */
export function utmToLatLng(easting, northing, zone = DATUM.zone) {
  const lon0 = ((zone - 1) * 6 - 180 + 3) * DEG;
  const x = easting - FALSE_E;
  const M = northing / K0;
  const mu = M / (A * (1 - E2 / 4 - 3 * E2 * E2 / 64 - 5 * E2 ** 3 / 256));
  const e1 = (1 - Math.sqrt(1 - E2)) / (1 + Math.sqrt(1 - E2));
  const phi1 = mu
    + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * Math.sin(2 * mu)
    + (21 * e1 * e1 / 16 - 55 * e1 ** 4 / 32) * Math.sin(4 * mu)
    + (151 * e1 ** 3 / 96) * Math.sin(6 * mu)
    + (1097 * e1 ** 4 / 512) * Math.sin(8 * mu);
  const s = Math.sin(phi1), c = Math.cos(phi1), t = Math.tan(phi1);
  const C1 = EP2 * c * c;
  const T1 = t * t;
  const N1 = A / Math.sqrt(1 - E2 * s * s);
  const R1 = A * (1 - E2) / (1 - E2 * s * s) ** 1.5;
  const D = x / (N1 * K0);
  const lat = phi1 - (N1 * t / R1) * (D * D / 2
    - (5 + 3 * T1 + 10 * C1 - 4 * C1 * C1 - 9 * EP2) * D ** 4 / 24
    + (61 + 90 * T1 + 298 * C1 + 45 * T1 * T1 - 252 * EP2 - 3 * C1 * C1) * D ** 6 / 720);
  const lng = lon0 + (D - (1 + 2 * T1 + C1) * D ** 3 / 6
    + (5 - 2 * C1 + 28 * T1 - 3 * C1 * C1 + 8 * EP2 + 24 * T1 * T1) * D ** 5 / 120) / c;
  return { lat: lat / DEG, lng: lng / DEG };
}

/** A point in the scene's local metres to { lat, lng }. */
export function localToLatLng(e, n, datum = DATUM) {
  return utmToLatLng(datum.origin_utm_e + e, datum.origin_utm_n + n, datum.zone);
}

/** The initial true bearing, degrees clockwise from north, from one lat/lng to another. */
export function trueBearing(from, to) {
  const p1 = from.lat * DEG, p2 = to.lat * DEG, dl = (to.lng - from.lng) * DEG;
  const y = Math.sin(dl) * Math.cos(p2);
  const x = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
  return ((Math.atan2(y, x) / DEG) + 360) % 360;
}

/** Great-circle distance in metres (a sphere of the ellipsoid's mean radius). */
export function distanceM(a, b) {
  const R = 6371008.8;
  const p1 = a.lat * DEG, p2 = b.lat * DEG;
  const dp = p2 - p1, dl = (b.lng - a.lng) * DEG;
  const h = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

/** Degrees to add to a grid bearing at (e, n) to get a true one (meridian convergence). */
export function gridToTrueDeg(e, n, datum = DATUM) {
  const here = localToLatLng(e, n, datum);
  const up = localToLatLng(e, n + 100, datum);
  let d = trueBearing(here, up);
  if (d > 180) d -= 360;
  return d;
}

/**
 * Where the walker stands and looks, as Street View wants it: `{ lat, lng, heading,
 * target }`, the heading TRUE and `target` the spot `aheadM` metres along the line of
 * sight, so a panorama a few metres off the walker can be aimed at what they look at.
 */
export function viewFromLocal({ e = 0, n = 0, bearingDeg = 0 } = {}, aheadM = 30, datum = DATUM) {
  const here = localToLatLng(e, n, datum);
  const b = bearingDeg * DEG;
  const target = localToLatLng(e + Math.sin(b) * aheadM, n + Math.cos(b) * aheadM, datum);
  const heading = ((bearingDeg + gridToTrueDeg(e, n, datum)) % 360 + 360) % 360;
  return { lat: here.lat, lng: here.lng, heading, target };
}

/**
 * Google Maps' own documented link to Street View at a spot and heading (Maps URLs,
 * developers.google.com/maps/documentation/urls): it needs no key and opens the
 * Google Maps app on a phone.
 */
export function streetViewUrl({ lat, lng, heading = 0, pitch = 0 }) {
  const f = (v, d) => Number(v).toFixed(d);
  const pitchC = Math.max(-90, Math.min(90, pitch));
  return 'https://www.google.com/maps/@?api=1&map_action=pano'
    + `&viewpoint=${f(lat, 6)},${f(lng, 6)}&heading=${f(heading, 0)}&pitch=${f(pitchC, 0)}&fov=90`;
}
