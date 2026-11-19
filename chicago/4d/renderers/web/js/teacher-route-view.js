/**
 * T-3672 — a teacher's route on screen (the pure half is teacher-route.js).
 *
 *   mountRouteBuilder  Guide › For teachers: start from a jaunt or find places and people of
 *                      this year, order them, add a note and a question to any stop, title it,
 *                      then make ONE share link, download the route file, open one again, or
 *                      try the route here as a student will see it.
 *   mountRoutePanel    Jaunts, pinned above the list while a route is open: its stops in
 *                      order, Go there for each, the teacher's note and question shown as the
 *                      teacher's words, and an answer box that saves to the field notebook.
 *
 * Everything a teacher typed reaches the page through textContent and input values only.
 * The page is read through `ctx` (the Navigator's context), never by importing main.js.
 */
import { t } from './strings/index.js';
import './strings/route.js';
import './strings/notebook.js';
import {
  ROUTE_LIMITS, ROUTE_YEARS, activeRoute, answerEntry, jauntStops, normalRoute, readRouteFile,
  routeFileName, routeFileText, routeLink, savedAnswer,
} from './teacher-route.js';
import { fieldNotebook } from './field-notebook.js';

const tr = (key, params) => t(`route.${key}`, params);
function useStyle(doc) {
  if (!doc?.head || doc.getElementById?.('teacher-route-style')) return;
  const css = doc.createElement('link'); css.id = 'teacher-route-style'; css.rel = 'stylesheet';
  css.href = new URL('../css/teacher-route.css', import.meta.url).href;
  doc.head.append(css);
}
const maker = (doc) => (tag, cls, text) => {
  const n = doc.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};
const sceneYear = (ctx) => String(typeof ctx?.scene === 'object' ? (ctx.scene?.id ?? ctx.scene?.target_date?.slice(0, 4) ?? '') : (ctx?.scene ?? ''));
const plural = (n, one, many, params = {}) => (n === 1 ? tr(one, params) : tr(many, { n, ...params }));
/** On a phone the device steps down so the ride (or the arrival) is in view, as Map's Go does. */
const stepDown = (ctx, ok) => { if (ok !== false && ['half', 'full'].includes(ctx?.navigator?.detent)) ctx.navigator?.dock?.(); };

// ---- Guide › For teachers ------------------------------------------------------------- //

export function mountRouteBuilder(container, ctx = {}, { win = container?.ownerDocument?.defaultView } = {}) {
  const doc = container.ownerDocument;
  const n = maker(doc);
  const root = n('section', 'nav-route-build');
  root.id = 'guide-route';
  const year = sceneYear(ctx);
  root.append(n('h3', null, tr('build.title')), n('p', 'nav-sub', tr('build.intro', { year })), n('p', 'nav-sub', tr('build.private')));
  const open = n('button', 'setting-button', tr('build.open')); open.type = 'button'; open.id = 'route-build-open';
  const content = n('div', 'route-build'); content.id = 'route-build-content'; content.hidden = true;
  open.setAttribute('aria-expanded', 'false'); open.setAttribute('aria-controls', content.id);
  const status = n('p', 'route-status'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  root.append(open, status, content);
  container.append(root);
  const say = (text) => { status.textContent = text; };

  const state = { title: '', jaunt: null, stops: [] };
  let catalog = null, opened = false;

  open.addEventListener('click', async () => {
    if (opened) { content.hidden = !content.hidden; open.setAttribute('aria-expanded', String(!content.hidden)); return; }
    useStyle(doc);
    if (!ROUTE_YEARS.includes(year)) { say(tr('build.yearOnly')); return; }
    opened = true; open.disabled = true; say(tr('build.reading'));
    try { catalog = await ctx.actions?.routeCatalog?.(); } catch { catalog = null; }
    open.disabled = false;
    if (!catalog) { opened = false; say(tr('build.failed')); return; }
    say('');
    build();
    content.hidden = false; open.setAttribute('aria-expanded', 'true');
  });

  function build() {
    // The title.
    const titleLabel = n('label', 'route-field', tr('build.name'));
    const title = n('input'); title.type = 'text'; title.maxLength = ROUTE_LIMITS.title; title.id = 'route-title';
    title.autocomplete = 'off';
    title.addEventListener('input', () => { state.title = title.value; stale(); });
    titleLabel.append(title);

    // Start from a jaunt.
    const jauntRow = n('div', 'route-jaunt-pick');
    const jauntLabel = n('label', 'route-field', tr('build.fromJaunt'));
    const select = n('select'); select.id = 'route-jaunt';
    const first = n('option', null, tr('build.pickJaunt')); first.value = ''; select.append(first);
    for (const j of catalog.jaunts) { const o = n('option', null, j.title); o.value = j.id; select.append(o); }
    jauntLabel.append(select);
    const use = n('button', 'setting-button', tr('build.useJaunt')); use.type = 'button'; use.disabled = true;
    select.addEventListener('change', () => { use.disabled = !select.value; });
    use.addEventListener('click', () => {
      const j = catalog.jaunt(select.value);
      if (!j) return;
      const { stops, dropped } = jauntStops(j, catalog);
      state.jaunt = j.id; state.stops = stops;
      if (!state.title.trim()) { state.title = j.title.slice(0, ROUTE_LIMITS.title); title.value = state.title; }
      paintStops(); stale();
      say(dropped ? tr('build.jauntSkipped', { title: j.title, n: dropped }) : tr('build.usedJaunt', { title: j.title }));
    });
    jauntRow.append(jauntLabel, use);
    if (!catalog.jaunts.length) jauntRow.hidden = true;
    const jauntLine = n('p', 'route-jaunt-line');

    // Find a place or person.
    const findLabel = n('label', 'route-field', tr('build.find'));
    const find = n('input'); find.type = 'search'; find.id = 'route-find'; find.autocomplete = 'off';
    find.setAttribute('aria-describedby', 'route-find-hint');
    findLabel.append(find);
    const hint = n('p', 'nav-sub', tr('build.findHint')); hint.id = 'route-find-hint';
    const results = n('ul', 'route-results'); results.setAttribute('aria-label', tr('build.find'));
    const paintResults = () => {
      results.replaceChildren();
      const q = find.value.trim();
      if (!q) return;
      const rows = catalog.search(q, 8);
      if (!rows.length) { results.append(n('li', 'nav-sub', tr('build.none'))); return; }
      for (const row of rows) {
        const li = n('li', 'route-result');
        const words = n('span', 'route-result-words');
        words.append(n('strong', null, row.label), ' ', n('span', 'route-kind', tr(`kind.${row.kind}`)));
        if (row.sub) words.append(' ', n('span', 'nav-sub', row.sub));
        const add = n('button', 'setting-button route-add', tr('build.add')); add.type = 'button';
        add.setAttribute('aria-label', `${tr('build.add')} ${row.label}`);
        add.addEventListener('click', () => {
          if (state.stops.length >= ROUTE_LIMITS.stops) { say(tr('build.full', { n: ROUTE_LIMITS.stops })); return; }
          state.stops.push({ kind: row.kind, id: row.id, note: '', question: '' });
          paintStops(); stale();
          say(tr('build.added', { n: state.stops.length, label: row.label }));
        });
        li.append(words, add);
        results.append(li);
      }
    };
    find.addEventListener('input', paintResults);

    // The stops, in order.
    const count = n('p', 'route-count');
    const list = n('ol', 'route-stops'); list.setAttribute('aria-label', tr('build.stops'));
    function paintStops(focus = null) {
      list.replaceChildren();
      count.textContent = tr('build.count', { n: state.stops.length, max: ROUTE_LIMITS.stops });
      const jaunt = state.jaunt ? catalog.jaunt(state.jaunt) : null;
      jauntLine.replaceChildren();
      if (jaunt) {
        const drop = n('button', 'setting-button', tr('build.dropJaunt')); drop.type = 'button';
        drop.addEventListener('click', () => { state.jaunt = null; paintStops(); stale(); select.focus?.(); });
        jauntLine.append(n('span', null, tr('build.jauntLine', { title: jaunt.title })), ' ', drop);
      }
      jauntLine.hidden = !jaunt;
      if (!state.stops.length) list.append(n('li', 'nav-sub route-empty', tr('build.empty')));
      state.stops.forEach((stop, i) => {
        const row = catalog.get(stop.kind, stop.id);
        const li = n('li', 'route-stop'); li.dataset.routeStop = String(i);
        const head = n('div', 'route-stop-head');
        const words = n('div');
        words.append(n('span', 'nav-k', tr('panel.stop', { n: i + 1 })), ' ', n('strong', 'route-stop-name', row?.label ?? stop.id), ' ',
          n('span', 'route-kind', tr(`kind.${stop.kind}`)));
        head.append(words);
        const tools = n('div', 'route-stop-tools');
        const tool = (key, glyph, run, disabled) => {
          const b = n('button', 'setting-button route-tool', glyph); b.type = 'button'; b.dataset.tool = key;
          b.setAttribute('aria-label', tr(`build.${key}`, { n: i + 1 })); b.title = tr(`build.${key}`, { n: i + 1 });
          b.disabled = disabled; b.addEventListener('click', run); tools.append(b); return b;
        };
        const move = (to) => {
          const [s] = state.stops.splice(i, 1); state.stops.splice(to, 0, s);
          paintStops({ index: to, tool: to < i ? 'up' : 'down' }); stale();
        };
        tool('up', '↑', () => move(i - 1), i === 0);
        tool('down', '↓', () => move(i + 1), i === state.stops.length - 1);
        tool('remove', '×', () => {
          state.stops.splice(i, 1); paintStops({ index: Math.min(i, state.stops.length - 1), tool: 'remove' }); stale();
          say(tr('build.removed'));
        }, false);
        head.append(tools);
        const field = (key, prop) => {
          const label = n('label', 'route-field', tr(`build.${key}`));
          const area = n('textarea'); area.rows = 2; area.maxLength = ROUTE_LIMITS[prop]; area.value = stop[prop];
          area.addEventListener('input', () => { stop[prop] = area.value; stale(); });
          label.append(area); return label;
        };
        li.append(head, field('note', 'note'), field('question', 'question'));
        list.append(li);
      });
      if (focus) {
        const li = list.children[focus.index];
        const b = li?.querySelector?.(`[data-tool="${focus.tool}"]`);
        (b && !b.disabled ? b : li?.querySelector?.('button:not([disabled])') ?? find).focus?.({ preventScroll: true });
      }
    }

    // Share: one link, one file, and the way back in.
    const actions = n('div', 'route-actions');
    const button = (key, run) => { const b = n('button', 'setting-button', tr(`build.${key}`)); b.type = 'button'; b.dataset.action = key; b.addEventListener('click', run); actions.append(b); return b; };
    const linkLabel = n('label', 'route-field route-link', tr('build.linkLabel'));
    const link = n('input'); link.type = 'text'; link.readOnly = true; link.id = 'route-link';
    linkLabel.append(link); linkLabel.hidden = true;
    const copy = n('button', 'setting-button', tr('build.copy')); copy.type = 'button'; copy.hidden = true;
    function stale() { linkLabel.hidden = true; copy.hidden = true; link.value = ''; }
    const current = () => normalRoute({ year, title: state.title, jaunt: state.jaunt, stops: state.stops });
    button('link', () => {
      const route = current();
      if (!route) { say(tr('build.needStop')); return; }
      const href = routeLink(route, win?.location?.href);
      if (!href) { stale(); say(tr('build.tooLong')); return; }
      link.value = href; linkLabel.hidden = false; copy.hidden = false; say('');
      link.focus?.({ preventScroll: true }); link.select?.();
    });
    copy.addEventListener('click', async () => {
      try { await win.navigator.clipboard.writeText(link.value); say(tr('build.copied', { year })); }
      catch { link.focus?.(); link.select?.(); say(tr('build.copyFallback')); }
    });
    button('download', () => {
      const route = current();
      const text = route && routeFileText(route);
      if (!text) { say(tr('build.needStop')); return; }
      const url = win.URL.createObjectURL(new win.Blob([text], { type: 'application/json' }));
      const a = n('a'); a.href = url; a.download = routeFileName(route);
      doc.body.append(a); a.click(); a.remove();
      win.setTimeout(() => win.URL.revokeObjectURL(url), 1000);
      say(tr('build.downloaded'));
    });
    const file = n('input'); file.type = 'file'; file.accept = '.json,application/json'; file.hidden = true; file.id = 'route-file';
    file.setAttribute('aria-label', tr('build.openFile'));
    button('openFile', () => file.click());
    file.addEventListener('change', async () => {
      const chosen = file.files?.[0];
      file.value = '';
      if (!chosen) return;
      let route = null;
      try { route = chosen.size <= ROUTE_LIMITS.file ? readRouteFile(await chosen.text()) : null; } catch { route = null; }
      if (!route) { say(tr('build.badFile')); return; }
      if (route.year !== year) { say(tr('build.fileYear', { year: route.year })); return; }
      const known = route.stops.filter((s) => catalog.get(s.kind, s.id));
      state.title = route.title; title.value = route.title;
      state.jaunt = route.jaunt && catalog.jaunt(route.jaunt) ? route.jaunt : null;
      state.stops = known.map((s) => ({ ...s }));
      paintStops(); stale();
      const skipped = route.stops.length - known.length;
      say([tr('build.opened', { title: route.title || tr('panel.untitled') }), skipped ? tr('build.fileSkipped', { n: skipped }) : ''].filter(Boolean).join(' '));
    });
    button('try', async () => {
      const route = current();
      if (!route) { say(tr('build.needStop')); return; }
      const ok = await ctx.actions?.beginRoute?.(route);
      if (ok !== false) say(tr('build.tried'));
    });
    content.replaceChildren(titleLabel, jauntRow, jauntLine, findLabel, hint, results, n('h4', null, tr('build.stops')), count, list,
      actions, file, linkLabel, copy);
    paintStops();
  }
  return { root, get state() { return state; }, destroy() { root.remove(); } };
}

// ---- Jaunts: the student's Route panel ------------------------------------------------ //

export function mountRoutePanel(host, ctx = {}, { notebook = fieldNotebook, store = activeRoute } = {}) {
  const doc = host.ownerDocument;
  const n = maker(doc);
  let context = ctx;
  const drafts = new Map();
  function paint() {
    const session = store.get();
    host.replaceChildren();
    host.hidden = !session;
    if (!session) return;
    useStyle(doc);
    const root = n('section', 'nav-block route-panel'); root.id = 'route-panel';
    root.setAttribute('aria-labelledby', 'route-panel-title');
    const heading = n('h3', 'nav-place', session.title || tr('panel.untitled')); heading.id = 'route-panel-title';
    root.append(n('span', 'nav-k', tr('panel.k')), ' ', heading);
    const close = n('button', 'setting-button route-close', tr('panel.close')); close.type = 'button';
    close.addEventListener('click', () => { store.clear(); });
    if (session.state === 'wrong-year') {
      root.append(n('p', null, tr('panel.otherYear', { year: session.year })));
      if (session.link) { const a = n('a', 'setting-button route-year-link', tr('panel.openYear', { year: session.year })); a.href = session.link; root.append(a); }
      root.append(' ', close);
      host.append(root);
      return;
    }
    root.append(n('p', 'nav-sub', plural(session.stops.length, 'panel.countOne', 'panel.count', { year: session.year })));
    if (session.skipped) root.append(n('p', 'route-skipped', plural(session.skipped, 'panel.skippedOne', 'panel.skipped')));
    if (session.jaunt) {
      const line = n('div', 'route-panel-jaunt');
      const start = n('button', 'setting-button', tr('panel.startJaunt')); start.type = 'button';
      start.addEventListener('click', () => { void context.api?.jaunts?.start?.(session.jaunt.id); });
      line.append(n('p', null, tr('panel.jaunt', { title: session.jaunt.title })), start);
      root.append(line);
    } else if (session.jauntMissing) root.append(n('p', 'route-skipped', tr('panel.jauntMissing')));
    const saved = notebook.read();
    const list = n('ol', 'route-panel-stops');
    for (const stop of session.stops) {
      const li = n('li', 'route-panel-stop'); li.dataset.routeStop = String(stop.n);
      const head = n('div', 'route-stop-head');
      const words = n('div');
      words.append(n('span', 'nav-k', tr('panel.stop', { n: stop.n })), ' ', n('strong', 'route-stop-name', stop.label), ' ',
        n('span', 'route-kind', tr(`kind.${stop.kind}`)));
      const go = n('button', 'setting-button route-go', tr('panel.go')); go.type = 'button';
      go.setAttribute('aria-label', `${tr('panel.go')}: ${stop.label}`);
      go.addEventListener('click', async () => {
        const a = context.actions ?? {};
        const ok = await (a.routeGo ? a.routeGo(stop) : stop.kind === 'place' ? a.goTo?.(stop.id) : false);
        stepDown(context, ok);
      });
      const keys = n('div', 'route-stop-tools'); keys.append(go);
      if (stop.kind === 'person' && context.actions?.openPerson) {
        const card = n('button', 'setting-button', tr('panel.card')); card.type = 'button';
        card.setAttribute('aria-label', `${tr('panel.card')}: ${stop.label}`);
        card.addEventListener('click', () => { void context.actions.openPerson(stop.id); });
        keys.append(card);
      }
      head.append(words, keys);
      li.append(head);
      // The teacher's words: always labelled as theirs, always text.
      if (stop.note) {
        const note = n('div', 'route-teacher');
        note.append(n('p', 'route-teacher-k', tr('panel.note')), n('p', 'route-teacher-words', stop.note));
        li.append(note);
      }
      if (stop.question) {
        const q = n('div', 'route-teacher route-teacher-question');
        q.append(n('p', 'route-teacher-k', tr('panel.question')), n('p', 'route-teacher-words', stop.question));
        const label = n('label', 'route-field', tr('panel.answer'));
        const area = n('textarea'); area.rows = 3; area.maxLength = ROUTE_LIMITS.answer;
        const key = `${session.title}\u0000${stop.n}`;
        const before = savedAnswer(saved.entries, session, stop);
        area.value = drafts.get(key) ?? before?.answer ?? '';
        area.addEventListener('input', () => drafts.set(key, area.value));
        label.append(area);
        const saveRow = n('div', 'route-answer-row');
        const save = n('button', 'setting-button', tr('panel.save')); save.type = 'button';
        const said = n('p', 'route-status'); said.setAttribute('role', 'status');
        save.addEventListener('click', () => {
          const entry = answerEntry(session, stop, area.value);
          if (!entry) { said.textContent = tr('panel.emptyAnswer'); return; }
          const state = notebook.read();
          const old = state.error ? null : savedAnswer(state.entries, session, stop);
          const r = old ? notebook.update(old.id, entry.text) : notebook.add(entry);
          said.textContent = r.ok ? tr(old ? 'panel.updated' : 'panel.saved') : t(`notebook.error.${r.reason}`, null, tr('panel.emptyAnswer'));
          if (r.ok) drafts.delete(key);
        });
        saveRow.append(save, said);
        // The student's answer sits under the teacher's words, outside their mark.
        const answer = n('div', 'route-answer');
        answer.append(label, saveRow);
        li.append(q, answer);
      }
      list.append(li);
    }
    root.append(list, n('p', 'nav-sub route-words', tr('panel.words')), n('p', 'nav-sub', tr('panel.notebook')), close);
    host.append(root);
  }
  const off = store.subscribe(() => { drafts.clear(); paint(); });
  paint();
  return {
    refresh(next) { if (next) context = next; paint(); },
    destroy() { off(); host.replaceChildren(); },
  };
}

