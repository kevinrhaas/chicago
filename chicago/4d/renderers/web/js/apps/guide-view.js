/**
 * Guide (SCR 09), loaded the first time it opens (T-2661, NAV-803; DESIGN §07 "Guide").
 *
 * The controls sheet, which replaces the control-help popover. It shows the controls the
 * visitor is actually using — touch on a phone (the left thumb walks, the right side
 * looks), keyboard and mouse on a laptop — read from the one switch that knows,
 * js/controls/intent.js (`ctx.controls`, `ctx.coarse`), and follows it when it changes:
 * a laptop with a touch screen that is tapped turns the sheet to touch. The other sheet
 * is one tap away, for a visitor who wants to read it. Tour mode, the glossary and
 * "Is this real?" join this screen with their own tickets (NAV-801, NAV-804).
 */
import { CONTROL_SHEETS, SCHEMES } from '../controls/sheet.js';
import { controlScheme } from '../controls/intent.js';

const state = { scheme: null, chosen: false, off: null };

function render(el) {
  const doc = el.ownerDocument;
  const node = (tag, cls, text) => {
    const n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };
  const sheet = CONTROL_SHEETS[state.scheme];
  const block = node('section', 'nav-block nav-guide');
  block.id = 'guide-controls';
  block.dataset.scheme = state.scheme;
  const k = node('span', 'nav-k nav-k-row');
  k.append(node('span', null, 'Guide'), ' ',
    node('span', 'nav-step', state.chosen ? 'Your choice' : 'On this device'));
  const title = node('strong', 'nav-place', 'The controls');
  const seg = node('div', 'seg nav-guide-seg');
  seg.id = 'guide-scheme';
  seg.setAttribute('role', 'radiogroup');
  seg.setAttribute('aria-label', 'Controls for');
  for (const id of SCHEMES) {
    const b = node('button', 'seg-btn', CONTROL_SHEETS[id].title);
    b.type = 'button';
    b.dataset.scheme = id;
    b.setAttribute('role', 'radio');
    b.setAttribute('aria-checked', String(id === state.scheme));
    b.classList.toggle('is-on', id === state.scheme);
    b.addEventListener('click', () => {
      if (state.scheme === id) return;
      state.scheme = id;
      state.chosen = true;
      render(el);
    });
    seg.append(b);
  }
  const intro = node('p', 'nav-sub', sheet.intro);
  const list = node('dl', 'keys nav-guide-keys');
  list.dataset.scheme = state.scheme;
  for (const [keys, does] of sheet.rows) {
    const dt = node('dt');
    keys.forEach((key, i) => {
      if (i) dt.append(' ');
      // Keyboard keys are keys; a touch gesture is words.
      dt.append(state.scheme === 'keyboard' ? node('kbd', null, key) : node('span', null, key));
    });
    list.append(dt, ' ', node('dd', null, does), ' ');
  }
  block.append(k, ' ', title, ' ', seg, ' ', intro, ' ', list);
  el.replaceChildren(block);
}

export function mount(el, ctx = {}) {
  state.scheme = controlScheme(ctx.controls, ctx.coarse);
  state.chosen = false;
  render(el);
  state.off?.();
  // Follow the live controls until the visitor picks a sheet themselves.
  state.off = ctx.actions?.onControls?.((name) => {
    const next = controlScheme(name, ctx.coarse);
    if (state.chosen || next === state.scheme) return;
    state.scheme = next;
    render(el);
  }) ?? null;
}

/** Each time Guide opens: the sheet for the controls in use, unless one was picked. */
export function shown(el, ctx = {}) {
  if (state.chosen) return;
  const next = controlScheme(ctx.controls, ctx.coarse);
  if (next !== state.scheme) { state.scheme = next; render(el); }
}

export function unmount(el) {
  state.off?.();
  state.off = null;
  el.replaceChildren();
}
