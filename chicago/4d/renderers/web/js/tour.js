/**
 * Tour mode, the Field Check (T-2663, NAV-801; design doc section 11, M10).
 *
 * Seven steps the Navigator runs itself, framed as a Confluence Laboratory field check.
 * Every step waits for the visitor to actually do the thing — read from the page through
 * `probe()`, never assumed — and Skip is always there. Progress is kept per device
 * (localStorage, inside try/catch), so a reload mid-tour resumes at the same step; it can
 * be replayed, and abandoned, from Guide.
 *
 * Bubbles are 14 words or fewer (section 11). Where a step's own app is not built yet the
 * step completes on the real action the page has today, and says so here:
 *   - step 05's tabs are the building card's (Evidence, Images, Liberties, Record) until
 *     the Inspect tabs land (T-2639), so its bubble names the Full record, not "Design";
 *   - step 06 completes on a Confidence view preset other than Normal (T-2647): the
 *     colouring on, or a grade hidden — the state every such preset puts in force;
 *   - step 07's Finish ends the tour and calls `onFinish`, which awards the Navigator
 *     License keepsake (T-2665, js/license.js); Skip ends it without.
 *
 * `probe()` returns { yawDeg, e, n, opens, deeper, confidence, confChanges, scene, front }:
 * the camera's bearing, where the visitor stands, how many times Inspect or a building card
 * has opened on a structure, how many times a deeper layer of a record was opened, whether
 * the Confidence view is doing anything and how many times it has changed, the scene id,
 * and the name of the building in front of the visitor (or null). The counters are what
 * make a step wait for an action taken DURING it: a card already open, or a Confidence
 * view already on, when the step begins does not complete it.
 */
export const TOUR_KEY = 'chicago4d.tour';
export const YAW_DEG = 60;
export const WALK_M = 5;

/** The seven steps. `task` is the field-check line over the bubble; `target` the selector
 *  the spotlight rings; `done(p, base)` whether the step's real action has happened. */
export const STEPS = [
  { task: 'Your device', bubble: () => 'This is your Navigator. Everything you need lives here.',
    target: '#navigator', action: 'next' },
  { task: 'Look around', bubble: () => 'Look around. Drag the right side of the screen (or move the mouse).',
    target: null, done: (p, base) => base.turned >= YAW_DEG },
  { task: 'Walk', bubble: () => 'Walk. Left thumb, or W A S D. Head for the corner.',
    target: null, done: (p, base) => Math.hypot(p.e - base.e, p.n - base.n) >= WALK_M },
  { task: 'Inspect a structure',
    // Section 11: in 1904 the Glessner House; in 1835 and 1812 the building in front of you.
    bubble: (p) => `Tap the ${String(p.scene) === '1904' ? 'Glessner House' : (p.front || 'building in front of you')}. Every building has a file.`,
    target: null, done: (p, base) => (p.opens ?? 0) > base.opens },
  { task: 'Go deeper', bubble: () => 'Front page first. The Full record goes deeper. Open it.',
    target: '#navigator', done: (p, base) => p.deeper > base.deeper },
  // T-2647: the Confidence view is a Navigator app now (the HUD chip is gone), so the step
  // rings the device; any preset but Normal — the colouring on, or a grade hidden — does it.
  { task: 'How sure are we?', bubble: () => 'How sure are we? Turn on the Confidence view.',
    target: '#navigator', done: (p, base) => !!p.confidence && (p.confChanges ?? 0) > base.confChanges },
  { task: 'Ready', bubble: () => 'Ready. Take a Jaunt, or Jump to another year.',
    target: '#navigator', action: 'finish' },
];

const angle = (a, b) => Math.abs(((a - b + 540) % 360) - 180);

export function createTour({ probe = () => ({}), render = () => {}, onFinish = () => {},
  storage = (() => { try { return globalThis.localStorage; } catch { return null; } })() } = {}) {
  let step = -1;          // -1: not running
  let base = null;        // the step's starting point
  let lastYaw = null;
  const read = () => { try { return JSON.parse(storage?.getItem(TOUR_KEY) || 'null'); } catch { return null; } };
  const write = (v) => { try { storage?.setItem(TOUR_KEY, JSON.stringify(v)); } catch { /* this page only */ } };
  const sample = () => { try { return probe() ?? {}; } catch { return {}; } };

  function view() {
    if (step < 0) return null;
    const s = STEPS[step];
    const p = sample();
    return { step, n: step + 1, of: STEPS.length, task: s.task, bubble: s.bubble(p), target: s.target,
      action: s.action ?? null, waiting: !s.action };
  }
  function enter(i) {
    step = i;
    const p = sample();
    base = { e: p.e ?? 0, n: p.n ?? 0, deeper: p.deeper ?? 0, opens: p.opens ?? 0, confChanges: p.confChanges ?? 0, turned: 0 };
    lastYaw = p.yawDeg ?? null;
    write({ active: true, step, done: !!read()?.done });
    render(view());
  }
  function finish(how) {
    const was = step;
    step = -1; base = null;
    write({ active: false, step: null, done: how === 'finished' || !!read()?.done });
    render(null);
    if (how === 'finished') onFinish();
    return was;
  }
  return {
    /** Start from step 01 (Guide's "Take the field check", and a replay). */
    start() { enter(0); return true; },
    /** A reload: pick the tour up where it was left, if it was running. */
    resume() {
      const saved = read();
      if (!saved?.active || !Number.isInteger(saved.step) || saved.step < 0 || saved.step >= STEPS.length) return false;
      enter(saved.step);
      return true;
    },
    /** Next on step 01, Finish on step 07; nothing on a step that waits for an action. */
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
      return false;
    },
    get step() { return step; },
    get running() { return step >= 0; },
    get finished() { return !!read()?.done; },
    view,
  };
}
