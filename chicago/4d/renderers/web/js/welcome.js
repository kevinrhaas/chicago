/** Welcome presentation; destinations and safe spawn belong to the shared model. */
import { scenePresentation } from './scene-presentation.js';
import { iconSvg } from './menu-icons.js';
// T-2120: five one-tap starting points per scene, picked for what they show of the
// town; any anchor the scene does not carry is skipped, and a scene with no list
// offers its own first viewpoints instead.
export const QUICK_STARTS = {
  1835: [['from_above', 'Town from above', 'aerial'], ['fort_dearborn', 'Fort Dearborn', 'fort'],
    ['forks', 'The forks', 'forks'], ['south_water', 'South Water St.', 'street'],
    ['newberry_dole_wharf', 'The wharf', 'wharf']],
};
export function createWelcome({ gate, scene = { id: '1835', target_date: '1835-07-01' }, destinations, enter, resume, pause, hasEntered, onJaunts = () => {}, onExplore = () => {}, isTouch = false }) {
  const $ = id => document.getElementById(id);
  const title = $('gate-title'), body = $('welcome'), close = $('welcome-close');
  const picker = $('welcome-picker'), jaunts = $('welcome-jaunts-region');
  const search = $('welcome-search'), list = $('welcome-results'), message = $('welcome-message');
  const spawn = $('gate-btn'), back = $('welcome-back');
  let state = 'arrival', kind = 'all', limit = 40;
  $('welcome-jaunts').insertAdjacentHTML('afterbegin', iconSvg('jaunts', 22));
  $('welcome-explore').insertAdjacentHTML('afterbegin', iconSvg('start', 22));
  back.innerHTML = iconSvg('back', 20);
  search.insertAdjacentHTML('beforebegin', iconSvg('search', 16));
  const listed = QUICK_STARTS[scene.id] || (scene.anchors || []).slice(0, 5).map(a => [a.id, a.label || a.id, 'view']);
  for (const [id, label, glyph] of listed) {
    if (!destinations.byId('anchor', id)) continue;
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'welcome-quick-start'; button.dataset.id = id;
    button.innerHTML = iconSvg(glyph, 24);
    const name = document.createElement('span'); name.textContent = label; button.appendChild(name);
    button.title = destinations.byId('anchor', id).label;
    button.addEventListener('click', () => choose('anchor', id));
    $('welcome-quick').appendChild(button);
  }
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
  // T-2120: every sub-view has a way back to the three choices — the back arrow, or Escape.
  function top() {
    const was = gate.dataset.region;
    picker.hidden = jaunts.hidden = true; delete gate.dataset.region;
    $('welcome-explore').setAttribute('aria-expanded', 'false');
    $('welcome-jaunts').setAttribute('aria-expanded', 'false');
    $(was === 'explore' ? 'welcome-explore' : 'welcome-jaunts').focus({ preventScroll: true });
  }
  function region(which) {
    const explore = which === 'explore';
    picker.hidden = !explore; jaunts.hidden = explore;
    gate.dataset.region = which;
    $('welcome-explore').setAttribute('aria-expanded', String(explore));
    $('welcome-jaunts').setAttribute('aria-expanded', String(!explore));
    // A phone would raise its keyboard over the quick starts; focus the region instead.
    if (explore) { onExplore(); render(); if (isTouch) { picker.tabIndex = -1; picker.focus({ preventScroll: true }); } else search.focus(); }
    else {
      onJaunts();
      // T-2046: held sideways the compact welcome hides the button that was just
      // pressed, so focus would fall to the page; give it to the region it opened.
      if (!$('welcome-jaunts').getClientRects().length) { jaunts.tabIndex = -1; jaunts.focus({ preventScroll: true }); }
    }
  }
  // T-0472. A scene's own interpretive cards: what an event is called, whose accounts
  // it rests on, where they disagree. The text is the project's; each quote is a
  // source's words with its attribution, and a held card says so on its face.
  function about(year) {
    const cards = (scene.cards || []).filter(card => card && card.title && card.text);
    const box = $('welcome-about'), list = $('welcome-about-cards');
    box.hidden = !cards.length; list.replaceChildren();
    if (!cards.length) return;
    box.querySelector('summary').textContent = `About ${year}: names, evidence and what is not shown`;
    for (const card of cards) {
      const article = document.createElement('article'), h = document.createElement('h3'), p = document.createElement('p');
      article.className = 'welcome-about-card'; article.dataset.card = card.id;
      h.textContent = card.title; p.textContent = card.text;
      article.append(h, p);
      for (const q of card.quotes || []) {
        const figure = document.createElement('figure'), quote = document.createElement('blockquote'), cite = document.createElement('figcaption');
        quote.textContent = `“${q.text}”`; cite.textContent = q.cite;
        figure.append(quote, cite); article.appendChild(figure);
      }
      if (card.review_required) {
        const held = document.createElement('p');
        held.className = 'welcome-about-held'; held.textContent = card.review_note;
        article.appendChild(held);
      }
      list.appendChild(article);
    }
  }
  function show({ focus = true } = {}) {
    pause(); state = 'welcome'; gate.hidden = false; gate.dataset.state = state;
    delete gate.dataset.region;
    body.hidden = false; picker.hidden = true; jaunts.hidden = true;
    $('welcome-explore').setAttribute('aria-expanded', 'false');
    $('welcome-jaunts').setAttribute('aria-expanded', 'false');
    const presentation = scenePresentation(scene.id, scene.target_date);
    title.textContent = presentation.welcomeTitle;
    gate.querySelector('.gate-eyebrow').textContent = presentation.eyebrow;
    gate.querySelector('.welcome-intro').textContent = presentation.intro;
    about(presentation.year);
    // The arrival's own button becomes the third choice: straight into the town.
    if (spawn.parentElement !== back.parentElement) back.parentElement.appendChild(spawn);
    spawn.classList.add('welcome-action');
    spawn.innerHTML = `${iconSvg('explore', 22)}<strong>Explore<span class="welcome-long"> by myself</span></strong><span>Free roam</span>`;
    spawn.setAttribute('aria-label', isTouch ? 'Explore by myself: tap to enter Chicago' : 'Explore by myself: enter Chicago');
    spawn.disabled = false;
    close.hidden = !hasEntered();
    if (focus) title.focus({ preventScroll: true });
  }
  function choose(type, id) {
    if (state !== 'welcome') return false;
    if (type === 'jaunts' || type === 'explore') { region(type); return true; }
    const target = type === 'spawn' ? null : destinations.byId(type, id);
    if (type !== 'spawn' && !target) return false;
    onExplore();
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
  back.addEventListener('click', top);
  $('gate-btn').addEventListener('click', () => choose('spawn'));
  $('btn-start').addEventListener('click', show);
  close.addEventListener('click', returnToWorld);
  search.addEventListener('input', () => { limit = 40; render(); });
  window.addEventListener('keydown', event => {
    if (gate.hidden) return;
    // Menu typing and navigation must never reach the world's keyboard handlers.
    event.stopImmediatePropagation();
    if (event.key === 'Escape') { event.preventDefault(); if (gate.dataset.region) top(); else returnToWorld(); }
    if (event.key !== 'Tab') return;
    const controls = [...gate.querySelectorAll('button:not(:disabled), input, select:not(:disabled), a[href]')]
      .filter(el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && (document.activeElement === first || document.activeElement === title)) {
      event.preventDefault(); last?.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !gate.contains(document.activeElement))) {
      event.preventDefault(); first?.focus();
    }
  }, true);
  return { get state() { return state; }, enter: choose, show, close: returnToWorld };
}
