/** Welcome presentation; destinations and safe spawn belong to the shared model. */
export function createWelcome({ gate, destinations, enter, resume, pause, hasEntered, isTouch = false }) {
  const $ = id => document.getElementById(id);
  const title = $('gate-title'), body = $('welcome'), close = $('welcome-close');
  const picker = $('welcome-picker'), jaunts = $('welcome-jaunts-region');
  const search = $('welcome-search'), list = $('welcome-results'), message = $('welcome-message');
  let state = 'arrival', kind = 'all', limit = 40;
  const kinds = [['all', 'All'], ['structure', 'Places'], ['business', 'Businesses'],
    ['person', 'People'], ['intersection', 'Corners'], ['anchor', 'Views']];
  for (const [id, label] of kinds) {
    const button = document.createElement('button');
    button.type = 'button'; button.textContent = label; button.dataset.kind = id;
    button.setAttribute('aria-pressed', String(id === kind));
    button.addEventListener('click', () => {
      kind = id; limit = 40;
      for (const b of $('welcome-kinds').children) b.setAttribute('aria-pressed', String(b === button));
      render();
    });
    $('welcome-kinds').appendChild(button);
  }
  function render() {
    const rows = destinations.search(search.value, { kind, includeReconstructed: true });
    list.replaceChildren(); message.textContent = '';
    for (const row of rows.slice(0, limit)) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'welcome-destination';
      button.dataset.kind = row.kind; button.dataset.id = row.id;
      const name = document.createElement('strong'), detail = document.createElement('span');
      name.textContent = row.label;
      const located = Number.isFinite(row.e) && Number.isFinite(row.n);
      // No invented destination for a person or firm whose address is unknown.
      detail.textContent = located ? row.sub : `${row.label} — no known starting place`;
      button.append(name, detail); button.disabled = !located;
      button.addEventListener('click', () => choose(row.kind, row.id));
      list.appendChild(button);
    }
    if (!rows.length) message.textContent = 'No matching places. Try another name or kind.';
    if (rows.length > limit) {
      const more = document.createElement('button'); more.type = 'button';
      more.className = 'welcome-link'; more.textContent = 'More places';
      more.addEventListener('click', () => { limit += 40; render(); }); list.appendChild(more);
    }
  }
  function region(which) {
    const explore = which === 'explore';
    picker.hidden = !explore; jaunts.hidden = explore;
    gate.dataset.region = which;
    $('welcome-explore').setAttribute('aria-expanded', String(explore));
    $('welcome-jaunts').setAttribute('aria-expanded', String(!explore));
    if (explore) { render(); search.focus(); }
  }
  function show() {
    pause(); state = 'welcome'; gate.hidden = false; gate.dataset.state = state;
    delete gate.dataset.region;
    body.hidden = false; picker.hidden = true; jaunts.hidden = true;
    $('welcome-explore').setAttribute('aria-expanded', 'false');
    $('welcome-jaunts').setAttribute('aria-expanded', 'false');
    title.textContent = 'Welcome to Chicago, summer 1835.';
    gate.querySelector('.gate-eyebrow').textContent = 'A town at the water’s edge';
    $('gate-btn').textContent = isTouch ? 'Tap to enter Chicago' : 'Enter Chicago';
    $('gate-btn').disabled = false;
    close.hidden = !hasEntered();
    title.focus({ preventScroll: true });
  }
  function choose(type, id) {
    if (state !== 'welcome') return false;
    if (type === 'jaunts' || type === 'explore') { region(type); return true; }
    const target = type === 'spawn' ? null : destinations.byId(type, id);
    if (type !== 'spawn' && !target) return false;
    if (!enter(target)) {
      message.textContent = 'There is no safe starting place here. Please choose another.';
      return false;
    }
    state = 'world'; gate.dataset.state = state;
    // Drop focus from the now-hidden search before movement keys are used.
    document.activeElement?.blur();
    return true;
  }
  function returnToWorld() {
    if (state !== 'welcome' || !hasEntered() || !resume()) return false;
    state = 'world'; gate.dataset.state = state; $('btn-start').focus(); return true;
  }
  $('welcome-jaunts').addEventListener('click', () => region('jaunts'));
  $('welcome-explore').addEventListener('click', () => region('explore'));
  $('welcome-jaunts-explore').addEventListener('click', () => region('explore'));
  $('gate-btn').addEventListener('click', () => choose('spawn'));
  $('btn-start').addEventListener('click', show);
  close.addEventListener('click', returnToWorld);
  search.addEventListener('input', () => { limit = 40; render(); });
  window.addEventListener('keydown', event => {
    if (gate.hidden) return;
    // Menu typing and navigation must never reach the world's keyboard handlers.
    event.stopImmediatePropagation();
    if (event.key === 'Escape') { event.preventDefault(); returnToWorld(); }
    if (event.key !== 'Tab') return;
    const controls = [...gate.querySelectorAll('button:not(:disabled), input')]
      .filter(el => el.getClientRects().length);
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && (document.activeElement === first || document.activeElement === title)) {
      event.preventDefault(); last?.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !gate.contains(document.activeElement))) {
      event.preventDefault(); first?.focus();
    }
  }, true);
  return { get state() { return state; }, enter: choose, show, close: returnToWorld };
}
