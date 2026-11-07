/**
 * Tour mode, the Field Check (T-2663, NAV-801; design doc section 11, M10).
 *
 * Nine steps the Navigator runs itself, framed as a Confluence Laboratory field check.
 * Every step waits for the visitor to actually do the thing — read from the page through
 * `probe()`, never assumed — and Skip is always there. Progress is kept per device
 * (localStorage, inside try/catch), so a reload mid-tour resumes at the same step; it can
 * be replayed, and abandoned, from Guide.
 *
 * T-2954 (the owner, 2026-10-20) made it the basics of getting around: select a building
 * and RELEASE it (the step he found missing: "after you click glessner its hard"), then the
 * two menus a first visit needs, Move and Settings. The Confidence view step and the
 * card's Go deeper step are gone — the owner found the first hard to find and turn off,
 * and neither is getting around. Bubbles say click on a mouse device and tap on touch.
 *
 * T-3445 (the owner, 2026-11-07: "is the first time user tour current?") brings it up to
 * what the town does now: the card's tabs (T-3435), a People step for the directory and
 * Follow (T-3430, T-3404) where the scene has a People app, and Go to by photo (T-3436).
 *
 * Bubbles are 14 words or fewer (section 11). The last step's Finish ends the tour and calls
 * `onFinish`, which awards the Navigator License keepsake (T-2665, js/license.js); Skip
 * ends it without.
 *
 * `probe()` returns { yawDeg, e, n, opens, selected, card, apps, touch, level, scene, front, people }:
 * the camera's bearing, where the visitor stands, how many times Inspect or a building
 * card has opened on a structure, whether one is open now (and whether it is the floating
 * card, T-3022), how many times each Navigator
 * app has been opened, whether the visitor is on touch, how far the Navigator is open
 * (0 docked), the scene id, the name of the building in front of the visitor (or
 * null), and whether the rail has a People app (false skips the People step). The
 * counters are what make a step wait for an action taken DURING it: a card
 * already open, or a menu already open, when the step begins does not complete it.
 */
import { count as countField } from './field-log.js'; // T-2660

export const TOUR_KEY = 'chicago4d.tour';
export const YAW_DEG = 60;
export const WALK_M = 5;

const press = (p) => (p.touch ? 'Tap' : 'Click');
const opened = (id) => (p, base) => (p.apps?.[id] ?? 0) > (base.apps?.[id] ?? 0);
/** On a phone the rail is inside the docked Navigator: ring the dock until it is open. */
const railKey = (id) => (p) => (p.touch && !(p.level > 0) ? '#navigator' : `#navigator .nav-app[data-app="${id}"]`);
const menuOpen = (name, what) => (p) => (p.touch && !(p.level > 0)
  ? `Open the Navigator, then ${name}: ${what}.`
  : `Open ${name} on the rail: ${what}.`);

/** The nine steps. `task` is the field-check line over the bubble; `target` the selector
 *  the spotlight rings (or a function of the probe); `done(p, base)` whether the step's
 *  real action has happened; `when(p)`, where given, whether the step applies here (People
 *  only where the scene has a People app on the rail) — a step that does not is passed over
 *  and not counted. */
export const STEPS = [
  { task: 'Your device', bubble: () => 'This is your Navigator. Every menu lives on its rail.',
    target: '#navigator', action: 'next' },
  { task: 'Look around', bubble: () => 'Look around. Drag the right side of the screen (or move the mouse).',
    target: null, done: (p, base) => base.turned >= YAW_DEG },
  { task: 'Walk', bubble: () => 'Walk. Left thumb, or W A S D. Head for the corner.',
    target: null, done: (p, base) => Math.hypot(p.e - base.e, p.n - base.n) >= WALK_M },
  { task: 'Select a building',
    // Section 11: in 1904 the Glessner House; in 1835 and 1812 the building in front of you.
    // T-3445: the card's tabs as they are now (T-3435).
    bubble: (p) => `${press(p)} the ${String(p.scene) === '1904' ? 'Glessner House' : (p.front || 'building in front of you')}. Its card opens: Design, Timeline, Photos, Sources.`,
    target: null, done: (p, base) => (p.opens ?? 0) > base.opens },
  // T-3022: a building opened by hand opens in Inspect, let go by its Back key; the floating
  // card (`p.card`), where one is open, by its Close.
  { task: 'Release it',
    bubble: (p) => { const key = p.card ? 'Close' : 'Back';
      return p.touch ? `Release it. Tap ${key}, or tap the street.` : `Release it. Press Esc, click ${key}, or click the street.`; },
    target: (p) => (p.card ? '#popup:not([hidden]) .pop-close' : '#nav-app-inspect .insp-back'), done: (p) => !p.selected },
  { task: 'Move', bubble: menuOpen('Move', 'walk, run, ride or fly'),
    target: railKey('move'), done: opened('move') },
  // T-3445: People — the directory (T-3430), and in 1904 Follow for someone out in town (T-3404).
  { task: 'People',
    bubble: (p) => menuOpen('People', String(p.scene) === '1904' ? 'find anyone, visit their house, follow them' : 'find a person or a household')(p),
    target: railKey('people'), done: opened('people'), when: (p) => p.people !== false },
  { task: 'Settings', bubble: menuOpen('Settings', 'light, season, time of day, labels'),
    target: railKey('settings'), done: opened('settings') },
  { task: 'Ready', bubble: () => 'Ready. Take a Jaunt, Go to a place or a photo, or Jump years.',
    target: '#navigator', action: 'finish' },
];

/** Whether step `s` applies where the visitor is (no `when`: everywhere). */
const applies = (s, p) => { try { return !s.when || !!s.when(p); } catch { return true; } };

const angle = (a, b) => Math.abs(((a - b + 540) % 360) - 180);

export function createTour({ probe = () => ({}), render = () => {}, onFinish = () => {},
  storage = (() => { try { return globalThis.localStorage; } catch { return null; } })() } = {}) {
  let step = -1;          // -1: not running
  let base = null;        // the step's starting point
  let lastYaw = null;
  const read = () => { try { return JSON.parse(storage?.getItem(TOUR_KEY) || 'null'); } catch { return null; } };
  const write = (v) => { try { storage?.setItem(TOUR_KEY, JSON.stringify(v)); } catch { /* this page only */ } };
  const sample = () => { try { return probe() ?? {}; } catch { return {}; } };

  let shown = null;        // the view last painted, so a step repaints when its words change
  function view() {
    if (step < 0) return null;
    const s = STEPS[step];
    const p = sample();
    const live = STEPS.filter((x) => applies(x, p));
    return { step, n: live.indexOf(s) + 1 || step + 1, of: live.length, task: s.task, bubble: s.bubble(p),
      target: typeof s.target === 'function' ? s.target(p) : s.target,
      action: s.action ?? null, waiting: !s.action };
  }
  function paint(v) { shown = v; render(v); }
  function enter(i, { resumed = false } = {}) {
    // A step that does not apply here (no People app on this rail) is passed over.
    while (i < STEPS.length - 1 && !applies(STEPS[i], sample())) i++;
    step = i;
    if (!resumed) countField('tourStep'); // T-2660: a step reached, not one a reload resumes
    const p = sample();
    base = { e: p.e ?? 0, n: p.n ?? 0, opens: p.opens ?? 0, apps: { ...(p.apps ?? {}) }, turned: 0 };
    lastYaw = p.yawDeg ?? null;
    write({ active: true, step, done: !!read()?.done });
    paint(view());
  }
  function finish(how) {
    const was = step;
    step = -1; base = null;
    write({ active: false, step: null, done: how === 'finished' || !!read()?.done });
    paint(null);
    if (how === 'finished') onFinish();
    return was;
  }
  return {
    /** Start from step 01 (Guide's "Take the tour", and a replay). */
    start() { enter(0); return true; },
    /** A reload: pick the tour up where it was left, if it was running. */
    resume() {
      const saved = read();
      if (!saved?.active || !Number.isInteger(saved.step) || saved.step < 0 || saved.step >= STEPS.length) return false;
      enter(saved.step, { resumed: true });
      return true;
    },
    /** Next on step 01, Finish on the last; nothing on a step that waits for an action. */
    press() {
      if (step < 0) return false;
      const a = STEPS[step].action;
      if (a === 'next') { enter(step + 1); return true; }
      if (a === 'finish') { finish('finished'); return true; }
      return false;
    },
    skip() { if (step < 0) return false; finish('skipped'); return true; },
    /** Read the page; move on when the step's real action has happened. */
    tick() {
      if (step < 0) return false;
      const s = STEPS[step];
      const p = sample();
      if (Number.isFinite(p.yawDeg) && Number.isFinite(lastYaw)) base.turned += angle(p.yawDeg, lastYaw);
      if (Number.isFinite(p.yawDeg)) lastYaw = p.yawDeg;
      if (s.done?.(p, base)) { enter(step + 1); return true; }
      // The same step, said for where the visitor is now (the Navigator opened on a phone,
      // a mouse picked up): repaint only when the words or the ring move.
      const v = view();
      if (v.bubble !== shown?.bubble || v.target !== shown?.target) paint(v);
      return false;
    },
    get step() { return step; },
    get running() { return step >= 0; },
    get finished() { return !!read()?.done; },
    view,
  };
}
