import { currentStop, choicesFor, canNext, choiceStatus, choiceConsequence, resourceSummary, shownMode, isFinalStop, openingLight, routeCount, routeStops } from './jaunts.js';
import { claimPresentation } from './jaunt-context.js';
import { PACES } from './travel-settings.js';
import { formatEstimate } from './travel-estimate.js';
import { groupIcon, groupOf, groupSlot, icon } from './menu-icons.js';
import { ambienceLabel } from './jaunt-menu.js';
import { clockText } from './jaunt-pace.js';
import { readingTabs, forgetAge, levelOfGrade, WRITTEN } from './reading-level.js';
import { narrationScripts } from './narration.js';

/** T-3432: a jaunt's opening, in paragraphs, without the "JAUNT: ITS TITLE." its welcome
 *  already shows as a heading. */
export function openingParagraphs(jaunt) {
  const paragraphs = String(jaunt?.opening?.text ?? '').split(/\n\s*\n/).map(t => t.trim()).filter(Boolean);
  if (paragraphs.length) paragraphs[0] = paragraphs[0].replace(/^(?:JAUNT|PASEO):\s*[^.!?]*[.!?]\s*/, '');
  return paragraphs.filter(Boolean);
}
/** T-3432: road notes are read in the leg they belong to, or not at all: the lines of
 *  `lines`, in order, that a visitor can read (about 3 words a second, after a second to
 *  look up) before a leg of `seconds` ends. Unknown time keeps every line. */
export const READ_WORDS_PER_S = 3;
export function readableLines(lines = [], seconds) {
  if (!Number.isFinite(seconds)) return lines;
  let left = seconds - 1.5;
  const kept = [];
  for (const line of lines) {
    const need = String(line.text ?? '').split(/\s+/).filter(Boolean).length / READ_WORDS_PER_S + 0.5;
    if (need > left) break;
    kept.push(line); left -= need;
  }
  return kept;
}
/** T-3671 (WCAG 1.2.1): words compared as words, for whether a card shows what its voice says. */
export const sameWords = (a, b) => {
  const norm = t => String(t ?? '').toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
  return norm(a) === norm(b);
};
/** T-3671: the words a voiced part of a jaunt says (narration.js narrationScripts), or ''. */
export const scriptFor = (jaunt, part, id) => narrationScripts(jaunt).find(s => s.part === part && s.id === id)?.text ?? '';
/** T-3671: the polite status line's words for where an outing is now, and the key that says it once. */
export function outingNews(state, place = '', where = '') {
  const s = state?.session, j = state?.jaunt;
  where = where.replace(/ · /g, ', ');
  if (!j) return null;
  if (state.phase === 'opening') return { key: `${s}:opening`, text: `Jaunt started: ${j.title}. Flying to the start, ${place}.` };
  if (state.phase === 'travelling') return { key: `${s}:${state.leg}:way`, text: `On the way to ${place}, ${where.toLowerCase()}.` };
  if (state.phase === 'paused') return { key: `${s}:${state.leg}:paused`, text: 'Ride paused.' };
  if (state.phase === 'atStop') return { key: `${s}:${state.leg}:at`, text: `Arrived at ${place}. ${where}.`,
    waiting: state.hostWaiting ? { key: `${s}:${state.leg}:waiting`, text: 'Your guide is approaching.' } : null };
  if (state.phase === 'closing') return { key: `${s}:closing`, text: `Closing: ${j.title}.` };
  if (state.phase === 'outcome' && state.outcome) return { key: `${s}:outcome`, text: `${state.outcome.fallback ? 'Outing interrupted' : 'Outing complete'}: ${j.title}.` };
  return null;
}
const pauseIcon = size => {
  const t = document.createElement('template');
  t.innerHTML = `<svg class="menu-icon" viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 6.5v11M15 6.5v11"/></svg>`;
  return t.content.firstChild;
};

/** The scrollable story and persistent controls have separate layout ownership. */
export function createJauntPanel({ destinations, actions, catalogRow = () => null, narration = null, tellings = () => [] }) {
  // T-2946: a stop is headed by the jaunt's own name for it, the one its road notes use.
  const stopName = (state, stop) => state.jaunt.places?.[stop.destination.id]
    || destinations.byId(stop.destination.kind, stop.destination.id)?.label || stop.destination.id;
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
  // T-3629 (the owner's interface sweep): one big Next stop, and small keys with an icon and a
  // short word for the rest, in a game's order: Back · Jaunts · End · Next stop. Each keeps
  // its full name for a screen reader.
  // T-3753: and Stops, the jaunt's stops in a list, any one of them a tap away.
  for (const [id, label, name, glyph] of [['prev', 'Back', 'Previous stop', 'back'], ['stops', 'Stops', 'All stops', 'stops'],
    ['menu', 'Jaunts', 'Jaunts menu', 'jaunts'], ['end', 'End', 'End jaunt', 'close'], ['next', 'Next stop', null, null]]) {
    buttons[id] = button(label, () => { if (['prev', 'next', 'stops'].includes(id)) pressed = id;
      return id === 'next' ? goNext() : id === 'stops' ? toggleStops() : actions[id](); });
    buttons[id].dataset.action = id;
    if (glyph) { buttons[id].prepend(icon(glyph, 16)); buttons[id].classList.add('jaunt-key'); }
    if (name) { buttons[id].setAttribute('aria-label', name); buttons[id].title = name; }
    controls.append(buttons[id]);
  }
  buttons.next.classList.add('jaunt-primary');
  const mode = node('select', '', 'jaunt-pace'); mode.setAttribute('aria-label', 'Jaunt travel mode');
  mode.addEventListener('change', () => actions.setMode(mode.value));
  const straight = button('Skip the ride', actions.straight); straight.dataset.action = 'straight';
  straight.setAttribute('aria-label', 'Go straight to next stop'); straight.title = 'Go straight to next stop';
  straight.className = 'jaunt-straight';
  controls.prepend(mode, straight);
  // T-3671 (WCAG 1.4.2): while a voice of this outing speaks, Pause on the controls and on the
  // collapsed bar holds it, and Resume lets it go on, whatever card or phase is up. Settings ›
  // Sound's Narration level (and the Navigator's mute keys) set its volume apart from the rest.
  const voiceKeys = [false, true].map(onBar => {
    const b = button('', () => { if (narration?.paused) narration.resume(); else narration?.pause?.(); });
    b.dataset.action = onBar ? 'bar-voice' : 'voice'; b.className = onBar ? 'jaunt-voice' : 'jaunt-key jaunt-voice'; b.hidden = true;
    return b;
  });
  straight.after(voiceKeys[0]);
  function paintVoice() {
    const on = !!state?.jaunt && !!narration?.speaking?.(state.jaunt), held = on && !!narration.paused;
    voiceKeys.forEach((b, i) => {
      b.hidden = !on;
      if (!on) return;
      const name = held ? 'Resume narration' : 'Pause narration';
      b.replaceChildren(held ? icon('play', 16) : pauseIcon(16), ...(i === 0 ? [node('span', held ? 'Resume' : 'Pause')] : []));
      if (b.getAttribute('aria-label') !== name) { b.setAttribute('aria-label', name); b.title = name; }
    });
    voiceKeys[0].classList.toggle('jaunt-voice-wide', mode.hidden);
    mode.classList.toggle('jaunt-mode-wide', straight.hidden && voiceKeys[0].hidden);
  }
  // Collapsing folds the panel to one bar — where you are, Next Stop, and a tap to
  // open it again — so the world can be looked at from a stop on a phone, where the
  // open panel covers most of the screen. Arriving at a new stop opens it again.
  let collapsed = false;
  const collapse = button('▾', () => setCollapsed(true)); collapse.className = 'jaunt-collapse';
  collapse.setAttribute('aria-label', 'Collapse the outing panel'); collapse.setAttribute('aria-expanded', 'true');
  const bar = node('div', '', 'jaunt-bar'), barLabel = button('', () => setCollapsed(false));
  barLabel.className = 'jaunt-bar-label'; barLabel.setAttribute('aria-expanded', 'false');
  const barNext = button('Next stop', () => { pressed = 'next'; goNext(); }); barNext.dataset.action = 'bar-next'; barNext.classList.add('jaunt-primary');
  const barReturn = button('Return', () => { if (state?.phase === 'detail') actions.returnFromDetail(); else actions.closeOverlay(); }); barReturn.hidden = true; barReturn.dataset.action = 'return';
  const barEnd = button('End', actions.end); barEnd.setAttribute('aria-label', 'End Jaunt');
  bar.append(barLabel, voiceKeys[1], barNext, barReturn, barEnd);
  // The owner, 2026-11-16: a quiet meter of the jaunt, one hairline segment a stop, the
  // stop under way filling as its scene plays (and, fainter, as the way to it is covered),
  // with the scene's time left beside it. On the controls, and along the collapsed bar.
  const meters = [makeMeter(true), makeMeter(false)];
  controls.prepend(meters[0].el); bar.prepend(meters[1].el);
  // T-3671 (WCAG 4.1.3): one polite status line for where the outing is (started, on the way,
  // arrived, closing, complete). It stands outside the panel, which is hidden between outings,
  // so it is in the page before anything is said in it; each news is said once a session.
  const status = node('div', '', 'jaunt-status'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  status.dataset.jauntStatus = '';
  let toldKeys = new Set(), toldSession = null;
  function tell(news) {
    if (!news || !state) return;
    if (toldSession !== state.session) { toldSession = state.session; toldKeys = new Set(); }
    const parts = [news, news.waiting].filter(n => n && !toldKeys.has(n.key));
    if (!parts.length) return;
    for (const n of parts) toldKeys.add(n.key);
    status.textContent = parts.map(n => n.text).join(' ');
  }
  // T-3671 (WCAG 1.2.1): the words on a voiced card are the words its voice says (narration.js
  // keys each clip to them; tools/narrate_jaunts.mjs holds a performance's words to the
  // script's), so the card is its own transcript, lit while it is read. Where the card shows
  // other words (a reading-age tab on another telling), a Transcript fold beside Listen gives
  // the words the voice reads.
  // T-3735 (the owner, 2026-11-23: "if they are on 11-13 ... and you do not have narration for
  // that then don't play that other wrong narration"; "when you switch tabs to an age that has
  // its own recording, it should start playing that recording"): a reading-age tab that puts
  // another telling's words on the opening or a stop is read in THAT telling's voice
  // (narration.js `retell`): a voice reading the old words stops and the new one starts, and
  // where that telling has no recording the part has none (no Listen, nothing plays). Words no
  // telling of this jaunt says, as shown, have no voice either.
  const voiceNote = node('span', 'Read aloud in a synthetic voice: the words on this card.', 'jaunt-status'); voiceNote.id = 'jaunt-voice-card';
  const voiceNoteOther = node('span', 'Read aloud in a synthetic voice: the words in its Transcript.', 'jaunt-status'); voiceNoteOther.id = 'jaunt-voice-transcript';
  let voiced = [], shownParts = [];
  const shownWords = p => p.els.map(el => el.textContent).join(' ');
  /** T-3735: whose words a part shows now: null, its own (as drawn); { jaunt, part, id }, the
   *  telling for the age tab picked; false, words no telling of this jaunt says as shown. */
  function sourceOf(p) {
    const shown = shownWords(p);
    if (sameWords(shown, p.first)) return null;
    const age = body.dataset.readingAge, own = levelOfGrade(state.jaunt?.grade_band) || WRITTEN;
    const telling = age && age !== own ? (tellings(state.jaunt) ?? []).find(t => t?.audience !== 'adults' && (levelOfGrade(t.grade_band) || WRITTEN) === age) : null;
    const at = p.part === 'opening' ? 'opening' : telling?.stops?.[state.jaunt.stops.findIndex(s => s.id === p.id)]?.id;
    if (!telling || !at) return false;
    return sameWords(shown, scriptFor(telling, p.part, at)) ? { jaunt: telling, part: p.part, id: at } : false;
  }
  /** T-3735: each part on the card is voiced by the telling whose words it shows. */
  function retellShown() {
    for (const p of shownParts) if (p.els[0]?.isConnected) void narration?.retell?.(state.jaunt, p.part, p.id, sourceOf(p));
  }
  function transcript(part, id, els, hear) {
    const own = scriptFor(state.jaunt, part, id);
    if (!own) return;
    const first = els.map(el => el.textContent).join(' ');   // the card's words as drawn, before any age tab
    if (part !== 'ending') shownParts.push({ part, id, els, first });
    if (!hear) return;
    const fold = node('details', '', 'jaunt-transcript'); fold.dataset.readingSkip = ''; fold.dataset.transcript = `${part}:${id}`; fold.hidden = true;
    hear.after(fold);
    const on = narration.isPlaying(state.jaunt, part, id);
    for (const el of els) { el.dataset.voiced = part; el.classList.toggle('jaunt-voicing', on); }
    voiced.push({ els, fold, script: null, own, hear, part, id, first });
  }
  function syncTranscripts() {
    retellShown();
    for (const v of voiced) {
      if (!v.fold.isConnected) continue;
      const from = v.part === 'ending' ? null : sourceOf(v);
      const script = from ? scriptFor(from.jaunt, from.part, from.id) : v.own;   // the words its voice reads
      if (script !== v.script) {
        v.script = script;
        v.fold.replaceChildren(node('summary', 'Transcript'), node('p', 'The voice reads the words as first written:', 'jaunt-transcript-note'),
          ...script.split(/\n\s*\n/).map(t => node('p', t.trim())));
      }
      const same = sameWords(shownWords(v), script), away = from === false;
      v.hear.hidden = away;
      v.fold.hidden = same || away; if (v.fold.hidden) v.fold.open = false;
      v.hear.setAttribute('aria-describedby', same ? voiceNote.id : voiceNoteOther.id);
    }
  }
  let syncing = false;
  const swaps = new MutationObserver(() => { if (syncing) return; syncing = true; queueMicrotask(() => { syncing = false; syncTranscripts(); }); });
  swaps.observe(body, { characterData: true, subtree: true });
  /**
   * T-3753 (the owner, 2026-11-26: "Allow users to jump directly to a specific stop within a
   * jaunt rather than only progressing sequentially"): Stops opens the route's stops in place of
   * the story, numbered, the one you are at marked; a tap goes straight there (jaunts.js JUMP),
   * back or ahead. Where a choice decides the way on, the list ends at it and says so.
   */
  const stopsSheet = node('section', '', 'jaunt-stop-sheet'); stopsSheet.id = 'jaunt-stops'; stopsSheet.hidden = true;
  stopsSheet.setAttribute('aria-label', 'Stops on this jaunt');
  buttons.stops.setAttribute('aria-controls', stopsSheet.id); buttons.stops.setAttribute('aria-expanded', 'false');
  let stopsOpen = false;
  function setStops(value, { focus = true } = {}) {
    value = !!value && !!state?.jaunt && state.phase !== 'closing';
    if (stopsOpen === value) return;
    stopsOpen = value; stopsSheet.hidden = !value; root.classList.toggle('jaunt-stops-open', value);
    buttons.stops.setAttribute('aria-expanded', String(value));
    if (value) { paintStops(); if (focus) stopsSheet.querySelector('[aria-current]')?.focus({ preventScroll: false }); }
    else if (focus) buttons.stops.focus({ preventScroll: true });
  }
  function toggleStops() { setCollapsed(false, { focus: false }); setStops(!stopsOpen); }
  function paintStops() {
    if (!stopsOpen || !state?.jaunt) return;
    const { stops, open } = routeStops(state), count = state.jaunt.stops.length;
    const had = stopsSheet.contains(document.activeElement) ? document.activeElement : null;
    const keep = had?.dataset.stop ?? (had?.classList.contains('jaunt-stops-close') ? 'close' : null);
    const head = node('div', '', 'jaunt-stops-head');
    const title = node('h3', 'Stops'); title.append(node('small', ` · ${state.jaunt.title}`));
    const shut = button('', () => setStops(false)); shut.className = 'jaunt-stops-close';
    shut.setAttribute('aria-label', 'Close the stops list'); shut.title = 'Close the stops list'; shut.append(icon('close', 16));
    head.append(title, shut);
    const list = node('ol', '', 'jaunt-stops-list');
    for (const row of stops) {
      const stop = state.jaunt.stops.find(x => x.id === row.id); if (!stop) continue;
      const item = node('li', ''), b = button('', () => {
        setStops(false, { focus: false }); pressed = 'stops';
        if (row.state === 'here') return buttons.stops.focus({ preventScroll: true });
        actions.jump?.(row.id);
        buttons.stops.focus({ preventScroll: true });
      });
      b.className = `jaunt-stop-row jaunt-stop-${row.state}`; b.dataset.stop = row.id;
      const name = stopName(state, stop), said = row.state === 'here' ? 'You are here' : row.state === 'seen' ? 'Visited' : '';
      b.append(node('span', String(row.index + 1), 'jaunt-stop-n'), node('span', name, 'jaunt-stop-name'));
      if (said) b.append(node('small', row.state === 'here' ? 'Here' : 'Seen', 'jaunt-stop-said'));
      b.setAttribute('aria-label', `Stop ${row.index + 1}: ${name}${said ? `, ${said.toLowerCase()}` : ''}`);
      if (row.state === 'here') b.setAttribute('aria-current', 'step');
      item.append(b); list.append(item);
    }
    stopsSheet.replaceChildren(head, list);
    if (open) stopsSheet.append(node('p', 'Your choice at this stop decides the way on.', 'jaunt-stops-note'));
    else if (stops.length < count) stopsSheet.append(node('p', `${stops.length} of the jaunt's ${count} stops are on your way.`, 'jaunt-stops-note'));
    // A repaint (the visitor arriving, a voice starting) keeps focus where it was in the list.
    if (keep) (keep === 'close' ? shut : [...list.querySelectorAll('[data-stop]')].find(el => el.dataset.stop === keep) ?? shut).focus({ preventScroll: true });
  }
  stopsSheet.addEventListener('keydown', e => {
    if (e.key === 'Escape') { e.preventDefault(); setStops(false); return; }
    if (!['ArrowDown', 'ArrowUp'].includes(e.key)) return;
    const rows = [...stopsSheet.querySelectorAll('.jaunt-stop-row')], at = rows.indexOf(document.activeElement);
    if (at < 0) return;
    e.preventDefault(); rows[Math.max(0, Math.min(rows.length - 1, at + (e.key === 'ArrowDown' ? 1 : -1)))].focus();
  });
  /**
   * T-3753 (the owner, 2026-11-26: "Display a spinner or loading indicator on the play and
   * navigation buttons while a jaunt or scene is loading"): while the scene at the stop is still
   * coming (its people's figures loading, the guide on the way), the key that moved the visitor
   * there (Next stop, Back or Stops; Next stop when they walked in) spins a small ring, and the
   * Listen key does while its voice is still arriving. Never for longer than LOADING_CAP_MS a
   * stop, so a figure that never comes does not leave a key spinning for ever.
   */
  const LOADING_CAP_MS = 20000;
  let pressed = null, loadKey = null, loadSince = 0, loadingOn = false;
  function loading(m) {
    const now = performance.now(), k = state?.jaunt ? `${state.session}:${state.stopIndex}:${state.phase}` : null;
    if (k !== loadKey) { loadKey = k; loadSince = now; }
    const busy = !!m?.scene && now - loadSince < LOADING_CAP_MS;
    const on = busy ? (pressed === 'prev' ? [buttons.prev] : pressed === 'stops' ? [buttons.stops] : [buttons.next, barNext]) : [];
    for (const b of [buttons.prev, buttons.stops, buttons.next, barNext]) {
      const spin = on.includes(b);
      if (b.classList.contains('jaunt-loading') !== spin) { b.classList.toggle('jaunt-loading', spin); b.toggleAttribute('aria-busy', spin); }
    }
    if (busy !== loadingOn) { loadingOn = busy; root.toggleAttribute('aria-busy', busy); if (!busy && state?.phase === 'atStop') pressed = null; }
    for (const b of body.querySelectorAll('[data-action="listen"]')) {
      const spin = !!m?.voice && b.getAttribute('aria-pressed') === 'true';
      if (b.classList.contains('jaunt-loading') !== spin) { b.classList.toggle('jaunt-loading', spin); b.toggleAttribute('aria-busy', spin); }
    }
  }
  // T-3671 (WCAG 2.2.1): the closing scene goes on to Outing complete by itself; a visitor who
  // touches, scrolls or keys in the panel while it is up holds it there until Finish jaunt.
  let engaged = false;
  for (const type of ['pointerdown', 'keydown', 'wheel', 'touchstart']) root.addEventListener(type, () => { if (root.classList.contains('jaunt-closing')) engaged = true; }, { passive: true });
  root.append(collapse, body, stopsSheet, controls, bar, voiceNote, voiceNoteOther); document.body.append(root, status);
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
    if (value) setStops(false, { focus: false });
    document.documentElement.toggleAttribute('data-jaunt-collapsed', value);
    measureNav();
    if (focus) (value ? barLabel : collapse).focus({ preventScroll: true });
  }
  function makeMeter(withClock) {
    const el = node('div', '', 'jaunt-meter'), track = node('span', '', 'jaunt-meter-stops'), clock = withClock ? node('span', '', 'jaunt-meter-clock') : null;
    el.setAttribute('role', 'progressbar'); el.setAttribute('aria-label', 'Jaunt progress');
    el.setAttribute('aria-valuemin', '0'); el.setAttribute('aria-valuemax', '100'); el.hidden = true;
    el.append(track); if (clock) { clock.setAttribute('aria-hidden', 'true'); el.append(clock); }
    let segs = [], shown = '';
    function set(m) {
      el.hidden = !m; if (!m) return;
      if (segs.length !== m.count) {
        segs = Array.from({ length: m.count }, () => { const seg = node('i'), fill = node('b'); seg.append(fill); return { seg, fill }; });
        track.replaceChildren(...segs.map(x => x.seg));
      }
      segs.forEach(({ seg, fill }, i) => {
        const v = i < m.index ? 1 : i > m.index ? 0 : m.value;
        fill.style.transform = `scaleX(${v.toFixed(4)})`;
        seg.classList.toggle('jaunt-meter-now', i === m.index); seg.classList.toggle('jaunt-meter-way', i === m.index && m.kind === 'way');
      });
      const pct = String(Math.round(m.overall * 100)), said = `Stop ${m.index + 1} of ${m.count}, ${pct} percent of the jaunt`;
      if (said !== shown) { shown = said; el.setAttribute('aria-valuenow', pct); el.setAttribute('aria-valuetext', said); }
      if (clock) { const t = clockText(m.left); clock.textContent = t; clock.title = t ? (m.kind === 'way' ? 'Time to the stop' : 'Time left in this scene') : ''; }
    }
    return { el, set };
  }
  root.addEventListener('keydown', e => e.stopPropagation());
  let state, key, overlayView = null, needsChoice = false;
  // T-3578: a voiced part shows Listen; the voice repaints the panel as it starts and stops.
  // T-3671: on the next microtask, not inside a render that started the voice (a nested
  // repaint replaced the stop's heading as it took focus, and focus fell to the page).
  let repaint = false;
  const offNarration = narration?.on?.(() => {
    if (!state?.jaunt || repaint) return;
    repaint = true; queueMicrotask(() => { repaint = false; if (state?.jaunt) render(state); });
  });
  function listen(part, id) {
    if (!narration?.clip(state.jaunt, part, id)) return null;
    const on = narration.isPlaying(state.jaunt, part, id);
    const b = button('', () => { void narration.toggle(state.jaunt, part, id); });
    b.className = 'jaunt-listen'; b.dataset.action = 'listen';
    b.setAttribute('aria-pressed', String(on));
    b.append(icon(on ? 'stop' : 'listen', 15), node('span', on ? 'Stop' : 'Listen'));
    b.title = on ? 'Stop the narration' : 'Listen: read aloud in a synthetic voice';
    return b;
  }
  // T-2114: a stop that asks for a choice used to grey out Next Stop with the options
  // below the fold on a phone, so the outing read as stuck. Next Stop now says so and,
  // tapped, opens the panel and brings the first open option into view.
  function goNext() {
    // The flight to the start, read to by the opening, may be skipped; the closing finished.
    if (state?.phase === 'opening') return actions.skip?.();
    if (state?.phase === 'closing') return actions.finish?.();
    if (!needsChoice) return actions.next();
    setCollapsed(false, { focus: false });
    const first = body.querySelector('[data-choice]:not(:disabled)');
    first?.closest('.jaunt-choices')?.scrollIntoView({ block: 'nearest' });
    first?.focus({ preventScroll: true });
  }
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
    if (open && state?.jaunt) { saveView(); setCollapsed(true, { focus: false }); setStops(false, { focus: false }); }
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
  function prose(parent, text, ids = [], narrative = false, carried = [], since = '') {
    const claims = [...ids.map(id => state.jaunt.evidence.find(c => c.id === id)), ...carried];
    const unsafe = claims.some(c => claimPresentation(c).text === 'Unverified attribution withheld.');
    const paragraph = node('p', unsafe ? 'Unverified attribution withheld.' : text, narrative ? 'jaunt-narrative' : '');
    // T-3406: a story stop opens on how long since the one before ("Four hours later."),
    // ahead of the date and hour its text starts with.
    if (since && !unsafe) paragraph.prepend(node('strong', `${since}.`, 'jaunt-since'), ' ');
    paragraph.title = paragraph.textContent; parent.append(paragraph);
    if (unsafe) paragraph.dataset.withheld = '';
    if (!claims.length) return paragraph;
    // T-2120: the sourcing folds behind one quiet toggle per passage instead of a row of
    // [DOC]/[INF]/[CONJ] chips under the story; every claim and source is one tap away.
    const chips = node('div', '', 'jaunt-evidence'); chips.hidden = true;
    const toggle = button(`Sources · ${claims.length}`, () => {
      chips.hidden = !chips.hidden; toggle.setAttribute('aria-expanded', String(!chips.hidden));
    });
    toggle.className = 'jaunt-sources-toggle'; toggle.setAttribute('aria-expanded', 'false');
    parent.append(toggle);
    for (const claim of claims) {
      const presentation = claimPresentation(claim), fold = node('details', '', presentation.narrative ? 'jaunt-narrative' : '');
      // T-2825: the claim is introduced by its grade's label, never by its record id.
      fold.append(node('summary', `${presentation.label} Sources`), node('p', presentation.text));
      if (presentation.narrative) fold.append(node('small', 'Invented connective narrative; not a historical quotation.'));
      for (const id of claim?.sources || []) fold.append(button('Read source', () => actions.detail({ kind: 'source', id, label: 'Source' })));
      chips.append(fold);
    }
    parent.append(chips);
    return paragraph;
  }
  function contextLines(parent, lines = state.context?.lines || []) {
    for (const line of lines) {
      if (line.generated) parent.append(node('p', line.text));
      else if (line.claims) prose(parent, line.text, [], false, line.claims);
      else prose(parent, line.text, line.evidence, line.evidence?.every(id => state.jaunt.evidence.find(c => c.id === id)?.confidence === 'reconstructed'));
    }
    // T-3379: the owner found T-2956's "[MAP] From the model's map" line unnecessary; a
    // passing note now names the house and, where one is known, gives its sourced fact.
  }
  /**
   * T-3432 (owner, 2026-11-06: "for the first page of the jaunt make it a little more of a
   * welcome and background on the jaunt ... and make those screens nice and with icons"): the
   * first page opens on the jaunt itself — its kind, title and premise, what it takes, and its
   * opening told in full — and stop 1 follows. It is up while the eye flies to the start. Back
   * at stop 1 later in the outing, the opening folds away.
   */
  function welcome(opening) {
    // T-3584: the welcome names the jaunt's menu group, as its card does.
    const row = catalogRow(state.jaunt.id) || {}, family = groupOf(row);
    const hero = node('header', '', `jaunt-welcome jaunt-type-${groupSlot(family)}`);
    const badge = node('span', '', 'jaunt-welcome-badge'); badge.append(icon(family ? groupIcon(family) : 'jaunts', 26));
    const words = node('div', '', 'jaunt-welcome-words');
    words.append(node('p', `Jaunt · ${state.jaunt.scene}${family ? ` · ${family}` : ''}`, 'jaunt-welcome-k'), node('h2', state.jaunt.title, 'jaunt-welcome-title'));
    hero.append(badge, words); body.append(hero);
    // The owner, 2026-11-16: the first card drops the summary (the premise, which nobody reads
    // aloud) and heads the opening with the jaunt's name, as the narrator says it.
    const facts = node('ul', '', 'jaunt-welcome-facts'); facts.setAttribute('aria-label', 'This jaunt');
    const fact = (name, text) => { if (!text) return null; const li = node('li', ''); li.append(icon(name, 16), node('span', text)); facts.append(li); return li; };
    fact('start', `${routeCount(state)} stops`);
    // The time it takes, as the remaining-time line gives it at every later stop.
    const time = state.estimate && fact('clock', formatEstimate(state.estimate).replace(/^about /, '~'));
    if (time) { time.dataset.jauntRemaining = ''; time.title = `${formatEstimate(state.estimate)} remaining`; }
    // T-3459: the light its first scene is shown in (a dated stop's own season).
    const ambience = openingLight(state.jaunt) || row.ambience;
    if (ambience) fact(['dusk', 'night'].includes(ambience.hour) ? 'night' : 'day', ambienceLabel(ambience));
    const mode = shownMode(state);
    if (PACES[mode]) fact(mode, PACES[mode].label);
    body.append(facts);
    const paragraphs = openingParagraphs(state.jaunt);
    if (!paragraphs.length) return;
    const fresh = opening || state.visited.length === 1;
    const story = node(fresh ? 'section' : 'details', '', 'jaunt-welcome-story');
    const named = node('span', state.jaunt.title);
    const head = node(fresh ? 'h3' : 'summary', '', 'jaunt-welcome-story-k'); head.append(icon('story', 16), named);
    story.append(head);
    const hear = listen('opening', 'opening'); if (hear) story.append(hear);
    const told = paragraphs.map(text => node('p', text));
    story.append(...told);
    // Gap analysis item 15: a translated jaunt says once that its quotations are translated.
    if (state.jaunt.quotesNote) story.append(node('p', state.jaunt.quotesNote, 'jaunt-meta'));
    body.append(story);
    transcript('opening', 'opening', [named, ...told], hear);
  }
  /**
   * The owner, 2026-11-16: "you should see that text as the final scene of the jaunt and then
   * you get the end jaunt screen". The ending, on screen while it is read aloud and the eye
   * rises to a last view of where the jaunt began (jaunt-pace.js); Finish Jaunt goes on to
   * Outing complete at once, and it comes by itself when the scene is done.
   */
  function closingScene(old) {
    const nextKey = `${state.session}:closing`, same = key === nextKey;
    const scroll = same ? body.scrollTop : 0;
    const listening = same && document.activeElement?.dataset.action === 'listen' && body.contains(document.activeElement);
    const onHeading = same && document.activeElement?.tagName === 'H2' && body.contains(document.activeElement);
    root.classList.add('jaunt-final'); root.classList.add('jaunt-closing');
    straight.hidden = true; mode.hidden = true; // nothing is left to travel by
    const progress = node('p', '', 'jaunt-progress jaunt-stop-k jaunt-final-k');
    progress.append(icon('finish', 15), node('span', 'Closing'));
    const heading = node('h2', state.jaunt.title); heading.tabIndex = -1;
    body.replaceChildren(progress, heading);
    voiced = []; shownParts = [];
    if (!same) engaged = false;
    const hear = listen('ending', state.outcome.id); if (hear) body.append(hear);
    const ending = String(state.outcome.text).split(/\n\s*\n/).map(t => node('p', t.trim(), 'jaunt-closing-text'));
    body.append(...ending);
    transcript('ending', state.outcome.id, ending, hear);
    buttons.prev.disabled = true; buttons.next.disabled = barNext.disabled = false;
    setStops(false, { focus: false }); buttons.stops.disabled = true;   // T-3753: nothing is left to go to
    for (const b of [buttons.next, barNext]) {
      b.textContent = 'Finish jaunt'; b.classList.remove('jaunt-needs-choice'); b.classList.add('jaunt-finish', 'jaunt-closing-finish');
    }
    needsChoice = false;
    barLabel.replaceChildren(node('span', `▴ ${state.jaunt.title}`), node('small', 'Closing'));
    barLabel.classList.add('jaunt-final-k');
    barLabel.setAttribute('aria-label', `Open the outing panel: ${state.jaunt.title}, closing`);
    if (!same) setCollapsed(false, { focus: false });
    body.hidden = false; root.classList.remove('jaunt-detail'); barNext.hidden = false; barReturn.hidden = true;
    body.scrollTop = scroll; key = nextKey;
    narration?.at(state.jaunt, 'ending', state.outcome.id);
    syncTranscripts(); paintVoice(); tell(outingNews(state));
    if (listening) body.querySelector('[data-action="listen"]')?.focus({ preventScroll: true });
    else if (!same || onHeading) heading.focus({ preventScroll: true });
  }
  function render(next) {
    const old = state;
    if (next.phase === 'detail' && old?.phase !== 'detail') saveView();
    state = next;
    const active = !!state.jaunt && !['menu', 'outcome'].includes(state.phase);
    root.hidden = !active; document.documentElement.toggleAttribute('data-jaunt-active', active);
    // T-3578: the voice follows the outing — its ending when it finishes, nothing once it is left.
    if (state.jaunt) void narration?.prepare(state.jaunt);
    if (!active) {
      setStops(false, { focus: false });
      if (state.phase === 'outcome' && state.outcome?.id) narration?.at(state.jaunt, 'ending', state.outcome.id);
      else narration?.end();
      tell(outingNews(state));
      key = null; overlayView = null; setCollapsed(false, { focus: false }); return;
    }
    if (state.phase === 'closing') { closingScene(old); return; }
    voiced = []; shownParts = [];
    const stop = currentStop(state), nextKey = `${state.session}:${stop.id}`, same = key === nextKey;
    if (old?.session !== state.session) {
      pressed = null; setStops(false, { focus: false });
      mode.replaceChildren(...state.jaunt.allowed_modes.map(id => {
        const option = node('option', PACES[id].label); option.value = id; return option;
      }));
    }
    mode.hidden = false; mode.value = shownMode(state);   // T-3405: the mode this leg really travels in
    straight.hidden = !['travelling', 'paused'].includes(state.phase);
    mode.classList.toggle('jaunt-mode-wide', straight.hidden);
    const scroll = same ? (overlayView?.scroll ?? body.scrollTop) : 0, focused = document.activeElement?.dataset.choice;
    const listening = same && document.activeElement?.dataset.action === 'listen' && body.contains(document.activeElement);
    // T-3671: a repaint keeps focus on the stop's heading where it was (a voice starting or stopping repaints).
    const onHeading = same && document.activeElement?.tagName === 'H2' && body.contains(document.activeElement);
    const opening = state.phase === 'opening' || (state.phase === 'detail' && state.detailPhase === 'opening');
    const final = !opening && isFinalStop(state), count = routeCount(state);   // T-3754: this route's stops
    root.classList.toggle('jaunt-final', final); root.classList.remove('jaunt-closing');
    const heading = node('h2', stopName(state, stop));
    heading.tabIndex = -1;
    // T-3671: arriving is said once in the panel's status line (`tell`), not by this line,
    // which is drawn anew each time.
    const progress = node('p', '', 'jaunt-progress jaunt-stop-k');
    // T-3432: the last stop says it is the last, on the page and on the bar.
    if (final) { progress.classList.add('jaunt-final-k'); progress.append(icon('finish', 15)); }
    if (state.stopIndex > 0) progress.append(node('span', state.jaunt.title, 'jaunt-progress-title'), ' · ');
    progress.append(node('span', final ? `Final stop · ${state.stopIndex + 1} of ${count}` : `Stop ${state.stopIndex + 1} of ${count}`));
    body.replaceChildren();
    if (state.stopIndex === 0) welcome(opening);
    if (!opening) body.append(progress, heading);
    const resources = resourceSummary(state);
    if (resources.length) {
      const strip = node('ul', '', 'jaunt-resources'); strip.setAttribute('aria-label', 'Outing resources');
      strip.replaceChildren(...resources.map(text => node('li', text))); body.append(strip);
    }
    if (state.estimate && !(opening || state.stopIndex === 0)) {
      const eta = node('p', `${formatEstimate(state.estimate)} remaining`, 'jaunt-progress'); eta.dataset.jauntRemaining = ''; body.append(eta);
    }
    let withheld = false;
    const travelling = ['travelling', 'paused'].includes(state.phase) || (state.phase === 'detail' && ['travelling', 'paused'].includes(state.detailPhase));
    if (opening) {
      const flying = node('p', '', 'jaunt-flying');
      flying.append(icon('fly', 18), node('span', `Flying to the start · ${stopName(state, stop)}`));
      body.append(flying);
    } else if (travelling) {
      body.append(node('p', state.phase === 'paused' ? 'Ride paused. Explore here, or resume when you are ready.'
        : state.error || (final ? 'On the way to the final stop…' : 'On the way to the next stop…')));
      // T-3432 (owner, 2026-11-06: "the text of your story along the way gets cut off or if it
      // really fast between locations there is no time to read it so don't show it"): each
      // line is shown whole, and only the lines this leg leaves time to read. The rest wait in
      // the stop's own On the way fold.
      const readable = readableLines(state.context?.lines || [], state.estimate?.legs?.[0]?.seconds);
      if (readable.length && !state.contextDismissed) {
        const notes = node('aside', '', 'jaunt-leg-notes'); notes.setAttribute('aria-label', 'On the way');
        // T-3629: the notes close with a small × in their corner, not a full-width key.
        const shut = button('', actions.dismissContext); shut.className = 'jaunt-notes-close';
        shut.setAttribute('aria-label', 'Dismiss road notes'); shut.title = 'Dismiss road notes'; shut.append(icon('close', 16));
        notes.prepend(shut); contextLines(notes, readable); body.append(notes);
        // T-3671: Esc in the notes closes them too, and leaves focus on the outing's controls.
        notes.addEventListener('keydown', e => {
          if (e.key !== 'Escape') return;
          e.preventDefault(); actions.dismissContext();
          [straight, buttons.next, collapse].find(b => b.isConnected && !b.hidden && !b.disabled)?.focus({ preventScroll: true });
        });
      }
      if (state.phase === 'paused') body.append(button('Resume ride', actions.resumeRide));
      if (state.error) body.append(button('Try this stop again', actions.retry));
    } else if (state.hostWaiting) {
      body.append(node('p', 'Your guide is approaching. You can wait here, continue to the next stop, or leave the jaunt.', 'jaunt-meta'));
    } else {
      let hear = listen('stop', stop.id); if (hear) body.append(hear);
      const historicalClaims = stop.narrative ? stop.evidence.filter(id => state.jaunt.evidence.find(c => c.id === id)?.confidence !== 'reconstructed') : stop.evidence;
      const told = prose(body, stop.text, historicalClaims, historicalClaims?.every(id => state.jaunt.evidence.find(c => c.id === id)?.confidence === 'reconstructed'), [], stop.since);
      // T-3671: words the card withholds are not read aloud either.
      if (told.dataset.withheld !== undefined) { withheld = true; hear?.remove(); hear = null; }
      transcript('stop', stop.id, [told], hear);
      if (stop.narrative) prose(body, stop.narrative, stop.evidence.filter(id => state.jaunt.evidence.find(c => c.id === id)?.confidence === 'reconstructed'), true);
      // T-3755: the stop closes with the narrator's line sending you on, or round this place
      // first (narration.js onwardLines); in a voiced telling it is read after the stop's voice.
      const onward = withheld ? '' : scriptFor(state.jaunt, 'onward', stop.id);
      if (onward) {
        const line = node('p', onward, 'jaunt-onward'); line.dataset.readingSkip = ''; line.dataset.voiced = 'onward';
        line.classList.toggle('jaunt-voicing', !!narration?.isPlaying(state.jaunt, 'onward', stop.id));
        body.append(line);
      }
      // T-3553: a stop played by its people (jaunt-stage.js) can be watched again from the start.
      if (stop.stage?.cast?.length && actions.replay) {
        const again = button('Watch again', () => actions.replay()); again.dataset.action = 'replay'; again.className = 'jaunt-replay';
        const what = stop.stage.caption ? node('p', stop.stage.caption, 'jaunt-stage-caption') : null;
        const row = node('div', '', 'jaunt-stage'); if (what) row.append(what); row.append(again);
        // The burning of the fort (2026-11-16): the visitor holds a torch, and may put it to the
        // nearest building that is not burning yet.
        if (stop.stage.fire?.visitor && actions.kindle) {
          const said = node('p', 'You hold a burning brand. Walk up to a building and put it to the logs.', 'jaunt-stage-caption jaunt-fire-note');
          said.setAttribute('role', 'status'); said.setAttribute('aria-live', 'polite');
          const light = button('Set it alight', () => {
            const r = actions.kindle();
            said.textContent = r?.lit ? `You put your torch to the ${r.name}. It catches.`
              : r?.none === 'all' ? 'Everything that will burn is burning.'
                : r?.none === 'far' ? `Too far to reach. Walk nearer the fort${r.nearest ? ` (the ${r.nearest} is ${r.distance} m off)` : ''}.`
                  : 'Wait for the fire to begin.';
          });
          light.dataset.action = 'kindle'; light.className = 'jaunt-replay jaunt-kindle';
          row.append(light, said);
        }
        body.append(row);
      }
      if (state.context?.lines.length) {
        const notes = node('details', '', 'jaunt-road-history'); notes.append(node('summary', 'On the way')); contextLines(notes);
        // T-2946: a long block reads as a list, not a wall of twenty addresses.
        const passed = state.context.passed, more = passed.length - 6;
        if (passed.length) notes.append(node('p', `Along this route: ${passed.slice(0, 6).map(p => p.label).join(' · ')}${more > 0 ? ` · and ${more} more` : ''}`));
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
    const here = state.visited[state.stopIndex];
    needsChoice = state.phase === 'atStop' && !canNext(state) && !here.committed && choicesFor(state).length > 0;
    buttons.prev.disabled = state.stopIndex === 0; buttons.next.disabled = barNext.disabled = !canNext(state) && !needsChoice && !opening;
    buttons.stops.disabled = false;
    // T-3432: at the last stop the one way on is to finish.
    const finish = final && canNext(state) && !needsChoice;
    for (const b of [buttons.next, barNext]) {
      b.textContent = opening ? 'Skip to the start' : needsChoice ? 'Choose an option' : finish ? 'Finish jaunt' : 'Next stop';
      b.classList.remove('jaunt-closing-finish');
      b.classList.toggle('jaunt-needs-choice', needsChoice); b.classList.toggle('jaunt-finish', finish);
    }
    const place = stopName(state, stop), where = final ? `Final stop · ${state.stopIndex + 1} of ${count}` : `Stop ${state.stopIndex + 1} of ${count}`;
    barLabel.replaceChildren(node('span', `▴ ${opening ? 'Flying to ' : ['travelling', 'paused'].includes(state.phase) ? 'On the way to ' : ''}${place}`),
      node('small', where));
    barLabel.classList.toggle('jaunt-final-k', final);
    barLabel.setAttribute('aria-label', `Open the outing panel: ${place}, ${where.toLowerCase()}`);
    if (collapsed && state.phase === 'atStop' && old?.phase === 'travelling') setCollapsed(false, { focus: false });
    const open = overlayOpen() || state.phase === 'detail';
    if (open) setCollapsed(true, { focus: false });
    root.classList.toggle('jaunt-detail', open); body.hidden = open; barNext.hidden = open; barReturn.hidden = !open;
    // T-3645: the stop at the reader's age, from this jaunt's other tellings; an age picked
    // here holds for the rest of the outing.
    if (old?.session !== state.session) forgetAge(body);
    readingTabs(body, opening ? { into: body } : { after: heading });
    body.scrollTop = scroll; key = nextKey;
    if (!open) restoreView();
    retellShown();   // T-3735: before arriving, so a part shown at another age speaks in its telling's voice
    narration?.at(state.jaunt, ...(opening ? ['opening', 'opening'] : state.phase === 'atStop' && !state.hostWaiting && !withheld ? ['stop', stop.id] : [null]));
    syncTranscripts(); paintVoice(); tell(outingNews(state, place, where));
    if (stopsOpen) { paintStops(); return; }   // T-3753: the list stays up, and keeps the focus
    if (listening) body.querySelector('[data-action="listen"]')?.focus({ preventScroll: true });
    else if (focused && same) [...body.querySelectorAll('[data-choice]')].find(el => el.dataset.choice === focused)?.focus();
    else if (onHeading || (state.phase === 'atStop' && (!same || old?.phase === 'travelling'))) heading.focus({ preventScroll: true });
  }
  return { render, get collapsed() { return collapsed; }, collapse: value => setCollapsed(value, { focus: false }),
    /** T-3671: the visitor is at the closing scene (jaunt-pace.js createClosingClock `hold`). */
    get holding() { return engaged && root.classList.contains('jaunt-closing'); },
    /** The owner, 2026-11-16: the meter, from jaunt-pace.js meterReading (null hides it). */
    meter(m) { for (const x of meters) x.set(m); },
    /** T-3753: whether the stop's scene ({ scene }) or its voice ({ voice }) is still loading (null: nothing is). */
    loading,
    /** T-3753: the Stops list (open: true / false). */
    stops: value => setStops(value, { focus: false }),
    destroy() { offNarration?.(); narration?.end(); observer.disconnect(); swaps.disconnect(); controlSize.disconnect(); root.remove(); status.remove(); sheet.remove(); document.documentElement.removeAttribute('data-jaunt-active'); document.documentElement.removeAttribute('data-jaunt-collapsed'); document.documentElement.style.removeProperty('--jaunt-nav'); } };
}
