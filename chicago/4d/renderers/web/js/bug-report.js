/**
 * T-3743 — crash reports and the Report a bug key (the owner, 2026-11-24: "When it crashes
 * … we get a record and an email … a button maybe tiny in the upper right … shown by default
 * but you can turn it off … takes screen shot and collects environmental stuff and ships all
 * of that to firebase, a person can add comments and we know who filed it because of login").
 *
 * Every report is one Firestore document, `bugs/<id>`, written over REST like the visitor
 * rows (visitor-store.js), under the signed-in visitor's uid; the rules in docs/SIGN-IN.md
 * let anyone write one with their own uid (or none, when sign-in let them in without one)
 * and only the owner read. The owner reads them on /4d/walk/visitors.html.
 *
 * WHAT FILES ONE
 *   bug      the visitor pressed the key and sent the sheet: their words, a screenshot of
 *            the town, and everything below.
 *   crash    the page before this one was cut off (blackbox.js § wasCut): the tab killed for
 *            memory, or the display reset and never left cleanly. Filed by the next load,
 *            with that page's last steps.
 *   context  the display reset (a lost WebGL context), filed at once by the page it hit.
 *   error    an uncaught error or a rejected promise, the first of each message, three a page.
 * A bug, a crash and a context loss also email the owner (FormSubmit, as the contact page
 * does), at most MAIL_PER_DAY automatic ones a device a day so a looping crash cannot fill
 * his inbox. Errors are recorded and not emailed.
 *
 * WHERE IT SENDS. Only where the sign-in gate runs (SIGN_IN.hosts, not under automation),
 * so a local serve, the smoke and the film tools never write to the live project. Elsewhere
 * the sheet still opens and Send copies the report instead. Every report says which site it
 * came from (`live`, `dev`, `local`): the owner chose one Firebase project for both
 * (2026-11-24), with the rows told apart.
 *
 * KEPT LIGHT. Nothing is read until something is filed: the key is one button, the sheet
 * and its CSS are built on the first press, the screenshot is one JPEG of one frame drawn
 * anyway (main.js § bugShot), and the console tap keeps the last ERRORS_KEPT lines.
 */

import { autoId, deviceClass } from './visitor-store.js';
import { t } from './strings/index.js';
import './strings/bugs.js';

export const BUG_FIELDS = ['uid', 'email', 'kind', 'comment', 'year', 'site', 'build', 'device', 'gpu',
  'place', 'link', 'page', 'env', 'errors', 'steps', 'shot', 'at'];
/** The longest each string field may be; docs/SIGN-IN.md's rule says the same numbers. */
export const BUG_LIMITS = {
  uid: 128, email: 254, kind: 10, comment: 4000, year: 10, site: 10, build: 80, device: 160, gpu: 200,
  place: 200, link: 600, page: 300, env: 20000, errors: 8000, steps: 20000, shot: 900000,
};
export const BUG_KINDS = ['bug', 'crash', 'context', 'error'];
export const MAIL_TO = 'kevin.haas@polecat.live';
export const MAIL_PER_DAY = 3;
export const AUTO_PER_PAGE = 3;
export const AUTO_PER_DAY = 20;
export const ERRORS_KEPT = 20;
export const SENT_KEY = 'c4d.bugs.sent';
export const SHOT_EDGE = 800;

const DAY = 86_400_000;

/** `live`, `dev` or `local`, from the page's host. */
export function siteOf(hostname = '') {
  if (hostname === 'chicago.polecat.live') return 'live';
  if (/^dev\./.test(hostname) || /\.github\.io$/.test(hostname)) return 'dev';
  return 'local';
}

/** Whether reports go to Firebase from this page: the sign-in gate's own hosts, no robot. */
export function sendsFrom({ config, hostname = '', webdriver = false } = {}) {
  const fb = config?.firebase;
  return !!(config?.enabled && fb?.apiKey && fb?.projectId && !webdriver
    && (config.hosts || []).includes(hostname));
}

const cut = (v, n) => String(v ?? '').slice(0, n);

/** The browser and engine, in a few words: "Chrome 131", "Safari 18", "Firefox 133". */
export function browserOf(ua = '') {
  const m = /(Edg|OPR|Firefox|FxiOS|CriOS|Chrome|Version)\/(\d+)/.exec(ua);
  if (!m) return '';
  const name = { Edg: 'Edge', OPR: 'Opera', FxiOS: 'Firefox', CriOS: 'Chrome', Version: 'Safari' }[m[1]] || m[1];
  return `${name} ${m[2]}`;
}

/** What the browser says about the machine. No DOM beyond navigator, screen and performance. */
export function deviceFacts(win = globalThis) {
  const n = win.navigator || {};
  const s = win.screen || {};
  const mem = win.performance?.memory;
  const mb = (v) => (Number.isFinite(v) ? Math.round(v / 1048576) : null);
  return {
    class: deviceClass(win),
    browser: browserOf(n.userAgent || ''),
    platform: n.userAgentData?.platform || n.platform || '',
    ua: cut(n.userAgent, 300),
    lang: n.language || '',
    cores: n.hardwareConcurrency ?? null,
    memoryGB: n.deviceMemory ?? null,
    screen: s.width ? `${s.width}x${s.height}` : '',
    window: `${win.innerWidth ?? '?'}x${win.innerHeight ?? '?'}`,
    dpr: win.devicePixelRatio ?? null,
    touchPoints: n.maxTouchPoints ?? 0,
    heapMB: mb(mem?.usedJSHeapSize),
    heapLimitMB: mb(mem?.jsHeapSizeLimit),
    connection: n.connection?.effectiveType || '',
  };
}

/** The Firestore fields of one report, each cut to its limit. Exported for the self-test. */
export function reportFields(r, { now = () => Date.now() } = {}) {
  const str = (key, v) => ({ stringValue: cut(v, BUG_LIMITS[key]) });
  const json = (key, v) => {
    if (v == null) return str(key, '');
    const text = typeof v === 'string' ? v : JSON.stringify(v);
    // A JSON field that will not fit keeps its tail: the newest steps and errors are the last ones.
    return str(key, text.length > BUG_LIMITS[key] ? text.slice(text.length - BUG_LIMITS[key]) : text);
  };
  return {
    uid: str('uid', r.uid), email: str('email', r.email),
    kind: str('kind', BUG_KINDS.includes(r.kind) ? r.kind : 'bug'),
    comment: str('comment', r.comment), year: str('year', r.year), site: str('site', r.site),
    build: str('build', r.build), device: str('device', r.device), gpu: str('gpu', r.gpu),
    place: str('place', r.place), link: str('link', r.link), page: str('page', r.page),
    env: json('env', r.env), errors: json('errors', r.errors), steps: json('steps', r.steps),
    shot: { stringValue: r.shot && String(r.shot).length <= BUG_LIMITS.shot ? String(r.shot) : '' },
    at: { timestampValue: new Date(now()).toISOString() },
  };
}

/** The one-line device label a list row shows: "phone · iPhone · Safari 18". */
export function deviceLabel(f = {}) {
  return [f.class, f.platform, f.browser].filter(Boolean).join(' · ');
}

/** The email that goes with a report (FormSubmit's JSON body). */
export function mailBody(r, { reportUrl = '' } = {}) {
  const tag = r.site === 'live' ? '' : ` [${r.site}]`;
  const what = { bug: 'Bug report', crash: 'Crash', context: 'Display reset', error: 'Error' }[r.kind] || 'Report';
  return {
    _subject: `4D Chicago${tag} — ${what} — ${r.year} — ${r.email || 'not signed in'}`,
    _template: 'table', _captcha: 'false',
    ...(r.email && /@/.test(r.email) ? { _replyto: r.email } : {}),
    kind: what, from: r.email || 'not signed in', year: r.year, site: r.site,
    comment: r.comment || '—', place: r.place || '—', device: r.device || '—', gpu: r.gpu || '—',
    build: r.build || '—', spot: r.link || '—', report: reportUrl || '—',
  };
}

/** The recent errors: window errors, rejected promises and console.error lines, newest last. */
export function createErrorRing({ max = ERRORS_KEPT, now = () => Date.now() } = {}) {
  const lines = [];
  const start = now();
  return {
    push(kind, msg) {
      lines.push({ t: Math.round((now() - start) / 100) / 10, k: kind, msg: cut(msg, 300) });
      if (lines.length > max) lines.splice(0, lines.length - max);
    },
    get lines() { return lines.slice(); },
  };
}

function textOf(v) {
  if (v instanceof Error) return `${v.name}: ${v.message}${v.stack ? ` @ ${String(v.stack).split('\n').slice(1, 3).join(' ').trim()}` : ''}`;
  if (typeof v === 'string') return v;
  try { return JSON.stringify(v); } catch { return String(v); }
}

/**
 * The reporter. `send` and `mail` are the two network calls, handed in so the self-test
 * and the smoke can watch them; by default they are Firestore REST and FormSubmit.
 */
export function createBugReports({
  config = null,
  year = '',
  build = '',
  win = globalThis,
  store = (() => { try { return win.localStorage; } catch { return null; } })(),
  now = () => Date.now(),
  fetchFn = (...a) => win.fetch(...a),
  hookConsole = true,
} = {}) {
  const loc = win.location || {};
  const site = siteOf(loc.hostname);
  const live = sendsFrom({ config, hostname: loc.hostname, webdriver: !!win.navigator?.webdriver });
  const errors = createErrorRing({ now });
  let account;          // undefined until sign-in has answered; null when nobody is signed in
  let extra = () => ({});
  const queue = [];
  const seenErrors = new Set();
  let autoThisPage = 0;
  const sentLog = [];   // what this page filed, for the smoke

  const readJson = (key, fallback) => { try { return JSON.parse(store?.getItem(key) || 'null') ?? fallback; } catch { return fallback; } };
  const writeJson = (key, v) => { try { store?.setItem(key, JSON.stringify(v)); } catch { /* storage refused */ } };

  /** The device's record of what it has filed: page ids already reported, and when. */
  function ledger() {
    const l = readJson(SENT_KEY, {});
    const fresh = (a) => (Array.isArray(a) ? a.filter((x) => now() - x < DAY) : []);
    return { pages: Array.isArray(l.pages) ? l.pages.slice(-20) : [], auto: fresh(l.auto), mail: fresh(l.mail) };
  }

  const projectId = config?.firebase?.projectId;
  const docs = projectId
    ? `https://firestore.googleapis.com/v1/projects/${encodeURIComponent(projectId)}/databases/(default)/documents`
    : '';

  /** Firestore: one new document under a chosen id, so the email can link to it. */
  async function send(id, fields, idToken) {
    const url = `${docs}/bugs?documentId=${encodeURIComponent(id)}&key=${encodeURIComponent(config.firebase.apiKey)}`;
    const headers = { 'Content-Type': 'application/json' };
    if (idToken) headers.Authorization = `Bearer ${idToken}`;
    const res = await fetchFn(url, { method: 'POST', headers, body: JSON.stringify({ fields }) });
    if (!res.ok) throw new Error(`store ${res.status}`);
    return true;
  }
  async function mail(body) {
    const res = await fetchFn(`https://formsubmit.co/ajax/${MAIL_TO}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    });
    const j = await res.json().catch(() => ({}));
    if (!(res.ok && String(j.success) === 'true')) throw new Error(j?.message || `mail ${res.status}`);
    return true;
  }
  const net = { send, mail };

  function reportUrl(id) {
    const host = site === 'dev' ? 'https://dev.chicago.polecat.live/4d/dev/walk/visitors.html' : 'https://chicago.polecat.live/4d/walk/visitors.html';
    return `${host}?bug=${id}`;
  }

  /** Everything about where and how the visitor is, read now. */
  function gather(kind, { comment = '', steps = null, shot = '', of = year } = {}) {
    let more = {};
    try { more = extra() || {}; } catch (err) { more = { extraFailed: textOf(err) }; }
    const facts = deviceFacts(win);
    return {
      kind, comment, year: String(of || ''), site, build,
      uid: account?.uid || '', email: account?.email || '',
      device: deviceLabel(facts), gpu: more.gpu || '',
      place: more.place || '', link: more.link || '',
      page: cut(`${loc.pathname || ''}${loc.search || ''}`, BUG_LIMITS.page),
      env: { device: facts, ...more, gpu: undefined, place: undefined, link: undefined },
      errors: errors.lines, steps, shot,
    };
  }

  /** File one report: Firestore, then (where it should) the email. Never throws. */
  async function file(r, { email = true } = {}) {
    const id = autoId();
    const entry = { id, kind: r.kind, stored: false, mailed: false, live };
    sentLog.push(entry);
    if (!live) return entry;
    // The email's place is taken now, before any wait, so reports filed together count right.
    const automatic = r.kind !== 'bug';
    let mailOk = email;
    if (email && automatic) {
      const l = ledger();
      mailOk = l.mail.length < MAIL_PER_DAY;
      if (mailOk) writeJson(SENT_KEY, { ...l, mail: [...l.mail, now()] });
    }
    let idToken = '';
    try { idToken = account?.idToken ? await account.idToken() : ''; } catch { idToken = ''; }
    try { entry.stored = await net.send(id, reportFields(r, { now }), idToken); } catch (err) {
      entry.error = textOf(err);
      console.warn('[4D Chicago] report not stored', entry.error);
    }
    if (mailOk) {
      try { entry.mailed = await net.mail(mailBody(r, { reportUrl: entry.stored ? reportUrl(id) : '' })); }
      catch (err) { entry.mailError = textOf(err); }
    }
    return entry;
  }

  /** An automatic report: counted against the page's and the day's caps, then queued. */
  function auto(kind, opts = {}, { pageId = null } = {}) {
    const l = ledger();
    if (autoThisPage >= AUTO_PER_PAGE || l.auto.length >= AUTO_PER_DAY) return false;
    if (pageId && l.pages.includes(pageId)) return false;
    autoThisPage++;
    writeJson(SENT_KEY, { ...l, auto: [...l.auto, now()], pages: pageId ? [...l.pages, pageId].slice(-20) : l.pages });
    const job = () => file(gather(kind, opts), { email: kind !== 'error' });
    if (account === undefined) queue.push(job); else void job();
    return true;
  }

  // The console tap: errors only, kept as short lines; the console still prints them.
  if (hookConsole && win.console?.error) {
    const original = win.console.error.bind(win.console);
    win.console.error = (...args) => {
      try { errors.push('console', args.map(textOf).join(' ')); } catch { /* never in the way */ }
      original(...args);
    };
  }

  const ownScript = (file) => !file || String(file).startsWith(loc.origin || '\u0000');
  function onError(e) {
    const msg = textOf(e?.error ?? e?.message ?? e);
    errors.push('error', msg);
    // "Script error." is a cross-origin script's, which this page does not load: a browser
    // extension's, or the in-app browser's own (blackbox.js § Meg's crash). Not ours.
    if (/^Script error\.?$/i.test(String(e?.message ?? '')) || !ownScript(e?.filename)) return;
    // The same message from another line is the same fault: one report a message.
    const key = String(e?.error?.message ?? e?.message ?? msg).slice(0, 120);
    if (seenErrors.has(key)) return;
    seenErrors.add(key);
    auto('error', { comment: msg });
  }
  function onRejection(e) {
    const msg = textOf(e?.reason);
    errors.push('rejection', msg);
    const key = String(e?.reason?.message ?? msg).slice(0, 120);
    if (seenErrors.has(key)) return;
    seenErrors.add(key);
    auto('error', { comment: `Unhandled rejection: ${msg}` });
  }
  win.addEventListener?.('error', onError);
  win.addEventListener?.('unhandledrejection', onRejection);

  return {
    live, site, errors, sentLog, net,
    /** Sign-in has answered: who files from here on (null: nobody signed in). Sends the queue. */
    signedIn(who) {
      account = who ?? null;
      for (const job of queue.splice(0)) void job();
    },
    /** main.js's reader of the scene: gpu, place, link, settings, position, renderer, tiers. */
    setExtra(fn) { extra = fn; },
    /** The page before this one was cut off: file its record once (blackbox.js § wasCut). */
    crash(record, line = '') {
      if (!record?.page) return false;
      return auto('crash', { comment: line, steps: record, of: record.year ?? year }, { pageId: record.page });
    },
    /** The display reset on this page: file it now, and not again from the next load. */
    contextLost(box) { return auto('context', { comment: 'The display was reset (WebGL context lost).', steps: box }, { pageId: box?.page }); },
    /** The visitor's own report, from the sheet. */
    bug({ comment = '', shot = '', steps = null } = {}) { return file(gather('bug', { comment, shot, steps })); },
    /** The report the sheet would send, as text, for Copy where nothing is sent. */
    preview({ comment = '', steps = null } = {}) { return JSON.stringify(gather('bug', { comment, steps }), null, 1); },
  };
}

// ---- the key and the sheet --------------------------------------------------------------- //

const BUG_ICON = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.9" '
  + 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 7.5V6a3 3 0 0 1 6 0v1.5"/>'
  + '<rect x="7" y="7.5" width="10" height="12" rx="5"/><path d="M12 11v8.5M3.5 10.5 7 12M20.5 10.5 17 12M3.5 19 7 17M20.5 19 17 17M3 14.5h4M17 14.5h4"/></svg>';

/**
 * The key, a small round one hung beside the compass row's other keys (walk.css §
 * .instrument-keys), and the sheet it opens. `capture()` resolves a JPEG data URL of the
 * town (main.js draws it into the next frame), or '' where none could be had.
 */
export function mountBugKey({ doc = globalThis.document, reports, capture = async () => '', steps = () => null,
  shown = true, onOpen = () => {} } = {}) {
  const host = doc?.querySelector?.('.hud-instrument .instrument-keys');
  if (!host || !reports) return null;
  const key = doc.createElement('button');
  key.type = 'button';
  key.id = 'bug-key';
  key.className = 'bug-key';
  key.title = t('bugs.key');
  key.setAttribute('aria-label', t('bugs.key'));
  key.setAttribute('aria-haspopup', 'dialog');
  key.innerHTML = BUG_ICON;
  key.hidden = !shown;
  host.append(key);

  let sheet = null;
  let parts = null;
  let shot = '';
  let opened = 0;

  function style() {
    if (doc.getElementById('bug-report-style')) return;
    const css = doc.createElement('link');
    css.id = 'bug-report-style'; css.rel = 'stylesheet';
    css.href = new URL('../css/bug-report.css', import.meta.url).href;
    doc.head.append(css);
  }
  function build() {
    style();
    sheet = doc.createElement('div');
    sheet.className = 'bug-sheet';
    sheet.id = 'bug-sheet';
    sheet.setAttribute('role', 'dialog');
    sheet.setAttribute('aria-modal', 'true');
    sheet.setAttribute('aria-labelledby', 'bug-title');
    sheet.hidden = true;
    sheet.innerHTML = `
      <div class="bug-head"><h2 id="bug-title"></h2><button type="button" class="bug-x" data-act="close"><span aria-hidden="true">×</span></button></div>
      <figure class="bug-shot-wrap"><img class="bug-shot" alt=""><figcaption class="bug-shot-none"></figcaption></figure>
      <label class="bug-include"><input type="checkbox" class="bug-with-shot" checked> <span></span></label>
      <label class="bug-comment-label" for="bug-comment"></label>
      <textarea id="bug-comment" class="bug-comment" rows="4" maxlength="${BUG_LIMITS.comment}"></textarea>
      <p class="bug-what"></p>
      <p class="bug-status" role="status" aria-live="polite"></p>
      <div class="bug-actions"><button type="button" data-act="close" class="bug-cancel"></button><button type="button" data-act="send" class="bug-send"></button></div>`;
    doc.body.append(sheet);
    const q = (s) => sheet.querySelector(s);
    parts = {
      title: q('#bug-title'), x: q('.bug-x'), img: q('.bug-shot'), none: q('.bug-shot-none'),
      include: q('.bug-with-shot'), includeText: q('.bug-include span'), label: q('.bug-comment-label'),
      comment: q('.bug-comment'), what: q('.bug-what'), status: q('.bug-status'),
      cancel: q('.bug-cancel'), send: q('.bug-send'),
    };
    parts.title.textContent = t('bugs.title');
    parts.x.setAttribute('aria-label', t('bugs.close'));
    parts.includeText.textContent = t('bugs.includeShot');
    parts.label.textContent = t('bugs.comment');
    parts.comment.placeholder = t('bugs.placeholder');
    parts.what.textContent = t('bugs.what');
    parts.cancel.textContent = t('bugs.cancel');
    parts.send.textContent = t('bugs.send');
    parts.img.alt = t('bugs.shotAlt');
    sheet.addEventListener('click', (e) => {
      const act = e.target.closest?.('[data-act]')?.dataset.act;
      if (act === 'close') close();
      else if (act === 'send') void submit();
    });
    // The sheet takes its own keys: Esc closes it, and nothing typed here walks the visitor.
    sheet.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Escape') { e.preventDefault(); close(); }
      else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); void submit(); }
      else if (e.key === 'Tab') {
        const stops = [...sheet.querySelectorAll('button, textarea, input')].filter((el) => !el.disabled && el.offsetParent !== null);
        if (!stops.length) return;
        const first = stops[0]; const last = stops.at(-1);
        if (e.shiftKey && doc.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && doc.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    sheet.addEventListener('keyup', (e) => e.stopPropagation());
  }

  async function open() {
    if (!sheet) build();
    if (!sheet.hidden) return;
    opened++;
    try { doc.exitPointerLock?.(); } catch { /* not locked */ }
    // The town first, before the sheet covers any of it.
    key.disabled = true;
    shot = '';
    try { shot = await capture(); } catch { shot = ''; }
    key.disabled = false;
    parts.img.hidden = !shot;
    if (shot) parts.img.src = shot; else parts.img.removeAttribute('src');
    parts.none.hidden = !!shot;
    parts.none.textContent = shot ? '' : t('bugs.noShot');
    parts.include.checked = !!shot;
    parts.include.disabled = !shot;
    parts.status.textContent = reports.live ? '' : t('bugs.notLive');
    parts.send.textContent = reports.live ? t('bugs.send') : t('bugs.copy');
    parts.send.disabled = false;
    sheet.hidden = false;
    key.setAttribute('aria-expanded', 'true');
    onOpen(true);
    parts.comment.focus();
  }
  function close() {
    if (!sheet || sheet.hidden) return;
    sheet.hidden = true;
    key.setAttribute('aria-expanded', 'false');
    onOpen(false);
    key.focus();
  }
  async function submit() {
    const comment = parts.comment.value.trim();
    const withShot = parts.include.checked ? shot : '';
    if (!reports.live) {
      const text = reports.preview({ comment, steps: steps() });
      try { await doc.defaultView.navigator.clipboard.writeText(text); parts.status.textContent = t('bugs.copied'); }
      catch { parts.status.textContent = t('bugs.copyFailed'); }
      return;
    }
    parts.send.disabled = true;
    parts.status.textContent = t('bugs.sending');
    const entry = await reports.bug({ comment, shot: withShot, steps: steps() });
    if (entry.stored || entry.mailed) {
      parts.status.textContent = t('bugs.sent');
      parts.comment.value = '';
      setTimeout(close, 1400);
    } else {
      parts.send.disabled = false;
      parts.status.textContent = t('bugs.failed');
    }
  }

  key.addEventListener('click', () => { void open(); });
  return {
    key, open, close,
    get sheet() { return sheet; },
    get opened() { return opened; },
    get shot() { return shot; },
    setShown(on) { key.hidden = !on; if (!on) close(); },
  };
}

/**
 * One frame of the town as a small JPEG. Call it inside the frame that drew the canvas
 * (main.js § bugShot): outside it the drawing buffer is already cleared.
 */
export function frameJpeg(canvas, { doc = globalThis.document, edge = SHOT_EDGE, quality = 0.62 } = {}) {
  const w = canvas?.width || 0; const h = canvas?.height || 0;
  if (!w || !h) return '';
  const scale = Math.min(1, edge / Math.max(w, h));
  const out = doc.createElement('canvas');
  out.width = Math.max(1, Math.round(w * scale)); out.height = Math.max(1, Math.round(h * scale));
  const ctx = out.getContext('2d');
  if (!ctx) return '';
  ctx.drawImage(canvas, 0, 0, out.width, out.height);
  const url = out.toDataURL('image/jpeg', quality);
  out.width = out.height = 0;
  return url.length <= BUG_LIMITS.shot ? url : '';
}
