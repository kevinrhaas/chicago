/**
 * today-view.js — the Today window: Google Street View, today, from where you stand (T-3601).
 *
 * The owner, 2026-11-14: "show the view from the street view side of Google Maps or Apple
 * and show what that view is today in a window ... a small expandable today window that
 * would sync along with the main window, you could hide or show that window".
 *
 * A small window under the THEN / TODAY readout. It turns as you turn and moves as you
 * walk: the walker's local metres and grid bearing become latitude, longitude and a true
 * heading (today-geo.js), the nearest outdoor Street View panorama is found, and it is
 * aimed at the spot you are looking at. The expand key makes it big; the close key, the
 * TODAY tag in the readout and Settings › Show › Today window all hide or show it.
 *
 * WHY GOOGLE. Apple's MapKit JS Look Around opens at a coordinate but takes no heading,
 * so it could not turn with you. Google's Maps JavaScript API Street View panorama takes
 * a position and a point of view and changes either without reloading.
 *
 * COST, MEMORY AND THE NETWORK. Nothing from Google is fetched until the window is first
 * shown, so the boot, the memory budgets and a phone that never opens it are untouched.
 * One panorama is made once and kept (Google bills a panorama's load, not its turns), it
 * is told to stop drawing while the window is hidden, a new spot is asked for only after
 * you have walked MOVE_M and at most once per QUERY_MS, and the point of view is set at
 * most once per POV_MS and only when it has changed. Without a key (today-view-config.js)
 * the window is a card: the spot, the heading, and Google Maps' own keyless Street View
 * link there.
 *
 * Today's view is a navigation aid, like today's street names: nothing in a period layer
 * is read off it.
 */
import { viewFromLocal, trueBearing, distanceM, streetViewUrl } from './today-geo.js';
import { TODAY_VIEW } from './today-view-config.js';

/** Walk this far before asking for a new panorama. */
export const MOVE_M = 5;
/** And ask at most this often. */
export const QUERY_MS = 1200;
/** Set the point of view at most this often (a turn is smooth well below a frame rate). */
export const POV_MS = 80;
/** The search radii for a panorama, nearest first: a yard, then the block. */
export const RADII_M = [35, 100];
/** The look is aimed at the spot this far ahead of you... */
export const AHEAD_M = 40;
/** ...unless the panorama is this far off, when aiming would swing it round. */
const AIM_MAX_OFF_M = 18;
const KEY_STORE = 'chicago4d.todayKey';

const CARDINALS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
export const cardinal16 = (deg) => CARDINALS[Math.round((((deg % 360) + 360) % 360) / 22.5) % 16];

/** The key to use here, or '' for the link-only card. */
export function keyFor({ config = TODAY_VIEW, hostname = '', stored = '' } = {}) {
  if (stored) return stored;
  return config?.googleMapsKey && (config.hosts ?? []).includes(hostname) ? config.googleMapsKey : '';
}

/** "Jul 2024" from Street View's "2024-07". */
export function imageDateText(d) {
  const m = /^(\d{4})-(\d{2})/.exec(d ?? '');
  if (!m) return '';
  const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${names[Number(m[2]) - 1] ?? ''} ${m[1]}`.trim();
}

function readStored() {
  try { return localStorage.getItem(KEY_STORE) ?? ''; } catch { return ''; }
}

/** Load the Maps JavaScript API once, and its Street View library. */
let mapsPromise = null;
function loadStreetView(key, onAuthFailure) {
  if (mapsPromise) return mapsPromise;
  mapsPromise = new Promise((resolve, reject) => {
    const cb = '__chicago4dTodayMaps';
    window[cb] = () => {
      try { delete window[cb]; } catch { window[cb] = undefined; }
      window.google.maps.importLibrary('streetView').then(resolve, reject);
    };
    // Google calls this, by this name, when it refuses the key (wrong host, API off,
    // no billing). It is the only signal: the script itself loads either way.
    window.gm_authFailure = () => onAuthFailure?.();
    const s = document.createElement('script');
    s.src = 'https://maps.googleapis.com/maps/api/js'
      + `?key=${encodeURIComponent(key)}&v=weekly&loading=async&callback=${cb}`;
    s.async = true;
    s.onerror = () => { mapsPromise = null; reject(new Error('Google Maps did not load')); };
    document.head.appendChild(s);
  });
  return mapsPromise;
}

export function createTodayView({
  root = document, config = TODAY_VIEW, hostname = globalThis.location?.hostname ?? '',
  onShownChange = null, onExpandedChange = null, load = loadStreetView,
} = {}) {
  const $ = (id) => root.getElementById?.(id) ?? root.querySelector?.(`#${id}`) ?? null;
  const box = $('today-view');
  const panoEl = $('today-pano');
  const note = $('today-note');
  const where = $('today-where');
  const openLink = $('today-open');
  const expandKey = $('today-expand');
  const closeKey = $('today-close');
  const tagKey = $('street-today-key');

  let shown = false;
  let expanded = false;
  let mode = 'off'; // off | link | loading | live | none | error
  let lib = null;
  let service = null;
  let panorama = null;
  let pose = null;
  let view = null;
  let queried = null; // the spot the last panorama was asked for
  let pending = false;
  let lastQuery = -Infinity;
  let lastPov = -Infinity;
  let lastLink = -Infinity;
  let sentPov = null;
  let pano = null; // { id, lat, lng, date, offM }
  let failure = '';
  let queries = 0;
  let povSets = 0;

  function paintNote() {
    if (!note) return;
    const text = {
      off: '',
      link: 'Street View opens in Google Maps. The live window needs the site’s Google key.',
      loading: 'Loading Google Street View…',
      live: `Google Street View${pano?.date ? ` · ${imageDateText(pano.date)}` : ''}`
        + `${pano && pano.offM >= 8 ? ` · ${Math.round(pano.offM)} m away` : ''}`,
      none: `No Street View within ${RADII_M[RADII_M.length - 1]} m of here today.`,
      error: failure || 'Google Street View did not load.',
    }[mode] ?? '';
    note.textContent = text;
    box?.setAttribute('data-mode', mode);
    panoEl?.toggleAttribute('hidden', mode !== 'live');
  }

  function paintWhere() {
    if (!view) return;
    if (where) where.textContent = `looking ${cardinal16(view.heading)} ${String(Math.round(view.heading) % 360).padStart(3, '0')}°`;
    if (openLink) openLink.href = streetViewUrl({ lat: view.lat, lng: view.lng, heading: view.heading, pitch: pose?.pitchDeg ?? 0 });
  }

  function aim(now) {
    if (!panorama || !view || !pano) return;
    const heading = pano.offM <= AIM_MAX_OFF_M ? trueBearing(pano, view.target) : view.heading;
    const pitch = Math.max(-60, Math.min(60, pose?.pitchDeg ?? 0));
    if (sentPov && Math.abs(((heading - sentPov.heading + 540) % 360) - 180) < 0.4
      && Math.abs(pitch - sentPov.pitch) < 0.8) return;
    if (now - lastPov < POV_MS) return;
    lastPov = now;
    sentPov = { heading, pitch };
    panorama.setPov({ heading, pitch });
    povSets += 1;
  }

  async function query(v, now) {
    if (!service || pending) return;
    pending = true;
    lastQuery = now;
    queried = { lat: v.lat, lng: v.lng };
    queries += 1;
    let data = null;
    for (const radius of RADII_M) {
      try {
        const res = await service.getPanorama({
          location: { lat: v.lat, lng: v.lng }, radius,
          preference: lib.StreetViewPreference?.NEAREST ?? 'nearest',
          sources: [lib.StreetViewSource?.OUTDOOR ?? 'outdoor'],
        });
        data = res?.data ?? res;
        if (data?.location?.pano) break;
      } catch { data = null; } // ZERO_RESULTS rejects; try the wider radius
    }
    pending = false;
    if (!shown) return;
    if (!data?.location?.pano) {
      mode = 'none'; pano = null; paintNote();
      return;
    }
    const ll = data.location.latLng;
    const at = { lat: typeof ll.lat === 'function' ? ll.lat() : ll.lat, lng: typeof ll.lng === 'function' ? ll.lng() : ll.lng };
    const offM = distanceM(at, queried);
    if (pano?.id !== data.location.pano) {
      panorama.setPano(data.location.pano);
      sentPov = null;
    }
    pano = { id: data.location.pano, ...at, date: data.imageDate ?? '', offM };
    panorama.setVisible(true);
    mode = 'live';
    paintNote();
    aim(performance.now());
  }

  async function start() {
    const key = keyFor({ config, hostname, stored: readStored() });
    if (!key) { mode = 'link'; paintNote(); return; }
    if (panorama) { mode = pano ? 'live' : 'loading'; paintNote(); return; }
    mode = 'loading'; paintNote();
    try {
      lib = await load(key, () => {
        failure = 'Google refused the site’s key here. Street View still opens in Google Maps.';
        mode = 'error'; paintNote();
      });
    } catch (err) {
      failure = `Google Street View did not load (${err?.message ?? err}). It still opens in Google Maps.`;
      mode = 'error'; paintNote();
      return;
    }
    if (mode === 'error' || !panoEl) return;
    service = new lib.StreetViewService();
    panorama = new lib.StreetViewPanorama(panoEl, {
      visible: false,
      disableDefaultUI: true, clickToGo: false, linksControl: false, panControl: false,
      zoomControl: false, addressControl: false, fullscreenControl: false,
      motionTracking: false, motionTrackingControl: false, showRoadLabels: false,
      scrollwheel: false, disableDoubleClickZoom: true, keyboardShortcuts: false,
      imageDateControl: false, enableCloseButton: false,
    });
    if (shown && view) void query(view, performance.now());
  }

  function update({ e = 0, n = 0, bearingDeg = 0, pitchDeg = 0 } = {}) {
    pose = { e, n, bearingDeg, pitchDeg }; // kept while hidden, so opening is immediate
    if (!shown) return;
    const now = performance.now();
    view = viewFromLocal({ e, n, bearingDeg }, AHEAD_M);
    if (now - lastLink > 400) { lastLink = now; paintWhere(); }
    if (!panorama || !service) return;
    if (!pending && (!queried || (distanceM(queried, view) > MOVE_M && now - lastQuery > QUERY_MS))) {
      void query(view, now);
    }
    aim(now);
  }

  function setShown(on, { quiet = false } = {}) {
    on = !!on;
    if (on === shown) return shown;
    shown = on;
    box?.toggleAttribute('hidden', !on);
    tagKey?.setAttribute('aria-pressed', String(on));
    if (on) {
      lastLink = -Infinity;
      if (pose) update(pose);
      void start();
    } else {
      mode = 'off';
      panorama?.setVisible(false);
      queried = null; // a fresh spot is asked for the next time it opens
    }
    if (!quiet) onShownChange?.(on);
    return shown;
  }

  function setExpanded(on, { quiet = false } = {}) {
    expanded = !!on;
    box?.setAttribute('data-size', expanded ? 'big' : 'small');
    expandKey?.setAttribute('aria-pressed', String(expanded));
    expandKey?.setAttribute('aria-label', expanded ? 'Make the Today window small' : 'Make the Today window big');
    if (expandKey) expandKey.title = expandKey.getAttribute('aria-label');
    if (!quiet) onExpandedChange?.(expanded);
    return expanded;
  }

  expandKey?.addEventListener('click', () => setExpanded(!expanded));
  closeKey?.addEventListener('click', () => setShown(false));
  tagKey?.addEventListener('click', () => setShown(!shown));
  // Keys pressed in the window are the window's, not the walker's.
  box?.addEventListener('keydown', (ev) => ev.stopPropagation());

  return {
    update,
    setShown,
    setExpanded,
    get shown() { return shown; },
    get expanded() { return expanded; },
    /** For tests and the harness: what the window is doing and what it was told. */
    get state() {
      return {
        shown, expanded, mode, queries, povSets,
        view: view && { lat: +view.lat.toFixed(6), lng: +view.lng.toFixed(6), heading: +view.heading.toFixed(1) },
        pano: pano && { id: pano.id, off_m: +pano.offM.toFixed(1), date: pano.date },
        pov: sentPov && { heading: +sentPov.heading.toFixed(1), pitch: +sentPov.pitch.toFixed(1) },
        link: openLink?.href ?? null,
      };
    },
  };
}
