/**
 * Tour mode, the Field Check (T-2663, NAV-801; design doc section 11, M10).
 *
 * Ten steps (T-3642, T-3742) the Navigator runs itself, framed as a Confluence Laboratory field check.
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
 * T-3642 (the owner, 2026-11-17) brings it to the interface as it is after the T-3629 sweep:
 * an Interact step (talk to anyone, ride a horse, take a boat) and a Jaunts step take the
 * People step's place, and the bubbles say Shift / a full push runs.
 *
 * T-3742 (the owner, 2026-11-23: "update the first time user tour so it is current") brings
 * it to what has landed since: Interact names Tell me a story and Ask a question (T-3553),
 * Jaunts names the mysteries and the parts to play (T-3663, T-3678, T-3679, T-3693),
 * Settings names Language, Reading age and Graphics (T-3680, T-3645, T-3736), and Ready
 * sends the visitor on: a Jaunt, Home's Go to, or Free roam. The owner, the
 * same day: "dont you just go to jaunt or free roam or find after the tour?" A Jump step
 * was tried and dropped for that, and because "1871 ... is kind of early in development,
 * 1904 is much more refined": the tour names no other year.
 *
 * Bubbles are 14 words or fewer (section 11). The last step's Finish ends the tour and calls
 * `onFinish`, which awards the Navigator License keepsake (T-2665, js/license.js); Skip
 * ends it without.
 *
 * `probe()` returns { yawDeg, e, n, opens, acts, selected, card, apps, app, touch, level, scene, front }:
 * the camera's bearing, where the visitor stands, how many times Inspect or a building
 * card has opened on a structure, how many times the visitor has used the Interact key
 * (T-3642), whether one is open now (and whether it is the floating
 * card, T-3022), how many times each Navigator
 * app has been opened, whether the visitor is on touch, how far the Navigator is open
 * (0 docked), the scene id, the name of the building in front of the visitor (or
 * null). The counters are what make a step wait for an action taken DURING it: a card
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

/** The ten steps. `task` is the field-check line over the bubble; `target` the selector
 *  the spotlight rings (or a function of the probe); `done(p, base)` whether the step's
 *  real action has happened; `when(p)`, where given, whether the step applies here — a
 *  step that does not is passed over and not counted.
 *
 *  T-3642 (the owner, 2026-11-17: "We have added a lot of capabilities and design changes
 *  so update the tour"): the rail is labelled and is a tab bar on a phone (T-3629); Look and
 *  Walk name Click-to-look and Shift / a full push to run; Interact is the town's one "use"
 *  key, for a person (Greet, Tell me a story, Ask a question), a horse to ride, a boat's
 *  helm or a gate (T-3319, T-3553, T-3560, T-3612); Jaunts are narrated and told for the
 *  visitor's grade (T-3578, T-3590). People's own step gave way to Interact: the People
 *  key is labelled on the rail.
 *
 *  T-3742: Interact is said as what a visitor does with it most, talk; a horse to ride is
 *  Move's ("ride"). Ready sends the visitor on and never to another year. */
export const STEPS = [
  { task: 'Your device',
    bubble: (p) => (p.touch ? 'This is your Navigator. Tap it open: every menu is a tab.'
      : 'This is your Navigator. Every menu is a key on its rail.'),
    target: '#navigator', action: 'next' },
  { task: 'Look around',
    bubble: (p) => (p.touch ? 'Look around. Drag the right side of the screen.'
      : 'Look around. Click the scene, then move the mouse.'),
    target: null, done: (p, base) => base.turned >= YAW_DEG },
  { task: 'Walk',
    bubble: (p) => (p.touch ? 'Walk with your left thumb. Push it all the way to run.'
      : 'Walk with W A S D. Hold Shift to run.'),
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
    target: (p) => (p.card ? '#popup:not([hidden]) .pop-close' : '#nav-app-inspect .insp-back'), done: (p) => !p.selected,
    escape: 'page' }, // T-3671: Esc is this step's own action, so the card does not take it to end the tour
  // T-3642: the Interact key, used during the step (a press, or its list opened on a person).
  // T-3742: walking up to someone opens their card by itself and never holds the walk
  // (T-3553); the key's list is Greet, Tell me a story, Ask a question. The ring is on the
  // key once it shows.
  { task: 'Interact',
    bubble: (p) => (p.touch ? 'Walk up to someone. Tap Interact: greet, hear a story, ask a question.'
      : 'Walk up to someone. Press R: greet them, hear a story, ask a question.'),
    target: '#btn-interact', done: (p, base) => (p.acts ?? 0) > (base.acts ?? 0) },
  // T-3642: Jaunts, narrated (T-3578) and told for the visitor's age (T-3590, T-3629).
  // T-3742: and the case jaunts (Make your case) and play-a-part jaunts (T-3663, T-3679).
  { task: 'Jaunts', bubble: menuOpen('Jaunts', 'stories read aloud, mysteries to solve, parts to play'),
    target: railKey('jaunts'), done: opened('jaunts') },
  // T-3629: Move left the rail; it is Home's Move tile. The ring goes dock, Home key, tile.
  { task: 'Move',
    bubble: (p) => (p.touch && !(p.level > 0) ? 'Open the Navigator, then Move on Home: walk, run, ride or fly.'
      : 'Open Move on Home: walk, run, ride or fly.'),
    target: (p) => (p.touch && !(p.level > 0) ? '#navigator' : p.app === 'home' ? '#nav-tile-move' : railKey('home')(p)),
    done: opened('move') },
  // T-3742: Display's Language and Reading age (T-3680, T-3645), the Graphics tab (T-3736).
  { task: 'Settings', bubble: menuOpen('Settings', 'language, reading age, graphics, name cards, sound'),
    target: railKey('settings'), done: opened('settings') },
  // T-3742 (the owner, 2026-11-23): Ready sends the visitor on, in the year they are in: the
  // Jaunts key, or Home's Go to and Free roam (T-3629).
  { task: 'Ready', bubble: () => 'Ready. Pick a Jaunt, Go to someone, or Free roam.',
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
      action: s.action ?? null, waiting: !s.action, escape: s.escape ?? 'end' };
  }
  function paint(v) { shown = v; render(v); }
  function enter(i, { resumed = false } = {}) {
    // A step that does not apply here is passed over.
    while (i < STEPS.length - 1 && !applies(STEPS[i], sample())) i++;
    step = i;
    if (!resumed) countField('tourStep'); // T-2660: a step reached, not one a reload resumes
    const p = sample();
    base = { e: p.e ?? 0, n: p.n ?? 0, opens: p.opens ?? 0, acts: p.acts ?? 0, apps: { ...(p.apps ?? {}) }, turned: 0 };
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
