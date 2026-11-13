/**
 * window.js — Window mode (T-3577): stand where you are and look through the
 * screen into the year.
 *
 * The owner, 2026-11-13: *"Would this vr stuff work on a good iPad and then we could
 * geolocate and be on a corner and look around like it is a window"*. The headset
 * mode (xr.js) needs WebXR, which no iPad or iPhone offers; this needs only what every
 * phone and tablet browser has — its location and its motion sensors.
 *
 *  - WHERE: `navigator.geolocation` gives latitude and longitude; `toLocal` projects
 *    them to UTM zone 16N (the datum's EPSG:26916; WGS84 and NAD83 differ by about a
 *    metre here, far under GPS's own error) and subtracts data/datum.json's origin, so
 *    the fix lands in the scene's own East-North metres, the frame the "Today" street
 *    readout already reads. A fix outside the year's ground is said, never walked to.
 *    The visitor is set down only when a fix moves more than `moveThreshold` (half
 *    the reported accuracy, at least MOVE_MIN_M), so GPS wander does not shuffle the
 *    view while you stand still.
 *  - WHICH WAY: the device's orientation, with an absolute compass heading — iOS's
 *    `webkitCompassHeading`, elsewhere `deviceorientationabsolute` — turns the view as
 *    the device turns. The heading is magnetic: Chicago's declination (DECLINATION_DEG)
 *    and the UTM grid's convergence (`gridConvergenceDeg`, the scene's north is grid
 *    north) are taken out. A compass still drifts a few degrees beside steel and cars,
 *    so a sideways drag on the view turns it to line up with the street (`offsetDeg`).
 *  - The walker keeps the last word on where you stand (a fix inside a building is
 *    pushed out to its wall, as any step is), and its yaw and pitch are only steered,
 *    through the intent, like any other backend. Roll is dropped: the horizon stays
 *    level in the window, as it does on foot.
 *
 * `?window-at=<lat>,<lon>` stands in for the GPS (to try a corner from home, or for
 * the harness). Pure helpers are exported for tools/check_window_mode.mjs; the session
 * half takes THREE from main.js so this file imports nothing.
 */

/** Magnetic declination at Chicago, degrees (west negative): about 3.3 W in 2026 (NOAA WMM). */
export const DECLINATION_DEG = -3.3;
/** The smallest move a fix makes before the visitor is set down again, metres. */
export const MOVE_MIN_M = 3;
/** Degrees of turn per CSS pixel of sideways drag, lining the view up. */
export const ALIGN_DEG_PER_PX = 0.15;

const DEG = Math.PI / 180;

/**
 * WGS84/GRS80 latitude and longitude to UTM easting and northing, metres
 * (Krüger series to n^3, millimetre-good across a zone).
 */
export function latLonToUtm(lat, lon, zone = 16) {
  const a = 6378137, f = 1 / 298.257222101, k0 = 0.9996;
  const n = f / (2 - f);
  const A = a / (1 + n) * (1 + n * n / 4 + n ** 4 / 64);
  const al = [n / 2 - 2 * n * n / 3 + 5 * n ** 3 / 16, 13 * n * n / 48 - 3 * n ** 3 / 5, 61 * n ** 3 / 240];
  const e = Math.sqrt(f * (2 - f));
  const phi = lat * DEG;
  const lam = (lon - (zone * 6 - 183)) * DEG;
  const t = Math.sinh(Math.atanh(Math.sin(phi)) - e * Math.atanh(e * Math.sin(phi)));
  const xi = Math.atan2(t, Math.cos(lam));
  const eta = Math.atanh(Math.sin(lam) / Math.sqrt(1 + t * t));
  let E = eta, N = xi;
  for (let j = 1; j <= 3; j++) {
    E += al[j - 1] * Math.cos(2 * j * xi) * Math.sinh(2 * j * eta);
    N += al[j - 1] * Math.sin(2 * j * xi) * Math.cosh(2 * j * eta);
  }
  return { e: 500000 + k0 * A * E, n: k0 * A * N };
}

/** The scene's local East-North metres for a latitude and longitude (data/datum.json). */
export function toLocal(lat, lon, datum) {
  const zone = Number(String(datum?.crs || '').match(/^EPSG:269(\d\d)$/)?.[1]) || 16;
  const u = latLonToUtm(lat, lon, zone);
  return { e: u.e - datum.origin_utm_e, n: u.n - datum.origin_utm_n };
}

/** Grid convergence, degrees: the angle from true north to the UTM grid's north (+ east). */
export function gridConvergenceDeg(lat, lon, zone = 16) {
  return Math.atan(Math.tan((lon - (zone * 6 - 183)) * DEG) * Math.sin(lat * DEG)) / DEG;
}

/** `?window-at=lat,lon`, or null. */
export function windowAt(search) {
  try {
    const v = new URLSearchParams(search || '').get('window-at');
    if (!v) return null;
    const [lat, lon] = v.split(',').map(Number);
    return Number.isFinite(lat) && Number.isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180 ? { lat, lon } : null;
  } catch { return null; }
}

/** How far a fix must move before the visitor is set down again. */
export function moveThreshold(accuracy) {
  return Math.max(MOVE_MIN_M, (Number(accuracy) || 0) / 2);
}

/** The compass's magnetic heading, from a deviceorientation event, or null. */
export function magneticHeading(event) {
  const h = Number(event?.webkitCompassHeading);
  if (Number.isFinite(h) && h >= 0) return h;               // iOS: degrees clockwise from north
  if (event?.absolute && Number.isFinite(event.alpha)) return (360 - event.alpha) % 360;
  return null;
}

/** The smallest signed difference a - b in degrees, -180..180. */
export function degDiff(a, b) {
  let d = (a - b) % 360;
  if (d > 180) d -= 360;
  if (d < -180) d += 360;
  return d;
}

/**
 * Where a device held at (alpha, beta, gamma) looks, with alpha already turned so
 * 0 is the scene's north: { yaw, pitch } in the walker's convention (radians, yaw +
 * is left of north, pitch + is up). The W3C device frame through three's
 * DeviceOrientationControls: a camera looking out of the back of the screen.
 */
export function deviceLook(THREE, alphaDeg, betaDeg, gammaDeg, screenDeg = 0) {
  const euler = new THREE.Euler(betaDeg * DEG, alphaDeg * DEG, -gammaDeg * DEG, 'YXZ');
  const q = new THREE.Quaternion().setFromEuler(euler);
  q.multiply(new THREE.Quaternion(-Math.sqrt(0.5), 0, 0, Math.sqrt(0.5)));
  q.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), -screenDeg * DEG));
  const out = new THREE.Euler().setFromQuaternion(q, 'YXZ');
  return { yaw: out.y, pitch: out.x };
}

/**
 * Window mode and its backend.
 * @param {object} o
 * @param {object} o.THREE
 * @param {object} o.walker    walker.js
 * @param {object} o.intent    the shared intent
 * @param {object} o.backends  intent.js's switch
 * @param {Function} o.fallback the backend to hand back to
 * @param {object} o.datum     data/datum.json
 * @param {Function} o.inBounds (e, n) => whether the year's ground is there
 * @param {Function} o.say      a terse line to the visitor
 * @param {Function} [o.onChange]
 * @param {HTMLElement} [o.surface] the view, for the line-up drag
 * @param {string} [o.search]  location.search, for ?window-at=
 */
export function createWindowMode({ THREE, walker, intent, backends, fallback, datum, inBounds, say,
  onChange = () => {}, surface = null, search = '', win = globalThis.window, nav = globalThis.navigator }) {
  let on = false;
  let watchId = null;
  let look = null;               // { yaw, pitch } wanted, from the sensors
  let alphaOffset = null;        // compass heading's alpha less the event's own alpha, smoothed
  let offsetDeg = 0;             // the visitor's line-up
  let placed = null;             // the last fix the visitor was set down at
  let lastFix = null;
  let outsideSaid = false;
  let drag = null;
  const pinned = windowAt(search);

  let sawAbsolute = false;
  function onOrientation(event) {
    if (!on || !Number.isFinite(event?.beta) || !Number.isFinite(event?.gamma)) return;
    // Where the absolute event exists (Chrome on Android), the plain one's alpha is from
    // an arbitrary start and would fight it; iOS has only the plain one, with its compass.
    if (event.type === 'deviceorientationabsolute') sawAbsolute = true;
    else if (sawAbsolute && !Number.isFinite(Number(event.webkitCompassHeading))) return;
    const alpha = Number.isFinite(event.alpha) ? event.alpha : 0;
    const mag = magneticHeading(event);
    if (mag !== null) {
      const lat = lastFix?.lat ?? datum?.origin_lat ?? 41.88;
      const lon = lastFix?.lon ?? datum?.origin_lon ?? -87.63;
      const gridHeading = mag + DECLINATION_DEG - gridConvergenceDeg(lat, lon);
      const want = degDiff(360 - gridHeading, alpha);
      // Smoothed on the circle, so a compass's jitter does not shake the view.
      alphaOffset = alphaOffset === null ? want : alphaOffset + 0.1 * degDiff(want, alphaOffset);
    }
    const screen = Number(win?.screen?.orientation?.angle ?? win?.orientation ?? 0) || 0;
    look = deviceLook(THREE, alpha + (alphaOffset ?? 0) - offsetDeg, event.beta, event.gamma, screen);
  }

  function place(fix) {
    lastFix = fix;
    const at = toLocal(fix.lat, fix.lon, datum);
    if (!inBounds(at.e, at.n)) {
      if (!outsideSaid) {
        say(`Window: you are ${Math.round(Math.hypot(at.e, at.n) / 100) / 10} km from the river forks, outside this year's town`);
        outsideSaid = true;
      }
      return false;
    }
    outsideSaid = false;
    if (placed && Math.hypot(at.e - placed.e, at.n - placed.n) < moveThreshold(fix.accuracy)) return false;
    const first = !placed;
    placed = at;
    walker.teleport({ local_e: at.e, local_n: at.n, yaw_deg: walker.bearingDeg, pitch_deg: walker.state.pitch / DEG });
    if (first) say(`Window: placed by ${pinned ? 'the address' : `GPS, ±${Math.round(fix.accuracy || 0)} m`} · turn to look · drag sideways to line up`);
    return true;
  }

  const onDown = (e) => { if (on) drag = { id: e.pointerId, x: e.clientX }; };
  const onMove = (e) => {
    if (!on || !drag || e.pointerId !== drag.id) return;
    offsetDeg += (e.clientX - drag.x) * ALIGN_DEG_PER_PX;
    drag.x = e.clientX;
  };
  const onUp = (e) => { if (drag && e.pointerId === drag.id) drag = null; };

  const backend = {
    name: 'window',
    enable() {},
    disable() { intent.clear(); },
    update() {
      if (!on || !look) return;
      let d = (look.yaw - walker.state.yaw) % (2 * Math.PI);
      if (d > Math.PI) d -= 2 * Math.PI;
      if (d < -Math.PI) d += 2 * Math.PI;
      intent.yawDelta = d;
      intent.pitchDelta = look.pitch - walker.state.pitch;
    },
  };

  function stop() {
    if (!on) return;
    on = false;
    win?.removeEventListener?.('deviceorientationabsolute', onOrientation);
    win?.removeEventListener?.('deviceorientation', onOrientation);
    surface?.removeEventListener('pointerdown', onDown);
    surface?.removeEventListener('pointermove', onMove);
    win?.removeEventListener?.('pointerup', onUp);
    if (watchId !== null) nav?.geolocation?.clearWatch?.(watchId);
    watchId = null;
    look = null;
    drag = null;
    if (backends.active === backend) backends.activate(fallback());
    onChange(false);
  }

  return {
    backend,
    get on() { return on; },
    get offsetDeg() { return offsetDeg; },
    get placed() { return placed; },

    /** Whether this device can be a window: motion sensors, and a location or ?window-at=. */
    supported() {
      return !!win && 'DeviceOrientationEvent' in win && (!!nav?.geolocation || !!pinned);
    },

    /**
     * Start. Call it from the tap itself: iOS asks for motion permission only inside
     * a user gesture, so that request is the first thing done.
     */
    async start() {
      if (on) return true;
      const ask = win?.DeviceOrientationEvent?.requestPermission;
      if (typeof ask === 'function') {
        let answer = 'denied';
        try { answer = await ask.call(win.DeviceOrientationEvent); } catch { answer = 'denied'; }
        if (answer !== 'granted') { say('Window needs motion access: allow it when the browser asks'); return false; }
      }
      on = true;
      alphaOffset = null;
      sawAbsolute = false;
      placed = null;
      outsideSaid = false;
      win.addEventListener('deviceorientationabsolute', onOrientation);
      win.addEventListener('deviceorientation', onOrientation);
      surface?.addEventListener('pointerdown', onDown);
      surface?.addEventListener('pointermove', onMove);
      win.addEventListener('pointerup', onUp);
      backends.activate(backend);
      onChange(true);
      if (pinned) place({ ...pinned, accuracy: 0 });
      else {
        say('Window: finding where you are…');
        watchId = nav.geolocation.watchPosition(
          (p) => place({ lat: p.coords.latitude, lon: p.coords.longitude, accuracy: p.coords.accuracy }),
          (err) => say(err?.code === 1 ? 'Window needs your location: allow it when the browser asks' : 'Window: no location yet'),
          { enableHighAccuracy: true, maximumAge: 2000, timeout: 30000 });
      }
      return true;
    },

    stop,
    /** For the harness: feed one orientation reading or one fix as the device would. */
    feedOrientation: (event) => onOrientation(event),
    feedFix: (fix) => place(fix),
  };
}
