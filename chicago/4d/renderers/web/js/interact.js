/**
 * interact.js — things in the town a visitor can work, and the Interact key (T-3319).
 *
 * The owner, 2026-11-02: *"have like with inspect an interact button ... for the gate
 * where there is only two settings open and closed then you should be able to interact
 * and otherwise for future there may be some kind of interaction sequence on how or a
 * move to do something to interact with objects across the scenes, but start here with
 * the fort gates"*.
 *
 * So an INTERACTABLE is any object with:
 *
 *   id, name, kind          'fort_dearborn_palisade:s', 'South gate', 'gate'
 *   states, state           the states it can be in, and the one it is in now
 *   at, reach               where it is (local ENU [e, n]) and how near a visitor on foot
 *                           must stand to work it (metres)
 *   actions[state]          what can be done from that state: each `{ id, label, to,
 *                           steps }`, landing in state `to` when its last step ends
 *
 * and an action is a SEQUENCE of steps, each `{ label, seconds, run(t), prompt }`: `run`
 * is called with t from 0 to 1 over `seconds` (0 = at once), and a step with a `prompt`
 * waits, before it starts, for the visitor to press Interact again — the key reads the
 * prompt. A gate's open and close are one step each with no prompt; a thing that needs a
 * bar lifted before its leaves swing, or a pump handle worked three times, is the same
 * object with more steps. While a sequence runs the thing carries `running` (`{ action,
 * index, t, waiting }`) and its state is the one it started from; the state changes once,
 * when the last step ends.
 *
 * The KEY sits in the quick column under Inspect (index.html `#btn-interact`). It shows
 * while the visitor stands on foot within reach of something, names what Interact will do
 * there ("Open gate"), and R presses it from the keyboard. Nothing here knows THREE or the
 * DOM beyond the elements it is handed: tools/test_fort_gates.mjs drives it with fakes.
 */

export const INTERACT_KEY = 'KeyR';

/**
 * @param {object} [o]
 * @param {(thing: object, event: string) => void} [o.onChange]  told on every start, step and finish
 */
export function createInteractions({ onChange = () => {} } = {}) {
  const things = new Map();
  const listeners = new Set([onChange]);
  const tell = (thing, event) => { for (const fn of listeners) fn(thing, event); };

  function actionsOf(thing) {
    return thing?.actions?.[thing.state] ?? [];
  }

  /** What one press of Interact does at this thing now: { label, action, waiting, busy }. */
  function offer(thing) {
    if (!thing) return null;
    const r = thing.running;
    if (r) {
      const step = r.action.steps[r.index];
      return r.waiting
        ? { label: step.prompt, action: r.action, waiting: true, busy: false }
        : { label: `${step.label ?? r.action.label}…`, action: r.action, waiting: false, busy: true };
    }
    const action = actionsOf(thing)[0];
    return action ? { label: action.label, action, waiting: false, busy: false } : null;
  }

  function begin(thing, index) {
    const step = thing.running.action.steps[index];
    thing.running.index = index;
    thing.running.t = 0;
    thing.running.waiting = !!step.prompt;
    if (!step.prompt) step.run?.(0);
    tell(thing, step.prompt ? 'waiting' : 'step');
  }

  function finish(thing) {
    const { action } = thing.running;
    thing.running = null;
    thing.state = action.to ?? thing.state;
    tell(thing, 'done');
  }

  /** Advance one running step by dt seconds; a step done starts the next or finishes. */
  function advance(thing, dt) {
    const r = thing.running;
    if (!r || r.waiting) return;
    const step = r.action.steps[r.index];
    const seconds = Math.max(0, Number(step.seconds) || 0);
    r.t = seconds > 0 ? Math.min(1, r.t + dt / seconds) : 1;
    step.run?.(r.t);
    if (r.t < 1) return;
    if (r.index + 1 < r.action.steps.length) begin(thing, r.index + 1);
    else finish(thing);
  }

  return {
    get list() { return [...things.values()]; },
    get(id) { return things.get(id) ?? null; },
    add(thing) {
      if (!thing?.id || !Array.isArray(thing.states) || !thing.states.includes(thing.state)) {
        throw new Error(`interact: ${thing?.id ?? 'a thing'} needs an id, its states and a state among them`);
      }
      thing.running = null;
      things.set(thing.id, thing);
      return thing;
    },
    actionsOf,
    offer,
    /**
     * The thing a visitor at (e, n) facing `bearing` (compass degrees) would work: the
     * nearest within its reach, with what is ahead of them preferred to what is behind.
     */
    nearest(e, n, bearing = null) {
      let best = null, score = Infinity;
      for (const thing of things.values()) {
        if (!thing.at) continue;
        const de = thing.at[0] - e, dn = thing.at[1] - n;
        const d = Math.hypot(de, dn);
        if (d > (thing.reach ?? 5)) continue;
        let s = d;
        if (bearing !== null && d > 0.5) {
          const to = (Math.atan2(de, dn) * 180) / Math.PI;
          const off = Math.abs(((to - bearing + 540) % 360) - 180);
          if (off > 100) s += 3;                      // behind you: only if nothing is ahead
        }
        if (s < score) { score = s; best = thing; }
      }
      return best;
    },
    /**
     * Press Interact on a thing: start its first action, or let a waiting step go.
     * Returns what happened ({ ok, why }); a press while a step is moving does nothing.
     */
    act(id, actionId = null) {
      const thing = typeof id === 'string' ? things.get(id) : id;
      if (!thing) return { ok: false, why: 'nothing there' };
      const r = thing.running;
      if (r) {
        if (!r.waiting) return { ok: false, why: 'already moving' };
        r.waiting = false;
        r.action.steps[r.index].run?.(0);
        tell(thing, 'step');
        return { ok: true, started: r.action.id };
      }
      const actions = actionsOf(thing);
      const action = actionId ? actions.find((a) => a.id === actionId) : actions[0];
      if (!action) return { ok: false, why: `nothing to do while ${thing.state}` };
      if (!Array.isArray(action.steps) || !action.steps.length) {
        thing.state = action.to ?? thing.state;
        tell(thing, 'done');
        return { ok: true, started: action.id };
      }
      thing.running = { action, index: 0, t: 0, waiting: false };
      begin(thing, 0);
      tell(thing, 'start');
      return { ok: true, started: action.id };
    },
    /** Move every running sequence on by dt seconds (0 while the clock is held). */
    update(dt) {
      for (const thing of things.values()) if (thing.running) advance(thing, dt);
    },
    on(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    /** Every thing's state, for the smoke and the console. */
    snapshot() {
      return [...things.values()].map((t) => ({ id: t.id, name: t.name, kind: t.kind, state: t.state,
        running: t.running ? { action: t.running.action.id, index: t.running.index, t: t.running.t, waiting: t.running.waiting } : null }));
    },
  };
}

/**
 * The Interact key: shown while the visitor stands on foot within reach of something.
 *
 * @param {object} o
 * @param {ReturnType<typeof createInteractions>} o.interactions
 * @param {HTMLElement} [o.keyEl]        the button (#btn-interact)
 * @param {() => {e:number, n:number, bearing:number, flying:boolean} | null} o.where
 * @param {(text: string) => void} [o.say]  the HUD's status line
 * @param {() => boolean} [o.enabled]    false while the visitor is not in the town
 * @param {EventTarget} [o.keys]         where R is listened for (window)
 * @param {(target: EventTarget) => boolean} [o.isTyping]
 */
export function createInteractKey({ interactions, keyEl = null, where, say = () => {}, enabled = () => true,
  keys = null, isTyping = () => false } = {}) {
  let near = null;
  const words = keyEl?.querySelector?.('.ik-what') ?? null;

  function paint() {
    const o = near ? interactions.offer(near) : null;
    if (keyEl) {
      keyEl.hidden = !o;
      if (o) {
        if (words) words.textContent = o.label;
        else keyEl.textContent = o.label;
        keyEl.setAttribute?.('aria-label', `Interact: ${o.label} — ${near.name}`);
        keyEl.title = `Interact (R): ${o.label.replace(/…$/, '')} — ${near.name}`;
        keyEl.setAttribute?.('aria-disabled', o.busy ? 'true' : 'false');
        if (keyEl.dataset) keyEl.dataset.thing = near.id;
      }
    }
  }

  /** Re-read who is in reach. Cheap: a handful of things, a distance each. */
  function refresh() {
    const here = enabled() ? where?.() : null;
    const next = here && !here.flying ? interactions.nearest(here.e, here.n, here.bearing) : null;
    if (next !== near) near = next;
    paint();
    return near;
  }

  function press() {
    const thing = refresh();
    if (!thing) return { ok: false, why: 'nothing in reach' };
    const res = interactions.act(thing);
    paint();
    return res;
  }

  const off = interactions.on((thing, event) => {
    if (thing === near) paint();
    if (event === 'done') say(`${thing.name} ${thing.state}`);
  });
  const onClick = (e) => { e?.preventDefault?.(); press(); };
  keyEl?.addEventListener?.('click', onClick);
  const onKey = (e) => {
    if (e.code !== INTERACT_KEY || e.repeat || e.metaKey || e.ctrlKey || e.altKey) return;
    if (isTyping(e.target)) return;
    if (!enabled()) return;
    if (refresh()) { e.preventDefault?.(); press(); }
  };
  keys?.addEventListener?.('keydown', onKey);

  return {
    get current() { return near; },
    refresh,
    press,
    dispose() {
      off();
      keyEl?.removeEventListener?.('click', onClick);
      keys?.removeEventListener?.('keydown', onKey);
    },
  };
}
