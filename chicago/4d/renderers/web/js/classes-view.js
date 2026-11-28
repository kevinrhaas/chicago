/**
 * T-3778 — classes on screen (the account half is js/classes.js).
 *
 *   startClasses         main.js, after sign-in: who is signed in, and the class a student
 *                        is in (read once per visit, which also moves their "last in")
 *   mountStudentClass    Settings › About › Your class: enter a code, join, leave
 *   mountTeacherClasses  Guide › For teachers › Your classes: make a class, its code, the
 *                        roster with joined / last in / handed in / reflections, each
 *                        student's hand-ins, CSV, print, remove a student, close, delete
 *   handInControl        Field notebook: Hand in, Hand in again, Take back, per entry
 *
 * A class's name and a student's name are typed by people, so they reach the page through
 * textContent only. Every button works by keyboard; the confirm rows take focus and give it
 * back. Nothing here judges the work: the teacher reads it.
 */
import { t, LANG } from './strings/index.js';
import './strings/classes.js';
import {
  CLASS_LIMITS, YEAR_GROUPS, REFLECTION_TOPICS, classesFor, typedCode, codeOk, shownCode,
  makeClass, myClasses, classRoster, newCode, closeClass, removeStudent,
  lookUpCode, joinClass, myClass, leaveClass, handIn, takeBack, rosterRows, classCSV, classSheetHTML,
} from './classes.js';
import { cloudFeaturesOn } from './student-data.js';

const tr = (key, vars) => t(`classes.${key}`, vars);
const when = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleString(LANG || undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
};
/** The roster's short date: "Nov 27" (the time only matters for last in, shown on hover). */
const shortDay = (iso) => {
  const d = new Date(iso || '');
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString(LANG || undefined, { month: 'short', day: 'numeric' });
};
const day = (iso) => {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString(LANG || undefined, { month: 'long', day: 'numeric', year: 'numeric' });
};
const why = (r) => tr(r?.why === 'refused' ? 'error.refused' : r?.why === 'offline' ? 'error.offline' : 'error.other');
const kindName = (h) => {
  const topic = h.topic ?? h.entry?.topic ?? '';
  return tr(`kind.${topic || h.kind || h.entry?.kind || 'note'}`);
};
const maker = (doc) => (tag, cls, text) => {
  const n = doc.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};
function useStyle(doc) {
  if (!doc?.head || doc.getElementById?.('classes-style')) return;
  const css = doc.createElement('link'); css.id = 'classes-style'; css.rel = 'stylesheet';
  css.href = new URL('../css/classes.css', import.meta.url).href;
  doc.head.append(css);
}
const btn = (n, text, fn, cls = 'setting-button') => {
  const b = n('button', cls, text); b.type = 'button'; b.addEventListener('click', fn); return b;
};

/** An inline "Are you sure?" row: Yes / Cancel, focus in and back out. */
function confirmRow(n, ask, yesText, onYes, trigger) {
  const row = n('div', 'field row saved-data-confirm class-confirm');
  const choice = n('span', 'saved-data-choice');
  const no = btn(n, tr('cancel'), () => { row.remove(); trigger.hidden = false; trigger.focus?.(); });
  const yes = btn(n, yesText, async () => {
    yes.disabled = true; no.disabled = true;
    try { await onYes(); } finally { row.remove(); trigger.hidden = false; }
  }, 'setting-button danger');
  choice.append(yes, no);
  row.append(n('span', null, ask), choice);
  trigger.hidden = true;
  trigger.after(row);
  yes.focus?.();
  return row;
}

// ---- the session: who is signed in, and the class a student is in -----------------------

const session = {
  account: null, projectId: '', config: null, fetchFn: undefined,
  on: false, loaded: false, mine: null, gone: null, handed: new Map(), why: '',
};
const listeners = new Set();
const notify = () => { for (const fn of listeners) { try { fn(session); } catch { /* a view cannot stop another */ } } };
export const classSession = {
  get state() { return session; },
  subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
};
const net = () => ({ projectId: session.projectId, account: session.account, fetchFn: session.fetchFn ?? globalThis.fetch?.bind(globalThis) });

/** Read the student's class (and move their "last in"). Returns the session. */
export async function refreshMine({ touch = true } = {}) {
  if (!session.on) { session.loaded = true; notify(); return session; }
  const r = await myClass({ ...net(), touch });
  session.loaded = true;
  if (r.ok) { session.mine = r.mine; session.handed = r.handed; session.gone = r.gone ?? null; session.why = ''; }
  else session.why = r.why;
  notify();
  return session;
}

/** main.js, once per visit, after the sign-in gate. */
export function startClasses({ account, config, projectId, fetchFn, doc = globalThis.document } = {}) {
  Object.assign(session, { account: account ?? null, config, projectId: projectId ?? '', fetchFn, on: classesFor(account, config),
    loaded: false, mine: null, gone: null, handed: new Map(), why: '' });
  mountStudentClass(doc);
  return session.on ? refreshMine() : Promise.resolve(session);
}

// ---- Settings › About › Your class -------------------------------------------------------

export function mountStudentClass(doc = globalThis.document) {
  const box = doc?.getElementById?.('s-class');
  if (!box) return null;
  const n = maker(doc);
  let stage = { step: 'idle' };
  const status = n('p', 'legend-note class-status');
  status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const say = (text) => { status.textContent = text; };

  function paint() {
    const { account, config, on, loaded, mine, gone } = session;
    if (!account?.uid || !cloudFeaturesOn(config)) { box.hidden = true; return; }
    box.hidden = false;
    const kept = status.textContent;
    box.replaceChildren(n('h5', null, tr('student.title')));
    if (!on) { box.append(n('p', 'legend-note', tr('student.needSignIn'))); return; }
    if (!loaded) { box.append(n('p', 'legend-note', tr('loading'))); return; }
    if (mine) {
      const line = mine.teacherName ? tr('student.in', { name: mine.className, teacher: mine.teacherName }) : tr('student.inNoTeacher', { name: mine.className });
      box.append(n('p', 'class-line', line), n('p', 'legend-note', tr(mine.closed ? 'student.closedLine' : 'student.how')));
      const row = n('div', 'field row');
      const leave = btn(n, tr('student.leave'), () => {
        confirmRow(n, tr('student.leaveAsk', { name: mine.className }), tr('student.leaveYes'), async () => {
          const r = await leaveClass({ ...net(), mine });
          if (!r.ok) { say(why(r)); return; }
          const name = mine.className;
          session.mine = null; session.handed = new Map(); notify();
          say(tr('student.left', { name }));
          box.querySelector('#s-class-code')?.focus?.();
        }, leave);
      });
      leave.id = 's-class-leave';
      row.append(n('span', null, mine.name), leave);
      box.append(row);
    } else {
      if (gone) box.append(n('p', 'legend-note', tr('student.gone', { name: gone.className })));
      box.append(n('p', 'legend-note', tr('student.intro')));
      const form = n('form', 'class-join');
      const label = n('label', 'field row');
      const input = n('input'); input.id = 's-class-code'; input.type = 'text'; input.autocomplete = 'off';
      input.spellcheck = false; input.maxLength = 12; input.setAttribute('autocapitalize', 'characters');
      input.placeholder = 'BCD-FGH'; input.value = stage.typed ?? '';
      label.append(n('span', null, tr('student.code')), input);
      const find = n('button', 'setting-button', tr('student.find')); find.type = 'submit'; find.id = 's-class-find';
      form.append(label, find);
      box.append(form);
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = typedCode(input.value);
        stage = { step: 'idle', typed: input.value };
        if (!codeOk(code)) { say(tr('student.notCode')); input.focus(); return; }
        find.disabled = true;
        const r = await lookUpCode({ ...net(), code });
        find.disabled = false;
        if (!r.ok) { say(r.why === 'no such code' ? tr('student.noSuch') : r.why === 'expired' ? tr('student.expired') : why(r)); input.focus(); return; }
        stage = { step: 'confirm', typed: input.value, found: r.code };
        say('');
        paint();
        box.querySelector('#s-class-name')?.focus?.();
      });
      if (stage.step === 'confirm') {
        const f = stage.found;
        const confirm = n('form', 'class-join-confirm');
        confirm.append(n('p', 'class-line', f.teacherName ? tr('student.confirm', { name: f.className, teacher: f.teacherName }) : tr('student.confirmNoTeacher', { name: f.className })));
        const nameLabel = n('label', 'field row');
        const name = n('input'); name.id = 's-class-name'; name.type = 'text'; name.maxLength = CLASS_LIMITS.studentName;
        name.value = stage.name ?? session.account?.name ?? '';
        nameLabel.append(n('span', null, tr('student.yourName')), name);
        const choice = n('span', 'saved-data-choice');
        const join = n('button', 'setting-button', tr('student.join')); join.type = 'submit'; join.id = 's-class-join';
        const cancel = btn(n, tr('cancel'), () => { stage = { step: 'idle', typed: stage.typed }; paint(); box.querySelector('#s-class-code')?.focus?.(); });
        choice.append(join, cancel);
        confirm.append(nameLabel, n('div', 'field row', null));
        confirm.lastChild.append(n('span'), choice);
        box.append(confirm);
        confirm.addEventListener('submit', async (e) => {
          e.preventDefault();
          if (!name.value.trim()) { say(tr('student.noName')); name.focus(); return; }
          join.disabled = true;
          stage.name = name.value;
          const r = await joinClass({ ...net(), code: f.code, name: name.value });
          join.disabled = false;
          if (!r.ok) {
            say(r.why === 'already in' ? tr('student.already') : r.why === 'expired' ? tr('student.expired') : r.why === 'no such code' ? tr('student.noSuch') : why(r));
            return;
          }
          stage = { step: 'idle' };
          await refreshMine({ touch: false });
          say(tr('student.joined', { name: f.className }));
          box.querySelector('#s-class-leave')?.focus?.();
        });
      }
    }
    status.textContent = kept;
    box.append(status);
  }
  classSession.subscribe(paint);
  paint();
  return { paint };
}

// ---- Field notebook: Hand in -------------------------------------------------------------

/** The Hand in control for one notebook entry, or null when the student is in no class. */
export function handInControl(doc, entry, { say = () => {} } = {}) {
  const { mine, handed, on } = session;
  if (!on || !mine) return null;
  const n = maker(doc);
  const wrap = n('span', 'class-handin');
  const sent = handed.get(entry.id);
  const now = JSON.stringify(entry);
  const send = async (b) => {
    b.disabled = true;
    const r = await handIn({ ...net(), mine, entry });
    b.disabled = false;
    if (!r.ok) { say(r.why === 'too big' ? tr('handin.tooBig') : why(r)); return; }
    session.handed = new Map(session.handed).set(entry.id, { at: new Date().toISOString(), h: r.h });
    say(tr('handin.sent', { name: mine.className }));
    notify();
  };
  if (mine.closed) { if (sent) wrap.append(n('span', 'nav-sub', tr('handin.done', { date: when(sent.at) }))); return sent ? wrap : null; }
  if (!sent) {
    const b = btn(n, tr('handin.button', { name: mine.className }), () => send(b));
    b.dataset.handin = entry.id;
    wrap.append(b);
    return wrap;
  }
  wrap.append(n('span', 'nav-sub', tr('handin.done', { date: when(sent.at) })));
  if (sent.h !== now) {
    wrap.append(' ', n('span', 'nav-sub', tr('handin.edited')), ' ');
    const again = btn(n, tr('handin.again'), () => send(again));
    wrap.append(again);
  }
  const back = btn(n, tr('handin.back'), async () => {
    back.disabled = true;
    const r = await takeBack({ ...net(), mine, entryId: entry.id });
    back.disabled = false;
    if (!r.ok) { say(why(r)); return; }
    const next = new Map(session.handed); next.delete(entry.id); session.handed = next;
    say(tr('handin.taken'));
    notify();
  });
  back.dataset.takeBack = entry.id;
  wrap.append(' ', back);
  return wrap;
}

// ---- Guide › For teachers › Your classes -------------------------------------------------

const csvHead = () => ['student', 'joined', 'lastIn', 'kind', 'title', 'year', 'place', 'handedIn', 'text'].map((k) => tr(`csv.${k}`));
const fileName = (name) => `${String(name).replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '').slice(0, 60) || 'class'}.csv`;

export function downloadClassCSV(cls, members, handins, doc = globalThis.document) {
  const csv = classCSV(cls, members, handins, { head: csvHead(), clock: when, kindName });
  const url = URL.createObjectURL(new Blob(['﻿', csv], { type: 'text/csv;charset=utf-8' }));
  const a = doc.createElement('a'); a.href = url; a.download = fileName(cls.name);
  doc.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  return csv;
}
export function sheetWords(cls) {
  return {
    lang: LANG, name: tr('roster.name'), joined: tr('roster.joined'), lastIn: tr('roster.lastIn'),
    handedIn: tr('roster.handedIn'), reflections: tr('roster.reflections'), untitled: tr('work.untitled'),
    none: tr('work.none'), group: cls.group ? tr(`group.${cls.group}`) : '', printed: tr('sheet.printed', { date: day(new Date().toISOString()) }),
  };
}
/** Print one class's sheet in a small frame, never a second running town. */
export function printClass(cls, members, handins, doc = globalThis.document) {
  doc.querySelectorAll('.class-print-frame').forEach((f) => f.remove());
  const frame = doc.createElement('iframe');
  frame.title = cls.name; frame.className = 'class-print-frame'; frame.setAttribute('aria-hidden', 'true');
  frame.addEventListener('load', () => {
    const win = frame.contentWindow;
    win.addEventListener('afterprint', () => frame.remove(), { once: true });
    try { win.focus(); win.print(); } catch { frame.remove(); }
  }, { once: true });
  frame.srcdoc = classSheetHTML(cls, members, handins, { words: sheetWords(cls), clock: when, kindName });
  doc.body.append(frame);
  return frame;
}

export function mountTeacherClasses(container) {
  const doc = container.ownerDocument;
  useStyle(doc);
  const n = maker(doc);
  const root = n('section', 'nav-route-build class-panel');
  root.id = 'guide-classes';
  root.append(n('h3', null, tr('title')), n('p', 'nav-sub', tr('intro')), n('p', 'nav-sub', tr('noGrades')), n('p', 'nav-sub', tr('yearEnd')));
  const gate = n('p', 'nav-sub class-gate');
  const open = n('button', 'setting-button', tr('open')); open.type = 'button'; open.id = 'classes-open';
  const content = n('div', 'class-content'); content.id = 'classes-content'; content.hidden = true;
  open.setAttribute('aria-expanded', 'false'); open.setAttribute('aria-controls', content.id);
  const status = n('p', 'route-status class-status'); status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
  const say = (text) => { status.textContent = text; };
  root.append(gate, open, status, content);
  container.append(root);

  let classes = [];
  const rosters = new Map(); // class id → { members, handins } | { why }
  const openCards = new Set();

  const paintGate = () => {
    const { account, config, on } = session;
    const ready = on;
    gate.hidden = ready;
    gate.textContent = !cloudFeaturesOn(config) ? tr('off') : tr('needSignIn');
    open.hidden = !ready;
    if (!ready) { content.hidden = true; open.setAttribute('aria-expanded', 'false'); }
    return ready && Boolean(account);
  };

  async function load() {
    say(tr('loading'));
    const r = await myClasses(net());
    if (!r.ok) { say(tr('failed')); return; }
    classes = r.classes;
    say('');
    paint();
  }
  async function loadRoster(cls) {
    rosters.set(cls.id, { loading: true });
    paintCard(cls);
    const r = await classRoster({ ...net(), cls });
    rosters.set(cls.id, r.ok ? { members: r.members, handins: r.handins } : { why: r });
    paintCard(cls);
  }

  // The make form.
  const make = n('form', 'class-make');
  make.append(n('h4', null, tr('make.title')));
  const nameLabel = n('label', 'route-field');
  const name = n('input'); name.type = 'text'; name.maxLength = CLASS_LIMITS.name; name.id = 'class-make-name';
  nameLabel.append(n('span', null, tr('make.name')), name);
  const groupLabel = n('label', 'route-field');
  const group = n('select'); group.id = 'class-make-group';
  for (const g of YEAR_GROUPS) { const o = n('option', null, tr(`group.${g}`)); o.value = g; group.append(o); }
  group.value = '5';
  groupLabel.append(n('span', null, tr('make.group')), group);
  const makeButton = n('button', 'setting-button', tr('make.button')); makeButton.type = 'submit'; makeButton.id = 'class-make';
  make.append(nameLabel, groupLabel, makeButton);
  make.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!name.value.trim()) { say(tr('make.noName')); name.focus(); return; }
    if (classes.length >= CLASS_LIMITS.classes) { say(tr('make.tooMany', { n: classes.length })); return; }
    makeButton.disabled = true;
    const r = await makeClass({ ...net(), name: name.value, group: group.value, teacherName: session.account?.name ?? '' });
    makeButton.disabled = false;
    if (!r.ok) { say(tr('make.failed')); return; }
    classes = [r.cls, ...classes];
    rosters.set(r.cls.id, { members: [], handins: [] });
    openCards.add(r.cls.id);
    name.value = '';
    paint();
    say(tr('make.made', { name: r.cls.name, code: shownCode(r.cls.code) }));
    content.querySelector(`[data-class-id="${r.cls.id}"] summary`)?.focus?.();
  });

  const list = n('div', 'class-list');
  content.append(make, list);
  const cards = new Map();

  function paintCard(cls) {
    const card = cards.get(cls.id);
    if (!card) return;
    const body = card.querySelector('.class-card-body');
    const summary = card.querySelector('summary');
    const roster = rosters.get(cls.id);
    const count = roster?.members?.length;
    summary.textContent = [cls.name, cls.group ? tr(`group.${cls.group}`) : '',
      count == null ? '' : count === 1 ? tr('card.students.one') : tr('card.students.many', { n: count })].filter(Boolean).join(' · ');
    body.replaceChildren();
    // The code.
    if (cls.open) {
      const codeRow = n('div', 'class-code-row');
      const code = n('strong', 'class-code', shownCode(cls.code));
      code.setAttribute('aria-label', `${tr('code')} ${[...cls.code].join(' ')}`);
      codeRow.append(n('span', 'nav-k', tr('code')), ' ', code);
      body.append(codeRow);
      const expired = cls.expires && cls.expires <= new Date().toISOString();
      body.append(n('p', 'nav-sub', expired ? tr('code.expired') : cls.expires ? tr('code.until', { date: day(cls.expires) }) : ''),
        n('p', 'nav-sub', tr('code.how')));
    }
    // The actions.
    const actions = n('div', 'field-notebook-actions class-actions');
    const r = roster?.members ? roster : null;
    const refresh = btn(n, tr('refresh'), () => loadRoster(cls));
    const csv = btn(n, tr('csv'), () => { if (r) downloadClassCSV(cls, r.members, r.handins, doc); });
    const print = btn(n, tr('print'), () => { if (r) printClass(cls, r.members, r.handins, doc); });
    csv.disabled = print.disabled = !r;
    actions.append(refresh, csv, print);
    if (cls.open) {
      const fresh = btn(n, tr('code.new'), async () => {
        fresh.disabled = true;
        const res = await newCode({ ...net(), cls });
        fresh.disabled = false;
        if (!res.ok) { say(why(res)); return; }
        Object.assign(cls, res.cls);
        paintCard(cls);
        say(tr('code.made', { code: shownCode(cls.code) }));
      });
      actions.append(fresh);
    }
    // Closing deletes the class and all it holds (the school agreement § Deletion); the CSV
    // and the printed sheet beside it are how a teacher keeps a copy.
    const close = btn(n, tr('close'), () => confirmRow(n, tr('close.ask', { name: cls.name }), tr('close.yes'), async () => {
      const res = await closeClass({ ...net(), cls });
      if (!res.ok) { say(why(res)); return; }
      classes = classes.filter((c) => c.id !== cls.id);
      rosters.delete(cls.id);
      paint();
      say(tr('close.done', { name: cls.name }));
      open.focus();
    }, close), 'setting-button danger');
    actions.append(close);
    body.append(actions);
    // The roster.
    if (!roster || roster.loading) { body.append(n('p', 'nav-sub', tr('loading'))); return; }
    if (roster.why) { body.append(n('p', 'nav-sub', why(roster.why))); return; }
    if (!roster.members.length) { body.append(n('p', 'nav-sub', tr('roster.empty'))); return; }
    const rows = rosterRows(roster.members, roster.handins);
    const scroll = n('div', 'class-roster-scroll');
    scroll.tabIndex = 0;
    const table = n('table', 'class-roster');
    table.append(n('caption', 'visually-hidden', tr('roster.caption', { name: cls.name })));
    const head = n('tr');
    for (const k of ['name', 'joined', 'lastIn', 'handedIn', 'reflections']) { const th = n('th', null, tr(`roster.${k}`)); th.scope = 'col'; head.append(th); }
    head.append(n('th', 'visually-hidden', tr('roster.remove')));
    const thead = n('thead'); thead.append(head);
    const tbody = n('tbody');
    for (const row of rows) {
      const tr_ = n('tr');
      const nameCell = n('th', null, row.member.name); nameCell.scope = 'row';
      // Short dates, unbroken, so the roster fits the panel; the full time is on hover.
      const dated = (iso) => { const c = n('td', 'class-date', shortDay(iso)); c.title = when(iso); return c; };
      tr_.append(nameCell, dated(row.member.joinedAt), dated(row.member.lastIn),
        n('td', 'class-num', String(row.handins.length)), n('td', 'class-num', String(row.reflections)));
      const cell = n('td');
      const remove = btn(n, tr('roster.remove'), () => confirmRow(n, tr('remove.ask', { name: row.member.name }), tr('remove.yes'), async () => {
        const res = await removeStudent({ ...net(), cls, uid: row.member.uid });
        if (!res.ok) { say(why(res)); return; }
        say(tr('remove.done', { name: row.member.name }));
        await loadRoster(cls);
        card.querySelector('summary')?.focus?.();
      }, remove));
      remove.setAttribute('aria-label', `${tr('roster.remove')} ${row.member.name}`);
      cell.append(remove);
      tr_.append(cell);
      tbody.append(tr_);
    }
    table.append(thead, tbody);
    scroll.append(table);
    body.append(scroll);
    // Each student's hand-ins.
    const work = n('div', 'class-work');
    work.append(n('h4', null, tr('work.title')));
    let any = false;
    for (const row of rows) {
      if (!row.handins.length) continue;
      any = true;
      const fold = n('details', 'class-work-student');
      fold.append(n('summary', null, tr('work.student', { name: row.member.name, n: row.handins.length })));
      for (const h of row.handins) {
        const e = h.entry ?? {};
        const art = n('article', 'class-work-entry');
        art.append(n('h5', null, e.title || h.title || tr('work.untitled')),
          n('p', 'nav-sub', [kindName(h), e.year, e.place, when(h.at)].filter(Boolean).join(' · ')));
        if (typeof e.photo === 'string' && /^data:image\/(jpeg|png);base64,/.test(e.photo)) {
          const img = n('img'); img.src = e.photo; img.alt = e.title || ''; img.loading = 'lazy'; art.append(img);
        }
        if (e.text) art.append(n('p', 'class-work-text', e.text));
        fold.append(art);
      }
      work.append(fold);
    }
    if (!any) work.append(n('p', 'nav-sub', tr('work.none')));
    body.append(work);
  }

  function paint() {
    list.replaceChildren();
    cards.clear();
    if (!classes.length) { list.append(n('p', 'nav-sub', tr('none'))); return; }
    for (const cls of classes) {
      const card = n('details', 'class-card');
      card.dataset.classId = cls.id;
      card.append(n('summary'), n('div', 'class-card-body'));
      card.open = openCards.has(cls.id);
      card.addEventListener('toggle', () => {
        if (card.open) { openCards.add(cls.id); if (!rosters.has(cls.id)) loadRoster(cls); }
        else openCards.delete(cls.id);
      });
      cards.set(cls.id, card);
      list.append(card);
      paintCard(cls);
    }
  }

  open.addEventListener('click', () => {
    const show = content.hidden;
    content.hidden = !show;
    open.setAttribute('aria-expanded', String(show));
    if (show) { load(); name.focus(); }
  });
  const off = classSession.subscribe(() => { paintGate(); });
  paintGate();
  return { destroy() { off(); root.remove(); }, reload: load };
}

/** Is this hand-in a reflection (a jaunt's check or a Make your case answer)? */
export const isReflectionHandin = (h) => REFLECTION_TOPICS.includes(h.topic ?? h.entry?.topic ?? '');
