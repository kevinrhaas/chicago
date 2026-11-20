/**
 * The Field Check's face (T-2663, section 11, M10): a card that says which step of how many,
 * the task, the bubble and WAITING FOR INPUT, with Skip always there; and, when a step has
 * a target, a spotlight ring around it with the rest of the screen dimmed to 55 %; and (T-3642) a
 * row of segments, one a step, lit up to the step in hand. The
 * overlay takes no pointer events but its card's, so the visitor acts on the real page.
 * js/tour.js runs the steps; this only paints the view it is handed.
 */
export function createTourOverlay({ doc = globalThis.document, onNext = () => {}, onSkip = () => {} } = {}) {
  const root = doc.getElementById('tour');
  if (!root) return { paint() {}, place() {} };
  const $ = (id) => doc.getElementById(id);
  const hole = root.querySelector('.tour-hole');
  $('tour-next')?.addEventListener('click', () => onNext());
  $('tour-skip')?.addEventListener('click', () => onSkip());
  let target = null;
  let shownStep = null;
  // T-3671 (WCAG 2.4.3, 2.1.2): the card takes focus as the tour starts, and again as a step
  // begins when focus was on nothing or on the card (its Next key hides as a step waits), so a
  // keyboard or screen reader meets each step where it is said. The card is a region, not a
  // dialog: the visitor acts on the page, and walking keys work while it holds focus
  // (controls/keyboard.js READERS). Esc in the card ends the tour, unless a building card is
  // open under it (the Release step asks for Esc); focus then goes back to where it was.
  const card = root.querySelector('.tour-card');
  let returnTo = null, escape = 'end';
  const visible = (el) => !!el?.isConnected && !el.closest?.('[hidden]') && (el.getClientRects?.().length ?? 0) > 0;
  root.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || root.hidden || escape !== 'end') return;
    const popup = doc.getElementById('popup');
    if (popup && !popup.hidden) return;
    e.preventDefault(); e.stopPropagation(); onSkip();
  });

  function place() {
    let el = target ? doc.querySelector(target) : null;
    // T-3642: a key kept in layout while it is hidden (the Interact key fades, so it keeps its
    // box) is not there to ring until it shows.
    if (el && (el.hidden || doc.defaultView?.getComputedStyle?.(el)?.visibility === 'hidden')) el = null;
    const r = el?.getBoundingClientRect?.();
    const shown = !!r && r.width > 0 && r.height > 0;
    root.classList.toggle('has-target', shown);
    if (!hole) return;
    hole.hidden = !shown;
    if (shown) {
      const pad = 6;
      Object.assign(hole.style, { left: `${r.left - pad}px`, top: `${r.top - pad}px`, width: `${r.width + pad * 2}px`, height: `${r.height + pad * 2}px` });
    }
  }

  /** Paint a step's view, or hide everything for null. */
  function paint(v) {
    const was = !root.hidden, focused = doc.activeElement;
    const idle = !focused || focused === doc.body || focused === doc.documentElement;
    const inside = !!focused && root.contains(focused);
    root.hidden = !v;
    doc.documentElement.toggleAttribute('data-tour', !!v);
    if (!v) {
      target = null; shownStep = null;
      if (was && (idle || inside)) { if (visible(returnTo)) returnTo.focus({ preventScroll: true }); else if (inside) focused.blur?.(); }
      returnTo = null;
      return;
    }
    escape = v.escape ?? 'end';
    const fresh = shownStep === null, moved = fresh || v.step !== shownStep;
    if (fresh && !inside && !idle) returnTo = focused;
    target = v.target;
    $('tour-count').textContent = `Field check · ${v.n} / ${v.of}`;
    // T-3642: a segment a step, lit to the one in hand, as the jaunt meter (T-3620); the card
    // gives a short pulse as a step is passed.
    const pips = $('tour-pips');
    if (pips) {
      if (pips.childElementCount !== v.of) pips.replaceChildren(...Array.from({ length: v.of }, () => doc.createElement('i')));
      [...pips.children].forEach((pip, i) => { pip.className = i < v.n - 1 ? 'done' : i === v.n - 1 ? 'now' : ''; });
    }
    if (shownStep !== null && v.step > shownStep) {
      const card = root.querySelector('.tour-card');
      card?.classList.remove('tour-advance'); void card?.offsetWidth; card?.classList.add('tour-advance');
    }
    shownStep = v.step;
    $('tour-task').textContent = `Task · ${v.task}`;
    $('tour-bubble').textContent = v.bubble;
    const status = $('tour-status');
    status.hidden = !v.waiting;
    status.textContent = 'Waiting for input';
    const next = $('tour-next');
    next.hidden = !v.action;
    next.textContent = v.action === 'finish' ? 'Finish' : 'Next';
    place();
    const now = doc.activeElement;
    if (card && moved && (fresh || idle || inside) && !(now && now !== card && root.contains(now) && visible(now))) card.focus({ preventScroll: true });
  }
  return { paint, place };
}
