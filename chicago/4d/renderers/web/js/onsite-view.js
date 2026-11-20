/**
 * onsite-view.js — the on-site tour's card (T-3674), over Window mode in 1904.
 *
 * Loaded only when Window mode starts in the tour's year (main.js), never at boot: first
 * the offer ("Start the tour" / "Not now"), then, on Start, the tour's data and the card.
 * The card shows the stop in hand, the GPS accuracy as the device reports it, the distance
 * and compass point to the stop walked to next with an arrow turned to the view, the stop's
 * cited text, and Back / I'm here / Next stop. js/onsite.js is the walk itself.
 */
import { t } from './strings/index.js';
import './strings/onsite.js';
import { createOnsiteTour, tourProblems, sayDistance, turnDeg } from './onsite.js';
import { gridToTrueDeg } from './today-geo.js';

/** How often the arrow follows the view while the card is up, ms. */
const ARROW_MS = 250;

/**
 * @param {HTMLElement} host
 * @param {object} o
 * @param {Function} o.load      () => Promise<tour document>
 * @param {Function} o.toLocal   (lat, lon) => { e, n } in the scene's metres
 * @param {Function} o.heading   () => the view's grid bearing, degrees, or null
 * @param {Function} o.where     () => the walker's { e, n }, for the grid-to-true turn
 * @param {Function} o.lastFix   () => Window mode's last fix, or null
 * @param {boolean}  o.pinned    whether ?window-at= stands in for the GPS
 * @param {Function} [o.openHouse] (structure id) => opens that building's card
 * @param {Function} [o.say]     a terse line to the visitor
 * @param {Function} [o.onRun]   (running) => told when the tour starts and ends
 */
export function mountOnsite(host, { load, toLocal, heading = () => null, where = () => null, lastFix = () => null,
  pinned = false, openHouse = null, say = () => {}, onRun = () => {} } = {}) {
  const doc = host?.ownerDocument;
  if (!doc) return null;
  if (doc.head && !doc.getElementById('onsite-style')) {
    const css = doc.createElement('link'); css.id = 'onsite-style'; css.rel = 'stylesheet';
    css.href = new URL('../css/onsite.css', import.meta.url).href;
    doc.head.append(css);
  }
  const make = (tag, cls, text) => {
    const el = doc.createElement(tag);
    if (cls) el.className = cls;
    if (text !== undefined) el.textContent = text;
    return el;
  };
  const button = (key, act, cls = '') => {
    const b = make('button', cls, t(`onsite.${key}`)); b.type = 'button'; b.dataset.act = act; return b;
  };

  const root = make('section', 'onsite');
  root.setAttribute('aria-label', t('onsite.title'));
  root.hidden = true;
  host.append(root);

  let session = null, tourDoc = null, timer = null, loading = false, expanded = false, lastArrived = -1;

  function stopTimer() { if (timer !== null) { clearInterval(timer); timer = null; } }

  function offer() {
    if (session || loading) return;
    root.replaceChildren();
    root.hidden = false;
    root.classList.remove('onsite-running');
    const card = make('div', 'onsite-card onsite-offer');
    const head = make('div', 'onsite-head');
    head.append(make('span', '', t('onsite.title')), make('span', 'onsite-dim', t('onsite.where')));
    const p = make('p', 'onsite-offer-text', t('onsite.offer'));
    const row = make('div', 'onsite-actions');
    const start = button('start', 'start', 'onsite-primary');
    row.append(button('dismiss', 'dismiss'), start);
    const status = make('p', 'onsite-status'); status.setAttribute('role', 'status');
    card.append(head, p, row, status);
    root.append(card);
  }

  async function begin() {
    if (loading) return;
    loading = true;
    const status = root.querySelector('.onsite-status');
    if (status) status.textContent = t('onsite.loading');
    try {
      tourDoc = await load();
      const problems = tourProblems(tourDoc);
      if (problems.length) throw new Error(problems[0]);
      session = createOnsiteTour({ doc: tourDoc, toLocal });
      const fix = lastFix();
      if (fix) session.update(fix);
      expanded = false;
      lastArrived = session.state.arrived ? session.state.cursor : -1;
      render(true);
      timer = setInterval(turnArrow, ARROW_MS);
      onRun(true);
    } catch {
      if (status) status.textContent = t('onsite.unavailable');
    } finally { loading = false; }
  }

  function end() {
    stopTimer();
    const was = !!session;
    session = null;
    root.replaceChildren();
    root.hidden = true;
    root.classList.remove('onsite-running');
    if (was) onRun(false);
  }

  function gpsLine(s) {
    if (s.off) return ['off', t('onsite.gps.off')];
    if (!s.fix) return ['wait', t('onsite.gps.waiting')];
    if (pinned && s.fix.accuracy === 0) return ['pinned', t('onsite.gps.pinned')];
    const accuracy = Math.round(s.fix.accuracy);
    if (s.rough) return ['rough', t('onsite.gps.rough', { accuracy })];
    return ['fix', t('onsite.gps.fix', { accuracy, radius: Math.round(s.radius) })];
  }

  /** The turn from where the view looks to the stop, degrees (+ right), or null. */
  function turnTo(bearingTrue) {
    const h = heading();
    if (!Number.isFinite(h)) return null;
    const at = where();
    const conv = at ? gridToTrueDeg(at.e, at.n) : 0;
    return turnDeg(bearingTrue, h + conv);
  }
  const turnWord = (d) => (d === null ? '' : Math.abs(d) <= 30 ? t('onsite.ahead') : Math.abs(d) >= 150 ? t('onsite.behind') : d > 0 ? t('onsite.right') : t('onsite.left'));

  function turnArrow() {
    if (!session || root.hidden) return;
    const tw = session.state.toward;
    const arrow = root.querySelector('.onsite-arrow');
    const line = root.querySelector('.onsite-away');
    if (!tw || !arrow || !line) return;
    const d = turnTo(tw.bearing);
    arrow.style.transform = `rotate(${d ?? tw.bearing}deg)`;
    arrow.dataset.relative = d === null ? 'north' : 'view';
    const words = d === null
      ? t('onsite.awayNoTurn', { distance: sayDistance(tw.distance), point: tw.point })
      : t('onsite.away', { distance: sayDistance(tw.distance), point: tw.point, turn: turnWord(d) });
    if (line.textContent !== words) line.textContent = words;
  }

  function render(focus = false) {
    if (!session) return;
    const s = session.state, stops = session.stops, stop = session.stop;
    root.hidden = false;
    root.classList.add('onsite-running');
    root.replaceChildren();
    const card = make('div', 'onsite-card');
    card.dataset.cursor = String(s.cursor);
    card.dataset.arrived = String(s.arrived);
    // Head: the stop count and the way out.
    const head = make('div', 'onsite-head');
    head.append(make('span', '', `${t('onsite.title')} · ${t('onsite.stop', { n: s.cursor + 1, count: stops.length })}`));
    const close = make('button', 'onsite-close', '×'); close.type = 'button'; close.dataset.act = 'end';
    close.setAttribute('aria-label', t('onsite.end')); close.title = t('onsite.end');
    head.append(close);
    const pips = make('div', 'onsite-pips'); pips.setAttribute('aria-hidden', 'true');
    stops.forEach((_, i) => pips.append(make('i', i === s.cursor ? 'now' : s.reached[i] ? 'done' : '')));
    const [gpsKind, gpsText] = gpsLine(s);
    const gps = make('p', `onsite-gps onsite-gps-${gpsKind}`, gpsText);
    gps.setAttribute('role', 'status');
    card.append(head, pips, gps);

    // The stop in hand.
    const badge = make('p', `onsite-badge${s.arrived ? ' onsite-badge-here' : ''}`, s.arrived ? t('onsite.here') : t('onsite.walkTo'));
    const addr = make('p', 'onsite-address', stop.address);
    const title = make('h3', 'onsite-title', stop.title); title.tabIndex = -1;
    card.append(badge, addr, title);

    // Where to walk: to this stop, or (once here) to the next.
    const tw = s.toward;
    if (tw) {
      const dir = make('div', 'onsite-dir');
      const arrow = make('span', 'onsite-arrow');
      arrow.setAttribute('aria-hidden', 'true');
      arrow.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l6 16-6-4-6 4z"/></svg>';
      const words = make('div', 'onsite-dir-words');
      if (tw.index !== s.cursor) words.append(make('span', 'onsite-dim', `${t('onsite.next')}: ${stops[tw.index].title}`));
      words.append(make('strong', 'onsite-away', ''));
      dir.append(arrow, words);
      card.append(dir);
    }
    if (s.off && tw) card.append(make('p', 'onsite-note', t('onsite.offNote', { distance: sayDistance(tw.distance) })));
    else if (!s.arrived && s.rough) card.append(make('p', 'onsite-note', t('onsite.roughNote')));
    else if (!s.arrived && pinned && s.fix?.accuracy === 0 && s.cursor === 0) card.append(make('p', 'onsite-note', t('onsite.pinnedNote')));

    // The stop's card: open once reached, or on asking.
    const body = make('div', 'onsite-body');
    if (s.arrived || expanded) {
      if (s.arrived) {
        const by = s.how !== 'gps' ? 'reachedHand' : pinned && s.fix?.accuracy === 0 ? 'reachedAddress' : 'reachedBy';
        body.append(make('p', 'onsite-dim', t(`onsite.${by}`)));
      }
      body.append(make('p', 'onsite-text', stop.text));
      const det = make('details', 'onsite-sources');
      det.append(make('summary', '', t('onsite.sources', { count: stop.sources.length })));
      const list = make('ol');
      for (const id of stop.sources) list.append(make('li', '', tourDoc.citations[id]));
      det.append(list);
      body.append(det);
      if (openHouse && stop.structure) {
        const links = make('div', 'onsite-links');
        const about = button('about', 'about'); links.append(about); body.append(links);
      }
    } else {
      body.append(button('readMore', 'read', 'onsite-link'));
    }
    if (s.complete) body.append(make('p', 'onsite-complete', `${t('onsite.complete')} · ${t('onsite.completeNote', { count: stops.length })}`));
    card.append(body);

    // Controls.
    const row = make('div', 'onsite-actions');
    const back = button('back', 'back'); back.disabled = s.cursor === 0;
    let primary;
    if (!s.arrived) primary = button('arrive', 'here', 'onsite-primary');
    else if (s.cursor < stops.length - 1) primary = button('nextStop', 'next', 'onsite-primary');
    else primary = button('finish', 'end', 'onsite-primary');
    row.append(back, primary);
    card.append(row);
    root.append(card);
    turnArrow();
    if (focus) title.focus({ preventScroll: true });
  }

  root.addEventListener('click', (e) => {
    const act = e.target.closest?.('[data-act]')?.dataset.act;
    if (!act) return;
    if (act === 'start') { void begin(); return; }
    if (act === 'dismiss') { end(); return; }
    if (act === 'end') { end(); return; }
    if (!session) return;
    if (act === 'read') { expanded = true; render(); return; }
    if (act === 'about') { openHouse?.(session.stop.structure); return; }
    if (act === 'here') session.here();
    else if (act === 'next') { session.next(); expanded = false; }
    else if (act === 'back') { session.back(); expanded = false; }
    noteArrival();
    render(true);
  });

  function noteArrival() {
    const s = session.state;
    if (s.arrived && lastArrived !== s.cursor) { lastArrived = s.cursor; say(t('onsite.arrived', { name: session.stop.title })); }
    if (!s.arrived) lastArrived = -1;
  }

  return {
    get running() { return !!session; },
    get state() { return session ? { ...session.state, stop: session.stop.id } : null; },
    offer,
    start: begin,
    end,
    /** Window mode's every fix. Returns true when the tour holds the visitor where they are. */
    fix(fix, at) {
      if (!session) return false;
      const was = `${session.state.cursor}:${session.state.arrived}:${session.state.off}:${session.state.rough}`;
      session.update(fix);
      const now = `${session.state.cursor}:${session.state.arrived}:${session.state.off}:${session.state.rough}`;
      if (was !== now) { noteArrival(); render(); }
      else {
        const gps = root.querySelector('.onsite-gps');
        const [kind, line] = gpsLine(session.state);
        if (gps && gps.textContent !== line) { gps.textContent = line; gps.className = `onsite-gps onsite-gps-${kind}`; }
        turnArrow();
      }
      return session.hold(at);
    },
    destroy() { end(); root.remove(); },
  };
}
