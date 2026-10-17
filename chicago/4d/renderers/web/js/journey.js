/**
 * T-2613 (NAV-104): the journey — one tiny state machine every screen shares
 * (DESIGN §04, §14). The Observatory owns the first three states on its own page;
 * this page opens in the time-stream and moves forward from there:
 *
 *   observatory › locking › jumping › time-stream › landing › landed ›
 *   exploring ⇄ inspecting · on-jaunt · touring › recall
 *
 * A move the map does not allow is refused (returns false) rather than emitted, and
 * a move to the state already held is a no-op, so every transition is emitted once,
 * in order. Subscribers (HUD, Navigator, Tour, audio) call `on(fn)`; the current state
 * is also mirrored on <html data-journey> for CSS.
 */
export const JOURNEY_STATES = Object.freeze(['observatory', 'locking', 'jumping', 'time-stream',
  'landing', 'landed', 'exploring', 'inspecting', 'on-jaunt', 'touring', 'recall']);

const AFTER_LANDING = ['exploring', 'inspecting', 'on-jaunt', 'touring'];
const NEXT = {
  observatory: ['locking'],
  locking: ['jumping', 'observatory'],
  jumping: ['time-stream'],
  'time-stream': ['landing'],
  landing: ['landed'],
  landed: AFTER_LANDING,
  exploring: AFTER_LANDING,
  inspecting: AFTER_LANDING,
  'on-jaunt': AFTER_LANDING,
  touring: AFTER_LANDING,
  recall: [],
};

export function createJourney({ initial = 'time-stream', root = globalThis.document?.documentElement ?? null,
  now = () => (globalThis.performance?.now?.() ?? Date.now()) } = {}) {
  if (!JOURNEY_STATES.includes(initial)) throw new Error(`journey: unknown state ${initial}`);
  let state = initial;
  const listeners = new Set();
  const history = [{ state, at: now() }];
  if (root?.dataset) root.dataset.journey = state;

  function go(to) {
    if (to === state) return true;
    if (!JOURNEY_STATES.includes(to)) throw new Error(`journey: unknown state ${to}`);
    // Recall (back to the Observatory) is open from anywhere but itself.
    if (!(to === 'recall' || NEXT[state].includes(to))) return false;
    const from = state;
    state = to;
    history.push({ state, at: now() });
    if (root?.dataset) root.dataset.journey = state;
    for (const fn of [...listeners]) {
      try { fn({ from, to, state }); } catch (error) { console.error('[journey] listener failed', error); }
    }
    return true;
  }

  return {
    get state() { return state; },
    get history() { return history.map(h => ({ ...h })); },
    go,
    on(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    land: () => go('landing'),
    landed: () => go('landed'),
    explore: () => go('exploring'),
    recall: () => go('recall'),
  };
}
