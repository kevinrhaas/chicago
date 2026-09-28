import { currentStop, choicesFor, canNext } from './jaunts.js';

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
  root.append(body, controls); document.body.append(root);
  root.addEventListener('keydown', e => e.stopPropagation());
  let state, key;
  const overlayOpen = () => ['popup', 'panel'].some(id => { const el = document.getElementById(id); return el && !el.hidden; });
  const syncOverlay = () => {
    const open = overlayOpen(); root.classList.toggle('jaunt-detail', open); body.hidden = open;
    if (!open && state?.phase === 'detail') actions.returnFromDetail();
  };
  const observer = new MutationObserver(syncOverlay);
  for (const id of ['popup', 'panel']) {
    const el = document.getElementById(id);
    if (el) observer.observe(el, { attributes: true, attributeFilter: ['hidden'] });
  }
  function render(next) {
    const old = state; state = next;
    const active = !!state.jaunt && !['menu', 'outcome'].includes(state.phase);
    root.hidden = !active; document.documentElement.toggleAttribute('data-jaunt-active', active);
    if (!active) { key = null; return; }
    const stop = currentStop(state), nextKey = `${state.session}:${stop.id}`, same = key === nextKey;
    const scroll = same ? body.scrollTop : 0, focused = document.activeElement?.dataset.choice;
    const heading = node('h2', destinations.byId(stop.destination.kind, stop.destination.id)?.label || stop.destination.id);
    heading.tabIndex = -1;
    const progress = node('p', `${state.jaunt.title} · Stop ${state.stopIndex + 1} of ${state.jaunt.stops.length}`, 'jaunt-progress');
    progress.setAttribute('aria-live', 'polite'); body.replaceChildren(progress, heading);
    if (state.phase === 'travelling') {
      body.append(node('p', state.error || 'On the way to the next stop…'));
      if (state.error) body.append(button('Try this stop again', actions.retry));
    } else {
      if (state.stopIndex === 0) {
        const about = node('details', ''); about.append(node('summary', 'About this outing'), node('p', state.jaunt.opening.text)); body.append(about);
      }
      body.append(node('p', stop.text));
      const visit = state.visited[state.stopIndex];
      if (visit.committed) {
        const chosen = stop.choices?.find(c => c.id === visit.choice);
        if (chosen) body.append(node('p', chosen.consequence));
      } else if (stop.choices?.length) {
        const choices = node('div', '', 'jaunt-choices');
        for (const choice of choicesFor(state)) {
          const b = button(choice.label, () => actions.choose(choice.id)); b.dataset.choice = choice.id;
          b.setAttribute('aria-pressed', String(state.choice === choice.id)); choices.append(b);
        }
        body.append(choices, node('p', choicesFor(state).find(c => c.id === state.choice)?.consequence
          || (stop.next ? 'Choose a preference, or continue without one.' : 'Choose an option to continue.')));
      }
      for (const link of stop.links || []) body.append(button(link.label, () => actions.detail(link)));
    }
    buttons.prev.disabled = state.stopIndex === 0; buttons.next.disabled = !canNext(state);
    const open = overlayOpen(); root.classList.toggle('jaunt-detail', open); body.hidden = open;
    body.scrollTop = scroll; key = nextKey;
    if (focused && same) [...body.querySelectorAll('[data-choice]')].find(el => el.dataset.choice === focused)?.focus();
    else if (state.phase === 'atStop' && (!same || old?.phase === 'travelling')) heading.focus({ preventScroll: true });
  }
  return { render, destroy() { observer.disconnect(); root.remove(); sheet.remove(); document.documentElement.removeAttribute('data-jaunt-active'); } };
}
