/** Content-only session state. No destination or jaunt identity is special. */
export const SESSION_KEY = 'c4d.jaunt.session.v1';
export const emptyState = () => ({ jaunt: null, session: null, leg: 0, stopIndex: 0,
  visited: [], vars: {}, inventory: [], events: [], eventSeq: 0, phase: 'menu', choice: null,
  mode: null, estimate: null, notice: null, restored: false, context: null, contextDismissed: false });
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
const money = cents => Math.abs(cents) < 100 ? `${Math.abs(cents)} ¢` : `$${(Math.abs(cents) / 100).toFixed(2)}`;
const label = name => name.replace(/[_-]+/g, ' ').replace(/^./, c => c.toUpperCase());
// Units a visitor can read as a resource. Any other unit (the pilot's `preference`) is
// the outing's own bookkeeping for branching, and is never shown as a chip or a cost.
const SHOWN_UNITS = new Set(['cents', 'minutes', 'count']);
export const shownResource = spec => SHOWN_UNITS.has(spec?.unit);
export function formatResource(name, value, spec = {}) {
  if (spec.unit === 'cents') return `${label(name)} ${money(value)}`;
  if (spec.unit === 'minutes') return `${label(name)} ${value} min`;
  return `${label(name)} ${value}`;
}
function rawEffects(s, list = []) {
  const vars = { ...s.vars }, inventory = new Set(s.inventory);
  let overflow = null;
  for (const e of list) {
    if (e.var) {
      const spec = s.jaunt.variables[e.var], raw = e.op === 'set' ? e.value : vars[e.var] + e.value;
      if (raw < spec.min || raw > spec.max) overflow ??= { kind: 'variable', name: e.var, raw, spec };
      vars[e.var] = Math.max(spec.min, Math.min(spec.max, raw));
    } else if (e.op === 'add') {
      if (!inventory.has(e.item) && inventory.size >= (s.jaunt.inventory?.capacity ?? 0))
        overflow ??= { kind: 'inventory', item: e.item };
      else inventory.add(e.item);
    } else if (e.op === 'remove') inventory.delete(e.item);
  }
  return { vars, inventory: [...inventory], overflow };
}
export function choiceStatus(s, choice) {
  if (!matches(choice.when, s.vars, s.inventory)) {
    const test = choice.when;
    if (test?.var && s.jaunt.variables[test.var]?.unit === 'cents')
      return { available: false, reason: `Needs ${money(test.value)} · you have ${money(s.vars[test.var])}` };
    if (test?.has) return { available: false, reason: `Needs ${label(test.has)}` };
    return { available: false, reason: 'Unavailable after your earlier choices' };
  }
  const result = rawEffects(s, choice.effects);
  if (result.overflow?.kind === 'inventory')
    return { available: false, reason: `Basket full · ${s.inventory.length} of ${s.jaunt.inventory.capacity}` };
  if (result.overflow?.kind === 'variable') {
    const { name, raw, spec } = result.overflow;
    if (spec.unit === 'cents' && raw < spec.min)
      return { available: false, reason: `Not enough ${label(name).toLowerCase()} · you have ${money(s.vars[name])}` };
    return { available: false, reason: `${label(name)} is already at its ${raw > spec.max ? 'maximum' : 'minimum'}` };
  }
  return { available: true, reason: null };
}
export const choicesFor = s => (currentStop(s)?.choices || []).filter(c => choiceStatus(s, c).available);
export function choiceConsequence(s, choice) {
  const details = [];
  for (const e of choice.effects || []) {
    if (e.var) {
      const spec = s.jaunt.variables[e.var];
      if (!shownResource(spec)) continue;
      if (spec.unit === 'cents' && e.op === 'inc' && e.value < 0)
        details.push(`costs ${money(e.value)} · you have ${money(s.vars[e.var])}`);
      else if (e.op === 'inc') details.push(`${label(e.var)} ${e.value >= 0 ? '+' : ''}${e.value} · you have ${s.vars[e.var]}`);
      else details.push(`${label(e.var)} becomes ${formatResource(e.var, e.value, spec).replace(`${label(e.var)} `, '')}`);
    } else if (e.op === 'add') details.push(`adds ${label(e.item).toLowerCase()} · basket ${s.inventory.length}/${s.jaunt.inventory?.capacity ?? 0}`);
    else if (e.op === 'remove') details.push(`uses ${label(e.item).toLowerCase()}`);
  }
  return details.length ? details.join(' · ') : choice.consequence;
}
export function resourceSummary(s) {
  const rows = Object.entries(s.jaunt?.variables || {}).filter(([, spec]) => shownResource(spec)).map(([name, spec]) => formatResource(name, s.vars[name], spec));
  if (s.jaunt?.inventory) rows.push(`Basket ${s.inventory.length}/${s.jaunt.inventory.capacity}`);
  return rows;
}
export const canNext = s => (s.phase === 'atStop' || (s.phase === 'detail' && s.detailPhase === 'atStop'))
  && !!(s.stopIndex < s.visited.length - 1 || currentStop(s)?.next || s.choice);
const append = (s, type, data = {}, eventId = null) => {
  const eventSeq = s.eventSeq + 1;
  return { ...s, eventSeq, events: [...s.events,
    { id: eventId || `${s.session}:${eventSeq}`, type, ...data }] };
};
function effects(s, list = []) {
  const { vars, inventory } = rawEffects(s, list);
  return { ...s, vars, inventory };
}
function initialResources(jaunt) {
  return { vars: Object.fromEntries(Object.entries(jaunt.variables || {}).map(([k, v]) => [k, v.initial])),
    inventory: [...(jaunt.inventory?.initial || [])] };
}
function revise(s) {
  const kept = s.visited.slice(0, s.stopIndex + 1).map((v, i) => i === s.stopIndex
    ? { id: v.id } : { ...v });
  let resources = { ...s, ...initialResources(s.jaunt) };
  for (const visit of kept.slice(0, -1)) {
    const stop = s.jaunt.stops.find(x => x.id === visit.id);
    const choice = stop?.choices?.find(x => x.id === visit.choice);
    resources = effects(resources, choice?.effects);
  }
  const cut = s.events.findIndex(event => event.type === 'decision' && event.stop === currentStop(s).id);
  resources = { ...resources, visited: kept, choice: null, phase: 'atStop', outcome: null,
    error: null, events: cut < 0 ? s.events : s.events.slice(0, cut), restored: false };
  return append(resources, 'revise', { stop: currentStop(s).id });
}
const fallbackEnding = () => ({ id: 'content-error', fallback: true, completion_eligible: false, read_s: 0,
  text: 'This outing reached an unfinished ending. Return to the Jaunts Menu and choose another route.' });
function endingFor(s, next) {
  const endings = s.jaunt.endings || [];
  if (next === '$end') return endings.find(x => !x.default && matches(x.when, s.vars, s.inventory))
    || endings.find(x => x.default) || fallbackEnding();
  const ending = endings.find(x => x.id === next);
  return ending && matches(ending.when, s.vars, s.inventory) ? ending : fallbackEnding();
}
function move(s, index) {
  return append({ ...s, fromStopId: index === s.stopIndex ? s.fromStopId : currentStop(s)?.id, context: null, contextDismissed: false, stopIndex: index, leg: s.leg + 1, phase: 'travelling', choice: null, error: null, instant: false },
    'depart', { stop: s.visited[index].id, leg: s.leg + 1 });
}
export function reduce(s, e) {
  if (e.type === 'START') {
    if (!e.jaunt?.stops?.length || e.jaunt.review_required) throw new Error('Jaunt unavailable');
    return append({ ...emptyState(), jaunt: e.jaunt, session: e.session, leg: 1, phase: 'opening',
      visited: [{ id: e.jaunt.stops[0].id }], mode: e.jaunt.allowed_modes?.includes(e.mode) ? e.mode : e.jaunt.default_mode,
      ...initialResources(e.jaunt) }, 'start');
  }
  if (!s.jaunt) return s;
  if (['ARRIVE', 'STOPPED', 'FAILED', 'CONTEXT'].includes(e.type) && (e.session !== s.session || e.leg !== s.leg)) return s;
  if (e.type === 'CONTEXT' && s.phase === 'travelling') return { ...s, context: e.context };
  if (e.type === 'DISMISS_CONTEXT') return { ...s, contextDismissed: true };
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
    return append({ ...s, phase: 'menu', resumePhase: s.phase === 'detail' ? s.detailPhase || 'atStop' : s.phase === 'paused' ? 'travelling' : s.phase, leg: s.leg + 1 }, 'pause');
  }
  if (e.type === 'RESUME' && s.phase === 'menu') {
    const resumed = append({ ...s, phase: s.resumePhase || 'atStop' }, 'resume');
    return resumed.phase === 'travelling' ? move(resumed, s.stopIndex) : resumed;
  }
  if (e.type === 'DETAIL' && ['atStop', 'travelling', 'paused'].includes(s.phase))
    return { ...s, phase: 'detail', detailPhase: s.phase, leg: s.leg + (s.phase === 'travelling' ? 1 : 0) };
  if (e.type === 'RETURN' && s.phase === 'detail')
    return s.detailPhase === 'travelling' ? move(s, s.stopIndex) : { ...s, phase: s.detailPhase || 'atStop', detailPhase: null };
  if (e.type === 'RETRY' && s.phase === 'travelling' && s.error) return move(s, s.stopIndex);
  if (e.type === 'PREV' && ['travelling', 'paused', 'atStop', 'detail'].includes(s.phase)) return s.stopIndex ? move(s, s.stopIndex - 1) : s;
  if (e.type === 'REVISE' && ['atStop', 'detail'].includes(s.phase) && s.visited[s.stopIndex]?.committed) return revise(s);
  if (!['atStop', 'detail'].includes(s.phase)) return s;
  if (e.type === 'CHOOSE' && !s.visited[s.stopIndex].committed && choicesFor(s).some(c => c.id === e.id)) return { ...s, choice: e.id };
  if (e.type !== 'NEXT' || !canNext(s)) return s;
  if (s.stopIndex < s.visited.length - 1) return move(s, s.stopIndex + 1);
  const stop = currentStop(s), choice = stop.choices?.find(c => c.id === s.choice), next = choice?.next ?? stop.next;
  if (next === 'Previous') return s.stopIndex ? move(s, s.stopIndex - 1) : s;
  const eventId = e.eventId || `${s.session}:decision:${stop.id}:${choice?.id ?? 'continue'}`;
  if (s.events.some(event => event.id === eventId)) return s;
  let updated = effects(s, choice?.effects);
  updated = append({ ...updated, visited: s.visited.map((v, i) => i === s.stopIndex ? { ...v, committed: true, choice: choice?.id, next } : v) },
    'decision', { stop: stop.id, choice: choice?.id ?? null }, eventId);
  const ending = next === '$end' || s.jaunt.endings.some(x => x.id === next) ? endingFor(updated, next) : null;
  if (ending) return append({ ...updated, phase: 'outcome', outcome: ending, choice: null, leg: s.leg + 1,
    error: ending.fallback ? 'No declared ending matched this route.' : null }, 'complete', { ending: ending.id });
  if (!s.jaunt.stops.some(x => x.id === next)) throw new Error('Unknown validated stop');
  return move({ ...updated, visited: [...updated.visited, { id: next }] }, updated.visited.length);
}

export function replaySession(jaunt, saved, session = 1) {
  if (!saved || saved.jaunt !== jaunt.id || saved.content_version !== jaunt.content_version || !Array.isArray(saved.events))
    throw new Error('version');
  if (saved.events.length > 500 || saved.events.some(e => !e || typeof e.id !== 'string' || typeof e.type !== 'string'))
    throw new Error('corrupt');
  const mode = [...saved.events].reverse().find(e => e.type === 'mode')?.mode || jaunt.default_mode;
  let state = reduce(emptyState(), { type: 'START', jaunt, session, mode });
  state = reduce(state, { type: 'ARRIVE', session, leg: state.leg });
  for (const event of saved.events.filter(e => e.type === 'decision')) {
    if (state.phase === 'outcome' || currentStop(state)?.id !== event.stop) throw new Error('corrupt');
    if (event.choice != null) state = reduce(state, { type: 'CHOOSE', id: event.choice });
    state = reduce(state, { type: 'NEXT', eventId: event.id });
    if (state.phase === 'travelling') state = reduce(state, { type: 'ARRIVE', session, leg: state.leg });
  }
  if (saved.events.some(e => e.type === 'complete') && state.phase !== 'outcome') throw new Error('corrupt');
  const position = [...saved.events].reverse().find(e => ['arrival', 'depart'].includes(e.type) && e.stop);
  const positionIndex = position && state.visited.findIndex(visit => visit.id === position.stop);
  if (positionIndex >= 0 && state.phase !== 'outcome') state = { ...state, stopIndex: positionIndex };
  return state.phase === 'outcome' ? { ...state, restored: true }
    : { ...state, phase: 'menu', resumePhase: 'atStop', restored: true };
}

/** Adapters own UI and travel. Tokens invalidate every obsolete completion. */
export function createJaunts({ scene = '1835', load, resolve, place, travel, enter, showMenu, render, openDetail, closeDetail, onError,
  estimate = () => null, contextForRoute = () => null, onComplete = () => {}, storage: suppliedStorage }) {
  const sessionKey = scene === '1835' ? SESSION_KEY : `${SESSION_KEY}.${scene}`;
  let state = emptyState(), serial = 0, request, detailRequest, destroyed = false, previousMode;
  let storage = suppliedStorage;
  if (storage === undefined) { try { storage = globalThis.localStorage; } catch { storage = null; } }
  const clearSaved = () => { try { storage?.removeItem(sessionKey); } catch { /* memory-only */ } };
  const persist = () => {
    if (!state.jaunt) return clearSaved();
    try { storage?.setItem(sessionKey, JSON.stringify({ content_version: state.jaunt.content_version,
      jaunt: state.jaunt.id, events: state.events })); } catch { /* memory-only */ }
  };
  const restore = () => { if (previousMode !== undefined) travel.setMode(previousMode); previousMode = undefined; };
  const cancel = (reason = 'jaunt') => travel.stop(reason);
  const dismissDetail = () => { detailRequest?.abort(); detailRequest = null; closeDetail(); };
  function dispatch(event) {
    const old = state;
    state = reduce(state, event);
    if (state === old) return false;
    // T-1258: the one moment an outing completes; the daybook's award is idempotent anyway.
    if (state.phase === 'outcome' && old.phase !== 'outcome') { try { onComplete(state); } catch { /* the outing still ends */ } }
    if (old.phase === 'detail' && state.phase !== 'detail') dismissDetail();
    if (state.jaunt && !['DETAIL', 'RETURN'].includes(event.type) && (state.leg !== old.leg || state.phase !== old.phase || state.mode !== old.mode))
      state = { ...state, estimate: estimate(state) };
    render(state);
    if (state.phase === 'travelling' && (old.leg !== state.leg || old.phase !== state.phase)) {
      cancel(['MODE', 'INSTANT'].includes(event.type) ? 'replan' : 'jaunt'); dismissDetail();
      if (previousMode === undefined) previousMode = travel.mode;
      const token = { session: state.session, leg: state.leg }, target = resolve(currentStop(state).destination);
      travel.setMode(state.instant ? 'instantly' : state.mode);
      if (!target || !travel.go(target, { token,
        onArrive: tags => dispatch({ type: 'ARRIVE', ...tags }),
        onStop: tags => dispatch({ type: 'STOPPED', ...tags }),
        onRoute: route => {
          if (state.session !== token.session || state.leg !== token.leg || state.phase !== 'travelling') return;
          dispatch({ type: 'CONTEXT', ...token, context: contextForRoute(state, route) });
        } }))
        dispatch({ type: 'FAILED', ...token, message: 'This stop could not be reached. Try again, go back, or end the jaunt.' });
    } else if (state.phase === 'detail') {
      cancel('detail');
    } else if (state.phase === 'paused') {
      cancel(); restore();
    } else if (['menu', 'outcome'].includes(state.phase)) {
      cancel(); dismissDetail(); restore(); showMenu({ state, returnId: state.jaunt?.id ?? old.jaunt?.id });
    }
    persist();
    return true;
  }
  async function start(id, { mode } = {}) {
    const generation = ++serial; request?.abort(); request = new AbortController();
    state = emptyState(); clearSaved(); cancel(); dismissDetail(); restore(); render(state);
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
  async function restoreSession() {
    let saved;
    try {
      const raw = storage?.getItem(sessionKey);
      if (!raw) return false;
      saved = JSON.parse(raw);
      if (!saved || typeof saved.jaunt !== 'string' || !Array.isArray(saved.events)) throw new Error('corrupt');
    } catch {
      clearSaved(); state = { ...emptyState(), notice: 'A damaged saved outing was discarded.' }; render(state); return false;
    }
    try {
      const jaunt = await load(saved.jaunt);
      if (saved.content_version !== jaunt.content_version) throw new Error('version');
      state = replaySession(jaunt, saved, ++serial); render(state); persist(); return true;
    } catch (error) {
      clearSaved(); state = { ...emptyState(), notice: error.message === 'version'
        ? 'A saved outing from an older version was discarded.' : 'A damaged saved outing was discarded.' };
      render(state); return false;
    }
  }
  const explore = () => { ++serial; request?.abort(); state = emptyState(); clearSaved(); cancel(); dismissDetail(); restore(); render(state); };
  return { start, get state() { return state; }, next: () => dispatch({ type: 'NEXT' }), prev: () => dispatch({ type: 'PREV' }),
    choose: id => dispatch({ type: 'CHOOSE', id }), retry: () => dispatch({ type: 'RETRY' }),
    revise: () => dispatch({ type: 'REVISE' }), restore: restoreSession,
    setMode: mode => dispatch({ type: 'MODE', mode }), straight: () => dispatch({ type: 'INSTANT' }),
    resumeRide: () => dispatch({ type: 'RIDE' }),
    end() { ++serial; request?.abort(); return dispatch({ type: 'END' }); }, menu: () => dispatch({ type: 'MENU' }),
    resume() { if (state.phase !== 'menu' || !state.jaunt) return false;
      const target = state.restored ? resolve(currentStop(state).destination) : null;
      if (state.restored && (!target || !enter(target) || !place(target))) return false;
      if (!state.restored && !enter(null, { resume: true })) return false;
      previousMode = travel.mode; state = { ...state, restored: false }; return dispatch({ type: 'RESUME' }); },
    restart: () => state.jaunt && start(state.jaunt.id, { mode: state.mode }),
    detail(link) {
      if (!dispatch({ type: 'DETAIL' })) return false;
      detailRequest = new AbortController();
      const signal = detailRequest.signal;
      Promise.resolve().then(() => { if (!signal.aborted) return openDetail(link, { signal }); }).catch(() => {
        if (!signal.aborted) dispatch({ type: 'RETURN' });
      });
      return true;
    },
    dismissContext: () => dispatch({ type: 'DISMISS_CONTEXT' }),
    returnFromDetail: () => dispatch({ type: 'RETURN' }), explore,
    destroy() { destroyed = true; explore(); },
  };
}
