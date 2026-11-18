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
    root.hidden = !v;
    doc.documentElement.toggleAttribute('data-tour', !!v);
    if (!v) { target = null; shownStep = null; return; }
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
  }
  return { paint, place };
}
