import { t } from './strings/index.js';
import './strings/photo-hunt.js';
import { HUNT_YEAR, huntDay, huntLink, parseHuntLink, huntRounds, createHuntSession } from './photo-hunt.js';

/** Lazy Navigator content; only the current photograph has a src, released when hidden. */
export function mountPhotoHunt(host, { context = () => ({}), win = host?.ownerDocument?.defaultView,
  now = () => new Date(), storage = () => win.localStorage } = {}) {
  const doc = host?.ownerDocument;
  if (!doc) return null;
  const make = (tag, key, vars) => { const el = doc.createElement(tag); if (key) el.textContent = t(`hunt.${key}`, vars); return el; };
  const root = make('section'); root.className = 'photo-hunt'; root.setAttribute('aria-label', t('hunt.title'));
  const heading = make('h3', 'title'); heading.tabIndex = -1;
  const content = make('div'); content.className = 'photo-hunt-content';
  const status = make('p'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const saved = make('p'); saved.className = 'photo-hunt-storage'; saved.setAttribute('role', 'status');
  const foot = make('div'); foot.className = 'photo-hunt-actions';
  const shared = parseHuntLink(win?.location?.search);
  let day = shared?.day ?? huntDay(now()), rounds = [], session = null, visible = true, live = true, loading = false;
  let image = null, imageSource = null, imageReady = false, revision = 0;
  let guessButton = null, retryImage = null;
  const button = (parent, key, action) => {
    const el = make('button', key); el.type = 'button'; el.addEventListener('click', action); parent.append(el); return el;
  };
  const link = (parent, key, href) => {
    if (!href) return;
    const a = make('a', key); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; parent.append(a);
  };
  const releaseImage = () => { if (image) { image.onload = null; image.onerror = null; image.removeAttribute('src'); } image = null; imageSource = null; imageReady = false; };
  const storageStatus = () => {
    const state = session?.state;
    saved.textContent = state?.issue ? t(`hunt.storage.${state.issue}`) : state?.persisted ? t('hunt.saved') : '';
  };
  function loadImage() {
    if (!image || !imageSource || !visible) return;
    const current = image;
    imageReady = false; if (guessButton) guessButton.disabled = true;
    current.onload = () => {
      if (!live || image !== current) return;
      imageReady = true; if (guessButton) guessButton.disabled = false;
      if (retryImage) retryImage.hidden = true;
      if (!session?.state.answers[session.state.cursor]) status.textContent = t('hunt.ready');
    };
    current.onerror = () => {
      if (!live || image !== current) return;
      imageReady = false; if (guessButton) guessButton.disabled = true;
      if (retryImage) retryImage.hidden = false;
      status.textContent = t('hunt.imageFailed');
    };
    status.textContent = t('hunt.imageLoading'); current.src = imageSource;
  }
  function intro() {
    releaseImage(); content.replaceChildren(); foot.replaceChildren();
    heading.textContent = t('hunt.title'); saved.textContent = '';
    content.append(make('p', 'intro'), make('p', 'daily'), make('p', 'local'), make('p', 'date', { day }));
    if (String(context().scene?.id) !== HUNT_YEAR) { content.append(make('p', 'unavailableYear')); return; }
    if (win.location.search.includes('hunt=') && !shared) content.append(make('p', 'invalidLink'));
    button(content, 'open', start);
  }
  function shareControls() {
    const label = make('label', 'link'); label.hidden = true;
    const field = make('input'); field.type = 'text'; field.readOnly = true; field.setAttribute('aria-label', t('hunt.link')); label.append(field);
    button(foot, 'copy', async () => {
      const url = huntLink(day, win.location.href); if (!url) return;
      field.value = url; label.hidden = false;
      try { await win.navigator.clipboard.writeText(url); if (live) status.textContent = t('hunt.copied'); }
      catch { field.focus(); field.select(); status.textContent = t('hunt.copyFallback'); }
    });
    button(foot, 'restart', () => { session.reset(); render(true); });
    if (day !== huntDay(now())) button(foot, 'today', () => {
      day = huntDay(now()); session = null; intro(); void start();
    });
    foot.append(label);
  }
  function render(focus = false) {
    revision++; releaseImage(); content.replaceChildren(); foot.replaceChildren(); guessButton = null; retryImage = null;
    const state = session.state;
    heading.textContent = t(state.complete ? 'hunt.complete' : 'hunt.round', { n: state.cursor + 1 });
    content.append(make('p', 'date', { day }), make('p', 'total', { score: state.score }));
    status.textContent = ''; storageStatus();
    if (state.complete) {
      const list = make('ol');
      rounds.forEach((round, i) => {
        const li = make('li'); const result = state.results[i];
        li.textContent = `${round.name} · ${round.years} · ${t(state.answers[i].skipped ? 'hunt.skipped' : 'hunt.result',
          { distance: Math.round(result.distance), score: result.score })}`;
        list.append(li);
      });
      content.append(list); shareControls(); if (focus) heading.focus(); return;
    }
    const round = rounds[state.cursor], answer = state.answers[state.cursor];
    const figure = make('figure'); image = make('img'); image.className = 'photo-hunt-image';
    image.alt = t('hunt.imageAlt', { n: state.cursor + 1 }); image.decoding = 'async';
    imageSource = round.image;
    const credit = make('figcaption'); credit.textContent = [round.credit, round.holder !== round.credit ? round.holder : '', round.rights].filter(Boolean).join(' · ');
    figure.append(image, credit); content.append(figure);
    const actions = make('div'); actions.className = 'photo-hunt-actions';
    retryImage = button(actions, 'retryImage', loadImage); retryImage.hidden = true;
    if (!answer) {
      content.append(make('p', 'instructions'), make('p', 'rules'), make('p', 'distanceNote'));
      button(actions, 'move', () => context().actions?.freeRoam?.());
      guessButton = button(actions, 'guess', () => {
        if (!imageReady) return;
        if (!session.guess(context().actions?.photoHunt?.position?.())) { status.textContent = t('hunt.positionMissing'); return; }
        render(true);
      }); guessButton.disabled = true;
      button(actions, 'skip', () => { session.skip(); render(true); });
    } else {
      const result = state.results[state.cursor];
      content.append(make('p', answer.skipped ? 'skipped' : 'result', { distance: Math.round(result.distance), score: result.score }));
      const title = make('h4'); title.textContent = round.title; content.append(title);
      content.append(make('p', 'recordedYears', { years: round.years }));
      if (round.date) content.append(make('p', 'recordedDate', { date: round.date }));
      const sources = make('div'); sources.className = 'photo-hunt-actions';
      link(sources, 'source', round.source); link(sources, 'full', round.full); content.append(sources);
      button(actions, 'visit', () => {
        const ok = context().actions?.photoHunt?.visit?.(round.id);
        status.textContent = t(ok ? 'hunt.visiting' : 'hunt.noVisit');
      });
      button(actions, state.cursor === 4 ? 'finish' : 'next', () => { session.next(); render(true); });
    }
    content.append(actions); shareControls(); loadImage(); if (focus) heading.focus();
  }
  async function start() {
    if (loading || !live) return;
    loading = true; const token = ++revision; status.textContent = t('hunt.loading');
    try {
      const loaded = await context().actions?.photoHunt?.load?.();
      if (!live || token !== revision) return;
      rounds = huntRounds(loaded?.doc, loaded?.destinations, day);
      if (rounds.length !== 5) throw new Error('No eligible round set');
      session = createHuntSession({ day, rounds, storage }); render(true);
    } catch { if (live && token === revision) status.textContent = t('hunt.unavailable'); }
    finally { loading = false; }
  }
  root.append(heading, content, status, saved, foot); host.append(root); intro();
  return {
    setVisible(on) {
      visible = !!on;
      if (!visible && image) { image.onload = null; image.onerror = null; image.removeAttribute('src'); imageReady = false; }
      else if (visible && image && !image.hasAttribute('src')) loadImage();
    },
    destroy() { live = false; revision++; releaseImage(); root.remove(); },
  };
}
