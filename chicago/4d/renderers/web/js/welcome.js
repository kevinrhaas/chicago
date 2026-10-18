/** Welcome presentation; destinations and safe spawn belong to the shared model. */
import { scenePresentation } from './scene-presentation.js';
import { iconSvg } from './menu-icons.js';
import { markTerms } from './term-tips.js';
import { placeDistance, arrowTurn, cardinal, ARROW_SVG, hiddenReason } from './goto.js';
import { formatDistance } from './units.js';
import { SORTS, normal } from './destinations.js';

/** T-2740: the chosen order lasts the session (a tab), like the rest of an outing. */
const SORT_KEY = 'chicago4d.goto.sort';
const sortStore = (() => { try { return globalThis.sessionStorage ?? null; } catch { return null; } })();

/** Go to's filters (T-2632, DESIGN §07): All, then Places · People · Shops & work ·
 *  Viewpoints. A kind the scene has none of is not offered. Corners stay in All's search. */
export const GO_TO_KINDS = [['all', 'All'], ['structure', 'Places'], ['person', 'People'],
  ['business', 'Shops & work'], ['anchor', 'Viewpoints']];
/** The filters a scene offers: All, and each kind it has at least one of. */
export const offeredKinds = (destinations) => GO_TO_KINDS
  .filter(([id]) => id === 'all' || destinations.search('', { kind: id, includeReconstructed: true }).length > 0);
/** A row's distance and bearing from where the visitor stands: 'here' within 4 m, else
 *  { words: '120 m NE', turn: degrees for the arrow }; null with no position. */
export function rowDistance(row, v, units = 'imperial') {
  const d = placeDistance(row, v);
  if (!d) return null;
  if (d.m < 4) return { here: true, words: 'here' };
  return { here: false, words: `${formatDistance(d.m, units)} ${cardinal(d.bearing)}`, turn: arrowTurn(d, v) };
}
// T-2120: five one-tap starting points per scene, picked for what they show of the
// town; any anchor the scene does not carry is skipped, and a scene with no list
// offers its own first viewpoints instead.
export const QUICK_STARTS = {
  1835: [['from_above', 'Town from above', 'aerial'], ['fort_dearborn', 'Fort Dearborn', 'fort'],
    ['forks', 'The forks', 'forks'], ['south_water', 'South Water St.', 'street'],
    ['newberry_dole_wharf', 'The wharf', 'wharf']],
};
export function createWelcome({ gate, scene = { id: '1835', target_date: '1835-07-01' }, destinations, enter, resume, pause, hasEntered, onJaunts = () => {}, onExplore = () => {}, isTouch = false,
  // T-2630: told before the card shows, so the Navigator's Jaunts app hands back the
  // Jaunts list and the Go to search it borrowed.
  onShow = () => {},
  // T-2632: where the visitor stands ({ e, n, bearingDeg }) and their units, for each row's
  // distance and bearing.
  visitor = () => null, units = () => 'imperial',
  // T-2633: the grades the Confidence view is hiding; their rows are dimmed and say why.
  hiddenGrades = () => [] }) {
  const $ = id => document.getElementById(id);
  const title = $('gate-title'), body = $('welcome'), close = $('welcome-close');
  const picker = $('welcome-picker'), jaunts = $('welcome-jaunts-region');
  const search = $('welcome-search'), list = $('welcome-results'), message = $('welcome-message');
  const roam = $('home-roam'), back = $('welcome-back');
  let state = 'arrival', kind = 'all', limit = 40;
  let sort = (() => { try { return sortStore?.getItem(SORT_KEY); } catch { return null; } })();
  const sorts = destinations.sorts ?? SORTS;
  if (!sorts.some(s => s.id === sort)) sort = 'near';
  $('welcome-jaunts').insertAdjacentHTML('afterbegin', iconSvg('jaunts', 22));
  $('welcome-explore').insertAdjacentHTML('afterbegin', iconSvg('start', 22));
  roam.insertAdjacentHTML('afterbegin', iconSvg('explore', 22));
  roam.setAttribute('aria-label', isTouch ? 'Free roam: tap to enter Chicago' : 'Free roam: enter Chicago');
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
  const offered = new Set(offeredKinds(destinations).map(([id]) => id));
  for (const [id, label] of GO_TO_KINDS) {
    const button = document.createElement('button');
    button.type = 'button'; button.textContent = label; button.dataset.kind = id;
    button.setAttribute('aria-pressed', String(id === kind));
    // T-2632 (QA-14): no chip for a kind with nothing in it — no "Corners 0".
    if (!offered.has(id)) button.hidden = true;
    button.addEventListener('click', () => {
      kind = id; limit = 40;
      for (const b of $('welcome-kinds').children) b.setAttribute('aria-pressed', String(b === button));
      render();
    });
    $('welcome-kinds').appendChild(button);
  }
  const sortSelect = $('welcome-sort');
  if (sortSelect) {
    for (const { id, label } of sorts) sortSelect.add(new Option(label, id, false, id === sort));
    sortSelect.value = sort;
    sortSelect.addEventListener('change', () => {
      sort = sorts.some(s => s.id === sortSelect.value) ? sortSelect.value : 'near'; limit = 40;
      try { sortStore?.setItem(SORT_KEY, sort); } catch { /* the order still applies to this page */ }
      render(); list.scrollTop = 0;
    });
  }
  function render() {
    let here = null; try { here = visitor(); } catch { here = null; }
    const rows = destinations.search(search.value, { kind, includeReconstructed: true, sort, visitor: here });
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
      // T-2740: the line says what the list is ordered by when the title does not.
      const by = sort === 'owner' ? row.owner : sort === 'address' ? row.address?.text : null;
      if (by && !normal(row.label).includes(normal(sort === 'address' ? String(row.address.number) : by))) detail.textContent += ` · ${by}`;
      const text = document.createElement('div'); text.className = 'welcome-dest-text';
      text.append(name, ' ', detail);
      button.append(text); button.disabled = !located;
      // T-2633: a grade the Confidence view is hiding is dimmed, and says why in one line.
      let off = null; try { off = new Set(hiddenGrades() ?? []); } catch { off = new Set(); }
      if ((row.kind === 'structure' || row.kind === 'business') && row.presence && off.has(row.presence)) {
        button.classList.add('is-hidden-grade'); button.dataset.hiddenGrade = row.presence;
        const why = document.createElement('small'); why.className = 'welcome-why'; why.textContent = hiddenReason(row.presence);
        text.append(' ', why);
      }
      // T-2632: how far, and which way, from where you stand.
      const v = here;
      const d = located ? rowDistance(row, v, units()) : null;
      if (d) {
        const dist = document.createElement('span'); dist.className = 'welcome-dist';
        if (d.here) dist.append(d.words);
        else {
          const arrow = document.createElement('i'); arrow.setAttribute('aria-hidden', 'true');
          arrow.style.setProperty('--turn', `${d.turn}deg`); arrow.innerHTML = ARROW_SVG;
          const words = document.createElement('small'); words.textContent = d.words;
          dist.append(arrow, words);
        }
        button.append(' ', dist);
      }
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
    try { onShow(); } catch { /* the card shows regardless */ }
    pause(); state = 'welcome'; gate.hidden = false; gate.dataset.state = state;
    delete gate.dataset.region;
    body.hidden = false; picker.hidden = true; jaunts.hidden = true;
    $('welcome-explore').setAttribute('aria-expanded', 'false');
    $('welcome-jaunts').setAttribute('aria-expanded', 'false');
    const presentation = scenePresentation(scene.id, scene.target_date);
    title.textContent = presentation.welcomeTitle;
    gate.querySelector('.welcome-intro').textContent = presentation.intro;
    // T-2662: the intro is where Reconstructed and Sources first appear: tap either for its line.
    markTerms(gate.querySelector('.welcome-intro'));
    about(presentation.year);
    // T-2613: the eyebrow is the device's ARRIVED stamp; Free roam (#home-roam) is the
    // third choice, straight into the town.
    gate.querySelector('.gate-eyebrow').textContent = presentation.stamp;
    close.hidden = !hasEntered();
    if (focus) title.focus({ preventScroll: true });
  }
  function choose(type, id) {
    // T-2630: in the town, the Navigator's Go to (this same search, lent to it) picks a
    // place too; only the card's own sub-views need the card.
    if (state !== 'welcome' && !(state === 'world' && type !== 'jaunts' && type !== 'explore')) return false;
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
    state = 'world'; gate.dataset.state = state;
    // T-2625: Start / Jaunts lives in the Navigator now; focus returns to it where it shows,
    // else to the Navigator's own handle (the grip on a phone, the rail's key on a desktop).
    const back = ['btn-start', 'nav-grip', 'nav-collapse'].map((id) => document.getElementById(id))
      .find((el) => el?.checkVisibility?.() ?? el?.getClientRects?.().length > 0);
    (back ?? $('btn-start')).focus();
    return true;
  }
  $('welcome-jaunts').addEventListener('click', () => region('jaunts'));
  $('welcome-explore').addEventListener('click', () => region('explore'));
  back.addEventListener('click', top);
  roam.addEventListener('click', () => choose('spawn'));
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
  // T-2630: `refresh` re-runs the search, for the Navigator's Go to when it shows.
  return { get state() { return state; }, enter: choose, show, close: returnToWorld, refresh: () => render() };
}
