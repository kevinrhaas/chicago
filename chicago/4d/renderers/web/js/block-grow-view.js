/**
 * block-grow-view.js — the "Watch a block grow" bar over the town (T-3676).
 *
 * One block, one year at a time: a year slider with previous / play / next, a line of
 * what the year shows, a card for each building whose recorded year arrives, the block's
 * whole roll (each building's year, confidence and source, or "not recorded"), the
 * rules it is read by, and Leave, which restores the 1904 town exactly. Escape leaves
 * too. It draws nothing itself: `scene` (block-grow-scene.js) applies each year.
 * Loaded on first use, with its own stylesheet.
 */
import { t } from './strings/index.js';
import './strings/block-grow.js';
import { yearsOf } from './block-grow.js';

export const PLAY_MS = 650;

function gradeWord(grade) {
  return t(`blockgrow.grade_${grade}`) || String(grade ?? '');
}

/** A note a visitor can read: short, and naming no record id. */
export function readableNote(note) {
  const s = String(note ?? '').trim();
  if (!s || s.length > 220 || /[a-z0-9]+_[a-z0-9_]+/i.test(s) || /\bT-\d{3,}/.test(s)) return '';
  return s;
}

export function mountBlockGrowBar(host, { block, scene, onLeave = () => {}, win = host?.ownerDocument?.defaultView,
  startYear = null } = {}) {
  const doc = host.ownerDocument;
  if (doc.head && !doc.getElementById('block-grow-style')) {
    const css = doc.createElement('link'); css.id = 'block-grow-style'; css.rel = 'stylesheet';
    css.href = new URL('../css/block-grow.css', import.meta.url).href;
    doc.head.append(css);
  }
  const years = yearsOf(block);
  const make = (tag, cls, text) => {
    const el = doc.createElement(tag);
    if (cls) el.className = cls;
    if (text != null) el.textContent = text;
    return el;
  };
  const button = (cls, text, action, label) => {
    const b = make('button', cls, text); b.type = 'button';
    if (label) b.setAttribute('aria-label', label);
    b.addEventListener('click', action); return b;
  };
  const root = make('section', 'block-grow');
  root.setAttribute('role', 'region');
  root.setAttribute('aria-label', t('blockgrow.title'));
  const head = make('div', 'block-grow-head');
  const titles = make('div', 'block-grow-titles');
  const h = make('h2', null, t('blockgrow.title')); h.tabIndex = -1;
  titles.append(h, make('p', 'block-grow-block', block.title));
  const leave = button('block-grow-leave', t('blockgrow.leave'), () => close());
  head.append(titles, leave);

  const controls = make('div', 'block-grow-controls');
  const prev = button('block-grow-step', '‹', () => go(index - 1), t('blockgrow.previous'));
  const play = button('block-grow-play', t('blockgrow.play'), () => (timer ? stop() : start()));
  const next = button('block-grow-step', '›', () => go(index + 1), t('blockgrow.next'));
  const yearOut = make('output', 'block-grow-year');
  yearOut.setAttribute('aria-hidden', 'true');
  controls.append(prev, play, next, yearOut);
  const slider = make('input', 'block-grow-slider');
  slider.type = 'range'; slider.min = '0'; slider.max = String(years.length - 1); slider.step = '1';
  slider.setAttribute('aria-label', t('blockgrow.year'));
  slider.addEventListener('input', () => { stop(); go(Number(slider.value)); });
  const line = make('p', 'block-grow-line');
  line.setAttribute('role', 'status'); line.setAttribute('aria-live', 'polite');
  const cards = make('div', 'block-grow-cards');

  const roll = make('details', 'block-grow-roll');
  roll.append(make('summary', null, t('blockgrow.everyBuilding', { n: block.members.length })));
  const list = make('ul');
  for (const m of block.members) {
    const li = make('li');
    li.append(make('strong', null, m.name));
    if (m.built) {
      li.append(make('span', null, ` · ${t('blockgrow.appears', { value: m.built.value })} · ${gradeWord(m.built.confidence)}`));
      li.append(sourceList(m.built.sources));
    } else {
      const lot = block.lots.find((l) => l.stem === m.stem);
      const outbuilding = lot?.members.some((x) => x.built);
      li.append(make('span', 'block-grow-undated', ` · ${t(outbuilding ? 'blockgrow.outbuilding' : 'blockgrow.undated')}`));
    }
    list.append(li);
  }
  roll.append(list);
  const rules = make('details', 'block-grow-rules');
  rules.append(make('summary', null, t('blockgrow.howTo')));
  for (const k of ['rule1', 'rule2', 'rule3', 'rule4', 'rule5']) rules.append(make('p', null, t(`blockgrow.${k}`)));
  const scroll = make('div', 'block-grow-scroll');
  scroll.append(cards, roll, rules);
  root.append(head, controls, slider, line, scroll);
  host.append(root);

  function sourceList(sources) {
    const wrap = make('span', 'block-grow-sources');
    wrap.append(make('span', 'block-grow-k', `${t(sources.length > 1 ? 'blockgrow.sources' : 'blockgrow.source')}: `));
    sources.forEach((s, i) => {
      if (i) wrap.append('; ');
      const text = s.citation || s.id;
      if (s.url) {
        const a = make('a', null, text); a.href = s.url; a.target = '_blank'; a.rel = 'noopener noreferrer';
        wrap.append(a);
      } else wrap.append(text);
    });
    return wrap;
  }

  function card(row) {
    const c = make('article', 'block-grow-card');
    c.append(make('h3', null, `${row.built.by === state.year ? state.year : row.built.from} · ${row.name}`));
    c.append(make('p', null, row.state === 'ghost'
      ? t('blockgrow.spanStarts', { value: row.built.value, by: row.built.by })
      : t('blockgrow.appears', { value: row.built.value })));
    c.append(make('p', 'block-grow-grade', t('blockgrow.confidence', { grade: gradeWord(row.built.confidence) })));
    const note = readableNote(row.built.note);
    if (note) c.append(make('p', 'block-grow-note', note));
    const p = make('p'); p.append(sourceList(row.built.sources)); c.append(p);
    return c;
  }

  let index = 0, timer = null, state = null, live = true;
  function render() {
    yearOut.textContent = String(state.year);
    slider.value = String(index);
    slider.setAttribute('aria-valuetext', t('blockgrow.yearText', { year: state.year, standing: state.standing.length, ghost: state.ghost.length }));
    prev.disabled = index <= 0; next.disabled = index >= years.length - 1;
    line.textContent = `${state.year} · ${t('blockgrow.summary', { standing: state.standing.length, ghost: state.ghost.length, hidden: state.hidden.length })}`;
    cards.replaceChildren();
    if (state.final) cards.append(make('p', 'block-grow-final', t('blockgrow.finalYear', { undated: block.undated.length })));
    else if (!state.appearing.length) cards.append(make('p', 'block-grow-quiet', t('blockgrow.quiet', { year: state.year })));
    else for (const row of state.appearing) cards.append(card(row));
  }
  function go(i) {
    if (!live) return;
    index = Math.max(0, Math.min(years.length - 1, i));
    state = scene.setYear(years[index]);
    render();
  }
  function start() {
    if (index >= years.length - 1) go(0);
    play.textContent = t('blockgrow.pause'); play.setAttribute('aria-pressed', 'true');
    timer = win.setInterval(() => {
      if (index >= years.length - 1) { stop(); return; }
      go(index + 1);
    }, PLAY_MS);
  }
  function stop() {
    if (timer) win.clearInterval(timer);
    timer = null; play.textContent = t('blockgrow.play'); play.setAttribute('aria-pressed', 'false');
  }
  function close() {
    if (!live) return;
    live = false; stop();
    scene.leave();
    root.remove();
    onLeave();
  }
  root.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(); }
  });

  const at = startYear != null ? years.indexOf(startYear) : 0;
  index = at >= 0 ? at : 0;
  state = scene.enter(block, years[index]);
  render();
  h.focus({ preventScroll: true });
  return {
    root,
    get year() { return state?.year ?? null; },
    get playing() { return !!timer; },
    go: (year) => go(years.indexOf(year)),
    close,
  };
}
