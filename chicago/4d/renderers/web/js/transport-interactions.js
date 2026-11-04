// SPDX-License-Identifier: GPL-3.0-or-later
/** Moving drivers use the fort gate's Interact key and sequence engine.
 * The actor remains authoritative: a refused resume never changes its state.
 * No input handlers, model copies or invented conversation live in this adapter.
 */
const retired = new WeakSet();

export function registerTransportInteraction(interactions, actor, { reach = 6 } = {}) {
  if (!interactions?.add || !actor?.id || !actor?.name
      || typeof actor.stop !== 'function' || typeof actor.resume !== 'function'
      || typeof actor.canResume !== 'function' || !(Number.isFinite(reach) && reach > 0)) {
    throw Error('transport interaction requires a driver actor and the shared interaction engine');
  }
  const previous = interactions.get?.(`driver:${actor.id}`);
  if (previous && !retired.has(previous)) throw Error(`driver ${actor.id} already has an interaction`);
  let live = actor;
  const state = () => live?.state === 'moving' ? 'moving' : 'stopped';
  const refresh = () => { thing.state = state(); return thing; };
  const run = fn => t => {
    // Even a zero-second step receives run(0), then run(1). The command
    // happens once at its beginning; the sequence's finish is only a receipt.
    if (t !== 0 || !live?.visible) return;
    fn(live);
    refresh();
  };
  const stop = { id: 'stop', label: 'Stop driver', steps: [
    { label: 'Stopping', seconds: 0, run: run(a => a.stop('interaction')) },
  ] };
  const resume = { id: 'continue', label: 'Continue journey', steps: [
    { label: 'Continuing', seconds: 0, run: run(a => { if (a.canResume()) a.resume(); }) },
  ] };
  const blocked = { id: 'give-room', label: 'Step back to let the wagon pass', steps: [] };
  const thing = {
    id: `driver:${actor.id}`, name: actor.name, kind: 'vehicle',
    states: ['moving', 'stopped'], state: state(), reach,
    get at() {
      if (!live?.visible) return null;
      const at = live.at;
      return Array.isArray(at) && at.length === 2 && at.every(Number.isFinite) ? at : null;
    },
    get actions() {
      refresh();
      if (!live?.visible) return {};
      return { moving: [stop], stopped: [live.canResume() ? resume : blocked] };
    },
  };
  interactions.add(thing);
  return {
    thing, refresh,
    dispose() {
      // This adapter does not own the vehicle. Retire its offer even on the
      // original fort engine, which has no remove() API, without retaining it.
      live = null;
      retired.add(thing);
      thing.running = null;
      thing.state = 'stopped';
      interactions.remove?.(thing.id);
    },
  };
}

/** A layer owns its registrations, just as it owns its moving actors. */
export function registerTransportInteractions(interactions, actors, options) {
  const handles = actors.map(actor => registerTransportInteraction(interactions, actor, options));
  return {
    refresh() { for (const handle of handles) handle.refresh(); },
    dispose() { for (const handle of handles) handle.dispose(); },
    get list() { return handles.map(handle => handle.thing); },
  };
}
