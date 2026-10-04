import { currentStop, choicesFor, canNext, choiceStatus, choiceConsequence, resourceSummary } from './jaunts.js';
import { claimPresentation } from './jaunt-context.js';
import { PACES } from './travel-settings.js';
import { formatEstimate } from './travel-estimate.js';

/** The scrollable story and persistent controls have separate layout ownership. */
export function createJauntPanel({ destinations, actions }) {
  const sheet = document.createElement('link'); sheet.rel = 'stylesheet';
  sheet.href = new URL('../css/jaunt.css', import.meta.url); document.head.append(sheet);
  const node = (tag, text, className) => {
    const el = document.createElement(tag); el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  const button = (text, fn) => {
    const el = node('button', text); el.type = 'button'; el.addEventListener('click', fn); return el;
  };
  const root = node('section', '', 'jaunt-panel'); root.id = 'jaunt-panel'; root.hidden = true;
  root.setAttribute('aria-label', 'Current jaunt');
  const body = node('div', '', 'jaunt-body'), controls = node('nav', '', 'jaunt-controls');
  controls.setAttribute('aria-label', 'Jaunt navigation');
  const buttons = {};
  for (const [id, label] of [['prev', 'Previous Stop'], ['next', 'Next Stop'], ['end', 'End Jaunt'], ['menu', 'Jaunts Menu']]) {
    buttons[id] = button(label, () => actions[id]()); buttons[id].dataset.action = id; controls.append(buttons[id]);
  }
  const mode = node('select'); mode.setAttribute('aria-label', 'Jaunt travel mode');
  mode.title = 'Fly is a viewing convenience, not 1835 transport.';
  mode.addEventListener('change', () => actions.setMode(mode.value));
  const straight = button('Go straight to next stop', actions.straight); straight.dataset.action = 'straight';
  controls.prepend(mode, straight);
  // Collapsing folds the panel to one bar — where you are, Next Stop, and a tap to
  // open it again — so the world can be looked at from a stop on a phone, where the
  // open panel covers most of the screen. Arriving at a new stop opens it again.
  let collapsed = false;
  const collapse = button('▾', () => setCollapsed(true)); collapse.className = 'jaunt-collapse';
  collapse.setAttribute('aria-label', 'Collapse the outing panel'); collapse.setAttribute('aria-expanded', 'true');
  const bar = node('div', '', 'jaunt-bar'), barLabel = button('', () => setCollapsed(false));
  barLabel.className = 'jaunt-bar-label'; barLabel.setAttribute('aria-expanded', 'false');
  const barNext = button('Next Stop', () => actions.next()); barNext.dataset.action = 'bar-next';
  const barReturn = button('Return', () => { if (state?.phase === 'detail') actions.returnFromDetail(); else actions.closeOverlay(); }); barReturn.hidden = true; barReturn.dataset.action = 'return';
  const barEnd = button('End', actions.end); barEnd.setAttribute('aria-label', 'End Jaunt');
  bar.append(barLabel, barNext, barReturn, barEnd);
  root.append(collapse, body, controls, bar); document.body.append(root);
  // Native controls and translated/wrapped labels can make this row taller.
  // Reserve its measured height for cards and drawers instead of guessing it —
  // the controls' when the panel is open, the bar's when it is collapsed.
  const measureNav = () => {
    const el = collapsed ? bar : controls, height = el.offsetHeight;
    if (height > 0) document.documentElement.style.setProperty('--jaunt-nav', `${Math.ceil(height) + 1}px`);
  };
  const controlSize = new ResizeObserver(measureNav);
  controlSize.observe(controls); controlSize.observe(bar);
  function setCollapsed(value, { focus = true } = {}) {
    if (collapsed === value) return;
    collapsed = value; root.classList.toggle('jaunt-collapsed', value);
    document.documentElement.toggleAttribute('data-jaunt-collapsed', value);
    measureNav();
    if (focus) (value ? barLabel : collapse).focus({ preventScroll: true });
  }
  root.addEventListener('keydown', e => e.stopPropagation());
  let state, key, overlayView = null;
  const saveView = () => { overlayView ??= { scroll: body.scrollTop, collapsed, focus: document.activeElement?.dataset.link }; };
  const restoreView = () => {
    if (!overlayView) return;
    const saved = overlayView; overlayView = null;
    setCollapsed(saved.collapsed, { focus: false }); body.scrollTop = saved.scroll;
    [...body.querySelectorAll('[data-link]')].find(el => el.dataset.link === saved.focus)?.focus({ preventScroll: true });
  };
  const overlayOpen = () => ['popup', 'panel', 'jaunt-context-card'].some(id => { const el = document.getElementById(id); return el && !el.hidden; });
  const syncOverlay = () => {
    const open = overlayOpen(), was = document.activeElement;
    const lost = open && (!was || was === document.body || body.contains(was));
    if (open && state?.jaunt) { saveView(); setCollapsed(true, { focus: false }); }
    root.classList.toggle('jaunt-detail', open); body.hidden = open; barNext.hidden = open; barReturn.hidden = !open;
    // T-2046: the link that opened a card or source is now hidden with the story (and a
    // tap never focused it): keep focus on the outing — Return, which undoes the detour —
    // rather than leave it on the page.
    if (lost && !barReturn.hidden) barReturn.focus({ preventScroll: true });
    if (!open) {
      if (state?.phase === 'detail') actions.returnFromDetail();
      restoreView();
    }
  };
  const observer = new MutationObserver(syncOverlay);
  for (const id of ['popup', 'panel', 'jaunt-context-card']) {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { attributes: true, attributeFilter: ['hidden'] });
  }
  function prose(parent, text, ids = [], narrative = false) {
    const claims = ids.map(id => state.jaunt.evidence.find(c => c.id === id));
    const unsafe = claims.some(c => claimPresentation(c).text === 'Unverified attribution withheld.');
    const paragraph = node('p', unsafe ? 'Unverified attribution withheld.' : text, narrative ? 'jaunt-narrative' : '');
    paragraph.title = paragraph.textContent; parent.append(paragraph);
    const chips = node('div', '', 'jaunt-evidence');
    for (const claim of claims) {
      const presentation = claimPresentation(claim), fold = node('details', '', presentation.narrative ? 'jaunt-narrative' : '');
      fold.append(node('summary', `${presentation.label} ${claim?.id || 'Evidence'}`), node('p', presentation.text));
      if (presentation.narrative) fold.append(node('small', 'Invented connective narrative; not a historical quotation.'));
      for (const id of claim?.sources || []) fold.append(button('Read source', () => actions.detail({ kind: 'source', id, label: 'Source' })));
      chips.append(fold);
    }
    parent.append(chips);
  }
  function contextLines(parent) {
    for (const line of state.context?.lines || []) {
      if (line.generated) {
        const row = node('p', line.text); row.append(node('small', ' [MAP] Reconstruction route', 'jaunt-map-note')); parent.append(row);
      } else prose(parent, line.text, line.evidence, line.evidence?.every(id => state.jaunt.evidence.find(c => c.id === id)?.confidence === 'reconstructed'));
    }
  }
  function render(next) {
    const old = state;
    if (next.phase === 'detail' && old?.phase !== 'detail') saveView();
    state = next;
    const active = !!state.jaunt && !['menu', 'outcome'].includes(state.phase);
    root.hidden = !active; document.documentElement.toggleAttribute('data-jaunt-active', active);
    if (!active) { key = null; overlayView = null; setCollapsed(false, { focus: false }); return; }
    const stop = currentStop(state), nextKey = `${state.session}:${stop.id}`, same = key === nextKey;
    if (old?.session !== state.session) {
      mode.replaceChildren(...state.jaunt.allowed_modes.map(id => {
        const option = node('option', PACES[id].label); option.value = id; return option;
      }));
    }
    mode.value = state.mode;
    straight.hidden = !['travelling', 'paused'].includes(state.phase);
    mode.classList.toggle('jaunt-mode-wide', straight.hidden);
    const scroll = same ? (overlayView?.scroll ?? body.scrollTop) : 0, focused = document.activeElement?.dataset.choice;
    const heading = node('h2', destinations.byId(stop.destination.kind, stop.destination.id)?.label || stop.destination.id);
    heading.tabIndex = -1;
    const progress = node('p', `${state.jaunt.title} · Stop ${state.stopIndex + 1} of ${state.jaunt.stops.length}`, 'jaunt-progress');
    progress.setAttribute('aria-live', 'polite'); body.replaceChildren(progress, heading);
    const resources = resourceSummary(state);
    if (resources.length) {
      const strip = node('ul', '', 'jaunt-resources'); strip.setAttribute('aria-label', 'Outing resources');
      strip.replaceChildren(...resources.map(text => node('li', text))); body.append(strip);
    }
    if (state.estimate) {
      const eta = node('p', `${formatEstimate(state.estimate)} remaining`, 'jaunt-progress'); eta.dataset.jauntRemaining = ''; body.append(eta);
    }
    if (state.mode === 'fly') body.append(node('p', 'Fly is a viewing convenience, not 1835 transport.', 'jaunt-progress'));
    const travelling = ['travelling', 'paused'].includes(state.phase) || (state.phase === 'detail' && ['travelling', 'paused'].includes(state.detailPhase));
    if (travelling) {
      body.append(node('p', state.phase === 'paused' ? 'Ride paused. Explore here, or resume when you are ready.' : state.error || 'On the way to the next stop…'));
      if (state.context?.lines.length && !state.contextDismissed) {
        const notes = node('aside', '', 'jaunt-leg-notes'); notes.setAttribute('aria-label', 'On the way');
        contextLines(notes); notes.append(button('Dismiss road notes', actions.dismissContext)); body.append(notes);
      }
      if (state.phase === 'paused') body.append(button('Resume ride', actions.resumeRide));
      if (state.error) body.append(button('Try this stop again', actions.retry));
    } else {
      if (state.stopIndex === 0) {
        const about = node('details', ''); about.append(node('summary', 'About this outing'), node('p', state.jaunt.opening.text)); body.append(about);
      }
      const historicalClaims = stop.narrative ? stop.evidence.filter(id => state.jaunt.evidence.find(c => c.id === id)?.confidence !== 'reconstructed') : stop.evidence;
      prose(body, stop.text, historicalClaims, historicalClaims?.every(id => state.jaunt.evidence.find(c => c.id === id)?.confidence === 'reconstructed'));
      if (stop.narrative) prose(body, stop.narrative, stop.evidence.filter(id => state.jaunt.evidence.find(c => c.id === id)?.confidence === 'reconstructed'), true);
      if (state.context?.lines.length) {
        const notes = node('details', '', 'jaunt-road-history'); notes.append(node('summary', 'On the way')); contextLines(notes);
        if (state.context.passed.length) notes.append(node('p', `Along this route: ${state.context.passed.map(p => p.label).join(' · ')}`));
        body.append(notes);
      }
      const visit = state.visited[state.stopIndex];
      if (visit.committed) {
        const chosen = stop.choices?.find(c => c.id === visit.choice);
        if (chosen) body.append(node('p', chosen.consequence));
        if (stop.choices?.length) body.append(button('Revise choice', actions.revise));
      } else if (stop.choices?.length) {
        const choices = node('div', '', 'jaunt-choices');
        for (const choice of stop.choices) {
          const status = choiceStatus(state, choice), option = node('div', '', 'jaunt-choice');
          const b = button(choice.label, () => actions.choose(choice.id)); b.dataset.choice = choice.id;
          b.setAttribute('aria-pressed', String(state.choice === choice.id)); b.disabled = !status.available;
          option.append(b, node('small', status.reason || choiceConsequence(state, choice))); choices.append(option);
        }
        body.append(choices, node('p', choicesFor(state).find(c => c.id === state.choice)?.consequence
          || (stop.next ? 'Choose a preference, or continue without one.' : 'Choose an option to continue.')));
      }
      const links = node('div', '', 'jaunt-links');
      for (const link of stop.links || []) {
        const chip = button(link.label, () => actions.detail(link)); chip.dataset.link = `${link.kind}:${link.id}`; links.append(chip);
      }
      body.append(links);
    }
    buttons.prev.disabled = state.stopIndex === 0; buttons.next.disabled = barNext.disabled = !canNext(state);
    const place = destinations.byId(stop.destination.kind, stop.destination.id)?.label || stop.destination.id;
    barLabel.replaceChildren(node('span', `▴ ${['travelling', 'paused'].includes(state.phase) ? 'On the way to ' : ''}${place}`),
      node('small', `Stop ${state.stopIndex + 1} of ${state.jaunt.stops.length}`));
    barLabel.setAttribute('aria-label', `Open the outing panel: ${place}, stop ${state.stopIndex + 1} of ${state.jaunt.stops.length}`);
    if (collapsed && state.phase === 'atStop' && old?.phase === 'travelling') setCollapsed(false, { focus: false });
    const open = overlayOpen() || state.phase === 'detail';
    if (open) setCollapsed(true, { focus: false });
    root.classList.toggle('jaunt-detail', open); body.hidden = open; barNext.hidden = open; barReturn.hidden = !open;
    body.scrollTop = scroll; key = nextKey;
    if (!open) restoreView();
    if (focused && same) [...body.querySelectorAll('[data-choice]')].find(el => el.dataset.choice === focused)?.focus();
    else if (state.phase === 'atStop' && (!same || old?.phase === 'travelling')) heading.focus({ preventScroll: true });
  }
  return { render, get collapsed() { return collapsed; }, collapse: value => setCollapsed(value, { focus: false }),
    destroy() { observer.disconnect(); controlSize.disconnect(); root.remove(); sheet.remove(); document.documentElement.removeAttribute('data-jaunt-active'); document.documentElement.removeAttribute('data-jaunt-collapsed'); document.documentElement.style.removeProperty('--jaunt-nav'); } };
}
