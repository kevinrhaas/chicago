/** Content-only session state. No destination or jaunt identity is special. */
export const emptyState = () => ({ jaunt: null, session: null, leg: 0, stopIndex: 0,
  visited: [], vars: {}, inventory: [], events: [], phase: 'menu', choice: null, mode: null, estimate: null });
export function matches(test, vars, inventory) {
  if (!test) return true;
  if (test.all) return test.all.every(t => matches(t, vars, inventory));
  if (test.any) return test.any.some(t => matches(t, vars, inventory));
  if (test.not) return !matches(test.not, vars, inventory);
  if (test.has) return inventory.includes(test.has);
  const a = vars[test.var], b = test.value;
  return ({ '<': a < b, '<=': a <= b, '==': a === b, '!=': a !== b, '>=': a >= b, '>': a > b })[test.op] ?? false;
}
export const currentStop = s => s.jaunt?.stops.find(stop => stop.id === s.visited[s.stopIndex]?.id);
export const choicesFor = s => (currentStop(s)?.choices || []).filter(c => matches(c.when, s.vars, s.inventory));
export const canNext = s => ['atStop', 'detail'].includes(s.phase)
  && !!(s.stopIndex < s.visited.length - 1 || currentStop(s)?.next || s.choice);
const append = (s, type, data = {}) => ({ ...s, events: [...s.events,
  { id: `${s.session}:${s.events.length + 1}`, type, ...data }] });
function effects(s, list = []) {
  const vars = { ...s.vars }, inventory = new Set(s.inventory);
  for (const e of list) {
    if (e.var) {
      vars[e.var] = e.op === 'set' ? e.value : vars[e.var] + e.value;
      const bounds = s.jaunt.variables[e.var];
      if (!Number.isInteger(vars[e.var]) || vars[e.var] < bounds.min || vars[e.var] > bounds.max) throw new Error('Variable outside validated bounds');
    } else if (e.op === 'add') inventory.add(e.item);
    else if (e.op === 'remove') inventory.delete(e.item);
  }
  if (inventory.size > (s.jaunt.inventory?.capacity ?? 0)) throw new Error('Inventory capacity exceeded');
  return { ...s, vars, inventory: [...inventory] };
}
function move(s, index) {
  return append({ ...s, stopIndex: index, leg: s.leg + 1, phase: 'travelling', choice: null, error: null, instant: false },
    'depart', { stop: s.visited[index].id, leg: s.leg + 1 });
}
export function reduce(s, e) {
  if (e.type === 'START') {
    if (!e.jaunt?.stops?.length || e.jaunt.review_required) throw new Error('Jaunt unavailable');
    return append({ ...emptyState(), jaunt: e.jaunt, session: e.session, leg: 1, phase: 'opening',
      visited: [{ id: e.jaunt.stops[0].id }], mode: e.jaunt.allowed_modes?.includes(e.mode) ? e.mode : e.jaunt.default_mode,
      vars: Object.fromEntries(Object.entries(e.jaunt.variables || {}).map(([k, v]) => [k, v.initial])),
      inventory: [...(e.jaunt.inventory?.initial || [])] }, 'start');
  }
  if (!s.jaunt) return s;
  if (['ARRIVE', 'STOPPED', 'FAILED'].includes(e.type) && (e.session !== s.session || e.leg !== s.leg)) return s;
  if (e.type === 'END') return emptyState();
  if (e.type === 'MODE' && s.jaunt.allowed_modes?.includes(e.mode) && e.mode !== s.mode && s.phase !== 'outcome') {
    const changed = append({ ...s, mode: e.mode }, 'mode', { mode: e.mode });
    return ['travelling', 'paused'].includes(s.phase) ? move(changed, s.stopIndex) : changed;
  }
  if (e.type === 'INSTANT' && ['travelling', 'paused'].includes(s.phase))
    return { ...move(s, s.stopIndex), instant: true };
  if (e.type === 'RIDE' && s.phase === 'paused') return move(s, s.stopIndex);
  if (e.type === 'ARRIVE' && ['opening', 'travelling'].includes(s.phase))
    return append({ ...s, phase: 'atStop', error: null }, 'arrival', { stop: currentStop(s).id, leg: s.leg });
  if (e.type === 'FAILED' && s.phase === 'travelling') return { ...s, error: e.message };
  if (e.type === 'STOPPED' && s.phase === 'travelling')
    return append({ ...s, phase: 'paused', leg: s.leg + 1, error: null }, 'pause', { reason: e.reason });
  if (e.type === 'MENU') {
    if (['menu', 'outcome'].includes(s.phase)) return s;
    return append({ ...s, phase: 'menu', resumePhase: s.phase === 'detail' ? 'atStop' : s.phase === 'paused' ? 'travelling' : s.phase, leg: s.leg + 1 }, 'pause');
  }
  if (e.type === 'RESUME' && s.phase === 'menu') {
    const resumed = append({ ...s, phase: s.resumePhase || 'atStop' }, 'resume');
    return resumed.phase === 'travelling' ? move(resumed, s.stopIndex) : resumed;
  }
  if (e.type === 'DETAIL' && s.phase === 'atStop') return { ...s, phase: 'detail' };
  if (e.type === 'RETURN' && s.phase === 'detail') return { ...s, phase: 'atStop' };
  if (e.type === 'RETRY' && s.phase === 'travelling' && s.error) return move(s, s.stopIndex);
  if (e.type === 'PREV' && ['travelling', 'paused', 'atStop', 'detail'].includes(s.phase)) return s.stopIndex ? move(s, s.stopIndex - 1) : s;
  if (!['atStop', 'detail'].includes(s.phase)) return s;
  if (e.type === 'CHOOSE' && !s.visited[s.stopIndex].committed && choicesFor(s).some(c => c.id === e.id)) return { ...s, choice: e.id };
  if (e.type !== 'NEXT' || !canNext(s)) return s;
  if (s.stopIndex < s.visited.length - 1) return move(s, s.stopIndex + 1);
  const stop = currentStop(s), choice = choicesFor(s).find(c => c.id === s.choice), next = choice?.next ?? stop.next;
  if (next === 'Previous') return s.stopIndex ? move(s, s.stopIndex - 1) : s;
  let updated = effects(s, choice?.effects);
  updated = append({ ...updated, visited: s.visited.map((v, i) => i === s.stopIndex ? { ...v, committed: true, choice: choice?.id, next } : v) }, 'decision', { stop: stop.id, choice: choice?.id ?? null });
  const ending = next === '$end'
    ? s.jaunt.endings.find(x => !x.default && matches(x.when, updated.vars, updated.inventory)) || s.jaunt.endings.find(x => x.default)
    : s.jaunt.endings.find(x => x.id === next);
  if (ending) return append({ ...updated, phase: 'outcome', outcome: ending, choice: null, leg: s.leg + 1 }, 'complete', { ending: ending.id });
  if (!s.jaunt.stops.some(x => x.id === next)) throw new Error('Unknown validated stop');
  return move({ ...updated, visited: [...updated.visited, { id: next }] }, updated.visited.length);
}

/** Adapters own UI and travel. Tokens invalidate every obsolete completion. */
export function createJaunts({ load, resolve, place, travel, enter, showMenu, render, openDetail, closeDetail, onError, estimate = () => null }) {
  let state = emptyState(), serial = 0, request, destroyed = false, previousMode;
  const restore = () => { if (previousMode !== undefined) travel.setMode(previousMode); previousMode = undefined; };
  const cancel = (reason = 'jaunt') => travel.stop(reason);
  function dispatch(event) {
    const old = state;
    state = reduce(state, event);
    if (state === old) return false;
    if (state.jaunt && (state.leg !== old.leg || state.phase !== old.phase || state.mode !== old.mode))
      state = { ...state, estimate: estimate(state) };
    render(state);
    if (state.phase === 'travelling' && (old.leg !== state.leg || old.phase !== state.phase)) {
      cancel(['MODE', 'INSTANT'].includes(event.type) ? 'replan' : 'jaunt'); closeDetail();
      if (previousMode === undefined) previousMode = travel.mode;
      const token = { session: state.session, leg: state.leg }, target = resolve(currentStop(state).destination);
      travel.setMode(state.instant ? 'instantly' : state.mode);
      if (!target || !travel.go(target, { token,
        onArrive: tags => dispatch({ type: 'ARRIVE', ...tags }),
        onStop: tags => dispatch({ type: 'STOPPED', ...tags }) }))
        dispatch({ type: 'FAILED', ...token, message: 'This stop could not be reached. Try again, go back, or end the jaunt.' });
    } else if (state.phase === 'paused') {
      cancel(); restore();
    } else if (['menu', 'outcome'].includes(state.phase)) {
      cancel(); closeDetail(); restore(); showMenu({ state, returnId: state.jaunt?.id ?? old.jaunt?.id });
    }
    return true;
  }
  async function start(id, { mode } = {}) {
    const generation = ++serial; request?.abort(); request = new AbortController();
    state = emptyState(); cancel(); closeDetail(); restore(); render(state);
    try {
      const jaunt = await load(id, { signal: request.signal });
      if (destroyed || generation !== serial) return false;
      if (!jaunt?.stops?.length || jaunt.review_required) throw new Error('Jaunt unavailable');
      const target = resolve(jaunt.stops[0].destination);
      if (!target || !enter(target) || !place(target)) throw new Error('Starting place unavailable');
      previousMode = travel.mode;
      state = reduce(state, { type: 'START', jaunt, session: generation, mode });
      dispatch({ type: 'ARRIVE', session: generation, leg: state.leg });
      return true;
    } catch (error) { if (generation === serial && error.name !== 'AbortError') onError(error); return false; }
    finally { if (generation === serial) request = null; }
  }
  const explore = () => { ++serial; request?.abort(); state = emptyState(); cancel(); closeDetail(); restore(); render(state); };
  return { start, get state() { return state; }, next: () => dispatch({ type: 'NEXT' }), prev: () => dispatch({ type: 'PREV' }),
    choose: id => dispatch({ type: 'CHOOSE', id }), retry: () => dispatch({ type: 'RETRY' }),
    setMode: mode => dispatch({ type: 'MODE', mode }), straight: () => dispatch({ type: 'INSTANT' }),
    resumeRide: () => dispatch({ type: 'RIDE' }),
    end() { ++serial; request?.abort(); return dispatch({ type: 'END' }); }, menu: () => dispatch({ type: 'MENU' }),
    resume() { if (state.phase !== 'menu' || !state.jaunt || !enter(null, { resume: true })) return false;
      previousMode = travel.mode; return dispatch({ type: 'RESUME' }); },
    restart: () => state.jaunt && start(state.jaunt.id, { mode: state.mode }),
    detail(link) { if (dispatch({ type: 'DETAIL' })) openDetail(link); },
    returnFromDetail: () => dispatch({ type: 'RETURN' }), explore,
    destroy() { destroyed = true; explore(); },
  };
}
